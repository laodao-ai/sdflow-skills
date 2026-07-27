"""
Tests for init.py's bundle deployment, retired-file/hook cleanup, and hook installer.
Run with: python3 -m pytest sdflow-init/tests/test_init.py -v
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import init as init_mod
from init import copy_bundle, retire_deploy_files


class TestRetireDeployFiles:
    """drop-review-html-viewer：曾铺进消费仓 openspec/ 根的查看器根锚（serve.sh + review.html）
    在 init/update 每次运行时被**签名门控删除**；用户自建同名文件（无 bundle 签名）不被误删；
    fresh 安装（无残留）则 no-op。与 retire_hooks 同构。"""

    def _write(self, root, rel, content):
        osroot = root / "openspec"
        osroot.mkdir(parents=True, exist_ok=True)
        p = osroot / rel
        p.write_text(content, encoding="utf-8")
        return p

    def test_removes_deployed_viewer_anchors(self, tmp_path):
        # 复刻 bundle 部署签名：review.html 含渲染 token 的宿主变量名、serve.sh 含 PIDFILE key 前缀
        review = self._write(tmp_path, "review.html",
                             '<script>window.__OPENSPEC_PROJECT_NAME__ = "x";</script>')
        serve = self._write(tmp_path, "serve.sh",
                            'PIDFILE="/tmp/openspec-review-serve-${KEY}.pid"\n')
        acts = retire_deploy_files(str(tmp_path))
        assert not review.exists()
        assert not serve.exists()
        assert "review.html" in acts and "serve.sh" in acts

    def test_skips_user_files_without_signature(self, tmp_path):
        # 用户自建同名文件，内容不含 bundle 签名 → MUST NOT 删
        review = self._write(tmp_path, "review.html", "# my own notes about a review\n")
        serve = self._write(tmp_path, "serve.sh", "#!/bin/sh\necho my own server\n")
        acts = retire_deploy_files(str(tmp_path))
        assert review.exists() and serve.exists()
        assert acts.strip() == "· 无退役部署文件残留"

    def test_noop_on_fresh_install(self, tmp_path):
        (tmp_path / "openspec").mkdir()
        acts = retire_deploy_files(str(tmp_path))
        assert acts.strip() == "· 无退役部署文件残留"

    def test_idempotent(self, tmp_path):
        self._write(tmp_path, "review.html",
                    '<script>window.__OPENSPEC_PROJECT_NAME__ = "x";</script>')
        retire_deploy_files(str(tmp_path))
        acts2 = retire_deploy_files(str(tmp_path))   # 第二次跑：已删净 → no-op
        assert acts2.strip() == "· 无退役部署文件残留"

    def test_run_retires_deployed_viewer(self, tmp_path, monkeypatch):
        # 端到端：run(update) 应清掉已铺的查看器根锚
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "fake-claude"))
        proj = tmp_path / "proj"
        (proj / "openspec").mkdir(parents=True)
        (proj / "openspec" / "review.html").write_text(
            '<script>window.__OPENSPEC_PROJECT_NAME__ = "x";</script>', encoding="utf-8")
        (proj / "openspec" / "serve.sh").write_text(
            'PIDFILE="/tmp/openspec-review-serve-${KEY}.pid"\n', encoding="utf-8")
        init_mod.run(str(proj), "update")
        assert not (proj / "openspec" / "review.html").exists()
        assert not (proj / "openspec" / "serve.sh").exists()


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
        assert (wf / "tools" / "anchor_lint.py").is_file()   # 机械层脚本随 tools/ 部署
        # 查看器资产已移除（drop-review-html-viewer）——tools/ 下不再含 HTML 查看器文件
        assert not (wf / "tools" / "engine.js").exists()
        assert not (wf / "tools" / "review-stub.html").exists()
        assert not (wf / "tools" / "vendor").exists()
        assert not (wf / "workflow.md").exists()
        assert not (wf / "spec-checklists").exists()
        assert not (wf / "code-checklists").exists()
        # 两个非规则的 .md 显式豁免：
        # [mlh-p2-anchor-lint] lens-metric-contract.md —— tools/anchor_lint.py 的运行时机读依赖
        #   （读 lens-metric-enums 块），须与 tools/ 同批铺。
        # WORKFLOW-GUIDE.md —— 【给人看的】完整手册（每步 prompt 全文内联），是
        #   hack/gen_workflow_guide.py 的【生成物】而非真相源（单一源仍是 prompts/ + workflow.md，
        #   都在全局 canonical，不铺进消费仓）。规则走 canonical，但【人】需要一份随仓走、
        #   不用跳文件的完整参考 —— 拷过来的是产物，不是新的真相源。
        EXEMPT = {"lens-metric-contract.md", "WORKFLOW-GUIDE.md"}
        md_rules = [p for p in wf.rglob("*.md")
                    if "tools" not in p.parts and p.name not in EXEMPT]
        assert md_rules == []                      # 规则文件数 = 0（两个豁免除外）
        assert (wf / "lens-metric-contract.md").is_file()
        assert (wf / "WORKFLOW-GUIDE.md").is_file()

        # 🔴 规则本体 MUST NOT 被铺进来 —— 它们走全局 canonical（改了即时生效，无需 update）
        assert not (wf / "workflow.md").exists()
        assert not (wf / "prompts").exists()

    def test_full_flag_restores_whole_bundle(self, tmp_path):
        init_mod.copy_bundle(str(tmp_path), full=True)
        wf = tmp_path / "openspec" / "workflow"
        assert (wf / "workflow.md").is_file()      # --dev 整刷用（Task 7）

    def test_tools_tests_not_deployed_to_consumer(self, tmp_path):
        """[impl-review-fix CF-6]：tools/tests/（tools/ 脚本的内部 pytest，如
        test_trivial_shape.py）不得铺进消费仓——只污染其 pytest 收集，无实际用途。
        脚本本体（trivial_shape.py）仍照常部署。"""
        dst, _ = copy_bundle(str(tmp_path))
        tools_dst = Path(dst) / "tools"
        assert (tools_dst / "trivial_shape.py").is_file()
        assert not (tools_dst / "tests").exists()

    def test_full_flag_excludes_tools_tests(self, tmp_path):
        """--dev dogfood instance 是派生产物，不能复制 toolkit 自测。"""
        init_mod.copy_bundle(str(tmp_path), full=True)
        wf = tmp_path / "openspec" / "workflow"
        assert not (wf / "tools" / "tests").exists()

    def test_full_flag_prunes_legacy_tools_tests(self, tmp_path):
        """重复 --dev update 也要移除旧版留下的测试副本。"""
        stale = tmp_path / "openspec" / "workflow" / "tools" / "tests"
        stale.mkdir(parents=True)
        (stale / "test_stale.py").write_text("# stale\n", encoding="utf-8")
        init_mod.copy_bundle(str(tmp_path), full=True)
        assert not stale.exists()

    def test_full_flag_preserves_tests_outside_tools(self, tmp_path, monkeypatch):
        """只排除 tools/tests，bundle 其他层级的 tests 是正常运行时资产。"""
        source = tmp_path / "bundle"
        (source / "tools" / "tests").mkdir(parents=True)
        (source / "tools" / "tests" / "test_internal.py").write_text("# toolkit test\n", encoding="utf-8")
        (source / "references" / "tests").mkdir(parents=True)
        expected = source / "references" / "tests" / "fixture.md"
        expected.write_text("runtime fixture\n", encoding="utf-8")
        monkeypatch.setattr(init_mod, "BUNDLE_SRC", str(source))

        init_mod.copy_bundle(str(tmp_path / "target"), full=True)

        workflow = tmp_path / "target" / "openspec" / "workflow"
        assert not (workflow / "tools" / "tests").exists()
        assert (workflow / "references" / "tests" / "fixture.md").read_text(encoding="utf-8") == "runtime fixture\n"


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

    def test_nested_managed_content_keeps_separator_after_outer_marker(self, tmp_path):
        """--dev update 不得破坏 sync_principles 的 canonical 空行布局。"""
        f = tmp_path / "CLAUDE.md"
        nested = "<!-- sdflow:principles:start -->\n通则\n<!-- sdflow:principles:end -->"
        init_mod.inject(str(f), *init_mod.MARK_DOC, nested)
        assert f"{init_mod.MARK_DOC[0]}\n\n{nested}" in f.read_text(encoding="utf-8")

    def test_ordinary_index_content_has_no_nested_separator(self, tmp_path):
        """普通 MARK_IDX 内容不能因 nested 专用格式化而多出空行。"""
        f = tmp_path / "INDEX.md"
        init_mod.inject(str(f), *init_mod.MARK_IDX, "## 索引\n")
        assert f.read_text(encoding="utf-8") == (
            f"{init_mod.MARK_IDX[0]}\n## 索引\n{init_mod.MARK_IDX[1]}\n"
        )

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

    def test_settings_write_is_atomic_no_tmp_residue(self, tmp_path, monkeypatch):
        home = tmp_path / "home"; (home / "hooks").mkdir(parents=True)
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        settings = home / "settings.json"
        settings.write_text(json.dumps({"hooks": {"PostToolUse": [
            {"matcher": "Bash", "hooks": [
                {"type": "command", "command": 'python3 "$HOME/.claude/hooks/change-review-stub.py"'}]}
        ]}}), encoding="utf-8")
        assert init_mod._deregister_hook_in_settings(str(settings), "change-review-stub.py") is True
        json.loads(settings.read_text(encoding="utf-8"))   # 合法 JSON = 未撕裂
        assert list(home.glob("*.tmp")) == []              # 无 .tmp 残渣

    def test_deregister_write_failsafe_on_oserror(self, tmp_path, monkeypatch):
        # FB-3: 写路径 OSError（只读/满盘/权限）→ fail-safe 返回 False，不裸抛 traceback、不中断循环
        home = tmp_path / "home"; (home / "hooks").mkdir(parents=True)
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        settings = home / "settings.json"
        settings.write_text(json.dumps({"hooks": {"PostToolUse": [
            {"matcher": "Bash", "hooks": [
                {"type": "command", "command": 'python3 "$HOME/.claude/hooks/change-review-stub.py"'}]}
        ]}}), encoding="utf-8")
        monkeypatch.setattr(init_mod.os, "replace",
                            lambda *a, **k: (_ for _ in ()).throw(OSError("readonly")))
        assert init_mod._deregister_hook_in_settings(str(settings), "change-review-stub.py") is False
