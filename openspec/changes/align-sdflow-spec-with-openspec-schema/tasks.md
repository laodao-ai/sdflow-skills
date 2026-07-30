# Tasks · align-sdflow-spec-with-openspec-schema

> Requirement ID 对照：**SA-05** = `spec-authoring` 的「SA-05 生成经 openspec CLI；完成态与合格态分开判定」（MODIFIED）·
> **SA-17** = `spec-authoring` 的「SA-17 载荷的委派区块剥离、glob 写入目标与 skipped 态处置」（ADDED）·
> **SW-SCHEMA** = `spec-workflow` 的「project-local schema 随 bundle 下发，受 CLI 版本门与迁移前置约束」（ADDED）。
>
> 优先级承 `proposal.md`：**P0** 不做则有害 · **P1** 核心价值 · **P2** 清理。

## 1. fork schema 产出（bundle 权威源）〔SW-SCHEMA〕

- [ ] 1.1 **P1** 在 `sdflow-init/assets/schemas/` 下用 `openspec schema fork spec-driven sdflow-spec-driven` 产出 schema（**MUST NOT 用 `schema init`**——其产物 `instruction` 为空）
- [ ] 1.2 **P1** 在四个 artifact 的 `instruction` 前置委派区块：`<!-- sdflow:delegation:start -->` … `<!-- sdflow:delegation:end -->`，文案 = 停止 + 提示人敲 `/sdflow-spec`（模型唤不起它，见 ADR-0034）
- [ ] 1.3 **P1** 改 `requires` 边：`specs` → `[proposal, design]`、`tasks` → `[proposal, design, specs]`（**两条都要改**，只改 specs 则「tasks 读 proposal」仍需超集）
- [ ] 1.4 **P1** 把 `design` 的 `instruction` 改为无条件产物（去掉 "create only if any apply" 条件语），与 `specs.requires` 含 design 自洽
- [ ] 1.5 **P0** 核验 `id` 与 `generates` 四项均与内置逐字一致（相位 C 路径净化 allowlist 为硬编码字面量）
- [ ] 1.6 **P1** `openspec schema validate sdflow-spec-driven` 通过

## 2. sdflow-init：版本门、迁移补写、下发〔SW-SCHEMA〕

- [ ] 2.1 **P0** 加 CLI 版本门：`openspec --version` < 1.7.0 ⇒ 不铺 schema、`config.yaml` 的 `schema:` 保持内置值、fail-loud 输出一行原因
- [ ] 2.2 **P0** 加迁移补写：扫 `openspec/changes/*/`（**仅在途，不扫 `changes/archive/`**），缺 `.openspec.yaml` 者补写当前实际 schema 名；幂等
- [ ] 2.3 **P0** 固化顺序「先补写、后切 config」，并在代码注释写明颠倒的后果（补写方会读到新 schema 名）
- [ ] 2.4 **P1** schema 目录纳入 `copy_bundle`，采用与 `tools/` 同构的**整删重拷**收敛语义
- [ ] 2.5 **P1** `sdflow-init/assets/workflow/config.template.yaml` 的 `schema:` 指向 `sdflow-spec-driven`
- [ ] 2.6 **P1** 版本门与迁移补写各输出一行结论，进入既有动作汇总

## 3. sdflow-spec 相位 C 对齐〔SA-05 · SA-17〕

- [ ] 3.1 **P0** C.3 增委派区块剥离步，置于「应用载荷作为生成约束」**之前**；只做定界字符串切分，MUST NOT 解析 Markdown 结构〔SA-17(a)〕
- [ ] 3.2 **P0** 剥离步的两个边界：标记未出现 ⇒ no-op 不报错；标记不成对 ⇒ fail-closed 报 problem+cause+fix〔SA-17(a)〕
- [ ] 3.3 **P0** C.3 增 glob 分支：`resolvedOutputPath` 为 glob 时按 `instruction` 推导 `specs/<capability>/spec.md`；改写既有文件时取 `artifactPaths.<id>.existingOutputPaths`〔SA-17(b)〕
- [ ] 3.4 **P0** 路径净化改为对**推导出的具体路径**执行（当前是对 `resolvedOutputPath` 执行，glob 字面量会被 allowlist 放行）〔SA-17(b)〕
- [ ] 3.5 **P1** C.2/C.3 增 `skipped` 态处置：跳过该产物且 MUST NOT 创建文件；依赖它的阅读清单条目相应去掉〔SA-17(c)〕
- [ ] 3.6 **P1** C.2 强制阅读清单改为「以 schema 的 `requires` 为准 + 图不足时 fallback 写死超集」，**保留 fallback 分支**（内置 schema 与未来回退的正确性底座）〔SA-05〕
- [ ] 3.7 **P2** C.3 最小 schema 断言把 `dependencies` 收紧为对象列表（含 `id`/`done`/`path`/`description`）〔SA-05〕
- [ ] 3.8 **P2** 终审第 2 条（design↔specs 双向核）措辞由「唯一防线」降为「兜底」，并说明降级前提是 schema 已切换〔SA-05〕

