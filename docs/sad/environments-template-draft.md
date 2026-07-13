# `environments.md` 模板（过程·操作轴真相源）

> 状态：**已接地**（2026-07-13）——mqtt-console 按本模板真写出 203 行 `environments.md`，回执见 `06-process-axis-grounding-receipt.md`。交付形态已拍板 **B+C**（模板 + 归位型 prompt 起草；维护挂 `sdflow-init update`），见 `05` §5.2。
> 用途：给消费项目的 `environments.md`（**per-system 单例**，落 **`openspec/architecture/`**，与 `sad.md` 同居——见 `05` §2.2.1）作骨架；README/CLAUDE.md **概要+引用**本文，不复述。
> 边界（三条红线，起草时 MUST 守）：
> - 只放**操作**（怎么搭/怎么跑）——「**为什么是这个部署结构**」→ SAD §7（架构决策，引用不复述）；
> - **测什么/怎么分层**（测试方法）→ `testing-strategy.md`（本文 §2 只放测试**环境与命令**，方法引用它）；
> - **步骤会腐烂**——命令尽量指向脚本/Makefile 单一源（`make test` 而非逐条命令复制），本文描述「跑什么、依赖什么」。
>
> **两条接地纪律**（血泪，MUST 守）：
> - **命令必须为真**：每条命令都要能在 `Makefile` / `package.json` / `wails.json` 里找到出处（**建议直接写「出处」列**）。项目没有 `make dev/test/build` 就照实写真命令，**MUST NOT 为对齐模板范式而虚构 target**。（若认为该项目应把命令收拢进 Makefile，那是一条 **todo**，不是在文档里假装它已存在。）
> - **N/A 须连带记后果**：显式 `N/A — <理由>` 之外，还要记它**留下的洞**（例：CI = N/A ⇒「`assert-bindings` 因此无任何自动触发点，靠人工约定跑」）。只写 N/A 不写代价，等于把缺口藏进"这项不适用"。

---

<!-- 以下为 environments.md 的十六槽模板（§1 五 + §2 六 + §3 五）；<占位> 按项目实填，
     低风险节可一句话或显式 `N/A — <理由> + <后果>`。
     槽数订正史：原草案自称「十六槽」但实际只列了 14 个（4+5+5）——数字对不上；
     2026-07-13 接地补入「构建副产物」「测试选择路由」两槽（06 §2.1），现真为 16。
     示例填充用 Sarvelo mqtt-console 口径（Wails+Go+Svelte+MQTT），实际项目替换。 -->

## 1. 开发环境（本地 dev）

- **前置工具链**：<语言/运行时版本、构建工具、平台 SDK>
  <!-- 例：Go 1.22+ · Node 20+ · Wails v2 CLI · 平台 WebView 库(mac WKWebView / win WebView2 / linux webkit2gtk) -->
- **本地依赖服务**：<系统跑起来需要的外部依赖 + 如何起>
  <!-- 例：本地 MQTT broker(mosquitto)：`brew install mosquitto && mosquitto -p 1883`；无需 DB(纯文件) -->
- **构建 + 本地运行**：<一条命令起 dev；指向脚本，不逐条复制>
  <!-- 例：`wails dev`(GUI 热重载) · `go run . run --headless <args>`(CLI 形态) -->
- **构建副产物**：<dev/build 生成了什么、是否 gitignore、谁依赖它>   ← 接地补槽（06 §2.1）
  <!-- 例：首次 `wails dev` 生成 frontend/wailsjs/ 绑定代码（gitignore，仓库里没有），
       前端测试直接 import 它 ⇒ fresh clone 直接跑 npm test 会挂。
       为什么单列而不并进「常见坑」：它是**事实**（生成了什么），坑是它的**后果**；
       没有这一槽，坑就成了无源之因，读者不知道该怎么补救。 -->
- **常见坑**：<平台差异 / 首次搭建易错点>
  <!-- 例：linux 需装 webkit2gtk-4.0-dev；cgo 交叉编译限制。
       ⚠ 本槽 SAD 投影率为零、纯人写，却往往是全篇最高价值的一节（06 §4.1）。 -->

## 2. 测试环境（跑测试要什么 · 怎么跑）

> 测试**方法/分层/测什么**归 `testing-strategy.md`——本节只放**环境依赖 + 执行命令**，方法引用不复述。

- **测试依赖**：<测试专用基础设施 + fixture>
  <!-- 例：单元测试无外部依赖；集成测试需本地 broker；e2e 需 playwright 浏览器 -->
- **各层执行命令**：<unit / integration / e2e 各怎么跑，指向脚本>
  <!-- 例：`go test ./...`(unit+integration) · `pnpm vitest`(前端) · `pnpm test:e2e`(playwright)
       **建议带「出处」列**（命令 | 跑什么 | 出处=Makefile:11-14）——这是本模板里
       机械化程度最高的一槽（可对构建配置核验，甚至可生成；05 §4.2 / §5.2.1 ①）。 -->
