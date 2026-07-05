# Tasks — gate-checkpoint-hardening

> 全部为权威源（`sdflow-init/assets/**` bundle + 自制 skill）的规则/文案/注释编辑 + 极少 `ship_gate.py` 注释，无逻辑代码，无新 pytest（测试 = 机械核对 + 既有 `sdflow-ship/tests` 零回归）。
> 每任务 commit 步 MUST 用 `bash ~/.sdflow/hack/checkpoint-commit.sh gate-checkpoint-hardening:task<N>-<slug>`（命名空间格式，gate 只认本 change 标签）。

## 1. checkpoint 标签契约单一真相源（T36/T37/T38/T43，TG-25 一致性）

- [ ] 1.1 接地定位全套载体：`checkpoint-commit.sh` 头注释/`--help`、`workflow.md` 派发指令、`sdflow-ship/SKILL.md` 派发+台账、`sdflow-code-review/SKILL.md` 台账锚、主 spec Scenario、producer 模板样例锚——逐一确认现状（对 design.md BASE-29 scope-check 表核对）
- [ ] 1.2 确立 `checkpoint-commit.sh` 契约（头注释 + `--help`）为标签形状**唯一权威源**：补全/校准其格式串定义
- [ ] 1.3 T36：`workflow.md` + `sdflow-ship/SKILL.md` 的派发指令改**引用式**（"派发格式见 checkpoint-commit.sh 契约"），删除各自的完整格式串复述
- [ ] 1.4 T38：文档/spec 占位符 `<当前change>` 等歧义写法 → `<change-slug>`（明示占位），逐处替换（先接地确认哪些文件真含歧义写法）
- [ ] 1.5 T43：producer 展示的机器锚样例收紧为独占 bare line（去反引号/同行尾注），与真产报告一致
- [ ] 1.6 机械核对：全套载体无第二份完整格式串复述；grep 确认无残留 `<当前change>`；模板锚样例为独占行
- [ ] 1.7 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task1-tag-single-source`

## 2. gate 新鲜度 committed-only 定夺（T35 / T33，ADR-1=C）

- [ ] 2.1 `ship_gate.py:64-65` 的 T33 停置注释更新为定夺结论（committed-only 正式化，附"盘面即状态"理由），无逻辑变更
- [ ] 2.2 `sdflow-ship/SKILL.md` 收尾段加**非门禁软提示**：工作树有未提交非-openspec 改动时提示"gate 判定不含它们"（明确不改退出码语义）
- [ ] 2.3 跑 `pytest sdflow-ship/tests/` 确认零回归（无逻辑改动，应全绿）
- [ ] 2.4 关账：T33 已 WONTDO 无需动；T35 → WONTDO（gate 侧）附理由；软提示能力落 SKILL 记 DONE
- [ ] 2.5 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task2-freshness-committed-only`

## 3. gate 熔断计数负结果登记（T26，ADR-2=A）

- [ ] 3.1 `sdflow-ship/SKILL.md` 熔断条款补一句：重试计数 = 编排器单 invocation 短时职责，不下沉持久化（附三红线：盘面即状态 / gate 零副作用 / ship 零跨步状态）
- [ ] 3.2 关账：T26 → WONTDO，理由="已探索·结论=不下沉·撞三红线"（诚实负结果，防后人重开）
- [ ] 3.3 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task3-breaker-no-persist`

## 4. spec delta 对码核验 + 校验

- [ ] 4.1 按实现实况核 `specs/spec-workflow/spec.md` 三条 ADDED 需求与代码/文案一致（单源引用式、committed-only、熔断不下沉都已落实）
- [ ] 4.2 `openspec validate gate-checkpoint-hardening` 通过
- [ ] 4.3 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task4-spec-verify`

## 5. 部署 + 全量验证

- [ ] 5.1 开发 checkout 跑 `bash setup.sh`（改 assets/workflow + assets/hack 才让全局 canonical 生效、测得到）
- [ ] 5.2 `resolve-workflow.sh` 解析确认 canonical 指向本 checkout；抽查 workflow.md/checkpoint-commit.sh 改动经全局生效
- [ ] 5.3 全仓 `pytest` 确认零回归
- [ ] 5.4 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task5-deploy-verify`
