# tasks — add-sdflow-devenv

> 〔spec-review-amendment 2026-07-13〕本表已按设计门拍板（Q1–Q6）与 32 条采纳 finding **重写**。原表见 git 历史。
> Requirement 追溯：`R-*` = `specs/devenv-provisioning/spec.md`；`A-1` = `specs/architecture-design/spec.md`；`M-1` = `specs/maintain-scan/spec.md`。
> 纪律：改 `scripts/` 必跑 `tests/`。复选框在 `/sdflow-done` 的 archive 阶段勾——**实现期 MUST NOT 勾**。

## 0. ⭐ 实现前置（设计门 Q2，MUST 先于第 1 组）

- [ ] 0.1 **跑 `sdflow-architecture` 的首个真实试点**——用本来要做 SM-2 的**同一个绿地项目**（它是上游 hand-off 自己写下的最高优先 next action，至今未做）
- [ ] 0.2 据试点结果核验三条经验前提，**结论回写 proposal**：① 真实 SAD 的 §3/§5 **能否长出** devenv 需要的锚（依赖形态四问 / `covers` 对账）② greenfield 的**「命令虚构」风险是否真实存在**（Why 段唯一未观测项）③ `lane-patterns` 五格在**第二个样本**上是否还成立（A-2 的 n=1 过拟合）
- [ ] 0.3 若 ① 证伪（真实 SAD 长不出锚）→ **暂停本 change**，回 design 重议 SAD 依赖

## 1. 骨架与 schema

- [ ] 1.1 建 `sdflow-devenv/` 目录骨架（`SKILL.md` + `scripts/` + `references/` + `tests/`）〔R-触发分工〕
- [ ] 1.2 `scripts/devenv_schema.py`：**`.devenv-lanes.json` 的 schema**（标准库 `json`，**零第三方依赖**）——lane 含 `kind` / `status` / `command` / `source{file,kind,selector,digest}` / `smoke` / `neg_control` / `deps[{name,kind,up,down,owned_by,isolate}]` / `covers` / `blocked_by` / 执行证据字段；`environments.md` frontmatter 只解析三个扁平标量（`sad` / `mode` / **`schema_version`**）〔R-泳道数据落 JSON · ENG-5/ENG-2〕
- [ ] 1.3 schema 单测：无 PyYAML 环境下正常读写 · 非法 `kind`/`status` 枚举 · `id` 重复 · `schema_version` 缺失 → fail-closed

## 2. 机械层基座（并发 · 原子写 · 留痕）

- [ ] 2.1 **`openspec/` 写域单一锁**（`openspec/.sdflow-write.lock`，三 skill 共用）——`os.open(O_CREAT|O_EXCL)` 跨平台；锁文件记 **owner（UUID+PID+ts）**，释放前**核对 owner**，MUST NOT 删他人的锁〔R-并发 · ENG-6/codex〕
- [ ] 2.2 **顺带给 `sdflow-init/scripts/init.py` 的 `inject()` 补锁 + 原子写**（现为裸 `open(w)`，无锁无原子写 ⇒ 会静默吃掉 devenv 的注入）——**面治优先于点补**〔ENG-6〕
- [ ] 2.3 `atomic_write(path, text, mode=0o644)`：`mkstemp` 唯一 tmp 名 + `os.replace`；**脚本类落地物传 `0o755`**（原 `sad_scaffold` 硬编码 0644 ⇒ 生成的 doctor/broker 脚本**落盘即不可执行**）；覆盖既有文件时**保留原 mode**〔ENG-13〕
- [ ] 2.4 **锁短持有**：MUST NOT 跨 smoke 执行持有（`STALE=120s` vs smoke 数分钟 ⇒ 活锁被判残留锁 ⇒ 两 session 同写）〔R-并发 · ENG-10〕
- [ ] 2.5 **CAS**：`set-lane` / `verify-lane` 接受 `--expect <prior-status>`，锁内重读、状态不符 → exit 5；回写**只 patch 那一条 lane**，MUST NOT 用内存快照覆写整份〔R-并发 · ENG-10〕
- [ ] 2.6 `log` 子命令：append-only；`--line` 含换行符 → 拒绝
- [ ] 2.7 并发测试：**两进程并发 + 跨 skill（devenv ‖ init）不丢注入** · A 释放不得删 B 的锁 · **CAS 拒绝陈旧写入** · 中断只留 tmp · 长跑期间锁未被持有〔ENG-6/ENG-10〕

