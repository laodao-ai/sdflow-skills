## ADDED Requirements

### Requirement: recorder 跨脚本调用前校验 schema 版本，失配 fail-closed

`issues.py` **SHALL** 在派出任何取数子进程**之前**校验 sibling 脚本自报的 recorder schema 版本；与自身预期不一致时 **MUST** fail-closed：非零退出、stderr 给出**可执行**的修复指令（升级运行 checkout 并重跑 `setup.sh`），**MUST NOT** 继续取数、**MUST NOT** 降级为空集继续。

> 依据：`issues.py` 依赖派 `buglist.py` / `todolist.py` 子进程取数，而三者按**自身文件位置**互相定位（既有设计）。在 dev / runtime 双 checkout 纪律与 `pull → setup` 窗口期下，**版本偏斜是结构性常态、不是意外**。

被调方 `buglist.py` / `todolist.py` **SHALL** 各提供一个只读的版本自报入口，其输出为确定性的 schema 版本标识。

#### Scenario: sibling 滞后时硬停且零写盘

- **WHEN** `issues.py` 定位到的 `buglist.py` 自报 schema 版本低于自身预期
- **THEN** 命令非零退出，stderr 含具体的失配版本号与修复指令，且**任何盘面文件（INDEX / batches / dated 文件）字节未变**

#### Scenario: 版本一致时行为无变化

- **WHEN** sibling 自报版本与预期一致
- **THEN** 命令行为与握手引入前完全相同（退出码、stdout JSON 形状、写盘结果均不变）

#### Scenario: sibling 缺失版本自报入口按失配处置

- **WHEN** sibling 脚本不支持版本自报（更旧的版本，调用该入口即报错）
- **THEN** 视同版本失配，走同一条 fail-closed 路径，**MUST NOT** 解释为「无版本要求」而放行

### Requirement: 握手落在共用取数入口，覆盖全部调用方

版本校验 **SHALL** 落在 `issues.py` 的**共用取数入口**（派 sibling 子进程处），使全部经该路径的子命令一次获得保护，**MUST NOT** 只在单个子命令内点补。

受保护的调用方 **MUST** 至少包含：`sweep`、`reindex`、`batch rename`、`batch add`、`set-status`、`lint`。其中 **写盘类**（`reindex`、`batch rename`、`batch add`、`set-status`）的校验 **MUST** 前置于任何 discovery / 写盘动作（承 `adr/0022`：skill 可改不可删用户文件 ⇒ 破坏性动作前先把门关上）。

#### Scenario: 写盘类子命令在偏斜下不覆盖权威索引

- **WHEN** sibling 滞后时执行 `reindex`
- **THEN** 命令非零退出，`INDEX.md` 字节未变（**不得**出现「用只含 legacy 表项的残缺集合重建索引并 exit 0」）

#### Scenario: 每个调用方各自验证

- **WHEN** 为本需求编写测试
- **THEN** 上述每个受保护子命令**各有**一条偏斜场景断言，**MUST NOT** 仅测 `sweep` 一条路径即宣称覆盖（承 `adr/0011`：共用解析核心的返回语义按消费方各自定）
