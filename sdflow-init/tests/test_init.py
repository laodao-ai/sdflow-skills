"""
Tests for init.py's review-tool copying + generalized hook installer.
Run with: python3 -m pytest sdflow-init/tests/test_init.py -v
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
        # 模板源（openspec/workflow/tools/）须保持原始未替换——它是 copy_review_tool 渲染
        # 根 review.html 的源模板，须仍含字面 token（每目录 stub 生产者已移除）。
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
        # --dev 身份校验（B2-F2）要求 root == toolkit 源仓根；此处伪造 SKILL_DIR 令 root 过检。
        monkeypatch.setattr(init_mod, "SKILL_DIR", str(root / "sdflow-init"))
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


class TestDevRepoIdentityGuard:
    """B2-F2：--dev 只准在 toolkit 源仓自身跑，防把整套规则灌进消费仓。"""

    def test_dev_pointing_elsewhere_dies(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "fake-claude"))
        other_root = tmp_path / "consumer-repo"
        (other_root / "openspec").mkdir(parents=True)
        with pytest.raises(SystemExit):
            init_mod.run(str(other_root), "update", dev=True)
        err = capsys.readouterr().err
        assert "仅用于 toolkit 源仓" in err

    def test_dev_matching_source_repo_passes_identity_check(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "fake-claude"))
        fake_skill_dir = tmp_path / "some-repo" / "sdflow-init"
        fake_skill_dir.mkdir(parents=True)
        monkeypatch.setattr(init_mod, "SKILL_DIR", str(fake_skill_dir))
        root = tmp_path / "some-repo"
        (root / "openspec").mkdir()
        init_mod.run(str(root), "update", dev=True)  # 不应抛 SystemExit
        assert (root / "openspec" / "workflow" / "workflow.md").is_file()


class TestInitAlsoWarnsShadow:
    """B2-F3：陈旧遮蔽告警按磁盘状态触发——init 也要跑，不再只挂 update。"""

    def test_init_on_legacy_repo_warns_shadow(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "fake-claude"))
        root = tmp_path / "old"
        wf = root / "openspec" / "workflow"
        wf.mkdir(parents=True)
        (wf / "workflow.md").write_text("# old rules\n", encoding="utf-8")
        init_mod.run(str(root), "init")
        out = capsys.readouterr().out
        assert "遮蔽" in out


class TestCopyBundleConvergence:
    """B2-F4：非 full 模式下 tools/ 收敛——update 覆盖后，上游已删的旧文件不得残留。"""

    def test_update_clears_legacy_files_in_tools(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "fake-claude"))
        root = tmp_path / "proj"
        init_mod.run(str(root), "init")
        legacy = root / "openspec" / "workflow" / "tools" / "legacy-removed-upstream.txt"
        legacy.write_text("stale\n", encoding="utf-8")
        assert legacy.exists()
        init_mod.run(str(root), "update")
        assert not legacy.exists()


class TestRunFsErrorGuard:
    """B1-F2：run() 主体 FS 操作异常须走 _die 惯例，不裸抛 traceback。"""

    def test_readonly_root_dies_with_fs_error(self, tmp_path, monkeypatch, capsys):
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            pytest.skip("running as root — permission bits don't block writes")
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "fake-claude"))
        root = tmp_path / "proj"
        root.mkdir()
        root.chmod(0o500)
        try:
            with pytest.raises(SystemExit):
                init_mod.run(str(root), "init")
            err = capsys.readouterr().err
            assert "文件系统操作失败" in err
        finally:
            root.chmod(0o700)


class TestInjectMarkerMigration:
    """0.2：inject() 改 token 基定位——旧 marker 文案（opsx-project-init）区块被替换而非追加重复。"""

    OLD_BLOCK = ("<!-- opsx-init:start —— 由 opsx-project-init 维护，勿手改本区块 -->\n"
                 "旧内容\n<!-- opsx-init:end -->\n")

    def test_old_marker_block_replaced_not_duplicated(self, tmp_path):
        f = tmp_path / "CLAUDE.md"
        f.write_text("# 头\n\n" + self.OLD_BLOCK + "\n尾部用户内容\n", encoding="utf-8")
        init_mod.inject(str(f), *init_mod.MARK_DOC, "新内容")
        text = f.read_text(encoding="utf-8")
        assert text.count("opsx-init:start") == 1        # 只有一个区块（替换，非追加）
        assert "新内容" in text and "旧内容" not in text
        assert "sdflow-init 维护" in text                 # marker 文案已随替换更新
        assert "尾部用户内容" in text                     # 区块外内容无损

    def test_fresh_file_gets_new_marker(self, tmp_path):
        f = tmp_path / "CLAUDE.md"
        init_mod.inject(str(f), *init_mod.MARK_DOC, "内容", header="# H")
        assert "sdflow-init 维护" in f.read_text(encoding="utf-8")

    OLD_IDX_BLOCK = ("<!-- opsx-init:rules:start —— 由 opsx-project-init 维护，勿手改本区块 -->\n"
                     "旧内容\n<!-- opsx-init:rules:end -->\n")

    def test_old_idx_marker_block_replaced_not_duplicated(self, tmp_path):
        f = tmp_path / "INDEX.md"
        f.write_text("# 头\n\n" + self.OLD_IDX_BLOCK + "\n尾部用户内容\n", encoding="utf-8")
        init_mod.inject(str(f), *init_mod.MARK_IDX, "新内容")
        text = f.read_text(encoding="utf-8")
        assert text.count("opsx-init:rules:start") == 1   # 只有一个区块（替换，非追加）
        assert "新内容" in text and "旧内容" not in text
        assert "sdflow-init 维护" in text                 # marker 文案已随替换更新
        assert "尾部用户内容" in text                     # 区块外内容无损


class TestRetiredHooks:
    """ADR-1（drop-per-dir-review-stub）：init.py 需能反注册退役的全局 hook。
    hook 安装本是「只增不减」——退役一个 hook 时，存量安装的 ~/.claude/settings.json
    会留孤儿注册 + ~/.claude/hooks/ 残留脚本，之后每次 Bash 触发失败 hook。
    retire_hooks() 在 init/update 每次跑时自愈：外科式摘 settings.json 条目 + 删脚本。"""

    RETIRED = "change-review-stub.py"  # 当前退役名单里的 hook

    def _settings(self, home):
        return home / "settings.json"

    def _make_home_with_retired(self, home):
        """构造一个「装过退役 hook」的存量 home：脚本 + settings 注册；另含一个无关 hook (ff0)。"""
        (home / "hooks").mkdir(parents=True)
        (home / "hooks" / self.RETIRED).write_text("print('stub')\n", encoding="utf-8")
        (home / "hooks" / "ff0-branch-guard.py").write_text("print('ff0')\n", encoding="utf-8")
        self._settings(home).write_text(json.dumps({
            "hooks": {
                "PreToolUse": [{"matcher": "Bash", "hooks": [
                    {"type": "command", "command": 'python3 "$HOME/.claude/hooks/ff0-branch-guard.py"'}
                ]}],
                "PostToolUse": [{"matcher": "Bash", "hooks": [
                    {"type": "command", "command": 'python3 "$HOME/.claude/hooks/change-review-stub.py"'}
                ]}],
            }
        }), encoding="utf-8")

    def test_retires_existing_registration_and_script_keeping_others(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        self._make_home_with_retired(home)

        init_mod.retire_hooks()

        # 脚本删除
        assert not (home / "hooks" / self.RETIRED).exists()
        # settings 里退役 hook 的注册被摘除
        data = json.loads(self._settings(home).read_text(encoding="utf-8"))
        blob = json.dumps(data)
        assert "change-review-stub.py" not in blob
        # 无关 hook (ff0) 与其脚本保留
        assert "ff0-branch-guard.py" in blob
        assert (home / "hooks" / "ff0-branch-guard.py").exists()

    def test_fresh_install_is_noop(self, tmp_path, monkeypatch):
        """从未装过退役 hook 的 fresh 安装：只有 ff0，retire 全 no-op、不误删、不崩。"""
        home = tmp_path / "home"
        (home / "hooks").mkdir(parents=True)
        (home / "hooks" / "ff0-branch-guard.py").write_text("print('ff0')\n", encoding="utf-8")
        self._settings(home).write_text(json.dumps({
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": 'python3 "$HOME/.claude/hooks/ff0-branch-guard.py"'}
            ]}]}
        }), encoding="utf-8")
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))

        init_mod.retire_hooks()  # 不抛

        assert (home / "hooks" / "ff0-branch-guard.py").exists()
        data = json.loads(self._settings(home).read_text(encoding="utf-8"))
        assert len(data["hooks"]["PreToolUse"]) == 1

    def test_no_settings_file_still_deletes_script(self, tmp_path, monkeypatch):
        """settings.json 不存在，但 hooks/ 里残留退役脚本 → 删脚本、不崩。"""
        home = tmp_path / "home"
        (home / "hooks").mkdir(parents=True)
        (home / "hooks" / self.RETIRED).write_text("print('stub')\n", encoding="utf-8")
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))

        init_mod.retire_hooks()

        assert not (home / "hooks" / self.RETIRED).exists()

    def test_bad_json_settings_is_failsafe(self, tmp_path, monkeypatch):
        """settings.json 非法 JSON：反注册不崩（fail-safe），脚本删除照常进行。"""
        home = tmp_path / "home"
        (home / "hooks").mkdir(parents=True)
        (home / "hooks" / self.RETIRED).write_text("print('stub')\n", encoding="utf-8")
        self._settings(home).write_text("{ not valid json ", encoding="utf-8")
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))

        init_mod.retire_hooks()  # 不抛

        assert not (home / "hooks" / self.RETIRED).exists()

    def test_multiple_registrations_all_removed(self, tmp_path, monkeypatch):
        """退役 hook 被误注册多条（多个 entry）→ 全部摘除。"""
        home = tmp_path / "home"
        (home / "hooks").mkdir(parents=True)
        (home / "hooks" / self.RETIRED).write_text("print('stub')\n", encoding="utf-8")
        self._settings(home).write_text(json.dumps({
            "hooks": {"PostToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": 'python3 "$HOME/.claude/hooks/change-review-stub.py"'}]},
                {"matcher": "Bash", "hooks": [{"type": "command", "command": 'python3 "$HOME/.claude/hooks/change-review-stub.py"'}]},
            ]}
        }), encoding="utf-8")
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))

        init_mod.retire_hooks()

        data = json.loads(self._settings(home).read_text(encoding="utf-8"))
        assert "change-review-stub.py" not in json.dumps(data)

    def test_malformed_non_dict_hook_element_does_not_crash(self, tmp_path, monkeypatch):
        """[impl-review-fix] CR-F1：hooks 列表混入非 dict truthy 元素（字符串等）时，
        反注册 MUST fail-safe 不抛（旧实现 `(h or {}).get` 会 AttributeError 冒穿崩 init/update）。"""
        home = tmp_path / "home"
        (home / "hooks").mkdir(parents=True)
        (home / "hooks" / self.RETIRED).write_text("print('stub')\n", encoding="utf-8")
        self._settings(home).write_text(json.dumps({
            "hooks": {"PostToolUse": [{"matcher": "Bash", "hooks": [
                "not-a-dict-entry",
                {"type": "command", "command": 'python3 "$HOME/.claude/hooks/change-review-stub.py"'},
            ]}]}
        }), encoding="utf-8")
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))

        init_mod.retire_hooks()  # 不抛

        data = json.loads(self._settings(home).read_text(encoding="utf-8"))
        blob = json.dumps(data)
        assert "change-review-stub.py" not in blob   # 退役项摘除
        assert "not-a-dict-entry" in blob            # 畸形非 dict 元素原样保留、未误删

    def test_non_string_command_does_not_crash(self, tmp_path, monkeypatch):
        """[impl-review-fix] CR-F1：command 字段是非字符串 truthy 值（如 int）时不得
        `TypeError`（`name not in 123` 崩溃）；应视为不匹配、原样保留。"""
        home = tmp_path / "home"
        (home / "hooks").mkdir(parents=True)
        (home / "hooks" / self.RETIRED).write_text("print('stub')\n", encoding="utf-8")
        self._settings(home).write_text(json.dumps({
            "hooks": {"PostToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": 123},
                {"type": "command", "command": 'python3 "$HOME/.claude/hooks/change-review-stub.py"'},
            ]}]}
        }), encoding="utf-8")
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))

        init_mod.retire_hooks()  # 不抛

        data = json.loads(self._settings(home).read_text(encoding="utf-8"))
        blob = json.dumps(data)
        assert "change-review-stub.py" not in blob   # 退役项摘除
        assert "123" in blob                         # 非 str command 条目原样保留

    def test_mixed_entry_keeps_sibling_hook(self, tmp_path, monkeypatch):
        """一个 matcher entry 内同时含退役 hook 与另一 hook → 只摘退役、保留兄弟、entry 不空则留。"""
        home = tmp_path / "home"
        (home / "hooks").mkdir(parents=True)
        (home / "hooks" / self.RETIRED).write_text("print('stub')\n", encoding="utf-8")
        self._settings(home).write_text(json.dumps({
            "hooks": {"PostToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": 'python3 "$HOME/.claude/hooks/change-review-stub.py"'},
                {"type": "command", "command": 'python3 "$HOME/.claude/hooks/other-tool.py"'},
            ]}]}
        }), encoding="utf-8")
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))

        init_mod.retire_hooks()

        data = json.loads(self._settings(home).read_text(encoding="utf-8"))
        blob = json.dumps(data)
        assert "change-review-stub.py" not in blob
        assert "other-tool.py" in blob


class TestRetireHooksCli:
    """T44: `init.py retire-hooks` 独立 mode——只调 retire_hooks()，不需 openspec/。"""

    def test_retire_hooks_mode_cleans_stale_hook(self, tmp_path, monkeypatch, capsys):
        home = tmp_path / "home"
        (home / "hooks").mkdir(parents=True)
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        (home / "hooks" / "change-review-stub.py").write_text("# stale\n", encoding="utf-8")
        (home / "settings.json").write_text(json.dumps({"hooks": {"PostToolUse": [
            {"matcher": "Bash", "hooks": [
                {"type": "command", "command": 'python3 "$HOME/.claude/hooks/change-review-stub.py"'}]}
        ]}}), encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["init.py", "retire-hooks"])
        init_mod.main()
        assert not (home / "hooks" / "change-review-stub.py").exists()
        data = json.loads((home / "settings.json").read_text(encoding="utf-8"))
        assert data["hooks"]["PostToolUse"] == []
        assert "change-review-stub.py" in capsys.readouterr().out

    def test_retire_hooks_mode_needs_no_openspec(self, tmp_path, monkeypatch, capsys):
        home = tmp_path / "home"; home.mkdir()
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["init.py", "retire-hooks"])
        init_mod.main()
        assert "无退役 hook 残留" in capsys.readouterr().out
