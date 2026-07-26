# Task 2 · fix 轮次 4 —— canonical 阶段一入口同步（窄修收口）

**基线 HEAD**：`85fb547`（分支 `feat/add-sdflow-spec`）
**输入**：收票冷验第 2 次，1 Important + 3 Minor
**结论**：4 条全部处置完毕（3 修 + 1 如实改声明）；按基准 3 面治扩出的 4 处同形态漏网**一并修掉并上锚**；
11 处描述性引用逐处登记不改（理由见 §3）。**9 个变异全部实测**，判据「期望红 ⊆ 实际红」逐条成立。

---

## 0. 一句话结论表

| # | 发现 | 处置 | 机械锚 | 变异 |
|---|---|---|---|---|
| Important | `sdflow-roadmap/SKILL.md` 交棒块无条件给 `/opsx:new` | 两分支化 | `DOCS_CARRIERS["sdflow-roadmap/SKILL.md"]` ×2 | R1 / M3 ✅ |
| 面治 +1 | `sdflow-roadmap/SKILL.md:394` 只否定 `opsx:ff` | 两分支都点名 | 同上 ×1 | M4 ✅ |
| 面治 +2 | `sdflow-architecture/SKILL.md` frontmatter `description` 无条件给 `/opsx:ff` | 两分支化 | `DOCS_CARRIERS["sdflow-architecture/SKILL.md"]` ×1（新增第 2 条） | M5 ✅ |
| 面治 +3/+4/+5 | FF-0「入口全集」清单三处漏 `/sdflow-spec` | 三处补齐 | 新用例 `test_ff0_entry_roster_includes_branch_a` | M6a/b/c ✅ |
| Minor 1 | TTL 单边比较，未来 mtime 恒新鲜 | `0 <= age <= TTL` | 新用例（参数化 2 例） | M1 ✅ |
| Minor 2 | 三处硬写「10 分钟」与常量分叉 | **删数字，让 deny 文案自报** | 新用例 `test_ttl_window_has_a_single_source` | M2b/M2c ✅ |
| Minor 3 | `docs/sdflow-fable5/02` 混基线声明 | 声明改成如实的（活文档） | 无（语义残余，见 §2.4） | — |

---

## 1. Important + 面治：阶段一入口载体

### 1.1 根因复盘（为什么连续三轮点穿同一片面）

三轮的**修法**都对，**期望集的范畴**一直取窄：

| 轮次 | 期望集范畴 | 漏掉的 |
|---|---|---|
| fix2 前 | `docs/` 下四份「流程图」文档 | 仓 README、docs 包内其余份 |
| fix2 | 扩了「份」没扩「处」 | 同一份文档里的其它分支表述 |
| fix3 | 扩到「处」，但只到 `docs/` + README + 被点穿的 `sdflow-architecture/SKILL.md` | **其余 SKILL.md**（`sdflow-roadmap` 的交棒块） |
| **fix4** | **「任何呈现『怎么开一个 change / 阶段一入口』的行」，全仓 tracked，不限目录** | —— |

**根因不是"再补一处就齐了"，是每轮都用「上一轮被点穿的位置」反推范畴。** 故本轮先定范畴、再扫，
并把这条范畴定义**写进 `DOCS_CARRIERS` 上方注释**（连同三轮教训），下一轮改这片面的人一开文件就看得见。

### 1.2 扫法（可复现）

```bash
# 载体全集 = 全仓 tracked 的 SKILL.md ∪ docs/**（85 份）
git ls-files -z | grep -zE '(SKILL\.md$|^docs/)' | xargs -0 \
  grep -nE 'opsx:(ff|new|propose|explore)|openspec new change|grill-with-docs|/sdflow-spec'

# 补扫：SKILL.md 里的交棒/下游行（措辞可能不带命令名）
git ls-files -z | grep -zE 'SKILL\.md$' | grep -zv '^\.c' | xargs -0 \
  grep -nE '下游|交棒|建议骨架|常规 change|开一个 change|新建 change'

# 补扫：其余 tracked 载体（根 md / openspec/ / snippets），排除 changes/
git ls-files -z | grep -zvE '^(docs/|\.claude/|\.codex/)|SKILL\.md$|^openspec/changes/' | xargs -0 \
  grep -nE 'opsx:(ff|new|propose)|openspec new change'
```

**`grep` 一律不加 `--include`**（记忆 [[rename-string-consumers-span-file-types]]：限定文件类型正是上一次漏网的招式）。

