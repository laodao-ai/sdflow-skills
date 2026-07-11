# impl-review-fix v2: BUG2 弃贪婪、改基于 _annotate_lines 逐行 live/in_fence 判定

标签 `[impl-review-fix]`（代码审自动修的修正 commit；v1 的 BUG1 fence 修法正确、保留不动，本 v2 仅重做 BUG2）。

## 为何弃贪婪（v1 引入新回归，已实证）
v1 把 `_has_entity_content` 改为整段贪婪 `<!--.*-->` DOTALL sub。贪婪从**首个** `<!--` 吃到**末个** `-->`，会吃掉夹在两注释之间的真实处置内容 → 判 `section-empty`(exit 1) = **假阴**，阻塞已填的合法 roadmap。复现：
```
## Review 处置

<!-- 脚手架：逐条追加 -->
F1 采纳：outside_voice_guard 改 fence-aware，见 commit
<!-- 收尾 checklist：无未处置条目 -->

## 2026-07-08
```
「前置注释 + 真内容 + 收尾注释」是这批 task-log 的**常见模式**，贪婪会频繁误阻塞——比原假绿危害更大。非贪婪整段 sub（原 bug）则在注释体含 `-->` 时早闭泄漏残字。故**整段 DOTALL sub 两个方向都错**，正解必须逐行。

## 正解：基于 _annotate_lines 的 live/in_fence 逐行态（与 codex 跨模型同向）
`_has_entity_content` 改为逐行遍历 `_annotate_lines(body_lines)` 的 `(ln, live, in_fence)`，**不再做任何整段 DOTALL sub**：
- `in_fence` 行：fence **体**真实代码内容（`ln.strip() and not _FENCE_RE.match(ln)`，排除 ``` / ~~~ 起止 marker 行）→ 有内容；空 fence 仅 marker 行 → 无内容。
- `not live`（注释内行）→ 跳过。
- `live` 行：先剥行内成对完整注释（非贪婪 `_HTML_COMMENT_RE.sub("", ln)`），再取悬空未闭合 `<!--` 之前的文本（`.split("<!--", 1)[0]`——开启行被 `_annotate_lines` 标为 live，其 `<!--` 前才是可见文本）；该前文 `strip()` 后非空且非水平线(`_THEMATIC_RE`) → 有内容。
- 都不满足 → False（空）。

`_annotate_lines` 返回值扩为 `(line, is_live, in_fence)`（承 v1 已加的 in_fence 标志），**结构定位（find_section_body）与空判共用同一逐行 fence/注释态** → 两处注释模型真正统一，无整段 sub 漂移。移除 v1 的 `_HTML_COMMENT_GREEDY_RE`（已确认无残留引用）。

## 四类新测试（替换 v1 的两条 "断言 empty"）— `tests/test_review_disposition_check.py`
| 测试 | 输入 | 断言 | 性质 |
|---|---|---|---|
| `test_section_malformed_comment_trailing_render_text_is_ok` | 单行 `<!-- x --> y -->` | **section-ok** | 尾随 ` y -->` 按 CommonMark 是可见渲染文本，如实识别为内容（非真假绿，不 fail-closed 误判空）。**v1 曾错断言 empty，此处纠正为 ok** |
| `test_section_sandwich_real_content_between_comments_is_ok` | 前置注释 + 真内容 + 收尾注释 | **section-ok** | 贪婪回归护栏（防 v1 重现） |
| `test_section_empty_fence_only_markers_is_empty` | 仅 ``` 起止、体内空 | **section-empty** | codex F4：修真假绿（marker 行非实体内容） |
| `test_section_fence_with_body_is_ok` | fence 含真实代码体 | **section-ok** | fence 体真实内容计为内容 |
| `test_section_unclosed_comment_open_only_is_empty` | `<!-- scaffold`（无 `-->`） | **section-empty** | codex F4：修真假绿（悬空 `<!--` 前无文本） |

（5 条，含 fence_with_body 配对正例。）

### 红态验证（对 parent 49b0d47 原始 review_disposition_check.py 跑新测试）
- `test_section_empty_fence_only_markers_is_empty` → **FAILED**（原码判 `section-ok`；空 fence 假绿）。
- `test_section_unclosed_comment_open_only_is_empty` → **FAILED**（原码判 `section-ok`；未闭合注释假绿）。
- 其余 3 条（malformed→ok / sandwich→ok / fence_with_body→ok）原码即 pass = 回归护栏（尤其 sandwich 锁住"不得贪婪"）。
两条 codex-F4 假绿由本正解转绿。

## 回归结果
```
python3 -m pytest sdflow-init/assets/workflow/tools/tests/ -W error -q
190 passed in 0.66s   # 0 warning
```
- 计数：v1 的 187 → 移除 2（v1 两条 "断言 empty"）+ 新增 5 = 190。
- **无正例回归**：真实 mlh/wco OK 夹具仍 section-ok；纯脚手架空模版 fixture 仍 section-empty；既有 `test_section_with_bullet_content_is_ok` / 多行注释剥净空 / level-3 子标题属内容 / 下一 h2 后内容不计 等全部保持。
- BUG1（outside_voice_guard fence 修法）未触动，其两条 fence 测试与全部原正例仍绿。

## 回灌下游一致性
仅 `review_disposition_check.py` 变（BUG1 的 outside_voice_guard 已在 v1 commit 回灌、本次不动）。逐字复制权威源 → 下游：
```
diff sdflow-init/assets/workflow/tools/review_disposition_check.py openspec/workflow/tools/review_disposition_check.py → IDENTICAL
```
`grep GREEDY` 权威源+下游均无残留；下游 `ast.parse` 通过。

## 约束核对
- 纯 stdlib、无 subprocess、门控外置（相关静态断言仍绿）；all-or-nothing fail-closed 语义不破。
- adr/0018 输出诚实：空 fence / 未闭合注释两条真假绿转为诚实 `section-empty`；畸形注释尾随渲染文本如实判 `section-ok`（不冤判空）。
- 三校验器口径一致：rdc 结构定位与空判共用 `_annotate_lines`（真正单一逐行态，非两套 sub）；outside_voice_guard fence-outside 对齐 anchor_lint（v1）。

## 已知小边角（可接受）
`~~~` 字面行出现在 ``` fence 体内时，`not _FENCE_RE.match(ln)` 会把它误当 marker 排除、不计为内容——仅当 fence 体**全部**由 fence-marker 形状行组成才影响判定（极罕见），且偏向"判空"= fail-closed 安全侧，无假绿。
