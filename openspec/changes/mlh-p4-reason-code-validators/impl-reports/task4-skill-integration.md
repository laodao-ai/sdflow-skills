# Task 4 impl report — 三处 SKILL.md 接入 + hr-tg 锚扩 declared= 字段

**状态：** DONE
**R-ID：** OVG, HRT, RDC · **Blocked-by：** 1, 2, 3

## 做了什么

把三处评审/规划 SKILL 的模型手做机械判定步接到已过审的三校验器（调 `$RULES_ROOT/tools/<validator>.py` 出 reason_code，判断/编排语义保留给模型），并让 anchor_lint 认得 hr-tg 锚新增的 `declared=` 字段。

## anchor_lint declared= 改动（新增校验，走 TDD 红→绿）

**核实结论：anchor_lint 此前不认 declared=——不校验、也不报错。** 现状仅在 `check_existence` 里把 hr-tg 记入 MANDATORY 存在性（`anchor_prefix` 前缀匹配 `<!-- sdflow:hr-tg v1`，尾随 `declared=` 属性不影响识别），对 hr-tg 锚的**字段一个都不校验**。故 `declared=` 加进锚不会报错（满足"不因其存在而报错"），但也**未校验**（"漏校验"）——新 schema 要求该字段在场却无门。

按 TDD 补齐：
1. **红**：在 `tests/test_anchor_lint.py` 新增 7 个用例（调不存在的 `check_hr_tg` + 一个端到端），确认 7 failed。
2. **绿**：`anchor_lint.py` 新增 `check_hr_tg(report_text)`——fence 外真 hr-tg 锚 MUST 含 `hit=` + `declared=` 两字段（缺任一 → `{kind:"missing-field"}`）；字段**值**任意（TG 记号 CSV / none / 空串均合法，命中判定归模型，脚本不校验 CSV 内容）。在 `main()` 里**无条件**接入（`violations += check_hr_tg(report_text)`，不受 `metrics.enabled` 门控——hr-tg 恒必有锚）。
3. 更新既有 fixture `test_clean_report_exit0` 的 hr-tg 锚 → `hit="none" declared=""`（贴合新 schema）；新增端到端 `test_hr_tg_missing_declared_exit1`（完整报告但 hr-tg 缺 declared= → VIOLATION exit 1）。

新增用例：`test_hr_tg_declared_present_ok` / `test_hr_tg_none_with_declared_ok` / `test_hr_tg_missing_declared_violation` / `test_hr_tg_missing_hit_violation` / `test_hr_tg_value_content_not_checked` / `test_hr_tg_in_fence_not_checked` / `test_hr_tg_missing_declared_exit1`。

**只改权威源** `sdflow-init/assets/workflow/tools/anchor_lint.py`（+ tests/）——推下游副本是 Task 5，本票未碰 `openspec/workflow/tools/`。

## 三处 SKILL.md 接入（前后对比要点）

### ① sdflow-spec-review/SKILL.md:39-44 → T80 outside_voice_guard（OVG）
- **前**：step 5「outside-voice 复用守卫（三前置·R2）」模型手做三判——①来源 mode ②**新鲜度用 `git log -1 --format=%ct -- {change_dir}` 对比**（看不到未提交编辑的坑）③结构 codex 段。
- **后**：改为调 `python3 $RULES_ROOT/tools/outside_voice_guard.py --review-path {change_dir}/gstack-review.md --change-dir {change_dir}`，脚本纯 stdlib、新鲜度用源文件 fs-mtime 直比（排除评审产物自身、不调 git）、归约唯一 reason_code。**保留给模型的编排**：`none`(exit0)→复用不重开；其余码→回落自跑设计 outside voice（site="design-voice"），`file-missing` 时措辞声明「仅补偿 outside-voice 切片」。C2/P2b 交叉引用注记原样保留。手做 `git log` 新鲜度口径已清除。

