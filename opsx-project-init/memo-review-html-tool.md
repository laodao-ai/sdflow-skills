# Memo：OpenSpec 文档 HTML Review 工具（探索结论，待实现）

> 讨论产出于 mqtt-console 项目的 `/opsx:explore` 会话。这里记的是**收敛后的设计**，
> 不是任务拆解——真正动手时按这份 memo 走 brainstorming/writing-plans，不要跳过设计校验直接抄。

## 问题

`openspec/` 目录下文档量大（mqtt-console 项目实测 71 个 .md，分布在 roadmaps/adr/specs/
workflow/changes 等多处），互相引用方式不统一——部分是真 Markdown 链接（`[text](path.md)`），
部分是纯文本反引号路径（`` `openspec/xxx.md` ``，点不动）。人工 review 这堆文档目前只能靠
逐个开文件 + 手动定位路径，体验差。想要一个"打开就能看、点链接能跳转"的轻量查看器，
但排除了需要构建/打包/额外依赖的重方案（docsify/mkdocs 等），选择自建。

## 约束（决定了技术选型）

- **零构建**：不能有 npm/webpack/打包步骤，就是静态 html+js+css。
- **md 文件会动态增删改**：不能靠"生成时打包一份清单"这种要重新构建才能刷新的方案。
- **打开方式**：确认可以接受"一个项目起一次 `python -m http.server`"，不强求纯 `file://` 双击
  （`file://` 下 `fetch()` 被 Chrome CORS 拦死，且无法枚举目录内容，此路排除）。
- **浏览器**：日常用 Chrome/Edge，但既然走 `http://` 真实源而非 `file://`，方案对任意浏览器通用，
  不需要局限于 Chromium 专属 API（File System Access API 那条路因此也被更简单的方案替代）。
- **多项目隔离**：`python -m http.server` 天然按启动目录隔离，物理上互相看不到；唯一可能冲突的是
  端口，必要时 `python -m http.server 0` 让系统分配空闲端口。

## 最终架构

```
openspec/
  review.html              根入口壳子。scope="" （全树导航起点）
  serve.sh                 一行封装：python3 -m http.server "$@"
  tools/
    engine.js               共享逻辑（唯一实现，供所有壳子引用）
    engine.css               共享样式
  roadmaps/<name>/
    review.html              壳子：scope="roadmaps/<name>/"，缺省侧栏=本目录 md 列表
                              + 固定一行"← 全部文档"链接
  changes/<name>/
    review.html              同款壳子：scope="changes/<name>/"
```

**壳子（每个目录下的 review.html）职责**：
- 十几行薄文件，只设一个 scope 变量 + 引用共享引擎，不重复实现逻辑
- 缺省视图 = 本目录下的 md 文件列表（不是全树），但不是文件系统级沙箱限制——引擎仍可
  fetch 到 scope 之外的路径，点击任何跨目录链接都能正常加载
- 必须提供一条"回根"链接指向 `/review.html`

**关键坑（已用 `openspec/changes/archive/` 实例验证）**：change 目录 archive 前后深度不同——
活跃态 `openspec/changes/<name>/` 是 openspec 下 2 层，归档后 `openspec/changes/archive/<name>/`
变成 3 层。若"回根链接"/"引擎脚本引用"在生成时硬编码相对路径（如 `../../review.html`），
archive 把整个目录搬家之后就会断链（archive 是整目录搬迁，不是选择性拷贝，靠现有归档样本里
`staff-review-report.md` 等非标准文件也原样跟着搬确认过）。
**修法**：壳子里所有静态引用一律用**根相对路径**（`/review.html`、`/workflow/tools/engine.js`，以 `/`
开头、相对 server origin 解析，不相对当前文档深度），不管 stub 躺多深、目录怎么搬，字符串不变。
（B1 归位后工具机械在 `openspec/workflow/tools/`，故资产路径带 `/workflow/` 前缀；服务器根仍是 `openspec/`。）
文档正文里作者手写的相对路径（如 `design.md` 里的 `../adr/...`）不受影响，那些走浏览器标准的
"相对当前文档 URL"解析，本来就是对的，不需要改动引擎的这部分逻辑。

## 引擎（`workflow/tools/engine.js` + `engine.css`）能力清单

- Markdown 渲染：需要**内联 vendor 一份小型渲染库**（如压缩后的 marked.js），不用 CDN `<script src>`
  ——避免离线不可用（这个产品本身定位 local-first，查看工具也不该依赖联网）
- 目录动态发现：`fetch(目录URL)` 拿 Python `http.server` 自动生成的目录索引 HTML，
  用 `DOMParser` 解析出 `<a href>` 列表、过滤 `.md` 文件和子目录——每次都是当场读磁盘，
  天然满足"文件动态增删"，不需要任何自定义后端接口
  - 风险点：这是 stdlib 的"实现细节"输出格式，非正式文档化契约，多年稳定但非保证。
    若未来解析出问题，退路是换一个几十行的自定义 Python server 脚本加干净的 JSON 列表接口
    （仍是一条命令、零依赖），先按 stock 命令来，不行再升级。
- 链接拦截：拦 `<a>` 点击默认跳转，按当前文档的实际 URL 做标准相对解析（`new URL(href, docURL)`），
  重新 fetch + 渲染，同步浏览器历史（前进后退可用）
