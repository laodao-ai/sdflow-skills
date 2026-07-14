# tasks — add-sdflow-devenv

> 〔spec-review-amendment · round-3 · 2026-07-13〕本表已按 round-3 设计门（总则 §0.0「机械层防漏，不防伪」）**整体重写**。
> **本次删除的机制**（前一版任务组已作废，见 `design.md`/`docs/sad/07-devenv-skill-design.md` 附录 A13–A20）：
> negative control 作为 `verified` 的定义 · 测试计数门槛（`collected≥1`）· `isolate` 字段 · `expected-failure predicate` ·
> `kind → 策略 dispatch` · runner 白名单 · **`owned_by` 字段（整个删除，"运行时派生"的锚不存在）** ·
> **cleanup ledger 自动记账（整个删除，同上）** · **`confirm-lane` 的调用者身份保证（删除，agent session 里模型是唯一执行者，
> 且本就不必防）** · **`method_digest` 的"smoke 可达的 harness/fixture"覆盖（删除，"可达"需跨语言 import 图分析，
> 零依赖做不到；改为 lane 显式声明的 `fixtures[]` 清单）**。
>
> 〔**round-4 · 2026-07-14 · 实现期修正**〕**再删一个机制**（见 `07` 附录 **A21**）：
> **`source.digest` 字段 + 「按 `selector` 用 parser 重定位 make target、提取 recipe body 做 digest」+ 其衍生的
> 「digest 规范化规则按文件类型分治」——三者一并删除。** 理由：GNU make **语法面无界**（`ifeq`/`define`/双冒号/
> 模式规则/续行/内联 `;`/target-specific 变量…），手搓解析器必然带一堆「语法不支持」的罢工分支，而**它罢工一次就击穿
> 「不管什么项目都能给一份三层框架」这条核心承诺**；且它精确防的是「操作者偷改 recipe 不重跑」（§0.0 已宣告此人不存在），
> 却完全不覆盖真正高频的「被测实现改了」。**A20（手搓 Markdown 解析器）的理由逐字适用，只是当时没往这边看。**
> **替代**：`source: {file, kind, selector}` 无 digest；时效锚 = **`evidence.file_digests`**（`source.file` + `smoke` +
> 声明的 `fixtures[]`，**逐文件原始字节 sha256，零规范化**——不提取 recipe ⇒ 无缩进噪声 ⇒ 规范化规则整条消失）。
> **实现期代价（务必记住）**：Task「digest」三轮补丁螺旋，脚本 261→562 行、测试 304→753 行，每轮 review 都挖出一个新的
> make 语法角落。**无界语法面上补丁循环不会自己收敛——这本身就是「该删掉它」的信号。**
>
> **⚠️ 返工序（A21 后，实现进度的实际状态）**：Task 1/2 的产物**不受影响**；**Task 3 与 Task 4 的已提交代码需返工**，
> 且 **MUST 先于 Task 5**（Task 8 的 `verify-lane`、Task 11 的 lint 都依赖它们的新接口）：
>
> | 文件 | 返工 |
> |---|---|
> | `scripts/devenv_digest.py` | **整体重写**：562 → ~60 行。删 `find_make_target` / `digest_make_recipe` / `method_digest` / 7 个 `MakefileUnsupported` 分支；改为 `file_digest` / `lane_file_digests` / `stale_files`，**零 make 知识** |
> | `tests/test_digest.py` | **整体重写**：753 → ~180 行。**新增两条 A21 红线**：`test_complex_makefile_never_raises`（核心承诺守卫）· `test_no_make_parsing_symbols_exist`（防 parser 从后门爬回来） |
> | `scripts/devenv_schema.py` | evidence 必填键 `method_digest` → **`file_digests`（dict）+ `method_at_verify`（str）**；加「`method` != `method_at_verify` ⇒ 报验证方法已改动」 |
> | `tests/test_schema.py` | 同步 evidence fixture |
>
> **`method_at_verify` 是 A21 的面治补口，不是新功能**——见 4.3。旧 `method_digest` 覆盖了「命令字符串」这一面，
> 换成只认文件的 `file_digests` 后它掉出去了。**拆错的机制时 MUST 接住它原本覆盖的合法面**（基准 3）。
> Requirement 追溯：`R-*` = `specs/devenv-provisioning/spec.md`（21 条 Requirement，见下方图例）；
> `A-1` = `specs/architecture-design/spec.md`；`M-1` = `specs/maintain-scan/spec.md`。
> 纪律：改 `scripts/` 必跑 `tests/`。复选框在 `/sdflow-done` 的 archive 阶段勾——**实现期 MUST NOT 勾**。

**Requirement 简写图例**（对应 `specs/devenv-provisioning/spec.md` 的 21 条 Requirement 标题）：

| 简写 | Requirement 标题 |
|---|---|
| R-PF | preflight 两级与三模式分流 |
| R-FACT | 事实采集与时序纪律 |
| R-STRAT | 测试三层框架——三层必答，无一层可留白〔核心承诺〕 |
| R-LANE | 泳道设计候选与拍板 |
| R-VERIFY | 验证方法——模型研究提方案，人拍板；尽可能跑一遍确认〔核心〕 |
| R-TRISTATE | 泳道三态与渐进 DoD |
| R-EXEC | 状态迁移的执行者分工——证据只能由执行者本人写 |
| R-BOUND | 执行边界与「不伤害」 |
| R-PATH | 路径边界校验——所有模型提供的路径 MUST 经 containment 检查 |
| R-APPEND | 落地物追加边界——skill 是追加者非拥有者 |
| R-RELOC | 归位模式——素材盘点、判归属、删源 |
| R-DELGUARD | 删源护栏——逐文件校验与可恢复备份 |
| R-GATE | 冷审与人门 |
| R-TXN | ③-pre 否决的回退——touched-files 事务 journal |
| R-MAINT | lint 的触发点——挂 `sdflow-maintain` |
| R-LINT | 机械 lint——只查诚实（防漏），不查质量（防伪） |
| R-DATA | 数据模型——两份 JSON 侧文件与 digest 出处锚 |
| R-DOC | 文档渲染与两文档边界 |
| R-MARKER | 入口托管注入使用独立 marker |
| R-CONC | 并发安全写入 |
| R-TRIG | 触发分工与前置声明 |

## 0. 实现前的唯一前置

> ⚠️ **原「第 0 组 = 实现前置」已作废（鸡生蛋）**：它要求「先验证模型能否为三层提出像样的验证方法」**才准动工**——
> 但这件事**只能靠跑这个 skill 才能验证**，而 skill 还不存在。原 0.3「证伪就暂停 change」是一个**永远无法被证伪的前置条件**。
> **正确位置 = 实现后的首个真实试点（验收，见第 12 组）。**〔操作者拍定：「需要先把 skill 做出来，我再拿项目测试」〕

- [ ] 0.1 **开发 checkout 跑一次 `bash setup.sh`**——本 change 改 skill 源 + `assets/`，**不重跑就测不到**（CLAUDE.md adr/0005 dev/runtime checkout 纪律）

