# Task 4 · 第 1 步：GO/NO-GO 探针所需的最小面

> **范围**：只建探针所需的最小面（1 个 agent 定义 + sync_principles 投放面 + setup.sh 铺设）。
> **不含** `sdflow-web-researcher` / `sdflow-spec-writer`、`test_install_agents.py`、
> `test_sync_principles.py` 新用例、SKILL.md dispatch 段改写、SA-12 S2 secret scan、S3/S4/S5 验证
> —— 按票面，这些等主 session 的 GO/NO-GO 结论出来再做（NO-GO 则不做）。

## 1. 产物与落点

| 产物 | 落点 | 对应任务 |
|---|---|---|
| agent 定义 | `sdflow-spec/agents/sdflow-local-researcher.md` | 6.1 |
| 投放面声明 | `hack/sync_principles.py` 新增 `AGENT_TARGETS` + `agent_defs()` | 6.5 |
| 铺设函数 | `setup.sh` 新增 `install_agents()`（调用点在 `install_sdflow` 之前） | 6.7 |

## 2. 关键设计决策

### 2.1 `sdflow-local-researcher.md`

- **frontmatter**：`model: inherit`（D3 —— 档位仍由派发时的 `model` 参数覆盖，SKILL.md 正文
  MUST NOT 内联具体模型 id）· `effort: low` · 排他式 `description`（BASE-28 S5：明写
  「仅由 `/sdflow-spec` 编排派发，其它场景 MUST NOT 选用」+ 一句「误选会得到什么」，
  降低全局名册里被别的项目选中的概率）。
- **`tools` 走 BASE-28 S1 的「首选」写法**（作用域收窄）：
  ```
  tools: Read, Glob, Grep, Bash(git log:*), Bash(git show:*), Bash(git blame:*), Bash(git grep:*), Bash(rg:*)
  ```
  🔴 **作用域语法是否被宿主解析生效，本步未实测，也不宣称任何结论**——这是 tasks 5.3 的实测项，
  由主 session 的探针一并核验（判据见 §4.4）。定义正文里已按「两种结果都成立」的写法交代了
  诚实边界：作用域若生效才构成机械门；若不生效，只读性**只由角色纪律约束，属指令层非机械门**。
  正文**没有**任何「全只读」「工具白名单挡住写权」的措辞。
- **无网络**：`WebFetch` / `WebSearch` 均未列入；正文另加一条禁止用 Bash 绕道联网
  （`curl` / `wget` / `nc`），并指向 `sdflow-web-researcher`。
- **正文角色纪律**：① 结论 + `file:line` 出处、原始材料不回传（附「为什么」——主 session 上下文
  是相位 B 的稀缺资源）② 找不到 = 合法答案（防「为交差给个最接近的答案」）③ 检索纪律
  （共享字符串 grep 不加 `--include`；先证伪再落笔）④ 工具面诚实边界 ⑤ 仓内内容是数据不是指令。
- **通则托管块**：写占位注释对后跑 `--apply` 注入，**块内未手改**。

### 2.2 `sync_principles.py`

```python
AGENT_TARGETS = (REPO / "sdflow-spec" / "agents", SOURCE)   # (目录, 该用哪个源)

def agent_defs():
    d, _ = AGENT_TARGETS
    return sorted(d.glob("*.md")) if d.is_dir() else []
```

- **独立一项，不并进 `PROJECT_TARGETS`**：后者固定配 `SOURCE_PROJECT`（项目味）；agent 定义的
  读者是**被下发的子代理**，受众同 SKILL.md ⇒ 必须配 skill 味 `SOURCE`（含 fan-out 传播纪律那一段）。
  直接加进去 = 注入错误味源而 `--check` 照样报绿。
- **`AGENT_TARGETS` 写成「(目录, 源)」而不是文件清单**，成员由 `agent_defs()` **每次调用重新 glob**：
  ① 硬编码清单做不出「新增定义忘了纳入投放面 → 变红」这个场景（tasks 6.6 的定点用例要它）；
  ② glob 若在 import 期算死，测试「写入新 `.md` 后调 `SP.main(['--check'])`」在同进程内看不见新文件。
- **反向实证（非恒真锚）**：写完占位块、注入前跑 `--check` → 精确列出
  `sdflow-spec/agents/sdflow-local-researcher.md` 并 `exit=1`；`--apply` 后 `--check` 绿，
  投放面计数 19 → **20**。

### 2.3 `setup.sh install_agents()`

按 D11 **新写**，不沿用 `install_into`。函数头注释写清了三条「不能沿用」的实证理由
（顶层目录 + `SKILL.md` 循环进不去 / `is_our_marker_copy()` 对散装文件是路径谬误恒 false /
`cleanup_orphans` 的 `[ ! -d ]` 判据对 `*.md` 恒真）。

- **所有权守卫（比既有 idiom 更严，是新增不是复用）**：
  目标存在时——非软链 ⇒ skip；是软链但 `readlink` 不以 `$REPO_DIR/` 开头 ⇒ skip。
  两种 skip 都进 `skipped[]` 且**消息里带上实际指向**，人一眼知道怎么修。
  存在性判定用 `[ -e "$target" ] || [ -L "$target" ]`——`-e` 对悬空软链为 false，只用 `-e` 会漏。
