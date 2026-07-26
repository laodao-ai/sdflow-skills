# Task 2 · fix 轮次 3 —— 逃生口两步化 + 残留令牌有界化 + 锚「逐处」补齐

**R-ID**：SA-05 · SA-11 · SA-14（承 `task2-canonical-sync-fix1/fix2.md`，**不覆盖前几轮报告**）
**基线 HEAD**：`ffd7239`
**结论**：`DONE`（1 Critical + 2 Important + 2 Minor 全部落地；变异回验 **43/43**（A6 变异本身设计有误，
按真实形态 A6′ 重跑后 ✅）；全量 **2704 passed**）

---

## 零、总览

| # | 条目 | 处置 | 关键证据 |
|---|---|---|---|
| 1 | 🔴 hook 拒掉自己开的逃生口（死循环）+ 残留令牌 = 常驻后门 | **文案两步化** + **哨兵加有界时效（10 min，过期即删）** + docstring 假断言改掉 | A1/A2/A3/A4/A5/A6′/A7/A8 全红 |
| 2 | 下游 gitignore 缺哨兵条目 | **加了**（上一轮的不做理由被推翻，见 §二） | B1/B2/B3 全红 |
| 3 | `DOCS_CARRIERS` 只扩「份」没扩「处」 | 补 **13 条**逐处锚，并把**每一份每一处**过了一遍 | C1–C3 + D1–D12 全红 |
| 4 | 仓 `README.md` 未纳入期望集 | 纳入（3 处锚） | D9/D10/D11 全红 |
| 5 | `fable5/02` 旧 skill 名 + 写死计数 | 清干净（全量 grep 复核 → `CLEAN`） | §五 |
| + | `sdflow-architecture/SKILL.md` 交棒行无条件 `/opsx:ff`（**超出点名范围，自扫发现**） | 修 + 上锚 | D12 红 |

**全量验证**：`/usr/bin/python3 -m pytest -q` → **2704 passed, 10 skipped, 3 xfailed**（较基线 +6 用例）；
`bash setup.sh` 三门全绿；`hack/sync_principles.py --check` ✅。
已知抖动用例 `test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret` **本轮通过**。

---

## 一、🔴 Critical —— 逃生口自锁死循环 + 残留令牌

### 1.1 复现（TDD 起手，先红）

新增 3 条用例，**改代码前实跑全红**：

```
$ /usr/bin/python3 -m pytest sdflow-init/tests/test_ff0_branch_guard.py -q
FAILED …::test_escape_hatch_command_in_deny_reason_is_itself_allowed
FAILED …::test_two_step_escape_hatch_runs_end_to_end
  E  AssertionError: 第一步 touch 被 deny ⇒ 逃生口不可用
FAILED …::test_stale_sentinel_expires_and_is_swept
  E  AssertionError: 过期哨兵仍然放行 —— 残留令牌成了常驻绕过口
3 failed, 20 passed
```

### 1.2 修法 ① —— 文案两步化

deny 文案原给一条 `touch <token> && openspec new change <name>`。PreToolUse 在命令**执行前**判定
⇒ 判定那一刻 touch 还没跑、哨兵不存在 ⇒ 本 hook 把这条命令连同 touch 一起 deny。改为两条分开给：

```
  c) 就地继续 —— 人明确拍板后，由**人**分两步敲（本守卫在命令执行【前】判定，
     写成 `touch … && openspec …` 一条会连同 touch 一起被 deny）：
       touch <abs>/openspec/.ff0-ack
     然后重跑：
       openspec new change <name>
     （该哨兵用后即焚：守卫读到就删，只对下一次调用生效；
       且 10 分钟内未被消费即失效并自动删除）
```

**「touch 本身会不会被拦」已实测确认**：`NEW_CHANGE_RE` 只匹配 `openspec new change`，
裸 touch 命令不触发 → 放行。这一条不是推理，是 `test_escape_hatch_command_in_deny_reason_is_itself_allowed`
**把文案里的 touch 行原样喂回 hook 跑一遍**得到的（锚打在「文案给的命令自己能不能过」上，
而不是打在某个字面量上 —— 换文案写法也守得住）。