- **测试选择路由**：<改了什么 → 该跑哪条；建议画决策图>   ← 接地补槽（06 §2.1）
  <!-- 例：改 Go 代码日常迭代 → go test ./...；改连接/停机等集成行为 → make embedded；
       改 driver/TLS → make integration；改前端组件 → npm test；改布局/性能 → make frontend-e2e。
       为什么单列：命令表回答「有哪些命令」，路由回答「我该敲哪条」——两件事，
       后者是 contributor 最高频的问题，前者答不了它。 -->
- **CI 环境**：<CI runner 平台 / headless 特殊处理 / 缓存>
  <!-- 例：GitHub Actions ubuntu；headless build tag 产不带 Wails/cgo/WebView 的精简 CLI 供裸测。
       无 CI 时：显式 `N/A — 当前无 CI，门禁全在本地` **并连带记后果**
       （例：「`assert-bindings` 因此无任何自动触发点」）——见抬头「N/A 须连带记后果」。 -->
- **fixture / 测试数据**：<测试用 Pack/broker 数据从哪来；文件在哪、怎么生成>
  <!-- 数据**代表什么 / 为什么这样造**（golden vs factory 取向）→ testing-strategy，不在此。 -->
- **方法指针**：见 `testing-strategy.md`（泳道分层 / contract 即集成测试点 / 护栏 / 盲区）

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

README 放**最小起步 + 指针**，不复述 environments 细节。

> ⚠ **下面的 `make dev/test/build` 是占位示例，不是范式要求**——照抄它是接地时点名的头号陷阱（模型会为对齐范式而虚构 Makefile target）。**用项目真实的命令**。

```markdown
## 快速开始
    <项目真实的 dev 命令>      # 例：wails dev
    <项目真实的 test 命令>     # 例：go test ./...
    <项目真实的 build 命令>    # 例：wails build

环境搭建、其余测试泳道的执行命令、数据目录与发布 →
[`environments.md`](openspec/architecture/environments.md)（单一真相源）。
测试怎么分层、护栏与门禁清单 →
[`testing-strategy.md`](openspec/architecture/testing-strategy.md)。
```

## 附 B：CLAUDE.md 概要引用范式（agent context 入口）

CLAUDE.md 是**给 AI 的 context 路由**——放 build/test/run **各一行关键命令**（agent 高频用）+ 指针；完整命令表/故障排查留给 environments.md，避免挤爆 context：

```markdown
## 常用命令
- 开发：`<真实 dev 命令>`
- 测试：`<各泳道各一条真实命令>`
- 构建：`<真实 build 命令>`

> 完整命令表（含 <低频 target>）、环境依赖、数据目录、发布/回滚 →
> **`openspec/architecture/environments.md`（单一真相源，勿在本文复述）**；
> 测试分层与护栏 → **`openspec/architecture/testing-strategy.md`**。
```

> 现实锚：本仓 `CLAUDE.md`「## 常用命令」节（`bash setup.sh` / `pytest ...`）即此范式的雏形——关键命令在 CLAUDE.md，细节在别处。
> 接地锚：mqtt-console 的 `CLAUDE.md`「常用命令」节（含那句 **「勿在本文复述」**）是本范式的完整实例。

---

## 引用纪律小结（单向、不复述）

```
SAD §7 部署(决策) ──被引──▶ environments §3(操作)     ← 决策 vs 操作
testing-strategy(方法) ─被引─▶ environments §2(环境)   ← 方法 vs 环境
environments(真相源) ──被引──▶ README / CLAUDE.md(概要) ← 真相 vs 入口
```

任一格内容只有一个家；跨格一律引用，禁复述（承 `04-ecosystem-boundaries.md` §5 真相源分工 + S11）。

**唯一合法例外 = 同一事实的两面投影**（`05` §3.0）：结构轴「行为是什么」与过程轴「为什么这条断言长这样」各 own 一个面，**不算双写**，但 **MUST 显式互指**。

## 起草纪律：必须用「归位型」prompt，不是「填模板型」

**素材通常已存在且已散落**（getting-started / 模块文档 / roadmap 包里的测试策略…）。若 prompt 写成「读模板 → 填 environments.md」，模型会**重写一份**而源文件原地不动 ⇒ **双写变三写**，正是本模板全篇要防的东西。

骨架 MUST 是：

```
盘点素材 → 判归属（每节判去一个格）→ 搬运（含删源/留指针）→ 补空槽 → 反向瘦身入口 → 自检
                     └─ 唯一无确定性信号的一步：人门放这里 ─┘
```

「新写」只发生在真正没有素材的空槽里。可执行实例（含三个已知硬骨头）见 `mqtt-console-process-docs-prompt.md`；接地回执见 `06-process-axis-grounding-receipt.md`。
