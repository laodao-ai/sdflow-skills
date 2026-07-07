# mlh-p5-gate-frontmatter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 ship-gate 状态锚（design_approved/verify/code_review）从报告正文 inline HTML 注释迁到报告 YAML frontmatter，gate live 读 frontmatter、归档 frontmatter+inline 双读，根治 B4/B5 正文提及假命中。

**Architecture:** 新增单一自持 `parse_ship_gate_frontmatter(text)` helper（手写 stdlib、不 import yaml），live 读与归档 git-show 文本读**都调它**（防漂移）。live 报告三类结论的**全部 4 类读点**（`anchors_in`-design + `pick_exclusive`×3 + peek + `anchor_set`熔断）统一走「frontmatter 优先→过渡期回退 inline」。dual-read 读侧先行（零破坏）→ 三 producer 迁写侧 → 退役全 live inline 读点。

**Tech Stack:** Python 3 stdlib（无第三方）· pytest · Markdown SKILL 模板。

## Global Constraints

- **零 import yaml**：`ship_gate.py` 手写 stdlib frontmatter 解析，保零第三方依赖不变量（现 import 仅 `argparse/json/re/subprocess/sys/pathlib`）。契约测试断言 `"import yaml" not in ship_gate.py 源码`。
- **D1 致命 · live 读点完整集合**：live inline 读点 = `anchors_in`(design-approved, ship_gate.py:506) + `pick_exclusive`×3(verify 早检:519/终门:588、code-review:563) + peek `anchors_in`(verify=FAIL:576) + `anchor_set`熔断(250)。frontmatter 化/退役 MUST 覆盖全部，MUST NOT 只动 `anchors_in`（否则 verify/code-review 迁后读不出→STEP_IN_PROGRESS 永卡）。
- **D2 · 只认文件首块**：只识别文件第 1 行 `---`（先去 BOM）起、到下一 `---` 止的唯一首块；`splitlines()` 口径；正文 `---` 横线 / `ship-gate:` 键 MUST NOT 参与（报告正文横线密布）。
- **D3 · 坏≠无键 + 退出码映射**：三分支——有效键→用之 / 顶层无 ship-gate 键→过渡期回退 inline / 键存在但坏→**永不回退、fail-closed**。退出码确定映射：越域/重复键/坏语法/类型不符→**UNKNOWN(exit 6)**；纯缺字段（半成品）→既有无锚语义（spec-review→REFUSE_START(3)、verify·code-review→STEP_IN_PROGRESS(0)）。消除「停下或进行中」歧义。
- **D4 · 共用严格 helper**：单一 `parse_ship_gate_frontmatter(text)`，live 读与归档 git-show 文本读都调它；归档坏 frontmatter→fail-safe `none` 不回退；Q4 已决 frontmatter 有效 PASS 即采信、不交叉扫 inline FAIL + `ship_gate.py`「已知不覆盖」登记盲区。
- **D5 · 冲突承载**：verify 单键无法承载行级并存，**重复键→UNKNOWN 是唯一冲突触发**（块内枚举全部同名键计数，非见第二个即覆盖）。
- **D12 · fail-closed 可观测**：fail-closed 的 `emit()` reason MUST 携带被拒字段名 + 失败类别（unterminated/duplicate-key/out-of-domain/bad-type/tab-indent）。
- **fail-closed + pytest 坏输入断言退出码**（adr/0006 R3）；门禁语义（退出码/UNKNOWN/命名空间/新鲜度分域）对未迁部分不变。
- **checkpoint TAG 格式**：每 Task commit 步 MUST 用 `~/.sdflow/hack/checkpoint-commit.sh mlh-p5-gate-frontmatter:task<N>-<slug> "<描述>"`（带命名空间 + task<N>- 横杠，ship_gate TAG_RE 主锚契约），勿改标签。
- **Migration 顺序纪律（D10 symlink 窗口）**：读侧 dual-read 先落 commit + 本地 `bash setup.sh` 生效，再改 producer（skill 全局 symlink 即时生效，改 sdflow-done/ship_gate 中途窗口波及并发 /sdflow-done；分步提交缩窗口）。

