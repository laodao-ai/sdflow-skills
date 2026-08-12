---
impl-pipeline: tickets
---

## Global Constraints

- 清理是**编辑动作**：每处删/迁必须可通过 DOC-1 删除测试逐条复核，审计留档使 code-review 冷层能抽查「删的是不是考古层」。
- 拍板三问是**增量锚**：新锚加入不改变既有锚（`sdflow:hr-tg` / `sdflow:lens-metric` / `sdflow:outside-voice` / `sdflow:fanout-capability` / `sdflow:declared-sites` / `sdflow:step1-broad-review`）的任何检查语义。
- 分批条款只改**提问节奏**，不动相位 A/B 的收束判据（A.2 禁止清单、B.5 停止信号原样）。
- MUST NOT 动 ship_gate.py、评审镜 roster、裁决协议（adr/0041）、model/effort 分档链。
- `sdflow:principles` 托管块 MUST NOT 触碰（`sync_principles.py --check` 门守）。
- anchor_lint 改动走权威源 `sdflow-init/assets/workflow/tools/`，不在消费仓改。
- 外迁载体统一：`<skill>/references/evolution-notes.md`（design Dd），SKILL 正文末尾指针统一为一行：`历史取舍不进入默认运行；仅在审计历史依据时读取 references/evolution-notes.md。`
- T275 清理的 DOC-1 删除测试判据：「只有读过上一版的人才需要的句子，不属于正文」。
- 每文件清理后即跑该 skill 对应 `tests/` + `hack/tests/`（memo C2 爆破面）+ `python3 hack/sync_principles.py --check`，红了当场修断言或回滚该处删改。

### Task 1: anchor_lint 拍板三问机验实现

**Blocked-by:** none
**R-ID:** GQ

在 `sdflow-init/assets/workflow/tools/anchor_lint.py` 实现 `sdflow:gate-questions` 锚的机验检查：

- `ANCHOR_PREFIXES` 字典登记 `"<!-- sdflow:gate-questions v1"` 前缀
- 新增 `check_gate_questions(report_text, layer, findings)` 函数：
  - MUST 接收 `layer` 参数，在函数体内按 layer 早返回（沿 `check_declared_sites` 的 layer-conditional 模式）
  - `layer=spec-review` 时 always-on 检查（不受 `metrics.enabled` 门控）
  - `layer=code-review` 时直接返回，不检查
  - 校验规则：fence 外存在性恒须、`q` 值逐字等于 `scope,deps,risk`（有序无增减）、缺 `q=` 属性同判违规、fence 外 ≥2 条判重复违规（fail-closed，沿 `duplicate-fanout-anchor` 先例）
  - MUST NOT 复用/扩展 `check_existence`/`MANDATORY` 列表（其 layer 参数是死参从不分流）

在 `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` 新增七组契约测试：正例 / 缺锚负例 / q 值变异负例（缺项·增项·乱序·缺 `q=` 属性）/ 重复锚负例 / fence 内示范锚不算 / code-review layer 不查。

用 p4 归档报告**副本**做回放核验：原样 lint FAIL（缺新锚）→ 手工加段后 PASS（不改归档文件原件）。

- [x] `ANCHOR_PREFIXES` 登记 + `check_gate_questions` 函数实现（layer 分治、q 值校验、重复锚 fail-closed、fence-aware）
- [x] 七组契约测试全部通过（正例 / 缺锚 / q 变异四子项 / 重复锚 / fence 内 / code-review 不查）
- [x] p4 归档报告副本回放：原样 FAIL → 加段后 PASS
- [x] 既有 anchor_lint 测试无回归

### Task 2: sdflow-spec 分批条款 + 规范面同步

**Blocked-by:** none
**R-ID:** SA-03

重写 `sdflow-spec/SKILL.md` A.1 + B.3 条款为 D3 全文（呈现与拍板分离协议）：
- 独立批 ≤4 问必附推荐
- 依赖链整链呈现（链结构 + 每环推荐 + 推荐整链路径），人可拍整链或链头
- 链头改判时下游按新前提重提（背景不重复）
- 组合爆炸时退回链头 + 一句话预告各选项下游影响
- 只拍链头时下游保持待拍板状态，MUST NOT 把沉默当授权

同步「一次一问」残留规范面三处（design De）：
① `sdflow-spec/SKILL.md:161` 相位流程图字样改为与 D3 一致
② `sdflow-init/assets/workflow/generation-process.md:75` 拷问协议括号措辞同步（bundle 权威源）
③ spec-workflow 主 spec 的「拷问协议不因触发方式改变」Scenario 经本 change delta MODIFIED 同步

