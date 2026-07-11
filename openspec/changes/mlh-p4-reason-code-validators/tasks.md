# Tasks — mlh-p4-reason-code-validators

> 三校验器逻辑独立、依赖图稀疏（1/2/3 组互不 Blocked-by）；组 4 接入 Blocked-by 组 1-3；组 5 验收 Blocked-by 全部。
> 落盘权威源 `sdflow-init/assets/workflow/tools/`（+ `tests/`），承 4.C `lens_metric_emit.py` 形态。TDD：先写 pytest 红、再实现绿。

## 1. outside_voice_guard.py（capability: outside-voice-reuse-guard / T80）

- [ ] 1.1 写 `tests/test_outside_voice_guard.py`：**七** reason_code 正例（simulated-source / stale / **stale-dirty-tree** / section-not-found / zero-findings / file-missing / none）各一 + 锚缺失/mode非枚举 fail-closed 非零退出负例 + **工作树 dirty→stale-dirty-tree fail-safe（git fixture）**〔grill Q3；Req: 复用三判归约、坏输入 fail-closed、dirty fail-safe〕
- [ ] 1.2 实现 `outside_voice_guard.py`：`argparse`（`--review-path` + `--change-dir`）、**自跑 `git log -1 --format=%ct`（新鲜度）+ `git status --porcelain`（dirty）**、parse `step1-broad-review` mode、best-effort codex 段 parse + findings 计数 → 单一 reason_code（dirty→`stale-dirty-tree`）；`EmitError`+`EXIT_FAIL` all-or-nothing〔grill Q3/D1；Req: 复用三判归约、自跑 git〕
- [ ] 1.3 git fixture 测新鲜度 + dirty fail-safe（临时 git repo、造未提交改动断言 `stale-dirty-tree`）；断言不读 config〔grill Q3 反转初版「断言无 subprocess」；Req: 自跑 git 作新鲜度 owner、门控外置〕

## 2. hr_tg_intersect.py（capability: hr-tg-intersection-check / T81）

- [ ] 2.1 写 `tests/test_hr_tg_intersect.py`：命中→`hit:[...]｜依据已声明:[...]`+锚串、无交集→`none｜依据已声明:[...]`、**依据可见使欠声明可审**、描述性/否定/fence内不算命中、正文区声明不计、单一源变更即生效、单一源损坏 fail-closed〔grill Q1；Req: 求交带依据、单一源读〕
- [ ] 2.2 实现 tg02_hit 三防线泛化：fence-aware + 头部区（首个 `## ` 前）+ `startswith("〔TG")` 声明行 → 抽全部 `〔TG-\d\d` 命中集〔Req: 求交（复用先例）〕
- [ ] 2.3 实现 HR-TG 单一源 parse：定位 `## 七、HR-TG` 段抓 `> 成员：` 行 `TG-\d\d`，禁硬编码；求交 + 输出 `hit/none｜依据已声明:[...]` + 规范锚串（不 emit 裸 none）〔grill Q1；Req: HR-TG 单一源读、依据暴露〕

## 3. review_disposition_check.py（capability: roadmap-review-reconcile / T82）

- [ ] 3.1 写 `tests/test_review_disposition_check.py`：section-missing / section-empty / **section-ok-DISPOSITION-UNCHECKED** 三码 + **收尾句「无『未处置』」不假阳负例** + 「不冒充逐条完整性」断言 + 文件不可读 fail-closed〔grill Q2；Req: 存在性非空断言、信任边界不假阳、坏输入 fail-closed〕
- [ ] 3.2 实现 `## Review 处置` 小节定位（fence/结构感知）+ 非空判定（剔脚手架注释）→ `section-missing|section-empty|section-ok-DISPOSITION-UNCHECKED`；**禁裸子串 `未处置`**〔grill Q2；Req: 存在性非空断言、信任边界〕
- [ ] 3.3 SKILL 接入步 + 本 tool docstring 显式声明「逐条已处置为模型信任边界」（承 lens_metric_emit 诚实先例）〔Req: 逐条已处置为显式模型信任边界〕

## 4. 消费方 SKILL.md 接入（Blocked-by 1-3）

- [ ] 4.1 `sdflow-spec-review/SKILL.md:39-44` 复用守卫三判手做 prose → 调 `$RULES_ROOT/tools/outside_voice_guard.py`；判断/编排语义保留〔D1/D5〕
- [ ] 4.2 `sdflow-spec-review` + `sdflow-code-review` SKILL.md HR-TG 判定步 → 调 `hr_tg_intersect.py`〔D3〕
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
| T81 描述性/否定/fence/正文区不算命中 | tg02_hit 口径负例 |
| T82 收尾句子串不假阳 | 陷阱负例（memory gate-substring-detection） |
| hr_tg/review_disposition 无 subprocess；T80 git fixture 新鲜度+dirty fail-safe | 纯度断言 + T80 git 例外测 |
| bundle 双路径一致 + tools 全套件 -W error | dogfood / 集成 |