---

## Pre-Flight（Task 1 起手第一步，P0 决策门）

**tasks 0.6 P0 门**：写任何 producer 前先实测 `openspec` CLI 对带 `ship-gate:` frontmatter 的 report 是否报错——
```bash
# 在临时样例报告加 frontmatter 后跑
openspec validate mlh-p5-gate-frontmatter 2>&1 | tail -5
```
预期：valid（report .md 非 openspec 校验对象，validate 只吃 proposal/tasks/specs）。**若报错 → NO-GO，停下上抛**（整 frontmatter 方案需返工）。GO 才继续。

---

### Task 1: `parse_ship_gate_frontmatter` 共用解析核心 + 坏输入退出码映射

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（新增 helper + 常量，在 `_line_scoped_hits` 段之后 ~236 行附近）
- Test: `sdflow-ship/tests/test_frontmatter_parse.py`（新建）

**Interfaces:**
- Produces: `parse_ship_gate_frontmatter(text: str) -> tuple[dict, tuple|None]` — 返回 `(state, error)`：`state` = `{field: value}` 已校验（空 dict = absent 无 frontmatter/无 ship-gate 键）；`error` = `None`（干净）或 `(field_or_"frontmatter", category)`（坏，category ∈ {unterminated, duplicate-key, out-of-domain, bad-type, tab-indent}）。live 与归档读都调它。
- Produces: `FIELD_ENUMS` dict 常量。

- [ ] **Step 1: 写失败测试（干净解析 + 首块锚定 + 坏输入穷举）**

```python
# sdflow-ship/tests/test_frontmatter_parse.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from ship_gate import parse_ship_gate_frontmatter as P

def test_clean_verify_pass():
    state, err = P("---\nship-gate:\n  verify: PASS\n---\n# 报告正文\n")
    assert state == {"verify": "PASS"} and err is None

def test_clean_design_approved_bool():
    state, err = P("---\nship-gate:\n  design_approved: true\n---\n")
    assert state == {"design_approved": True} and err is None

def test_absent_no_frontmatter():          # 无首行 --- = absent（非坏）
    state, err = P("# 报告\n正文\n")
    assert state == {} and err is None

def test_body_dashes_not_frontmatter():    # D2：正文中部 --- 块不当 frontmatter
    txt = "# 报告\n\n## 综述\n\n---\nship-gate:\n  verify: PASS\n---\n正文"
    state, err = P(txt)
    assert state == {} and err is None      # 首行非 ---，absent

def test_bom_stripped():                   # D2：去 BOM
    state, err = P("﻿---\nship-gate:\n  verify: PASS\n---\n")
    assert state == {"verify": "PASS"} and err is None

def test_unterminated_is_error():          # --- 不配对 → 坏
    state, err = P("---\nship-gate:\n  verify: PASS\n")
    assert err is not None and err[1] == "unterminated"

def test_duplicate_field_key_error():      # D5：重复键 → 坏（不取最后一个）
    state, err = P("---\nship-gate:\n  verify: PASS\n  verify: FAIL\n---\n")
    assert err is not None and err[1] == "duplicate-key"

def test_out_of_domain_error():            # 越域
    state, err = P("---\nship-gate:\n  verify: MAYBE\n---\n")
    assert err is not None and err[0] == "verify" and err[1] == "out-of-domain"

def test_bad_bool_type_error():            # design_approved 非 bool
    state, err = P("---\nship-gate:\n  design_approved: yes\n---\n")
    assert err is not None and err[1] == "bad-type"

def test_tab_indent_error():               # tab 缩进 → 坏
    state, err = P("---\nship-gate:\n\tverify: PASS\n---\n")
    assert err is not None and err[1] == "tab-indent"

def test_crlf_stripped():                  # CRLF 值不残留 \r
    state, err = P("---\r\nship-gate:\r\n  verify: PASS\r\n---\r\n")
    assert state == {"verify": "PASS"} and err is None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest sdflow-ship/tests/test_frontmatter_parse.py -x`
