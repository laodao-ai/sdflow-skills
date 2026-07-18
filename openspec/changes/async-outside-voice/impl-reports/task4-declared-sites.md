# Task 4 实现报告：declared-sites per-site 完整性机械核

**R-ID**：R2 ｜ **Blocked-by**：3（已完成）｜ 分支 `feat/async-outside-voice`

## 做了什么

家族级门（`check_existence`：报告有 ≥1 条 `outside-voice` 锚即过）不核 per-site ⇒ 放过「并发 2 站点漏收一个」。
本票补该盲区：报告落**恰好一条** `sdflow:declared-sites` 锚声明本层「**应有锚**站点集」，`anchor_lint.py`
新增 `check_declared_sites` 做**双向**机械核。

### 改动点

| 文件 | 改动 |
|---|---|
| `sdflow-init/assets/workflow/tools/anchor_lint.py`（**权威源**） | `ANCHOR_PREFIXES` 加 `declared-sites` 族；新增 `_LAYER_BASE_SITE` / `_SITE_VOCAB` / `_parse_site_csv` / `_hr_tg_intersect_nonempty` / `check_declared_sites`；`main()` always-on 接入 |
| `openspec/workflow/tools/anchor_lint.py` | 托管副本同步（与权威源逐字节一致） |
| `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` | +21 用例（含自指测试）；2 处既有 clean e2e 夹具补 declared-sites 锚、`_ov` 默认 `site` 由 `"x"` 改 `"code-voice"` |
| `sdflow-spec-review/SKILL.md` | 「helper 调用协议」节后加 per-site 完整性声明段（`{design-voice} ∪ {hr-tg\|HR-TG∩≠∅}`），**留 async-branch marker 外** |
| `sdflow-code-review/SKILL.md` | 同上，本层公式 `{code-voice} ∪ {hr-tg\|HR-TG∩≠∅}` |

### 核的语义（两道，缺一不可）

1. **declared == 公式重算期望集**：期望集 = `{层基站点}` ∪ `{hr-tg | HR-TG∩≠∅}`；HR-TG∩ 由报告里**唯一**
   那条 `hr-tg` 锚的 `declared=` ∩ HR-TG 子集**重算**（同 `check_hr_tg` M2 口径，不引二源）。
2. **declared == 实落 `site=` 集**：不等 → `site-missing-anchor` / `site-unexpected-anchor`。

> 只做 ② 会被「同时缩 declared 又不落锚」两边自洽绕过 ⇒ ① 是反规避那道。
> `guard=` 全程**未被解析**（其语义站点相关）；唯一动态输入 = HR-TG∩，符合 G1。

**fail-closed 面**：锚缺失 / ≥2 条 / 缺 `declared=` / 重复键 / 域外站点记号 / HR-TG∩ 算不出（hr-tg 锚缺失·
非唯一·`declared=` 畸形）——一律违规，**无静默放行分支**。

## 验收标准逐条证据

### ① 两层报告均落 declared-sites 集，按「应有锚站点集」定义

两 SKILL 已写入指令段（各自公式 + 「是应有锚集、非应 dispatch 集」+ 「MUST NOT 拿 guard= 当判据」）。
机械侧对应 `_LAYER_BASE_SITE = {"spec-review": "design-voice", "code-review": "code-voice"}`。

复用态判绿实证（G1 最常见路径不假红）：

```
$ pytest -k "ds_reuse_state_design_voice_no_dispatch_still_green" → PASSED
  （site="design-voice" guard="none" 未 dispatch，仍落锚 ⇒ 零违规）
$ pytest -k "ds_layer_base_site_is_layer_specific" → PASSED
  （code-review 层写 design-voice ⇒ declared-not-expected）
```

### ② 机械核比对 declared 与实落锚站点集，不等即非零退出

```
$ /usr/bin/python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -q -k "ds_"
23 passed, 113 deselected in 0.07s
```

端到端（CLI 退出码）：`test_ds_cli_end_to_end_violation` 断言漏收站点 → `returncode == 1` +
JSON 含 `site-missing-anchor`；`test_ds_cli_end_to_end_clean` 断言自洽 → `returncode == 0`。
反规避由 `test_ds_declared_shrink_and_drop_anchor_still_red` 锁死（两边一起缩水仍红）。

### ③ 实现复用既有 fence 剔除口径，无新增裸 grep 解析路径

`check_declared_sites` / `_hr_tg_intersect_nonempty` 均只经 `fence_outside_lines(report_text)` 取行，
文件内无新增 `re.search`/`grep` 式全文扫描。机械证明用打桩测试而非人眼：