### 1.3 修法 ② —— 残留令牌：④ 五问 + 三镜（本条按题面要求书面写满）

| 问 | 答 |
|---|---|
| **根因** | 哨兵是文件系统上的**持久状态**，而「创建」与「消费」之间没有任何约束。人若在**自己的终端**里敲 `openspec new change`（本 hook 根本不触发），或 touch 完改主意，令牌就永远留在盘上。 |
| **概率** | **中**。文案改成两步后，正常路径（在 Claude 里重跑）会消费掉它；但「人习惯自己开终端跑 openspec」是常见操作，且 touch 完改主意零成本。 |
| **影响（三镜）** | **系统镜**：残留 = 下一次**任意** change 的分支③被静默放行一次，守卫在那一次完全失效；叠加 `checkpoint-commit.sh:51` 的无条件 `git add -A`，还会被提交入库 ⇒ **每个 clone 都带一个常驻绕过口**。**用户镜**：人完全不可感知（无任何提示，就是"守卫这次没拦"）。**开发循环镜**：排查成本高——现象是"FF-0 莫名没生效"，而原因在几天前的一次 touch 上。**主次：系统镜为主**（正确性面），用户镜次之。 |
| **完美成本** | 完美 = 令牌绑定 (change 名, 分支, 时刻) 并签名校验。**成本过高且买不到东西**：本 hook 的信任级别从来就分不出人和模型（docstring 已如实写明），加密强度救不了一个非安全边界的守卫；且引入解析/存储/校验三个新面。 |
| **简化方案** | **mtime 有界时效**：`ACK_TTL_SECONDS = 600`，超窗即视为失效**并顺手删除**。零解析、语义面有界（**一个时间差**，符合基准 5）、顺带自愈残留。代价 = 人 touch 完拖过 10 分钟要重 touch（deny 文案已明写该时限）。 |

**推荐 = 题面给的方向（有界时效），照做。** 备选 A（只如实写明、不加时效）被否：一行代码就能把
「常驻」压成「10 分钟窗口」，不做没有理由。备选 B（撤逃生口）题面已否，同意（砍 SA-05 范围）。

⚠️ **窗口内的残留仍是真洞** —— 本 hook **MUST NOT 声称堵死它**。docstring 里那句
**「令牌不会残留成后门」是假断言，已删除**，改为原样写明残留场景与两条有界缓解。
`test_ff0_lingering_sentinel_is_declared_and_time_bounded` 机械守它不复活。

### 1.4 落点

| 载体 | 改了什么 |
|---|---|
| `ff0-branch-guard.py` docstring | 新增两段：〔逃生口必须是两步〕〔残留令牌是真实的绕过口 —— 如实写明，只做有界压缩〕；判据措辞改为「在不在、**且够新**」 |
| `ff0-branch-guard.py:ACK_TTL_SECONDS` | 新常量 600s + 理由注释 |
| `ff0-branch-guard.py:consume_ack()` | 先 `os.stat` 取 mtime 判鲜度 → 再 `os.remove`；**过期照样删、只是不放行** |
| `ff0-branch-guard.py:deny()` 分支③文案 | 两条命令分开给 + 写明"为什么不能写成一条" + 时限 |
| `assets/workflow/ff-generation-constraints.md:30` | 同步两步化 + 新增一整段「残留令牌是真实的绕过口，如实登记」（canonical 单一源不分叉） |

### 1.5 hook 重装到全局（执行契约第 4 条）

```
$ /usr/bin/python3 sdflow-init/scripts/init.py update --root .
  · ff0-branch-guard.py：脚本已更新 /Users/cheneyzhao/.claude/hooks/ff0-branch-guard.py；已注册（全局）
$ diff ~/.claude/hooks/ff0-branch-guard.py sdflow-init/assets/hooks/ff0-branch-guard.py
  → 无差异
```

`init.py update` 照例把 `CLAUDE.md`/`AGENTS.md` 托管块刷成少一个空行的形态，跑
`hack/sync_principles.py --apply` 回填后两文件 `git status` **干净**（净 0 改动）。

---

