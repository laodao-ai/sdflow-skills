import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TIERS = REPO / "sdflow-init" / "assets" / "workflow" / "model-tiers.md"
CONFIG = REPO / "sdflow-init" / "assets" / "workflow" / "config.template.yaml"
SKILLS = ["sdflow-ship/SKILL.md", "sdflow-done/SKILL.md",
          "sdflow-spec-review/SKILL.md", "sdflow-code-review/SKILL.md"]
# [impl-review-fix] 裁决项9：\b 在中文语境下对 CJK/ASCII 边界失效（CJK 字符不算
# word char，紧贴 ASCII 单词两侧仍会被 \b 判定为词边界），收紧为显式排除左右 ASCII
# 字母的负向环视，堵住"档位词紧贴裸模型名"类残留不被 \b 误判为非边界从而漏检的口子。
BARE = re.compile(r"(?<![A-Za-z])(opus|sonnet|haiku)(?![A-Za-z])", re.IGNORECASE)

def test_tiers_file_is_truth_source():
    t = TIERS.read_text(encoding="utf-8")
    for kw in ("强档", "中档", "弱档", "opus", "sonnet", "haiku",
               "verify", "对抗裁决", "机队锚定"):
        assert kw in t

def test_config_overlay_section():
    t = CONFIG.read_text(encoding="utf-8")
    assert "model-tiers" in t and "覆盖" in t and "model-tiers.md" in t

def test_skills_zero_inline_model_names():
    # [impl-review-fix] 裁决项9：删除 "model-tiers.md" 引用句白名单——四 SKILL 的引用句
    # 本身应零裸模型名（用"强档/中档/弱档"代称，见 sdflow-done/spec-review/code-review
    # SKILL.md 的 model-tiers.md 引用行），应对全文强制零命中，不留白名单口子。
    for rel in SKILLS:
        for i, line in enumerate((REPO / rel).read_text(encoding="utf-8").splitlines(), 1):
            assert not BARE.search(line), f"{rel}:{i} 残留裸模型名: {line.strip()}"
