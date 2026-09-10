"""守 workflow 拆分（prompts/ 单一源 · workflow.md 骨架 · WORKFLOW-GUIDE.md 生成物）。

【为什么拆】
模型为了取【一行】prompt，原先要 Read 整份 workflow.md —— 它只需要其中 300 字节。
现在 prompt 单一源 = `prompts/step*.md`（一步一文件），模型只读它要的那个。

【拆完最容易腐化的三处，本文件逐一焊死】
  1. 有人手改 WORKFLOW-GUIDE.md（它是生成物）⇒ 与单一源漂移，手册教人跑一段已废的 prompt
  2. workflow.md 的指针指向不存在的 prompts/ 文件 ⇒ 模型取不到，只能凭记忆重写（而规则禁止）
  3. 有人把 prompt 全文塞回 workflow.md 的表格 ⇒ 拆分白做，token 又回去了
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen_workflow_guide as G  # noqa: E402


def test_guide_is_in_sync_with_its_sources():
    """⭐ WORKFLOW-GUIDE.md MUST 与 workflow.md + prompts/ 一致。

    它是【生成物】。手改 = 制造 prompt 的第二份真相源 = 必漂。
    修：python3 hack/gen_workflow_guide.py --write
    """
    assert G.main(["--check"]) == 0


def test_every_pointer_resolves():
    """⭐ workflow.md 里的每个 prompt 指针，MUST 指向真实存在的 prompts/ 文件。"""
    w = G.WORKFLOW.read_text(encoding="utf-8")
    pointers = G._POINTER_RE.findall(w)
    assert len(pointers) >= 1, "workflow.md 里找不到任何 prompt 指针"
    for fname in pointers:
        f = G.PROMPTS / fname
        assert f.is_file(), f"指针悬空：prompts/{fname} 不存在"
        assert f.read_text(encoding="utf-8").strip(), f"prompts/{fname} 是空的"


def test_prompts_are_not_inlined_back_into_the_table():
    """⭐ 回归：MUST NOT 把 prompt 全文塞回 workflow.md 的表格。

    塞回去 = 拆分白做（模型又要为取一行读整份）。判据：表格的 prompt 列只许是指针。
    每个 prompt 各挑一个【只在它自己那份里出现】的特征串来测。
    """
    w = G.WORKFLOW.read_text(encoding="utf-8")
    fingerprints = {
        "step8-code-review": "Step1 自持 scope 审计的 scope-drift",
    }
    for name, fp in fingerprints.items():
        assert fp in (G.PROMPTS / f"{name}.md").read_text(encoding="utf-8"), \
            f"prompts/{name}.md 丢了特征串「{fp}」——测试本身失鲜了，先核对再改"
        assert fp not in w, \
            f"prompt 全文被塞回 workflow.md 了（命中「{fp}」）—— 拆分白做"


def test_history_is_out_of_the_body():
    """DOC-1：演进史进独立文件，不在 workflow.md 正文。"""
    w = G.WORKFLOW.read_text(encoding="utf-8")
    hist = (G.WF_DIR / "workflow-history.md")
    assert hist.is_file()
    assert "workflow-history.md" in w
    assert "旧 step 11" not in w
    assert "旧 step 11" in hist.read_text(encoding="utf-8")


def test_guide_has_no_unresolved_pointers():
    """WORKFLOW-GUIDE.md 里不该残留任何 prompt 指针（应全部被替换为实际内容）。"""
    guide = G.GUIDE.read_text(encoding="utf-8")
    assert not G._POINTER_RE.search(guide), \
        "WORKFLOW-GUIDE.md 里还有未替换的 prompt 指针"
