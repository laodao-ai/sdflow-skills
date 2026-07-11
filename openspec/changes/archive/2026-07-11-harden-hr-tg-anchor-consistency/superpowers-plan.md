# harden-hr-tg-anchor-consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 hr-tg 锚一致性一次机械化到目标态——`hr_tg_intersect`（出锚侧 M3 严格解析 + M-new catalog 全集存在性）与 `anchor_lint`（校验侧 M1 declared 硬必填 / M2 hit=declared∩HR-TG 重算 / M4 evidence 在场 / M-new），全 fail-closed、零妥协。

**Architecture:** 两工具纯 stdlib、门控外置，共享 trigger-catalog 单一源（HR-TG 成员 + 全 TG 集）。出锚侧先落 M3 严格解析与 M-new 全集解析 helper；校验侧复用同口径解析（仓内"非 import"约定 adr/0002，双份重实现由 F3 cross-tool golden 测试机械兜底）。回灌主 spec :550、原子接线两 SKILL 调用点、bundle 回灌收尾。

**Tech Stack:** Python 3 stdlib（argparse/re/pathlib）、pytest；OpenSpec bundle 分发（sdflow-init assets → setup.sh canonical → sdflow-init update 下游）。

## Global Constraints

以下逐字摘自 design.md 的 MUST / MUST NOT / SHALL 硬约束与 Compliance，每个任务的要求隐式包含本节：

- **工具真相源 = `sdflow-init/assets/workflow/tools/`**（含 `tests/`）——改这里，**MUST NOT** 只改仓根 `openspec/workflow/` 副本（那是 `sdflow-init update` 托管的下游镜像）。改后 dev checkout 跑 `bash setup.sh` 同步 canonical。
- **`--trigger-catalog` 必需**：`anchor_lint.check_hr_tg` 接必需 `--trigger-catalog`，未传 → **非零退出（fail-closed）**，**MUST NOT** WARN 降级放行（降级=fail-open 架空 M2/M4）。
- **零妥协**：**MUST NOT** 加 `--allow-legacy` flag、**MUST NOT** 加 declared grace、**MUST NOT** 留迁移旁路（B3 已核验归档不重 lint，为不存在场景留旁路 = YAGNI）。
- **纯 stdlib / 门控外置 / fail-closed**：两工具无第三方依赖、无 subprocess、不读 config、坏输入非零退出（all-or-nothing）。
- **单一源不硬编码**：HR-TG 成员 + 全 TG 集续从 `trigger-catalog.md` 读，**MUST NOT** 硬编码副本。
- **M-new 全集边界钉死（F8）**：全 TG 集只取 `## 三、触发词目录`（A–G 段）内 `fullmatch ^\s*\|\s*TG-\d+\s*\|` 的表行；正文游离 TG 提及（`命中 TG-01`/`参见 TG-99 草案`）**MUST NOT** blind-regex 纳入。
- **anchor_lint 侧 collect-not-raise（F9）**：`check_hr_tg` 新增校验就地转 violation dict、**MUST NOT** raise `EmitError`（护 human + JSON 双输出，stdout 仍合法 JSON）。
- **adr/0018 未越界**：`declared` 仍由模型给（S1 语义残余）；M2 只堵内部一致性，docs/docstring **MUST** 显式声明"不使锚 tamper-proof"（不冒充，避假绿）。
- **原子落防 skew**：§2.8 两 SKILL（`sdflow-code-review`/`sdflow-spec-review`）的 anchor_lint 调用步补 `--trigger-catalog`，**与工具改动同一 change 原子落**。
- **checkpoint 格式（ship_gate.py TAG_RE）**：每任务结尾 MUST 跑 `bash ~/.sdflow/hack/checkpoint-commit.sh "harden-hr-tg-anchor-consistency:task<N>-<slug>" "<一句话>"`——slug 含横杠且非空（如 `task1-strict-parse`），写成 `task<N>` 无尾横杠会让 gate 完成数卡 0/N。

---

## File Structure

