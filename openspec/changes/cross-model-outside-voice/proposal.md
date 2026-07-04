# Proposal: cross-model-outside-voice（Phase C）

## Why

评审的「独立视角」目前只到 fresh-context 同模型子代理——盲区同处，非重叠捕获有限；执行机队已锚定为 opus/sonnet/gpt-5.5 多家族混编（`adr/0006`），跨模型 outside voice 从锦上添花升为弱模型兜底机制，且混编机队下天然可得。同时 T25 实证了广审层的地基问题：sdflow-spec-review / sdflow-code-review 的 Step1 把 autoplan / gstack review 下放为「子代理读 SKILL.md 模拟执行」，两轮真实运行均自报偏离，且呈现方式把模拟当原生（违反反静默守卫精神）——而本 change 的 C2「复用 autoplan 产物」成立的前提恰是该产物为真，故 T25 是前置而非搭车。

## What Changes

- **新增共享 codex helper**（自包含重写，不引用 gstack 内部；源 = `sdflow-init/assets/hack/`，setup.sh 装到 `~/.sdflow/hack/`）：preflight 浅探针（二态 not_installed / ready，〔grill-amendment Q2/Q3〕）+ exec 包装（5min 超时）+「找漏」与文件系统边界 prompt 框架〔C1/C6〕。归档设计中的 off-switch 已裁——启停由环境层（装/不装 codex）决定，工作流层不设软开关〔grill-amendment Q3〕。
- **fallback 到原生 Task 子代理**：非 ready / 报错 / 超时 → 同 prompt 派 fresh Claude 子代理，非阻塞，审查永不因此中断〔C6〕。
- **sdflow-spec-review 接入**〔C2/C7〕：复用 autoplan 产出的 `gstack-review.md` 里的 codex outside-voice findings + 反静默守卫（缺失 / 解析不出 / 0 条 → 显式降级日志 + 回落自跑 codex 设计 voice）+ 命中 HR-TG 单开领域 cross-model。
- **sdflow-code-review 接入**〔C3〕：自带 code outside voice（always，无前置层零重叠）+ 命中 HR-TG 单开领域 cross-model。
- **HR-TG 判定**〔C4〕：两 skill 的规划镜头步顺带判 命中集 ∩ {TG-04/06/07/08/09/16/17/26} ≠ ∅，报告留痕，零新机制。
- **tension 适配**〔C5〕：spec-review → 报告决策登记区；code-review → 有把握自动裁决（记理由）/ 拿不准 defer；共守 user sovereignty（绝不静默自动采纳）。
- **trigger-catalog.md（bundle 权威源）新增 TG-26 并发/共享可变状态**（回填四列 + 各消费方引用 + `openspec/INDEX.md` TG 计数同步）〔C4/§7.5〕。
- **T25 前置修复**：Step1 广审改为主 session 经 Skill 机制**原生执行** autoplan / gstack review（方向已拍板，用户 2026-07-03；sdflow-ship 评审轮已有原生执行先例）；模拟仅作 fallback 且必须显式标注「模拟广审（降级模式）」。
- **gstack 边界守恒**〔C7〕：不动 autoplan / gstack review 原生 outside voice；自制机制只驱动自制 skill；读产出物 ✓、依赖内部实现 ✗。

## Capabilities

### New Capabilities

（无——本仓 capability 单一为 `spec-workflow`，本次全部为其行为增量）

### Modified Capabilities

- `spec-workflow`：新增 Requirement——①跨模型 outside voice 默认开、失败 fallback 且非阻塞（启停由环境层决定，无软开关）[gstack-amendment]〔C1/C6/C7〕；②高风险由 HR-TG 子集判定并留痕〔C4〕；③outside-voice 复用的反静默守卫（缺失/0 条 → 显式降级 + 回落自跑）〔C2·grill-amendment〕；④Step1 广审层原生执行或显式标注降级（T25，取代「模拟当原生」现状）。

## Impact

- **改**：`sdflow-spec-review/SKILL.md`（Step1 原生执行 + outside-voice 复用/回落 + 规划镜头 HR-TG 判定）、`sdflow-code-review/SKILL.md`（Step1 原生执行 + 新 code outside-voice 子步 + HR-TG 判定）。
- **新**：`sdflow-init/assets/hack/` 下 codex helper 脚本（含 pytest/bats 测试）；改后须重跑 `setup.sh`（copy 非 symlink）。
- **改（bundle 权威源）**：`sdflow-init/assets/workflow/trigger-catalog.md`（TG-26 四列）；经 `sdflow-init update` 推下游消费仓；本仓 `openspec/INDEX.md` TG 计数同步（toolkit 源仓适用）。
- **外部依赖**：codex CLI（OpenAI 计费，见成本估算）；gstack 仅作产物读取方（`gstack-review.md`），零内部依赖。
- **技术栈触发**：不命中 TG-01/02/03（Markdown + Bash/Python skills 仓），无领域清单，评审过 base 清单。

## Success Metrics

