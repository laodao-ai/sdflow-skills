## Context

`sdflow-maintain` 现为纯 Markdown 编排类 skill（零脚本）。其 SKILL.md 步骤 1-3 用 prose 指令让模型手做三类确定性 set-diff：① specs/rules ↔ INDEX 表格行、② CLAUDE.md 过时引用、③ workflow bundle 陈旧遮蔽兜底扫描（判据清单：`openspec/workflow/` 下残留 `workflow.md` / `spec-checklists/` / `code-checklists/` 任一 + 仓根 `hack/checkpoint-commit.sh` 孤儿副本）。步骤 4（按报告修复 INDEX）、步骤 5（提示 retro）是判断/编排。

本 change 属 MLH roadmap 阶段4·4.B（design §143 P6 行），把机械的三类 set-diff 下沉为脚本，判断/编排保留。约束：MLH 全局红线（fail-closed + 可观测 + 坏输入非零退出 + MUST NOT 引入静默面，见 roadmap §决策5）；adr/0006 硬约束「凡机械 prose 协议 MUST 脚本化」。

现存耦合信号：todolist T17 已记「陈旧遮蔽判据两处（脚本常量 vs SKILL prose 复述）无同步机制，改常量会漂」——本 change 把判据落进脚本常量、SKILL prose 改为「见脚本」，顺带收敛为单一源。

## Goals / Non-Goals

**Goals:**
- 三类 set-diff 由 `maintain_scan.py` 确定性产出只读报告；SKILL 步骤 1-3 改为调脚本。
- 坏输入全 fail-closed（非零退出 + 响亮 stderr），pytest 有负例断言。
- `sdflow-maintain` 升数据类（首个 `scripts/`+`tests/`），对齐仓内既有数据类 skill 形态。
- 判据清单（陈旧遮蔽）收敛为脚本单一源（闭 T17 隐忧）。

**Non-Goals:**
- 脚本不自动改 INDEX/任何文件（修复留模型步骤 4）。
- 不下沉「新 spec 归哪主题分组」内容判断。
- 不动 4.D 组 / ◐ 组。

## Decisions

### D1 只读报告，不自动修复（判断留人）
脚本零写文件，只出结构化差异报告；SKILL 步骤 4 由模型按报告判断是否改 INDEX、新 spec 归哪组。**理由**：「是否修复 / 归哪组」是内容判断（§1.3 判断权留人/模型红线）；set-diff 本身才是确定性机械活。**备选**：脚本直接改 INDEX——否决，越权且把内容判断塞回脚本。

### D2 INDEX 表格解析 + 畸形 fail-closed
解析 `INDEX.md` markdown 表格行提取已列 spec/rule 名。**关键**：区分「INDEX 存在但表格畸形不可解析」与「INDEX 空」——前者 fail-closed 非零退出（绝不静默当作「空 INDEX → 全部新增」误判），后者是合法态（报全部为新增未索引）。**理由**：静默把畸形当空是典型静默面（§1.3 反静默红线）。

### D3 归组建议不下沉（定 Q1）
脚本只报「新增未索引」条目名 + 类型（spec/rule），**不**建议归入哪个 INDEX 主题分组。**理由**：归组是内容判断，留模型步骤 4。

### D4 陈旧遮蔽判据入脚本常量，收敛单一源（定 Q2 + 闭 T17）
判据清单落 `maintain_scan.py` 模块常量（`STALE_BUNDLE_MARKERS = [workflow.md, spec-checklists/, code-checklists/]` + `hack/checkpoint-commit.sh` 孤儿检查），SKILL.md 陈旧遮蔽扫描 prose 改为「判据见 `maintain_scan.py` 常量」不再复述清单。**理由**：现在两处复述（脚本待建 + SKILL prose）会漂（T17）；一处定义即单一源。**备选**：判据从更上层配置读——否决，过度设计，判据本就少且稳。