| 文件 | 责任 | 本 change 动作 |
|---|---|---|
| `sdflow-init/assets/workflow/tools/hr_tg_intersect.py` | 出锚侧：M3 严格解析 + M-new 全集解析/存在性 | Modify（`parse_tg_set:54-62`、`_TG_TOKEN_RE:14`、加 `load_all_tg_set` + `validate_exist`） |
| `sdflow-init/assets/workflow/tools/anchor_lint.py` | 校验侧：M1/M2/M4/M-new + 必需 catalog | Modify（`check_hr_tg:163-174`、`main:207-245` 加 `--trigger-catalog`） |
| `sdflow-init/assets/workflow/tools/tests/test_hr_tg_intersect.py` | 出锚侧测试 | Modify（`_catalog` retrofit、`test_single_source_mutability` 重设计、新增 M3/M-new/F8 用例） |
| `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` | 校验侧测试 | Modify（`_run`/`check_hr_tg` 签名、F1/F2/F6 用例、docstring 断言反转） |
| `sdflow-init/assets/workflow/tools/tests/test_hr_tg_cross_tool.py` | F3 跨文件一致性 golden | Create |
| `openspec/specs/spec-workflow/spec.md`（归档时同步） + delta | 主 spec :550 hr-tg 锚定义回灌 | 由 delta 驱动，实现期确认 |
| `sdflow-spec-review/SKILL.md` · `sdflow-code-review/SKILL.md` | anchor_lint 调用补 `--trigger-catalog` | Modify |
| `docs/workflow-map.md` · `docs/workflow-skills/{sdflow-spec-review,sdflow-code-review}.md` | ground-truth 文档调用串 | Modify（F12） |

---

### Task 1: hr_tg_intersect 严格解析（M3）

**R-ID:** R1 · **tasks.md:** §1.1, §1.2, §1.4（部分）

**Files:**
- Modify: `sdflow-init/assets/workflow/tools/hr_tg_intersect.py:54-62`（`parse_tg_set`）、`:14`（`_TG_TOKEN_RE`）
- Test: `sdflow-init/assets/workflow/tools/tests/test_hr_tg_intersect.py`

**Interfaces:**
- Produces: `parse_tg_set(raw)` 保持返回 token 列表；空 cell/前后逗号/连续逗号 → `EmitError`；成员抽取词边界严格。

- [ ] **Step 1: 写失败测试（M3 空 cell + 严格 token）**

```python
# test_hr_tg_intersect.py 追加
def test_tg_set_empty_cell_fail_closed():
    """TG-04,,TG-16 连续逗号空 cell → EmitError（非静默过滤）。"""
    m = _mod()
    for raw in ("TG-04,,TG-16", ",", "TG-04,", ",TG-16", " , "):
        with pytest.raises(m.EmitError):
            m.parse_tg_set(raw)

def test_tg_set_empty_string_is_empty_set():
    """仅原始空串表空集（合法空集入口保留）。"""
    m = _mod()
    assert m.parse_tg_set("") == []

def test_member_strict_token_rejects_malformed():
    """成员/tg-set 畸形 token TG-04x → EmitError，不宽松正规化抽 TG-04。"""
    m = _mod()
    with pytest.raises(m.EmitError):
        m.parse_tg_set("TG-04x")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_hr_tg_intersect.py::test_tg_set_empty_cell_fail_closed -v`
Expected: FAIL（当前 `:58 [t for t in tokens if t]` 静默过滤空 cell，不 raise）

- [ ] **Step 3: 改 parse_tg_set 删静默过滤 + 严格空 cell 判定**

```python
def parse_tg_set(raw):
    """--tg-set CSV → token 列表（原样、含重复，序化留给 intersect）。
    仅原始空串 = 空集；split 后出现空/纯空白 cell（前后/连续逗号）→ EmitError（M3 fail-closed）。
    任一 token 不形如 TG-<数字> → EmitError（坏输入 fail-closed）。"""
    if raw == "":
        return []
    tokens = [t.strip() for t in raw.split(",")]
    for t in tokens:
        if t == "":
            raise EmitError(f"tg-set 含空 cell（前后/连续逗号），仅空串表空集: {raw!r}")
        if not _TG_STRICT_RE.match(t):
            raise EmitError(f"tg-set 含非法 TG 记号（须 TG-<数字>）: {t!r}")
    return tokens
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_hr_tg_intersect.py -k "empty_cell or empty_string or strict_token" -v`
Expected: PASS

- [ ] **Step 5: 跑全文件回归确认无打崩**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_hr_tg_intersect.py -v`
Expected: 全 PASS（M3 改动不涉全集，成员抽取 `_TG_TOKEN_RE` 用于 catalog 成员行解析，token 边界见 Task 2 F8）

- [ ] **Step 6: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "harden-hr-tg-anchor-consistency:task1-strict-parse" "hr_tg_intersect M3 严格解析：删空cell静默过滤+严格token"
```

---

### Task 2: hr_tg_intersect catalog 全集存在性（M-new）+ F8 边界 + F7 内部一致 + F4/F5 fixture

**R-ID:** R1 · **tasks.md:** §1.3, §1.4（余）, §3.4(F4), §3.5(F5), §3.7(F7), §3.8(F8)

**Files:**
- Modify: `hr_tg_intersect.py`（加 `load_all_tg_set` + declared/hit 存在性校验）
- Test: `tests/test_hr_tg_intersect.py`（`_catalog` retrofit、`test_single_source_mutability` 重设计、M-new/F8 用例）