## 1. 骨架与 schema

- [ ] 1.1 建 `sdflow-devenv/` 目录骨架（`SKILL.md` + `scripts/` + `references/` + `tests/`）
- [ ] 1.2 `scripts/devenv_schema.py`：**`.devenv-lanes.json` schema**（标准库 `json`，**零第三方依赖**）——lane 含
  `id` / `layer`（unit\|integration\|e2e）/ `kind`（external-dep\|ui\|lang-bridge\|hardware\|pure）/
  `status`（planned\|scaffolded\|verified）/
  **`verification{method,executor,strength,why_not_scriptable,human_steps,evidence{at,at_commit,exit,output_digest,file_digests,method_at_verify,confirmed_what,attested_by}}`** /
  `source{file,kind,selector}`（**无 `digest`**〔A21〕）/ `smoke` / **`fixtures[]`** / **`env[]`** / `deps[{name,kind}]`
  （**`deps` 不含 `owned_by`**）/ `covers` / `blocked_by`〔R-DATA〕
- [ ] 1.3 `scripts/devenv_schema.py`：**`.devenv-strategy.json` schema**——`layers.{unit,integration,e2e}` 各含五槽
  `how/convention/process/tooling/status`；`status: implemented` 时另含 `lane_ids[]`；
  `status: not-applicable` 时另含 `reason` + `consequence`（豁免①-④槽）；
  `status: manual` 时另含 `why_not_scriptable` + `human_steps`；顶层 `known_blind_spots[]`〔R-DATA · R-STRAT〕
- [ ] 1.4 **`schema_version` 的消费行为**（**MUST NOT 只是留个位**）：缺失 → fail-closed；**高于本实现已知版本 → fail-closed**
  「skill 版本过旧，请升级」，**MUST NOT 尽力解析**；**v1 阶段无需处理低版本**（当前只有 v1），**后续版本演进 MUST 在
  引入该版本的 change 里显式定义策略**（fail-closed 要求迁移 / `migrate` 子命令 / 只读兼容），**MUST NOT 在无设计的
  情况下现场处理**〔R-DATA〕
- [ ] 1.5 schema 单测：无 PyYAML 环境正常读写 · 非法枚举 · `id` 重复 · `schema_version` 缺失/未来值双向 fail-closed ·
  `.devenv-strategy.json` 三层五槽结构校验 · 三态各自的强制附带项字段存在性

## 2. 机械层基座（并发 · 原子写 · CAS · containment · 退出码）—— **面治：三条腿一起改**

- [ ] 2.1 **`openspec/` 写域单一锁**（`openspec/.sdflow-write.lock`，三 skill 共用）——`os.open(O_CREAT|O_EXCL)` 跨平台；
  锁文件记 **owner（UUID+PID+ts）**，释放前**核对 owner**，MUST NOT 删他人的锁〔R-CONC〕
- [ ] 2.2 **腿 2：`sdflow-init/scripts/init.py` 的 `inject()` 补锁 + 原子写**（现为裸 `open(w)`，无锁无原子写 ⇒ 会静默
  吃掉 devenv 的注入）〔R-CONC · 面治〕
- [ ] 2.3 **⭐ 腿 3：`sdflow-architecture/scripts/sad_scaffold.py` 迁到共用锁**（现用 `.sad-scaffold.lock` 是**另一把锁**）+
  **补 owner 记录**（**从零新增，非"补核对"**——`_acquire_lock` **根本没写入过 owner 信息**）+ 释放前核对 owner
  （`_release_lock` 现也不核对）〔R-CONC · 面治〕
- [ ] 2.4 **`atomic_write(path, text, mode=0o644)`**：`mkstemp` 唯一 tmp 名 + `os.replace`；**脚本类落地物传 `0o755`**
  （原 `sad_scaffold` 硬编码 0644 ⇒ 生成的 doctor 脚本**落盘即不可执行**）；覆盖既有文件时**保留原 mode**〔R-CONC〕
- [ ] 2.5 **锁短持有**：MUST NOT 跨验证执行持有（`LOCK_STALE_SEC=120` vs 验证数分钟 ⇒ **活锁被判残留锁** ⇒ 提示删锁 ⇒
  两 session 同写；「陈旧锁检测」由保护变成攻击面）〔R-CONC〕
- [ ] 2.6 **⭐ 路径 containment helper**（新增，横切）：① 只接受 **repo-relative 的规范化路径**——拒绝绝对路径、拒绝
  `..` ② **逐级 `lstat` 拒绝 symlink 祖先目录**（不只是目标文件本身）③ 验证最终 `realpath` 位于消费仓根之内；
  任一项不满足 ⇒ **fail-closed 拒绝该路径**，如实报告。**所有读 / 写 / 删 / digest 的路径（`source.file` ·
  `smoke` · `fixtures[]`（**含外部配置文件——无独立字段，见 3.7 注**）· touched-files 清单）MUST 统一经它**，
  不得各自实现校验〔R-PATH〕
- [ ] 2.7 **⭐ CAS 快照覆盖整个 verification plan**（**不只 `status`**）：`status` + **`executor`** + **`kind`** +
  `method` + `source` + `smoke` + `fixtures` + `env` + `deps`——**尤其 `executor` 与 `kind`**，长跑期间 lane 从
  `script`/`pure` 被改成 `human`/`hardware`，旧脚本**仍能通过只比 `status` 的 CAS 回写**〔codex〕；digest 算法明确为
  `sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode("utf-8"))`；回写在锁内重读比对，不一致 →
  拒绝要求重跑；回写 **MUST 只 patch 那一条 lane**〔R-CONC · R-DATA〕
- [ ] 2.8 **退出码一码一义** + 提供覆盖全部子命令的**退出码表**（见 6.7）——**「CAS 冲突」与「锁被占」MUST NOT 共用同一码**
  （前者应重读重跑，后者应退避重试，处置完全相反）〔R-CONC〕
- [ ] 2.9 `log` 子命令：append-only；`--line` 含换行符 → 拒绝
- [ ] 2.10 并发测试：**三 skill 两两并发不丢注入**（devenv‖init · devenv‖architecture · init‖architecture）· A 释放不删
  B 的锁 · **CAS 拒绝陈旧回写（改 `executor` 或 `kind` 而非 `status`）** · 长跑期间锁未被持有 · containment helper
  拒绝仓外路径 / `..` / symlink 祖先目录（综合用例）

## 3. scaffold 子命令

- [ ] 3.1 `init`：preflight（无 `openspec/` → exit 3）+ **SAD 缺失显式降级**（写 `sad: missing`，MUST NOT 佯装）+
  exit 4（continue/replan 显式区分，continue 前先读 `devenv-log.md` 定位断点）+ 存量素材检出 → 归位模式〔R-PF〕
- [ ] 3.2 `set-lane`：**只管 `planned` / `scaffolded` 两态**；`scaffolded` ⇒ `blocked_by` 非空且含可辨认修复指引；
  **`--status verified` 一律拒绝（exit 5）**〔R-EXEC〕
