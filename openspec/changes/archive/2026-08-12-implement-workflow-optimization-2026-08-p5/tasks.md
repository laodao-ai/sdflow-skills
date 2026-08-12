# Tasks · implement-workflow-optimization-2026-08-p5

> Requirement 追溯：SA-03（spec-authoring delta·分批条款）/ GQ（spec-workflow delta·
> 拍板三问与机验锚）/ T275（proposal What Changes·考古层清理，无 spec delta——编辑动作）。

## 1. 拍板三问 + 机验锚（Requirement: GQ）

- [x] 1.1 `sdflow-init/assets/workflow/tools/anchor_lint.py`：`ANCHOR_PREFIXES` 登记
      `sdflow:gate-questions` + 新 check 函数（layer=spec-review 恒须、q 逐字
      `scope,deps,risk`、fence-aware、重复锚 fail-closed、code-review 不查），design Db
      口径 [spec-review-amendment]：新函数 MUST 接收 `layer` 参数并按
      `check_declared_sites` 模式在函数体内分支；MUST NOT 复用/扩展
      `check_existence`/`MANDATORY`（其 layer 死参从不分流）
- [x] 1.2 `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`：正例 / 缺锚 /
      q 变异（缺项·增项·乱序·**整个缺 `q=` 属性**）/ **重复锚** / fence 内示范 /
      code-review layer 不查，七组契约测试（GQ 全 Scenario 覆盖）[spec-review-amendment]
- [x] 1.3 `sdflow-spec-review/SKILL.md` Step4 报告条款：决策登记区顶部三问小节模版
      （每问 = 问题 + 评审侧自答指回证据 + 勾选位）+ 锚行；grep bundle 内 spec-review
      规则文件是否另有报告结构描述，有则同步（design scope-check 表逐行核对）；
      [spec-review-amendment] SKILL 自检步对该锚报错的提示文案须含 fix 指引
      （problem/cause/fix，fix 指回报告模版所在小节——lint 本身沿用既有
      `[anchor_lint] VIOLATION` 结构化格式，三件套转译由 SKILL 层承担）
- [x] 1.4 p4 归档报告**副本**回放：原样 lint FAIL（缺新锚）、手工加段后 PASS——验证
      检查真实生效（不改归档文件）

## 2. sdflow-spec 分批条款（Requirement: SA-03）

- [x] 2.1 `sdflow-spec/SKILL.md` A.1 + B.3 条款重写为 D3 全文（独立批 ≤4 问必附推荐；
      依赖链整链呈现可拍整链或链头；链头改判下游重提；组合爆炸退回链头 + 预告）
- [x] 2.2 核对 `hack/tests/` 中消费 sdflow-spec SKILL 文本的既有测试（memo C2 名单）
      是否断言旧「一次一问」字面，有则同步断言（已知
      `test_sdflow_spec_resident_contract.py:28` 一处）
- [x] 2.3 [spec-review-amendment] 「一次一问」残留规范面同步（design De 修订版三处）：
      ① `sdflow-spec/SKILL.md:161` 相位流程图字样改为与 D3 一致；
      ② `sdflow-init/assets/workflow/generation-process.md:75` 拷问协议括号措辞同步
      （bundle 权威源，经 `sdflow-init update` 下发）；③ spec-workflow 主 spec 的
      「拷问协议不因触发方式改变」Scenario 经本 change delta MODIFIED 同步（archive 时
      对码核验）；完成后全仓负向 grep `一次只问一个|一次一问` 确认规范面归零
      （docs/ 与 reference/ 描述性提法除外）

## 3. T275 考古层审计清理（proposal What Changes）

- [x] 3.1 审计通道建立：`{change_dir}/audit/skill-doc1-audit.md` 骨架（**15** 节
      [spec-review-amendment]，每节删/迁/留三计数 + 边界个案注记格式；名单以
      `find . -maxdepth 2 -name SKILL.md` 实测为准，含 sdflow-devenv /
      sdflow-upstream-watch），design Dc
- [x] 3.2 7 个超 500 行 SKILL 清理（implement / code-review / roadmap / spec-review /
      done / architecture / spec）：逐文件过 DOC-1 删除测试，删或迁
      `<skill>/references/evolution-notes.md`（design Dd 统一名 + 正文末一行指针；
      sdflow-spec 已有该文件则追加）；`sdflow:principles` 托管块不触碰
- [x] 3.3 其余 8 个 SKILL 审计（≤500 行者）[spec-review-amendment]：过删除测试，
      预期改动量小，审计结论同样落 audit 文件（含「零改动」结论也留档）
- [x] 3.4 每文件清理后即跑该 skill 对应 tests/ + `hack/tests/`（memo C2 爆破面）+
      `python3 hack/sync_principles.py --check`（挪进逐文件循环，托管块误伤当场归因
      [spec-review-amendment]），红了当场修断言或回滚该处删改

## 4. 收尾（proposal What Changes·回填）

- [x] 4.1 roadmap 阶段 5 回填：5.3 措辞按 memo D4 修正（「评估收口」→「调研记录 +
      保持 OPEN」）、5.2 过时措辞顺带修正（「spec-review SKILL Step3 报告模版」→
      Step4，roadmap.md:345 [spec-review-amendment]）、子任务勾选、验收标准状态
- [x] 4.2 issues set-status：T275→DONE、T101→DONE（evidence 各指交付锚）；T256 确认
      仍 OPEN 且调研段在册（开发 checkout 脚本，显式 `--change` 字段）
- [x] 4.3 hand-off 注记：三问首个真实 dogfood 挂下一次设计审（本 change 时序上无法自证，
      proposal Success Metrics 时序注记）

## 5. 实现验证收尾

- [x] 5.1 全仓 `/usr/bin/python3 -m pytest -q` 绿（含新增 anchor_lint 测试与 22 个
      SKILL 文本消费测试）
- [x] 5.2 `git diff` 亲验：改动面与 design 组件图三流一致，无 scope 外文件

## 测试覆盖图（TG-18）

| code path | 测试类型 | 落点 |
|---|---|---|
| anchor_lint gate-questions check（存在/q 值/缺属性/重复锚/fence/layer 分治） | 契约单测（正例 + 6 组负例）[spec-review-amendment] | `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`（task 1.2） |
| anchor_lint 对真实报告的端到端行为 | 归档报告副本回放（FAIL→PASS） | task 1.4 手工验收留档 |
| SKILL.md 清理后文本契约不破 | 既有 22 个文本消费测试回归 | `hack/tests/` + 各 skill `tests/`（task 3.4） |
| principles 托管块完整性 | 既有机械门 | `sync_principles.py --check` + `test_sync_principles.py`（task 3.4） |
| sdflow-spec 条款字面 | 既有 SKILL 文本断言同步 | task 2.2 |
| 三问人读交互（勾选行为） | 无自动化路径——真实 dogfood 挂下一 change 设计审 | hand-off（task 4.3，诚实边界） |
