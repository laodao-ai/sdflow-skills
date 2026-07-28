"""producer 侧写死的 checkpoint slug ↔ `retro_report.map_stage` 词表的一致性守卫。

【为什么要有本文件】[impl-review-fix] F5
两处硬编码、零守卫：**产出侧**是各 producer 文件里逐字写死的
`checkpoint-commit.sh <slug> "<描述>"`（模型照抄执行），**消费侧**是
`sdflow-retro/scripts/retro_report.py::_STAGE_RULES` 的前缀词表。
SKILL.md 改一个 slug、词表没跟 ⇒ 该阶段的墙钟**静默**落进 `unknown` 桶
——不报错、不缺文件，只有 retro 报告的数字悄悄变难看。

这**已经是第二次复发**：`sdflow-spec-grill` / `sdflow-spec-generate` 落 unknown 是第一次
（dogfood 实测），`sdflow-code-review` / `<change>:plan` 是第二次（本轮双轴审 F1）。
逐条补词表是点补；本文件把**整片面**钉住：**每一个 producer 文件里出现的 slug，
经 `map_stage` MUST NOT 落 unknown**。新加 slug 而忘了配词表 ⇒ 当场红。

【期望集为什么是这四片，不是「全仓」】[impl-review-fix fix2] F-C（面治）
`grep -rn "checkpoint-commit.sh"`（不加 `--include`）全仓扫过一遍，命中分两类：

- **producer（会被照抄执行 ⇒ 本文件必须覆盖）** —— 见 `PRODUCER_GLOBS`：
  各 `*/SKILL.md`（模型读了就跑）· `sdflow-init/assets/workflow/**/*.md`（**下发给下游项目
  的权威源**，`sdflow-init update` 推给每一个消费仓）· `openspec/workflow/**/*.md`（本仓的
  已解析副本，`gen_workflow_guide` 刷新）· `assets/hack/checkpoint-commit.sh` 自身的 `--help`
  样例（人照着敲）。**上一版只 glob `*/SKILL.md`，漏掉后三片。**
- **非 producer（描述性散文 / 历史件 ⇒ 不纳入）** —— `docs/**`（讲这套工作流是怎么回事，
  没人从这里执行）· `openspec/specs/**` 与 `openspec/adr/**`（规格与决策记录）·
  `openspec/changes/**`（含 archive 的 per-change 四件套与计划文件 `tickets.md` /
  `superpowers-plan.md`〔D5：两轨计划文件名分列〕：**一次性、已执行完**，它们的 slug 早已在
  git 历史里定型，回头改词表也追不回来）·
  各 `tests/`（夹具字面量）。把它们纳入 = 让守卫去管一堆改不动的历史文本。

🔴 **边界（本门证明什么、不证明什么）**：
  · 证明 —— 「producer 写出的 slug 都能被归类」。
  · **不证明** —— 归类得*对不对*（`sdflow-spec-generate → ff` 这条对不对是判断，无确定性信号），
    也不证明模型真的执行了那条命令（那是运行时行为，git 历史里才有）。
"""
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# ── 消费侧：从文件路径加载 retro_report，取它**真正在用**的 map_stage ────────────────
# MUST NOT 在此复刻一份词表 —— 复刻出来的守卫守的是自己，不是被消费的那份实现。
_RR_PATH = REPO / "sdflow-retro" / "scripts" / "retro_report.py"
_rr_spec = importlib.util.spec_from_file_location("_retro_report_for_slug_guard", _RR_PATH)
_retro_report = importlib.util.module_from_spec(_rr_spec)
_rr_spec.loader.exec_module(_retro_report)   # 模块自己会 sys.path.insert 自己的目录
map_stage = _retro_report.map_stage

# ── 产出侧：从 producer 文件里抠 `checkpoint-commit.sh <slug>` ─────────────────────
# 期望集见文件头「为什么是这四片」。新增一片 producer ⇒ 在这里加 glob。
PRODUCER_GLOBS = (
    "*/SKILL.md",                             # 各 skill 指令（模型照抄执行）
    "sdflow-init/assets/workflow/**/*.md",    # bundle 权威源（下发给每个消费仓）
    "openspec/workflow/**/*.md",              # 本仓已解析副本（gen_workflow_guide 刷新）
    "sdflow-init/assets/hack/checkpoint-commit.sh",   # 脚本 --help 样例（人照着敲）
)

# 有界形态（基准 5）：脚本名之后紧跟一个 bare / 单引号 / 双引号 token，取到即止。
# 认不出的形态**不会**被静默跳过 —— 下方 MIN_CALLSITES 兜底（抠不到东西 = 恒真锚）。
_SLUG_RE = re.compile(
    r"checkpoint-commit\.sh\s+"
    r"(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z0-9_.:<>{}\-]+))"
)