Expected: FAIL（`parse_ship_gate_frontmatter` not defined）

- [ ] **Step 3: 实现 helper（手写 stdlib，不 import yaml）**

在 `ship_gate.py` 的 `_line_scoped_hits` 定义后插入：

```python
# [mlh-p5] frontmatter 状态解析（手写 stdlib，不 import yaml——保零依赖不变量）。
# live 读与归档 git-show 文本读共用此单一核心（防漂移，D4）。
FIELD_ENUMS = {
    "design_approved": (True, False),   # bool
    "verify": ("PASS", "FAIL"),
    "code_review": ("pass", "blocked"),
}

def parse_ship_gate_frontmatter(text):
    """解析报告 frontmatter 的 ship-gate 状态。返回 (state, error)：
      state: {field: value}（已枚举校验）；{} = absent（无 frontmatter / 无 ship-gate 键）
      error: None（干净）或 (field|'frontmatter', category)
             category ∈ unterminated|duplicate-key|out-of-domain|bad-type|tab-indent
    D2 只认文件首块：首行须 '---'（去 BOM）；正文 --- 横线不参与。
    D3 坏≠无：absent(state={},error=None) vs 坏(error!=None) 由调用方分流退出码。
    D5 重复键→duplicate-key（枚举全部同名键计数，非取最后一个）。"""
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.splitlines()               # 统一 \r\n/\n（值不残留 \r）
    if not lines or lines[0].strip() != "---":
        return {}, None                     # absent：无首块 frontmatter
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, ("frontmatter", "unterminated")
    block = lines[1:end]
    # 找顶层 ship-gate: 键（0 缩进），统计出现次数（重复→坏）
    top_idx = [i for i, ln in enumerate(block)
               if ln.rstrip() == "ship-gate:" and not ln[:1].isspace()]
    if len(top_idx) == 0:
        return {}, None                     # absent：有 frontmatter 但无 ship-gate 键
    if len(top_idx) > 1:
        return {}, ("ship-gate", "duplicate-key")
    # 收集 ship-gate: 下方缩进的 field: value（下一个 0 缩进非空行为界）
    start = top_idx[0] + 1
    state, seen = {}, {}
    for ln in block[start:]:
        if ln.strip() == "":
            continue
        if not ln[:1].isspace():
            break                           # 回到 0 缩进 = ship-gate 块结束
        if "\t" in ln[:len(ln) - len(ln.lstrip())]:
            return {}, ("frontmatter", "tab-indent")
        body = ln.strip()
        if ":" not in body:
            return {}, ("frontmatter", "bad-type")
        field, _, raw = body.partition(":")
        field, raw = field.strip(), raw.strip()
        if field not in FIELD_ENUMS:
            continue                         # 非本 schema 字段（外来 metadata），忽略
        seen[field] = seen.get(field, 0) + 1
        if seen[field] > 1:
            return {}, (field, "duplicate-key")
        val = _coerce_ship_gate_value(field, raw)
        if val is _BAD_TYPE:
            return {}, (field, "bad-type")
        if val not in FIELD_ENUMS[field]:
            return {}, (field, "out-of-domain")
        state[field] = val
    return state, None


_BAD_TYPE = object()

def _coerce_ship_gate_value(field, raw):
    if field == "design_approved":
        if raw == "true":
            return True
        if raw == "false":
            return False
        return _BAD_TYPE                     # yes/1/True 等非规范 bool → 坏
    return raw                               # verify/code_review：字符串，交枚举校验
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest sdflow-ship/tests/test_frontmatter_parse.py -v`
Expected: 全 PASS

- [ ] **Step 5: P0 决策门（tasks 0.6）** — 实测 `openspec validate mlh-p5-gate-frontmatter`，确认带 frontmatter 的 report 不使 CLI 报错（GO）；NO-GO 则停下上抛。

