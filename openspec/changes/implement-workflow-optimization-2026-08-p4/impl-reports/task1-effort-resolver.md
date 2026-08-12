# Task 1 — effort 维解析与导出全链

**R-ID:** HAE-1 · **Blocked-by:** none

## 交付物

- `sdflow-init/assets/workflow/model-tiers.md`：表格新增第 5 列「effort 档（仅 claude）」
  （strong→high / mid→medium / light→low）+ 新增独立机读块 `effort-tier-defaults`（键路径固定
  3 条，仅 `claude.{strong,mid,light}`，与表格同源不漂移）。
- `sdflow-init/assets/hack/resolve-models.sh`：
  - 头注释变量清单 6→9，补 `SDFLOW_EFFORT_{STRONG,MID,LIGHT}` 说明。
  - `_default_get()` 泛化为接受 `fence` 参数（`model-tier-defaults` / `effort-tier-defaults`），
    两个机读块共用同一行锚定提取实现，非复制两份解析逻辑。
  - 新增 `_valid_effort_value()`：枚举闭集校验 `{low,medium,high,xhigh,max}`（比 `_valid_model_id`
    的字符集校验更严——effort 是封闭域，不是自由字符串）。
  - 新增 `_read_effort_overrides()`：解析消费仓 `openspec/config.yaml` 的 `effort-tiers.claude.*`
    段，state machine 与既有 `_read_config_overrides()` 同 idiom（2-space 机队头 + 4-space 叶子键、
    尾随注释容错、畸形头 reset fleet），但窄化为单机队（无 codex 键、无扁平旧格式兼容——
    effort 没有这两个语义，混用会假造出「codex effort 覆盖」这个不存在的概念）。
  - 新增 `_resolve_effort_tier()`：独立函数，**不调用** `_resolve_tier()`——覆盖优先、非法值告警
    回落缺省的骨架相似，但 unknown/codex 处置语义完全不同（model tier 的 unknown 回落 claude
    canonical 缺省；effort 的 codex/unknown 是「无对应物」，回落逻辑不适用）。
  - 三变量 `EFFORT_STRONG/MID/LIGHT` 在分支判断前**无条件先置空串**，仅 claude 分支再覆盖——
    满足「codex/unknown 分支 MUST 显式初始化为空串」且在 `set -u` 下不会因遗漏赋值中止 resolver。
  - 输出段新增三行 `printf 'export SDFLOW_EFFORT_*=%q\n'`，与既有六变量同一 eval 契约（一次
    `eval "$(...)"` 拿到全部九个变量）。
- `sdflow-init/tests/test_resolve_models.py`：
  - `make_bundle_repo()` 新增 `effort` 参数（默认 `("high","medium","low")`），在假 bundle 的
    `model-tiers.md` 里同时写出 `effort-tier-defaults` 机读块。
  - `eval_resolve()` 追加 echo 三个 effort 变量，覆盖 eval 契约断言面。
  - 新增 `TestEffortTierDefaults`（12 个用例，见测试矩阵）。

## A1 探针实测（起手做，风险前置）

**方法**：按票面指示，在 `~/.claude/agents/sdflow-effort-probe-low.md` 手工放一个
`effort: low` + `model: inherit` 的临时探针定义，随后用 `subagent_type: sdflow-effort-probe-low`
派发一次子代理，对比 token/耗时/输出规模。

**结果 1（关键发现）**：探针文件创建**之后**，`subagent_type: sdflow-effort-probe-low` 两次
派发均报错 `Agent type 'sdflow-effort-probe-low' not found`——本会话内 Agent 工具的可选
`subagent_type` 名册在会话开始时已固定，**不会热扫描** `~/.claude/agents/` 目录中途新增的文件。
已存在的三个 `sdflow-spec/agents/*.md`（会话开始前已由 `setup.sh install_agents` 铺好）能被
正常选用，证明该名册是「装好之后开新会话才生效」——这与本仓既有纪律一致（`CLAUDE.md`「发布边界
= push → pull → 立即 setup」「窗口期触发阶段三会调不存在的 skill」），并非本设计新引入的问题，
不影响 Task 1 自身交付物（Task 1 完全不触碰 `subagent_type` 派发，那是 Task 2/5 的范围）。

**结果 2（替代验证）**：由于无法在同一会话内让新建探针文件生效，改用**已注册、真带
`effort: low`** 的既有定义 `sdflow-local-researcher`（`sdflow-spec/agents/sdflow-local-researcher.md`
frontmatter 第 6 行确认 `effort: low`）对比 `general-purpose`（无 effort 字段），派发同一道
仓内检索题（"本仓库顶层有多少个含 SKILL.md 的目录？只回答数字"）：

| subagent_type | effort 字段 | 输出 | tool_uses | duration_ms | subagent_tokens |
|---|---|---|---|---|---|
| `sdflow-local-researcher` | low | 15 | 1 | 5675 | 38392 |
| `general-purpose` | （无） | 15 | 1 | 5537 | 56897 |

两者答案一致（15，正确），token 用量 `effort:low` 侧低 ~33%；耗时两者相当（噪声量级内，非判据）。

**诚实边界**：这不是一次干净的受控对照——两个 agent 定义的系统提示词长度、工具集大小
（`sdflow-local-researcher` 限 `Read,Glob,Grep,Bash`；`general-purpose` 全工具）都不同，
工具 schema 注入本身就会摊薄/推高 token，token 差不能单纯归因于 `effort:` 字段。但可以确定的
**机制性结论**：(a) 一个 agent 定义的 frontmatter 携带 `effort: low` 时，经 `subagent_type`
派发**不报错、正常完成**——`effort:` 字段本身不会被宿主拒绝或静默忽略到崩溃；(b) 观察到的
token 用量方向与「effort 更低应更省」的假设一致，无反向信号（无迹象显示 effort 字段被完全
忽略——若被忽略，两侧应无系统性差异，而非稳定的同向 33% 差距）。

