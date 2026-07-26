"""canonical 规则单一源：阶段一「四入口选择规则 + G1 具名例外 + FF-0 三分支判定」不得分叉。

【为什么要有本文件】
`add-sdflow-spec` 引入的阶段一单入口与**七处**既有权威源冲突。本仓运行时经
`resolve-workflow.sh` 解析到**全局 canonical**、仓内不留规则副本 ⇒ 任何一处漏改，
结果就是「人从 README/CLAUDE.md 读到新入口，AI 从 bundle 读到旧入口」，且两者对
`/clear` 直接矛盾。这类分叉没有自然的报错口——不机械钉住，就只能靠人记得。

【锚的质量纪律（本文件的重点）】
- **MUST 单行命中**：G1 的两处载体措辞不同（`workflow.md` 写「全流程不用 `/clear`」，
  `quality-layering.md` 写「无 `/clear`（G1）」），**一条 grep 命不中两处**，必须分开断言。
- **MUST NOT 用跨行结构当判据**：`generation-process.md` §四 是跨行 ASCII 图，
  `explore.*ff.*grill` 这类单行正则对它**实测零命中** = 一个永远不会红的空判据。
  故对 canonical bundle 一律锚**单行散文/表格行**，不锚图。
- **锚要打在它自称守的那句话上**：一条锚若能被**别处**的行满足，它就守不住被点名的那一处。
  （实测教训：`keeps_legacy_path_alive` 原先锚 `opsx:explore` / `grill-with-docs` 两个裸词，
  删掉 §四 整个分支 B 块仍绿——它被 §五 的 skill 选择表满足了。）
- **例外：人读侧（CLAUDE.md / AGENTS.md）用「压掉空白后比对」，不用单行锚。**
  那两份是硬折行的中文散文，句子会跨行；单行锚会随折行位置变化而假红/假绿。
- 每条断言都做过**定点变异回验**（把被锚的那句话改掉/删掉 → 该断言必红）。

【谁不在本文件里，为什么】
- `WORKFLOW-GUIDE.md` 是**生成物**：与单一源的一致性由 `test_workflow_split.py` 的
  `gen_workflow_guide --check` 守；这里只补一条「重生成后阶段一段落确实带上了新入口」。
- `ff0-branch-guard.py` 的**行为**由 `sdflow-init/tests/test_ff0_branch_guard.py` 守
  （真跑 hook）；这里只守「规则文本与 hook 说的是同一个逃生口机制」。

【人核残余：如实登记，MUST NOT 硬造恒真锚】
下面三项无可靠单行锚点，机械层**故意**不覆盖（登记于此即可，**不需要一条测试来给它背书**——
一条只断言「本文件自己的字面量非空」的用例，参照系不含任何仓状态，无任何仓改动能使它红）：
  · `generation-process.md` §四 的两张 ASCII 流水线图本身（跨行结构；本文件只锚其周边散文）
  · `workflow.md` §一 的阶段一流程图分支框（同上）
  · 「例外情形①②③的语义是否真的互斥且穷尽」——语义判断，无确定性信号
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WF = REPO / "sdflow-init" / "assets" / "workflow"

WORKFLOW = WF / "workflow.md"
GENERATION = WF / "generation-process.md"
QUALITY = WF / "reference" / "quality-layering.md"
FF_CONSTRAINTS = WF / "ff-generation-constraints.md"
GUIDE = WF / "WORKFLOW-GUIDE.md"
CLAUDE_SECTION = REPO / "sdflow-init" / "assets" / "snippets" / "claude-section.md"
SPEC_WORKFLOW = REPO / "openspec" / "specs" / "spec-workflow" / "spec.md"
HOOK = REPO / "sdflow-init" / "assets" / "hooks" / "ff0-branch-guard.py"
RUNTIME_GITIGNORE = REPO / "sdflow-init" / "assets" / "snippets" / "runtime-gitignore.txt"

# 人读侧的两份载体（非托管区，手写）——本 change 的立项理由就是「人读侧与 AI 读侧分叉」，
# 故这一面 MUST NOT 只靠 prose「改一处就改另一处」兜底。
HUMAN_SIDE = {
    "CLAUDE.md": REPO / "CLAUDE.md",
    "AGENTS.md": REPO / "AGENTS.md",
}
ENTRY_HEADING = "## 阶段一入口："

# 人读侧的第三类载体：docs/ 下四份「呈现阶段一流程」的文档。
# 它们不是规则真相源，但**人从它们读到入口**——只写旧三步即 D10 描述的分叉形态。
#
# ⚠️ 锚**逐处**打，不是「全文提过分支 A 就算数」：一份文档完全可能在总览图里提了
# `/sdflow-spec`、而它的阶段一详解小节仍只画旧三步 —— 那正是本组要修的缺陷形态。
# （实测：只写「全文含『分支 A』+『sdflow-spec』」的弱锚，删掉 overview §2 的分支 A
# 小节标题、删掉 map.html 的入口行，都仍然绿。）
#
# ⚠️⚠️ 「逐处」= 该文档里**每一处**分支表述各自一条锚，**不是每份一条**。判据逐处问：
# 「把这一处删掉/改回无条件表述，本文件会红吗？」红不了就是漏网格。
# （fix2 的实测教训：`DOCS_CARRIERS` 只扩了「份」没扩「处」—— overview `:62`/`:247`、
#  map.md `:30` 三处逐一删掉，25 个用例仍全绿。典型「扩枚举不回改派生判据」。）
# 两类都算「一处」：① 呈现阶段一入口的行；② **带分支限定词的条件表述**——删掉限定词后
# 它会变成无条件成立的错误声明（`〔仅分支 B〕`、`〔分支 B〕问题清晰否`…）。
DOCS_CARRIERS = {
    "docs/workflow-overview.md": (
        REPO / "docs" / "workflow-overview.md",
        [("/sdflow-spec（分支 A · 默认）",),          # §0 全局流程图节点
         ("一 · 生成", "分支 A `/sdflow-spec` 一次跑完", "分支 B `opsx:ff`"),  # §1 三阶段画像表
         ("### 分支 A（默认）", "sdflow-spec"),       # §2 阶段一 · 分支 A 小节
         ("### 分支 B", "旧三步"),                    # §2 阶段一 · 分支 B 小节
         ("分支 B 里 grill 一律全深度", "MUST NOT 瘦跑"),  # §2 分支 B 的深度约束
         ("`opsx:ff`", "仅分支 B", "非黑盒"),         # §6 黑盒 skill 表（无条件成立即错）
         ("装了 `sdflow-spec` 吗", "分支 A"),         # §7 自检清单 · 入口选择
         ("〔分支 B〕", "问题清晰否"),                 # §7 自检清单 · explore 条（同上）
         ("〔分支 B〕", "grill 是否收敛后才提交")],    # §7 自检清单 · grill 条（同上）
    ),
    "docs/workflow-map.md": (
        REPO / "docs" / "workflow-map.md",
        # ⚠️「propose + /sdflow-spec」会被下面的阶段表行满足 ⇒ 用轨道箭头把锚钉在 ASCII 轨上
        [("──▶", "/sdflow-spec"),                     # ASCII 轨 · propose 行
         ("分支 B 才走", "分支 A 无此步"),             # ASCII 轨 · explore 行的分支限定
         ("〔分支 A · 默认〕", "git checkout -b"),     # ASCII 轨 · propose 行下的分支标
         ("/opsx:ff / :new", "〔分支 B〕"),            # ASCII 轨 · 旧入口的分支限定
         ("A: /sdflow-spec 相位 B", "B: grill-with-docs"),  # ASCII 轨 · 人类门①两分支
         ("| 0 |", "explore", "〔分支 B〕"),           # 阶段表 · explore 行
         ("分支 A · 默认", "/sdflow-spec")],          # 阶段表 · propose 行
    ),
    "docs/workflow-map.html": (
        REPO / "docs" / "workflow-map.html",
        [("stage-skill", "/sdflow-spec"),             # STAGE 1 的 skill 行
         ("分支 A（默认）", "/sdflow-spec")],         # STAGE 1 的入口行
    ),
    "docs/workflow-console.html": (
        REPO / "docs" / "workflow-console.html",
        # ⚠️ 裸词 `sdflow-spec` 是 `sdflow-spec-review` 的前缀 ⇒ chips 锚须带尖括号定界
        [("分支 A（默认）", "/sdflow-spec"),          # 阶段一卡片的角色描述
         ("chip", ">sdflow-spec<")],                  # 阶段一卡片的 skill chips
    ),
    # ⚠️ 同一文档包内也会自相矛盾：01/02 改了、README 的速览图没改，包内两说。
    #    故**包内每份**呈现阶段一的载体各自上锚，不靠「同包某处提过分支 A」。
    "docs/sdflow-fable5/README.md": (
        REPO / "docs" / "sdflow-fable5" / "README.md",
        [("分支 A（默认）/sdflow-spec", "分支 B explore→ff→grill")],  # 一图速览的生成节点
    ),
    "docs/sdflow-fable5/01-goals-and-rationale.md": (
        REPO / "docs" / "sdflow-fable5" / "01-goals-and-rationale.md",
        [("S0[", "分支 A · 默认"),                    # §2 全局形态图
         ("需求明确", "分支 A（默认）", "分支 B"),      # §7 目标 vs 现状对照
         ("生成 Spec", "分支 A（默认）", "分支 B")],
    ),
    "docs/sdflow-fable5/02-module-reference.md": (
        REPO / "docs" / "sdflow-fable5" / "02-module-reference.md",
        [("SP[", "分支 A · 默认")],                   # §7 端到端调用拓扑
    ),
    # 位置声明类载体：它自称「阶段一第 N 步」，分支 A 下该定位无条件成立即错
    # （分支 A 的拷问是 `/sdflow-spec` 相位 B，前置于成文，不经本 skill）。
    "docs/workflow-skills/grill-with-docs.md": (
        REPO / "docs" / "workflow-skills" / "grill-with-docs.md",
        [("人类对话岛", "分支 B 的第 3 步"),           # 文首定位
         ("分支 A（默认，`/sdflow-spec`）不走本 skill", "前置于成文"),  # 文首的分支 A 排除句
         ("谁调它", "分支 B", "分支 A 不经本 skill")],  # §1 位置与契约表
    ),
    # ⚠️ 仓 README 是**人第一眼**读到的阶段一入口（`:20-29` 的出口序列代码块 + 旧三步注）。
    #    fix2 实测：把那两处删掉，25 个用例全绿 —— 期望集只圈了 docs/，漏了仓门口那一份。
    "README.md": (
        REPO / "README.md",
        [("/sdflow-spec", "阶段一：澄清 → 拷问 → 生成"),      # 出口序列代码块
         ("没装 `sdflow-spec` 的项目沿用旧三步", "opsx:explore"),  # 分支 B 注
         ("`sdflow-spec`", "阶段一·产 spec 单一入口")],       # Skills 列表行
    ),
    # ⚠️⚠️⚠️ **载体范畴 = 「任何呈现『怎么开一个 change / 阶段一入口』的行」，不限于 `docs/`。**
    #    连续三轮冷验都是同一个失效：**期望集的范畴取窄**（先只圈 docs/，再补 README，
    #    再补 architecture 一份 SKILL.md）。fix4 起按上述范畴把**全仓 tracked 的 SKILL.md
    #    + docs/** 一次扫全（`grep -rnE 'opsx:(ff|new|propose)|openspec new change'`，不加
    #    `--include`），逐处「改掉 + 上锚」或在 fix4 报告里登记不改的理由。
    #    扫出的 **指示性**载体（告诉读者去敲哪条命令开 change）全部在下面上锚；
    #    **描述性**引用（历史来源标注、粒度度量、hook 覆盖面、否定式排除）登记在报告里不改。
    "sdflow-architecture/SKILL.md": (
        REPO / "sdflow-architecture" / "SKILL.md",
        [("skeleton-ready", "/sdflow-spec", "分支 A · 默认"),   # §5.2 对话收尾行
         # frontmatter `description` 的「不触发」清单原写死「单次 change 的 spec/design（走 /opsx:ff）」
         # —— 它是**指路行**，分支 A 下无条件成立即错。
         ("单次 change 的 spec/design", "/sdflow-spec`〔分支 A · 默认〕", "`opsx:ff`〔分支 B〕")],
    ),
    # ⚠️ roadmap 的「下游：阶段实施」交棒块与 architecture §5.2 **同形态、同范畴**：
    #    都在 SKILL.md 里给下游 change 的创建命令。原写死 `/opsx:new`（分支 B 入口，
    #    见 docs/workflow-map.md 阶段表 / workflow-map.html STAGE 1）。
    "sdflow-roadmap/SKILL.md": (
        REPO / "sdflow-roadmap" / "SKILL.md",
        [("/sdflow-spec implement-", "〔分支 A · 默认〕"),      # 下游交棒块 · 分支 A
         ("/opsx:new implement-", "〔分支 B〕"),                # 下游交棒块 · 分支 B
         # 「直写不经 change 生产路径」原只否定 `opsx:ff` —— 分支 A 下该否定不完整，
         # 读者会问「那经 /sdflow-spec 吗」。两分支都要点名。
         ("不经 change 生产路径", "分支 A `/sdflow-spec`", "分支 B `opsx:ff`")],
    ),
}

# FF-0 hook 拦的是 `openspec new change` 这一条 CLI —— 三处载体各抄了一份「哪些入口殊途同归
# 调它」的**入口全集**清单。本 change 新增的 `/sdflow-spec` 相位 B ③ 同样调它
# （`sdflow-spec/SKILL.md` 的「③ 建 change 目录」），三处清单漏它 ⇒ 人会读成「分支 A 不过 FF-0」，
# 与 `docs/workflow-overview.md`「相位 B **起手**即过 FF-0 三分支判定 + `openspec new change`」矛盾。
FF0_ROSTER_CARRIERS = {
    "ff0-branch-guard.py": HOOK,
    "ff-generation-constraints.md": FF_CONSTRAINTS,
    "sdflow-init/SKILL.md": REPO / "sdflow-init" / "SKILL.md",
}


def lines(p: Path):
    return p.read_text(encoding="utf-8").splitlines()


def has_line(p: Path, *needles: str) -> bool:
    """存在**同一行**同时含全部 needles。跨行结构一律不算命中。"""
    return any(all(n in ln for n in needles) for ln in lines(p))


def require(p: Path, *needles: str):
    assert has_line(p, *needles), (
        f"{p.relative_to(REPO)} 里找不到同时含 {needles!r} 的**单行** —— "
        "canonical 与本 change 的阶段一规则已分叉，或这条锚失鲜了（先核对再改测试）"
    )


def flat(text: str) -> str:
    """压掉全部空白（含换行）。用于比对**硬折行的中文散文**，见模块 docstring。"""
    return re.sub(r"\s+", "", text)


def entry_section(p: Path) -> str:
    """截出「阶段一入口」那一节（到下一个同级 `## ` 标题为止）。"""
    text = p.read_text(encoding="utf-8")
    start = text.find(ENTRY_HEADING)
    assert start >= 0, (
        f"{p.relative_to(REPO)} 里没有「{ENTRY_HEADING}…」这一节 —— "
        "SA-14 要求四入口选择规则**同时**落在人读侧与 AI 读侧，人读侧这份不许消失"
    )
    end = text.find("\n## ", start + 1)
    return text[start:] if end < 0 else text[start:end]


# ── ① generation-process.md：推荐流水线两分支 + 四入口选择规则 ─────────────

def test_generation_process_has_two_branches():
    """锚 §四 的两个**小节标题**本身。

    ⚠️ 不能只锚裸词「分支 A」+「sdflow-spec」——§八 检查清单那行
    （「装了 `sdflow-spec` 吗？装了就走**分支 A 单入口**」）同样含这两个词，
    ⇒ 把 §四 的分支 A 小节整块删掉，那种弱锚仍会绿。
    """
    require(GENERATION, "### 分支 A", "已装", "单入口")
    require(GENERATION, "### 分支 B", "未装", "旧三步")


def test_generation_process_states_entry_selection_rule():
    require(GENERATION, "默认走 `/sdflow-spec`")
    require(GENERATION, "仅下列三种情形用旧三步")
    require(GENERATION, "模型侧", "MUST NOT", "opsx:ff")


def test_generation_process_keeps_legacy_path_alive():
    """旧三步未被删除——它仍是三种例外情形下的合法路径。

    ⚠️ 锚必须落在 §四 里**明说这件事**的那一句上。原先锚裸词 `opsx:explore` /
    `grill-with-docs` 是**打偏的**：实测把 §四 的分支 B 整块删掉，本用例仍绿
    ——那两个词被 §五 的 skill 选择表满足了，而 §五 说的是「什么时候用哪个 skill」，
    不是「旧三步仍是合法路径」。
    """
    require(GENERATION, "旧三步仍是合法路径", "三个原入口未被删除")
    require(GENERATION, "分支 B", "grill 一律全深度", "MUST NOT")


# ── ② workflow.md：G1 具名例外（载体一，措辞「全流程不用 `/clear`」）──────

def test_workflow_md_g1_still_states_the_rule():
    require(WORKFLOW, "全流程不用 `/clear`")


def test_workflow_md_g1_names_the_exception():
    require(WORKFLOW, "具名例外", "阶段一 → 阶段二")


def test_workflow_md_g1_exception_cites_exactly_the_two_allowed_reasons():
    require(WORKFLOW, "cache 按模型隔离")
    require(WORKFLOW, "产 / 审错档")


def test_workflow_md_g1_exception_forbids_the_cold_view_reason():
    """「主审裁决需冷视角」已被 G1 正面回答 ⇒ MUST 有一行明令禁止拿它当本例外的理由。

    ⚠️ 判据是「存在这条禁令行」，**不是**「全文提到冷视角的行都带 MUST NOT」——
    后者会被 §一流程图里那句「独立冷视角·强制主审」误伤（那是在说 code-review，不是理由）。
    """
    require(WORKFLOW, "MUST NOT", "冷视角")


# ── ③ quality-layering.md：G1 具名例外（载体二，措辞「无 `/clear`（G1）」）─
#     ⚠️ 与 ② 字面不同，一条 grep 命不中两处 —— 故必须分开断言。

def test_quality_layering_still_states_the_rule():
    require(QUALITY, "无 `/clear`（G1）")


def test_quality_layering_names_the_same_exception():
    require(QUALITY, "具名例外", "sdflow-spec")
    require(QUALITY, "cache 按模型隔离")
    require(QUALITY, "产 / 审错档")


def test_quality_layering_forbids_the_cold_view_reason():
    require(QUALITY, "MUST NOT", "冷视角")


def test_quality_layering_checklist_carries_the_exception():
    """检查清单是另一处载体（`:117` 那条）—— 清单说「不许 /clear」而正文说「有例外」即分叉。"""
    checklist = [ln for ln in lines(QUALITY) if ln.startswith("- [ ]") or ln.startswith("      ")]
    assert any("例外" in ln and "sdflow-spec" in ln for ln in checklist), \
        "quality-layering.md 的检查清单没跟上 G1 例外"


# ── ④ ff-generation-constraints.md + hook：FF-0 三分支判定 ────────────────

def test_ff0_rule_is_three_way():
    require(FF_CONSTRAINTS, "三分支判定")
    require(FF_CONSTRAINTS, "其它 feature 分支", "halt 问人")
    require(FF_CONSTRAINTS, "MUST NOT 沿用「已在 feature 分支就跳过」的弱判据")


def test_ff0_rule_and_hook_agree_on_the_escape_hatch():
    """规则文本与 hook 实现是两处载体 —— 逃生口必须是同一个哨兵路径。"""
    require(FF_CONSTRAINTS, "openspec/.ff0-ack")
    assert 'os.path.join("openspec", ".ff0-ack")' in HOOK.read_text(encoding="utf-8"), \
        "hook 没实现规则文本承诺的哨兵逃生口 —— 人拍板「就地继续」这条路会走不通"


def test_ff0_escape_hatch_is_not_a_command_string_passphrase():
    """规则文本与 hook 都 MUST NOT 退回「从命令串里认口令」（基准 5：shell 语法面无界）。

    这条锚的是**机制本身**而非某个字面量：口令一旦回到命令串上，「注释算不算 / 在不在
    命令起始位置」就要解析 shell，而每堵一种形态就冒出下一种（行尾注释 → 行首注释 → …）。
    """
    require(FF_CONSTRAINTS, "MUST NOT 从命令串里认口令")
    hook = HOOK.read_text(encoding="utf-8")
    assert "MUST NOT 退回「从命令串里认口令」" in hook
    assert "SDFLOW_FF0_ACK" not in hook, \
        "hook 里又出现了命令串口令 —— 逃生口判据 MUST 只看哨兵文件在不在"


def test_ff0_escape_hatch_is_two_steps_in_both_carriers():
    """逃生口 MUST 是两步，规则文本与 hook 两侧同说。

    PreToolUse 在命令**执行前**判定 ⇒ `touch <token> && openspec new change X` 这一条
    在判定时哨兵还不存在，会被本 hook 连同 touch 一起 deny —— 唯一合规逃生口死循环。
    （hook 侧的**行为**由 `test_ff0_branch_guard.py::test_escape_hatch_command_in_deny_reason_is_itself_allowed`
    真跑一遍钉住；这里钉的是「两处载体都写明了这件事」。）
    """
    require(FF_CONSTRAINTS, "MUST NOT 写成 `touch … && openspec …` 一条")
    assert "MUST NOT 写成一条 `touch … && openspec …`" in HOOK.read_text(encoding="utf-8")


def test_ff0_lingering_sentinel_is_declared_and_time_bounded():
    """残留令牌是真实绕过口 —— MUST NOT 再声称「令牌不会残留成后门」（那是假断言）。

    成因：人在**自己的终端**里敲 `openspec new change` 时本 hook 根本不触发 ⇒ 哨兵永不被
    消费、原样留在盘上。缓解只有两件有界的事：有界时效 + 进 canonical runtime gitignore。
    """
    hook = HOOK.read_text(encoding="utf-8")
    assert "令牌不会残留成后门" not in hook, \
        "hook docstring 又断言令牌不会残留 —— 人在自己终端跑 openspec 时它就是会残留"
    assert "ACK_TTL_SECONDS" in hook, "哨兵没有有界时效 ⇒ 残留令牌 = 常驻绕过口"
    require(FF_CONSTRAINTS, "残留令牌是真实的绕过口")


def test_ttl_window_has_a_single_source():
    """哨兵时效的**分钟数只有一个源** = hook 的 `ACK_TTL_SECONDS`（deny 文案 `//60` 自报）。

    冷验变异 X1 实证：把 `ACK_TTL_SECONDS` 600→300，hook 行为测试与本文件**全绿**——
    三处散文（hook docstring / 常量注释 / canonical 规则文本）各手抄了一份「10 分钟」，
    与常量分叉无人守。修法取本仓既有手法「**删掉数字、让脚本自己报**」：散文一律不写死
    分钟数，唯一的数字出口是 deny 文案里的 `{ACK_TTL_SECONDS // 60}`。
    故本用例的判据是**散文里不许再出现字面分钟数**（正锚会随数字改动而失鲜，负锚不会）。
    """
    minutes = re.compile(r"\d+\s*分钟")
    hook = HOOK.read_text(encoding="utf-8")
    assert "ACK_TTL_SECONDS // 60" in hook, \
        "deny 文案不再从常量算分钟数 —— 数字失去唯一出口，散文必然重新手抄一份"
    for label, blob in (("ff0-branch-guard.py", hook),
                        ("ff-generation-constraints.md",
                         FF_CONSTRAINTS.read_text(encoding="utf-8"))):
        hits = [ln.strip() for ln in blob.splitlines() if minutes.search(ln)]
        assert not hits, (
            f"{label} 的散文里写死了分钟数 {hits!r} —— 它与 `ACK_TTL_SECONDS` 是两份口径，"
            "改常量不会红。让 deny 文案（`ACK_TTL_SECONDS // 60`）自己报，散文只说「有界时效」"
        )


def test_ff0_sentinel_is_ignored_in_consumer_repos():
    """哨兵 MUST 进 canonical runtime gitignore —— hook 是**全局**安装、拦所有项目。

    否则叠加 `checkpoint-commit.sh` 的无条件 `git add -A`，残留令牌会被提交入库，
    **每个 clone 都带一个常驻绕过口**。本仓 `.gitignore`（dogfood）同样必须有。
    """
    entry = "/openspec/.ff0-ack"
    snippet = RUNTIME_GITIGNORE.read_text(encoding="utf-8").splitlines()
    assert entry in snippet, (
        f"canonical runtime gitignore 缺 {entry} —— 消费仓不会忽略 FF-0 哨兵，"
        "checkpoint 的 git add -A 会把它提交入库"
    )
    assert entry in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines(), \
        "本仓 .gitignore 未 dogfood 同一条目"


# ── ⑤ claude-section.md（托管块源）：grill 条款分支化 + 归属修正 ──────────

def test_claude_section_scopes_the_grill_clause_to_branch_b():
    require(CLAUDE_SECTION, "ff 之后是 grill", "本条只管分支 B")


def test_claude_section_attribution_is_fixed():
    require(CLAUDE_SECTION, "Matt Pocock", "~/.agents/skills")
    blob = CLAUDE_SECTION.read_text(encoding="utf-8")
    assert "grill-with-docs" in blob
    assert "来自 superpowers 插件" not in blob, \
        "grill-with-docs 的归属仍写着 superpowers 插件（实为 Matt Pocock 的 ~/.agents/skills）"


def test_claude_section_carries_the_entry_selection_rule():
    require(CLAUDE_SECTION, "阶段一入口二选一")
    require(CLAUDE_SECTION, "FF-0 三分支判定")


# ── ⑥ 仓级主 spec：新旧入口共存与路由 ────────────────────────────────────

def test_spec_workflow_declares_coexistence_and_routing():
    require(SPEC_WORKFLOW, "新旧入口共存与路由")
    require(SPEC_WORKFLOW, "分支 A（默认）", "sdflow-spec")
    require(SPEC_WORKFLOW, "MUST NOT 沿用「已在 feature 分支就跳过」的弱判据")


# ── ⑦ 生成物：重生成后阶段一段落确实带上了新入口 ──────────────────────────

def test_generated_guide_reflects_the_new_entry():
    """一致性本身由 gen_workflow_guide --check 守（test_workflow_split.py）；
    这里只钉「新入口确实进了人读手册的阶段一段落」。"""
    require(GUIDE, "阶段一", "步骤 0", "/sdflow-spec")


# ── ⑧ 人读侧（CLAUDE.md / AGENTS.md 非托管区）：SA-14 的另一半落点 ────────
#     本 change 的立项理由就是「人读侧与 AI 读侧分叉」。人读侧这 60 行手抄成
#     第三、第四份副本，若零机械守，就是在**要消除的问题形态本身**上留了唯一无守面。

def test_entry_section_exists_in_both_human_carriers():
    for name, path in HUMAN_SIDE.items():
        assert entry_section(path).strip(), f"{name} 的阶段一入口小节是空的"


def test_two_human_carriers_are_verbatim_identical():
    """CLAUDE.md 与 AGENTS.md 的该节 MUST 逐字相等。

    两份是手抄的同一段话，唯一的兜底原本只是一句 prose「改一处就改另一处」——
    而「会想起去查那句 prose 的人本来就不会漏改」。这条把它变成机械的。
    """
    claude = entry_section(HUMAN_SIDE["CLAUDE.md"])
    agents = entry_section(HUMAN_SIDE["AGENTS.md"])
    assert claude == agents, (
        "CLAUDE.md 与 AGENTS.md 的「阶段一入口」小节已分叉 —— "
        "两份是同一条规则的两个手抄副本，MUST 逐字相同（改一处就改另一处）"
    )


def _require_flat(name: str, section: str, *needles: str):
    for n in needles:
        assert flat(n) in flat(section), (
            f"{name} 的「阶段一入口」小节里找不到「{n}」 —— "
            "人读侧与 AI 读侧的四入口选择规则/sunset 阈值已分叉或被删"
        )


def test_human_carriers_state_the_default_entry_and_the_model_ban():
    for name, path in HUMAN_SIDE.items():
        _require_flat(name, entry_section(path),
                      "**默认走 `/sdflow-spec`**",
                      "MUST NOT 默认拿 `opsx:ff` 起手",
                      "模型 MUST NOT 自行选 `opsx:ff` 绕过拷问")


def test_human_carriers_state_the_sunset_thresholds_and_disposition():
    """sunset 那节的价值全在**具体数字**上；数字被抹掉/改软 = 条款失效。"""
    for name, path in HUMAN_SIDE.items():
        _require_flat(name, entry_section(path),
                      "连续 6 个新开 change",   # 观察窗（次数）
                      "8 周",                   # 观察窗（时间）
                      "5/6",                    # 采用率阈值
                      "0.79",                   # findings 采纳率下限
                      "75 min",                 # 阶段一墙钟上限
                      "删除 `sdflow-spec`",      # 未达标处置（不许软化成「再看看」）
                      "MUST NOT 无限期延长观察窗")


def test_human_side_and_canonical_use_the_same_wording():
    """人读侧与 AI 读侧（canonical）**同串**——不许各写各的。"""
    canonical = GENERATION.read_text(encoding="utf-8")
    shared = (
        "**默认走 `/sdflow-spec`**",
        "MUST NOT 默认拿 `opsx:ff` 起手",
        "① 需要 wayfinder 跨会话铺图（`sdflow-spec` 不覆盖该职责）；"
        "② 用户明确要求分步执行；③ `sdflow-spec` 因环境原因不可用"
        "（未跑 setup / Codex 宿主降级不可接受）",
    )
    for n in shared:
        assert flat(n) in flat(canonical), (
            f"canonical（generation-process.md §四）里找不到「{n}」"
        )
    for name, path in HUMAN_SIDE.items():
        _require_flat(name, entry_section(path), *shared)


# ── ⑨ docs/ 下呈现「阶段一流程」的人读载体：不许只画旧三步 ────────────────
#     它们不是规则真相源，但人从它们读到入口 —— 只写 explore→ff→grill 就是 D10 的分叉形态。

def test_ff0_entry_roster_includes_branch_a():
    """三处「哪些入口殊途同归调 `openspec new change`」的清单 MUST 含分支 A 的 `/sdflow-spec`。

    漏它不是措辞问题：清单的**用途**就是回答「我这条路会不会被 FF-0 拦」。只列四个 opsx
    入口 ⇒ 读者读成「走 `/sdflow-spec` 不过 FF-0」，而 `sdflow-spec` 相位 B ③ 就是
    `openspec new change "<name>"`，照样被拦。
    """
    for name, path in FF0_ROSTER_CARRIERS.items():
        assert has_line(path, "opsx:onboard", "sdflow-spec"), (
            f"{name} 的「共用 `openspec new change` 入口」清单里没有 `/sdflow-spec` —— "
            "分支 A 同样撞 FF-0 守卫（相位 B ③ 建 change 目录），清单漏它即误导"
        )


def test_docs_stage_one_carriers_present_branch_a():
    for name, (path, anchors) in DOCS_CARRIERS.items():
        for needles in anchors:
            assert has_line(path, *needles), (
                f"{name} 里找不到同时含 {needles!r} 的单行 —— 该文档的这一处仍只呈现"
                "旧三步，人从它读到的入口与 canonical 分叉（D10 / SA-11）"
            )
