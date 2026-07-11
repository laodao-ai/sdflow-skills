# Task 3 impl-report — review_disposition_check 校验器（RDC）

## 做了什么

TDD 实现 T82 校验器：断言一份 roadmap task-log 的 `## Review 处置` 小节**存在且非空**，
归约出唯一 reason_code ∈ {`section-missing`, `section-empty`, `section-ok-DISPOSITION-UNCHECKED`}。
承 4.C `lens_metric_emit` / 同批 `outside_voice_guard` / `hr_tg_intersect` 形态：纯 stdlib、无 subprocess、
门控外置（不读 config）、`EmitError` + `EXIT_OK/EXIT_FAIL=0,1`、all-or-nothing fail-closed、跨模块口径重实现不 import。

- 权威源脚本：`sdflow-init/assets/workflow/tools/review_disposition_check.py`
- 测试：`sdflow-init/assets/workflow/tools/tests/test_review_disposition_check.py`（28 例）
- 夹具：`sdflow-init/assets/workflow/tools/tests/fixtures/task_log_review_*.md`（6 份）

红→绿：先落夹具+测试（28 失败，脚本缺失），再实现（26 过 / 2 挂），2 挂为我自写的过严静态断言撞 docstring
prose（"无 subprocess" / "不读 config"），已修正为查调用面 + AST import（非 prose）。全套件 176 passed、0 warning。

## 公共接口 seam（CLI 契约）

- `--task-log <path>`（唯一入参）。
- 判定态 → **stdout** 印 reason_code；退出码分流：`section-ok-DISPOSITION-UNCHECKED` → exit 0；
  `section-missing` / `section-empty` → exit 非 0（stdout 仍载码，语义=门未过）。
- 坏输入（文件缺失/非普通文件/解码失败）→ **stderr** `[review_disposition_check] FAIL: <原因>`、无 stdout、exit 1。
- 模块级 seam：`classify(text)->code`、`find_section_body(text)->list|None`、`_has_entity_content(body)->bool`、
  `_annotate_lines(lines)->[(line,is_live)]`（fence/注释感知的结构定位核心）。

## 三 reason_code 正例

| code | 夹具 | 语义 |
|---|---|---|
| `section-ok-DISPOSITION-UNCHECKED` | `task_log_review_ok_mlh.md` / `task_log_review_ok_wco.md` / `task_log_review_ok_bracket_variant.md` | 小节存在 + 去注释后有实体内容（表格/bullet）。尾缀 UNCHECKED 显式点明逐条未核（adr/0018） |
| `section-empty` | `task_log_review_empty_template.md` | 小节存在但正文仅脚手架 HTML 注释 / 空白 / 水平线 |
| `section-missing` | `task_log_review_missing.md` / `task_log_review_fence_trap.md` | 无 live `## Review 处置` 小节（含 fence 内伪标题不算） |

## 真实负例夹具来源与内容（自指陷阱核心）

负例取**真实 in-repo task-log**（标注来源于夹具首行 HTML 注释）：

1. `task_log_review_ok_mlh.md` ← `openspec/roadmaps/mechanical-layer-hardening/task-log.md`（行 1-53 摘录）。
   含**两处**收尾声明子串「未处置」，位置不同：blockquote 组头「**不存在「未处置」状态**的条目」（真实行 35）+
   bullet「本小节**无「未处置」状态条目**」（真实行 53）。判 OK 而非假阳。
2. `task_log_review_ok_wco.md` ← `openspec/roadmaps/workflow-cost-optimization/task-log.md`（行 1-71 摘录）。
   含 blockquote 收尾声明「…**无「未处置」**。」（真实行 69）。判 OK。
3. `task_log_review_empty_template.md` ← `sdflow-roadmap/references/task-log-template.md`（行 1-78 摘录）。
   `## Review 处置` 正文仅脚手架注释，注释里含「不存在**未处置条目**」子串——去注释后判 empty，不因该子串误判有内容。
