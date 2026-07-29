"""config-lint（mlh-p3-determ-guards Task 2）：openspec/config.yaml 结构 fail-closed 校验门。
只校验结构（schema 顶层键存在 / rules 四子键 / model-tiers 枚举 / metrics.enabled 布尔），
不碰内容文案。手写 stdlib 行扫描（follow anchor_lint.py::read_metrics_enabled 范式，不 import yaml）。
顶层块（model-tiers / metrics）缺失一律条件化放行（防 mlh-p2 假阳，见 memory
dogfood-blind-spot-source-config）。

Run: python3 -m pytest sdflow-init/tests/test_config_lint.py -v
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent / "fixtures"))

from model_tiers_cases import CASES as MODEL_TIERS_CASES  # noqa: E402  共享畸形输入语料，见该文件 docstring

REPO_ROOT = Path(__file__).parent.parent.parent
INIT_PY = Path(__file__).parent.parent / "scripts" / "init.py"


def _write_config(root: Path, content: str):
    osdir = root / "openspec"
    osdir.mkdir(parents=True, exist_ok=True)
    (osdir / "config.yaml").write_text(content, encoding="utf-8")


def _run_lint(root):
    return subprocess.run(
        ["python3", str(INIT_PY), "config-lint", "--root", str(root)],
        capture_output=True, text=True,

        encoding="utf-8",
        errors="replace",)


VALID_RULES_BLOCK = """schema: spec-driven
rules:
  proposal:
    - a
  specs:
    - b
  design:
    - c
  tasks:
    - d
"""


class TestConfigLintBadStructure:
    def test_missing_schema_and_rules_nonzero_with_reason(self, tmp_path):
        _write_config(tmp_path, "foo: bar\n")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "schema" in r.stderr
        assert "rules" in r.stderr


class TestConfigLintMissingRuleSubkey:
    def test_missing_rules_proposal_nonzero(self, tmp_path):
        _write_config(tmp_path, """schema: spec-driven
rules:
  specs:
    - b
  design:
    - c
  tasks:
    - d
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "proposal" in r.stderr


