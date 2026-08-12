# Tasks · implement-workflow-optimization-2026-08-p5

> Requirement 追溯：SA-03（spec-authoring delta·分批条款）/ GQ（spec-workflow delta·
> 拍板三问与机验锚）/ T275（proposal What Changes·考古层清理，无 spec delta——编辑动作）。

## 1. 拍板三问 + 机验锚（Requirement: GQ）

- [ ] 1.1 `sdflow-init/assets/workflow/tools/anchor_lint.py`：`ANCHOR_PREFIXES` 登记
      `sdflow:gate-questions` + 新 check 函数（layer=spec-review 恒须、q 逐字
      `scope,deps,risk`、fence-aware、code-review 不查），design Db 口径
- [ ] 1.2 `tools/tests/test_anchor_lint.py`：正例 / 缺锚 / q 变异（缺项·增项·乱序）/
      fence 内示范 / code-review layer 不查，五组契约测试（GQ 全 Scenario 覆盖）
- [ ] 1.3 `sdflow-spec-review/SKILL.md` Step4 报告条款：决策登记区顶部三问小节模版
      （每问 = 问题 + 评审侧自答指回证据 + 勾选位）+ 锚行；grep bundle 内 spec-review
      规则文件是否另有报告结构描述，有则同步（design scope-check 表逐行核对）
- [ ] 1.4 p4 归档报告**副本**回放：原样 lint FAIL（缺新锚）、手工加段后 PASS——验证
      检查真实生效（不改归档文件）

## 2. sdflow-spec 分批条款（Requirement: SA-03）

- [ ] 2.1 `sdflow-spec/SKILL.md` A.1 + B.3 条款重写为 D3 全文（独立批 ≤4 问必附推荐；
      依赖链整链呈现可拍整链或链头；链头改判下游重提；组合爆炸退回链头 + 预告）
- [ ] 2.2 核对 `hack/tests/` 中消费 sdflow-spec SKILL 文本的既有测试（memo C2 名单）
      是否断言旧「一次一问」字面，有则同步断言

## 3. T275 考古层审计清理（proposal What Changes）

- [ ] 3.1 审计通道建立：`{change_dir}/audit/skill-doc1-audit.md` 骨架（14 节，每节
      删/迁/留三计数 + 边界个案注记格式），design Dc
- [ ] 3.2 7 个超 500 行 SKILL 清理（implement / code-review / roadmap / spec-review /
      done / architecture / spec）：逐文件过 DOC-1 删除测试，删或迁
      `<skill>/references/evolution-notes.md`（design Dd 统一名 + 正文末一行指针；
      sdflow-spec 已有该文件则追加）；`sdflow:principles` 托管块不触碰
- [ ] 3.3 其余 7 个 SKILL 审计（≤500 行者）：过删除测试，预期改动量小，审计结论
      同样落 audit 文件（含「零改动」结论也留档）
- [ ] 3.4 每文件清理后即跑该 skill 对应 tests/ + `hack/tests/`（memo C2 爆破面），
      红了当场修断言或回滚该处删改；全部完成后 `python3 hack/sync_principles.py --check`

## 4. 收尾（proposal What Changes·回填）

- [ ] 4.1 roadmap 阶段 5 回填：5.3 措辞按 memo D4 修正（「评估收口」→「调研记录 +
      保持 OPEN」）、子任务勾选、验收标准状态
- [ ] 4.2 issues set-status：T275→DONE、T101→DONE（evidence 各指交付锚）；T256 确认
      仍 OPEN 且调研段在册（开发 checkout 脚本，显式 `--change` 字段）
- [ ] 4.3 hand-off 注记：三问首个真实 dogfood 挂下一次设计审（本 change 时序上无法自证，
      proposal Success Metrics 时序注记）

## 5. 实现验证收尾

- [ ] 5.1 全仓 `/usr/bin/python3 -m pytest -q` 绿（含新增 anchor_lint 测试与 22 个
      SKILL 文本消费测试）
- [ ] 5.2 `git diff` 亲验：改动面与 design 组件图三流一致，无 scope 外文件

## 测试覆盖图（TG-18）

| code path | 测试类型 | 落点 |
|---|---|---|
| anchor_lint gate-questions check（存在/q 值/fence/layer 分治） | 契约单测（正例 + 4 组负例） | `tools/tests/test_anchor_lint.py`（task 1.2） |
| anchor_lint 对真实报告的端到端行为 | 归档报告副本回放（FAIL→PASS） | task 1.4 手工验收留档 |
| SKILL.md 清理后文本契约不破 | 既有 22 个文本消费测试回归 | `hack/tests/` + 各 skill `tests/`（task 3.4） |
| principles 托管块完整性 | 既有机械门 | `sync_principles.py --check` + `test_sync_principles.py`（task 3.4） |
| sdflow-spec 条款字面 | 既有 SKILL 文本断言同步 | task 2.2 |
| 三问人读交互（勾选行为） | 无自动化路径——真实 dogfood 挂下一 change 设计审 | hand-off（task 4.3，诚实边界） |