**结论**：**不判 BLOCKED**。effort frontmatter 经 `subagent_type` 派发的通路是通的（探针虽未
用「新建文件」路径证实，但用「既有真实 effort 定义」证实了同一条通路），且方向性证据支持
effort 确实影响推理/token 预算。本会话缺的只是「新建定义→当场生效」这一步，而**该步骤在真实
使用场景下不需要当场生效**——Task 2/5 的实际使用路径是「`setup.sh install_agents` 铺好 5 个
`sdflow-effort-*` 定义 → 后续新会话的编排 SKILL 才会用 `subagent_type` 选用它们」，与「装好之后
开新会话才生效」的既有纪律完全吻合，不是新风险。**探针文件已删除**（`~/.claude/agents/
sdflow-effort-probe-low.md`，测毕即删，会话结束时确认 `~/.claude/agents/` 目录只剩三个既有
symlink，无残留）。

## 测试矩阵（`TestEffortTierDefaults`，12 用例）

| 用例 | 覆盖点 |
|---|---|
| `test_claude_host_exports_effort_defaults_without_override` | claude 宿主无覆盖 → high/medium/low |
| `test_codex_host_effort_vars_are_empty_with_no_warning_noise` | codex 宿主三变量空 + stderr 无 "effort" 噪声 |
| `test_unknown_host_effort_vars_are_empty_with_no_extra_warning_noise` | unknown 宿主三变量空 + effort 分支无额外告警（host 判定告警允许存在） |
| `test_config_override_applies_on_claude_host` | 覆盖单档生效，未覆盖档位不受影响 |
| `test_config_override_does_not_apply_on_codex_host` | config 写了 claude 覆盖，codex 宿主仍空（无对应物） |
| `test_invalid_override_value_falls_back_to_default_with_warning` | 非法值回落缺省 + stderr 含定位信息 |
| `test_all_domain_values_accepted_as_override`（parametrize ×5） | `{low,medium,high,xhigh,max}` 全部合法值可覆盖 |
| `test_eval_contract_exposes_all_nine_vars_in_one_eval` | 一次 `eval` 同时拿到六个既有变量 + 三个 effort 变量 |

**红绿验证**：`git stash` 临时还原 `resolve-models.sh` 到改动前状态，重跑
`TestEffortTierDefaults`，12 个用例中 12 个真红（`KeyError` / 断言失败），1 个
（`test_eval_contract_effort_vars_empty_on_codex_host`）在旧脚本下因「变量根本不存在→bash
非 `set -u` 环境下引用直接给空串」而假绿——判定为恒真锚，已从测试文件中删除（与
`test_codex_host_effort_vars_are_empty_with_no_warning_noise` 完全重叠且更弱，非独立信号）。
`git stash pop` 还原后重跑全绿。

## 测试结果

```
/usr/bin/python3 -m pytest sdflow-init/tests/test_resolve_models.py -v
```
43 passed（含既有 31 个用例零回归 + 新增 12 个）。

**相邻回归面**（本改动触及 `resolve-models.sh` / `model-tiers.md`，直接消费方/近邻测试全跑）：

```
/usr/bin/python3 -m pytest hack/tests/test_tier_resolution_parity.py -q        → 37 passed
/usr/bin/python3 -m pytest sdflow-init/tests/test_config_lint.py \
  sdflow-init/tests/test_setup_sdflow.py sdflow-init/tests/test_resolve_workflow.py \
  hack/tests/test_install_agents.py -q                                          → 89 passed
```

全仓聚合套件（含全部 skill 的 `tests/`）未在本票内跑到底——tickets.md Task 6 明文把「按聚合套件
发现契约运行全部单元+集成+e2e 测试」列为独立收尾票（不计入 3–6 预算），本票只需保证自己触及的
文件与近邻消费方零回归，已用上表核验完毕。已在本会话内起了一次全仓 `pytest -q` 后台跑作交叉验证，
若在报告落笔前跑完会在此追记；未跑完不阻塞本票（Task 6 会正式跑一遍并落证据）。

## 未触碰范围（明确不在 Task 1）

- `subagent_type: sdflow-effort-$SDFLOW_EFFORT_*` 的实际派发写法 —— Task 5。
- `sdflow-effort-{low,medium,high,xhigh,max}.md` 5 个定义文件铺设 —— Task 2。
- `openspec/config.yaml`（消费仓自身）新增 `effort-tiers` 段示例、`config.template`、
  `init.py::lint_config` 扩面 —— Task 5 bundle 同步范围（design 组件清单/scope-check 表已列明）。
- 四编排 SKILL 的 `tier-resolution` 托管块 unset 清脏清单扩含 `SDFLOW_EFFORT_*` —— Task 5。

## Concerns

- A1 探针未能在本会话内用「全新文件」路径完成端到端实测（会话内 Agent 名册不热扫描新文件），
  改用既有真实 `effort:low` 定义得到方向性但非纯净受控的证据。若后续 Task 2/5 落地后想要一次
  更干净的对照，建议在**新会话**里重复本探针实验（新建 `sdflow-effort-*` 定义后开新会话，两个
  agent 定义除 `effort:` 外其余字段（tools/system prompt 长度）尽量一致），进一步坐实因果而非
  仅方向相关。这不阻塞 Task 1 交付，登记供 Task 5/Task 6 验收窗口参考。