### 1.3 处置判据（两类，逐处归一次）

| 类别 | 判据 | 处置 |
|---|---|---|
| **指示性** | 这一行在**告诉读者去敲哪条命令开一个 change / 走阶段一**。删掉分支限定词后 ⇒ **无条件成立的错误声明** | **改掉 + 上锚** |
| **描述性** | 历史来源标注 · 粒度度量单位 · hook 覆盖面陈述 · 否定式排除 · 已冻结文档 | **登记不改**（§3） |

### 1.4 逐处处置 —— 指示性（全部已修 + 已上锚）

| # | 位置 | 原文（要害） | 改后 | 锚 |
|---|---|---|---|---|
| A | `sdflow-roadmap/SKILL.md`「下游：阶段实施」代码块 | `/opsx:new implement-{roadmap-name}-p1`（**无条件**） | 代码块改 `/sdflow-spec … 〔分支 A · 默认〕`；块下补一句分支 B 沿用 `/opsx:new …〔分支 B〕`，并指回单一源 `generation-process.md` §四 | `("/sdflow-spec implement-", "〔分支 A · 默认〕")` + `("/opsx:new implement-", "〔分支 B〕")` |
| B | `sdflow-roadmap/SKILL.md:394` | 「直写三件套、**不经** `opsx:ff`」——只否定分支 B，分支 A 下不完整 | 「**不经 change 生产路径**（分支 A `/sdflow-spec` · 分支 B `opsx:ff`，两条都不经）」 | `("不经 change 生产路径", "分支 A \`/sdflow-spec\`", "分支 B \`opsx:ff\`")` |
| C | `sdflow-architecture/SKILL.md` frontmatter `description` | 「**不触发**：单次 change 的 spec/design（走 `/opsx:ff`）」——**指路行**，无条件即错 | 「（走 `/sdflow-spec`〔分支 A · 默认〕，未装则 `opsx:ff`〔分支 B〕）」；同时把该句折成**单行**以便单行锚 | `DOCS_CARRIERS["sdflow-architecture/SKILL.md"]` 新增第 2 条 |
| D1 | `sdflow-init/assets/hooks/ff0-branch-guard.py` docstring | 「/opsx:new、/opsx:propose、/opsx:ff、/opsx:onboard **全都殊途同归调** `openspec new change`」 | 清单补 `/sdflow-spec`（分支 A，相位 B ③）+ 一句「两条分支同样受管辖」 | `test_ff0_entry_roster_includes_branch_a` |
| D2 | `sdflow-init/assets/workflow/ff-generation-constraints.md:29` | 同一份清单（canonical 规则文本） | 同上 | 同上 |
| D3 | `sdflow-init/SKILL.md:242` | 同一份清单（skill 说明） | 同上 | 同上 |

**D1–D3 为什么算本票范畴**（而不是"顺手扩"）：这三处清单的**用途**就是回答「我这条路会不会被 FF-0 拦」。
本 change 新增的 `/sdflow-spec` 相位 B ③ 就是 `openspec new change "<name>"`
（实查 `sdflow-spec/SKILL.md:288-291`），**照样被拦**；清单漏它 ⇒ 人读成「分支 A 不过 FF-0」，
与 `docs/workflow-overview.md:115`「相位 B **起手**即过 FF-0 三分支判定 + `openspec new change`」正面矛盾。
本 change 引入了一个新的 `openspec new change` producer 而没回改「producer 全集」清单 —— 与
Important 同源（**扩枚举不回改派生判据**），故属同一片面。

### 1.5 冷验已确认「无需改」的两处（复核成立，未动）

- `sdflow-roadmap/SKILL.md:284/289`（`## 讨论层：三分支路由` 下的「分支 A（默认）：`/opsx:explore`」）——
  该处判的是**讨论工具怎么选**（explore vs wayfinder vs office-hours），与 change 级入口是**两个决策点**，
  且它自带的「分支 A/B/C」是这一节自己的局部命名空间，与阶段一入口的分支 A/B 无关。**未动。**
- `docs/sdflow-fable5/02` 的 skill 总表缺 4 行（`sdflow-spec`/`implement`/`devenv`/`architecture`）——
  冷验已判留置成立（非本票范畴），**未动**。

---

## 2. 三条 Minor

### 2.1 TTL 单边比较（`ff0-branch-guard.py:consume_ack`）