```
$ pytest -k "ds_reuses_fence_outside_lines_no_bare_grep" → PASSED
  （给 fence_outside_lines 打桩只放行首行 ⇒ 该核的可见行随之变化 ⇒ 证明它走的是该函数）
```

### ④ 含模版/示例锚的报告正文不产生自指假阳（含本 change 自身报告）

合成用例：围栏内放**相反的** `declared-sites` + 多余 `outside-voice` 模版锚（含 ``` 与 ~~~ 两种围栏），
真锚在围栏外 → 零违规（`test_ds_fenced_template_anchors_no_false_positive` PASSED）。

**自指实跑**（本 change 自己的报告，真实文件）：

```
$ /usr/bin/python3 sdflow-init/assets/workflow/tools/anchor_lint.py \
    --report openspec/changes/async-outside-voice/spec-review-report.md \
    --layer spec-review --trigger-catalog sdflow-init/assets/workflow/trigger-catalog.md --root .
{"result": "VIOLATION", "violations": [{"kind": "missing-declared-sites", ...}]}
```

**唯一**违规是「该报告尚无 declared-sites 锚」（它早于本锚族，属预期），**无任何自指假阳**。
补上应有锚 + 再追加一段围栏内的**相反**模版锚后：

```
$ ... --report <augmented copy> --layer spec-review ...
[anchor_lint] CLEAN
{"result": "CLEAN"}
```

（同一断言另有 pytest 版 `test_ds_self_referential_real_report_no_false_positive`，直读真实文件、
未 skip——`pytest -rs -k ds_` 显示 0 skipped。）

### ⑤ 合法组合矩阵未被修改（矩阵回归绿）

对 `git show HEAD:...anchor_lint.py` 与改后版本做全笛卡尔对拍：

```
cells: 720 | categories: ['cross-model','illegal','no-exec','same-family','self-review']
classify_combo diffs: {}
check_legal_combo 全笛卡尔 540 例，逐条差异 0
OUTSIDE_VOICE_REQUIRED_FIELDS 同: True
```

`site=` 的必填校验刻意放在 `check_declared_sites` 内、**未**加进 `OUTSIDE_VOICE_REQUIRED_FIELDS`
（`test_ds_outside_voice_missing_site_field` 同时断言该常量未变）⇒ 与「不改矩阵」Non-Goal 不冲突。

## 全量门禁

```
$ /usr/bin/python3 -m pytest -q
1666 passed, 2 skipped in 75.67s          # 基线 1645 → +21（2 skip 为既有 Windows 本地盘用例）
$ /usr/bin/python3 hack/check_async_branch_parity.py
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致            exit=0
$ /usr/bin/python3 hack/sync_principles.py --check
[sync_principles] ✅ 20 个投放面全部与真相源一致                      exit=0
```

change 四件套（proposal / design / tasks / specs）**零改动**（未触 ship_gate 设计门失鲜）。

## 遗留 concerns

1. **本核抓不到「barrier 早退产生的假 timeout」**（设计已登记的已知不覆盖）：它比对**站点集合**、
   不核 `reason_code` 新鲜度——早退站点仍在集合内、判绿。防线是 ADR-3 正向 barrier 语义
   （`timeout` 只允许由实测 exit 124 产生）+ `tasks §4.1` 三时刻单调锚。**本票未改变该边界。**
2. **`declared-sites` 是硬必填**：存量报告（含本 change 自己的 spec-review-report.md）跑 anchor_lint
   会红。这是刻意的（可省略 = 门可绕过 = 假绿）；存量报告不回改，新轮次报告按 SKILL 指令落锚即可。
3. **站点词表钉死 `{design-voice, code-voice, hr-tg}`**（有界、可枚举 ⇒ 合基准 5）。将来若新增 voice
   站点，须同步改 `_SITE_VOCAB` + `_LAYER_BASE_SITE`，否则新站点会被判 `malformed-site-csv` /
   `site-unexpected-anchor`——fail-closed 方向，不会假绿。
4. **运行 checkout 未同步**：改的是 `assets/workflow/tools/`，`~/.sdflow/workflow` 软链指向运行
   checkout（`~/.skills/sdflow-skills`）。SKILL 真跑要吃到本改动，须在合并后于运行 checkout
   `git pull` + `bash setup.sh`（发布边界纪律）。本票只做脚本 + 指令，未跑真实评审。