class TestConfigLintModelTiers:
    def test_out_of_domain_subkey_nonzero(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK + """model-tiers:
  strong: some-model
  mid: another-model
  bogus: nope
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "model-tiers" in r.stderr
        assert "bogus" in r.stderr

    def test_no_model_tiers_block_passes(self, tmp_path):
        """条件化放行：无 model-tiers 块 → 0（消费仓正常态，非违规）。"""
        _write_config(tmp_path, VALID_RULES_BLOCK)
        r = _run_lint(tmp_path)
        assert r.returncode == 0, r.stderr


class TestConfigLintModelTiersFleetKeyed:
    """add-codex-host-support ADR-8：model-tiers 覆盖按机队分键 `{claude,codex}.{strong,mid,light}`，
    扁平旧格式 `{strong,mid,light}` 兼容。"""

    def test_nested_fleet_keyed_valid_passes(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK + """model-tiers:
  claude:
    strong: some-claude-model
    mid: another-claude-model
  codex:
    strong: some-codex-model
""")
        r = _run_lint(tmp_path)
        assert r.returncode == 0, r.stderr

    def test_flat_legacy_valid_passes(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK + """model-tiers:
  strong: legacy-model
""")
        r = _run_lint(tmp_path)
        assert r.returncode == 0, r.stderr

    def test_fleet_leaf_out_of_domain_subkey_nonzero(self, tmp_path):
        """机队子块下的三级叶子键越域（如 claude.bogus）也须报错——config_lint 是 fail-closed
        结构门，比 resolve-models.sh（对未知叶子键静默跳过、best-effort）更严格。"""
        _write_config(tmp_path, VALID_RULES_BLOCK + """model-tiers:
  claude:
    strong: ok-model
    bogus: nope
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "claude.bogus" in r.stderr

    def test_top_level_out_of_domain_subkey_with_fleet_header_nonzero(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK + """model-tiers:
  claude:
    strong: ok-model
  weird:
    strong: nope
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "weird" in r.stderr

    def test_nested_invalid_model_id_value_nonzero(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK + """model-tiers:
  claude:
    strong: $(touch pwned)
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "claude.strong" in r.stderr

    def test_flat_invalid_model_id_value_nonzero(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK + """model-tiers:
  mid: `touch pwned`
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "flat.mid" in r.stderr

    def test_empty_value_nonzero(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK + """model-tiers:
  codex:
    light:
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "codex.light" in r.stderr


class TestConfigLintModelTiersSharedFixture:
    """跨工具一致性守（design D10）：本文件与 test_resolve_models.py 从同一份
    `fixtures/model_tiers_cases.py` 语料驱动，断言 config_lint 侧的 accept/reject 判据。"""

    def test_shared_cases_match_lint_expectation(self, tmp_path):
        for case in MODEL_TIERS_CASES:
            root = tmp_path / case["name"]
            _write_config(root, VALID_RULES_BLOCK + case["yaml_block"])
            r = _run_lint(root)
            if case["lint_clean"]:
                assert r.returncode == 0, f"{case['name']}: expected clean, got {r.stderr}"
            else:
                assert r.returncode != 0, f"{case['name']}: expected violation, got clean"
                for substr in case["lint_reason_substrs"]:
                    assert substr in r.stderr, f"{case['name']}: missing {substr!r} in {r.stderr}"


class TestConfigLintLeafMissingColonNoPoison:
    """Task 6 复评 r2 Important：叶子层漏冒号笔误 MUST NOT 毒化整个 fleet 块——后续合法叶子
    仍须被 attribute + validate（fail-closed 结构门不被一个笔误整段静默放行）。"""

    def test_missing_colon_does_not_poison_following_leaf_validation(self, tmp_path):
        """漏冒号 strong 行之后的 `mid: <非法值>` MUST 被校验到——证明 fleet_ctx 未被毒化成 None。
        若毒化（老 bug），mid 从不 attribute ⇒ 非法值静默放行 ⇒ stderr 无 claude.mid。"""
        _write_config(tmp_path, VALID_RULES_BLOCK + """model-tiers:
  claude:
    strong opus
    mid: bad$value
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "claude.mid" in r.stderr, f"漏冒号毒化了后续 mid 叶子的校验: {r.stderr}"


class TestParseModelTiersBlockAttribution:
    """白盒锁（直测 `_parse_model_tiers_block` 的 entries 归属）——config_lint 只对外报违规
    存在性，无法从 CLI 侧观察「后续叶子归给了哪个 fleet」。这两条直测 entries dict，锁住两处
    与 resolver 同口径的关键 reset/sustain 行为（防未来重构悄悄回归、成无测试锁的死码）。"""

    @staticmethod
    def _parse(yaml_block):
        import init  # scripts/ 已在 sys.path（本文件顶部 line 14）
        lines = (VALID_RULES_BLOCK + yaml_block).splitlines()
        blk = init._find_top_level_block(lines, "model-tiers")
        return init._parse_model_tiers_block(lines, *blk)

    def test_missing_colon_leaf_sustains_fleet_attribution(self):
        """漏冒号叶子后的合法叶子仍归当前 fleet（entries 含 claude.mid），fleet_ctx 未被毒化。"""
        entries, bad, bad_headers = self._parse(
            "model-tiers:\n  claude:\n    strong opus\n    mid: sonnet-real\n")
        assert entries.get("claude.mid") == "sonnet-real", entries
        # 漏冒号那行被记 bad（config_lint 更严格），但不清空后续归属
        assert any("strong opus" in b for b in bad), bad

    def test_trailing_content_header_resets_fleet_no_crosstalk(self):
        """`claude: rogue`（带值畸形头）后的叶子 MUST NOT 归前一个 fleet（codex）——reset 生效。
        锁住 bad_headers 分支的 fleet_ctx=None（防其成无测试的死码/串扰回归）。"""
        entries, bad, bad_headers = self._parse(
            "model-tiers:\n  codex:\n    strong: codex-real\n  claude: rogue\n    strong: claude-leak\n")
        assert entries.get("codex.strong") == "codex-real", entries
        # claude-leak MUST NOT 覆盖 codex.strong（若 reset 缺失，stale codex fleet 会把它读进 codex）
        assert entries.get("codex.strong") != "claude-leak", entries
        assert any("claude: rogue" in h for h in bad_headers), bad_headers


class TestConfigLintMetrics:
    def test_metrics_enabled_non_bool_nonzero(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK + """metrics:
  enabled: yes-please
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "metrics" in r.stderr
        assert "enabled" in r.stderr

    def test_no_metrics_block_passes_consumer_style_fixture(self, tmp_path):
        """mlh-p2 假阳防护（M3）：消费仓风格 config——metrics 块整段不存在（sdflow-init update
        从不注入新顶层键，故 100% 存量消费仓无 metrics 块）→ 必须放行 exit 0，不得裸
        KeyError/误判违规。"""
        _write_config(tmp_path, """schema: spec-driven
context: |
  ## 本项目
  consumer repo, unrelated tech stack context prose.
""" + VALID_RULES_BLOCK.split("\n", 1)[1])
        r = _run_lint(tmp_path)
        assert r.returncode == 0, r.stderr


class TestConfigLintRegressionBaseline:
    def test_real_repo_config_yaml_passes(self):
        """回归基线：本仓真实 openspec/config.yaml（含 metrics: enabled: true，注释掉的
        model-tiers）必须 lint 通过。"""
        r = _run_lint(REPO_ROOT)
        assert r.returncode == 0, r.stderr


class TestConfigLintEncodingError:
    """[impl-review-fix] F2：`lint_config` 此前只 `except OSError`——非 UTF-8 config.yaml
    会让 `f.read()` 抛 `UnicodeDecodeError`，未被捕获、以裸 traceback 崩溃（不是干净的
    reason + 非零退出）。补捕获 `UnicodeDecodeError`，与 anchor_lint.py 的既有范式
    （read_metrics_enabled / load_enums 同款 `except (OSError, UnicodeDecodeError)`）对齐。"""

    def test_non_utf8_config_yaml_clean_reason_nonzero(self, tmp_path):
        osdir = tmp_path / "openspec"
        osdir.mkdir(parents=True)
        (osdir / "config.yaml").write_bytes(
            b"schema: spec-driven\nrules:\n  proposal:\n\xff\xfe bad bytes here \n"
        )
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "Traceback" not in r.stderr
        assert "config.yaml" in r.stderr


class TestConfigLintMissingFile:
    """补测（minor polish）：config.yaml 整个文件不存在（连 openspec/ 目录都没有）时，
    `lint_config` 走 `except OSError` 分支报干净 reason + 非零退出，不裸 KeyError/FileNotFoundError。"""

    def test_missing_config_yaml_clean_reason_nonzero(self, tmp_path):
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "Traceback" not in r.stderr
        assert "config.yaml" in r.stderr


class TestConfigLintGitRootAutoProbe:
    """补测（minor polish）：`--root` 省略时走 `_git_root_or_dot()` 自动探测 git 仓根——
    在本仓任意子目录下裸跑 `config-lint`（不传 --root）应能探到仓根并 lint 通过（本仓
    真实 config.yaml 干净）。"""

    def test_no_root_flag_probes_git_root(self):
        r = subprocess.run(
            ["python3", str(INIT_PY), "config-lint"],
            capture_output=True, text=True, cwd=str(REPO_ROOT / "sdflow-init"),

            encoding="utf-8",
            errors="replace",)
        assert r.returncode == 0, r.stderr


class TestConfigLintCliSmoke:
    """adv-A 爆点2：config-lint 加进 mode choices 后，既有 3 个 mode（init/update/
    retire-hooks）的 argparse 解析 + 实际执行不受扰动（未误引入 add_subparsers 重构）。"""

    def test_existing_modes_still_run(self, tmp_path):
        env = dict(os.environ)
        env["CLAUDE_CONFIG_DIR"] = str(tmp_path / "fake-claude")
        project = tmp_path / "proj"
        project.mkdir()

        r_init = subprocess.run(
            ["python3", str(INIT_PY), "init", "--root", str(project)],
            capture_output=True, text=True, env=env,

            encoding="utf-8",
            errors="replace",)
        assert r_init.returncode == 0, r_init.stderr
        assert (project / "openspec" / "config.yaml").is_file()

        r_update = subprocess.run(
            ["python3", str(INIT_PY), "update", "--root", str(project)],
            capture_output=True, text=True, env=env,

            encoding="utf-8",
            errors="replace",)
        assert r_update.returncode == 0, r_update.stderr

        r_retire = subprocess.run(
            ["python3", str(INIT_PY), "retire-hooks"],
            capture_output=True, text=True, env=env,

            encoding="utf-8",
            errors="replace",)
        assert r_retire.returncode == 0, r_retire.stderr
