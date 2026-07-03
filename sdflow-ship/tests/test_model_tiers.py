import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TIERS = REPO / "sdflow-init" / "assets" / "workflow" / "model-tiers.md"
CONFIG = REPO / "sdflow-init" / "assets" / "workflow" / "config.template.yaml"
SKILLS = ["sdflow-ship/SKILL.md", "sdflow-done/SKILL.md",
          "sdflow-spec-review/SKILL.md", "sdflow-code-review/SKILL.md"]
BARE = re.compile(r"\b(opus|sonnet|haiku|Opus|Sonnet|Haiku)\b")

def test_tiers_file_is_truth_source():
    t = TIERS.read_text(encoding="utf-8")
    for kw in ("强档", "中档", "弱档", "opus", "sonnet", "haiku",
               "verify", "对抗裁决", "机队锚定"):
        assert kw in t

def test_config_overlay_section():
    t = CONFIG.read_text(encoding="utf-8")
    assert "model-tiers" in t and "覆盖" in t and "model-tiers.md" in t

def test_skills_zero_inline_model_names():
    for rel in SKILLS:
        for i, line in enumerate((REPO / rel).read_text(encoding="utf-8").splitlines(), 1):
            if "model-tiers.md" in line:      # 引用句白名单
                continue
            assert not BARE.search(line), f"{rel}:{i} 残留裸模型名: {line.strip()}"