- [ ] 3.3 `render`：从 `.devenv-lanes.json` + `.devenv-strategy.json` 渲染 `environments.md` / `testing-strategy.md`
  （`DO NOT EDIT` banner）；**`verified` 渲染为 `verified-at <sha 前 7 位>`**，MUST NOT 呈现为无条件的绿；
  **`human-attested` 的绿与脚本验证的绿可区分**（如「已确认（人工验证）」）；**每条泳道的 `strength` MUST 渲染进文档**
  （不能只在人门口头说）；行号动态生成供阅读、不作真相〔R-DOC · R-DATA〕
- [ ] 3.4 `inject`：`opsx-devenv` marker 幂等注入；MUST NOT 写 `opsx-init` 区块〔R-MARKER〕
- [ ] 3.5 **`inject` 实现 fence-aware**——MUST NOT 照抄 `init.py`（其 `:49-52` 注释明示非 fence-aware）。覆盖
  CommonMark 全部 fence 变体（` ``` ` / `~~~` / 四 backtick / 缩进 fence）；孤儿 / 逆序 / 交错 → **fail-closed 报位置**
  〔R-MARKER〕
- [ ] 3.6 **`source` 出处锚**〔**round-4 重写，见 A21**〕：`source: {file, kind, selector}`，**无 `digest` 字段**。
  **`devenv_digest.py` MUST 零 make 知识**——lint 对 `source` **只查 `file_digests` 未失配**（见 3.7）。
  **MUST NOT 用行号存在性**（恒真 = 假绿）· **MUST NOT 按 `selector` 提取 recipe body 做 digest**（make 语法面无界，
  手搓解析器必带「语法不支持」罢工分支，**罢工一次即击穿「不管什么项目」的核心承诺**）· **MUST NOT 用正则查 target
  存在性**（「正则找不到」≠「target 不存在」——`ifeq` 包裹 / `define` 内 / 一行多 target 都会漏判 ⇒ 要么**误报罢工**、
  要么**永不 fail = 恒真假绿**，两条路都错）。
  **「target 存在且能跑」由 `verify-lane` 真 fork 执行保证——make 自己是权威判官**：拼错/不存在 → make 报
  `No rule to make target` → `exit≠0` → 泳道进不了 `verified`；被删/改名 → Makefile 字节变 → `file_digests` 失配。
  > **一般化规则**：机械层想知道「某个 make/shell/语言构造是什么意思」，**正解是让那个工具自己回答**（真跑一遍 /
  > `make -n`），**MUST NOT 手搓解析器去猜**。本 skill 的核心机制就是「尽可能跑一遍确认」——**跑一遍即最强的解析器。**
  〔R-DATA · A21〕
- [ ] 3.7 **⭐ 时效锚 = `evidence.file_digests`，逐文件原始字节，零规范化**〔**round-4 重写，取代原「分治」条**〕：
  **算法** = `sha256(<文件原始字节>)`，**所有文件类型一视同仁**；**MUST NOT** 做任何空白/注释/缩进规范化。
  **覆盖面** = `source.file`（非 `-` 时）+ `smoke` + lane 显式声明的 `fixtures[]`。
  > **原「按文件类型分治」（Makefile 剥空白保 tab / YAML 原始字节）整条删除**——它是 **recipe 提取的衍生债**：只有切出
  > recipe body 才有缩进噪声、才需要 normalize。**不提取 recipe ⇒ 无需规范化 ⇒「通用 `normalize()` 把两份缩进不同的
  > YAML 算出同一 digest」这个假绿在结构上不可能发生**。严格更强，且不可能踩错。
  **失配语义 = 提醒不是抓贼**；**允许多报**（改了 Makefile 里别的 target 也触发）——多报代价 = 重跑一次 smoke，
  消除多报代价 = 300 行解析器，**且方向反了（防漏宁可多报）**〔R-DATA · A21〕
- [ ] 3.8 **`append_makefile_target()`**：锁内「读 → 扫 target 名 → 补尾换行 → 以 tab 拼 recipe → 原子写」；
  **重名 → fail-closed**（脚本**只判名字碰撞**，**语义符不符归模型+人**，MUST NOT 假装机械判断了语义）〔R-APPEND〕
- [ ] 3.9 **`doctor-gen` 子命令**：生成依赖自查脚本（`0o755`）+ 安装命令清单——**MUST NOT 替操作者安装**〔R-BOUND〕
- [ ] 3.10 **v1 入口支持边界**：`inject` **只支持行文本型入口**（Markdown / Makefile / YAML）；结构化入口
  （`package.json`）v1 MUST NOT 直接注入 ⇒ 走 **Makefile 薄壳**；CI 配置**只生成独立新文件**，MUST NOT 就地改写既有
  CI 文件；门禁逻辑 SHALL 落在 Makefile，CI 配置只做调用壳；项目无 CI → CI 槽显式「不适用」并连带记后果〔R-APPEND〕
- [ ] 3.11 scaffold 测试：各退出码 · `set-lane --status verified` 被拒 · **render 输出 `verified-at <sha>` 且
  human-attested 与脚本验证在渲染上可区分** · render 输出含 `strength` · inject 在含 marker 演示的 fence 语料上不劫持
  （checkin **固定 fixture**，**MUST NOT 拿本仓活语料当 fixture**）· Makefile 追加三炸点（无尾换行 / tab / 重名） ·
  **⭐ 复杂 Makefile 不罢工**（`ifeq` 块 / 双冒号 / 一行多 target / target-specific 变量 / `define` 块 / 续行 —— 逐个
  造 fixture，**MUST 全部正常工作**，**MUST NOT 出现「语法不支持」类 fail-closed**）〔A21 回归守卫〕 ·
  **任意文件字节变化必改变 digest**（含 YAML 缩进变化）· **行号位移必被检出**（整文件字节变了）

## 4. 验证：两条通道（`verified` 的唯一产出者）

- [ ] 4.1 **`verify-lane` 子命令**（`executor: script` 通道）：脚本**自己 fork** 执行 `verification.method` 声明的命令，
  捕获 exit / 时长 / 输出摘要，**自行决定**写 `verified` 还是 `scaffolded+blocked_by`〔R-EXEC〕
- [ ] 4.2 **`confirm-lane` 子命令**（`executor: human` 通道）：人跑完人工验证后，经人门写入 `confirmed_what`；产出的
  `verified` **MUST 如实标 `attested_by: human`**（人说的，不是脚本验的）——**MUST NOT 声称脚本保证了执行者本人写入**
  （agent session 里模型是唯一命令执行者，「模型不能代替操作者调用」按字面永远为假，**且本就不必防**）〔R-EXEC〕
- [ ] 4.3 **执行证据原子落盘**：`at` / `at_commit`（HEAD SHA，**给人读的坐标，MUST NOT 作机械比对基准**）/ `exit` /
  `output_digest` / **`file_digests`** / **`method_at_verify`**——无证据则冷审「诚实镜」在数据上无从查证〔R-EXEC〕
  > **`method_at_verify` = A21 的面治补口**：旧 `method_digest` 覆盖「验证命令字符串 + recipe + smoke + fixtures」；
  > A21 换成只认**文件**的 `file_digests` 后，**`verification.method` 字符串本身掉出了时效锚**（人把 method 改成
  > `make integration-fast`，一个文件没动 ⇒ digest 不变 ⇒ lint 全绿 ⇒ verified 挂着，而它验的根本不是这条命令）。
  > 记下验证时的 method 原文，lint 一行比对即可。**信号确定（字符串比较）· 性质防漏 · 成本 ~5 行。**
  > **CAS 不顶替它**：`plan_snapshot` 覆盖 `method`，但那是**验证期间的并发保护**，不是**跨时间的时效检测**。
  > **`at_commit` 为何不能当时效锚**〔round-4 否决 git diff 方案〕：主路径是「落地物刚写完 → 立刻 fork 跑 smoke →
  > 写 `verified`」，**此刻 Makefile target 与 smoke 必然 uncommitted** ⇒ `git diff <at_commit> -- Makefile`
  > **在验证成功那一瞬间就报「已改动」**，锚在主路径上直接失效。
- [ ] 4.4 **⭐ `file_digests` 覆盖面**（**MUST 明确，MUST NOT 写「可达」这种做不到的词**）：`source.file`（非 `-` 时，
  **整份文件的原始字节，MUST NOT 提取 recipe body**〔A21〕）+ `smoke` 文件 + **lane 显式声明的 `fixtures[]` 清单**
  ——**穷尽，无第四项**。`fixtures` 由 **模型声明、人门确认**（无独立信号 ⇒ 语义层，进 ③-pre 分类清单）。
  **`fixtures[]` 的语义 MUST 钉死** = 本泳道验证所依赖、需纳时效锚的**全部文件**：harness · testdata ·
  **外部配置（`compose.yml` / `broker.conf` / lockfile）**。
  > **⚠️ MUST NOT 把「外部配置文件」写成与 `fixtures[]` 并列的第四项**〔round-4 修正〕：前一版 spec 正是这么写的，
  > 而**数据模型里根本没有承载它的字段**（`deps[]` 只有 `{name, kind}`，无路径）⇒ 旧 `method_digest()` 的签名里
  > 压根没这个参数，**这条 MUST 从来没被实现过，而 spec 不会报错**。**A16（`owned_by` 锚不存在）的同类病，
  > A19 预言的「平铺 MUST ⇒ 实现期发明假机械」。**
  > **纪律**：**写下「MUST 覆盖 X」之前，先在数据模型里指出承载 X 的那个字段——指不出就删掉这条 MUST。**
  〔R-EXEC · R-DATA〕
- [ ] 4.5 **证据失效检测（两条）**：① **`file_digests` 失配** ⇒ 报「验证证据已过期：`<file>` 已改动，需重验」
  （**允许多报**——Makefile 里别的 target 改了也报，刻意如此）② **`verification.method` ≠ `evidence.method_at_verify`**
  ⇒ 报「验证方法已改动（`<旧>` → `<新>`），需重验」。任一命中 **MUST NOT** 继续声称 `verified`〔R-EXEC · R-LINT〕
- [ ] 4.6 **超时杀进程树**：`start_new_session=True` + TERM→KILL 整棵进程组；默认超时 **300s，可按 lane 覆盖**，
  **实际用值写进 evidence**（便于事后复核"是不是超时太短误杀"）〔R-BOUND〕
- [ ] 4.7 **⭐ 中止后如实告知可能的孤儿资源**（**MUST NOT 假装能回收**）：recipe 内部起的 Docker 容器不属于子进程组，
  杀进程树杀不到它。超时/中断后 skill **SHALL 响亮报告**「本次验证被中止，可能留下孤儿资源（容器/端口占用），请检查」，
  并把该提示写进 `blocked_by` 与 `devenv-log.md`；**MUST NOT** 声称已清理〔R-BOUND〕
- [ ] 4.8 **非 POSIX → `verify-lane` refuse**：v1 进程树杀灭只承诺 POSIX（`start_new_session` + `os.killpg`）；非
  POSIX 时响亮告知平台限制，该泳道走 `executor: human`；**MUST NOT** 写一段从未在该平台执行过的代码并声称它能杀进程树
  （Windows `taskkill /T /F` 未实测，挂 Q-5）〔R-BOUND〕
- [ ] 4.9 **`kind: hardware` → `verify-lane` refuse** → 该泳道走 `executor: human`（指向 `embedded-test-sop`）。
  **诚实边界**：`kind` 无独立信号，**MUST NOT 佯装纯机械识别**，同时进 ③-pre 人门分类清单 + 冷审分类镜〔R-BOUND〕
- [ ] 4.10 **⭐ 最小环境 allowlist**（**主护栏**，取代"事后打码"）：子进程环境由 allowlist 构造，**MUST NOT 继承 agent
  的完整环境**（recipe 或其下游脚本可把凭证写进文件、发往网络，事后打码管不着）。**默认 allowlist**：`PATH` ·
  `HOME` · `SHELL` · `TMPDIR` · `LANG`/`LC_ALL` · `TERM`，**按栈追加**（Go：`GOPATH`/`GOCACHE`/`GOMODCACHE`/
  `GOPROXY`/`GOFLAGS`；Docker：`DOCKER_HOST`/`DOCKER_CONFIG`；网络：`SSL_CERT_FILE`/`*_PROXY`）；lane 需要的额外变量
  **显式声明**（`env: []`，无独立信号 ⇒ MUST 进 ③-pre 人门清单）；**敏感变量需人门单独授权，且 MUST NOT 落盘**〔R-BOUND〕
- [ ] 4.11 落盘的命令输出**额外**截断 + 过 secret 正则打码——**但此为 best-effort 缓解、非泄露保证**；正则集合登记
  已知盲区，**MUST NOT 用绝对语气佯装保证**〔R-BOUND〕
- [ ] 4.12 **跑前呈现 recipe（best-effort 展示，⚠️ 不是机械判定）**〔**round-4 重写**〕：`verify-lane` 跑之前，向人 /
  编排层**尽量**呈现该 target 的 recipe 原文（安全：recipe 里可能有 `rm -rf`、可能起容器），不只是 `make integration`
  这一行调用。
  > **⚠️ 这是 A21 的后门，措辞 MUST 精确**：本条**只做展示**，**MUST 是 best-effort**——提取不确定（条件块 / `define` /
  > 续行 / 一行多 target …）时**降级为「无法自动展开，请查看 `<file>` 的 `<selector>` target」**，**MUST NOT fail-closed
  > 罢工**（那正是 A21 杀掉的东西）。
  > **两条硬约束**：① 本条的提取代码 **MUST NOT 被复用为任何 digest / 判定的基准**（`file_digests` 只认整文件原始
  > 字节）——否则 parser 从后门原地复活；② **MUST NOT 为提高提取精度而扩充 make 语法覆盖**——想要权威展开，正解是
  > **调 `make` 自己**（如 `make -n <target>`，并如实标注它会执行 `$(shell ...)` 的边界），**MUST NOT 手搓**。
  > **判据**：机械保证的东西必须正确（∴ 无界语法面 = 死路）；**给人看的辅助允许 best-effort + 降级**。〔R-BOUND · A21〕
- [ ] 4.13 验证测试：verify-lane 亲自 fork 执行 · 证据字段齐全 · **`file_digests` 覆盖面**（改 `fixtures[]` 声明清单 /
  `source.file` / `smoke` → digest 失配，改未声明的其他文件 → 不失配）· **recipe 展示在复杂 Makefile 上降级而非罢工**
  （`ifeq` 包裹的 target → 输出「无法自动展开，请查看…」，**MUST NOT** 抛异常/fail-closed）〔A21〕·
  超时杀进程树（能杀的被杀，杀不到的被**响亮报告**而非静默）·
  **非 POSIX refuse → 走 human 通道**（mock 平台）· `kind: hardware` refuse → human · **子进程 env 不含 allowlist
  外的变量** · `set-lane --status verified` 被拒 · `confirm-lane` 落人门证据且 `attested_by: human`

## 5. lint 与其触发点

- [ ] 5.1 `devenv_lint.py` 主体骨架（**只查诚实，不查质量**——总则）〔R-LINT〕
- [ ] 5.2 检查①：任一泳道 `verification.method` 或 `verification.strength` 为空 → fail-closed〔R-LINT〕
- [ ] 5.3 检查②：状态与证据匹配——`verified` ⇒ `evidence` 齐全 ∧ **`file_digests` 未失配** ∧
  **`verification.method` == `evidence.method_at_verify`**（A21 面治补口）；`verified` ⇒
  **`blocked_by` 必须为空**（绿泳道挂着「本机无 mosquitto」= 文档在说谎）；`scaffolded` ⇒ `blocked_by` 非空**且含
  可辨认修复指引**〔R-LINT〕
- [ ] 5.4 **⭐ 检查③：三层框架完整性**（读 `.devenv-strategy.json`，**非解析 Markdown**）：三层各自的槽逐一存在且
  非空 → 缺任一 fail-closed；**`status: not-applicable` 的层豁免 ①–④ 槽**〔R-STRAT · R-LINT〕
- [ ] 5.5 **⭐ 检查④：三层状态的强制附带项**：`not-applicable` ⇒ `consequence` 非空**且非占位**；`manual` ⇒
  `why_not_scriptable` + `human_steps` 非空**且非占位**；`implemented` ⇒ `lane_ids` 指向的泳道**存在且
  `status ∈ {scaffolded, verified}`**（声称已实现却没有泳道、或只挂一条 `planned` 空壳，都是文档在说谎）〔R-STRAT · R-LINT〕
- [ ] 5.6 **反敷衍启发式**（与 `blocked_by` 同款）：`consequence` / `human_steps` / `blocked_by` **MUST NOT** 为纯
  占位符（`无` / `没有` / `N/A` / `TODO` / `待定` 独占整段 → 报警）；**诚实边界注释**：此为启发式，挡得住敷衍，挡不住
  「写得像模像样但没用」，后者归人门与冷审〔R-STRAT · R-LINT〕
- [ ] 5.7 检查⑤：命令出处一致性——**只查 `evidence.file_digests` 未失配**（逐文件原始字节）。**MUST NOT** 用行号
  存在性；**MUST NOT** 对 `source` 做任何 make 语法解析（**既不提取 recipe，也不用正则查 target 存在性**）——
  「target 能不能跑」由 `verify-lane` 真跑一遍让 **make 自己判**〔R-LINT · A21〕
- [ ] 5.8 检查⑥：指针不悬空——Markdown 链接 + 章节锚可达〔R-LINT〕
- [ ] 5.9 检查⑦：删源残留引用（含代码注释，**排除 `.devenv-backup/`**）〔R-LINT〕
- [ ] 5.10 检查⑧：路径 containment——所有声明的路径经边界校验（复用 2.6 的 helper）〔R-LINT · R-PATH〕
- [ ] 5.11 检查⑨：入口复述检测——README/CLAUDE 出现真相源才该有的完整命令表 → 告警（保守阈值：只在出现**完整命令表**
  时告警）〔R-LINT〕
- [ ] 5.12 lint 通过码 SHALL 带诚实后缀（`structure-ok-SEMANTICS-UNCHECKED`）；lint 按泳道状态分档：`verified` →
  强制②⑤；`scaffolded` → 强制 `smoke` 存在 + `blocked_by`；`planned` → 不核验命令出处；**第③④条是文档级检查，与
  泳道状态无关，每次都跑**；断言带 E 编号注释（scope-check 可机械核对）〔R-LINT〕
- [ ] 5.13 **⭐ `sdflow-maintain` 集成**（`devenv_lint` 的**唯一触发点**）：检出 `environments.md` 存在 ⇒ 调用
  `devenv_lint` 并入扫描报告；报告 SHALL 含未 `verified` 泳道清单（`planned`/`scaffolded`，**逐条列出非只给计数**）·
  失配的 `file_digests` · 空或敷衍的 `blocked_by` · **残留 `blocked_by` 的 `verified` 泳道** · 测试三层框架的留白；
  **报告 SHALL 原样透传 `devenv_lint` 的诚实后缀，MUST NOT 二次简化渲染成「verified = ✓」式的绿色状态**；无
  `environments.md` → 跳过（非报错）；`devenv_lint` 不可用 → **显式提示「检出 environments.md 但 devenv_lint 不可用，
  跳过健康度扫描」，MUST NOT 静默略过**。**注**：maintain 现为四类**硬编码**扫描、**无插件挂点** ⇒ 本任务是**新增代码**
  〔M-1〕
- [ ] 5.14 lint 测试：各条造坏输入 fail-closed · **「行还在、内容变了」被抓** · **YAML 缩进变化被抓** · **target 被
  改名/删除 → 通过 `file_digests` 失配被抓**（**非**靠静态解析）· **⭐ 复杂 Makefile（`ifeq`/双冒号/一行多 target/
  `define`/续行）→ lint 正常工作，MUST NOT 「语法不支持」罢工**〔A21〕 · **三层缺一层被抓** · **`not-applicable` 未记
  后果被抓** · **`manual` 无 `human_steps` 被抓** · **`implemented` 无对应泳道被抓** · `blocked_by: TODO` 被抓 ·
  `planned` 不误报 · 通过码含诚实后缀 · **maintain 集成：真实回归（`file_digests` 失配）被拦下** ·
  **maintain 报告原样透传诚实后缀、不被二次渲染成绿色**

## 6. references

- [ ] 6.1 `quality-criteria.md`：E 判据全集 + 拆解表（三处投影唯一真相源）
- [ ] 6.2 `lane-patterns.md`：依赖形态四问 + 五格阶梯**判据**（非规格）+ 最小可用集 + 参考实例（标「实例，非规格」）+
  未覆盖形态兜底（临场推导 + 显式标注「无参考实例，系临场推导」+ 登记 todo，MUST NOT 凭空编造权威候选）
- [ ] 6.3 **`verification-patterns.md`**：验证方法**参考实例**（标「实例，非规格」）+ **已知负面知识**——
  ① 轮询式连接观测对瞬时连接漏检率 100%（round-2 实验：5/5 全漏）⇒ **不可作为判据**
  ② proxy 计数零漏检但适用面 ⊆「skill 能控制依赖启动」
  ③ 前一版的 negative control 只证「耦合」不证「断言有效」，且对 testcontainers / 依赖内嵌 recipe 失效（**已否**，
  见本文件顶部说明）
  ④ **`assert True` 类语义恒真，任何外部插桩都堵不住**（要堵只有变异测试，判为太重）
- [ ] 6.4 `boundary-rules.md`：切线表 + 归属判据 + 删源三处置 + `grep` 引用面判据
- [ ] 6.5 `testing-strategy-template.md`：**三层 × 五槽**强制框架（含 `not-applicable`/`manual`/`implemented` 三态
  的附带项模板）+ `environments-template.md`（十六槽）
- [ ] 6.6 `review-lenses.md`：冷审镜单——覆盖镜 / **验证方法镜**（模型提的方法是否名副其实：强度有无夸大、盲区有无如实
  说出、`executor` 判定是否合理、`why_not_scriptable` 是否成立）/ **分类镜**（`kind`/`layer`/`fixtures`/`env` 的声明
  是否属实——无独立信号却是机械层输入，必须有一镜专查）/ **vacuous 镜**（唯一防线，MUST 如实声明其局限）/ **诚实镜**
  （`planned` 是否被伪装成 `verified` / `blocked_by` 与 `consequence` 是否敷衍 / `human-attested` 的 `confirmed_what`
  是否具体可信）/ 归位模式加删源镜；条目带 E 编号
- [ ] 6.7 **`exit-codes.md`**（新增）：覆盖全部子命令的退出码表，**一码一义**，**CAS 冲突与锁被占 MUST NOT 共用同一码**
  （处置完全相反）；实现期照抄，**不留现场发明空间**

## 7. SKILL.md 编排

- [ ] 7.1 frontmatter：`description` 含与 init 的分流判据句 + 两条前置声明（需已 `sdflow-init`；建议先
  `sdflow-architecture`，无 SAD → 降级可跑）〔R-TRIG〕
- [ ] 7.2 起手 A：preflight + 三模式分流 + SAD 降级话术〔R-PF〕
- [ ] 7.3 步骤 ①：事实采集——投影候选事实（栈/平台 ← SAD §2；依赖形态 ← SAD §3；集成测试点 ← SAD §5）**给操作者
  复核，MUST NOT 直接采信**；**时序纪律**（MUST 先问后记，MUST NOT 预填/臆测）；SAD 投影事实**批量呈现一次确认**
  （MUST NOT 逐条问）；无源事实（CI 平台 / 团队机器可用依赖 / 部署形态）逐条提问〔R-FACT〕
- [ ] 7.4 步骤 ①'（归位）：素材盘点 → 判归属 → **搬运表先确认再落笔** + 删源三处置（引用数 0 → 直接删；引用可枚举 →
  改引用后删；引用面广/散 → 降为一行指针）+ **显著呈现「以下 N 个文件将被整体删除」**〔R-RELOC〕
- [ ] 7.5 **⭐ 删源护栏**：入口**一次性** `git status` 干净检查（`git status` 非空 → 拒绝，提示先 commit/stash；
  backup manifest 写入**不重触发**它）；删除任一源文件前**逐文件校验**（在 containment 检查之后）：HEAD 有效（非
  unborn branch）· 已 tracked · 非 submodule、非 symlink（含祖先）· 内容 digest 与搬运表人门确认时一致；
  **backup manifest SHALL 入 git**（`.devenv-backup/`，**MUST NOT gitignore**——可恢复必须跨机器成立），含被删文件
  完整原内容 + 路径 + mode；残留引用扫描**排除该目录**〔R-DELGUARD〕
- [ ] 7.6 **⭐ 步骤 ②：测试三层框架 + 泳道 + 验证方法拍板**——三层各答五槽（模型现场调研推荐，**人拍板**）；
  `status: not-applicable` ⇒ ①–④ 槽豁免；泳道按 `references/lane-patterns.md` 的依赖形态四问推导（**MUST NOT
  按语言分格**）；验证方法由模型提出（**含 `strength` 强度与盲区自陈**），`executor: script` 为默认首选，`human`
  为降级路径需写 `why_not_scriptable`；**区分「方法本身没法程序跑」（human）与「能跑但条件不具备」（scaffolded +
  blocked_by）**，模型 MUST NOT 预判「大概跑不了」就直接标 human 偷懒；三处候选**批量呈现**供人一次拍板（MUST NOT
  逐条打断式提问）〔R-STRAT · R-LANE · R-VERIFY〕
- [ ] 7.7 步骤 ③：落地物追加（**追加者非拥有者**：已有的 → 登记，缺失的 → 追加带来源注释；v1 只支持行文本型入口；
  CI 只生成独立新文件；`package.json` 走 Makefile 薄壳）+ 归位模式 smoke **从已有测试中选取一条作为锚，MUST NOT 新写
  冗余 smoke**〔R-APPEND〕
- [ ] 7.8 **⭐ touched-files 事务清单**：**MUST 在写入任何落地物之前**，**原子落盘**（`openspec/architecture/
  .devenv-txn.json`）——路径（经 containment 校验）· **原先是否存在** · **原完整内容**（**非仅 digest**，digest
  恢复不了文件）· 原 mode〔R-TXN〕
- [ ] 7.9 **⭐ 步骤 ③-pre 人门（执行任何验证之前）**：①新写落地物 diff 全文（recipe body + smoke 源码；**仅登记的
  既有 target 只展示登记映射**，MUST NOT 要求人重读他自己写的、skill 不会改动的代码）②**验证方法逐条确认**（含
  `strength` 的强度与盲区）③**声明清单过目**：`kind` / `layer` / `executor` / `fixtures` / `env`——**全部无独立
  信号，必须人看**④将执行的命令（**recipe 展开**）。**②③ 表格化一次性呈现**（逐条 = 清单逐行列出，不是逐条打断式
  提问）；**呈现用人话**，`executor`/`kind`/`layer` 这类字段先翻译成一句后果描述再呈现，MUST NOT 直接抛内部字段名；
  **否决 → MUST 按 touched-files 事务清单回退**〔R-GATE〕
- [ ] 7.10 **⭐ ③-pre 否决 → 按 touched-files journal 逐项回退**：**原先存在的** → 用 journal 里的原内容**恢复**；
  **原先不存在的**（新写的 smoke/harness）→ **删除该文件**。**MUST NOT** 用 `git checkout --`（对 untracked
  **无效**，而「新写 smoke」是**主路径**）或**无路径限定的 `git clean`**（会误删操作者未 `git add` 的其他文件）〔R-TXN〕
- [ ] 7.11 **skill 每次启动 SHALL 先检查未完成的 journal**——若存在（上次在「写落地物 → ③-pre」之间崩溃），SHALL
  向操作者报告并提供「回退 / 继续」选择，**MUST NOT 无视**；回退成功后 SHALL 删除 journal〔R-TXN〕
- [ ] 7.12 步骤 ④：冷审（**MUST fresh 子代理**；宿主无原语 → 显式降级响亮留痕）按 `references/review-lenses.md`
  取镜（覆盖镜 / 验证方法镜 / 分类镜 / vacuous 镜 / 诚实镜 / 归位模式加删源镜）；冷审失败重派一次，再失败**显式报告
  缺口**，MUST NOT 无冷审静默过人门 + 人门④（泳道设计复核 / 未 `verified` 泳道逐条确认 / **三层框架的 `不适用` 槽
  逐条确认后果写对了吗** / `executor: human` 泳道的人工验证结果 → `confirm-lane` / **归位模式删源清单单独拎出，要求
  比其余议程更明确的确认动作**，不可逆）〔R-GATE〕
- [ ] 7.13 步骤 ⑤：render + inject + **收尾逐条列出未 `verified` 泳道及其 `blocked_by`** + 一句话给出整体判定与下一步
  （如「环境已可用于 N 条能力，M 条待补；下次直接触发本 skill 即走 continue」），**MUST NOT 让操作者自己猜**〔R-TRISTATE · R-MARKER〕
- [ ] 7.14 留痕总则（`devenv-log.md` append-only）+ 泳道/三层状态迁移速查表 + 模型档位（全强档）

## 8. 上下游 skill 改动

- [ ] 8.1 `sdflow-architecture/SKILL.md`：交棒话术改为**指向 `/sdflow-devenv`**（保留「不代写」边界：MUST NOT 代写
  environments.md/testing-strategy.md，亦 MUST NOT 将其内容写入 SAD；继续给出可投影的 SAD 锚 §2/§3/§5/§7/§8）+
  description 加**过程轴分流句**（「建 dev/test 环境 / 定测试策略 → `/sdflow-devenv`」，与既有时间轴分流句并列）〔A-1〕
- [ ] 8.2 **⭐ `sdflow-init/SKILL.md` description 加反向排除句**（「不管理项目的 dev/test 运行环境 / 依赖 / CI ——
  那部分 → `/sdflow-devenv`」）——**词面碰撞（"初始化环境"）是双向的，只补一边不解决路由**〔R-TRIG〕
- [ ] 8.3 `sdflow-maintain`：见 5.13（**同一件事，此处不重复列**）〔M-1〕

## 9. 仓级集成

- [ ] 9.1 更新 `README.md` Skills 列表
- [ ] 9.2 更新 `CLAUDE.md`「两类 skill」分类（devenv 归数据类）
- [ ] 9.3 跑 `bash setup.sh` 验证双宿主装载

## 10. 验收

- [ ] 10.1 **SM-5（诚实性）**：`pytest sdflow-devenv/tests/` 全绿；lint 坏输入全 fail-closed；`set-lane --status
  verified` 被拒；`verification.method` 为空被拒；`scaffolded` ⇒ `blocked_by` 非空且含修复指引；`verified` ⇒ 证据
  齐全且 `blocked_by` 为空
- [ ] 10.2 **⭐ SM-1（三层框架无留白）**：任一项目跑完，三层 × 五槽全部有内容；`not-applicable` 有非占位
  `consequence` · `manual` 有非占位 `human_steps` · `implemented` 有对应泳道且 `status ∈ {scaffolded, verified}`
- [ ] 10.3 **SM-3（新建）**：绿地项目产出完整三层框架 + ≥1 条 `verified` 泳道（`script` 或 `human` 均可）+ 待建清单。
  **诚实边界：零代码 greenfield 的 `verified` 数可为 0**，达标线为「三层框架完整 + 泳道表 + 待建清单」；**MUST NOT**
  为凑 `verified` 造空跑测试
- [ ] 10.4 **SM-2（归位）**：在 **checkin 的 brownfield fixture** 上跑，删源集与搬运结果**确定性断言**
- [ ] 10.5 **SM-6**：出处锚生效——造「行还在、内容变了」的坏输入被抓；**任意文件字节变化被 digest 捕获**（含 YAML
  缩进变化）；**target 被删/改名 → 经 `file_digests` 失配被抓**；**`selector` 拼错 → `verify-lane` 跑 make 时被 make
  自己抓（`exit≠0` → 进不了 `verified`）**；**⭐ 复杂 Makefile（`ifeq`/双冒号/一行多 target/`define`/续行）上 skill
  全程正常工作，MUST NOT 出现任何「语法不支持」类罢工**〔A21 核心承诺回归守卫〕
- [ ] 10.6 **SM-4**：`sdflow-maintain` 扫描中 `devenv_lint` **被自动调用**，并在真实回归（`file_digests` 失配）上
  拦下，报告**原样透传诚实后缀**
- [ ] 10.7 **SM-7（产品有效性）**：记录 clean checkout → 首条测试跑通的耗时 · 人工回答数 · 生成 diff 被保留的比例
- [ ] 10.8 **SM-8（不伤害，round-3 改写）**：异常中断（超时 / SIGINT）下，能杀的进程树被杀，**杀不到的孤儿资源被
  响亮报告**（MUST NOT 声称已清理）；非 POSIX 平台 `verify-lane` refuse 并走 human 通道；子进程 env **不含 allowlist
  外的变量**；敏感变量不落盘
- [ ] 10.9 **SM-9（新增：并发与路径安全）**：CAS 拒绝陈旧回写（尤其 `executor`/`kind` 被改而 `status` 未变）；
  containment helper 拒绝仓外路径、`..`、symlink 祖先；touched-files journal 在崩溃后可被下次启动发现并提供
  「回退/继续」

## 11. 测试覆盖图〔TG-18〕

```
code path                          │ 测试类型        │ 用例要点
───────────────────────────────────┼────────────────┼────────────────────────────────────────
devenv_schema (JSON, 两份侧文件)    │ 单元            │ 无 PyYAML 正常读写 · 枚举越界 · 三层五槽结构
schema_version                     │ 单元            │ 缺失 → fail · **未来值 → fail（非尽力解析）**
───────────────────────────────────┼────────────────┼────────────────────────────────────────
openspec 写域单一锁 (三 skill)      │ 并发(多进程)    │ devenv‖init · devenv‖arch · init‖arch
                                   │                │ 不丢注入 · A 释放不删 B 的锁