**Interfaces:**
- Consumes: `parse_tg_set`（Task 1）
- Produces: `load_all_tg_set(catalog_path) -> set[str]`（`## 三` 段 `| TG-NN |` 表行全集）；`main` 在 intersect 前校验 declared 每 TG ∈ 全集，否则 `EmitError`；`load_hr_tg_subset` 加载时断言 HR-TG 成员 ⊆ 全集（F7）。

- [ ] **Step 1: 先 retrofit `_catalog()` fixture 加 A–G 表行（F4，防打崩存量正例）**

`_catalog()` 现只写 HR-TG 段。M-new 会解析"全集"，若 fixture 无 A–G 表行则所有用到的 TG 号都不在全集 → 打崩 10+ 现有正例。改 `_catalog()` 默认注入一段最小 `## 三、触发词目录` 表（含所有测试用到的 TG 号：TG-01,04,06,07,08,09,16,17,19,26）：

```python
# test_hr_tg_intersect.py 的 _catalog 内，写文件前拼入全集表段
_ALL_TG_TABLE = (
    "## 三、触发词目录\n\n"
    "| ID | 触发 |\n|---|---|\n"
    + "".join(f"| TG-{n:02d} | x |\n" for n in (1,4,6,7,8,9,16,17,19,26,99))
    + "\n"
)
# _catalog(): text = _ALL_TG_TABLE + <原 HR-TG 段>
```

> 注：TG-99 纳入 fixture 全集是为 F5 重设计（"存在但非 HR-TG 成员"）；真实 catalog 无 TG-99，M-new 的"不存在"负例另用 fixture 全集外的号（如 TG-77）。

- [ ] **Step 2: 写失败测试（M-new 存在性 + F8 边界 + F7 内部一致 + F5 重设计）**

```python
def test_mnew_declared_tg_not_in_catalog_fail_closed(tmp_path):
    """declared 含 catalog 全集外 TG（TG-77 shape 合法不存在）→ 非零退出。"""
    m = _mod(); cat = _catalog(tmp_path)
    rc = m.main(["--tg-set", "TG-77", "--trigger-catalog", str(cat)])
    assert rc == m.EXIT_FAIL

def test_mnew_full_set_boundary_ignores_prose_tg(tmp_path):
    """正文游离 TG（'参见 TG-88 草案'）不入全集；引用它 → fail-closed。"""
    m = _mod()
    cat = _catalog(tmp_path, prose_extra="\n参见 TG-88 草案，非表行。\n")
    rc = m.main(["--tg-set", "TG-88", "--trigger-catalog", str(cat)])
    assert rc == m.EXIT_FAIL

def test_mnew_token_fullmatch_rejects_residue(tmp_path):
    """表行 token 逐个 fullmatch，残留后缀 TG-04.0 不当 TG-04 纳入全集。"""
    m = _mod()
    subset_all = m.load_all_tg_set(_catalog(tmp_path))
    assert "TG-04" in subset_all and "TG-04.0" not in subset_all

def test_f7_hr_tg_must_subset_full_set(tmp_path):
    """HR-TG 成员含全集外 TG → 加载 fail-closed（catalog 内部一致）。"""
    m = _mod()
    # 成员 TG-77 不在 A–G 全集表行内
    cat = _catalog(tmp_path, members="TG-77")
    with pytest.raises(m.EmitError):
        m.load_hr_tg_subset(cat)  # 或 main 级 fail-closed，按实现落点断言
```

`test_single_source_mutability` 重设计（F5）——改用"全集内存在但不属 HR-TG 8 员"的号证"改 HR-TG 段即改行为"（全集不变）：

```python
def test_single_source_mutability(tmp_path):
    """改 HR-TG 段成员即改命中行为，全集不变。用 TG-19（全集内、非 HR-TG 8 员）。"""
    m = _mod()
    cat = _catalog(tmp_path, members="TG-19")   # TG-19 在 A–G 全集表，非真实 HR-TG 成员
    subset = m.load_hr_tg_subset(cat)
    assert subset == {"TG-19"}
    hits, _ = m.intersect(m.parse_tg_set("TG-19,TG-04"), subset)
    assert hits == ["TG-19"]                     # TG-04 不再命中（本 catalog HR-TG 段只列 TG-19）
```

- [ ] **Step 3: 跑测试确认失败**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_hr_tg_intersect.py -k "mnew or f7_hr_tg or single_source" -v`
Expected: FAIL（`load_all_tg_set` 未定义 / M-new 未接线）

- [ ] **Step 4: 实现 load_all_tg_set + F7 子集断言 + M-new main 接线**

```python
_H3_SECTION_RE = re.compile(r'^#{1,2}\s.*三')      # ## 三、触发词目录 段定位（按实际标题微调）
_TABLE_TG_RE = re.compile(r'^\s*\|\s*(TG-\d+)\s*\|')  # F8：段内表行首列 TG，token fullmatch

