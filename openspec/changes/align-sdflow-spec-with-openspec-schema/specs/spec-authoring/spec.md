## MODIFIED Requirements

### Requirement: SA-05 生成经 openspec CLI；完成态与合格态分开判定

**相位 B 起手 SHALL 按序执行三步（前移，非在收敛点）** [窄复核 F-12：原设计把这三步排在 B 收敛点，导致 B 进行中无 change 目录、SA-04 的增量落盘无处可写]：

1. **工作树前置检查**：`git status --porcelain`。若含与本 change 无关的条目 → **halt 并向用户说明**（stash / 先提交 / 确认带过来三选一），MUST NOT 静默继续。理由：FF-0 的 `git checkout -b` 会把脏改动带上新分支，而 `checkpoint-commit.sh` 的无条件 `git add -A` 会将其全部提交——该失效模式本仓已真实发生过。
2. **FF-0 三分支判定**：在保护分支（main/master）→ `git checkout -b feat/{change}`；已在 `feat/{本 change}` → 跳过（真幂等）；**在其它 feature 分支 → halt 问人**（从当前切出 / 回 base 切出 / 就地继续）。MUST NOT 沿用「已在 feature 分支就跳过」的弱判据——那会让第二个 change 落在前一个 change 的分支上。`git checkout -b` 失败（分支已存在）SHALL fallback 到 `git checkout feat/{change}`，否则如实报告。
3. `openspec new change`。change 名此时即可定——SA-03 的相位 A 收束禁止清单已含「目标态一句话尚写不出」，故进入相位 B 时目标态必然已明确。**MUST NOT 使用暂定名后改名**：openspec CLI 无 rename change 命令，手工 `git mv` + 改 `.openspec.yaml` 即手搓 change 目录结构（本 requirement 下方明令禁止）。

**相位 B 收敛点 SHALL 执行**：

4. 决策纪要定稿（补齐身份字段）。
5. checkpoint 提交。

**相位 C SHALL**：起手核验 `decision-memo.md` 存在、必填字段非空**且身份字段匹配当前 change/branch**；按**强制阅读清单**串行生成产物；每个生成步 SHALL 自行调用 `openspec instructions <artifact> --change <name> --json` 获取载荷（MUST NOT 由主 session 转述），并对返回载荷做**最小 schema 断言**（必需字段存在性 + 类型），不兼容即 fail-closed 并报告实际 CLI 版本。

**最小 schema 断言的字段形状 SHALL 锚 CLI 实际返回值**：`artifactId` / `instruction` / `template` / `resolvedOutputPath` 为字符串，`dependencies` 为**对象列表**（每项含 `id` / `done` / `path` / `description`），MUST NOT 断言为字符串列表。`context`（字符串）/ `rules`（列表）若存在 SHALL 作为生成约束应用、MUST NOT 复制进产物。

**强制阅读清单 SHALL 以 schema 声明的依赖图为准，并对图不足时 fallback 到写死超集**：

- 当 `instructions --json` 返回的 `dependencies` **已覆盖**下述清单时，按 CLI 依赖图走即可；
- 当**不覆盖**时（例如运行在内置 `spec-driven` 上，其 `design`/`specs` 的 `dependencies` 都只有 `[proposal]`、`tasks` 的只有 `[specs, design]` 而不含 `proposal`），生成步 SHALL 按下述**写死超集**读取，MUST NOT 因「CLI 没要求」而跳过：design 读 proposal；specs 读 proposal **+ design**；tasks 读 proposal + design + specs。

理由：若照字面按不足的 CLI 依赖图走，specs 生成步不会读 design.md，而 design↔specs 矛盾没有任何其它环节会发现。fallback 分支 SHALL 保留——它是 schema 未切换、或未来 schema 回退时的正确性底座。

**完成态与合格态 SHALL 分开判定** [spec-review-amendment]：
- **完成态**（产物是否已产出、下一个 ready 是哪个）问 `openspec status --json`；
- **合格态**（产物是否结构合法）问 `openspec validate <change> --strict`；
- MUST NOT 手搓 Markdown 解析器判断任一者。