**CAS (全部输入快照)**              │ 并发            │ **改 executor/kind 而非 status → 旧验证被拒回写**
**containment helper**             │ 单元            │ **仓外绝对路径 / `..` / symlink 祖先 → 拒绝**
atomic_write(mode=)                │ 单元            │ 脚本类落 0o755 · 覆盖时保留原 mode
锁短持有                            │ 并发            │ 长跑期间锁未被持有(不被误判残留)
退出码一码一义                      │ 单元            │ CAS 冲突 ≠ 锁被占 · 各失败原因码不同
───────────────────────────────────┼────────────────┼────────────────────────────────────────
set-lane --status verified         │ 单元            │ **一律 exit 5 拒绝**   ← 核心守卫
verify-lane (script 通道)          │ 集成            │ 亲自 fork 执行 · 证据字段齐全
confirm-lane (human 通道)          │ 单元            │ 落人门证据 · `attested_by: human`
**file_digests 覆盖面**             │ 单元            │ **改 source.file/smoke/声明的 fixtures[] → 失配**
                                   │                │ 改未声明的其他文件 → 不失配
**recipe 展示 best-effort**〔A21〕  │ 单元            │ **复杂 Makefile → 降级提示，MUST NOT 罢工**
恢复路径(超时/中断)                 │ 故障注入        │ 能杀的进程树被杀 · **杀不到的被响亮报告，非静默**
超时杀进程树                        │ 集成            │ TERM→KILL 整棵进程组 · 实际超时写进 evidence
**最小环境 allowlist**              │ 单元            │ **子进程 env 不含 allowlist 外的变量**
非 POSIX refuse                    │ 单元(mock平台)  │ verify-lane refuse → 走 human 通道
kind:hardware refuse               │ 单元            │ verify-lane refuse → 走 human 通道
───────────────────────────────────┼────────────────┼────────────────────────────────────────
source 出处锚〔A21 重写〕           │ 单元            │ **「行还在、内容变了」被抓**（整文件字节）
                                   │                │ **target 改名/删除 → digest 失配被抓**
                                   │                │ **任意字节变化改变 digest**（含 YAML 缩进）
                                   │                │ **零 make 知识**（不解析、不查存在性）