## 4. 本仓 dogfood 切换与迁移验证〔SW-SCHEMA〕

- [ ] 4.1 **P0** 切换**前**对本仓全部在途 change 跑 `openspec status --json` 存快照
- [ ] 4.2 **P1** 跑 `sdflow-init`（本仓）铺 schema + 切 `openspec/config.yaml` 的 `schema:`
- [ ] 4.3 **P0** 切换**后**重跑 status 并与 4.1 快照逐 artifact 比对，**状态必须一致**（迁移零回归）
- [ ] 4.4 **P1** 新建一个一次性 change 验证 `instructions <artifact> --json` 的 `dependencies` 已反映新依赖图（`specs` 含 `design`、`tasks` 含 `proposal`），验完删除

## 5. 测试〔SA-05 · SA-17 · SW-SCHEMA〕

- [ ] 5.1 **P0** `sdflow-init/tests/` 加版本门用例：<1.7.0 不铺 + 报一行 + config 未被改写
- [ ] 5.2 **P0** 加迁移补写用例：缺 `.openspec.yaml` 的在途 change 被补写；已有者 no-op；`changes/archive/` 不被触碰
- [ ] 5.3 **P0** 加**顺序**用例：断言补写发生在 config 改写之前（顺序颠倒即红）
- [ ] 5.4 **P1** 加 `copy_bundle` 整删重拷用例：权威源删文件后消费仓不残留孤儿
- [ ] 5.5 **P1** schema 内容契约用例：四个 `id` 与 `generates` 与内置一致；委派标记成对；`requires` 两条边符合 1.3
- [ ] 5.6 **P0** 每条新增用例先跑「定点破坏 → 必须红」验证非恒真（承本仓既有反恒真锚纪律）
- [ ] 5.7 **P0** 全仓 `pytest` 绿

## 6. 文档与收尾

- [ ] 6.1 **P1** `CLAUDE.md` 阶段一入口段落同步：说明产 spec 走 project-local schema，且委派是**提示层**不是机械保证
- [ ] 6.2 **P1** roadmap `openspec/roadmaps/openspec-1.7.0-followup/roadmap.md` 的 P1 标记为已交付
- [ ] 6.3 **P2** 把「fork 漂移无机械门」记进 todolist（本次不解决，见 ADR-0034 Consequences）
- [ ] 6.4 **P0** 改 `sdflow-init/assets/` 下内容后**重跑一次安装**（hook/bundle 为 copy 安装，非 symlink），否则测的是旧版

## 测试覆盖图〔TG-18〕

```
code path                                          测试类型            用例锚
──────────────────────────────────────────────────────────────────────────────
init.py · 版本门分支（<1.7.0 / ≥1.7.0）           单元(pytest)        5.1
init.py · 迁移补写（缺→补 / 有→跳 / archive 不扫） 单元(pytest)        5.2
init.py · 补写与切 config 的先后顺序               单元(顺序断言)      5.3
init.py · copy_bundle 整删重拷收敛                 单元(pytest)        5.4
assets/schemas/ · schema 内容契约                  契约测试            5.5
assets/schemas/ · schema 结构合法性                CLI 判定            1.6（schema validate）
sdflow-spec SKILL.md · 剥离/glob/skipped           指令层，无自动化    4.4 + 一次完整走通产四件套
本仓迁移 · 切换前后 status 一致                    端到端(人工比对)    4.1/4.3
全仓回归                                           pytest              5.7
```

🔴 **诚实边界**：第 3 组（相位 C 的剥离 / glob / skipped）是**指令层**改动，写在 `SKILL.md` 里由模型执行，**没有自动化测试面**——其验证只能靠 4.4 与「一次完整走通产四件套」的端到端观察。MUST NOT 在验收时把它算作有机械门守护。