def load_all_tg_set(catalog_path):
    """从 `## 三、触发词目录`（A–G 段）表行 `| TG-NN |` parse 全 TG 集（F8 边界钉死）。
    正文游离 TG 提及 MUST NOT 纳入；段缺/无表行 → EmitError（单一源损坏 fail-closed）。"""
    try:
        text = Path(catalog_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise EmitError(f"trigger-catalog 不可读: {e}")
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if _H3_SECTION_RE.match(ln) and "触发词目录" in ln), None)
    if start is None:
        raise EmitError("trigger-catalog 缺 `## 三、触发词目录` 段（M-new 全集单一源损坏）")
    full = set()
    for ln in lines[start + 1:]:
        if _H12_RE.match(ln):                      # 到下一 level-1/2 标题 = 段结束
            break
        mm = _TABLE_TG_RE.match(ln)
        if mm and _TG_STRICT_RE.match(mm.group(1)):  # 逐 token fullmatch，拒残留后缀
            full.add(mm.group(1))
    if not full:
        raise EmitError("`## 三` 段无 `| TG-NN |` 表行（M-new 全集单一源损坏）")
    return full
```

`load_hr_tg_subset` 末尾加 F7 断言（成员 ⊆ 全集）；`main` 在 intersect 前加 M-new declared 存在性校验：

```python
# main() 内，parse 后 intersect 前：
all_tg = load_all_tg_set(Path(args.trigger_catalog))
for t in set(declared_tokens):
    if t not in all_tg:
        raise EmitError(f"declared 含 catalog 全集外 TG（不存在，M-new）: {t}")
# load_hr_tg_subset 内末尾：
# if not set(members) <= all_tg: raise EmitError("HR-TG 成员含全集外 TG（F7 内部不一致）")
```

- [ ] **Step 5: 跑测试确认通过 + 全文件回归**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_hr_tg_intersect.py -v`
Expected: 全 PASS（含 retrofit 后的 10+ 存量正例 + 新 M-new/F8/F7/F5）

- [ ] **Step 6: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "harden-hr-tg-anchor-consistency:task2-mnew-existence" "hr_tg_intersect M-new全集存在性+F8边界+F7内部一致+F4/F5 fixture retrofit"
```

---

### Task 3: anchor_lint 接必需 --trigger-catalog + 复用解析（fail-closed）+ F6 签名

**R-ID:** R2 · **tasks.md:** §2.1, §3.6(F6)

**Files:**
- Modify: `anchor_lint.py:163-174`（`check_hr_tg` 签名）、`:207-245`（`main` 加 `--trigger-catalog`）
- Test: `tests/test_anchor_lint.py`（`_run`/`check_hr_tg` 全部调用点 + 签名 + exit2 断言原因）

**Interfaces:**
- Consumes: `hr_tg_intersect.load_hr_tg_subset` / `load_all_tg_set` / `parse_tg_set`（同口径重实现，非 import——仓内 adr/0002；漂移由 Task 6 golden 兜）
- Produces: `check_hr_tg(report_text, hr_tg_subset, all_tg_set)` 新签名（接单一源解析结果）；`main` 加 `--trigger-catalog` required。

- [ ] **Step 1: 写失败测试（缺 catalog fail-closed + F6 exit2 断言原因）**

```python
def test_anchor_lint_missing_catalog_fail_closed(tmp_path):
    """未传 --trigger-catalog → 非零退出（fail-closed），MUST NOT WARN 放行。"""
    rpt = tmp_path / "r.md"
    rpt.write_text('<!-- sdflow:hr-tg v1 hit="none" declared="" -->\n', encoding="utf-8")
    # argparse required 缺参 → SystemExit(2)
    with pytest.raises(SystemExit) as e:
        al.main(["--report", str(rpt), "--layer", "spec-review"])
    assert e.value.code == 2

def test_config_bad_block_exit2_reason(tmp_path, capsys):
    """F6：exit2 须断言 stderr 原因码，非只 returncode==2（防 argparse 缺参撞码假绿）。"""
    # ... 造 metrics 块坏的 config，跑 main，断言 stderr 含 'metrics-block-bad' 或 JSON reason
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -k "missing_catalog or bad_block_exit2_reason" -v`
Expected: FAIL

- [ ] **Step 3: main 加 --trigger-catalog required + 传入解析结果；F6 更新全部 check_hr_tg 调用点与 _run**

```python
# main(): ap.add_argument("--trigger-catalog", required=True, help="HR-TG 单一源，M2/M-new 前提")
# 读单一源（复用出锚侧口径的本地重实现，见 Task 4）：
try:
    hr_tg_subset = load_hr_tg_subset(args.trigger_catalog)   # 本地实现，非 import
    all_tg_set = load_all_tg_set(args.trigger_catalog)
