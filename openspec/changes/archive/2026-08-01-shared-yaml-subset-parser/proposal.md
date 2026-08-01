# shared-yaml-subset-parser

## Why

7 个数据类脚本各自手写 ~456 行 YAML 解析代码（`init.py` 175 行、`ship_gate.py` 106 行、
`impl_route.py` 72 行、`anchor_lint.py` 23 行 ×2 份、`roadmap_writeback_draft.py` 35 行、
`sad_schema.py` 45 行），因零依赖不变量（`MUST NOT import yaml`）而无法使用 PyYAML。

**后果已实证**（`impl-rework-cost-report.md` 标本 A/B）：
- 各脚本的行内注释剥离口径不同（`init.py` 字符级扫描 vs `impl_route.py` `find("#")` vs
  `ship_gate.py` `split(" #")`），对 `"value#tag"` 的处理各异。
- 每轮 code-review 都在某个脚本里挖到一个新的 YAML 语法角落（多文档 `---`、指令 `%YAML`、
  键后空格……），手搓解析器无法穷举无界语法面 ⇒ 补丁循环不收敛。
- 最严重标本 `align-sdflow-spec-with-openspec-schema` 跑到 fix8、37 个 fix 轮。

**根治手段 = 不再手搓**：用 `yq`（mikefarah/yq，成熟的单一二进制 YAML CLI）替代全部手写
YAML 解析，脚本通过 subprocess 调用 yq，零依赖不变量不破（yq 是外部工具，同 git）。

同时建立 `setup.sh` / `sdflow-init` 的运行依赖预检系统，统一检测 python3 / openspec / yq / pytest
等全部运行依赖（当前检测分散在各处，缺统一全景）。

## What Changes

### 依赖预检系统
- `setup.sh` 新增 `check_dependencies()` 函数，检测 python3 ≥ 3.7 / git / yq / openspec（可选 pytest）
- 不中止 setup.sh（套用既有降级范式），检测结果进汇总
- `sdflow-init` 的 init/update 路径同步检测 yq 可用性

### YAML 解析重构
- 7 个脚本中的 ~456 行手搓 YAML 解析代码全部删除
- 替换为 `subprocess.run(["yq", ...])` + `json.loads()` 调用
- 读操作：`yq -o json '.key' file.yaml`
- 写操作：`yq -i '.key = "value"' file.yaml`（保留注释）
- Markdown frontmatter：`yq --front-matter=extract/process`

### ADR
- 新增 `openspec/adr/0036-yq-replaces-hand-rolled-yaml.md`

## Capabilities

### New Capabilities
- `yq-yaml-operations`: yq subprocess 封装与依赖检测

### Modified Capabilities
- `spec-workflow`: 依赖预检系统加入 setup.sh / sdflow-init

## Impact

- `sdflow-init/scripts/init.py` — 删 ~175 行 YAML 解析，改为 yq 调用
- `sdflow-ship/scripts/ship_gate.py` — 删 ~106 行 frontmatter 解析，改为 yq `--front-matter`
- `sdflow-implement/scripts/impl_route.py` — 删 ~72 行，改为 yq 调用
- `openspec/workflow/tools/anchor_lint.py` (×2 份) — 删 ~23 行，改为 yq 调用
- `sdflow-done/scripts/roadmap_writeback_draft.py` — 删 ~35 行，改为 yq `--front-matter`
- `sdflow-architecture/scripts/sad_schema.py` — 删 ~45 行，改为 yq `--front-matter`
- `setup.sh` — 新增依赖预检
- `sdflow-init/SKILL.md` 或 `scripts/init.py` — yq 可用性检测

## Success Metrics

1. 全部 7 个脚本中无任何手搓 YAML 解析代码（`grep -rn` 验证无 `partition(":")` 式 YAML 解析模式），但 ship_gate.py 的 duplicate-key/tab-indent 原始文本预扫描除外（R11）
2. 既有测试全绿（每个 skill 的 `tests/` 目录）
3. `setup.sh` 运行时输出依赖检测汇总（含 yq 状态）
4. yq 不可用时 fail-loud（明确报错 + 安装指引），不静默降级
5. yq 安装后端到端读写验证通过（config.yaml 读写 + frontmatter 读写 + 注释保留）[spec-review-amendment C10]

## Non-Goals

- 不改 `resolve-models.sh`（shell 脚本，跨语言无法共享，保持各自实现 + golden 测试守一致）
- 不把 yq 打包进 `~/.sdflow/bin/`（全局安装，包管理器管理）
- 不重构依赖管理为框架（只做检测 + 提示，不做自动安装——用户的包管理器是正确的安装手段）
- 不扩展到非 YAML 格式的解析优化（Markdown fence 解析已有机械守且有界，不需要动）

## Compliance

不命中任何 TG 触发。不涉及 DB/API/安全/数据保护。yq 是 MIT 协议开源工具。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)。