4. `task_log_review_ok_bracket_variant.md` ← MLH 行 53 收尾句的**括号变体**：真实用「」，此处逐字换 『』，
   覆盖 spec.md 场景「本小节无『未处置』状态条目」。证明校验器括号无关（根本不匹配该子串）。
5. `task_log_review_fence_trap.md`（fence 结构感知负例）：`## Review 处置` 仅作示例文本出现在 ```markdown fence 内 → missing。

**dogfood 实证**（跑真实文件）：两真实 task-log（均含「未处置」自指句）→ `section-ok` exit 0；
模版 → `section-empty` exit 1；缺失文件 → stderr FAIL exit 1。零假阳。

## fence-aware 判定逻辑

不 grep「未处置」——断的是「小节存在 + 非空」，结构化两层：

1. **小节定位（`_annotate_lines`）**：逐行跟踪 code fence（``` / ~~~ 成对）与 HTML 注释（`<!-- ... -->` 跨行）状态，
   只有 `is_live`（不在 fence、不在注释内）的行才参与标题识别。`## Review 处置`（level-2，`_H2_RE` 标题文本严格 ==）
   命中即小节起点；fence 内 / 注释内的伪标题**不算**（fence_trap 夹具证之）。小节体 = 起点后到下一个 live level-1/2
   标题（`_H12_RE`；level-3 `### ` 不作边界=属小节内）前的原始行。
2. **非空判定（`_has_entity_content`）**：小节体先 `re.sub` 去除跨行 HTML 注释，再逐行剔空白 + 水平分隔线
   （`--- / *** / ___`），残留任何实体行（表格/bullet/段落/fenced 真实内容）→ 非空。仅脚手架注释 → 空。

「未处置」子串从不进入任何比较路径 → 收尾声明句自指陷阱天然规避（memory `gate-substring-detection-dogfood`）。

## fail-closed 路径

`main` 顺序守卫：路径不存在 / 非普通文件（如目录）/ `read_text` 抛 OSError|UnicodeDecodeError → `EmitError` →
捕获后 stderr 印 `[review_disposition_check] FAIL: <原因>`、**不印 stdout**、`return EXIT_FAIL`。无部分输出。
判定态（missing/empty/ok）不经 EmitError，走正常 stdout + 退出码分流。

## 验收标准逐条

- [x] 三 reason_code 各有正例；小节缺失 → section-missing（非真空通过，exit 非 0）
- [x] 收尾声明句「无『未处置』」不触发假阳——负例取真实 in-repo task-log，含「」/『』变体 + blockquote 组头/bullet 位置差异
- [x] 不冒充逐条完整性——输出码显式 `-DISPOSITION-UNCHECKED`；测试 `test_section_with_bullet_content_is_ok` 等证「存在+非空」即 OK，不查逐条
- [x] 文件不可读 fail-closed；pytest 28 例覆盖；全套件 `python3 -m pytest sdflow-init/assets/workflow/tools/tests/ -W error -q` → **176 passed, 0 warning**
- [x] 静态断言源码无 subprocess/os/yaml import、无 os.system/Popen/git 调用记号、无 config.yaml 读取

## 全套件结果

`176 passed in 0.62s`（`-W error`，0 warning）。

## Concerns

- **『』变体夹具为真实句的括号换写**（非另有一份用『』的真实 task-log——现存两份均用「」）。已在夹具首行诚实标注为
  「真实行的括号变体」。由于校验器根本不匹配该子串，括号种类对判定无影响，此变体仅作回归护栏，不影响正确性。
- **「非空」是保守机械底线**：一个只填了模版脚手架 blockquote（无真实 issue）的小节，若 blockquote 是非注释文本，
  会判 `section-ok`。这是设计**有意**的机械/判断切分——「登记的是否真实处置」是判断，归模型（`-DISPOSITION-UNCHECKED`
  已诚实声明未核）。与 design D4 / spec RDC「不断言逐条已处置」一致，非缺陷。
- 下游副本（`openspec/workflow/tools/`）由 `sdflow-init update` 托管刷新，本 ticket 只落权威源，未推下游（按 Migration Plan step 4 后置）。
