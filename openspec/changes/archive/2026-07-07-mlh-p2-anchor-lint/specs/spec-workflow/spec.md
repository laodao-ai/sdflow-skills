## ADDED Requirements

### Requirement: 评审报告锚自检由确定性脚本判定

spec-review Step3 / code-review Step5 的**评审报告锚自检**（四类 v1 锚存在性 + `sdflow:lens-metric` 字段/枚举/子格式合法性）MUST 由确定性脚本 `anchor_lint` 判定，MUST NOT 作为 prose 协议交执行模型手 grep + 肉眼核枚举（与 `resolve-workflow.sh`、`ship_gate.py`、`trivial_shape.py` 同族——机械协议脚本化，adr/0006）。脚本 MUST 只读、双输出（human 行 + JSON 机读）、以退出码承载判定（0=干净 / 非零=违规或脚本自身错误）；编排 SKILL MUST 调该脚本并遵其退出码，MUST NOT 静默吞非零退出。

脚本 MUST 校验：①四类锚存在性——`sdflow:outside-voice`、`sdflow:hr-tg`、`sdflow:step1-broad-review` 恒须存在，`sdflow:lens-metric` 受 `config.yaml metrics.enabled` 门控（关闭或 config 未配置 metrics 时缺此类 MUST NOT 阻塞；config 存在且 `metrics:` 块在但值非法 → fail-closed，见下 Scenario）；metrics 启用时 lens-metric 不止「≥1 条」——`lens="broad"` 与 `lens="outside-voice"` 各 MUST 至少一行（两者恒跑），缺即违规；其余 per-lens 完整性属主 session 信任边界。②`sdflow:lens-metric` 锚的字段校验——`layer`/`lens`/`runner` 枚举域、`sev` 子格式（`致N/高N/中N/低N`）、且 `layer` MUST 等于 CLI `--layer`（防错层度量锚漏网）、五计数字段 `findings`/`采纳`/`裁掉`/`defer`/`独立` MUST 为十进制非负整数。枚举取值域 MUST 从 `lens-metric-contract.md` 的 `lens-metric-enums` 机读块单一权威源读取而 MUST NOT 在脚本内复制清单。脚本 MUST 沿用 fence-aware 行级纪律（跳 fenced code block、锚独占行前缀匹配、受限 kv 解析），在脚本内重实现该纪律（与 `lens_metric_aggregate` 平行、同纪律、MUST NOT 跨 skill import）而 MUST NOT 用 `ship_gate` 的定长整行原语（匹配不了变长度量锚）。契约 `lens-metric-enums` 机读块 SHALL 为 layer/lens/runner/sev 的机读单一源，任何消费该枚举者（`anchor_lint` 运行时读、`lens_metric_aggregate` 硬编码）MUST NOT 与之漂移，一致性 SHALL 由测试守卫。**契约机读块 SHALL 与消费它的 `tools/` 脚本同批部署下发**（`sdflow-init` 刷新 `tools/` 时一并刷新 `lens-metric-contract.md`），使本地 pin 消费仓 MUST NOT 出现「新脚本 + 旧契约无块」的永久 fail-closed 错配。

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

#### Scenario: config 缺失或未配置 metrics 块时缺 lens-metric 锚不阻塞

- **WHEN** 下列之一：`config.yaml` 文件不存在；或文件存在但**无顶层 `metrics:` 块**（该键从未声明——消费仓常态，`sdflow-init update` 从不为已存在 config 注入新顶层键）。报告不含任何 `sdflow:lens-metric` 锚，四类恒须锚（除 lens-metric）齐全
- **THEN** 脚本 SHALL 判 `enabled=false` 并以退出码 0 返回——lens-metric 一类整体不校验不阻塞。**「无 `metrics:` 块」与「文件缺失」同属放行分支**（消费仓默认 false），MUST NOT 因未配置 metrics 而 ERROR 阻塞（否则 100% 未配置 metrics 的消费仓每轮评审假阻塞）

#### Scenario: metrics 块存在但值非法 fail-closed

- **WHEN** `config.yaml` 存在且有顶层 `metrics:` 块，但该块内（至下一顶层键前）**解不出合法 `enabled: true|false`**（拼错 / 非法布尔拼写 / 结构损坏）
- **THEN** 脚本 SHALL 以非零退出码（ERROR）返回、拒绝认证——MUST NOT 因 config 读取静默失败而悄悄跳过整类 lens-metric 校验（反静默）。「坏」严格限于**块在但值非法**；块**不在**走上一 Scenario 放行。块边界判定 MUST 先定位 `metrics:` 行再限范围至下一顶层键（防多段 config 误配对）

