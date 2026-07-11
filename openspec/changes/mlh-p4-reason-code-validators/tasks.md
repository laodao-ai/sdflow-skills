# Tasks — mlh-p4-reason-code-validators

> 三校验器逻辑独立、依赖图稀疏（1/2/3 组互不 Blocked-by）；组 4 接入 Blocked-by 组 1-3；组 5 验收 Blocked-by 全部。
> 落盘权威源 `sdflow-init/assets/workflow/tools/`（+ `tests/`），承 4.C `lens_metric_emit.py` 形态。TDD：先写 pytest 红、再实现绿。

## 1. outside_voice_guard.py（capability: outside-voice-reuse-guard / T80）

- [ ] 1.1 写 `tests/test_outside_voice_guard.py`：**六** reason_code 正例（simulated-source / stale / section-not-found / zero-findings / file-missing / none）各一 + 锚缺失/mode非枚举 fail-closed 非零退出负例 + **产物 fs-mtime 早于源文件→stale（造 tmp 文件设 mtime）**〔spec-review Q-C；Req: 复用三判归约、fs-mtime、坏输入 fail-closed〕
- [ ] 1.2 实现 `outside_voice_guard.py`：`argparse`（`--review-path` + `--change-dir`）、**`os.stat` 比产物 fs-mtime vs 源文件(proposal/design/tasks/specs)最大 fs-mtime、排除评审产物自身**、parse `step1-broad-review` mode、best-effort codex 段 parse + findings 计数 → 单一 reason_code；**纯 stdlib 无 subprocess**；`EmitError`+`EXIT_FAIL` all-or-nothing〔spec-review Q-C；Req: 复用三判归约、fs-mtime 纯 stdlib〕
- [ ] 1.3 断言纯 stdlib 无 subprocess + 不读 config（fs-mtime 直比、不 fork）〔spec-review Q-C 撤销 grill Q3 的 git；Req: fs-mtime 纯 stdlib、门控外置〕

## 2. hr_tg_intersect.py（capability: hr-tg-intersection-check / T81）

- [ ] 2.1 写 `tests/test_hr_tg_intersect.py`：模型传入集命中 HR-TG→`hit:[...]｜依据模型判定:[...]`+锚、无交集/空集→`none｜依据模型判定:[...]`、命中 `sorted(set())` 确定序、`--trigger-catalog` 参定位单一源、单一源损坏 fail-closed〔spec-review Q-D；Req: 模型传入求交、单一源读〕
- [ ] 2.2 实现入参解析：`argparse`（`--tg-set` 模型判定的命中集 + `--trigger-catalog` 路径），**不自扫 proposal 声明**（Q-D 推翻 grill Q1 的 tg02_hit 泛化）〔Req: 模型传入求交〕
- [ ] 2.3 实现 HR-TG 单一源 parse：定位 `## 七、HR-TG` 段抓 `> 成员：` 行 `TG-\d\d`，禁硬编码、路径由 `--trigger-catalog` 给（禁 `__file__` 推导，A3）；求交 + 输出 `hit/none｜依据模型判定:[...]` + 规范锚串（不 emit 裸 none）〔spec-review Q-D；Req: HR-TG 单一源读、依据暴露〕

## 3. review_disposition_check.py（capability: roadmap-review-reconcile / T82）

- [ ] 3.1 写 `tests/test_review_disposition_check.py`：section-missing / section-empty / **section-ok-DISPOSITION-UNCHECKED** 三码 + **收尾句「无『未处置』」不假阳负例** + 「不冒充逐条完整性」断言 + 文件不可读 fail-closed〔grill Q2；Req: 存在性非空断言、信任边界不假阳、坏输入 fail-closed〕
- [ ] 3.2 实现 `## Review 处置` 小节定位（fence/结构感知）+ 非空判定（剔脚手架注释）→ `section-missing|section-empty|section-ok-DISPOSITION-UNCHECKED`；**禁裸子串 `未处置`**〔grill Q2；Req: 存在性非空断言、信任边界〕
- [ ] 3.3 SKILL 接入步 + 本 tool docstring 显式声明「逐条已处置为模型信任边界」（承 lens_metric_emit 诚实先例）〔Req: 逐条已处置为显式模型信任边界〕