## 3. scaffold 子命令

- [ ] 3.1 `init`：preflight（无 `openspec/` → exit 3）+ **SAD 缺失显式降级**（写 `sad: missing`，MUST NOT 佯装）+ exit 4（continue/replan）+ 存量素材检出 → 归位模式〔R-preflight〕
- [ ] 3.2 `set-lane`：合法迁移表；`scaffolded` ⇒ `blocked_by` 非空；**`--status verified` 一律拒绝（exit 5）**〔R-verified 由脚本执行 · ENG-1〕
- [ ] 3.3 `render`：从 `.devenv-lanes.json` 渲染命令表（含 `DO NOT EDIT` banner）；**行号动态生成供阅读、不作真相**〔R-数据落 JSON〕
- [ ] 3.4 `inject`：`opsx-devenv` marker 幂等注入；MUST NOT 写 `opsx-init` 区块〔R-入口注入〕
- [ ] 3.5 **`inject` 实现 fence-aware**——MUST NOT 照抄 `init.py`（其 T21 注释明示非 fence-aware）。**MUST 覆盖 CommonMark 全部 fence 变体**：` ``` ` / `~~~` / 四 backtick / 缩进 fence；孤儿 marker / 逆序 / 交错 → **fail-closed 报位置**〔ADR-7 · codex〕
- [ ] 3.6 **`source` digest 锚**：按 `selector` 用 parser 重定位 target，比对 recipe 规范化 digest；**MUST NOT 用行号存在性**（对任何长度 ≥N 的文件恒真 = 假绿）〔R-数据落 JSON · ENG-4〕
- [ ] 3.7 **`append_makefile_target()`**：锁内「读 → 扫 target 名 → **补尾换行** → **以 tab 拼 recipe** → 原子写」；重名 → **fail-closed**（脚本只判名字撞了，**语义符不符归模型+人**，MUST NOT 假装机械）〔ENG-14/ENG-16〕
- [ ] 3.8 scaffold 测试：各退出码 · 迁移表外拒绝 · **`set-lane --status verified` 被拒** · render 幂等 · **inject 在含 marker 演示的 fence 语料上不劫持**（checkin **固定 fixture**：fence 内 marker + 孤儿 marker + 双重区块三形态，**MUST NOT 拿本仓活语料当 fixture**）· Makefile 追加三炸点（无尾换行 / tab / 已有同名 target）〔ENG-17/codex〕

## 4. `verify-lane` —— `verified` 的唯一产出者

- [ ] 4.1 **`verify-lane` 子命令**：脚本**自己 fork** 正向跑 + 阴性对照跑，捕获 exit code / 时长 / 输出摘要 / **测试计数**，**自行决定**写 `verified` 还是 `scaffolded+blocked_by`〔R-verified · ENG-1（CRITICAL）〕
- [ ] 4.2 **执行证据原子落盘**：`verified_at` / `verified_at_commit` / `fwd_exit` / `fwd_tests` / `neg_exit` / `neg_strategy` / `evidence_digest`——**无证据则冷审「诚实镜」在数据上无从查证**〔R-verified · ENG-1/ENG-16〕
- [ ] 4.3 **机械门槛①（对所有泳道强制）**：解析 `go test -json` / pytest `collected N items`，**断言「至少跑了 ≥1 个测试且 0 skipped」**——否则正向绿不成立（`go test` 无匹配测试 / 全 skip / `@echo TODO` 全部 exit 0）〔R-negative control · ENG-8〕
- [ ] 4.4 **机械门槛② negative control（强信号，条件适用）**：仅 `neg_control: applicable` 且抽离机制已定义时执行；反向的红 **MUST 匹配 expected-failure predicate**，**普通非零不通过**〔R-negative control · Q3〕
- [ ] 4.5 **依赖抽离策略（纯函数 + 可 mock runner）**：`dep 描述符 → command plan`（**返回计划，不执行**）；`owned_by: operator` → **拒绝停** · `kind: toolchain` → **`n/a`**（无法「抽掉」编译器）· **首选 `isolate`（endpoint 指向不可达地址，副作用为零）**，停服务是最后手段〔R-执行边界 · ENG-3（CRITICAL）〕
- [ ] 4.6 **恢复保证**：`try/finally` 恢复被抽离的依赖；**超时 / SIGINT / 异常下恢复仍执行**；**恢复失败 = 独立失败状态**（响亮报告 + 写 devenv-log），不能只写普通 `blocked_by`〔R-执行边界 · ENG-3〕
- [ ] 4.7 **超时杀进程树**：`start_new_session=True` + TERM→KILL 整棵进程组；容器等进 **cleanup ledger**，`finally` 回收（否则 `docker compose up` 孤儿容器占端口 → 下条泳道拿到假的「端口占用」）〔R-执行边界 · codex〕
- [ ] 4.8 **`kind: hardware` → `verify-lane` 直接 refuse**（脚本判定，非模型自觉）→ 置 `scaffolded` + 指向 `embedded-test-sop`〔R-执行边界 · ENG-2〕
- [ ] 4.9 **输出脱敏**：截断（尾 N 行 / 大小上限）+ 过 secret 正则打码 + **MUST NOT dump 环境变量**——命令继承 agent session 完整 env，失败回显会进 `blocked_by` → **commit → push**〔R-执行边界 · ENG-12〕
- [ ] 4.10 verify-lane 测试：**注入异常 → 断言 down 被调用后 up 也被调用**（恢复路径）· `owned_by: operator` → 拒绝停 · `kind: toolchain` → n/a · **空转测试（collected 0）不算绿** · 反向红不匹配 predicate → 不通过 · **vacuous smoke（`assert True` + fixture 连不上）被抓**〔ENG-17〕

## 5. lint 与其触发点

- [ ] 5.1 `devenv_lint.py` 五条：① **source digest 一致性**（非行号）② 指针不悬空 ③ 删源残留引用（含代码注释）④ N/A 显式性（理由 + **后果**）⑤ 入口复述检测〔R-lint 五条〕
- [ ] 5.2 分档核验 + 诚实性断言：`verified` ⇒ 执行证据齐全未失效 ∧ **`blocked_by` 为空**（绿泳道挂着「本机无 X」= 文档说谎）；`scaffolded` ⇒ `blocked_by` 非空〔R-lint · ENG-15〕
- [ ] 5.3 诚实通过码 `structure-ok-SEMANTICS-UNCHECKED`
- [ ] 5.4 lint 断言**带 E 编号注释**（scope-check：投影与 `quality-criteria.md` 一致性可机械核对）
- [ ] 5.5 **⭐ `sdflow-maintain` 集成**：其扫描调用 `devenv_lint`，报告未 verified 泳道 / 失配 digest / 空 blocked_by / 残留 blocked_by；无 `environments.md` → 跳过；`devenv_lint` 不可用 → **显式提示不静默**〔M-1 · CEO-2 · Q6〕
- [ ] 5.6 lint 测试：五条各造坏输入 fail-closed · **「行还在、内容变了」被抓**（原规格下这不是坏输入 ⇒ 测了也测不到真问题）· `planned` 不误报〔ENG-17〕

## 6. references

- [ ] 6.1 `quality-criteria.md`：E1–E11 + 拆解表（三处投影唯一真相源）
- [ ] 6.2 `lane-patterns.md`：依赖形态四问 + 五格阶梯**判据**（非规格）+ 最小可用集 + **依赖抽离策略表**（`kind` → `isolate`/`up`/`down`/`n/a`）+ 参考实例（标「实例，非规格」）+ 未覆盖形态兜底〔R-泳道设计〕
- [ ] 6.3 `boundary-rules.md`：切线表 + 归属判据 + 删源三处置 + `grep` 引用面判据
- [ ] 6.4 `environments-template.md`（十六槽）+ `testing-strategy-template.md`（九槽）
- [ ] 6.5 `review-lenses.md`：冷审镜单（覆盖 / **vacuous（挂 `CleanSession` 语义恒真真案例）** / 边界 / 诚实 / 删源），条目带 E 编号

## 7. SKILL.md 编排

- [ ] 7.1 frontmatter：`description` 含与 init 的分流判据句 + 两条前置声明〔R-触发分工〕
- [ ] 7.2 起手 A：preflight + 三模式分流 + SAD 降级话术〔R-preflight〕
- [ ] 7.3 步骤 ①：事实采集 + **时序纪律**（先问后记，禁预填）〔R-事实采集〕
- [ ] 7.4 步骤 ①'（归位）：盘点 → 判归属 → **搬运表先确认** + 删源三处置 + **显著呈现「以下 N 个文件将被删除」**〔R-归位〕
- [ ] 7.5 **⭐ 删源护栏**（设计门 Q1 的连带义务）：逐文件校验 **HEAD 有效 / 已 tracked / 非 submodule / 非 symlink / digest 与人门确认时一致**；生成**可恢复 backup manifest**（`.devenv-backup/`）；任一项不满足 → **fail-closed 拒删该文件**〔R-删源护栏 · codex〕
- [ ] 7.6 步骤 ②：泳道候选（依赖形态四问）+ 拍板 + 最小可用集〔R-泳道设计〕
- [ ] 7.7 步骤 ③：落地物追加（追加者非拥有者；**v1 只支持行文本型入口**，CI **只生成独立新文件**）+ 归位模式 smoke **复用已有测试**〔R-落地物 · ENG-11〕
- [ ] 7.8 **⭐ 步骤 ③-pre 人门（执行之前）**：落地物 diff 过目（**含 recipe body 与 smoke 全文**）+ 命令清单（**recipe 展开**）+ 「将停止服务 X」显著呈现；**否决 → 回退本次追加**〔R-冷审与人门 · ENG-7〕
- [ ] 7.9 步骤 ④：冷审（**MUST fresh 子代理**；宿主无原语 → 显式降级响亮留痕）+ 人门④（执行后：泳道复核 / 未 verified 逐条确认 / N/A 槽 / 删源清单）〔R-冷审与人门〕
- [ ] 7.10 步骤 ⑤：render + inject + **收尾逐条列出未 verified 泳道**〔R-状态机〕
- [ ] 7.11 留痕总则 + 状态迁移速查 + 模型档位（全强档）

## 8. 上下游 skill 改动

- [ ] 8.1 `sdflow-architecture/SKILL.md`：description 加**过程轴分流句**〔A-1〕
- [ ] 8.2 `sdflow-architecture/SKILL.md` §5.3：交棒话术改为**指向 `/sdflow-devenv`**，保留「不代写」边界 + 继续给 SAD 锚〔A-1〕
- [ ] 8.3 `sdflow-maintain`：扫描面加 devenv 健康度（调 `devenv_lint`）〔M-1〕

## 9. 仓级集成

- [ ] 9.1 更新 `README.md` Skills 列表
- [ ] 9.2 更新 `CLAUDE.md`「两类 skill」分类（devenv 归数据类）
- [ ] 9.3 跑 `bash setup.sh` 验证双宿主装载

## 10. 验收

- [ ] 10.1 **SM-3/SM-4**：`pytest sdflow-devenv/tests/` 全绿；五条 lint 坏输入全 fail-closed；`set-lane --status verified` 被拒；`scaffolded` 空 `blocked_by` 被拒
- [ ] 10.2 **SM-2**（新建）：绿地项目产出 ≥1 条 `verified` 泳道，**执行证据落盘**
- [ ] 10.3 **SM-1**（归位）：在 **checkin 的 brownfield fixture** 上跑，删源集与搬运结果**确定性断言**（原「mqtt-console 副本 + 人工比对」跑一次后永不再跑）
- [ ] 10.4 **SM-5**：digest 锚生效——造「行还在、内容变了」的坏输入被抓
- [ ] 10.5 **SM-6**（产品有效性）：记录 clean checkout → 首条真实测试跑通的耗时 · 人工回答数 · 生成 diff 被保留的比例
- [ ] 10.6 **SM-7**（不伤害）：negative control 后所有被抽离依赖 **100% 恢复**；异常中断下恢复仍执行；`owned_by: operator` 被拒停

## 11. 测试覆盖图〔TG-18〕

```
code path                          │ 测试类型        │ 用例要点
───────────────────────────────────┼────────────────┼────────────────────────────────────────
devenv_schema (JSON)               │ 单元            │ 无 PyYAML 环境正常读写 · 枚举越界 · 无版本键
───────────────────────────────────┼────────────────┼────────────────────────────────────────
openspec 写域单一锁                 │ 并发(多进程)    │ devenv ‖ init 不丢注入 · A 释放不删 B 的锁
CAS (--expect)                     │ 并发            │ 陈旧写入被拒 · 只 patch 单条 lane
atomic_write(mode=)                │ 单元            │ 脚本类落 0o755 · 覆盖时保留原 mode
锁短持有                            │ 并发            │ 长跑期间锁未被持有(不被误判残留)
───────────────────────────────────┼────────────────┼────────────────────────────────────────
set-lane --status verified         │ 单元            │ **一律 exit 5 拒绝**  ← ENG-1 的守卫
verify-lane                        │ 集成            │ 亲自 fork 正/反两跑 · 证据字段齐全
  ├ 机械门槛① collected≥1 ∧ 0 skip │ 单元            │ 空转测试(go test 无匹配/全 skip)不算绿
  ├ 机械门槛② neg predicate        │ 单元            │ 反向红不匹配 predicate → 不通过
  ├ 依赖抽离策略(纯函数)            │ 单元            │ owned_by:operator→拒停 · toolchain→n/a
  │                                │                │ · isolate 优先于 stop
  ├ **恢复路径**                    │ 故障注入        │ **跑中抛异常 → 断言 down 后 up 被调用**
  ├ 超时杀进程树                    │ 集成            │ 孤儿容器被回收，不占端口
  └ 输出脱敏                        │ 单元            │ PASSWORD=xxx 被打码，env 不 dump
