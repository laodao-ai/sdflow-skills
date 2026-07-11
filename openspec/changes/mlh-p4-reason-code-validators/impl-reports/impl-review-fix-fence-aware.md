# impl-review-fix: 两校验器次要解析路径 fence/注释感知修正

标签 `[impl-review-fix]`（代码审自动修，非 task 完成标签）。同一系统性模式：校验器的**次要解析路径**未与其主路径口径对齐（fence / 注释感知漂移），造成中危假绿。TDD 红→绿→回归→回灌。

## BUG1（中危假绿）— outside_voice_guard.py 非 fence-aware

### 根因
`parse_codex_findings`（`_OV_ANCHOR_RE.finditer(text)` 全篇求和）与 `parse_mode`（`_S1_RE.search(text)` 全篇搜）都在**整篇原文**匹配锚，不剔 code fence。fence 内的文档示例锚被误算：outside-voice 层被静默当「有效复用」跳过（违 adr/0018 输出诚实），与姊妹校验器 `anchor_lint`（fence 外行才匹配）口径漂移。

### 红测试（`tests/test_outside_voice_guard.py`）
- `test_fenced_codex_anchor_not_counted_findings`：产物 mode=native、真实无 codex 锚，仅在 ```fenced``` 块内含 `runner="codex" findings="2"` 示例锚。断言 `section-not-found`。**红态**：原码把 fenced 锚计入 → total=2 → `none`（假绿可复用）。
- `test_fenced_step1_anchor_not_taken_as_mode`：fence 内 `mode="simulated"` step1 示例锚在前、fence 外真实 `mode="native"` 锚在后。断言 `none`。**红态**：原码 `search` 取到 fence 内 simulated → `simulated-source`。

### 修法（fence-outside 重实现要点）
- 新增 `_FENCE_RE = re.compile(r'^ {0,3}(`+"`"+`{3,}|~{3,})')` + `_fence_outside_lines`/`_fence_outside_text` 两个 helper，**口径逐字对齐** `anchor_lint.fence_outside_lines`（成对 fence 跟踪：同首字符 + 长度 ≥ 开启 marker + 闭合行 marker 后仅空白）。
- **D5 铁律**：本文件内重实现，MUST NOT import 跨模块（消费仓无 sdflow-retro/anchor_lint 依赖保证）。
- `parse_mode` 改 `_S1_RE.search(_fence_outside_text(text))`；`parse_codex_findings` 开头 `text = _fence_outside_text(text)`，使锚 finditer 与 codex#N 标签 fallback **都只看 fence 外**。
- 锚为单行、`_fence_outside_text` 以 `\n` join fence 外行保行完整；无 DOTALL，`.*?` 不跨行 → fenced 锚整块剔除、不参与匹配。

## BUG2（中危假绿）— review_disposition_check.py 空判用了另一套注释模型

### 根因
`_has_entity_content` 用 naive `_HTML_COMMENT_RE.sub("", "\n".join(...))`（**非贪婪** DOTALL）去注释，与 `find_section_body` 用的 `_annotate_lines`（fence/注释逐行感知）是两套模型。脚手架注释体含 `-->` 记号（模版示例如「例 F1 --> 采纳」）时，非贪婪在**首个** `-->` 早闭，残留脚手架文字被当实体内容 → 判非空假绿（`section-ok-DISPOSITION-UNCHECKED` exit 0）。

### 关键判定：为何用**贪婪**而非「简单套 `_annotate_lines` 逐行态」
经实证（对单行 `<!-- 例 F1 --> 采纳 -->` 及多行变体逐一验证）：**任何非贪婪、逐行、首个-`-->`-闭合的模型都无法把复现判空**——内部 `-->` 之后的尾串（同行 Variant X）或后续行孤立 `-->`（整行消费 Variant Y）必泄漏为「内容」。因 `<!-- a --> b -->` 与 `<!-- a --> 真内容 <!-- b -->` 结构同形，语义上不可区分。
本校验器是**门（gate）**：`section-empty` = 退出非零 = 卡住逼人补真实处置；`section-ok` = 放行。故「判空」是 **fail-closed 安全侧**——含 `-->` 记号的脚手架注释整体视作注释、**偏判空**，是正确取向（要求原文亦明示「纯脚手架注释哪怕含 `-->` → 判空」）。过删（罕见 `<!-- a -->内容<!-- b -->`）只会误卡→人复核，无假绿之害；漏删（原 bug）才有害。

