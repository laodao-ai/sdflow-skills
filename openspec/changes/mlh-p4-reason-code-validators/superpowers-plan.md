---
impl-pipeline: tickets
---

## Global Constraints

<逐字摘自 design.md 的 MUST/MUST NOT/SHALL 硬约束与 Compliance——每个 implementer/reviewer 子代理共享此注意力透镜>

- **纯 stdlib、无 subprocess**：三校验器均纯 stdlib、无 subprocess（Q-C 撤销 T80 git 例外后，T80 用源文件 fs-mtime 直比判新鲜度，MUST NOT 调 git）。
- **门控外置**：MUST NOT 读 config；被调即视 metrics/门控由上层决定。
- **all-or-nothing fail-closed**：`EmitError`+`EXIT_OK/EXIT_FAIL=0,1`；任一坏输入 raise→`main` 捕获 `return EXIT_FAIL` 且**不产部分输出**；单一源缺失/不可读 → 非零退出+stderr。
- **跨模块口径重实现不 import**（承 `lens_metric_emit.py` 形态样板）。
- **单一源原则**：HR-TG 清单从 `trigger-catalog.md` `## 七、HR-TG` `> 成员：` 行读、**MUST NOT 硬编码副本**；T80 枚举本地常量（`lens_metric_emit.py:9` 先例）；T82 状态枚举语义源锚 `sdflow-roadmap/SKILL.md`（校验器不读、仅语义来源）。
- **T80**（outside_voice_guard）：新鲜度 = 产物 fs-mtime vs 源文件(proposal/design/tasks/specs)最大 fs-mtime，产物较旧→`stale`；**MUST 排除评审产物自身**（gstack-review.md/spec-review-report.md/.outside-voice/）；6 枚举 `none|file-missing|section-not-found|zero-findings|stale|simulated-source`；codex 段 best-effort parse 失败 fail-closed 到 `section-not-found`。
- **T81**（hr_tg_intersect）：**MUST NOT 自扫 proposal 声明**——吃模型判好的命中 TG 集入参（`--tg-set`）；trigger-catalog 路径由 `--trigger-catalog` 入参给、**MUST NOT 用 `__file__.parent.parent` 推导**；命中集 `sorted(set(...))` 确定序；输出 `hit:[...]｜依据模型判定:[...]` / `none｜依据模型判定:[...]`，**不 emit 裸 none**。
- **T82**（review_disposition_check）：只断言 `## Review 处置` 小节存在+非空 → `section-missing|section-empty|section-ok-DISPOSITION-UNCHECKED`；**MUST NOT naive-grep `未处置`**（收尾句「无『未处置』」子串陷阱，须 fence/结构感知）；**MUST NOT 断言逐条已处置**（机械不可达、归模型）。
- **adr/0018（Proposed）输出诚实**：不可验输入 MUST 在输出信号里可见（T81 依据模型判定 / T82 -DISPOSITION-UNCHECKED / T80 新鲜度 fail-safe），MUST NOT emit 与「已完整验证」不可区分的裸通过码。
- **bundle 回灌纪律**：三校验器+测试落权威源 `sdflow-init/assets/workflow/tools/(tests/)`；改 assets/workflow 须 dev checkout 跑 `bash setup.sh` + `sdflow-init update` 推下游（下游不含 tests/，一致核对仅脚本本体）；**MUST NOT 只改下游副本**。
- **机械/判断切分**：脚本只出信号；命中哪些 TG（T81）、逐条处置（T82）、采纳/复用/裁决归模型。

### Task 1: outside_voice_guard 校验器（outside-voice 复用三判 → reason_code）

**Blocked-by:** none
**R-ID:** OVG

给定一份 outside-voice 产物与一个 change 目录，确定性地归约出**唯一** reason_code（六枚举），依据三前置：①来源（产物内 `step1-broad-review` 锚的 mode，simulated 视同无效）②新鲜度（产物 fs-mtime 早于该 change 源文件最大 fs-mtime → 陈旧，且排除评审产物自身）③结构（codex findings 段可否解析、条数）。纯 stdlib、无 subprocess、门控外置、坏输入 all-or-nothing fail-closed。

- [x] 六 reason_code（none/file-missing/section-not-found/zero-findings/stale/simulated-source）各有正例，行为可复现验证
- [x] 新鲜度用源文件 fs-mtime 直比、排除评审产物自身；无 git/subprocess 调用（可断言不 fork）
- [x] 坏输入（锚缺失/mode 非枚举）非零退出 + stderr，不静默产码掩盖损坏
- [x] pytest 覆盖上述，随权威源套件 `-W error` 全绿

