"""守 workflow 三分（prompts/ 单一源 · workflow.md 骨架 · WORKFLOW-GUIDE.md 生成物）。

【为什么拆】
模型为了取【一行】prompt，原先要 Read 整份 19.6KB 的 workflow.md —— 它只需要其中 300 字节。
现在 prompt 单一源 = `prompts/step*.md`（一步一文件），模型只读它要的那个。

【拆完最容易腐化的三处，本文件逐一焊死】
  1. 有人手改 WORKFLOW-GUIDE.md（它是生成物）⇒ 与单一源漂移，手册教人跑一段已废的 prompt
  2. workflow.md 的指针指向不存在的 prompts/ 文件 ⇒ 模型取不到，只能凭记忆重写（而规则禁止）
  3. 有人把 prompt 全文塞回 workflow.md 的表格 ⇒ 拆分白做，token 又回去了
"""
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
    """⭐ workflow.md 表格里的每个 `prompts/xxx.md` 指针，MUST 真的存在。

    指针悬空的后果是确定的：模型取不到 prompt → 只能凭记忆重写 →
    而 claude-section.md 明令「MUST NOT 凭记忆重写」→ 死锁 → 实际结果是静默跳过那一步。
    """
    w = G.WORKFLOW.read_text(encoding="utf-8")
    for name in G.STEP_FILES.values():
        f = G.PROMPTS / f"{name}.md"
        assert f.is_file(), f"指针悬空：prompts/{name}.md 不存在"
        assert f"prompts/{name}.md" in w, f"workflow.md 里没有指向 prompts/{name}.md 的指针"
        assert f.read_text(encoding="utf-8").strip(), f"prompts/{name}.md 是空的"


def test_prompts_are_not_inlined_back_into_the_table():
    """⭐ 回归：MUST NOT 把 prompt 全文塞回 workflow.md 的表格。

    塞回去 = 拆分白做（模型又要为取一行读整份）。判据：表格的 prompt 列只许是指针。
    每个 prompt 各挑一个【只在它自己那份里出现】的特征串来测。
    """
    w = G.WORKFLOW.read_text(encoding="utf-8")
    fingerprints = {
        "step6-writing-plans": "Global Constraints 不进 brief",
        "step8-code-review": "并入 gstack/review 的 scope-drift",
    }
    for name, fp in fingerprints.items():
        assert fp in (G.PROMPTS / f"{name}.md").read_text(encoding="utf-8"), \
            f"prompts/{name}.md 丢了特征串「{fp}」——测试本身失鲜了，先核对再改"
        assert fp not in w, \
            f"prompt 全文被塞回 workflow.md 了（命中「{fp}」）—— 拆分白做"


def test_history_is_out_of_the_body():
    """DOC-1：演进史进独立文件，不在 workflow.md 正文。

    放在【同一文件的附录】里省不到任何 token —— 模型 Read 整份照付。
    """
    w = G.WORKFLOW.read_text(encoding="utf-8")
    hist = (G.WF_DIR / "workflow-history.md")
    assert hist.is_file()
    assert "workflow-history.md" in w          # 正文留一行指针
    assert "旧 step 11" not in w               # 考古层本体不在正文
    assert "旧 step 11" in hist.read_text(encoding="utf-8")


def test_table_stays_six_columns():
    """表格解析的语法面前提：每行恰好 6 列（基准 5：有界才可手写解析）。

    单元格里出现裸 ' | ' 会让 _rows() fail-closed —— 这个测试提前把它抓住。
    行数下限反映 simplify-workflow 后的单轨线性流程（8 行：explore/sdflow-spec/
    spec-review/HARD-GATE/writing-plans/subagent-dev/code-review/done）。
    """
    rows = G._rows()
    assert len(rows) >= 6
    assert {r["step"] for r in rows} >= set(G.STEP_FILES)