**实证复现**（本轮 TDD 红）：`mtime = now + 300` / `now + 1 年` ⇒ 均 **ALLOW**。
`(time.time() - mtime) <= ACK_TTL_SECONDS` 在 mtime 落在未来时**恒真** ⇒ 「短窗口」退回常驻后门。

**命中场景不需要恶意**：系统时钟回拨 · 从备份/归档恢复保留原 mtime · `rsync -t` 从一台钟更快的机器带回。

**修**：

```python
age = time.time() - mtime
fresh = 0 <= age <= ACK_TTL_SECONDS
```

未来 mtime 与超窗**同等对待**：不放行 **且** 顺手 `os.remove`（沿用既有自愈残留语义）。
docstring 补一段说明「时效比较 MUST 双边」及成因。

**用例**：`test_future_mtime_sentinel_expires_and_is_swept`（参数化 2 例：`+300s` 时钟回拨 / `+1 年` 备份恢复），
两条断言：① 必须 deny ② 哨兵必须被清掉。

### 2.2 三处硬写「10 分钟」（X1 复现）

**先复现 X1**：`ACK_TTL_SECONDS` 600→300，canonical 与 hook 测试**全绿**（见 §4 M2）——三处散文与常量分叉无人守。

**二选一 → 选 ①（删掉数字，让脚本自己报）**。依据：

| 判据 | ① 散文不写数字 | ② 加断言比对三处散文的分钟数 |
|---|---|---|
| 单一源 | 数字**只剩一个出口**（`ACK_TTL_SECONDS`，deny 文案 `// 60` 自报） | 数字仍有 4 份，靠一条测试同步 |
| 失鲜 | 负锚，改常量不失鲜 | 正锚，改常量要同步改 3 处散文 + 测试期望 |
| 本仓先例 | ✅ 记忆 [[rename-string-consumers-span-file-types]]「硬编码数量（『投放面 20 个』实为 18）修法 = **删掉数字让脚本自己报**」；本 change 已用过（`docs/sdflow-fable5/02` 的「15 个 skill」→「全部 skill」） | 无先例 |

**改动三处**：
- `ff0-branch-guard.py` docstring：「压成『一个 10 分钟的窗口』」→「压成一个短窗口」+ 一句
  「窗口长度**只在 `ACK_TTL_SECONDS` 一处**给出，散文 MUST NOT 手抄」
- `ff0-branch-guard.py:ACK_TTL_SECONDS` 注释：「10 分钟已是极宽裕的上界」→「这里取的是一个极宽裕的上界」，
  并标明它是**全仓唯一的窗口长度出口**
- `ff-generation-constraints.md:31`：「哨兵带 **10 分钟时效**」→「哨兵带**有界时效**……窗口长度的**单一源** =
  hook 的 `ACK_TTL_SECONDS`，deny 文案按 `// 60` 自报分钟数，**本文与 hook 散文一律不写死数字**」；
  顺带把 2.1 的**双边判据**写进 canonical（规则文本与 hook 是两处载体，判据变了两侧都要说）

**用例** `test_ttl_window_has_a_single_source`：**负锚**，断言两份载体的散文里不存在 `\d+\s*分钟`，
外加正锚 `"ACK_TTL_SECONDS // 60" in hook`（数字的唯一出口不许消失，否则散文必然重新手抄一份）。
deny 文案里的 `{ACK_TTL_SECONDS // 60} 分钟` 不含字面数字 ⇒ 不被负锚误伤（实测：修后全绿）。

### 2.3 hook 重装与一致性核验

```
$ /usr/bin/python3 sdflow-init/scripts/init.py update --root .
  · ff0-branch-guard.py：脚本已更新 /Users/cheneyzhao/.claude/hooks/ff0-branch-guard.py；已注册（全局）
$ diff ~/.claude/hooks/ff0-branch-guard.py sdflow-init/assets/hooks/ff0-branch-guard.py
IDENTICAL
```

> ⚠️ **副作用登记（未引入，已还原）**：`init.py update` 的托管块注入会把 `<!-- opsx-init:start -->` 后的
> 空行删掉，而 `hack/sync_principles.py` 期望保留 ⇒ `test_sync_principles.py` 当场红。
> 跑一次 `sync_principles.py --apply` 即还原（`git diff CLAUDE.md AGENTS.md` 归零）。
> 这是**两个托管注入器对同一区块的一行空白口径不一致**，与本票无关、**未修**（通则③不加宽）；
> 影响 = 每次 `init update` 后须补跑 `sync_principles --apply`，`setup.sh` 的 `--check` 门会当场抓到，不会静默。