- **反引号路径自动转链接**：一个正则把 `` `openspec/xxx.md` `` 这类纯文本路径转成可点 `<a>`——
  现状里这类写法（42 处）比真链接（46 处）还多，不处理的话工具只覆盖不到一半的互链
- 无 mermaid 需求（已扫描全仓库确认 0 处 mermaid 代码块，不用引入图表渲染库）

## 三个环节的落点（对应三个不同的技术约束）

| 环节 | 落在哪 | 为什么 |
|---|---|---|
| 根引擎 + `serve.sh` | `opsx-project-init` 的 `assets/` + `init.py`（仿现有 `copy_bundle()`，同一套"单一源、update 覆盖刷新"机制） | 项目级铺设，本来就该在这一步 |
| `roadmaps/<name>/review.html` | `opsx-roadmap-planner` 四件套生成完之后，直接生成 | 该 skill 自己拥有、可编辑，不需要额外机制 |
| `changes/<name>/review.html` | **新增 PostToolUse hook**（`ff0-branch-guard.py` 的姊妹篇，同一目录 `assets/hooks/`） | change 目录由 `openspec new change <name>` 创建，而 `/opsx:new`/`/opsx:ff`/`/opsx:propose`/`/opsx:onboard` 等上层 skill 都不在 laodao-skills 控制范围内（本机找不到对应源码，应为第三方/官方插件分发）——参照现有 `ff0-branch-guard.py` 的思路：不逐个拦上层 skill，只拦它们殊途同归调用的同一条 CLI 命令 |

**新 hook 设计**（对照 `assets/hooks/ff0-branch-guard.py`）：
- PostToolUse（不是 PreToolUse——要等命令跑完、目录真的建出来才能补文件；不做 deny 判断）
- 复用同一条正则家族匹配 `openspec\s+new\s+change\s+(\S+)`，捕获 `<name>`
- 执行后检查 `openspec/changes/<name>/` 是否真实存在（不存在说明被 FF-0 挡了或命令失败，静默放行）
- 检查项目根 `openspec/review.html` 是否已铺设（没有说明还没跑过 `opsx-project-init`，静默跳过，
  不强迫铺设顺序）
- 写入 stub，幂等（已存在且内容一致则跳过）
- 白捡的好处：archive 是整目录搬迁，stub 会自动跟着搬进 `changes/archive/<name>/`，
  `opsx-done` 不需要再补一刀（前提是"根相对路径"那条修法生效）

## 有意排除的方案（避免以后重新踩一遍）

- **docsify/mkdocs 等现成文档站工具**：本可以直接解决 90% 需求，但需要额外依赖/约定，
  用户明确选择自建以贴合本仓库的怪癖（反引号路径自动转链接、workflow 阶段化导航等）
- **File System Access API（`showDirectoryPicker`）**：曾是"纯 `file://` 零服务器"方案的候选，
  但仅 Chromium 支持、且授权是按文件夹子树沙箱化（不能反向访问父级），会让"目录级视图仍要能
  跳到别的目录"这个需求别扭；用户确认可接受起一个 `python -m http.server`后，此路作废
- **静态生成的目录清单 JSON（"构建时"打包一份文件列表）**：与"md 文件会动态增删"这个约束直接冲突，
  作废
- **把功能挂在 `spec-review`/`impl-review`/`opsx-done` 的 review 时机上（而非创建时机）**：
  探索过程中一度提出的折中方案（因为以为创建时机拦不到），后来发现可以用 PostToolUse hook
  拦 CLI 命令解决创建时机问题，此折中方案作废，改回"创建时落地"

## 实现前待确认/待验证

- ~~Python stdlib 目录索引 HTML 的实际格式在当前 Python 版本下解析是否顺利~~ **已验证**
  （2026-07-01，Python 3.9.6，在 mqtt-console 的 `openspec/` 下实测）：
  ```html
  <ul>
  <li><a href="adr/">adr/</a></li>          <!-- 子目录：href 和文本都带尾部 / -->
  <li><a href="design.md">design.md</a></li> <!-- 文件：无尾部 / -->
  </ul>
  ```
  子目录与文件仅凭 href 是否以 `/` 结尾即可区分，规则简单可靠。直接 fetch 一个 `.md` 文件返回的是
  原始内容（无 HTML 包裹），headers 里 `Content-type: text/html; charset=utf-8` 是目录列表页特有的
  （fetch 具体文件时按文件本身类型返回），解析方案按原计划（`DOMParser` 取 `<a>` 列表）直接可行，
  无需退路方案。
- `engine.js` 内联的 markdown 渲染库选型（marked.js / markdown-it，体积、许可证）——未定，实现时选
- 新 hook 与 `ff0-branch-guard.py` 共享 `assets/hooks/` 目录，需确认 `opsx-project-init` 的
  `ensure_global_hook()` 逻辑要不要改造成"可以装多个 hook"（目前是单文件硬编码逻辑，见
  `init.py` 第106-164行）
- `opsx-project-init` 的 `SKILL.md` 描述需要更新，补充这个新增职责（职责单一性的取舍，
  探索时已提出过顾虑，用户选择接受耦合、复用现成分发管线）
- `laodao-skills` 仓库本身**没有 `openspec/` 目录**（2026-07-01 确认）——不像 mqtt-console 项目
  那样已经跑过 OpenSpec 工作流。若这次改造要走 OpenSpec 变更流程，需先在该仓库 `openspec init`。