# SKILL.md 里的 slug 带占位符（模型运行时替换）。这是一个**有界**集合：
# 每个占位符给一个合法样例值，替换后若仍残留 `<` ⇒ 出现了新占位符 ⇒ 判红（fail-closed），
# 逼人回来登记，MUST NOT 静默放过。
PLACEHOLDERS = {
    "<change>": "demo-change",
    "<N>": "1",
    "<slug>": "does-something",
    "<step>": "grill",
    "<desc>": "d",
}

# 抠到的调用点数量下限 —— 防「正则一个字都没匹配上 ⇒ 循环空转 ⇒ 恒真绿」。
# 语义是下限：新增调用点计数上升，不红；删光/正则失配则立刻打到下限之下。
# 当前实测 17 处：SKILL.md 侧 9（sdflow-code-review ×2 / sdflow-spec-review ×3 /
# sdflow-spec ×2 / sdflow-implement ×2）+ [F-C] 新纳入的 8（bundle 权威源 ×3 /
# 本仓 workflow 副本 ×1 / `checkpoint-commit.sh --help` 样例 ×4）。
MIN_CALLSITES = 17


def _resolve(slug):
    for ph, val in PLACEHOLDERS.items():
        slug = slug.replace(ph, val)
    return slug


def collect_slugs():
    """→ [(producer 相对路径, 行号, 原始 slug)]，扫 `PRODUCER_GLOBS` 全部命中文件。"""
    files = []
    for pat in PRODUCER_GLOBS:
        for f in sorted(REPO.glob(pat)):
            if f.is_file() and f not in files:      # glob 之间可能重叠 ⇒ 去重
                files.append(f)
    found = []
    for path in files:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for m in _SLUG_RE.finditer(line):
                slug = next(g for g in m.groups() if g)
                found.append((str(path.relative_to(REPO)), lineno, slug))
    return found


def test_extractor_actually_finds_the_callsites():
    """恒真锚防线：正则失配 / SKILL.md 改了写法 ⇒ 本用例先红，而不是主用例静默变空转。"""
    found = collect_slugs()
    assert len(found) >= MIN_CALLSITES, (
        f"只抠到 {len(found)} 个 checkpoint-commit.sh 调用点（下限 {MIN_CALLSITES}）——"
        f"要么调用点被删了，要么 producer 换了写法而 _SLUG_RE 没跟上。抠到的：{found}"
    )


def test_producer_globs_cover_the_downstream_authority_bundle():
    """[impl-review-fix fix2] F-C：期望集 MUST 含 bundle 权威源 —— 只 glob `*/SKILL.md` 是漏的。

    `sdflow-init/assets/workflow/` 是**下发给每个消费仓**的 `openspec/workflow/` 的唯一
    权威源；它里面的 `checkpoint-commit.sh <slug>` 与 SKILL.md 的同性质（模型照抄执行），
    却曾整片落在守卫视野之外。
    """
    files = {rel for rel, _, _ in collect_slugs()}
    for want in ("sdflow-init/assets/workflow/WORKFLOW-GUIDE.md",
                 "sdflow-init/assets/workflow/prompts/step6-writing-plans.md",
                 "sdflow-init/assets/workflow/workflow.md",
                 "openspec/workflow/WORKFLOW-GUIDE.md",
                 "sdflow-init/assets/hack/checkpoint-commit.sh"):
        assert want in files, (
            f"producer `{want}` 的 checkpoint slug 没被抠到 —— 期望集或 _SLUG_RE 退化了。"
            f"当前覆盖到的文件：{sorted(files)}"
        )


def test_every_skill_slug_is_classifiable():
    """每个 producer 写死的 slug 经 map_stage MUST NOT 落 unknown。"""
    bad = []
    for rel, lineno, slug in collect_slugs():
        resolved = _resolve(slug)
        assert "<" not in resolved, (
            f"{rel}:{lineno} 的 slug `{slug}` 含未登记的占位符 —— "
            f"请在 PLACEHOLDERS 里补一个样例值（fail-closed，MUST NOT 静默跳过）"
        )
        if map_stage(f"checkpoint({resolved})") == "unknown":
            bad.append(f"{rel}:{lineno}  `{slug}` → `{resolved}` 落 unknown")
    assert not bad, (
        "以下 SKILL.md 的 checkpoint slug 在 retro_report._STAGE_RULES 里无归类，"
        "该阶段墙钟会静默落进 unknown 桶：\n  " + "\n  ".join(bad)
    )
