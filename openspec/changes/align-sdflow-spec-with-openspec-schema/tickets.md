---
impl-pipeline: tickets
---

## Global Constraints

- **MUST NOT 用 `schema init`**——其产物 `instruction` 为空。
- `artifacts[].id` **MUST ∈ {`proposal`,`specs`,`design`,`tasks`}，不增不改**。
- `artifacts[].generates` **MUST 与内置一致**（`proposal.md` / `specs/**/*.md` / `design.md` / `tasks.md`）。
- **两条 `requires` 边都要改**：`specs` → `[proposal, design]`、`tasks` → `[proposal, design, specs]`。
- fork schema 是**跨项目共享的契约定义**；**权威源唯一** = `sdflow-init/assets/schemas/`；下游副本**只读**，改动一律回灌权威源再下发；下游手改会被整删重拷覆盖。
- 补写在途 change 的 schema 前，**MUST 先检查 `proposal.md` 存在**；非 change 目录跳过，归档 change 不扫描。
- **固化顺序「先补写、后切 config」**；任一 change 补写失败 **SHALL 中止整个 run**，不得继续到 config 切换。
- schema 目录下发 **MUST 采用 rmtree-first 整删重拷**，不得使用合并式拷贝。
- 相位 C 的委派剥离 **MUST 置于应用载荷作为生成约束之前**；只做定界字符串切分，**MUST NOT 解析 Markdown 结构**。
- 标记未出现时剥离步 **MUST no-op 不报错**；标记不成对时 **MUST fail-closed**，报告 problem+cause+fix。
- `resolvedOutputPath` 为 glob 时 **MUST** 按 `instruction` 推导具体目标路径，并对推导出的具体路径执行路径净化；**MUST NOT** 对 glob 字面量放行。
- `skipped` 产物 **MUST 跳过且 MUST NOT 创建文件**；依赖它的阅读清单条目相应去掉。
- 强制阅读清单以 schema 的 `requires` 为准；图不足时 **MUST 保留写死超集 fallback**。
- **不解析 `schema.yaml` 语义**；fork 与校验一律调 CLI 让 CLI 自己回答；剥离只做有界的定界标记字符串切分。
- `skip_specs`「够不够格」是语义残余，**MUST NOT** 伪装成机械门。
- 下游副本**只读**，改动一律回灌权威源再下发；本 change **不**为 schema 引入独立于 bundle 的第二条分发路径。

### Task 1: 建立可验证的 project-local schema 契约

**Blocked-by:** none
**R-ID:** SW-SCHEMA

系统拥有一个由内置 schema fork 出来的 project-local schema，四个 artifact 的标识和输出模式保持兼容，同时携带阶段一委派提示；其依赖图使 `specs` 读取 proposal/design、`tasks` 读取 proposal/design/specs，design 产物为无条件产物。

- [x] schema 由 `schema fork` 产出而非 `schema init` 产出
- [x] 四个 artifact 的 `id` 与 `generates` 和内置契约逐字一致
- [x] 四个 artifact 的委派标记成对，文案要求停止并提示人敲 `/sdflow-spec`
- [x] `specs` 与 `tasks` 的 `requires` 边符合目标依赖图，design instruction 无条件生成
- [x] CLI schema validate 通过

### Task 2: 让初始化与更新安全下发并迁移 schema

**Blocked-by:** 1
**R-ID:** SW-SCHEMA

消费仓在 CLI 版本满足门槛时能获得并启用 project-local schema；版本不足、命令缺失或输出异常时保持内置 schema 并明确报告原因。更新时，在途 change 先获得正确的 schema 绑定，再切换配置；下发采用整删重拷，且已有配置只改 schema 单键。

- [x] CLI 版本按 semver 数值元组判断，`<1.7.0`、命令缺失和非数字输出均 fail-closed 并输出一行结论
- [x] 仅扫描含 `proposal.md` 的在途 change；缺绑定者被补写，已有绑定者 no-op，归档和 stray 目录不受影响
- [x] 任一补写失败会中止本次运行，配置不会切换；顺序有测试证据
- [x] schema bundle 采用 rmtree-first 整删重拷，权威源删除的文件不会残留在消费仓
- [x] 配置模板与消费仓配置在版本门通过时指向 fork schema，update 模式只改 schema 行且其余内容保持 byte-identical
- [x] 版本门与迁移补写结论进入既有动作汇总