- [ ] **Step 6: Commit**

```bash
git add sdflow-ship/scripts/ship_gate.py sdflow-ship/tests/test_frontmatter_parse.py
~/.sdflow/hack/checkpoint-commit.sh mlh-p5-gate-frontmatter:task1-frontmatter-parser "手写 stdlib frontmatter 解析核心 parse_ship_gate_frontmatter(首块锚定/去BOM/CRLF/重复键/越域/tab→坏) + 坏输入穷举测试 + P0 门 openspec validate GO"
```

---

### Task 2: live 读点统一 dual-read（frontmatter 优先→过渡期回退 inline，零破坏）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（新增 `live_state` 分流 helper + 退出码映射；改 `decide()` 的 4 类 live 读点调用）
- Test: `sdflow-ship/tests/test_frontmatter_live_read.py`（新建）

**Interfaces:**
- Consumes: `parse_ship_gate_frontmatter`（Task 1）
- Produces: `live_ship_gate_field(path, field, on_bad) -> value|None|"__absent__"` — live 读某字段：frontmatter 有效→值；absent→回退 inline（调用方传 inline 读法）；坏→按 `on_bad` 分流退出码（D3 坏永不回退）。

- [ ] **Step 1: 写失败测试（dual-read 三分支 + 退出码映射）**

```python
# sdflow-ship/tests/test_frontmatter_live_read.py — 构造 live change 目录报告，断言 gate 判决
# （沿用现有 test_gate_*.py 的 fixture 构造法：写 openspec/changes/{c}/ 报告 + 跑 decide）
# 用例覆盖：
#   test_live_verify_frontmatter_pass  —— verify-report frontmatter verify: PASS → 正常推进
#   test_live_verify_absent_fallback_inline —— 无 ship-gate 键 + 旧 inline 锚 → 回退读出（过渡期）
#   test_live_verify_bad_no_fallback   —— frontmatter verify: MAYBE(越域) → UNKNOWN(6)，MUST NOT 回退 inline
#   test_live_body_mention_immune      —— frontmatter 无键 + 正文提及 ship-gate.verify: PASS → 不命中
#   test_live_design_approved_frontmatter —— spec-review-report frontmatter design_approved: true → 过设计门
#   test_live_dup_key_unknown          —— 重复 verify 键 → UNKNOWN(6)
# （每条断言 gate 退出码/verdict；具体 fixture 骨架见现有 test_gate_preflight.py:29 / test_gate_tail.py:38）
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest sdflow-ship/tests/test_frontmatter_live_read.py -x`
Expected: FAIL（live dual-read 未实现，现只读 inline）

- [ ] **Step 3: 实现 live 分流 + 退出码映射，改 4 类读点**

在 `ship_gate.py` 加分流 helper（把坏→退出码映射集中）：

```python
# [mlh-p5 D3] 坏 frontmatter → 退出码：越域/重复键/坏语法/类型不符 → UNKNOWN(6)（歧义须人裁、防 exit0 重跑死循环）。
def _fail_closed_on_bad(err, label):
    field, cat = err
    emit("UNKNOWN", EXIT_UNKNOWN, None,
         f"{label} frontmatter 坏（字段={field} 类别={cat}）→ fail-closed 无有效状态，请人工修复")  # D12 reason 点名

def live_ship_gate_state(path, label):
    """live 读某报告的 ship-gate 状态 dict。frontmatter 有效→state；坏→UNKNOWN(6) 停（不回退）；
    absent→返回 None 交调用方回退 inline（过渡期 D6/D3）。"""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    state, err = parse_ship_gate_frontmatter(text)
    if err is not None:
        _fail_closed_on_bad(err, label)      # 坏永不回退，直接 fail-closed
    if state:
        return state                         # 有效键
    return None                              # absent → 调用方回退 inline
```