except EmitError as e:
    print(f"[anchor_lint] ERROR trigger-catalog: {e}", file=sys.stderr)
    print(json.dumps({"result": "ERROR", "reason": "catalog-bad"}, ensure_ascii=False))
    return EXIT_ERROR
# check_hr_tg 调用：violations += check_hr_tg(report_text, hr_tg_subset, all_tg_set)
```

`tests/test_anchor_lint.py`：更新全部 6 处单参 `check_hr_tg(report)` → 三参 `check_hr_tg(report, subset, allset)`；`_run` helper 补 `--trigger-catalog`（写一份最小 fixture catalog 路径）；`test_config_bad_block_exit2`/`test_missing_report_error_exit2` 断言 stderr/JSON 原因码而非只 `returncode==2`。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -v`
Expected: 全 PASS（签名迁移 + fail-closed catalog）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "harden-hr-tg-anchor-consistency:task3-required-catalog" "anchor_lint接必需--trigger-catalog fail-closed+F6签名/exit2原因断言"
```

---

### Task 4: anchor_lint M1/M2/M4/M-new 一致性机械化 + F1 sentinel + F9 collect-not-raise

**R-ID:** R2 · **tasks.md:** §2.2(M1), §2.3(M2), §2.4(M4), §2.5(M-new), §3.1(F1), §3.9(F9)

**Files:**
- Modify: `anchor_lint.py`（`check_hr_tg` body 加 M2 重算 / M4 evidence / M-new；本地 `load_hr_tg_subset`/`load_all_tg_set`/`parse_tg_set` 重实现）
- Test: `tests/test_anchor_lint.py`

**Interfaces:**
- Consumes: Task 3 的 `hr_tg_subset`/`all_tg_set`
- Produces: `check_hr_tg` 返回 violation dict 列表，kind ∈ {`missing-field`(M1), `hit-declared-mismatch`(M2), `evidence-missing`(M4), `tg-not-in-catalog`(M-new)}；collect-not-raise（F9），stdout 仍合法 JSON。

- [ ] **Step 1: 写失败测试（M1 已在场；M2/M4/M-new/F1）**

```python
def test_m2_hit_recompute_mismatch_violation(subset, allset):
    """hit≠declared∩HR-TG → hit-declared-mismatch。"""
    r = '<!-- sdflow:hr-tg v1 hit="TG-04" declared="TG-19" evidence="x" -->\n'  # TG-19 非 HR-TG→hit 应 none
    v = al.check_hr_tg(r, subset, allset)
    assert any(x["kind"] == "hit-declared-mismatch" for x in v)

def test_m2_consistent_but_wrong_still_passes(subset, allset):
    """诚实边界（S1）：同改两字段一致但错 hit="none" declared="" → 过（M2 只堵内部一致性）。"""
    r = '<!-- sdflow:hr-tg v1 hit="none" declared="" -->\n'
    assert al.check_hr_tg(r, subset, allset) == []

def test_m4_evidence_missing_when_hit(subset, allset):
    """hit≠none 缺/空白 evidence → evidence-missing。"""
    r = '<!-- sdflow:hr-tg v1 hit="TG-04" declared="TG-04" evidence="   " -->\n'
    v = al.check_hr_tg(r, subset, allset)
    assert any(x["kind"] == "evidence-missing" for x in v)

def test_f1_declared_none_literal_is_violation(subset, allset):
    """F1：declared="none" 字面（应为空串""）→ 违规；hit="" 亦违规（none 才是 hit-only sentinel）。"""
    r = '<!-- sdflow:hr-tg v1 hit="none" declared="none" -->\n'
    v = al.check_hr_tg(r, subset, allset)
    assert v != []