───────────────────────────────────┼────────────────┼────────────────────────────────────────
source digest 锚                   │ 单元            │ **「行还在、内容变了」被抓**（原规格测不到）
append_makefile_target             │ 单元            │ 无尾换行 · tab · 重名 fail-closed
inject (fence-aware)               │ 单元(固定fixture)│ ``` / ~~~ / 四backtick / 缩进 fence
                                   │                │ 孤儿 / 逆序 / 交错 → fail-closed
                                   │                │ **MUST NOT 用本仓活语料当 fixture**
───────────────────────────────────┼────────────────┼────────────────────────────────────────
devenv_lint 五条 + 诚实性           │ 单元            │ verified 残留 blocked_by 被抓
sdflow-maintain 集成               │ 集成            │ **真实回归被拦下**（digest 失配）  ← SM-3
───────────────────────────────────┼────────────────┼────────────────────────────────────────
归位删源护栏                        │ 集成(临时 git 仓)│ untracked/symlink/submodule/digest 变 → 拒删
                                   │                │ backup manifest 可还原
归位端到端                          │ 集成(fixture)   │ **checkin 的 brownfield fixture**，确定性断言
───────────────────────────────────┴────────────────┴────────────────────────────────────────

无自动化覆盖（诚实登记）：
· SKILL.md 的编排纪律（时序/人门/冷审）——模型行为，无确定性信号 → 归 spec-review + code-review
· 语义恒真的 vacuous smoke（协议层面导致断言恒真）→ 归冷审镜（机械绝无可能抓到）
· covers 声明的正确性（declared 是否真命中）→ 归冷审（同 adr/0018）
· greenfield 端到端 → 归 Q2 试点（手动，SM-6 记录）
```