### 2.4 `docs/sdflow-fable5/02` 混基线声明

**判定**：该文档**非冻结快照**（上一轮已确认；且其定位是「模块级参考」，与 `docs/sad/07` 那种自带
「skill 落地后本文冻结」声明的文档不同）⇒ **改声明，不回退数字**（回退 = 让活文档故意留错数字）。

改后文首：

> 数据基线：**混基线，如实登记**——大部分数字取自 git HEAD `fc1b98b` 快照；`add-sdflow-spec` 触及的两片已按**当前 HEAD** 重取：① 阶段一入口（分支 A `/sdflow-spec` / 分支 B 旧三步）；② recorder skill 名册合并后的 `sdflow-issues` 一行（SKILL.md 行数 / 脚本行数 / 用例数）。
> 本文是**活文档**（非冻结快照）：数字与实况漂了以实况为准，重取用 `wc -l` / `pytest <skill>/tests/` 实测，勿凭本文回写代码。

**重取数字复核（当前 HEAD 实测）**：

```
$ wc -l sdflow-issues/SKILL.md                  →  559
$ cat sdflow-issues/scripts/*.py | wc -l        → 1746
$ pytest sdflow-issues/tests/ --collect-only    →  679 tests collected
```
表中 `559 / 1746 / 679` **三个数字全部对上**，声明如实。

**无机械锚，如实登记**：「基线声明是否如实」无确定性信号（要机验就得替全表每个数字各留一份取数脚本 +
基线 SHA 对照，成本远超收益，且本文档正在往「不写死数字」的方向收）——属 adr/0018 的合法语义残余，
**MUST NOT 硬造恒真锚**（本文件模块 docstring 已有明令）。

---

## 3. 描述性引用 —— 逐处登记不改

扫法命中的**全部**其余位置（按理由归组）：

| # | 位置 | 不改的理由 |
|---|---|---|
| 1 | `.claude/skills/openspec-*/SKILL.md` × 11、`.codex/skills/openspec-*/SKILL.md` × 11（`openspec new change` / `/opsx:*` 命令示例） | `CLAUDE.md` 明令：openspec CLI init 生成的官方 skill，**非本仓维护的源，勿在此手改**；改了下次 `openspec init` 即被覆盖 |
| 2 | `docs/sad/00,01,02,03,04` 文首 `> 来源：2026-07-12 /opsx:explore 探讨记录` | **历史来源标注**（考古层），不是入口指路 |
| 3 | `docs/sad/03:22`（L1/L2/L3 层级表 `L3 → opsx:ff`）、`04:60`（空间·交付表 `openspec/changes/`（L3, `opsx:ff`）） | **层级对照表**（「L3 这一层对应哪个产物目录」），非入口指路；且 00–04 整组是 2026-07-12 explore 讨论记录 |
| 4 | `docs/sad/07-devenv-skill-design.md:120`「**下游**：交棒回常规 change 流程（`/opsx:ff`）」 | **文档已按自身头部声明冻结**：「skill 落地后，方法论 live 真相源移交 `sdflow-devenv/references/`；此后本文冻结，修订一律改 references」——`sdflow-devenv/references/`（6 份）已存在。**已核**：live 源 `sdflow-devenv/SKILL.md` + `references/` 里 `grep 'opsx:\|sdflow-spec'` **零命中**，该交棒表述未被带进 live 层 ⇒ 无可修的活载体 |
| 5 | `sdflow-roadmap/SKILL.md:205`、`docs/sdflow-fable5/02:203`、`openspec/roadmaps/mechanical-layer-hardening/roadmap.md:104`（「恰好一次 `/opsx:new` 能完成」「粒度 ≈ 一次 `/opsx:new`」） | **粒度度量单位**，非入口指路。分支 A/B 下「一次 change」的工作量相同 ⇒ 该断言不因分支而**错**（判据 = 删掉分支限定词是否变成错误声明：这里本就没有分支限定词，也没有错误） |
| 6 | `sdflow-roadmap/SKILL.md:160`「OpenSpec 的 `/opsx:new` 很好地承载了单次变更」 | **背景论述**（讲 OpenSpec 这个工具的定位，论证「需要比 change 更大的层级」），非本工作流的入口推荐 |
| 7 | `sdflow-roadmap/SKILL.md:176/289/335/628`、`docs/*` 里的 `/opsx:explore` | **讨论层工具**，非 change 级入口（见 §1.5） |
| 8 | `docs/workflow-overview.md:12/124/125/126/128`、`docs/workflow-console.html:288`、`docs/workflow-map.*` | **已在既有锚覆盖内**：`:247` 带「仅分支 B」锚、`:111`/`### 分支 B` 小节锚、console chips 锚、map 的 7+2 条锚 |
| 9 | `docs/sdflow-context-policy.md:47/259/271/282`、`docs/skill-authoring-best-practices.md:88`、`docs/workflow-skills/setup-matt-pocock-skills.md:83/106` | 把 `grill-with-docs` 当**案例/通则块投放面**讨论，非阶段一入口呈现 |
| 10 | `docs/superpowers/plans/2026-07-01-openspec-review-html-tool.md`（8 处） | **已归档的 superpowers plan**（历史实现记录，含当时的 hook 测试 payload），改它 = 篡改历史记录 |
| 11 | `openspec/CONTEXT.md:108/149`、`openspec/adr/0008,0014,0015`、`openspec/INDEX.md:17`、`openspec/roadmaps/mechanical-layer-hardening/task-log.md`（4 处「下一步」）、`openspec/specs/**`（已全部带分支限定，见 `spec.md:970-1002`） | ADR / CONTEXT / task-log 是**历史决策与日志**；`INDEX.md:17` 描述的是 `ff-generation-constraints` 这份规则的**内容**（它确实是 ff 起手约束）；`specs/` 已在前几轮两分支化 |