### 红测试（`tests/test_review_disposition_check.py`）
- `test_section_scaffold_comment_internal_arrow_close_is_empty`：小节仅 `<!-- 例 F1 --> 采纳：写明文件与节 -->`。断言 `section-empty`。**红态**：原码 `section-ok-DISPOSITION-UNCHECKED`。
- `test_section_multiline_scaffold_comment_internal_arrow_is_empty`：跨行脚手架注释、中间行含 `例 F1 --> 采纳`。断言 `section-empty`。**红态**：`section-ok-DISPOSITION-UNCHECKED`。

### 修法（两处注释模型统一要点）
- `_annotate_lines` 返回值扩为 `(line, is_live, in_fence)`（新增 in_fence 标志），`find_section_body` 两处解包同步为三元组——**结构定位与空判共用同一逐行 fence/注释态**。
- `_has_entity_content` 重写为复用 `_annotate_lines`：① fence 内非空行（真实代码）直接计实体内容；② 非 fence 行拼回后用新增 `_HTML_COMMENT_GREEDY_RE = re.compile(r'<!--.*-->', re.DOTALL)`（**贪婪**）去注释，剔水平线/空白后仍有实体行 → 非空。
- 结构定位仍用非贪婪 `_HTML_COMMENT_RE`（标题行行首落注释与否需精确 HTML 语义，且现有结构夹具注释干净、无内部 `-->`，不受影响）；空判用贪婪（fail-closed 偏空）。两者共享同一 `_annotate_lines` fence/结构态，注释模型分工明确注释于代码。

## 回归结果
```
python3 -m pytest sdflow-init/assets/workflow/tools/tests/ -W error -q
187 passed in 0.68s   # 0 warning
```
- 修前基线 183 → 修后 187（+4 新红测试转绿）。
- **红态验证**：git stash 仅暂存两源文件、保留新测试跑原码 → 4 条全 FAILED（BUG1 两条示 `none`/`simulated-source`，BUG2 两条示 `section-ok-...`），确认复现；pop 恢复后全绿。
- **无正例回归**：BUG2 既有正例（`test_section_with_bullet_content_is_ok`、真实 mlh/wco OK 夹具、`test_content_after_next_h2_not_counted`、level-3 子标题属内容等）与 BUG1 六 reason_code 正例、codex#N fallback、坏输入 fail-closed 全部保持。贪婪去注释在这些夹具的 Review 处置小节内均只含单一 `-->` 区域或注释外真内容，未过删。

## 回灌下游一致性
权威源 `sdflow-init/assets/workflow/tools/` 改动，逐字复制到下游 `openspec/workflow/tools/`（下游无 tests/）。`init.py update` 从运行 checkout 的符号链接 assets 拉取（不含本 dev 修改），故此处按「权威源→下游逐字一致」范式直接 cp：
```
diff sdflow-init/assets/workflow/tools/outside_voice_guard.py    openspec/workflow/tools/outside_voice_guard.py     → IDENTICAL
diff sdflow-init/assets/workflow/tools/review_disposition_check.py openspec/workflow/tools/review_disposition_check.py → IDENTICAL
```
下游两文件 `ast.parse` 通过。

## 约束核对
- 纯 stdlib、无 subprocess（BUG1 现有 `test_no_subprocess_no_os_import_ast` / `test_no_exec_tokens_in_source`、BUG2 对应静态断言仍绿）。
- all-or-nothing fail-closed 语义不破（EmitError 路径、退出码分流未动）。
- adr/0018 输出诚实：两条假绿路径均转为正确诚实信号（BUG1 → section-not-found / 取 fence 外真锚；BUG2 → section-empty）。
- 三校验器口径一致：outside_voice_guard 的 fence-outside 与 anchor_lint 对齐；rdc 内部结构定位与空判共用 `_annotate_lines` fence 态。