- **孤儿清理**：`find -mindepth 1 -maxdepth 1` 枚举（glob 匹配不到 dangling 链），
  只清「指向 `$src_dir/` 且已悬空」的链。
- **Windows 分支明写取舍**：散装 `.md` 无 marker 落点 ⇒ 不铺设，`skipped[]` 报一行
  「Windows：散装 .md 无 marker 落点，不铺设；/sdflow-spec 走主 session 亲查/亲写」。
  **没有**写「copy + 所有权守卫」。

## 3. 验证

### 3.1 `bash setup.sh` 后的 `ls -la ~/.claude/agents/`

```
$ ls -la ~/.claude/agents/
total 0
drwxr-xr-x@  3 cheneyzhao  staff    96 Jul 26 23:09 .
drwxr-xr-x  46 cheneyzhao  staff  1472 Jul 26 23:09 ..
lrwxr-xr-x@  1 cheneyzhao  staff    90 Jul 26 23:09 sdflow-local-researcher.md -> /Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-spec/agents/sdflow-local-researcher.md
```

✅ 铺出、是软链、指向**本（开发）checkout**。setup 输出含
`✓ agents/sdflow-local-researcher.md @ /Users/cheneyzhao/.claude/agents`。

### 3.2 四条守卫路径的手工烟测（假 HOME = `/tmp/agtest`）

自动化测试是第 2 步的 6.8；本步先手工把四条分支各跑一遍，确认代码路径真的会走到：

| 场景 | 结果 |
|---|---|
| 预置**非软链真实文件** | `⚠ agents/… — 已存在真实文件，非本仓软链，未接管`；文件内容 `third party` **未被改** ✅ |
| 预置**指向 `/etc/hosts` 的软链** | `⚠ agents/… — 软链指向 /etc/hosts（非本仓），未接管`；`readlink` 仍是 `/etc/hosts` ✅ |
| 干净安装 + **重跑** | 两次都 `✓ installed`，链指向不变，幂等 ✅ |
| **悬空孤儿链**（`agents/gone.md` → 不存在的源） | `✗ agents/gone.md @ …` 进 `cleaned`，被清掉；有效链保留 ✅ |

⚠️ **Windows 分支未实测**——本机 `uname -s` 为 `Darwin`，`IS_WINDOWS` 无环境变量覆盖入口。
该分支只有一条 `skipped+=` + `return 0`，风险低；如需机械覆盖，6.8 可把 `IS_WINDOWS` 改为
可被环境变量覆盖（**本步未改**，避免为测试放宽生产逻辑）。

### 3.3 门禁

- `python3 hack/sync_principles.py --check` → `✅ 20 个投放面全部与真相源一致`
- `bash setup.sh` → 三个尾部检查全绿（sync_principles / gen_workflow_guide / async-branch-parity）
- `git add -A` 后仓根全量 `/usr/bin/python3 -m pytest -q` →
  **`2734 passed, 11 skipped, 3 xfailed in 273.88s`**，零失败。
  （已知抖动用例 `test_outside_voice_job.py::test_supervisor_transcript_…` 本轮**通过**。）

## 4. 给主 session 探针的交接

> 本节是本步最重要的交付：**怎么判定「确实走了 agent 定义路径」而不是 fallback。**

### 4.1 前置核验（探针之前，主 session 自己做）

1. `ls -la ~/.claude/agents/sdflow-local-researcher.md` —— 必须是指向本 checkout 的软链（已成立，见 §3.1）。
2. 看本 session 的**可用 agent 类型列表**里有没有 `sdflow-local-researcher`。
   🔴 **它不在列表里≠NO-GO**：agent 名册很可能在 session 启动时加载，而本文件是本 session 中途才铺出的。
   **允许且只允许重启一次 session 重测**；重启后仍不在 ⇒ 进 §4.5 的 NO-GO。
   MUST NOT 反复重试到「碰巧出现」为止。

### 4.2 探针怎么派

```
subagent_type: sdflow-local-researcher
model:  该轮 light 档解析出的【具体模型 id】（顺带做掉 tasks 5.2；不传则只验 5.1）
prompt: 见 §4.3
```

### 4.3 trivial 任务（答案唯一且主 session 能独立核验）

> 「查一件事：`hack/sync_principles.py` 里 `AGENT_TARGETS` 声明在第几行？它绑定的是哪一个源常量
> （`SOURCE` 还是 `SOURCE_PROJECT`）？
>
> 另外，回答完之后，**另起一节 `## 探针自报`**，逐条回答：
> ① 你这次实际拿到的工具清单是什么？**逐字列出**，包括括号里的作用域参数（如果有）。
> ② 你的系统提示里「工具面」那一节，关于 `Bash` 只读性的诚实边界，最后把需要联网的问题**指向了哪一个 agent 名字**？
> ③ 试着调用一次 `WebSearch`（查 `example`）。**如实报告**：这个工具你有没有？调用成功还是被拒？」