> 合计：指示性 **6 处全修**，描述性 **11 组全登记**。

---

## 4. 变异回验（全部实测输出）

**方法**：`rsync` 全仓（排除 `.git`）到 scratchpad `mut/`，逐条变异 → 跑
`pytest hack/tests/test_canonical_entry_sync.py sdflow-init/tests/test_ff0_branch_guard.py -q` → 记**实际红集** → `rsync` 还原。
**判据 = 期望红 ⊆ 实际红**。**基线红集 = ∅**（`55 passed`）。

| 变异 | 期望红 | 实际输出 | 判 |
|---|---|---|---|
| **M1** `fresh = 0 <= age <= TTL` → `fresh = age <= TTL`（回退单边） | `test_future_mtime_sentinel_expires_and_is_swept`（2 例） | `FAILED …[300-略超窗…]` + `FAILED …[31536000-远未来…]`；`2 failed, 53 passed` | ✅ |
| **M2** `ACK_TTL_SECONDS` 600→300（**冷验 X1 原样重跑**） | **∅**（见下注） | `55 passed` | ✅ 符合设计 |
| **M2b** canonical 散文重新手抄「**10 分钟时效**」 | `test_ttl_window_has_a_single_source` | `FAILED …::test_ttl_window_has_a_single_source`；`1 failed, 54 passed` | ✅ |
| **M2c** deny 文案 `{ACK_TTL_SECONDS // 60} 分钟` → `十 分钟`（数字唯一出口消失） | `test_ttl_window_has_a_single_source` | `FAILED …::test_ttl_window_has_a_single_source`；`1 failed, 54 passed` | ✅ |
| **R1** roadmap 交棒块回退成无条件 `/opsx:new …`（**冷验 R1 原样重跑**） | `test_docs_stage_one_carriers_present_branch_a` | `FAILED …::test_docs_stage_one_carriers_present_branch_a`；`1 failed, 54 passed` | ✅ |
| **M3** 删掉交棒块下方的分支 B 注 | 同上 | `1 failed, 54 passed` | ✅ |
| **M4** roadmap:394 回退成「**不经** `opsx:ff`」 | 同上 | `1 failed, 54 passed` | ✅ |
| **M5** architecture `description` 回退成「（走 /opsx:ff）」 | 同上 | `1 failed, 54 passed` | ✅ |
| **M6a** hook docstring 入口清单去掉 `/sdflow-spec` | `test_ff0_entry_roster_includes_branch_a` | `FAILED …::test_ff0_entry_roster_includes_branch_a`；`1 failed, 54 passed` | ✅ |
| **M6b** canonical 规则入口清单去掉 `/sdflow-spec` | 同上 | `1 failed, 54 passed` | ✅ |
| **M6c** `sdflow-init/SKILL.md` 入口清单去掉 `/sdflow-spec` | 同上 | `1 failed, 54 passed` | ✅ |