## 二、Important —— 下游 gitignore 缺哨兵条目

**上一轮不做的三条理由，本轮逐条查证后全部推翻**（题面判为「拿现状反驳目标 · 通则③」，**成立**）：

| 上一轮理由 | 查证结果 |
|---|---|
| ①「题面只问本仓 `.gitignore`」 | 那是**上一轮的题面范围**，不是目标态。hook 是**全局**安装、拦**所有**项目 ⇒ 目标态下每个消费仓都会产生这个哨兵。 |
| ②「`**/.outside-voice/` 也只在本仓」 | 拿现状当先例。而且不同构：outside-voice 目录是调试留档，哨兵是**绕过口**。 |
| ③「会改 8 个逐字节断言并触碰 spec 锁定的 SW-RI-2」 | **实测**：只撞 4 个（`[existing/user-bytes] × [init/update]`）。**且不与 SW-RI-2 冲突** —— 我打开 `openspec/specs/spec-workflow/spec.md:1243` 逐字读过：它要求「幂等合并 `/openspec/issues/.recorder.lock`；已有一条时 byte-noop，缺项时仅追加完整行，重复条目 fail-closed，其它 ignore bytes 必须保留」——**约束的是每条条目的合并语义，从未说 canonical 里只许有那一条**。`merge_runtime_gitignore()` 本身就是按 `entries` 列表写的多条目实现，一行都不用改。**故不 BLOCKED。** |

**修法**：
- `assets/snippets/runtime-gitignore.txt` +1 行 `/openspec/.ff0-ack`。
- `test_runtime_gitignore.py` 的 4 处逐字节断言**换判据、不放松**：由「结果 == 写死的那串 bytes」
  改为三条 canonical 驱动的断言 —— ① 用户既有 bytes 是结果的**逐字节前缀**；② 追加段 **==** 恰好那些
  缺失的 canonical 条目、各一行、按 canonical 顺序；③ **每条** canonical 条目在结果里**恰好一条**。
  比原断言更强（原来只钉了一条条目），且新增运行期产物不再连带撞红。
  变异 **B3**（`entries[:1]`，即"只合并第一条、第二条静默丢"）→ 该用例红，证明它真的守住了新条目。
- 新增 `test_ff0_sentinel_is_ignored_in_consumer_repos`：canonical snippet 与本仓 `.gitignore`（dogfood）
  都必须有该条目。

---

## 三、Important —— 锚「逐处」补齐（面治）

### 3.1 根因（题面判语成立）

`DOCS_CARRIERS` 上一轮从 4 份扩到 8 份，但**每份仍只挂 1–4 条锚**，而这些文档里**分支表述有更多处**。
典型「扩枚举不回改派生判据」——枚举的粒度（份）与文件自述的判据粒度（**处**）不一致。
已把这条判据写进模块 docstring（含 fix2 的实测教训），后来者照抄不会再错。

同时明确了「一处」的**两个范畴**（原先只想到第一种）：
① 呈现阶段一入口的行；② **带分支限定词的条件表述** —— 删掉限定词后它会变成**无条件成立的错误声明**
（`〔仅分支 B〕`、`〔分支 B〕问题清晰否`…）。第二类正是 fix2 修 grill-with-docs 时命名的形态，
但当时没把它推广到别的载体上。

### 3.2 全量扫法（不加 `--include`）

```bash
# 每份载体逐行列出全部分支表述
for f in <DOCS_CARRIERS 全部 + README.md>; do grep -n "分支 A\|分支 B" "$f"; done
# 再全仓找漏网载体
grep -rln "opsx:ff\|grill-with-docs\|explore *→ *ff\|阶段一" --exclude-dir=.git .
```
第二条网出 90 个文件，逐个归类后新捞到 **1 个真载体**：`sdflow-architecture/SKILL.md:484`
（交棒行原文 `下游：/opsx:ff <名>` —— 分支 A 下无条件成立即错，与 grill-with-docs 同形态）。
其余（`reference/PRD_vs_Spec.md`、`Spec_Quality_Collaboration.md`、`INDEX.md` 表行、
`prompts/step2-ff.md`、`docs/sad/*`、roadmaps、archive）经逐条查看均**不声称阶段一入口/位置**，不入网。

