---
schema_version: 1
change: shared-yaml-subset-parser
branch: feat/shared-yaml-subset-parser
generated_at: 2026-08-01T11:55:00+08:00
decision_hash: 6eed81224c72
---

# 决策纪要 · shared-yaml-subset-parser

## 目标态

用 yq（mikefarah/yq）替代 7 个脚本中 ~456 行手搓 YAML 解析代码，同时建立 setup.sh / sdflow-init 的运行依赖预检系统。

## 拍板决策

- **D1 用 yq 替代手搓 YAML** — 依据：yq 是成熟的单一二进制 YAML CLI 工具（v4.53.3，MIT，13k+ stars），实测覆盖全部现有场景（config.yaml 读写、Markdown frontmatter 读写、注释保留、连字符键名）。**砍掉的候选**：① 共享子集解析器（仍需维护手搓代码，只减量不消灭）；② PyYAML 降级封装（增加复杂度且 PyYAML 不保证消费仓可用）。
- **D2 yq 全局安装（包管理器）** — 依据：brew/winget/snap 已有官方包，与 git/python3/openspec CLI 同层级的系统工具。**砍掉的候选**：自管二进制放 `~/.sdflow/bin/`（增加平台判断、版本更新、架构检测的维护成本，且包管理器已做好这些）。
- **D3 依赖预检纳入本 change** — 依据：本 change 已引入 yq 检测，顺手覆盖其他依赖零增量成本；现有依赖检测分散在各 skill 的 preflight 中（setup.sh 只查 python3，各 SKILL.md 各自查 openspec），缺一次性全景。**砍掉的候选**：依赖预检作为独立 change（拆开后 yq 检测无落点，且延迟了统一预检的交付）。
- **D4 全部 7 个脚本都改为 yq** — 依据：yq `--front-matter=extract/process` 实测可处理 Markdown frontmatter（ship_gate.py / roadmap_writeback_draft.py / sad_schema.py / impl_route.py 的 plan marker 均适用）。**砍掉的候选**：只改 config.yaml 消费者（3 个脚本）——留下 4 个不改的脚本会形成混合态，比「全用 yq」更难维护。
- **D5 落 ADR-0036 记录 yq 引入决策** — 依据：命中 ADR 三条件（难逆转：删 456 行代码后回不去；缺上下文令人意外：为什么突然依赖 yq；有真实权衡：外部依赖 vs 零依赖）。

## 承重约束

- **C1 yq 全局安装 + setup.sh 检测** — 验证方式：`winget install --id MikeFarah.yq` 实测成功，yq v4.53.3 可用；`setup.sh:347-457` 已有 `install_sdflow()` 降级范式可套用。**证据锚**：`setup.sh:347`（install_sdflow 函数）、winget 安装日志。
- **C2 yq subprocess 替代全部手搓 YAML 解析** — 验证方式：yq 实测覆盖 config.yaml 读写（`.schema` / `.impl-pipeline` / `.metrics` / `.model-tiers`）、frontmatter 读写（`--front-matter=extract/process`）、注释保留（`-i` 写操作后注释完好）、连字符键名（`.ship-gate.design_approved`）。**证据锚**：本 session 的 yq 命令实测输出。
- **C3 零依赖不变量不破** — 验证方式：yq 是外部二进制工具（同 git / openspec CLI），脚本通过 subprocess 调用，不是 Python `import`。**证据锚**：`init.py:534`（零依赖声明的对象是 `import yaml`，不涉及外部工具）。
- **C4 依赖预检覆盖全部运行依赖** — 验证方式：子代理审计确认现有 gap 极小（git/bash 事实保证），有意义的检查项 = python3 ≥ 3.7（已有）/ openspec CLI（已有）/ yq（新增）/ pytest（开发可选）。**证据锚**：子代理审计报告（6 个脚本调用路径 + 全依赖清单）。
- **C5 `_parse_model_tiers_block` 的业务逻辑用 yq 数据 + Python 验证替代** — 验证方式：`yq -o json '.model-tiers' config.yaml` 返回完整嵌套 JSON，Python `json.loads()` 后的字典结构即可做 fleet/tier 键验证（越域键检测、畸形头检测等）。**证据锚**：yq 实测 `.model-tiers` 返回 `null`（注释态）/ 嵌套 JSON（活跃态）。

## 接受的边角

- yq 写操作的注释保留不保证 100% 格式不变（空行、尾部注释位置可能有微调）— 概率低（config.yaml 写操作只有 `_set_schema_key` 一处）/ 影响小（注释位置微调不影响语义）/ 完美成本过高（用 ruamel.yaml 多加一个依赖）。**接受。**
- Windows 上 yq 的 stderr 有非致命 temp file 清理 ERROR — 概率高（Windows 特有）/ 影响零（不影响功能和 stdout）/ 完美成本过高（需改 yq 上游）。**接受，subprocess 调用时 stderr 不检查。**
- yq 安装依赖包管理器（brew/winget/snap），无包管理器的环境需手动下载二进制 — 概率低（开发机几乎都有包管理器）/ 影响小（提示手动安装即可）。**接受。**

## 三镜代价

本次无 TG-23 命中（非≥2 方案选型——yq 是唯一合理方向，其余候选已在 D1 砍掉并记理由）。

简版三镜：系统镜——新增 yq 外部依赖，但消除 7 份各自漂移的脆弱实现，净降低复杂度；用户镜——`setup.sh` 多一行 yq 检测提示，无其他可感知变化；开发循环镜——「每轮 review 在某个脚本里挖到新 YAML 语法分支」的常态彻底消失。**主次**：开发循环镜为主。