### Task 3: 使阶段一相位 C 消费真实 CLI 载荷

**Blocked-by:** 1
**R-ID:** SA-05, SA-17

阶段一相位 C 能消费 project-local schema 返回的 instruction/requires 载荷：先剥离只供官方入口阅读的委派段，再按真实依赖图阅读和生成；能处理 glob 输出目标、既有输出路径、skipped 产物和对象列表形式的 dependencies，同时保留 schema 不足时的 fallback。

- [x] 委派标记成对时在应用载荷前剥离；无标记 no-op；不成对时 fail-closed 并报告 problem、cause、fix
- [x] glob 输出目标被依据 instruction 推导为具体 capability spec 路径，既有文件改写使用 existingOutputPaths
- [x] 路径净化作用于推导出的具体路径，不会把 glob 字面量当作合法目标
- [x] `skipped` 产物不创建文件，且依赖它的阅读清单条目被移除
- [x] 阅读清单以 schema requires 为准，并在依赖图不足时使用写死超集 fallback
- [x] dependencies 断言接受且验证包含 `id`、`done`、`path`、`description` 的对象列表
- [x] 终审 design↔specs 双向核被表述为 schema 已切换时的兜底，而非唯一防线

### Task 4: 完成本仓 dogfood 切换的零回归验证

**Blocked-by:** 2, 3
**R-ID:** SW-SCHEMA, SA-05, SA-17

本仓切换到 project-local schema 后，在途 change 的 artifact 状态保持不变；一次性新 change 能证明 CLI 返回的新依赖图被相位 C 正确消费，验证用 change 不进入最终工作树。

- [x] 切换前为全部在途 change 保存 `openspec status --json` 快照
- [x] 运行初始化/更新流程后，schema bundle 与 config 已切换到目标状态
- [x] 切换后逐 artifact 对比 status 快照，状态完全一致
- [x] 一次性 change 验证 `specs` 含 design、`tasks` 含 proposal 的 dependencies，验证完删除
- [x] 验证结果记录了 CLI 实际输出，不以静态解析配置文件替代

### Task 5: 建立回归测试与安装刷新门

**Blocked-by:** 2, 3
**R-ID:** SA-05, SA-17, SW-SCHEMA

版本门、迁移顺序、整删重拷、schema 内容契约、配置窄 patch 与相位 C 载荷契约均有反恒真回归覆盖；权威 bundle 变更后完成一次安装刷新并通过全仓测试。

- [ ] 版本门覆盖 `<1.7.0`、`1.10.0`、命令缺失和非数字输出
- [ ] 迁移覆盖缺绑定补写、已有绑定 no-op、archive/stray 跳过、单项失败阻止 config 切换
- [ ] copy bundle 覆盖权威源删除文件后的孤儿清理
- [ ] schema 内容覆盖 id/generates、委派标记和两条 requires 边
- [ ] update 模式 schema 单键改写覆盖且其余 config 内容 byte-identical
- [ ] 每条新增测试均先通过定点破坏验证非恒真
- [ ] 完成安装刷新后全仓 `pytest` 通过

### Task 6: 同步文档与已知边界

**Blocked-by:** 4, 5
**R-ID:** SA-05, SA-17, SW-SCHEMA

仓库使用说明和路线图反映 project-local schema 的最终流程，明确委派只有提示层效果；已知的 fork 漂移缺口被记录为后续事项，未把本 change 扩展到 roadmap 的 P2/P3。

- [ ] 阶段一入口文档说明 project-local schema 与提示层边界
- [ ] roadmap P1 标记为已交付
- [ ] fork 漂移无机械门记录到 todolist，且本 change 不实现该能力
- [ ] 文档中的 schema、委派、fallback 和迁移顺序与前述 ticket 语义一致

### Task 7: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1, 2, 3, 4, 5, 6
**R-ID:** all

按聚合套件发现契约运行本 change 的单元、集成和 e2e 测试套件并全部通过；证据落在实现验证报告中，每层记录命令、退出码和同一最终 SHA，缺失层记录未覆盖及判定依据。

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过，或记录未覆盖及判定依据
- [ ] e2e 测试证据齐全并通过，或记录未覆盖及判定依据