### 3.3 补的锚（13 条新增，逐份逐处过了一遍）

| 载体 | 新增锚（处） |
|---|---|
| `docs/workflow-overview.md` 4→9 | `:62` 三阶段画像表 · `:120` 分支 B 深度约束 · `:247` 黑盒 skill 表 · `:301` §7 explore 条 · `:303` §7 grill 条 |
| `docs/workflow-map.md` 2→7 | `:21` explore 行分支限定 · `:24` propose 行分支 A 标 · `:25` 旧入口分支 B 标 · `:30` 人类门①两分支 · `:73` 阶段表 explore 行 |
| `docs/workflow-skills/grill-with-docs.md` 2→3 | `:5` 文首分支 A 排除句 |
| **`README.md`（新载体）** | 出口序列 `/sdflow-spec` 行 · 旧三步注 · Skills 列表「单一入口」行 |
| **`sdflow-architecture/SKILL.md`（新载体）** | §5.2 交棒行 |
| `docs/workflow-map.html` · `console.html` · `fable5/README|01|02` | 逐处复核 —— **既有锚已覆盖全部处**，无新增（E7–E15 变异确认） |

**一处文档结构微调**：`docs/workflow-map.md` ASCII 轨原本把 `/opsx:ff / :new` 和 `〔分支 B〕` 拆两行，
而裸 `〔分支 B〕` 这一行会被同文件阶段表的行满足（= 恒真弱锚）。合并成一行
`/opsx:ff / :new〔分支 B〕` 后可单行定位。**改文档只为让锚打得准，未改语义。**

---

## 四、变异回验（43 条，工作树全程未被触碰）

方法：`rsync -a --exclude .git` 到 scratchpad 副本跑 `mutate3.py`，逐条变异 → 跑
`test_canonical_entry_sync.py` + `test_ff0_branch_guard.py` + `test_runtime_gitignore.py`
→ 记**实际红集** → 还原。判据 = **期望红 ⊆ 实际红**。基线红集 = ∅。

### 4.1 hook / gitignore（A、B 组）

| 变异 | 期望变红 | 实际 | 结果 |
|---|---|---|---|
| A1 deny 文案退回一行 `touch … && openspec …` | escape_hatch_command_in_deny_reason_is_itself_allowed + two_step_..._end_to_end | 同 | ✅ |
| A2 hook 侧删「两步」禁令 | escape_hatch_is_two_steps_in_both_carriers | 同 | ✅ |
| A3 规则文本侧删「两步」禁令 | 同上 | 同 | ✅ |
| A4 取消哨兵时效（`fresh = True`） | stale_sentinel_expires_and_is_swept | 同 | ✅ |
| A5 过期哨兵不放行但**也不删** | 同上 | 同 | ✅ |
| A6 `ACK_TTL_SECONDS` 常量消失 | lingering_sentinel_is_declared_and_time_bounded | **10 个行为用例红，该用例未红** | ❌ **变异设计有误** |
| **A6′** 同一变异改为**全量重命名** | 同上 | 同 | ✅ |
| A7 docstring 复活「令牌不会残留成后门」 | lingering_sentinel_is_declared_and_time_bounded | 同 | ✅ |
| A8 规则文本删「残留令牌是真实的绕过口」 | 同上 | 同 | ✅ |
| B1 canonical snippet 撤掉哨兵条目 | ff0_sentinel_is_ignored_in_consumer_repos | 同 | ✅ |
| B2 本仓 `.gitignore` 撤掉（dogfood 断链） | 同上 | 同 | ✅ |
| B3 merge 只合并首条 canonical 条目 | run_init_and_update_use_canonical_runtime_merge | 同 | ✅ |

> **A6 为什么算变异设计有误、不算锚失效**：我写的是 `replace(..., 1)`，**只改了定义行**，
> 引用处还叫旧名 ⇒ hook 运行期 `NameError` ⇒ 10 个行为用例红（变异被**更响地**抓到了），
> 但按字面 grep 的那条锚仍能找到旧名。这不是「常驻绕过口没人守」，是我造了个**语法上不自洽**的
> 变异体。改成真实形态（全量重命名 → hook 仍能跑，只是 TTL 这个名字不在了）后 **A6′ 唯一命中目标用例**。
> **如实登记这个次序，未把 A6 的结果修饰成通过。**

