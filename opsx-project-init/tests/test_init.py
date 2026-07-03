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


class TestNoConsumerHack:
    """checkpoint 全局化（~/.sdflow/hack/，由 setup.sh 安装）：init/update 不再往消费仓铺 hack/。"""

    def test_init_module_has_no_copy_hack(self):
        assert not hasattr(init_mod, "copy_hack")

    def test_run_does_not_create_consumer_hack_dir(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "fake-claude"))
        init_mod.run(str(tmp_path / "proj"), "init")
        assert not (tmp_path / "proj" / "hack").exists()


class TestBundleToolsOnly:
    """R-MRF-1：copy_bundle 只部署 tools/ 子树，规则文件数 = 0。"""

    def test_deploys_only_tools_subtree(self, tmp_path):
        dst, n = copy_bundle(str(tmp_path))
        wf = tmp_path / "openspec" / "workflow"
        assert (wf / "tools" / "engine.js").is_file()
        assert not (wf / "workflow.md").exists()
        assert not (wf / "spec-checklists").exists()
        assert not (wf / "code-checklists").exists()
        md_rules = [p for p in wf.rglob("*.md") if "tools" not in p.parts]
        assert md_rules == []                      # 规则文件数 = 0

    def test_full_flag_restores_whole_bundle(self, tmp_path):
        init_mod.copy_bundle(str(tmp_path), full=True)
        wf = tmp_path / "openspec" / "workflow"
        assert (wf / "workflow.md").is_file()      # --dev 整刷用（Task 7）


class TestUpdateDev:
    """5.6：toolkit 源仓 dogfood 刷新——update --dev 整 bundle 刷 instance；普通 update 只 tools/。"""

    def _seeded(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "fake-claude"))
        root = tmp_path / "proj"
        init_mod.run(str(root), "init")
        return root

    def test_plain_update_does_not_deploy_rules(self, tmp_path, monkeypatch):
        root = self._seeded(tmp_path, monkeypatch)
        init_mod.run(str(root), "update")
        assert not (root / "openspec" / "workflow" / "workflow.md").exists()

    def test_dev_update_deploys_full_bundle(self, tmp_path, monkeypatch):
        root = self._seeded(tmp_path, monkeypatch)
        init_mod.run(str(root), "update", dev=True)
        assert (root / "openspec" / "workflow" / "workflow.md").is_file()
        assert (root / "openspec" / "workflow" / "spec-checklists").is_dir()


class TestHandleConfigFromBundleSrc:
    """2.5：config 模版改读 BUNDLE_SRC——消费仓无规则副本时 init 不得 FileNotFoundError。"""

    def test_init_creates_config_without_consumer_template(self, tmp_path):
        root = tmp_path / "proj"
        (root / "openspec").mkdir(parents=True)    # 无 workflow/config.template.yaml
        status, _ = init_mod.handle_config(str(root), "init")
        assert status == "created"
        assert (root / "openspec" / "config.yaml").is_file()


class TestStaleShadowWarnings:
    """R-MRF-3：残留规则/孤儿 checkpoint 只告警绝不删（反静默守卫·陈旧遮蔽变体）。"""

    def _legacy_consumer(self, tmp_path):
        root = tmp_path / "old"
        wf = root / "openspec" / "workflow"
        wf.mkdir(parents=True)
        (wf / "workflow.md").write_text("# old rules\n", encoding="utf-8")
        (root / "hack").mkdir()
        (root / "hack" / "checkpoint-commit.sh").write_text("#!/bin/bash\n", encoding="utf-8")
        return root

    def test_warns_on_residual_rules_and_orphan_hack_without_deleting(self, tmp_path):
        root = self._legacy_consumer(tmp_path)
        warns = init_mod.stale_shadow_warnings(str(root))
        assert any("遮蔽" in w for w in warns)
        assert any("checkpoint-commit.sh" in w for w in warns)
        assert (root / "openspec" / "workflow" / "workflow.md").exists()   # 绝不删
        assert (root / "hack" / "checkpoint-commit.sh").exists()

    def test_clean_consumer_no_warnings(self, tmp_path):
        root = tmp_path / "clean"
        (root / "openspec" / "workflow" / "tools").mkdir(parents=True)
        assert init_mod.stale_shadow_warnings(str(root)) == []

    def test_update_prints_warnings(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "fake-claude"))
        root = self._legacy_consumer(tmp_path)
        init_mod.run(str(root), "update")
        out = capsys.readouterr().out
        assert "遮蔽" in out
        assert (root / "openspec" / "workflow" / "workflow.md").exists()


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