改 `decide()` 的读点（**全部 4 类，D1**）：
- **design-approved**（~506，现 `anchors_in(spec_review, [ANCHOR_DESIGN])`）→ 先 `live_ship_gate_state(spec_review,"spec-review")`，有 `design_approved==True` 则过门；absent 回退 `anchors_in`。
- **verify 早检/终门**（519/588，现 `pick_exclusive(vfile, PASS, FAIL)`）→ 先 live_state 取 `verify`（PASS/FAIL）；absent 回退 `pick_exclusive`。
- **code-review**（563，现 `pick_exclusive(cr, CR_PASS, CR_BLOCKED)`）→ 先 live_state 取 `code_review`；absent 回退 `pick_exclusive`。
- **peek verify=FAIL**（576，现 `anchors_in(vf_peek, [ANCHOR_VERIFY_FAIL])`）→ 先 live_state；absent 回退 inline。
- **anchor_set 熔断**（250）→ 见 Task 6（退役时迁「状态集合」，过渡期保留 inline 语义不影响熔断正确性，此处仅登记）。

> 过渡期（producer 未迁）：所有读点 absent→回退 inline，零破坏。

- [ ] **Step 4: 运行确认通过 + 全仓回归**

Run: `pytest sdflow-ship/tests/test_frontmatter_live_read.py -v && pytest sdflow-ship/tests/ -q`
Expected: 新测试 PASS，既有 gate 测试**全绿**（过渡期回退 inline 保兼容）

- [ ] **Step 5: 本地 setup 生效（symlink 窗口纪律 D10）**

Run: `bash setup.sh`（让 ship_gate.py 改动在运行环境生效，再改 producer）

- [ ] **Step 6: Commit**

```bash
git add sdflow-ship/scripts/ship_gate.py sdflow-ship/tests/test_frontmatter_live_read.py
~/.sdflow/hack/checkpoint-commit.sh mlh-p5-gate-frontmatter:task2-live-dual-read "live 4类读点(design anchors_in/verify·cr pick_exclusive×3/peek)统一 frontmatter优先→absent回退inline，坏→UNKNOWN(6)不回退(D3)；过渡期零破坏全绿"
```

---

### Task 3: 归档 dual-read（`archived_verify_state` 加 frontmatter 读，共用 helper）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（`archived_verify_state` ~151）
- Test: `sdflow-ship/tests/test_frontmatter_archived.py`（新建）

**Interfaces:**
- Consumes: `parse_ship_gate_frontmatter`（Task 1）

- [ ] **Step 1: 写失败测试（归档双读 + 坏 fail-safe + Q4 不交叉扫）**

```python
# test_archived_frontmatter_read —— 归档 verify-report frontmatter verify: PASS → archived_verify_state=='pass'
# test_archived_inline_read      —— 归档旧 inline <!-- ship-gate: verify=PASS --> → 'pass'（保留）
# test_archived_frontmatter_bad_fail_safe —— 归档坏 frontmatter → 'none'（不回退 inline 掩盖，不假 SHIPPED）
# test_archived_q4_frontmatter_wins —— 好 frontmatter PASS + 残留 inline FAIL → 'pass'（Q4：frontmatter 即真相，不交叉扫）
# 基于行为构造 fixture，MUST NOT 硬编码 88/168（D13）
```

- [ ] **Step 2: 运行确认失败** — `pytest sdflow-ship/tests/test_frontmatter_archived.py -x` → FAIL

- [ ] **Step 3: 改 `archived_verify_state`（frontmatter 优先→absent 回退 inline，坏→none）**

```python
def archived_verify_state(root, ref, archive_dir):
    rc, out = run_git_rc(root, "show",
                         f"{ref}:openspec/changes/archive/{archive_dir}/verify-report.md")
    if rc != 0:
        return "none"
    # [mlh-p5 D4/G2] frontmatter 优先（新归档），共用同一严格 helper
    state, err = parse_ship_gate_frontmatter(out)
    if err is not None:
        return "none"                        # 坏 frontmatter → fail-safe（不回退 inline 掩盖）
    if "verify" in state:                    # Q4：frontmatter 有效即采信，不再交叉扫 inline
        return "pass" if state["verify"] == "PASS" else "none"
    # absent → 回退旧 inline 读半场（迁移前旧归档，永久保留）
    hits, unbalanced = _line_scoped_hits(out, [ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL])
    if unbalanced:
        return "none"
    has_pass, has_fail = ANCHOR_VERIFY_PASS in hits, ANCHOR_VERIFY_FAIL in hits
    if has_pass and has_fail:
        return "conflict"
    return "pass" if has_pass else "none"
```

