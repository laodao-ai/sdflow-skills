---
ship-gate:
  code_review: pass
---
<!-- sdflow:step1-broad-review v1 mode="simulated" -->

## code-review 报告 — done-roadmap-writeback

> 阶段三代码评审（每次全跑·独立冷·强制主审）。Step1 scope-drift/完成度（主 session inline，mode=simulated）→ Step2 并行 4 镜（领域 backend / 对抗A 运行期爆·PoC / 对抗B spec符合·测试假绿 / 历史·漂移）+ code outside-voice（codex，exit 0）→ Step3 置信过滤+对抗裁决 → Step4 自动修/defer。metrics.enabled=true → 落 lens-metric。
> **结论：pass**（10 高/中/低 finding 全**自动修**[impl-review-fix]·48 tests green 0 warn·全仓 762 green；3 defer + 1 Minor 入 todolist T89–T92）。冷镜抓出真问题——尤 **P-5 fence-aware 缺陷簇**（对抗A 两 PoC 证实混用/未闭合 fence 绕过防自指、历史镜对标 anchor_lint CommonMark、违 MEMORY 教训），非"看着过"。

### 命中范围
- 栈: backend（stdlib Python 脚本 `roadmap_writeback_draft.py` 263→+行 + tests + `sdflow-done/SKILL.md` 集成）。清单: CR-01~09 + domains/backend。diff base=fa70872（8 实现 commit）。
- trivial_shape: NOT_EXEMPT（new-codepath + behavior-path SKILL.md）→ 照常 fan-out。
- Step1 scope-drift/完成度: built==planned（8 任务全落）、无 unrelated 顺手改；无 scope drift。

### Findings（置信 ≥80，全 CONFIRMED，均已自动修 [impl-review-fix]）

**F1 [高] fence-aware CommonMark 缺陷 → P-5 防自指被绕过**〔对抗A(2 PoC)+历史｜置信 高〕
- `strip_code_fences` 用 `lstrip()` 吞任意缩进 + 单 bool 不记定界符种类/长度 → ① ```/~~~ 混用时被对方提前关闭（PoC 证实 marker 泄漏被检测）② 未闭合 fence 静默吞到 EOF 漏检真 marker（PoC）③ 4 空格缩进 ``` 误判 fence。对标 `anchor_lint.py` 的 `_FENCE=r"^ {0,3}(\`{3,}|~{3,})"` CommonMark 口径。违 MEMORY「gate 子串检测 dogfood 自指坑」教训。
- **修复 FIX-1**：`strip_code_fences` 抄 anchor_lint CommonMark 口径（0-3 缩进、记定界符字符+长度、同字符≥长度才关闭）+ `detect_markers_ex` 暴露 `(markers, unclosed)` 信号 → 未闭合 fence 时 `resolve_association` warnings 追加「未闭合围栏、marker 可能不完整」。控制器独立 PoC 复验：混用→[]、未闭合→[]+unclosed=True、正文 marker 不误剥。

**F2 [高] pytest 锚 spec 不符 + 测试假绿**〔对抗B｜置信 高（三处交叉）〕
- spec.md/design 称 pytest 数「从 verify-report 取」，但无抽取代码、`--pytest-count` 全程无 wiring、SKILL.md 调用不传、verify-report 无契约计数字段 → 实际永远 N/A；单测 `pytest_count=39` 手喂参数掩盖。
- **修复 FIX-4**：改 spec.md:16 + design.md 措辞为「经 `--pytest-count` 显式传入则填、缺省 N/A（verify-report 无契约计数字段、不 scrape 散文避免第二真相源）」，标 [impl-review-fix]；脚本行为不变（本就此语义），诚实对齐、不新造真相源。

**F3 [中] `--roadmap` malformed 静默 fallback**〔领域+对抗B+outside-voice(codex)｜置信 高·cross-model〕
- flag 非空但 `FLAG_RE` 不匹配 → 静默丢弃、退化 marker/prefix；用户显式覆写被无声吞、产错 phase 草稿。违反本 change 通篇「反静默」。**T10 裁决**（客观判据=反静默+尊重显式覆写意图）→ 采 codex 解「不 fallback」。
- **修复 FIX-2**：`BadRoadmapFlag` 异常 → main 独立退出码 7 + stderr `BAD_ROADMAP_FLAG`，不 fallback。SKILL §2.2 退出码处置补 exit 7。

**F4 [中] frontmatter verify 解析漂移 ship_gate（nested-key 误采纳）**〔历史+outside-voice(codex)｜置信 高·cross-model〕
- 宽松 `^\s*verify:` 扫全块 → `note:\n  verify: PASS` 等非 ship-gate 直接子键会误采纳为 good；ship_gate 自己的 `test_frontmatter_parse.py:66` 钉死 `ship-gate.note.verify` 不得采纳。
- **修复 FIX-3**：只认顶层 `ship-gate:` 直接子键 verify（缩进恰一层、父为 ship-gate）。控制器复验：nested→malformed、proper ship-gate→good/PASS；FIX-3 补 ship-gate 包裹专项测试。