### ② sdflow-code-review/SKILL.md:75 + sdflow-spec-review/SKILL.md:56 → T81 hr_tg_intersect（HRT）
design.md 数据流图明示 hr_tg_intersect 供 **spec-review 与 code-review 两处**，两处「HR-TG 判定〔C4·R3〕」步文本逐字相同，**均已转换**（否则 spec-review 留残手做口径）。
- **前**：「命中 TG 集 ∩ HR-TG 子集（单一源 = trigger-catalog 附录，只引用不复制清单）≠ ∅ → 单开 cross-model」——模型**手比对交集**；锚 `<!-- sdflow:hr-tg v1 hit="…|none" evidence="…" -->`。
- **后**：模型只判**命中 TG 集**（无确定性信号=判断归模型），交 `python3 $RULES_ROOT/tools/hr_tg_intersect.py --tg-set "TG-xx,TG-yy" --trigger-catalog $RULES_ROOT/trigger-catalog.md` 做确定性 ∩ HR-TG 子集（脚本从 catalog `## 七、HR-TG` 段 `> 成员：` 行单一源 parse）+ 出锚。锚扩 `declared=`（承模型判定的命中集，adr/0018 输入可见）：`<!-- sdflow:hr-tg v1 hit="…|none" declared="…" -->`；`evidence=` 仍模型手填（task2 报告：校验器只出 hit/declared）。**hit 非空** → 单开 cross-model（编排归模型）。手比对交集口径已清除。

### ③ sdflow-roadmap/SKILL.md:346（收尾 checklist ①）→ T82 review_disposition_check（RDC）
- **前**：「① Review 处置无遗留：task-log.md『Review 处置』小节不存在未处置状态的条目。小节**缺失**视为不通过——先建小节再判，MUST NOT 真空通过」——模型**手断言**小节存在半场。
- **后**：先解析 `RULES_ROOT`（roadmap SKILL 原无此步，新增 `~/.sdflow/hack/resolve-workflow.sh` 解析 + 缺失降级人工断言的 fail-safe），再调 `python3 $RULES_ROOT/tools/review_disposition_check.py --task-log openspec/roadmaps/{name}/task-log.md`——fence/结构感知归约 `section-missing`/`section-empty`/`section-ok-DISPOSITION-UNCHECKED`。**存在半场机械化归脚本，逐条无未处置 (a) 仍归模型。**

## T82 信任边界声明落点

sdflow-roadmap/SKILL.md checklist ① 内新增独立一行（MUST 显式陈述）：「脚本**只断言小节存在+非空**（故输出码尾缀 `-DISPOSITION-UNCHECKED`，防 `present` 被误读为已核=假绿）；**逐条是否真处置归你判定**——脚本不断言逐条已处置（三实例格式不统一、机械不可达），亦 MUST NOT naive-grep `未处置` 子串（收尾声明句含该子串却恰是合规态）」。本项通过 = 脚本判 `section-ok-DISPOSITION-UNCHECKED` **且** 模型复核每条 issue 均标状态枚举、无遗留。

## 全套件结果

`python3 -m pytest sdflow-init/assets/workflow/tools/tests/ -W error -q` → **183 passed, 0 warning**（本票新增 7 anchor_lint 用例；其余存量校验器套件全绿）。

三校验器 SKILL 调用范式 CLI 实跑核对（arg 名对齐 argparse）：
- T81 `--tg-set "TG-04,TG-19" --trigger-catalog <real>` → `hit:[TG-04]｜依据模型判定:[TG-04,TG-19]` + declared= 锚，exit 0。
- T82 `--task-log openspec/roadmaps/workflow-cost-optimization/task-log.md` → `section-ok-DISPOSITION-UNCHECKED`，exit 0。
- T80 `--review-path <nonexistent> --change-dir <change>` → `file-missing`，exit 1。

## concerns

1. **roadmap SKILL 新引入 resolve-workflow.sh 依赖**：roadmap 原不依赖 workflow bundle，为调 T82 校验器新增 `$RULES_ROOT` 解析。已按 spec/code-review 先例配 fail-safe（脚本未装/解析失败 → 显式降级人工断言小节存在+非空、转发 stderr，不静默）。消费仓未装 bundle 时走降级路径——非"残留手做口径"，是工具缺位的兜底。
2. **hr-tg 锚 `evidence=` 仍模型手填**：脚本 emit 的锚只含 hit/declared，模型需手工把 `evidence=` 注入报告锚行。anchor_lint 不强制 evidence=（仅强制 hit=+declared=），与 task2 报告一致。
3. **T81 命中集 TG 记号规范化**（承 task2 concern 1）：脚本精确字符串匹配，模型须用 catalog 规范 ID（二位零填充 TG-04），SKILL 接入步已指示传 catalog 规范记号。