同步 `ship_gate.py` 头注释「已知不覆盖」登记 Q4 盲区（好 frontmatter PASS 掩盖残留 inline FAIL；迁移后新归档无残留 inline，风险低）。

- [ ] **Step 4: 运行确认通过 + 回归** — `pytest sdflow-ship/tests/ -q` 全绿

- [ ] **Step 5: Commit**

```bash
git add sdflow-ship/scripts/ship_gate.py sdflow-ship/tests/test_frontmatter_archived.py
~/.sdflow/hack/checkpoint-commit.sh mlh-p5-gate-frontmatter:task3-archived-dual-read "archived_verify_state frontmatter优先→absent回退inline(共用helper防漂移)，坏→fail-safe none，Q4 frontmatter有效不交叉扫inline+头注登记盲区"
```

---

### Task 4: 三 producer SKILL 迁移（写侧 frontmatter，读侧已就绪）

**Files:**
- Modify: `~/.claude/skills/sdflow-spec-review/SKILL.md`（拍板回写段 ~108-118）
- Modify: `~/.claude/skills/sdflow-done/SKILL.md`（verify 模板 ~78-81）
- Modify: `~/.claude/skills/sdflow-code-review/SKILL.md`（报告格式 ~186-190）
- Modify: `sdflow-ship/scripts/ship_gate.py`（docstring 契约块 ~5-12 同步 frontmatter shape）
- Test: `sdflow-ship/tests/test_anchor_contract.py`（迁移）

> 这些 SKILL 在**本仓**（sdflow-*/），改后须 `bash setup.sh` 生效（symlink）。

- [ ] **Step 1: 迁 sdflow-spec-review 拍板回写（D8/D9）** — 拍板锚从 `<!-- ship-gate: design-approved -->`（正文末尾）改为**报告头部 frontmatter prepend**：
```yaml
---
ship-gate:
  design_approved: true
---
```
保留正文人读拍板记录行；更新〔SR-M〕交叉引用（lens-metric 锚仍在正文注释、不迁——拍板时头 frontmatter `design_approved` + 正文 lens-metric 注释两处各写，SR-M 措辞订正指向两处）。

- [ ] **Step 2: 迁 sdflow-done verify 模板** — verify-report frontmatter `ship-gate.verify: PASS|FAIL`（头部），正文保留 `✅ PASS`/`❌ FAIL` 人读结论行。

- [ ] **Step 3: 迁 sdflow-code-review 报告格式** — code-review-report frontmatter `ship-gate.code_review: pass|blocked`（头部），正文保留人读结论行。

- [ ] **Step 4: 同步 ship_gate.py docstring 契约块（~5-12）** — 把「机判锚 = 5 个 inline 注释串」更新为「live=frontmatter ship-gate.{field} / 归档=frontmatter+inline dual-read」，与三 SKILL 模板双向钉死。

- [ ] **Step 5: 迁 test_anchor_contract.py（字段名精确断言防漂移）**

```python
# 断言三 producer 模板输出 frontmatter 字段（精确下划线名，防 code_review vs code-review 连字符漂移）
def test_producer_frontmatter_fields():
    # 从三 SKILL.md 提取模板 frontmatter，断言字段名 ∈ {design_approved, verify, code_review}（下划线）
    # 且枚举值 ∈ FIELD_ENUMS；断言 gate parse_ship_gate_frontmatter 能读出
    assert "code_review" in ...   # 下划线，非 code-review
def test_no_import_yaml():
    src = (pathlib.Path(...)/"ship_gate.py").read_text()
    assert "import yaml" not in src   # 零依赖不变量
```