核对 `hack/tests/` 中消费 sdflow-spec SKILL 文本的既有测试（已知 `test_sdflow_spec_resident_contract.py:28` 一处），如断言旧「一次一问」字面则同步断言。

完成后全仓负向 grep `一次只问一个|一次一问` 确认规范面归零（docs/ 与 reference/ 描述性提法除外）。

- [x] A.1 + B.3 条款重写为 D3 全文
- [x] 相位流程图「一次一问」字样已改
- [x] `generation-process.md:75` 括号措辞已同步
- [x] spec-workflow 主 spec Scenario 措辞已同步
- [x] 既有测试断言已同步（旧字面不再命中）
- [x] 全仓规范面 grep 确认归零

### Task 3: sdflow-spec-review 报告模版三问小节 + 锚行

**Blocked-by:** 1
**R-ID:** GQ

在 `sdflow-spec-review/SKILL.md` Step4 报告条款中：
- 决策登记区顶部新增「拍板三问」小节模版（每问 = 问题 + 评审侧自答指回证据 + 勾选位）
- 紧邻三问小节放锚行 `<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->`
- SKILL 自检步对该锚报错的提示文案须含 fix 指引（problem/cause/fix 三件套，fix 指回报告模版所在小节）

grep bundle 内 spec-review 规则文件（经 `~/.sdflow/hack/resolve-workflow.sh` 解析取得规则根）是否另有报告结构描述，有则同步（design scope-check 表逐行核对）。

- [x] 三问小节模版加入 Step4 报告条款（决策登记区顶部）
- [x] 锚行加入（紧邻三问小节）
- [x] 自检步报错文案含 problem/cause/fix 指引
- [x] bundle 内规则文件报告结构描述已同步（或确认无需同步）

### Task 4: 考古层审计清理（15 个 SKILL.md）

**Blocked-by:** 2,3
**R-ID:** T275

审计通道建立：`{change_dir}/audit/skill-doc1-audit.md` 骨架（15 节，每节删/迁/留三计数 + 边界个案注记格式；名单以 `find . -maxdepth 2 -name SKILL.md` 实测为准）。

7 个超 500 行 SKILL 重点清理（implement 821 / code-review 771 / roadmap 715 / spec-review 593 / done 567 / architecture 562 / spec 528 行）：逐文件过 DOC-1 删除测试，删或迁 `<skill>/references/evolution-notes.md`（design Dd 统一名 + 正文末一行指针；sdflow-spec 已有该文件则追加）；`sdflow:principles` 托管块不触碰。

其余 8 个 SKILL 审计（≤500 行者）：过删除测试，预期改动量小，审计结论同样落 audit 文件（含「零改动」结论也留档）。

每文件清理后即跑该 skill 对应 `tests/` + `hack/tests/`（memo C2 爆破面）+ `python3 hack/sync_principles.py --check`，红了当场修断言或回滚该处删改。

- [x] `audit/skill-doc1-audit.md` 骨架建立（15 节）
- [x] 7 个超 500 行 SKILL 逐文件审计清理 + 每文件测试绿
- [x] 8 个 ≤500 行 SKILL 审计（含零改动留档）
- [x] `sync_principles.py --check` 全仓通过
- [x] 全仓 pytest 无回归

### Task 5: 收尾回填（roadmap + issues + hand-off）

**Blocked-by:** 1,2,3,4
**R-ID:** GQ, SA-03, T275

- roadmap 阶段 5 回填：5.3 措辞按 memo D4 修正（「评估收口」→「调研记录 + 保持 OPEN」）、5.2 过时措辞修正（「Step3」→「Step4」）、子任务勾选、验收标准状态
- issues set-status：T275→DONE、T101→DONE（evidence 各指交付锚）；T256 确认仍 OPEN 且调研段在册（显式 `--change` 字段）
- hand-off 注记：三问首个真实 dogfood 挂下一次设计审

- [x] roadmap 5.3/5.2 措辞修正 + 子任务勾选
- [x] T275→DONE / T101→DONE / T256 确认 OPEN
- [x] hand-off 注记落盘

### Task 6: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4,5
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落 `impl-reports/task6-verify.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

`git diff` 亲验：改动面与 design 组件图三流一致，无 scope 外文件。

- [x] 单元测试证据齐全并通过
- [x] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [x] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