### D5 退出码语义（镜像 anchor_lint 口径）
`0` = 扫描完成（**含有差异**，差异是正常结果，不是错误）；`非0` = 坏输入/无法可靠完成（INDEX 缺失/畸形、目录缺失）。实现镜像 `anchor_lint.py`：typed error（如 `MaintainScanError`）→ `main(argv)` 捕获打 stderr → `sys.exit(非0)`；`sys.exit(main())`。**理由**：与仓内既有数据类脚本一致，降认知成本。**备选**：有差异也非零（类 lint 门禁）——否决，maintain 是「报告→人判修」不是门禁，有差异非零会误导编排。

### D6 maintain 数据类化骨架
新增 `sdflow-maintain/scripts/maintain_scan.py`（Python stdlib，无三方依赖）+ `sdflow-maintain/tests/test_maintain_scan.py`。skill 走 symlink，改源即时生效，`setup.sh` 逻辑不动（仅含 `SKILL.md` 目录才装的规则不变，本目录已有 SKILL.md）。

### 数据流（TG-11）

```
openspec/specs/*/spec.md ┐
openspec/rules/*.md      ┤
openspec/INDEX.md        ┼─► maintain_scan.py ─► 只读差异报告(4 类分节)
CLAUDE.md(根+子目录)     ┤    (纯读·fail-closed)      ├ 新增未索引
openspec/workflow/*      ┘                            ├ 已删未清理
                                                      ├ CLAUDE.md 过时引用
                                                      └ bundle 陈旧遮蔽
                                                             │
                                        SKILL 步骤4(模型判断是否修复 INDEX)◄┘
                                        SKILL 步骤5(提示跑 retro)
```

## Risks / Trade-offs

- **[INDEX 表格格式未来漂移致误解析]** → D2 fail-closed：不可解析即非零退出报错，不静默误判；pytest 固定「畸形→非零」负例断言。
- **[陈旧遮蔽判据清单演进]** → D4 收敛脚本常量单一源，未来改判据只改一处；SKILL prose 不再持副本（闭 T17）。
- **[归组误判风险]** → D3 归组不下沉，留模型，脚本层无此风险面。
- **[maintain 数据类化增测试维护面]** → 可接受：换来确定性 + 可测，符合仓内数据类取向；测试自包含在 `tests/`。

## 失败模式表（TG-08）

| 失败模式 | 触发条件 | 脚本行为 | 可观测 |
|---|---|---|---|
| INDEX 缺失 | 无 `openspec/INDEX.md` | 非零退出 | stderr 明示「INDEX 缺失」 |
| INDEX 畸形 | 表格结构不可解析出条目 | 非零退出（不当空处理） | stderr 明示「INDEX 表格不可解析」 |
| specs/rules 目录缺失 | 目录不存在（≠ 空目录） | 非零退出 | stderr 区分「目录缺失」vs「空」 |
| CLAUDE.md 不可读 | 权限/编码异常 | 非零退出（fail-closed，不跳过） | stderr 明示文件 + 原因 |
| 正常有差异 | set-diff 非空 | 退出 0 | 报告四类分节列出条目 |
| 正常无差异 | 全一致 | 退出 0 | 报告「一致，无差异」 |

## Migration Plan

- 新增脚本 + 测试，改 SKILL.md 步骤 1-3；无数据迁移、无破坏性变更。
- 回滚：删 `scripts/`/`tests/`、还原 SKILL.md 步骤 1-3 prose 即可（skill symlink，无安装态残留）。

## Open Questions

- 无阻塞性开放问题（Q1 归 D3、Q2 归 D4 均已定）。

## Compliance

- **MLH 全局红线**：遵守——fail-closed（失败模式表全非零退出）+ 可观测（stderr 明示）+ 坏输入 pytest 负例 + MUST NOT 引入静默面（D2 显式堵「畸形当空」静默面）。
- **§1.3 判断权留人/模型**：遵守——D1/D3 归组与是否修复不下沉。
- **adr/0006 机械 prose MUST 脚本化**：遵守——三类 set-diff 全脚本化。
- **仓库审查顺序**（本地 /review → PR → /code-review）：遵守，不颠倒。
- **bundle 边界**：本 change 不触 `sdflow-init/assets/`，无回灌链影响——遵守。
