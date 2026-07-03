"""
Tests for init.py's review-tool copying + generalized hook installer.
Run with: python3 -m pytest opsx-project-init/tests/test_init.py -v
"""
import json
import os
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import init as init_mod
from init import copy_review_tool, copy_bundle


class TestReviewToolDeployment:
    """B1 归位后：tools/ 由 workflow bundle 携带（copy_bundle → openspec/workflow/tools/），
    copy_review_tool 只铺「服务器根锚」——serve.sh + 根 review.html 留 openspec/ 根。
    故测试须先 copy_bundle 再 copy_review_tool（复刻 run() 的调用顺序）。"""

    def _deploy(self, root):
        copy_bundle(str(root))            # tools/ 落 openspec/workflow/tools/
        return copy_review_tool(str(root))  # serve.sh + 根 review.html 落 openspec/ 根

    def test_tools_under_workflow_and_root_anchors_at_openspec_root(self, tmp_path):
        n = self._deploy(tmp_path)
        osroot = tmp_path / "openspec"
        # 工具机械随 bundle 落 openspec/workflow/tools/（B1 归位）
        assert (osroot / "workflow" / "tools" / "engine.js").is_file()
        assert (osroot / "workflow" / "tools" / "engine.css").is_file()
        assert (osroot / "workflow" / "tools" / "review-stub.html").is_file()
        assert (osroot / "workflow" / "tools" / "vendor" / "marked.min.js").is_file()
        # 服务器根锚留 openspec/ 根（serve.sh 须从此起服务才覆盖到 changes/specs）
        assert (osroot / "serve.sh").is_file()
        assert (osroot / "review.html").is_file()
        # 不再在 openspec/ 根留 tools/
        assert not (osroot / "tools").exists()
        assert n == 2  # copy_review_tool 只铺 serve.sh + 根 review.html

    def test_root_review_html_substitutes_project_name(self, tmp_path):
        project_dir = tmp_path / "my-project"
        project_dir.mkdir()
        self._deploy(project_dir)
        osroot = project_dir / "openspec"
        content = (osroot / "review.html").read_text(encoding="utf-8")
        template = (osroot / "workflow" / "tools" / "review-stub.html").read_text(encoding="utf-8")
        # 模板源（openspec/workflow/tools/）须保持原始未替换——它是另两个生产者
        # （change-review-stub.py hook、gen_review_stub.py）各自替换的源，须仍含字面 token。
        assert "__PROJECT_NAME__" in template
        # 生成的根 review.html 须已替换为项目目录名，且与模板逐字节一致（仅 token 被换）。
        assert "__PROJECT_NAME__" not in content
        assert content == template.replace("__PROJECT_NAME__", "my-project")

    def test_root_review_html_references_workflow_tools_assets(self, tmp_path):
        # B1 归位后资产必须是根相对 /workflow/tools/...（服务器根 = openspec/），旧 /tools/ 不得残留
        self._deploy(tmp_path)
        content = (tmp_path / "openspec" / "review.html").read_text(encoding="utf-8")
        assert "/workflow/tools/engine.js" in content
        assert "/workflow/tools/engine.css" in content
        assert 'href="/tools/' not in content
        assert 'src="/tools/' not in content

    def test_serve_sh_is_executable(self, tmp_path):
        self._deploy(tmp_path)
        mode = (tmp_path / "openspec" / "serve.sh").stat().st_mode
        assert mode & stat.S_IXUSR

    def test_idempotent_rerun_overwrites_cleanly(self, tmp_path):
        project_dir = tmp_path / "another-project"
        project_dir.mkdir()
        self._deploy(project_dir)
        self._deploy(project_dir)  # update-mode re-run
        osroot = project_dir / "openspec"
        assert (osroot / "review.html").is_file()
        content = (osroot / "review.html").read_text(encoding="utf-8")
        template = (osroot / "workflow" / "tools" / "review-stub.html").read_text(encoding="utf-8")
        # still a clean substituted copy, not duplicated/appended, not re-substituted-twice
        assert content == template.replace("__PROJECT_NAME__", "another-project")