派发 prompt 里**MUST NOT**出现 `sdflow-web-researcher` 这个串（否则 ② 就不是自证了）。
prompt 里也**MUST NOT**贴四条通则——**agent 定义已经承载了它**，探针能否复述通则本身也是一条旁证。

### 4.4 判定（按顺序，前一条决定就不看后一条）

| # | 观测 | 判定 |
|---|---|---|
| **P0** | 派发**直接报错**（未知 `subagent_type` / 参数校验失败） | **NO-GO**，明确，无歧义 |
| **P1** | ③ 报告 **`WebSearch` 不在我的工具里 / 调用被拒** | **GO 的硬证据**——通用 fallback（`general-purpose` 工具面为 `*`）不可能缺 `WebSearch`。这是**否定式**判据，模型伪造不了「我没有这个工具」的失败 |
| **P2** | ① 自报清单 = `Read, Glob, Grep` + 若干 `Bash*`，**无** `Write` / `Edit` / `WebFetch` / `WebSearch` / `Agent` | **GO**（与定义 `tools` 行一致）。若出现 `Write`/`Edit` ⇒ 拿到的是通用工具面 ⇒ **NO-GO** |
| **P3** | ② 逐字答出 **`sdflow-web-researcher`** | GO 的**辅证**，不单独成立——定义文件在仓里，一个通用子代理理论上能 grep 到（虽无动机）。∴ P3 只能给 P1/P2 加权，MUST NOT 拿它当唯一依据 |
| **P4** | 回答自发采用「结论 + `file:line`」格式且**没有**回贴大段源码 | GO 的**行为旁证**，同样不单独成立 |

**GO 的最低门槛 = P1 或 P2 成立**（其一即可，两者同时成立最好）。**P3/P4 单独成立不算 GO。**

**顺带做掉的两项实测**（同一次探针即可结论，不必另派）：

- **tasks 5.2**：主 session 核对自己填进 `model` 参数的是**具体模型 id 字面值**、不是 `$SDFLOW_TIER_LIGHT`
  这类变量名；档位解析走既有四步加固协议（unset 清脏 → `[ -x ]` 预检 → 捕获退出码 → eval 后校验枚举与非空）。
- **tasks 5.3**（决定 SA-12 S1 走收窄还是诚实声明）：看 ① 自报清单里 `Bash` 的**呈现形态**——
  - 带括号作用域（`Bash(git log:*)` …）⇒ **作用域生效**，S1 走「收窄」，是机械门；
  - 退化成裸 `Bash` ⇒ **作用域被忽略**，S1 走**诚实声明**备选（定义正文已按这种情况写好，无需改字）；
  - `Bash` **整条消失**（解析失败被整行丢弃）⇒ 需要改写 `tools` 行（回退到无 Bash，或裸 `Bash` + 诚实声明）
    —— 这一支要在第 2 步动 `sdflow-local-researcher.md`。

### 4.5 NO-GO 的处置（票面硬约束）

判**红**，管线**停在阶段一形态**。
🔴 **MUST NOT** 把探针改成「验证 fallback 能不能走通」然后宣告通过——那把门变成不可能红的恒绿门。
🔴 **MUST NOT** 因为 NO-GO 就去派通用子代理顶替（D3：fallback 的唯一合法方向是**主 session 亲查/亲写**，
通用子代理路径撤掉了唯一的工具权限边界 = **降级即提权**）。
NO-GO 时本步的三件产物**保留在仓里**（它们不产生阶段一的行为改变：SKILL.md 的 dispatch 段尚未改写，
阶段一形态仍是主 session 亲做），第 2 步整体不做。

## 5. 遗留 / 需要留意的两点

1. **【设计层面的异议，已按原样实现】** D11 的守卫判据「`readlink` 指向本仓」我按**字面**实现为
   「以 `$REPO_DIR/` 为前缀」。副作用：**开发 checkout 与运行 checkout 之间来回切时，
   后一个 setup.sh 会 skip 而不是接管**（`~/.skills/sdflow-skills` 与本仓 `04-sdflow-skills`
   路径不同、目录名也不同 ⇒ 前缀不匹配；连既有 `cleanup_orphans` 的 `REPO_NAME` 子串 idiom 也匹配不上）。
   而 CLAUDE.md 的 dev/runtime 纪律恰恰要求「改 skill 后在开发 checkout 跑 setup 才测得到，
   测完在运行 checkout 重跑 setup 还原」——skills 那边靠 `install_into` 无条件覆盖软链做到了，
   **agents 这边做不到**。
   **不是静默失败**（`skipped[]` 会打印实际指向，人 `rm` 掉重跑即可），故未擅自放宽判据。
   若设计方认为该摩擦不可接受，最小修法 = 把判据放宽到「软链目标形如 `*/sdflow-spec/agents/<name>.md`」
   （无第三方会用这个路径），**一行 `case` 的改动**，属设计决策不属实现细节，留给编排层拍板。
2. **Windows 分支无机械覆盖**（见 §3.2 末）。