## 4. 消费方 SKILL.md 接入（Blocked-by 1-3）

- [ ] 4.1 `sdflow-spec-review/SKILL.md:39-44` 复用守卫三判手做 prose → 调 `$RULES_ROOT/tools/outside_voice_guard.py`；判断/编排语义保留〔D1/D5〕
- [ ] 4.2 `sdflow-spec-review` + `sdflow-code-review` SKILL.md HR-TG 判定步：模型判命中 TG 集后传 `--tg-set` 调 `hr_tg_intersect.py`；**扩 hr-tg 锚加 `declared=` 字段 + anchor_lint 认得**〔spec-review Q-D/F5〕
- [ ] 4.3 `sdflow-roadmap` 收尾 checklist Review 处置对账步 → 调 `review_disposition_check.py`，并注明机械层只保「存在+非空」、逐条交模型〔D4〕

## 5. bundle 回灌 + 验收 dogfood（Blocked-by 全部）

- [ ] 5.1 dev checkout `bash setup.sh` 同步 `~/.sdflow/` canonical；`sdflow-init update` 推 `openspec/workflow/tools/` 下游副本（双路径内容一致核对）〔Migration〕
- [ ] 5.2 `pytest openspec/workflow/tools/tests/ -W error`：三校验器全套 + 既有 tools 套件全绿、0 warning（承 4.C 门槛）〔TG-18 测试覆盖〕
- [ ] 5.3 本仓 dogfood：三校验器对本仓真实产物各跑一遍只读核对（尤其 T82 对 `openspec/roadmaps/*/task-log.md` 现有『Review 处置』收尾句不假阳）〔D4 陷阱防线〕

## 测试覆盖图〔TG-18〕

| code path | 测试类型 |
|---|---|
| 三校验器各 reason_code 正例 | 单元正例 |
| 坏输入 / 单一源损坏 / 文件缺失 | fail-closed 非零退出负例 |
| T81 模型传入集 sorted 确定序 + --trigger-catalog 定位单一源 | Q-D 契约测 |
| T82 收尾句子串不假阳 | 陷阱负例（memory gate-substring-detection） |
| 三校验器均无 subprocess（T80 fs-mtime 直比） | 纯度断言 |
| bundle 双路径一致（仅脚本本体，下游无 tests/）+ tools 全套件 -W error | dogfood / 集成 |

## 实现期携带（spec-review 决策区，阶段三落）

- **A1-A13 实现落地修**（详见 spec-review-report.md 决策区）：A1 pytest 路径改 `assets/workflow/tools/tests/` + 一致核对仅脚本本体 · A3 hr_tg `--trigger-catalog` 参（禁 `__file__` 推导）· A5 sorted 确定序 · A7 T82 Success Metric 打星降级 · A8 spec 内部矛盾 · A9 `lens_metric_emit.py:9` ADR-11 注释订正 · A10 roadmap.md:134 回填注 · A11 Compliance 措辞订正 · A12 CLI 契约 · A13 T82 非空判据可测定义 + 负例取真实 in-repo task-log 两实例（「」/『』变体 + bullet/组头位置）。〔**A2/A4/A6 因 Q-C 撤销 git 已消解。**〕
- **adr/0018 升级**：本 change 首个形态真 ship + dogfood 验证后，adr/0018 状态 Proposed→Accepted（洞察5）。
- **pilot caveat 记录**：本 change 作首个 tickets 试点跨 3 桶（违 pilot-briefing:35）+ 叠 3 first-of-kind → 判据①打折 + confounding；SHIPPED 后在 pilot 执行记录标注「① 跨桶打折、改按 per-ticket 分别归桶」。