def test_mnew_lint_tg_not_in_catalog(subset, allset):
    """M-new lint 侧：declared/hit 含全集外 TG → 违规。"""
    r = '<!-- sdflow:hr-tg v1 hit="none" declared="TG-77" -->\n'
    v = al.check_hr_tg(r, subset, allset)
    assert any(x["kind"] == "tg-not-in-catalog" for x in v)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -k "m2 or m4 or f1_declared or mnew_lint" -v`
Expected: FAIL

- [ ] **Step 3: 实现 check_hr_tg M2/M4/M-new + F1 sentinel + F9 collect-not-raise**

```python
def check_hr_tg(report_text, hr_tg_subset, all_tg_set):
    """M1 declared/hit 在场；M2 hit=declared∩HR-TG 重算逐元素一致（none⟺空交集）；
    M4 hit≠none⟹evidence= 非空白；M-new declared/hit 每 TG ∈ catalog 全集。
    诚实边界：M2 只堵内部一致性，declared 正确性属语义残余（S1）、非 tamper-proof。
    collect-not-raise（F9）：畸形就地转 violation dict，MUST NOT raise EmitError。"""
    v = []
    for ln in fence_outside_lines(report_text):
        if anchor_prefix(ln) != "hr-tg":
            continue
        kv = parse_kv(ln)
        anchor = ln.strip()[:80]
        # M1 在场
        for f in HR_TG_REQUIRED_FIELDS:
            if f not in kv:
                v.append({"anchor": anchor, "field": f, "kind": "missing-field"})
        if "hit" not in kv or "declared" not in kv:
            continue
        # F1：declared/hit 合法值域——declared 空集用 ""（非 "none"）；hit 空用 "none"（非 ""）
        hit_raw, decl_raw = kv["hit"], kv["declared"]
        try:
            declared = [] if decl_raw == "" else _parse_tg_csv(decl_raw)   # 本地严格解析
            for t in set(declared):
                if t not in all_tg_set:
                    v.append({"anchor": anchor, "field": "declared", "kind": "tg-not-in-catalog"})
            expect_hits = sorted({t for t in declared if t in hr_tg_subset}, key=lambda x: int(x[3:]))
            if hit_raw == "none":
                actual = []
            elif hit_raw == "":
                v.append({"anchor": anchor, "field": "hit", "kind": "hit-empty-not-none"}); actual = None
            else:
                actual = _parse_tg_csv(hit_raw)
                for t in set(actual):
                    if t not in all_tg_set:
                        v.append({"anchor": anchor, "field": "hit", "kind": "tg-not-in-catalog"})
            if decl_raw == "none":
                v.append({"anchor": anchor, "field": "declared", "kind": "declared-none-literal"})  # F1
            if actual is not None:
                actual_sorted = sorted(set(actual), key=lambda x: int(x[3:]))
                if actual_sorted != expect_hits:
                    v.append({"anchor": anchor, "field": "hit", "kind": "hit-declared-mismatch"})  # M2
                if expect_hits and kv.get("evidence", "").strip() == "":
                    v.append({"anchor": anchor, "field": "evidence", "kind": "evidence-missing"})  # M4
        except EmitError:
            v.append({"anchor": anchor, "field": "hit/declared", "kind": "malformed-tg-csv"})  # F9 转 violation
    return v
```

（`_parse_tg_csv` = 本地严格 CSV 解析，空 cell/畸形 raise `EmitError`；`load_hr_tg_subset`/`load_all_tg_set` 本地重实现，与 hr_tg_intersect 同口径。）

- [ ] **Step 4: 跑测试确认通过 + 全文件回归**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -v`
Expected: 全 PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "harden-hr-tg-anchor-consistency:task4-consistency-mechanize" "anchor_lint M2重算/M4evidence/M-new+F1 sentinel+F9 collect-not-raise"
```

---

### Task 5: 诚实边界 docstring + F2 整行严格解析拒重复键

**R-ID:** R2 · **tasks.md:** §2.6, §2.7, §3.2(F2)

**Files:**
- Modify: `anchor_lint.py`（`check_hr_tg` docstring + `parse_kv`/整行解析拒重复键）
- Test: `tests/test_anchor_lint.py`

**Interfaces:**
- Produces: hr-tg 锚整行严格解析——重复键（`hit=`/`declared=`/`evidence=` 出现两次）/ 未闭合注释 → violation（防 lint 末值胜 vs sdflow-retro 取首的跨消费者分歧）。

- [ ] **Step 1: 写失败测试（F2 dup-key + docstring 断言反转）**

```python
def test_f2_duplicate_key_violation(subset, allset):
    """重复 hit= → 违规（跨消费者防线：lint 末值胜 vs retro 取首）。"""
    r = '<!-- sdflow:hr-tg v1 hit="none" hit="TG-04" declared="" -->\n'
    v = al.check_hr_tg(r, subset, allset)
    assert any(x["kind"] == "dup-key" for x in v)

def test_hr_tg_value_content_now_checked(subset, allset):
    """§2.7 反转旧断言：hit="whatever" 传 catalog 后应违规（非旧 == []）。"""
    r = '<!-- sdflow:hr-tg v1 hit="whatever" declared="anything" evidence="x" -->\n'
    assert al.check_hr_tg(r, subset, allset) != []
