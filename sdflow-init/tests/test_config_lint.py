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
    )


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
        )
        assert r_init.returncode == 0, r_init.stderr
        assert (project / "openspec" / "config.yaml").is_file()

        r_update = subprocess.run(
            ["python3", str(INIT_PY), "update", "--root", str(project)],
            capture_output=True, text=True, env=env,
        )
        assert r_update.returncode == 0, r_update.stderr

        r_retire = subprocess.run(
            ["python3", str(INIT_PY), "retire-hooks"],
            capture_output=True, text=True, env=env,
        )
        assert r_retire.returncode == 0, r_retire.stderr
