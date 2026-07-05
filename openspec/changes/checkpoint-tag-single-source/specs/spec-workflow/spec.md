<!-- [spec-review-amendment] Q1=B：原「三站文案单一源 + doc 正则绑定」需求被证伪，
     重写为 producer→parser 集成绑定 + TAG_RE 负例矩阵。不自复制格式字面（消解 spec-review M3）。 -->

## ADDED Requirements

### Requirement: checkpoint 标签 producer→parser 契约测试

checkpoint 任务标签由 `checkpoint-commit.sh`（producer，把首参包成 commit subject）铸造、由 `ship_gate.py` 的 `TAG_RE`（parser）解析；这条 producer→parser 链 MUST 有机械绑定测试守卫，SHALL NOT 依赖对文档占位符文本的比对（文档是人读占位符、非机器解析对象）。测试 MUST 调用**真实脚本**产出 subject 再喂 parser，使 producer 包裹逻辑或 parser 正则任一漂移即令测试失败。此为纯防漂移加固，`TAG_RE` 与 `checkpoint-commit.sh` 的行为 MUST 逐字不变。

#### Scenario: 真实脚本产出的 subject 被 parser 正确识别

- **WHEN** 契约测试在临时 git repo 中以命名空间形式的首参调用真实 `checkpoint-commit.sh`（首参 = `<当前change>:task<号>-<slug>` 形态）
- **THEN** 测试 MUST 读回该次 commit 的 subject 并断言 `ship_gate.py` 的 `TAG_RE.match` 成功、捕获组分别等于该 change 名与该任务号；MUST 用真实脚本调用与真实 git commit（MUST NOT 用手写字符串 mock subject——否则放过 producer 包裹漂移）

#### Scenario: 裸格式经真实脚本产出仍被识别且命名空间组为空

- **WHEN** 契约测试以裸形式首参（`task<号>-<slug>`，无命名空间前缀）调用真实 `checkpoint-commit.sh`
- **THEN** 测试 MUST 断言 `TAG_RE.match` 成功、命名空间捕获组为 `None`、任务号捕获组正确——固定裸格式向后兼容在 producer→parser 链上的实际行为

### Requirement: TAG_RE 负例矩阵

`TAG_RE` 的正确性 MUST 由一组 **MUST NOT match** 的负例断言守卫，SHALL NOT 仅以单个 happy 正例（match + 捕获正确）覆盖——单正例对正则放松无区分力（已实证：尾 dash 变可选 / 命名空间允许大写 / 编号可空 三类放松在仅有正例时均静默保绿）。负例集 MUST 至少覆盖这三类已知放险。

#### Scenario: 已知放松类被负例矩阵挡住

- **WHEN** 负例矩阵对一组畸形 subject 断言 `TAG_RE.match`
- **THEN** 对"无尾 dash"（如 `checkpoint(task1slug)`）、"大写命名空间"（如 `checkpoint(DEMO:task1-)`）、"编号位非数字或为空"（如 `checkpoint(task-1-)`）三类，`TAG_RE.match` MUST 返回 `None`；使 `TAG_RE` 被无意放松时至少一条负例转红、MUST NOT 因只有 happy 正例而静默保绿
