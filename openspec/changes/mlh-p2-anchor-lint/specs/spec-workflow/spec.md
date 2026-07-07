## ADDED Requirements

### Requirement: 评审报告锚自检由确定性脚本判定

spec-review Step3 / code-review Step5 的**评审报告锚自检**（四类 v1 锚存在性 + `sdflow:lens-metric` 字段/枚举/子格式合法性）MUST 由确定性脚本 `anchor_lint` 判定，MUST NOT 作为 prose 协议交执行模型手 grep + 肉眼核枚举（与 `resolve-workflow.sh`、`ship_gate.py`、`trivial_shape.py` 同族——机械协议脚本化，adr/0006）。脚本 MUST 只读、双输出（human 行 + JSON 机读）、以退出码承载判定（0=干净 / 非零=违规或脚本自身错误）；编排 SKILL MUST 调该脚本并遵其退出码，MUST NOT 静默吞非零退出。

脚本 MUST 校验：①四类锚存在性——`sdflow:outside-voice`、`sdflow:hr-tg`、`sdflow:step1-broad-review` 恒须存在，`sdflow:lens-metric` 受 `config.yaml metrics.enabled` 门控（关闭或 config 缺失时缺此类 MUST NOT 阻塞；config 存在但读不出该键 → fail-closed，见下 Scenario）；②`sdflow:lens-metric` 锚的 `layer`/`lens`/`runner` 枚举域与 `sev` 子格式（`致N/高N/中N/低N`）合法性，枚举取值域 MUST 从 `lens-metric-contract.md` 的 `lens-metric-enums` 机读块单一权威源读取而 MUST NOT 在脚本内复制清单。脚本 MUST 沿用 fence-aware 行级纪律（跳 fenced code block、锚独占行前缀匹配、受限 kv 解析），在脚本内重实现该纪律（与 `lens_metric_aggregate` 平行、同纪律、MUST NOT 跨 skill import）而 MUST NOT 用 `ship_gate` 的定长整行原语（匹配不了变长度量锚）。契约 `lens-metric-enums` 机读块 SHALL 为 layer/lens/runner/sev 的机读单一源，任何消费该枚举者（`anchor_lint` 运行时读、`lens_metric_aggregate` 硬编码）MUST NOT 与之漂移，一致性 SHALL 由测试守卫。

`sdflow:lens-metric` 的 `site` 字段 MUST NOT 纳入越域自检——任意取值只多一个分组行、MUST NOT 触发报错（契约 CF-补2：仅 `layer`/`lens`/`runner`/`sev` 受自检约束）。锚行 `findings=N` 与合并池实收数的**数值一致性**MUST 显式声明为主 session 信任边界、**非机械可验**（主 session 自做去重又写锚、自核无独立性）——脚本 MUST NOT 谎称能机械保证数值正确，机械层只兜「存在 + 枚举域 + sev 子格式」。

#### Scenario: 干净报告自检通过

- **WHEN** 一份评审报告含全部恒须四类锚、且所有 `lens-metric` 锚字段齐全、枚举在域、`sev` 子格式合法，`anchor_lint --report <path> --layer <spec-review|code-review>` 运行
- **THEN** 脚本 SHALL 以退出码 0 返回、无违规输出；SKILL 自检步据此放行

#### Scenario: 缺恒须锚自检阻塞

- **WHEN** 报告缺失 `sdflow:outside-voice` / `sdflow:hr-tg` / `sdflow:step1-broad-review` 中任一恒须锚
- **THEN** 脚本 SHALL 以非零退出码返回并点名缺失锚类，SKILL 自检步 SHALL 报错阻塞，MUST NOT 静默放行

#### Scenario: lens-metric 越域枚举或缺字段或坏 sev 子格式被拦