class TestCopyHack:
    """copy_hack 把 assets/hack/*.sh 部署到消费仓 repo 根 hack/，保留可执行位。"""

    def test_deploys_scripts_to_repo_root_hack_with_exec_bit(self, tmp_path):
        n = init_mod.copy_hack(str(tmp_path))
        script = tmp_path / "hack" / "checkpoint-commit.sh"
        assert script.is_file()
        assert n >= 1
        assert script.stat().st_mode & stat.S_IXUSR  # 源 chmod +x，copymode 须保留

    def test_idempotent_rerun_overwrites_cleanly(self, tmp_path):
        init_mod.copy_hack(str(tmp_path))
        init_mod.copy_hack(str(tmp_path))  # update-mode 重跑
        assert (tmp_path / "hack" / "checkpoint-commit.sh").is_file()


class TestEnsureGlobalHooks:
    def _settings_path(self, home):
        return home / "settings.json"

    def test_installs_and_registers_a_new_hook_spec(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        src = tmp_path / "myhook.py"
        src.write_text("print('hi')\n", encoding="utf-8")
        spec = {
            "name": "myhook.py",
            "src": str(src),
            "event": "PostToolUse",
            "matcher": "Bash",
            "cmd": 'python3 "$HOME/.claude/hooks/myhook.py"',
        }
        msg = init_mod.ensure_global_hook(spec)
        assert "安装" in msg
        assert (home / "hooks" / "myhook.py").is_file()
        data = json.loads(self._settings_path(home).read_text(encoding="utf-8"))
        assert data["hooks"]["PostToolUse"][0]["matcher"] == "Bash"
        assert "myhook.py" in data["hooks"]["PostToolUse"][0]["hooks"][0]["command"]

    def test_rerun_is_idempotent_no_duplicate_registration(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        src = tmp_path / "myhook.py"
        src.write_text("print('hi')\n", encoding="utf-8")
        spec = {
            "name": "myhook.py",
            "src": str(src),
            "event": "PostToolUse",
            "matcher": "Bash",
            "cmd": 'python3 "$HOME/.claude/hooks/myhook.py"',
        }
        init_mod.ensure_global_hook(spec)
        init_mod.ensure_global_hook(spec)
        data = json.loads(self._settings_path(home).read_text(encoding="utf-8"))
        assert len(data["hooks"]["PostToolUse"]) == 1

    def test_two_different_hooks_land_in_their_own_event_lists(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        pre_src = tmp_path / "pre.py"
        pre_src.write_text("print('pre')\n", encoding="utf-8")
        post_src = tmp_path / "post.py"
        post_src.write_text("print('post')\n", encoding="utf-8")
        init_mod.ensure_global_hook({
            "name": "pre.py", "src": str(pre_src), "event": "PreToolUse",
            "matcher": "Bash", "cmd": 'python3 "$HOME/.claude/hooks/pre.py"',
        })
        init_mod.ensure_global_hook({
            "name": "post.py", "src": str(post_src), "event": "PostToolUse",
            "matcher": "Bash", "cmd": 'python3 "$HOME/.claude/hooks/post.py"',
        })
        data = json.loads(self._settings_path(home).read_text(encoding="utf-8"))
        assert len(data["hooks"]["PreToolUse"]) == 1
        assert len(data["hooks"]["PostToolUse"]) == 1

    def test_preexisting_single_hook_registration_still_recognized(self, tmp_path, monkeypatch):
        """Backward compat: a settings.json written by the OLD single-hook ensure_global_hook()
        must still be recognized as 'already registered' by the new generalized version."""
        home = tmp_path / "home"
        home.mkdir()
        (home / "hooks").mkdir()
        src = tmp_path / "ff0.py"
        src.write_text("print('ff0')\n", encoding="utf-8")
        (home / "hooks" / "ff0.py").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        (self._settings_path(home)).write_text(json.dumps({
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": 'python3 "$HOME/.claude/hooks/ff0.py"'}
            ]}]}
        }), encoding="utf-8")
        spec = {
            "name": "ff0.py", "src": str(src), "event": "PreToolUse",
            "matcher": "Bash", "cmd": 'python3 "$HOME/.claude/hooks/ff0.py"',
        }
        msg = init_mod.ensure_global_hook(spec)
        assert "已注册" in msg
        data = json.loads(self._settings_path(home).read_text(encoding="utf-8"))
        assert len(data["hooks"]["PreToolUse"]) == 1  # not duplicated