理由：CLI 源码实证（`dist/core/artifact-graph/state.js:25-29`）`status` 的完成判据是**文件存在性** ⇒ 一份被截断的产物会被判 `done`，叠加「不重写已完成产物」后**永久锁死**。

产物写入 SHALL 用临时文件 + 原子替换。写入目标路径 SHALL 经 canonicalization 后校验严格位于 `openspec/changes/<name>/` 内、匹配预期 artifact allowlist、拒绝 symlink 逃逸（`resolvedOutputPath` 来自第三方 CLI，直接当写入目标构成 confused deputy）。

openspec CLI 不可用、报错或 schema 不兼容 SHALL fail-closed 中止并报告，MUST NOT 手工创建 change 目录结构。`new change` 非零退出后 SHALL 检查 `.openspec.yaml`/status/新建路径并**精确报告 partial state**，MUST NOT 假定其原子性。

#### Scenario: 工作树不洁时停下
- **WHEN** 用户触发 `/sdflow-spec` 时工作树有与本 change 无关的未提交改动，管线走到相位 B 起手
- **THEN** 管线 halt 并说明检测到的条目，等用户选择处置；MUST NOT 执行 `checkout -b` 与 `git add -A`

#### Scenario: 在其它 feature 分支上开新 change
- **WHEN** 用户当前在 `feat/change-A`（A 未 merge），相位 B 起手要为 change-B 建分支
- **THEN** 管线 halt 问人，MUST NOT 因「已在 feature 分支」而跳过建分支

#### Scenario: 生成步自取载荷并断言 schema
- **WHEN** 生成 tasks.md
- **THEN** 生成方自己执行 `openspec instructions tasks --change <name> --json`、对载荷做最小 schema 断言（含 `dependencies` 为对象列表），并按强制阅读清单读取 proposal + design + specs 全文

#### Scenario: schema 依赖图不足时 fallback 到写死超集
- **WHEN** 相位 C 运行在内置 `spec-driven` 上生成 specs，`instructions specs --json` 返回的 `dependencies` 只有 `[proposal]`
- **THEN** 生成步判定该图**不覆盖**清单，按写死超集额外全文读取 `design.md` 后再生成；MUST NOT 因 CLI 未声明该依赖而跳过 design

#### Scenario: schema 依赖图已覆盖时按图走
- **WHEN** 相位 C 运行在已切换的 project-local schema 上生成 tasks，`dependencies` 返回 `[proposal, design, specs]`
- **THEN** 该图已覆盖清单，生成步按图读取三份依赖，无需再走 fallback 分支

#### Scenario: 半截产物不被判完成
- **WHEN** 生成 delta spec（`specs/<capability>/spec.md`）时命中输出上限，文件落盘但内容中途截断
- **THEN** `status` 报 done 但 `validate --strict` 不过 ⇒ 判该产物未完成，进重试/亲写阶梯；MUST NOT 因「文件存在」跳过
- **注**：`openspec validate <change> --strict`（CLI 1.5.0 实证：`dist/core/validation/validator.js` 只含 `validateChangeDeltaSpecs`，全文无 `design`/`proposal` 字样）**只覆盖 delta spec**，对 proposal.md/design.md/tasks.md 是恒假的机械门——这三份的「未截断」无机械门，由终审人判（SA-06 终审兜底；降级阶梯见 `sdflow-spec/references/degradation-ladder.md` §5）。

#### Scenario: CLI 缺失 fail-closed
- **WHEN** `openspec` 命令不存在、`new change` 失败、或 `instructions --json` 载荷 schema 断言不通过
- **THEN** 管线中止并向人报错（含实际版本 + 修复命令）；不产生任何手搓的 change 目录

## ADDED Requirements

### Requirement: SA-17 载荷的委派区块剥离、glob 写入目标与 skipped 态处置

相位 C 消费 `openspec instructions` 载荷时，SHALL 按下述三条处置 CLI 1.7.0 起的载荷形态。三条均为**确定性操作**，MUST NOT 退化为模型自由裁量。