- **WHEN** 某 `sdflow:lens-metric` 锚的 `layer`/`lens`/`runner` 取值越出枚举域、或缺任一必填字段、或 `sev` 不符 `致N/高N/中N/低N` 子格式
- **THEN** 脚本 SHALL 非零退出并点名违规锚与字段；枚举取值域 SHALL 从 `lens-metric-contract.md` 读取判定，MUST NOT 在脚本内复制枚举清单形成第二真相源

#### Scenario: site 任意取值不报错

- **WHEN** 某 `sdflow:lens-metric` 锚的 `site` 取一个不在常见集 {code-voice, hr-tg, design-voice, —} 内的值，但 `layer`/`lens`/`runner`/`sev` 均合法
- **THEN** 脚本 SHALL 判该锚合法（退出码不因 site 值而非零）——site 仅分组消歧、不纳入越域自检（契约 CF-补2）

#### Scenario: metrics 门控关闭或 config 缺失时缺 lens-metric 锚不阻塞

- **WHEN** `config.yaml` 的 `metrics.enabled` 为 false、或 `config.yaml` 文件不存在（环境问题非报告缺陷），报告不含任何 `sdflow:lens-metric` 锚，但四类恒须锚（除 lens-metric）齐全
- **THEN** 脚本 SHALL 以退出码 0 返回——lens-metric 一类整体不校验不阻塞，与两审 SKILL 现有门控一致；config 缺失 SHALL 判 `enabled=false`（与消费仓默认一致）

#### Scenario: config 存在但读不出 metrics.enabled 键 fail-closed

- **WHEN** `config.yaml` 文件存在，但受限解析匹配不到 `metrics:` 块下 `enabled: true|false`（被改坏 / 结构异常）
- **THEN** 脚本 SHALL 以非零退出码（ERROR）返回、拒绝认证——MUST NOT 因 config 读取静默失败而悄悄跳过整类 lens-metric 校验（反静默：任何一层覆盖不得无声蒸发）；区别于 config **文件缺失**（判 false 放行），config **存在却坏**须 fail-closed

#### Scenario: fenced code block 内示范锚不被当真锚

- **WHEN** 报告在 ``` fence 内含 `sdflow:lens-metric v1` 等锚字面作语法示范，且 fence 外无对应真锚
- **THEN** 脚本 SHALL 判该 fence 内锚为示范（非真锚、不计入存在性、不参与枚举校验）——沿用 fence-aware 行级纪律，MUST NOT 因 fence 内示范锚假命中或假报枚举违规

#### Scenario: 脚本读不到报告或自身错误 fail-closed

- **WHEN** `--report` 指向的文件不存在 / 不可读，或 `lens-metric-contract.md` 无法定位、或找不到 `lens-metric-enums` 机读块、或块解析出空枚举
- **THEN** 脚本 SHALL 以非零退出码返回（fail-closed，判「无法确证干净」），MUST NOT 以退出码 0 假装自检通过、MUST NOT 回落脚本内硬编码枚举兜底（否则第二真相源复活）

#### Scenario: 枚举单一源一致性由测试守卫

- **WHEN** `lens_metric_aggregate.py` 硬编码的 `LAYER_ENUM`/`LENS_ENUM` 与契约 `lens-metric-enums` 机读块的 `layer`/`lens` 集不一致（有人改契约块未同步 aggregator，或反之）
- **THEN** 一致性测试 SHALL 失败——契约机读块为单一权威源，消费该枚举的脚本 MUST NOT 与之漂移；该测试 MUST NOT 跨 skill import（自带极简契约块解析）

#### Scenario: 数值一致性诚实声明为信任边界

- **WHEN** 某 `sdflow:lens-metric` 锚的 `findings=N` 与该镜合并池实收数不符
- **THEN** 脚本 SHALL NOT 声称能检出该不一致（`findings=N` vs 实收数属主 session 信任边界、非机械可验）；SKILL 自检步 SHALL 保留「数值一致性是主 session 职责、脚本不谎称机验」的诚实声明，MUST NOT 因接了脚本而删除该边界声明
