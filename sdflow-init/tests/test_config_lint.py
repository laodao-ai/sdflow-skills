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

import pytest

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
        # 反引号在真 YAML 语法下是 "found character that cannot start any token"——整份文档
        # 解析失败，不再是 config_lint 精确点名到 flat.mid 的语义校验（yq 迁移的既定诊断精度
        # 代价，见 model_tiers_cases.py 文件头 Task 4 说明）。
        assert "解析失败" in r.stderr

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


class TestConfigLintWholeDocumentParseFailure:
    """shared-yaml-subset-parser 迁 yq 之后的行为变化（见 impl-report task4-init-yq.md）：
    旧版行扫描器能局部容错「叶子层漏冒号笔误」，之后合法叶子仍被 attribute+validate
    （Task 6 复评 r2 Important 的原始诉求）。yq 是真 YAML 解析器——`strong opus`（无冒号的
    裸标量行，出现在期望是 mapping 的上下文里）是**语法级非法 YAML**
    （`mapping values are not allowed in this context`），会让**整份 config.yaml**
    解析失败，不再有「局部容错、后续叶子仍被校验」这件事——`claude.mid` 后续叶子根本读不到，
    因为文档级读取（`_yq('.', cfg_path)`）本身就失败了。这不是本次改动引入的新缺陷，而是
    yq 委托的既定代价（spec-review F9/decision-memo：诊断精度下降换取「不手搓 YAML 解析器」）。"""

    def test_missing_colon_leaf_is_a_whole_document_parse_failure(self, tmp_path):
        """漏冒号叶子行 MUST 被 yq 判定整份文档语法错误（非零退出 + 通用「解析失败」reason），
        MUST NOT 静默放行、也不再有精确到 `claude.mid` 的局部诊断。"""
        _write_config(tmp_path, VALID_RULES_BLOCK + """model-tiers:
  claude:
    strong opus
    mid: bad$value
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "解析失败" in r.stderr, r.stderr


class TestModelTiersFromDict:
    """白盒锁（直测 `_model_tiers_from_dict` 的 entries/bad_headers 归属）——config_lint 只对外
    报违规存在性，无法从 CLI 侧观察「叶子归给了哪个 fleet」。语法层已交给 yq；本函数只处理
    yq 已解析出的 dict，故这里直接构造 Python dict 输入（不再需要构造原始 YAML 文本行）。"""

    @staticmethod
    def _parse(raw):
        import init  # scripts/ 已在 sys.path（本文件顶部 line 14）
        return init._model_tiers_from_dict(raw)

    def test_fleet_and_flat_entries_attributed_correctly(self):
        entries, bad, bad_headers = self._parse(
            {"claude": {"strong": "opus", "mid": "sonnet"}, "codex": {"strong": "gpt"}})
        assert entries == {"claude.strong": "opus", "claude.mid": "sonnet", "codex.strong": "gpt"}
        assert not bad and not bad_headers

    def test_scalar_fleet_header_is_bad_header_no_crosstalk(self):
        """`claude: rogue`（fleet 名当标量误用，值非 dict）MUST 记 bad_headers，且 MUST NOT
        产生任何 `claude.*` entries——锁住 bad_headers 分支（防其成无测试的死码/回归）。"""
        entries, bad, bad_headers = self._parse(
            {"codex": {"strong": "codex-real"}, "claude": "rogue"})
        assert entries == {"codex.strong": "codex-real"}
        assert any("claude: rogue" in h for h in bad_headers), bad_headers

    def test_none_leaf_value_maps_to_empty_string(self):
        """yq 对空值叶子（如 `light:`）给出 None——须映射为空串以保留旧版
        「空值即无效模型ID」语义（`_valid_model_id("")` 恒 False）。"""
        entries, bad, bad_headers = self._parse({"codex": {"light": None}})
        assert entries == {"codex.light": ""}


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


class TestConfigLintEffortTiers:
    """implement-workflow-optimization-2026-08-p4：effort-tiers 顶层块——**仅** `claude.{strong,
    mid,light}`（codex 无 effort 原语、无扁平旧格式），叶子值须 ∈ {low,medium,high,xhigh,max}。"""

    def test_no_effort_tiers_block_passes(self, tmp_path):
        """条件化放行：无 effort-tiers 块 → 0（消费仓正常态，非违规）。"""
        _write_config(tmp_path, VALID_RULES_BLOCK)
        r = _run_lint(tmp_path)
        assert r.returncode == 0, r.stderr

    def test_valid_claude_block_passes(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK + """effort-tiers:
  claude:
    strong: high
    mid: medium
    light: low
""")
        r = _run_lint(tmp_path)
        assert r.returncode == 0, r.stderr

    def test_all_domain_values_accepted(self, tmp_path):
        for val in ("low", "medium", "high", "xhigh", "max"):
            root = tmp_path / val
            _write_config(root, VALID_RULES_BLOCK + f"""effort-tiers:
  claude:
    mid: {val}
""")
            r = _run_lint(root)
            assert r.returncode == 0, f"{val}: {r.stderr}"

    def test_codex_key_is_out_of_domain(self, tmp_path):
        """codex 无 effort 原语——`effort-tiers.codex.*` MUST 报越域，不得像 model-tiers 那样
        被当成合法机队键静默接受。"""
        _write_config(tmp_path, VALID_RULES_BLOCK + """effort-tiers:
  codex:
    strong: high
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "effort-tiers" in r.stderr
        assert "codex" in r.stderr

    def test_flat_legacy_format_is_out_of_domain(self, tmp_path):
        """effort-tiers 无扁平旧格式（与 model-tiers 不同，无历史遗留包袱）——顶层直接写
        `strong:`/`mid:`/`light:`（无 `claude:` 机队头）MUST 报越域，不得被静默接受为 flat 覆盖。"""
        _write_config(tmp_path, VALID_RULES_BLOCK + """effort-tiers:
  strong: high
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "effort-tiers" in r.stderr
        assert "strong" in r.stderr

    def test_fleet_leaf_out_of_domain_subkey_nonzero(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK + """effort-tiers:
  claude:
    strong: high
    bogus: nope
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "claude.bogus" in r.stderr

    def test_invalid_effort_value_nonzero(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK + """effort-tiers:
  claude:
    mid: turbo
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "effort-tiers" in r.stderr
        assert "claude.mid" in r.stderr

    def test_model_id_style_value_rejected(self, tmp_path):
        """effort-tiers 值域是封闭集合，不是 model-tiers 那种自由字符集——一个合法的 model-id
        字符集字符串（如 `sonnet`）不在 effort 值域内，MUST 被拒绝，不得因两者校验函数
        混用而误放行。"""
        _write_config(tmp_path, VALID_RULES_BLOCK + """effort-tiers:
  claude:
    strong: sonnet
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "claude.strong" in r.stderr

    def test_empty_value_nonzero(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK + """effort-tiers:
  claude:
    light:
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "claude.light" in r.stderr

    def test_scalar_fleet_header_nonzero(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK + """effort-tiers:
  claude: rogue
""")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "effort-tiers" in r.stderr


class TestEffortTiersFromDict:
    """白盒锁（直测 `_effort_tiers_from_dict` 的 entries/bad/bad_headers 归属），同
    `TestModelTiersFromDict` 的测法——语法层交给 yq，本函数只处理已解析出的 dict。"""

    @staticmethod
    def _parse(raw):
        import init  # scripts/ 已在 sys.path（本文件顶部）
        return init._effort_tiers_from_dict(raw)

    def test_claude_entries_attributed_correctly(self):
        entries, bad, bad_headers = self._parse({"claude": {"strong": "high", "mid": "medium"}})
        assert entries == {"claude.strong": "high", "claude.mid": "medium"}
        assert not bad and not bad_headers

    def test_codex_key_goes_to_bad_not_entries(self):
        """与 `_model_tiers_from_dict` 的关键差异：`codex` 不在 `EFFORT_FLEET_KEYS` 里，
        整个 `codex: {...}` 块须落 `bad`（越域顶层键），MUST NOT 产生任何 `codex.*` entries。"""
        entries, bad, bad_headers = self._parse(
            {"claude": {"strong": "high"}, "codex": {"strong": "high"}})
        assert entries == {"claude.strong": "high"}
        assert "codex" in bad
        assert not bad_headers

    def test_flat_top_level_keys_go_to_bad_not_entries(self):
        """与 `_model_tiers_from_dict` 的关键差异：无扁平兼容分支——顶层 `strong`/`mid`/`light`
        （无 `claude:` 头）MUST NOT 落进 `entries["flat.*"]`，而是落 `bad`。"""
        entries, bad, bad_headers = self._parse({"strong": "high", "mid": "medium"})
        assert entries == {}
        assert bad == {"strong", "mid"}

    def test_scalar_fleet_header_is_bad_header_no_crosstalk(self):
        entries, bad, bad_headers = self._parse({"claude": "rogue"})
        assert entries == {}
        assert any("claude: rogue" in h for h in bad_headers), bad_headers

    def test_none_leaf_value_maps_to_empty_string(self):
        entries, bad, bad_headers = self._parse({"claude": {"light": None}})
        assert entries == {"claude.light": ""}


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


class TestYqWrapper:
    """直测 `_yq()`/`_check_yq()` 本体（shared-yaml-subset-parser Task 4）——config-lint 的
    CLI 断言只能间接观察 yq 委托的效果，这里直接锁住薄封装自身的关键契约：default 分支、
    非零退出 raise、未安装/非 mikefarah 时 fail-loud，与 anchor_lint.py 已落地的同类用例
    对齐（design.md §1 参考实现的核验面）。"""

    def _mod(self):
        """每次都用一个独立的模块实例，避免 `_yq_bin` 进程内缓存跨用例互相污染
        （同 anchor_lint.py 的 test_anchor_lint.py 既有范式）。"""
        import importlib
        import init as init_mod_local
        return importlib.reload(init_mod_local)

    def test_yq_default_for_missing_key(self, tmp_path):
        mod = self._mod()
        cfg = tmp_path / "x.yaml"
        cfg.write_text("schema: spec-driven\n", encoding="utf-8")
        assert mod._yq(".nope", str(cfg), default="fallback") == "fallback"

    def test_yq_reads_typed_value(self, tmp_path):
        mod = self._mod()
        cfg = tmp_path / "x.yaml"
        cfg.write_text("metrics:\n  enabled: true\n", encoding="utf-8")
        assert mod._yq(".metrics.enabled", str(cfg)) is True

    def test_yq_raises_on_nonzero_exit(self, tmp_path):
        mod = self._mod()
        cfg = tmp_path / "bad.yaml"
        cfg.write_text('key: "unterminated\n', encoding="utf-8")
        with pytest.raises(RuntimeError):
            mod._yq(".", str(cfg))

    def test_yq_not_installed_raises(self, tmp_path, monkeypatch):
        mod = self._mod()
        monkeypatch.setattr(mod.shutil, "which", lambda name: None)
        cfg = tmp_path / "x.yaml"
        cfg.write_text("schema: spec-driven\n", encoding="utf-8")
        with pytest.raises(RuntimeError, match="未安装"):
            mod._yq(".schema", str(cfg))

    def test_yq_identity_check_rejects_non_mikefarah(self, tmp_path, monkeypatch):
        mod = self._mod()
        monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/yq")

        class FakeProc:
            stdout = "yq 2.x (kislyuk/yq)\n"
            stderr = ""
            returncode = 0

        monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: FakeProc())
        cfg = tmp_path / "x.yaml"
        cfg.write_text("schema: spec-driven\n", encoding="utf-8")
        with pytest.raises(RuntimeError, match="mikefarah"):
            mod._yq(".schema", str(cfg))

    def test_check_yq_not_installed_returns_reason_not_raise(self, monkeypatch):
        mod = self._mod()
        monkeypatch.setattr(mod.shutil, "which", lambda name: None)
        ok, reason = mod._check_yq()
        assert ok is False
        assert "未安装" in reason

    def test_check_yq_ok_when_available(self):
        mod = self._mod()
        ok, reason = mod._check_yq()
        assert ok is True
        assert reason is None

    def test_lint_config_reports_reason_when_yq_missing(self, tmp_path, monkeypatch):
        """`lint_config` 的入口门（`_check_yq()`）在 yq 不可用时返回 reason 列表，不崩溃/
        不退出——这是它与 `run()` 路径（靠既有 `except RuntimeError: _die()` 兜底）的
        唯一差异化处理，见 `_check_yq()` docstring。"""
        mod = self._mod()
        monkeypatch.setattr(mod.shutil, "which", lambda name: None)
        osdir = tmp_path / "openspec"
        osdir.mkdir(parents=True)
        (osdir / "config.yaml").write_text("schema: spec-driven\n", encoding="utf-8")
        reasons = mod.lint_config(str(tmp_path))
        assert len(reasons) == 1
        assert "未安装" in reasons[0]


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


class TestDuplicateTopKeys:
    """T149: lint_config() 顶层重复键检测。"""

    def test_duplicate_top_key_detected(self, tmp_path):
        _write_config(tmp_path, "schema: spec-driven\nrules:\n  proposal:\n    - a\n  specs:\n    - b\n  design:\n    - c\n  tasks:\n    - d\nschema: other\n")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "重复" in r.stderr

    def test_no_duplicate_passes(self, tmp_path):
        _write_config(tmp_path, VALID_RULES_BLOCK)
        r = _run_lint(tmp_path)
        assert r.returncode == 0, r.stderr

    def test_non_utf8_no_crash(self, tmp_path):
        osdir = tmp_path / "openspec"
        osdir.mkdir(parents=True)
        (osdir / "config.yaml").write_bytes(b"\xff\xfe invalid utf8\n")
        r = _run_lint(tmp_path)
        assert "Traceback" not in r.stderr

    def test_bom_first_key_detected(self, tmp_path):
        osdir = tmp_path / "openspec"
        osdir.mkdir(parents=True)
        content = "schema: spec-driven\nrules:\n  proposal:\n    - a\n  specs:\n    - b\n  design:\n    - c\n  tasks:\n    - d\nschema: other\n"
        (osdir / "config.yaml").write_text(content, encoding="utf-8-sig")
        r = _run_lint(tmp_path)
        assert r.returncode != 0
        assert "重复" in r.stderr