1. **outside-voice 层留痕覆盖率** — 基准 0%（现无此层）→ 目标 100%：每次 sdflow-code-review 报告含 outside-voice 段（真跑 codex 或显式降级记录，二者必居其一）— 度量：grep 机器锚行 `<!-- outside-voice: … -->`〔grill Q5：确定性机判，不押自然语言〕。
2. **广审层静默模拟次数** — 基准：模拟未标注（T25 两轮实证）→ 目标 0：Step1 每次运行要么原生执行、要么显式标注「模拟广审（降级模式）」— 度量：grep 机器锚行 `<!-- step1-broad-review: … -->`〔grill Q5〕。
3. **无 codex 环境评审完成率** — 基准 N/A → 目标 100%：无 codex / 无 gstack 环境下 fallback 冒烟通过、审查不中断 — 度量：§8.3 冒烟测试。

## 需求优先级（TG-19）

- **P0**：codex helper + fallback〔C1/C6〕；spec-review 复用 + 反静默回落〔C2〕；code-review 自带 code voice〔C3〕；T25 Step1 原生执行。
- **P1**：HR-TG 判定 + 报告留痕〔C4〕；TG-26 入 catalog + INDEX 同步〔§7.5〕；tension 适配〔C5〕。
- **P2**：gstack 边界核验冒烟〔§8.4，C7 本身是贯穿 P0 的约束〕；gstack headless 路径调研（T25 思路②，补充项）。

## 假设列表（TG-22）

| 假设 | 失效影响 |
|------|---------|
| codex CLI 已安装且可认证 | fallback 到 Claude 子代理——只丢跨模型增益，层不丢，非阻塞 |
| `gstack-review.md` 文件名 / codex 段格式稳定 | 反静默守卫触发：显式降级 + 回落自跑 codex 设计 voice，绝不静默当「本次无 voice」 |
| autoplan 每次都跑（P2b）→ `gstack-review.md` 每次都在 | C2 复用失去前提：spec-review MUST 自跑设计 outside voice（守卫 fallback 路径），C2 与 P2b 两条 MUST 交叉引用 |
| Skill 机制可在主 session 原生执行 autoplan（sdflow-ship 评审轮先例） | 退 T25 思路③：显式标注「模拟广审（降级模式）」，不伪装原生 |

## 开放问题（TG-21）

| 问题 | 归属 | 截止 |
|------|------|------|
| ~~off-switch 形态~~ | 已闭〔grill Q3〕：不设 off-switch，启停归环境层 | — |
| helper 语言形态：bash 单脚本 vs Python（本仓测试惯例 pytest） | design.md 决策记录 | 设计门前 |
| gstack headless 调用路径是否存在、可否作原生执行的补充 | 实现期调研（P2） | 不阻塞 P0 |

## 成本估算（TG-24）

- codex exec 每次评审 0–4 调用：code-review 1（always code voice）+ 0–1（HR-TG 领域）；spec-review 0–1（仅守卫回落时）+ 0–1（HR-TG 领域）。单次 5min 封顶。
- 计费走用户 codex CLI 认证的 OpenAI 订阅/额度；按 review 输入以 diff + prompt 模板（~KB 级）计，每 change 量级为个位数调用，边际成本可忽略；不装 codex 的环境天然归零（无软开关，〔grill Q3〕）。

## Non-Goals

- **不改 gstack / superpowers 任何内部**（autoplan、gstack /review 的原生 outside voice 原样不动）——可证伪：`git diff` 不含任何 gstack 安装目录/内部文件；§8.4 冒烟核验其原生机制未被触碰。
- **不做「codex 占对抗镜 slot」**——已在归档 design §9.1 作废：outside voice 是不受清单约束的整体找漏，塞进镜位收益反降；可证伪：SKILL.md 镜位表不出现 codex 镜。
- **不新造风险分级体系**——HR-TG 只是 TG 具名子集；可证伪：全仓 grep 无新风险代号（R1~R6 之外的新码）。
- **不含 T26**（sdflow-ship 熔断计数脚本化）——与 outside voice 无耦合，留 sdflow-ship 批次；可证伪：本 change 不触碰 `sdflow-ship/SKILL.md`。
- **不含 setup.sh 所有权加固批次**（T24+T14+T16+T18+T23）——另开小 change（2026-07-04 explore 拍板拆分）；可证伪：本 change 对 `setup.sh` 的改动仅限安装新 helper 所需（如有）。

## Compliance（合规声明）

- `adr/0006`(b) prose 协议脚本化硬约束：preflight/exec/超时/降级链全部落 helper 脚本，SKILL.md 只剩「跑脚本、按输出分支」——遵守。
- C7 gstack 边界（归档 design §9.0 + grill-amendment「读产出物 ✓ 依赖内部 ✗」）——遵守。
- bundle 权威源纪律（trigger-catalog 改 `sdflow-init/assets/workflow/`，非下游副本）——遵守。
- 其余（数据模型跨产品边界 D-6 窄条款、DB 迁移 D-2）：不适用（N/A）。