**（a）委派区块剥离**：`instruction` 中以 `<!-- sdflow:delegation:start -->` 与 `<!-- sdflow:delegation:end -->` 成对包裹的区块，SHALL 在**应用载荷作为生成约束之前**整段剥离。该区块的受众是官方入口（`/opsx:ff` / `/opsx:propose` / `/opsx:continue`），其内容是「停止并提示人敲 `/sdflow-spec`」——相位 C 自己就是 `/sdflow-spec`，不剥离即自我劝退。剥离 SHALL 只做定界标记的字符串切分，MUST NOT 解析 `instruction` 的 Markdown 结构。标记**未出现**（如运行在内置 schema 上）SHALL 视为正常、不报错；标记**不成对**（只有 start 或只有 end）SHALL fail-closed 中止并报 problem + cause + fix，MUST NOT 带着未剥离的载荷继续生成。

**（b）glob 写入目标**：`resolvedOutputPath` 对 glob 型 artifact（如 `specs`，其值形如 `<change 目录>/specs/**/*.md`）返回的是**字面 glob 模式，不是文件路径**。生成步 SHALL 按 `instruction` 的指引推导具体文件路径（每个 capability 一个 `specs/<capability>/spec.md`），MUST NOT 把 glob 字面量当写入目标。改写既有文件时，目标 SHALL 取 `openspec status --json` 的 `artifactPaths.<id>.existingOutputPaths`（CLI 已 glob 展开），MUST NOT 自行遍历文件系统推测。路径净化（严格位于 change 目录内、匹配 artifact allowlist、拒绝 symlink 逃逸）SHALL 对推导出的具体路径执行。

**（c）`skipped` 态**：当 `openspec status --json` 报某 artifact 的 `status` 为 `"skipped"`（change 的 `.openspec.yaml` 声明了 `skip_specs: true`），相位 C SHALL 跳过该产物且 **MUST NOT 创建任何对应文件**——CLI 规定此时其文件必须不存在，创建会使 `validate` 因「marker 与 delta 同时存在」报错。强制阅读清单中依赖该产物的条目相应去掉。**「这个 change 够不够格声明 `skip_specs`」是相位 B 的人机拍板事项、SHALL 落进 `decision-memo.md`**；相位 C **只认 CLI 自报的 `status`**，MUST NOT 自行判定某个 change 是否应当 skip。

#### Scenario: 委派区块被剥离后不自我劝退
- **WHEN** 相位 C 在已切换 project-local schema 的仓内生成 proposal，载荷 `instruction` 以 `<!-- sdflow:delegation:start -->` 开头、内含「MUST NOT 自己写、请提示用户敲 /sdflow-spec」
- **THEN** 生成步先整段剥离该区块，再把剩余原文作为生成约束应用，正常产出 `proposal.md`；MUST NOT 因读到该文案而停止生成或提示用户改敲命令

#### Scenario: 委派标记不成对时 fail-closed
- **WHEN** 载荷 `instruction` 只含 `<!-- sdflow:delegation:start -->` 而无对应 end 标记
- **THEN** 生成步中止并报 problem + cause + fix，MUST NOT 猜测剥离范围、MUST NOT 带着未剥离载荷继续

#### Scenario: 内置 schema 下无标记不报错
- **WHEN** 相位 C 运行在内置 `spec-driven` 上，载荷 `instruction` 不含任何 `sdflow:delegation` 标记
- **THEN** 剥离步 no-op，生成正常进行，不产生告警

#### Scenario: glob artifact 不把模式当路径
- **WHEN** 生成 specs，`instructions specs --json` 返回 `resolvedOutputPath` 为 `<change 目录>/specs/**/*.md`
- **THEN** 生成步按 proposal 的 Capabilities 逐个推导 `specs/<capability>/spec.md` 并对每个具体路径做路径净化后写入；MUST NOT 创建名称含 `*` 的文件

#### Scenario: skipped 态不创建文件
- **WHEN** change 的 `.openspec.yaml` 声明 `skip_specs: true`，`status --json` 报 `specs` 的 `status` 为 `"skipped"`
- **THEN** 相位 C 跳过 specs 产物、不创建 `specs/` 下任何文件，且 tasks 的强制阅读清单不再要求读 specs；`validate --strict` 通过