### 4.2 逐处锚（C、D、E 组 —— 全部期望 `test_docs_stage_one_carriers_present_branch_a`，全部 ✅）

| 组 | 变异 | 结果 |
|---|---|---|
| **C（冷验点名的 3 处漏网格）** | C1 overview:62 画像表回退 · C2 overview:247 黑盒表回退成无条件 · C3 map.md 人类门①两分支注删除 | ✅✅✅ |
| **D（本轮新加的其余逐处锚）** | D1 overview 分支 B 深度约束句删 · D2/D3 §7 两条去掉分支限定 · D4/D5/D6 map.md ASCII 轨三处分支标删 · D7 map.md 阶段表 explore 行去限定 · D8 grill-with-docs 文首分支 A 排除句删 · D9/D10/D11 README 三处 · D12 architecture 交棒行回退成无条件 `/opsx:ff` | 12/12 ✅ |
| **E（存量锚回归复验）** | E1–E4 overview 四处 · E5/E6 map.md 两处 · E7/E8 map.html · E9/E10 console.html · E11 fable5/README · E12–E14 fable5/01 三处 · E15 fable5/02 · E16/E17 grill-with-docs 两处 | 17/17 ✅ |

原始输出留在 scratchpad `mutation-results-fix3.json`（不入库）。

---

## 五、Minor —— `docs/sdflow-fable5/` 旧 skill 名 + 写死计数

**先全量 grep（不加 `--include`）确认残留范围**，再一次清干净：

| 位置 | 原文 | 改法 |
|---|---|---|
| `02:1` 标题 | 「15 个 skill 的设计与实现」 | 「全部 skill 的设计与实现」 |
| `02:3` 导读 | 「15 skill 总表」 | 「skill 总表」 |
| `02:15` 仓库解剖树 | `<15 个 skill 目录>/` | `<各 skill 目录>/` |
| `02:27` 两类 skill 表 | `sdflow-buglist · sdflow-todolist · sdflow-issues · …（合计 ≈374 用例）` | `sdflow-issues · sdflow-init · sdflow-retro · sdflow-maintain · sdflow-architecture · sdflow-devenv`（后两个是实际的数据类 skill，原表也漏了）；用例数改为「以 `pytest <skill>/tests/` 实测为准，**勿在此写死**」 |
| `02:61` 小节标题 | 「## 2. 15 个 skill 总表」 | 「## 2. skill 总表」 |
| `02:71-73` 总表 | buglist / todolist / issues 三行 | 合并为一行 `sdflow-issues`，数字**实测重取**（`wc -l SKILL.md`=559、`scripts/*.py`=1746、`pytest --collect-only`=679） |
| `02:290-291` 拓扑图 | `IS --- BL["sdflow-buglist"]` / `TL["sdflow-todolist"]` | 删两节点，`IS` 改为 `sdflow-issues（bug/todo 两池，单一触发面）` |
| `README:11` | 「15 个 skill 各自怎么设计」 | 「每个 skill 各自怎么设计」 |
| `01:28` | 「自建的 15 个 `sdflow-*` skill」 | 「自建的一组 `sdflow-*` skill」 |

复核：`grep -rn "15 个\|15 skill\|sdflow-buglist\|sdflow-todolist" docs/sdflow-fable5/` → **CLEAN**。
`sdflow-issues/tests/test_downstream_reference_guard.py` 的 allowlist 含 `docs/**`（**允许**保留旧名，
不是**要求**），故本次刷新不与它冲突 —— 已确认全量绿。

---

## 六、全量验证