```

删/改旧 `test_hr_tg_value_content_not_checked`（`:186-189`，"任意合法"断言）。

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -k "f2_duplicate or content_now_checked" -v`
Expected: FAIL

- [ ] **Step 3: 加整行严格解析拒重复键 + 更新 docstring 诚实声明**

```python
_KV_ALL = re.compile(r'([^\s=]+)="([^"]*)"')
def parse_kv_strict(line):
    """整行严格解析：同键出现两次 → 抛 dup（caller 转 violation）。"""
    seen, dup = {}, []
    for k, val in _KV_ALL.findall(line.strip()):
        if k in seen:
            dup.append(k)
        seen[k] = val
    return seen, dup
```

`check_hr_tg` 用 `parse_kv_strict`，`dup` 非空 → append `{"kind": "dup-key", ...}`。docstring 改：删「字段值任意合法、脚本不校验 CSV 内容」，写「M2 只堵内部一致性；declared 是否=真命中集属语义残余（S1）、非 tamper-proof」。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -v`
Expected: 全 PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "harden-hr-tg-anchor-consistency:task5-strict-line-honesty" "anchor_lint F2整行拒重复键+诚实边界docstring+§2.7断言反转"
```

---

### Task 6: F3 跨文件一致性 golden 测试

**R-ID:** R1+R2 · **tasks.md:** §3.3(F3)

**Files:**
- Create: `sdflow-init/assets/workflow/tools/tests/test_hr_tg_cross_tool.py`

**Interfaces:**
- Consumes: `hr_tg_intersect`（emit 侧）+ `anchor_lint`（lint 侧独立重算）
- Produces: 断言同一 catalog+tg-set 下两侧 hit **逐元素相等**（含 numeric 同序）——机械兜底"非 import"双份重实现的漂移。

- [ ] **Step 1: 写 golden 一致性测试**

```python
"""F3 跨文件一致性：hr_tg_intersect emit 的 hit ⟺ anchor_lint 独立重算的 hit 逐元素相等。"""
import importlib.util, pytest
# 载入两模块 + 共用最小 catalog fixture（A–G 全集 + HR-TG 段）
@pytest.mark.parametrize("tg_set", ["TG-04,TG-16", "TG-19", "", "TG-04,TG-19,TG-26"])
def test_emit_hit_matches_lint_recompute(tmp_path, tg_set):
    cat = _shared_catalog(tmp_path)
    hi, al = _load_intersect(), _load_anchor_lint()
    subset = hi.load_hr_tg_subset(cat)
    emit_hits, _ = hi.intersect(hi.parse_tg_set(tg_set), subset)
    lint_subset = al.load_hr_tg_subset(cat)
    lint_hits = sorted({t for t in hi.parse_tg_set(tg_set) if t in lint_subset}, key=lambda x: int(x[3:]))
    assert emit_hits == lint_hits          # 逐元素 + 同序
```

- [ ] **Step 2: 跑测试确认通过（两侧口径应一致）**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_hr_tg_cross_tool.py -v`
Expected: PASS（若 FAIL 说明两侧解析口径已漂移，回 Task 2/4 对齐）

- [ ] **Step 3: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "harden-hr-tg-anchor-consistency:task6-cross-tool-golden" "F3跨文件一致性golden测试：emit hit⟺lint重算逐元素相等"
```

---

### Task 7: 主 spec :550 回灌 + SKILL 接线 + F12 docs 同步

**R-ID:** R2 · **tasks.md:** §2.0, §2.8, §3.10(F12)

**Files:**
- Modify: `sdflow-spec-review/SKILL.md` · `sdflow-code-review/SKILL.md`（anchor_lint 调用补 `--trigger-catalog $RULES_ROOT/trigger-catalog.md`）
- Modify: `docs/workflow-map.md`（hr-tg 锚 3 字段 + anchor_lint 必需 catalog）· `docs/workflow-skills/{sdflow-spec-review,sdflow-code-review}.md`（调用串）
- 确认: delta `specs/spec-workflow/spec.md` 已 MODIFIED :550（`hit=/declared=/evidence=` canonical）——归档时同步主 spec

**Interfaces:** 无代码接口——文档/SKILL 调用串与工具 CLI 原子对齐。

- [ ] **Step 1: 改两 SKILL 的 anchor_lint 调用串补 --trigger-catalog**

`sdflow-spec-review/SKILL.md` 第三步「锚行自检」+ `sdflow-code-review/SKILL.md` 第五步「锚行自检」的
`anchor_lint.py --report ... --layer ... --root ...` → 补 `--trigger-catalog $RULES_ROOT/trigger-catalog.md`。

- [ ] **Step 2: 改 F12 docs 调用串**