### Task 2: hr_tg_intersect 校验器（模型传入 TG 集 ∩ HR-TG 子集）

**Blocked-by:** none
**R-ID:** HRT

给定模型判好的命中 TG 集与 trigger-catalog，确定性地求「命中集 ∩ HR-TG 子集」，输出带「依据模型判定」的结果（`hit:[...]｜依据模型判定:[...]` 或 `none｜依据模型判定:[...]`，命中集确定序）+ 规范锚串。HR-TG 子集从 trigger-catalog 单一源读、禁硬编码；trigger-catalog 路径与 TG 集均由入参给定（不自扫 proposal、不 `__file__` 推导）；单一源损坏 fail-closed。

- [x] 命中 HR-TG 成员 / 无交集 / 空集三类正例，输出格式与确定序（sorted set）正确
- [x] HR-TG 清单从 trigger-catalog 单一源读，改单一源即改行为、无硬编码副本
- [x] trigger-catalog 路径由入参（`--trigger-catalog`）定位，裸调不依赖 `__file__` 推导
- [x] 单一源损坏/缺失 → 非零退出 + stderr，不静默按空子集放行
- [x] pytest 覆盖，随权威源套件 `-W error` 全绿

### Task 3: review_disposition_check 校验器（Review 处置小节存在+非空）

**Blocked-by:** none
**R-ID:** RDC

给定一份 roadmap task-log，确定性地断言其 `## Review 处置` 小节存在且非空（非仅脚手架注释），输出 `section-missing|section-empty|section-ok-DISPOSITION-UNCHECKED`（输出码点明逐条处置未核）。禁裸子串匹配「未处置」（须 fence/结构感知，防收尾声明句自指假阳）；不断言逐条已处置（归模型）；文件不可读 fail-closed。

- [ ] 三 reason_code 各有正例；小节缺失不被当作真空通过
- [ ] 收尾声明句「无『未处置』」不触发假阳——负例夹具取**真实 in-repo task-log**（含「」/『』括号变体 + bullet/组头位置差异）
- [ ] 不冒充逐条完整性（输出码显式 UNCHECKED）
- [ ] 文件不可读 fail-closed；pytest 覆盖，随权威源套件 `-W error` 全绿

### Task 4: 三处 SKILL.md 接入 + hr-tg 锚扩 declared 字段

**Blocked-by:** 1, 2, 3
**R-ID:** OVG, HRT, RDC

把 sdflow-spec-review / sdflow-code-review / sdflow-roadmap 三处对应的模型手做机械判定步，改为「调对应校验器出 reason_code」，判断/编排语义保留给模型；T82 接入步显式声明「逐条处置是模型的活」；hr-tg 锚 schema 扩 `declared=` 字段承载 T81 的「依据模型判定」并让 anchor_lint 认得。

- [ ] 三处 SKILL.md 手做 prose（手扫/手比对/手断言）替换为调校验器，无残留手做口径
- [ ] hr-tg 锚 schema 加 `declared=` 字段 + anchor_lint 认新字段（不因其存在而报错/漏校验）
- [ ] T82 接入步显式写「逐条无未处置归模型」的信任边界声明

### Task 5: bundle 回灌 + 验收 dogfood

**Blocked-by:** 4
**R-ID:** OVG, HRT, RDC

三校验器+测试落 bundle 权威源后推下游、跑全套件、对本仓真实产物 dogfood 只读验证——确保权威源与下游脚本本体一致、既有 tools 套件不回归、三校验器对本仓真实数据无误报（尤其 T82 对本仓真实 task-log 的收尾句不假阳、hr_tg 用本仓 change 的模型判定集跑通）。

- [ ] dev checkout `bash setup.sh` 同步 canonical；`sdflow-init update` 推下游，权威源↔下游脚本本体一致（下游无 tests/）
- [ ] 权威源 tools 全套件 `pytest -W error` 全绿、0 warning（承 4.C 门槛）
- [ ] 本仓 dogfood：三校验器各对本仓真实产物只读跑一遍，T82 对真实 task-log 不假阳
- [ ] 验收门 pytest 指向权威源 `sdflow-init/assets/workflow/tools/tests/`（非不存在的下游 tests/）