```
$ /usr/bin/python3 -m pytest -q
2704 passed, 10 skipped, 3 xfailed in 267.66s        （基线 2698 → +6 新用例）
$ bash setup.sh
  [sync_principles] ✅ 19 个投放面全部与真相源一致
  [gen_workflow_guide] ✅ WORKFLOW-GUIDE.md 与单一源一致
  [async-branch-parity] ✅ 2 处 async host 调度段逐字节一致
$ /usr/bin/python3 hack/sync_principles.py --check   → ✅
$ diff ~/.claude/hooks/ff0-branch-guard.py sdflow-init/assets/hooks/ff0-branch-guard.py  → 无差异
```

新增用例 6 条：`test_ff0_branch_guard.py` +3（20→23）、`test_canonical_entry_sync.py` +3（25→28）。

---

## 七、改动文件清单（`git diff --stat` 亲验）

```
M docs/sdflow-fable5/01-goals-and-rationale.md        （写死计数）
M docs/sdflow-fable5/02-module-reference.md           （旧 skill 名 + 写死计数）
M docs/sdflow-fable5/README.md                        （写死计数）
M docs/workflow-map.md                                （ASCII 轨两行合一，便于单行定位）
M hack/tests/test_canonical_entry_sync.py             （25 → 28 用例；DOCS_CARRIERS 8 → 10 份、锚 +13 处）
M sdflow-architecture/SKILL.md                        （§5.2 交棒行两分支化）
M sdflow-init/assets/hooks/ff0-branch-guard.py        （两步文案 + TTL + docstring 假断言）
M sdflow-init/assets/snippets/runtime-gitignore.txt   （+/openspec/.ff0-ack）
M sdflow-init/assets/workflow/ff-generation-constraints.md  （两步 + 残留令牌如实登记）
M sdflow-init/tests/test_ff0_branch_guard.py          （20 → 23 用例）
M sdflow-init/tests/test_runtime_gitignore.py         （4 处逐字节断言换 canonical 驱动判据）
```

`CLAUDE.md` / `AGENTS.md` 最终 `git status` **干净**（`init.py update` 的托管块抖动已 `sync_principles --apply` 回填）。
`openspec/changes/add-sdflow-spec/` 的 proposal / design / specs / tasks.md / superpowers-plan.md **一字未动**。

---

## Concerns

### C1（须人知情）`fable5/02` 的「skill 总表」**仍缺 4 个 skill**

清完旧名后该表列的是 issues / roadmap / spec-review / ship / code-review / done / embedded-test-sop /
retro / maintain / init / upgrade / openspec-upgrade + bundle tools 行，
**缺 `sdflow-spec`、`sdflow-implement`、`sdflow-devenv`、`sdflow-architecture` 四行**。

**未补**，理由：题面点名的是「旧 skill 名 + 写死计数」两类残留，补 4 行属**第三类**（内容补全），
且需为每行取行数/脚本行数/用例数（该文档整体标注「数据基线 git HEAD `fc1b98b`」，
只给 4 行取当前数会造成混基线）。按通则③「不加宽」留给人拍板：
**若要做，正解是把整张表的数字一次性重取 + 在表头写明新基线 HEAD**，是一次独立的文档交付。

### C2 `ACK_TTL_SECONDS = 600` 是**我定的**数，无实测依据

依据只有「人 touch 完立刻重跑是秒级动作」这一常识判断。它是**可调的单一常量**、
deny 文案会把时限直接告诉人、过期只是要求重 touch（无数据损失）⇒ 判为低风险。
若人实际使用中觉得窗口太短，改一个数字即可。

### C3 承 fix1/fix2 的既有 Concern，全部仍然成立

- 默认分支探测让全局 hook 拦截面变宽（fix1 C1）；`init.defaultBranch` 是次优信号（fix1 C2）。
- Minor `:113`（名为 `trunk` 的 feature 分支无逃生口）**仍未修、仍不建议修**（fix2 §四 / C1：
  修它必须牺牲「ack MUST NOT 解锁保护分支」这条 SA-05 不变量）。
- `tasks.md` 覆盖图仍标「人核 ❌」而实现已机械化（fix1 C3）——本轮又把 README、
  `sdflow-architecture/SKILL.md` 与 13 处逐处锚也机械化了，**未修改 `tasks.md`**（设计门产物），
  应在 `sdflow-done` 的 archive 阶段一并订正。