`docs/workflow-map.md` §3.2 hr-tg 锚 `hit+evidence`(2 字段) → `hit+declared+evidence`(3 字段，declared canonical)；§4 anchor_lint 输入补必需 `--trigger-catalog` + M1/M2/M4/M-new；`docs/workflow-skills/*.md` 里写死的 anchor_lint 调用串同步补参。

- [ ] **Step 3: 确认 delta spec:550 回灌口径**

Read `openspec/changes/harden-hr-tg-anchor-consistency/specs/spec-workflow/spec.md` 确认 MODIFIED :550 已写 `hit=/declared=/evidence=` canonical + `hit≠none⟹evidence` 非空；主 spec 同步在 sdflow-done archive 阶段由 `openspec archive` 完成（本步只确认 delta 正确，不手改主 spec）。

- [ ] **Step 4: 校验文档无遗漏调用串**

Run: `grep -rn "anchor_lint" sdflow-spec-review/SKILL.md sdflow-code-review/SKILL.md docs/ | grep -v "trigger-catalog"`
Expected: 无输出（所有 anchor_lint 调用串均已补 `--trigger-catalog`，除纯说明性提及）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "harden-hr-tg-anchor-consistency:task7-skill-docs-wire" "两SKILL anchor_lint调用补--trigger-catalog+F12 docs同步+确认spec:550回灌delta"
```

---

### Task 8: bundle 回灌 + 验收

**R-ID:** R1+R2 · **tasks.md:** §4（3.1/3.2/3.3）

**Files:**
- Run: `bash setup.sh`（dev checkout 同步 canonical `~/.sdflow/workflow/`）
- 确认: `openspec/workflow/tools/` 下游副本（`sdflow-init update` 托管，不含 tests/）

**Interfaces:** 无——验收与分发。

- [ ] **Step 1: dev setup.sh 同步 canonical**

Run: `bash setup.sh`
Expected: `~/.sdflow/workflow/tools/{hr_tg_intersect,anchor_lint}.py` 软链至本 checkout 的 assets 源（改即时生效）

- [ ] **Step 2: sdflow-init update 推下游副本（核对脚本本体，不含 tests/）**

Run: `openspec-cn update`（或按仓约定 `sdflow-init update`）刷新 `openspec/workflow/tools/`
Expected: 下游 `openspec/workflow/tools/{hr_tg_intersect,anchor_lint}.py` = assets 源本体；`diff sdflow-init/assets/workflow/tools/hr_tg_intersect.py openspec/workflow/tools/hr_tg_intersect.py` 无差异

- [ ] **Step 3: 全套件 pytest 绿**

Run: `pytest sdflow-init/assets/workflow/tools/tests/ -v`
Expected: 全 PASS（M3/M-new/M1/M2/M4 + F1-F9 + F3 golden + retrofit 存量正例）

- [ ] **Step 4: Success Metrics 三项核对**

核对 proposal.md Success Metrics：① hr-tg 锚一致性全确定性面机械化（M1/M2/M3/M4/M-new 有测试覆盖）；② 全 fail-closed（缺 catalog/缺 declared/畸形/TG 不存在 均非零/违规，无 WARN 降级）；③ S1 诚实边界（"一致但错→过"负例 + docstring 声明在场）。

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "harden-hr-tg-anchor-consistency:task8-bundle-verify" "bundle回灌canonical+下游副本+全套件绿+Success Metrics核对"
```

---

## Self-Review

- **Spec coverage:** R1（hr-tg-intersection-check M3+M-new）→ Task 1/2；R2（spec-workflow anchor_lint M1/M2/M4/M-new + 必需 catalog + :550 回灌）→ Task 3/4/5/7；F1-F9 冷层 fold → Task 2(F4/F5/F7/F8)/4(F1/F9)/5(F2)/6(F3)/3(F6)；F12 docs → Task 7；bundle → Task 8。tasks.md §1.1-1.4/§2.0-2.9/§3.1-3.10/§4 全覆盖。
- **依赖顺序:** Task 2（M-new 全集解析 + F4 fixture）先于 Task 3/4（校验侧复用同口径）；F4 fixture retrofit 在 Task 2 Step 1（M-new 接线前）避免打崩存量正例。
- **诚实边界:** M2「一致但错→仍过」是 S1 语义残余的合法划分（Task 4 `test_m2_consistent_but_wrong_still_passes` + Task 5 docstring），非机械可堵，MUST NOT 冒充 tamper-proof。
- **零妥协:** 全任务无 `--allow-legacy`/grace/WARP 降级；缺 catalog=SystemExit(2)、缺 declared=violation、TG 不存在=fail-closed。
- **kind 命名** 实现期可微调（design Open Questions），测试断言 kind 时与实现对齐。