- [ ] **Step 6: setup 生效 + 运行确认** — `bash setup.sh && pytest sdflow-ship/tests/test_anchor_contract.py -v` PASS

- [ ] **Step 7: Commit**

```bash
git add -A
~/.sdflow/hack/checkpoint-commit.sh mlh-p5-gate-frontmatter:task4-producer-migrate "三producer(spec-review拍板/done verify/code-review)迁frontmatter头部写入+正文保留人读行+SR-M交叉引用订正+docstring契约双向钉死+test_anchor_contract字段名精确断言(防下划线漂移)+no_import_yaml"
```

---

### Task 5: 契约测试盘面迁移 + 正文免疫 + B5 语料（D6）

**Files:**
- Modify/Test: `sdflow-ship/tests/test_gate_{freshness,tail,anchor_scope,terminal,preflight,impl_progress}.py`（审计 ~45 处 live inline fixture）
- Remove from migration scope: `test_producer_parser_contract.py`（错配，0 处 ship-gate 锚——不动它、不误迁）
- Test: B5 聚合语料测试

- [ ] **Step 1: 审计 8 个 test_gate_* 文件的 fixture（live vs 归档分流清单）** — 逐 fixture 标记：写进 active change 目录的 = **live→迁 frontmatter**；`git show` 归档的 = **归档→留 inline**。产出迁移前后 fixture 计数（退役步 DoD）。

- [ ] **Step 2: 迁 live fixture 到 frontmatter** — 把 live 报告 fixture 的 inline 锚（如 `test_gate_preflight.py:29` 的 `<!-- ship-gate: design-approved -->`）改为 frontmatter head。归档 fixture 保留 inline。

- [ ] **Step 3: 正文免疫测试（B4/B5 根治验证）**

```python
def test_live_body_mention_immune():   # frontmatter 无键 + 正文提及锚字面 → 不命中
    # spec-review-report 正文含 <!-- ship-gate: design-approved --> 但 frontmatter 无 design_approved
    # → gate REFUSE_START（未过设计门），MUST NOT 因正文提及假过门
```

- [ ] **Step 4: B5 聚合语料迁 frontmatter（live 侧）+ 保留归档 inline 语料** — 见现有 B5 语料测试，live 部分转 frontmatter。

- [ ] **Step 5: 全仓回归** — `pytest sdflow-ship/tests/ -q` 全绿

- [ ] **Step 6: Commit**

```bash
git add -A
~/.sdflow/hack/checkpoint-commit.sh mlh-p5-gate-frontmatter:task5-test-migrate "审计8个test_gate_*文件live/归档fixture分流+live迁frontmatter/归档留inline+正文免疫测试(B4/B5根治验证)+B5语料迁移；test_producer_parser_contract错配不动"
```

---

### Task 6: 退役全 live inline 读点 + anchor_set 熔断迁移 + 自身报告迁移（D1/D10/D11）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（退役 live inline 读半场 + anchor_set 迁状态集合）
- Modify: `sdflow-ship/SKILL.md`（熔断文案）
- Modify: `openspec/changes/mlh-p5-gate-frontmatter/{spec-review-report,verify-report,code-review-report}.md`（自身报告迁 frontmatter）
- Test: `sdflow-ship/tests/test_gate_breaker.py`

- [ ] **Step 1: 确认前置** — Task 3+4+5 全绿（三 producer 全迁、live/归档测试通过）后才退役。

- [ ] **Step 2: 退役 live inline 读半场（D1 全 4 类读点）** — Task 2 的 4 类读点 absent 回退分支删除（live 只读 frontmatter），`anchors_in`/`pick_exclusive` 对 live 的调用移除；`_line_scoped_hits` 归档读半场（`archived_verify_state` 内）**保留**。

