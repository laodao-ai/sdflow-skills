# `environments.md` 模板草案（过程·操作轴真相源）

> 状态：**草案**（explore 产出，未定稿为 sdflow 铺设物；`environments.md`/`testing-strategy.md` 等过程轴文档是否纳入 sdflow 铺设/维护属待议的生态问题，见 `04-ecosystem-boundaries.md` §8）。
> 用途：给消费项目的 `environments.md`（**per-system 单例**，落项目根或 `docs/`）作骨架；README/CLAUDE.md **概要+引用**本文，不复述。
> 边界（三条红线，起草时 MUST 守）：
> - 只放**操作**（怎么搭/怎么跑）——「**为什么是这个部署结构**」→ SAD §7（架构决策，引用不复述）；
> - **测什么/怎么分层**（测试方法）→ `testing-strategy.md`（本文 §2 只放测试**环境与命令**，方法引用它）；
> - **步骤会腐烂**——命令尽量指向脚本/Makefile 单一源（`make test` 而非逐条命令复制），本文描述「跑什么、依赖什么」。

---

<!-- 以下为 environments.md 的十六槽模板；<占位> 按项目实填，低风险节可一句话或显式 `N/A — <理由>`。
     示例填充用 Sarvelo mqtt-console 口径（Wails+Go+Svelte+MQTT），实际项目替换。 -->

## 1. 开发环境（本地 dev）

- **前置工具链**：<语言/运行时版本、构建工具、平台 SDK>
  <!-- 例：Go 1.22+ · Node 20+ · Wails v2 CLI · 平台 WebView 库(mac WKWebView / win WebView2 / linux webkit2gtk) -->
- **本地依赖服务**：<系统跑起来需要的外部依赖 + 如何起>
  <!-- 例：本地 MQTT broker(mosquitto)：`brew install mosquitto && mosquitto -p 1883`；无需 DB(纯文件) -->
- **构建 + 本地运行**：<一条命令起 dev；指向脚本，不逐条复制>
  <!-- 例：`wails dev`(GUI 热重载) · `go run . run --headless <args>`(CLI 形态) -->
- **常见坑**：<平台差异 / 首次搭建易错点>
  <!-- 例：linux 需装 webkit2gtk-4.0-dev；cgo 交叉编译限制 -->

## 2. 测试环境（跑测试要什么 · 怎么跑）

> 测试**方法/分层/测什么**归 `testing-strategy.md`——本节只放**环境依赖 + 执行命令**，方法引用不复述。

- **测试依赖**：<测试专用基础设施 + fixture>
  <!-- 例：单元测试无外部依赖；集成测试需本地 broker；e2e 需 playwright 浏览器 -->
- **各层执行命令**：<unit / integration / e2e 各怎么跑，指向脚本>
  <!-- 例：`go test ./...`(unit+integration) · `pnpm vitest`(前端) · `pnpm test:e2e`(playwright) -->
- **CI 环境**：<CI runner 平台 / headless 特殊处理 / 缓存>
  <!-- 例：GitHub Actions ubuntu；headless build tag 产不带 Wails/cgo/WebView 的精简 CLI 供裸测 -->
- **fixture / 测试数据**：<测试用 Pack/broker 数据从哪来>
- **方法指针**：见 `testing-strategy.md`（五泳道 / contract 即集成测试点 / 护栏）

## 3. 部署环境（怎么搭 · 怎么配 · 怎么发）

> 部署**架构决策**（进程形态/拓扑/分发方式）归 SAD §7——本节只放**目标环境搭建 + 配置项 + 发布/回滚操作**。

- **目标平台 + 依赖版本**：<生产/预发跑在哪、要装什么>
  <!-- 例：mac/win/linux 桌面单 binary；无服务端 -->
- **配置项清单**：<环境变量 / 配置文件 / 各项含义与默认>
  <!-- 例：四根目录经 location.yaml 覆盖(configDir/packsDir/dataDir/logsDir)，默认平台原生路径 -->
- **发布流程**：<打包 → 签名 → 分发，指向发布脚本/CI>
  <!-- 例：`wails build -platform <os>`；headless: `go build -tags headless` -->
- **回滚**：<出问题怎么退>
- **架构决策指针**：见 SAD §7 部署（多进程=1窗口1连接·单binary跨平台·非daemon）

---

## 附 A：README 概要引用范式

README 放**最小起步 + 指针**，不复述 environments 细节：

```markdown
## 快速开始
    make dev          # 本地开发（详见 environments.md §1）
    make test         # 跑测试（详见 environments.md §2）
    make build        # 打包发布（详见 environments.md §3）

环境搭建、CI、部署配置的单一真相源见 [environments.md](./environments.md)。
```

## 附 B：CLAUDE.md 概要引用范式（agent context 入口）

CLAUDE.md 是**给 AI 的 context 路由**——放 build/test/run/deploy **各一行关键命令**（agent 高频用）+ 指针；多环境细节/故障排查留给 environments.md，避免挤爆 context：

```markdown
## 常用命令
- 开发：`make dev`
- 测试：`make test`（unit+integration）/ `make test:e2e`
- 构建：`make build`
> 环境搭建/CI/部署细节 → environments.md（单一真相源，勿在本文复述）
```

> 现实锚：本仓 `CLAUDE.md`「## 常用命令」节（`bash setup.sh` / `pytest ...`）即此范式的雏形——关键命令在 CLAUDE.md，细节在别处。

---

## 引用纪律小结（单向、不复述）

```
SAD §7 部署(决策) ──被引──▶ environments §3(操作)     ← 决策 vs 操作
testing-strategy(方法) ─被引─▶ environments §2(环境)   ← 方法 vs 环境
environments(真相源) ──被引──▶ README / CLAUDE.md(概要) ← 真相 vs 入口
```

任一格内容只有一个家；跨格一律引用，禁复述（承 `04-ecosystem-boundaries.md` §5 真相源分工 + S11）。