**F5 [中] 同源多 marker 冲突静默取首**〔领域+outside-voice(codex)｜置信 中〕→ **FIX-5**：去重后 >1 不同值 → warnings 追加「同源多 marker 不一致、取首、请人工核对」+ 测试。

**F6 [中] SKILL §2.2 摘要模板未覆盖 exit 4/5/6/7**〔领域〕→ **FIX-7**：第六步摘要 `Roadmap:` 行补第三态 `⛔ 未生成(<原因>)`；退出码表补 exit 7；`/tmp/rwd_err`→`/tmp/rwd_err.$$`（防并发覆盖，A4）；加注「exit 3/4/5/6/7 均预期分支非异常、MUST 非 set -e 语境执行」（A3）。

**F7 [中] ROADMAP_MISSING 分支零测试**〔对抗B〕→ **FIX-6 附**：补 verify=PASS+roadmap.md 缺 → exit 4 测试。

**F8 [低] read_text 无编码兜底 → 裸 traceback**〔领域〕→ **FIX-6**：核心读文件 try/except OSError/UnicodeDecodeError → malformed/空串语义、stderr 记因，不 traceback + 测试。

**F9 [低] /tmp/rwd_err 固定路径并发覆盖**〔对抗A〕→ 并入 FIX-7（`.$$`）。
**F10 [低] SKILL §2.2 exit 3 在 set -e 下中断流水线**〔对抗A·推测〕→ 并入 FIX-7（加注非 set -e）。

### 已裁掉 / defer（反静默压制·可审计）

- **defer→todolist（真问题、本 change 不修）**：
  - **T89 [中]** probe_format 全文扫描非限定 phase（D2）——混合格式 roadmap 误判；现两存量 roadmap 各单一格式**无触发**，故 defer 非当场修。
  - **T90 [中]** frontmatter 全量 parity ship_gate（BOM/tab/YAML注释，H2#2/4/5·H3）——本仓 verify-report 格式固定 dogfood-green，消费仓非规范输入才漂移；nested-key 已 FIX-3 修。
  - **T91 [低]** PREFIX_RE 命名固有歧义（D5）——无法纯字符串消歧、机制已合理处理，记边界。
- **Minor→T92**：test_verify_state_malformed_duplicate_key/bad_enum 无 ship-gate 包裹，FIX-3 后经「无顶层 ship-gate」走 malformed 非经子路径——**行为正确已验**，FIX-3 已补 ship-gate 专项测试。
- **对抗A 自排除 5 个非 bug（留档）**：BOM→absent(fail-safe 安全向)、全角空格 strip OK、`verify: PASS ` 尾空格 `\s*$` OK、`verify:"PASS"`→malformed(fail-closed 符合)、locate_phase_rows `re.escape+\.` 无交叉误配。均非缺陷、不计裁掉。

### 修复 / defer 台账
- 自动修 **10 项**[impl-review-fix]（F1–F10，FIX-1..7）；defer **3 项**（T89–T91）+ Minor 1（T92）。
- T10复核: --roadmap malformed 处置（F3）| 客观判据（反静默+尊重显式覆写意图）自动选 codex「不 fallback、独立退出码」| 理由: 系统镜(反静默红线一致)＞用户镜(显式覆写不被静默吞)＞开发循环镜(独立退出码可测)；主次=反静默红线决定。
- 验证: `pytest sdflow-done/tests/ -q -W error` → 48 passed 0 warning；全仓 762 passed 0 warning；对抗A 两 PoC + FIX-3 nested 控制器独立复验通过。

### 度量锚（lens-metric，metrics.enabled=true；emitter exit 0 落，anchor_lint 门后自检）

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="4" sev="致0/高2/中2/低2" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="6" 采纳="4" 裁掉="0" defer="2" 独立="2" sev="致0/高0/中3/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="3" 采纳="2" 裁掉="0" defer="1" 独立="0" sev="致0/高1/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中3/低0" -->

> **残余信任边界**：分类正确性 + roster 完备性 + findings JSON 誊写准确仍是主 session 信任边界，emitter 只保证确定性归约。
> **反馈回路免责**：本 skill 只落锚，聚合/复评/淘汰镜一律 `/sdflow-retro` + 人决。**冷审印证**：adversarial 独立=4（F4 pytest/F7 ROADMAP-test/F9 tmp/F10 set-e 独家）、domain 独立=2、codex outside-voice 3 条全交叉印证 F3/F4/F5——冷独立层抓出 P-5 核心缺陷簇，非合成层能挖出（MEMORY「冷 code-review 层 load-bearing」再获证）。

### outside-voice 锚
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="ok" findings="3" truncated="false" -->

### HR-TG 判定
<!-- sdflow:hr-tg v1 hit="none" evidence="stdlib Python 助手脚本读盘面生成建议性草稿,非机械写roadmap、非DB/API/并发/信任边界,无难回退的HR-TG成员命中" -->

### 结论
- ☑ **建议进 /sdflow-done**（verify → hand-off → archive → commit → merge）。
- defer 残差已入 todolist T89–T92（hand-off 会引用）。
- （机判锚见头部 frontmatter `ship-gate.code_review: pass`）