> **M2 期望红为什么是 ∅**：本轮对 Minor 2 选的是修法 ①（**删掉散文里的数字**），
> 而不是修法 ②（加断言比对）。修法 ① 之后 `ACK_TTL_SECONDS` **就是这个数的唯一定义处**，
> 没有第二份口径可以与它分叉 —— 「改常量不红」在修法 ① 下**是正确行为**，不是漏网。
> 真正要证的是「散文不能重新长出第二份数字」和「数字的唯一出口不能消失」，
> 由 **M2b / M2c** 两条证（皆红）。**这两条替代 M2 承担 X1 的守卫职责。**
> 无关红：0 条（每次变异只红被点名的用例，其余 53–54 全绿）。

---

## 5. 全量验证

**先 `git add -A` 再跑全量**（`test_downstream_reference_guard` 扫的是 git tracked 文件，
未 add 的新报告它看不见 ⇒ 跑绿后一 commit 就红，本仓已连续两次踩坑）。

```
$ bash setup.sh
  [sync_principles]     ✅ 19 个投放面全部与真相源一致
  [gen_workflow_guide]  ✅ WORKFLOW-GUIDE.md 与单一源一致
  [async-branch-parity] ✅ 2 处 async host 调度段逐字节一致

$ /usr/bin/python3 hack/sync_principles.py --check
  [sync_principles] ✅ 19 个投放面全部与真相源一致

$ /usr/bin/python3 -m pytest -q          （仓根全量，跑了两遍，结果一致）
  2707 passed, 11 skipped, 3 xfailed in 268.39s
```

**与基线（fix3 的 `2704 passed, 10 skipped, 3 xfailed`）对账**：

| | 基线 | 本轮 | 差 |
|---|---|---|---|
| collected | 2717 | 2721 | **+4 = 本轮新增用例数**（TTL 未来 mtime ×2 参数化 · `test_ttl_window_has_a_single_source` · `test_ff0_entry_roster_includes_branch_a`） |
| passed | 2704 | 2707 | +3 |
| skipped | 10 | 11 | +1 |

**+1 skipped 不是回归，是已登记的环境敏感用例**（两跑均如此，`-rs` 实证）：
`test_outside_voice_utf8.py:855`（M3 满盘变异体在本次 ramdisk 上先撞到 coreutils 自己的满盘诊断，
未能建立可区分 M3 的前提）与 `test_outside_voice_child_lifecycle.py:436`（高频混合信号风暴本轮未复现）
两条都**自带 docstring 声明「常 skip，MUST NOT 因此删除」**，本轮其中一条翻到 skip。
任务单点名的 `test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`
**本轮两跑皆 passed**。**红集 = ∅。**

## 6. 改动清单

| 文件 | 改了什么 |
|---|---|
| `sdflow-init/assets/hooks/ff0-branch-guard.py` | `consume_ack` 双边时效 + docstring（时效双边判据 · 窗口长度单一源 · 入口清单补 `/sdflow-spec`）+ 常量注释去数字 |
| `sdflow-init/assets/workflow/ff-generation-constraints.md` | FF-0 块：入口清单补 `/sdflow-spec`；残留令牌段去掉「10 分钟」、写明单一源 + 双边判据 |
| `sdflow-init/SKILL.md` | FF-0 硬强制段的入口清单补 `/sdflow-spec` |
| `sdflow-roadmap/SKILL.md` | 「下游：阶段实施」交棒块两分支化；`:394` 直写路径两分支都点名 |
| `sdflow-architecture/SKILL.md` | frontmatter `description`「不触发」清单两分支化（并折成单行以便单行锚） |
| `docs/sdflow-fable5/02-module-reference.md` | 文首基线声明改成如实的混基线登记 + 活文档声明 |
| `sdflow-init/tests/test_ff0_branch_guard.py` | +1 参数化用例（未来 mtime ⇒ DENY 且被清） |
| `hack/tests/test_canonical_entry_sync.py` | `DOCS_CARRIERS` 范畴注释重写（三轮教训 + 扫法）；+`sdflow-roadmap/SKILL.md` 3 锚、+`sdflow-architecture` 1 锚；+`FF0_ROSTER_CARRIERS` 与 `test_ff0_entry_roster_includes_branch_a`；+`test_ttl_window_has_a_single_source` |