- [ ] **Step 3: anchor_set 熔断迁「状态集合」（D11）** — `anchor_set(text)` 改为读 frontmatter 状态集合（复用 parse helper），更新 `sdflow-ship/SKILL.md` 熔断文案；`test_gate_breaker.py` 加用例（before 无状态、after 仅 frontmatter PASS → 判有进展）。

- [ ] **Step 4: 头注释更新** — `ship_gate.py` 头注「live 读 frontmatter / 归档读 frontmatter+inline dual-read」分流说明 + 「已知不覆盖」清单同步（Q4 盲区）。

- [ ] **Step 5: 自身报告迁 frontmatter（D10）** — 把本 change 的 `spec-review-report.md`（现 inline `<!-- ship-gate: design-approved -->`）、`verify-report.md`、`code-review-report.md` 的 inline 锚迁为 frontmatter head（合法迁移收尾，非越权补锚）。

- [ ] **Step 6: 全仓回归 + dogfood** — `bash setup.sh && pytest sdflow-ship/tests/ -q` 全绿；`python3 ~/.claude/skills/sdflow-ship/scripts/ship_gate.py --change mlh-p5-gate-frontmatter --root "$(git rev-parse --show-toplevel)"` 能读出自身 frontmatter design-approved（不 REFUSE on itself）。

- [ ] **Step 7: Commit**

```bash
git add -A
~/.sdflow/hack/checkpoint-commit.sh mlh-p5-gate-frontmatter:task6-retire-live-inline "退役全4类live inline读点(仅归档读半场保留)+anchor_set熔断迁状态集合+SKILL熔断文案+自身报告迁frontmatter(D10自测闭环)+头注分流说明；dogfood不REFUSE on itself"
```

---

### Task 7: 收尾同步（roadmap F6 + validate）

**Files:**
- Modify: `openspec/roadmaps/mechanical-layer-hardening/roadmap.md`（阶段 5 前置区 F6）
- Modify: `openspec/roadmaps/mechanical-layer-hardening/task-log.md`

- [ ] **Step 1: 回填 roadmap F6** — 阶段 5 前置区「归档锚精确篇数」从「~39 约数」订正为**实测 88 文件/168 锚行**（已在 design 落定，此处回填 roadmap）。

- [ ] **Step 2: task-log 加「阶段 5 完成总结」** — SHIPPED、scope、冷审 1 致命+3 高、Leg2 S1 交付。

- [ ] **Step 3: validate** — `openspec validate mlh-p5-gate-frontmatter` 通过。

- [ ] **Step 4: Commit**

```bash
git add openspec/roadmaps/
~/.sdflow/hack/checkpoint-commit.sh mlh-p5-gate-frontmatter:task7-roadmap-sync "回填roadmap F6(归档锚实测88文件/168锚行订正~39)+task-log阶段5完成总结+validate通过"
```

---

## Self-Review

- **Spec coverage**：specs A1(D1 读点集合)→Task2/6 · A2(首块锚定)→Task1 · A3(坏≠无+退出码)→Task1/2 · A4(共用helper+Q4)→Task1/3 · A5(可观测)→Task1 · D5(重复键冲突)→Task1 · D6(测试盘面)→Task5 · D7(safe_load清)→已在设计阶段 · D8/D9(producer拆细/prepend)→Task4 · D10(自身迁移/symlink)→Task2 Step5/Task6 · D11(anchor_set)→Task6 · D12(可观测)→Task1 · D13(88行为)→Task3。全覆盖。
- **Placeholder scan**：无 TBD/TODO；核心新代码（parse helper、live_ship_gate_state、archived 改法）含完整实现；既有 fixture 迁移给 file:line + 分流规则（fixture 具体内容由 implementer 按现有测试骨架迁，非 placeholder——迁移类任务的合法形态）。
- **Type consistency**：字段名全程 `design_approved`/`verify`/`code_review`（下划线）；`parse_ship_gate_frontmatter` 返回 `(state, error)` 全 Task 一致；退出码 UNKNOWN(6)/REFUSE_START(3)/STEP_IN_PROGRESS(0) 与既有常量一致。