#### Scenario: metrics 启用时缺 broad 或 outside-voice 度量行被拦

- **WHEN** `metrics.enabled` 为 true，报告含若干 `sdflow:lens-metric` 锚但**缺 `lens="broad"` 或缺 `lens="outside-voice"` 行**（两者对应恒跑的 Step1 广审与 outside-voice）
- **THEN** 脚本 SHALL 非零退出并点名缺失 lens——metrics 启用时这两行为最小必有行；其余 per-lens（domain/adversarial/grounding）完整性 SHALL 属主 session 信任边界、脚本不强制（报告机读不出「本轮跑了哪些镜」）

#### Scenario: lens-metric 行内 layer 与 CLI --layer 不符被拦

- **WHEN** `anchor_lint --layer code-review` 运行，但某 fence 外 `sdflow:lens-metric` 锚的 `layer="spec-review"`（错层，如从另一 layer 报告误贴）
- **THEN** 脚本 SHALL 非零退出并点名错层锚——fence 外真 lens-metric 锚的 `layer` MUST 等于 CLI `--layer`，MUST NOT 仅因 `layer` 在枚举域内就放过错层锚

#### Scenario: 计数字段非非负整数被拦

- **WHEN** 某 `sdflow:lens-metric` 锚的 `findings`/`采纳`/`裁掉`/`defer`/`独立` 任一取负数 / 浮点串 / 空串 / 中文数字等非十进制非负整数值
- **THEN** 脚本 SHALL 非零退出并点名违规字段——五计数字段 MUST 校验为十进制非负整数，前置拦截坏值进聚合（不依赖下游 aggregator `_int` 兜底）

#### Scenario: fenced code block 内示范锚不被当真锚

- **WHEN** 报告在 ``` fence 内含 `sdflow:lens-metric v1` 等锚字面作语法示范，且 fence 外无对应真锚
- **THEN** 脚本 SHALL 判该 fence 内锚为示范（非真锚、不计入存在性、不参与枚举校验）——沿用 fence-aware 行级纪律，MUST NOT 因 fence 内示范锚假命中或假报枚举违规

#### Scenario: 脚本读不到报告或自身错误 fail-closed

- **WHEN** `--report` 指向的文件不存在 / 不可读，或 `lens-metric-contract.md` 无法定位、或找不到 `lens-metric-enums` 机读块、或块解析出空枚举
- **THEN** 脚本 SHALL 以非零退出码返回（fail-closed，判「无法确证干净」），MUST NOT 以退出码 0 假装自检通过、MUST NOT 回落脚本内硬编码枚举兜底（否则第二真相源复活）

#### Scenario: 枚举单一源一致性由测试守卫

- **WHEN** `lens_metric_aggregate.py` 硬编码的 `LAYER_ENUM`/`LENS_ENUM` 与契约 `lens-metric-enums` 机读块的 `layer`/`lens` 集不一致（有人改契约块未同步 aggregator，或反之）
- **THEN** 一致性测试 SHALL 失败——契约机读块为单一权威源，消费该枚举的脚本 MUST NOT 与之漂移；该测试 MUST NOT 跨 skill import（自带极简契约块解析），且 SHALL 对同一真实契约 fixture 交叉断言其 mini-parser 与 `anchor_lint` 解析路径输出相等（降低两独立解析器边界分歧造成的假绿）

#### Scenario: 机读契约与 tools 脚本同批部署防 pin 错配

- **WHEN** 本地 pin 消费仓（RULES_ROOT 落本地冻结规则集）经 `sdflow-init update` 刷新 `openspec/workflow/tools/`（含新版 `anchor_lint.py` 需读机读块）
- **THEN** 同一 update SHALL 一并刷新 sibling `lens-metric-contract.md`（含 `lens-metric-enums` 块）——契约为 `tools/anchor_lint.py` 运行时机读依赖，MUST NOT 只刷脚本不刷契约而致 pin 仓「新脚本 + 旧契约无块」永久 fail-closed；常态 tools-only 非 pin 消费仓 RULES_ROOT 落 canonical 全树、契约恒有块、不受此约束

#### Scenario: 数值一致性诚实声明为信任边界

- **WHEN** 某 `sdflow:lens-metric` 锚的 `findings=N` 与该镜合并池实收数不符
- **THEN** 脚本 SHALL NOT 声称能检出该不一致（`findings=N` vs 实收数属主 session 信任边界、非机械可验）；SKILL 自检步 SHALL 保留「数值一致性是主 session 职责、脚本不谎称机验」的诚实声明，MUST NOT 因接了脚本而删除该边界声明