selector 拼错                       │ 集成            │ **verify-lane 跑 make → exit≠0 → 非 verified**
                                   │                │ （**make 自己判**，非静态解析）
**⭐ 复杂 Makefile 不罢工**〔A21〕   │ 单元            │ **ifeq / 双冒号 / 一行多 target / define /**
                                   │                │ **续行 / target-specific 变量 → 全部正常**
                                   │                │ **MUST NOT 有「语法不支持」fail-closed**
append_makefile_target             │ 单元            │ 无尾换行 · tab · **重名 fail-closed(只判名)**
inject (fence-aware)               │ 单元(固定fixture)│ ``` / ~~~ / 四backtick / 缩进 fence
                                   │                │ 孤儿 / 逆序 / 交错 → fail-closed
                                   │                │ **MUST NOT 用本仓活语料当 fixture**
render (verified-at / human-attested) │ 单元         │ **verified 渲染带 sha** · **human 绿可区分** · strength 渲染
───────────────────────────────────┼────────────────┼────────────────────────────────────────
**三层框架完整性**                  │ 单元            │ **缺一层 → fail** · 五槽缺一 → fail
**三层状态附带项**                  │ 单元            │ **不适用无后果 → fail** · 人工无步骤 → fail
                                   │                │ **已实现无对应泳道 → fail**
devenv_lint 诚实性                  │ 单元            │ verified 残留 blocked_by 被抓
                                   │                │ blocked_by/consequence/human_steps: TODO 被抓
sdflow-maintain 集成               │ 集成            │ **真实回归被拦下**（file_digests 失配）
                                   │                │ **报告原样透传诚实后缀，不被二次渲染绿色**
───────────────────────────────────┼────────────────┼────────────────────────────────────────
**touched-files 回退**              │ 集成(临时 git 仓)│ **新写文件(untracked)被精确删除**
                                   │                │ **MUST NOT 用无路径限定 git clean**
                                   │                │ 既有文件被复原 · 人门期间手改 → 拒删
                                   │                │ **崩溃后下次启动检出未完成 journal**
归位删源护栏                        │ 集成(临时 git 仓)│ untracked/symlink/submodule/digest 变 → 拒删
                                   │                │ backup manifest **入 git** 且可还原
归位端到端                          │ 集成(fixture)   │ **checkin 的 brownfield fixture**，确定性断言
───────────────────────────────────┴────────────────┴────────────────────────────────────────

无自动化覆盖（诚实登记）：
· SKILL.md 的编排纪律（时序 / 人门 / 冷审 / R5 不重试 / R5 不装依赖）
  —— 模型行为，无确定性信号 → 归 spec-review + code-review
· **模型提的验证方法是否有效** —— §0.0 总则的诚实边界，本就不归机械
  → 归人门「验证方法逐条确认」+ 冷审「验证方法镜」
· **`kind` / `layer` / `covers` / `fixtures` / `env` 的声明是否属实** —— 无独立信号，机械层只能读它、不能验它
  → 归 ③-pre 人门「声明清单过目」+ 冷审「分类镜」
· **`assert True` 类语义恒真的 vacuous smoke** —— **任何外部插桩都堵不住**（要堵只有变异测试，判为太重）
  → 归冷审「vacuous 镜」——**唯一防线，MUST 如实声明局限**，MUST NOT 佯装机械层能堵
· **`human-attested` 的真实性**（人是否真确认了）—— agent session 架构边界：模型是唯一的命令执行者，
  「人亲自调用」在机械上不可区分，**且本就不必防**（使用者就是那个人自己，无动机骗自己）
  → 如实标注 `attested_by: human`，不设防伪
· greenfield 端到端 → 归第 0 组上游试点（手动，SM-7 记录）
```

## 12. ⭐ 首个真实试点（**实现完成后**，验收兼路线证伪）

> **这是整条路线的地基，且它至今零实证。** 机械层已放弃「防伪」，把质量判断整体交给「模型提方案 + 人拍板 + 冷审」——
> **若模型连给出「有方向」的验证方法都做不到，这道语义防线就无米下炊，§0.0 总则本身站不住。**
> **镜阵审不出这个，只有真实项目能。**

- [ ] 12.1 用一个**真实绿地项目**跑通 `/sdflow-devenv`（可与 `sdflow-architecture` 的首个真实试点合用同一项目，一份成本给两个 skill 去风险）
- [ ] 12.2 据试点结果核验四条经验前提，**结论回写 proposal**：
  ① 真实 SAD 的 §3/§5 **能否长出** devenv 需要的锚（依赖形态 ← §3 外边界 · 集成测试点 ← §5 contract）
  ② greenfield 的**「命令虚构」风险是否真实存在**（proposal 证据分层表里唯一的「预测，未观测」项）
  ③ `lane-patterns` 五格在**第二个样本**上是否还成立（n=1 过拟合）
  ④ **⭐ 模型能否为三层（unit/integration/e2e）各自提出像样的验证方法、并如实自陈强度与盲区**（假设 A-8）
- [ ] 12.3 记录 **SM-7**（产品有效性）：clean checkout → 首条测试跑通的**耗时** · **人工回答数** · 生成 diff 被操作者**保留的比例**
- [ ] 12.4 **若 ④ 证伪** → 不是修 bug，是**回设计桌重议 §0.0 总则**（语义防线撑不住 ⇒ 要么补机械、要么缩 scope）
