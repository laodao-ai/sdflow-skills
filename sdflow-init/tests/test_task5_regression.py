"""Task 5 regression coverage and the bundle refresh contract."""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import init as init_mod


def test_install_refresh_is_authoritative_and_prunes_schema_orphans(tmp_path, monkeypatch):
    """A refresh copies the authoritative bundle and removes consumer-only schema files."""
    bundle = tmp_path / "bundle"
    (bundle / "tools").mkdir(parents=True)
    (bundle / "tools" / "anchor_lint.py").write_text("# current\n", encoding="utf-8")
    schemas = tmp_path / "schemas"
    (schemas / "sdflow-spec-driven").mkdir(parents=True)
    (schemas / "sdflow-spec-driven" / "schema.yaml").write_text("current: true\n", encoding="utf-8")
    monkeypatch.setattr(init_mod, "BUNDLE_SRC", str(bundle))
    monkeypatch.setattr(init_mod, "SCHEMAS_SRC", str(schemas))

    root = tmp_path / "consumer"
    stale = root / "openspec" / "schemas" / "old-schema"
    stale.mkdir(parents=True)
    (stale / "orphan.yaml").write_text("stale\n", encoding="utf-8")

    init_mod.copy_bundle(str(root), include_schema=True)

    assert not stale.exists()
    assert (root / "openspec" / "schemas" / "sdflow-spec-driven" / "schema.yaml").read_text(
        encoding="utf-8"
    ) == "current: true\n"
    assert (root / "openspec" / "workflow" / "tools" / "anchor_lint.py").is_file()


@pytest.mark.parametrize(
    ("version", "allowed"),
    [((1, 6, 9), False), ((1, 7, 0), True), ((1, 10, 0), True)],
)
def test_task5_schema_gate_uses_numeric_semver(tmp_path, monkeypatch, version, allowed):
    monkeypatch.setattr(init_mod, "_openspec_cli_version", lambda: (version, None))
    enabled, _ = init_mod._schema_gate(str(tmp_path))
    assert enabled is allowed


@pytest.mark.parametrize("error", ["command missing", "non-numeric output"])
def test_task5_schema_gate_fails_closed_for_unusable_cli(tmp_path, monkeypatch, error):
    monkeypatch.setattr(init_mod, "_openspec_cli_version", lambda: (None, error))
    enabled, message = init_mod._schema_gate(str(tmp_path))
    assert enabled is False
    assert "不铺 project-local schema" in message


def test_task5_migration_runs_before_config_switch(tmp_path, monkeypatch):
    root = tmp_path / "project"
    (root / "openspec" / "changes" / "active").mkdir(parents=True)
    (root / "openspec" / "changes" / "active" / "proposal.md").write_text(
        "# proposal\n", encoding="utf-8"
    )
    (root / "openspec" / "config.yaml").write_text(
        "schema: spec-driven\ncontext: retained\n", encoding="utf-8"
    )
    monkeypatch.setattr(init_mod, "_schema_gate", lambda _root: (True, "enabled"))
    seen = []

    def record_migration(project_root, schema):
        config = Path(project_root) / "openspec" / "config.yaml"
        seen.append(config.read_text(encoding="utf-8"))
        marker = Path(project_root) / "openspec" / "changes" / "active" / ".openspec.yaml"
        marker.write_text(f"schema: {schema}\n", encoding="utf-8")
        return 1

    monkeypatch.setattr(init_mod, "migrate_changes", record_migration)
    monkeypatch.setattr(init_mod, "copy_bundle", lambda *args, **kwargs: ("workflow", 0))
    monkeypatch.setattr(init_mod, "handle_config", lambda project_root, mode, schema=None: ("updated", "ok"))

    init_mod.run(str(root), "update")

    assert seen == ["schema: spec-driven\ncontext: retained\n"]


def test_task5_schema_content_contract():
    schema = Path(init_mod.SCHEMAS_SRC) / init_mod.PROJECT_SCHEMA / "schema.yaml"
    text = schema.read_text(encoding="utf-8")
    for artifact_id, generated in {
        "proposal": "proposal.md",
        "specs": "specs/**/*.md",
        "design": "design.md",
        "tasks": "tasks.md",
    }.items():
        assert re.search(rf"id:\s*{artifact_id}\b", text)
        assert generated in text
    assert re.search(r"id:\s*specs[\s\S]*?requires:\s*\n(?:\s+-\s+[^\n]+\n)*\s+-\s+proposal\b", text)
    assert re.search(r"id:\s*tasks[\s\S]*?requires:\s*\n(?:\s+-\s+[^\n]+\n)*\s+-\s+proposal\b", text)
    assert "sdflow:delegation:start" in text
    assert "sdflow:delegation:end" in text
