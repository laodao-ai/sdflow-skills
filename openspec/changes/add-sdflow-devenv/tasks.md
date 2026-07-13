# tasks — add-sdflow-devenv

> Requirement 追溯：`R-*` = `specs/devenv-provisioning/spec.md` 的 Requirement；`A-1` = `specs/architecture-design/spec.md` 的 MODIFIED Requirement。
> 纪律：改 `scripts/` 必跑 `tests/`（本仓强制）。复选框在 `/sdflow-done` 的 archive 阶段勾——**实现期 MUST NOT 勾**（会触 ship_gate 设计门失鲜）。

## 1. 骨架与 schema

- [ ] 1.1 建 `sdflow-devenv/` 目录骨架（`SKILL.md` 占位 + `scripts/` + `references/` + `tests/`）〔R-14〕
- [ ] 1.2 写 `scripts/devenv_schema.py`：frontmatter schema 定义（`sad` / `mode` / `lanes[]` 全字段）+ 校验函数，**两脚本共用**防口径漂移〔R-4, R-11〕
- [ ] 1.3 schema 单测：合法/非法 frontmatter、必填字段缺失、`status` 枚举越界、`lane.id` 重复〔R-4〕

## 2. 机械层基座（并发 · 原子写 · 留痕）

> **不可后补**（proposal A-4：`sdflow-architecture` 同款场景已抓出 5 个 CRITICAL 并发缺陷）。

- [ ] 2.1 `devenv_scaffold.py`：仓级写互斥锁 `openspec/.devenv-scaffold.lock`——`os.open(O_CREAT|O_EXCL|O_WRONLY)` 跨平台（**不用 fcntl**）+ 陈旧锁检测（按 mtime 年龄提示删锁，**不静默夺锁**）〔R-13〕
- [ ] 2.2 `atomic_write`：`tempfile.mkstemp` 同目录唯一 tmp 名（**固定名会并发撞车**）→ `chmod 0o644` → `os.replace`〔R-13〕
- [ ] 2.3 `_repo_lock` contextmanager 包裹**整个读-改-写序列**（MUST NOT 只包 write）〔R-13〕
- [ ] 2.4 `log` 子命令：`devenv-log.md` append-only；`--line` 含换行符 → 坏输入退出码拒绝（防伪造审计行）〔R-13〕
- [ ] 2.5 并发/原子写测试：两进程并发 `set-lane` 不丢更新；中断只留 tmp 不留半写正式文件；换行符 `--line` 被拒〔R-13〕

## 3. scaffold 子命令

- [ ] 3.1 `init`：两级 preflight（无 `openspec/` → exit 3 fail-closed 指引 `/sdflow-init`）+ **SAD 缺失显式降级**（写 `sad: missing`，**MUST NOT 佯装**）+ 已存在产物 exit 4（continue/replan 分流）+ 存量素材检出 → 提示归位模式〔R-1〕
- [ ] 3.2 `set-lane`：状态迁移**只走合法迁移表**，表外拒绝；`scaffolded` ⇒ `blocked_by` 非空校验；`verified` ⇒ 双向判据已通过标记 + `source` 行存在〔R-4, R-5〕
- [ ] 3.3 `render`：从 frontmatter 渲染正文命令表（命令 | 跑什么 | 出处 | 状态），带 `DO NOT EDIT` banner——**单一真相源，MUST NOT 双写**〔R-11〕
- [ ] 3.4 `inject`：`opsx-devenv` marker 托管块注入（CLAUDE/AGENTS/README/INDEX），token 定位 + 幂等整块替换；**MUST NOT 写入 `opsx-init` 区块**〔R-12〕
- [ ] 3.5 **`inject` 实现 fence-aware**——**MUST NOT 照抄 `init.py`**（其 T21 注释明示非 fence-aware、会命中代码块内演示的 marker，修复已 defer）；复用同文件 fence 口径〔R-12, ADR-7〕
- [ ] 3.6 scaffold 子命令测试：各退出码分流；迁移表外拒绝；render 幂等；**inject 在「代码块内有 marker 演示」的语料上不劫持**（本仓自身即此类语料，可 dogfood）〔R-1, R-4, R-11, R-12〕

## 4. negative control（`verified` 的可执行判据）

> ADR-4 的落地关键；design Q-4 待定项在此收口。

- [ ] 4.1 定义「抽掉依赖」的执行策略：按 `deps` 声明类型分派——compose 服务 → `docker compose stop`；本地进程 → 不启动；端口类 → 指向不存在的端口。**策略表写入 `references/lane-patterns.md`**〔R-5〕
- [ ] 4.2 实现双向判据执行器：正向跑（绿）+ 抽依赖跑（必须红）→ 判 `verified`；抽依赖仍绿 → **拒绝 `verified`** + `blocked_by="smoke 未穿过依赖(vacuous)"`〔R-5〕
- [ ] 4.3 `deps: []` 豁免通道：退回「smoke 含断言语句」最低机械门槛〔R-5〕
- [ ] 4.4 negative control 测试：vacuous smoke（不碰依赖但恒绿）被拒；真穿过依赖的 smoke 通过；`deps: []` 豁免生效；**优雅降级依赖**（缺失时 fallback 不报错）触发 R-1 风险 → 如实记 `blocked_by` 留人裁决〔R-5〕

## 5. lint（E1–E11 的机械投影）

- [ ] 5.1 `devenv_lint.py` 五条机械检查：① 命令出处一致性（`verified` 的 `source` 行必须存在）② 指针不悬空 ③ **删源残留引用（含代码注释）** ④ N/A 显式性（`N/A — <理由> + <后果>`）⑤ 入口复述检测（弱启发告警）〔R-10〕
- [ ] 5.2 按泳道状态**分档核验**：`verified` → 强制①；`scaffolded` → `smoke` 文件存在 + `blocked_by` 非空；`planned` → 不核验出处〔R-10, R-4〕
- [ ] 5.3 诚实通过码 `structure-ok-SEMANTICS-UNCHECKED`（结构通过 ≠ 内容已审）〔R-10〕
- [ ] 5.4 lint 断言**带 E 编号注释**（scope-check：投影与 `quality-criteria.md` 一致性可机械核对）〔R-10, TG-25〕
- [ ] 5.5 lint 测试：五条各造一个坏输入 fail-closed；分档核验不误报（`planned` 不因无 `source` 报错）〔R-10〕

## 6. references

- [ ] 6.1 `quality-criteria.md`：E1–E11 + 拆解表（**三处投影的唯一真相源**）〔R-10, TG-25〕
- [ ] 6.2 `lane-patterns.md`：**依赖形态四问** + 五格阶梯**判据**（非规格）+ 最小可用集判据 + negative control 策略表（4.1）+ 参考实例（标注「实例，非规格」）+ **未覆盖形态兜底流程**〔R-3〕
- [ ] 6.3 `boundary-rules.md`：切线表（方法/决策 ↔ 环境/操作）+ 归属判据 + 删源三处置 + `grep` 引用面判据〔R-8, R-11〕
- [ ] 6.4 `environments-template.md`（十六槽）+ `testing-strategy-template.md`（九槽）——从 `docs/sad/environments-template-draft.md` 搬运并补齐〔R-11〕
- [ ] 6.5 `review-lenses.md`：冷审镜单（覆盖镜 / vacuous 镜 / 边界镜 / 诚实镜 / 删源镜），**条目带 E 编号引用**；vacuous 镜挂 `CleanSession` 语义恒真真案例当范例〔R-9, TG-25〕

## 7. SKILL.md 编排

- [ ] 7.1 frontmatter：`name` + `description`（含**与 init 的分流判据句**「装流程规则 → init；建项目 dev/test 环境 → devenv」+ 两条前置声明）〔R-14〕
- [ ] 7.2 起手 A：preflight + 三模式分流（新建 / 归位 / continue）+ SAD 降级话术〔R-1〕
- [ ] 7.3 步骤 ①：事实采集（SAD 投影给人复核 + 无源必问）+ **时序纪律**（MUST 先问后记，禁预填/臆测）〔R-2〕
- [ ] 7.4 步骤 ①'（归位专属）：素材盘点 → 判归属 → **搬运表先给人确认再落笔** + 删源三处置 + **显著呈现「以下 N 个文件将被删除」** + **git 前置 fail-closed（工作区必须干净）**〔R-8〕
- [ ] 7.5 步骤 ②：泳道候选（依赖形态四问）+ 拍板 + 最小可用集〔R-3〕
- [ ] 7.6 步骤 ③：落地物追加（**追加者非拥有者**：登记已有 / 追加缺失 / 重名 fail-closed；**归位模式 smoke 复用已有测试**）+ **smoke 执行边界四条**（跑前列命令 / 超时 / **失败不 debug** / 真硬件不跑 → 指 `embedded-test-sop`）+ **MUST NOT 替装依赖**〔R-6, R-7〕
- [ ] 7.7 步骤 ④：冷审（**MUST fresh 子代理，禁自查**；失败重派一次；宿主无原语 → **显式降级响亮留痕**）+ 人门四议程（含 **diff 过目**）〔R-9〕
- [ ] 7.8 步骤 ⑤：render + inject + **收尾逐条列出未 verified 泳道**（MUST NOT 只埋进文件）〔R-4, R-11, R-12〕
- [ ] 7.9 全流程留痕总则 + 状态迁移速查表 + 模型档位（**全强档**，无可下放弱档步）〔R-13〕

## 8. sdflow-architecture 改动（MODIFIED capability）

- [ ] 8.1 `sdflow-architecture/SKILL.md` description 增加**过程轴分流句**（「建 dev/test 环境 / 定测试策略 → `/sdflow-devenv`」），与时间轴分流句并列〔A-1〕
- [ ] 8.2 §5.3 交棒话术改写：从「指出不代写 + 给模板路径」→ **指向 `/sdflow-devenv`**；**保留**「不代写」边界 + 继续给 SAD 锚（§2/§3/§5/§7/§8，含**依赖形态锚 = §3 外边界**）〔A-1〕

## 9. 仓级集成

- [ ] 9.1 更新 `README.md` Skills 列表（新增 `sdflow-devenv`）
- [ ] 9.2 更新 `CLAUDE.md` 的「两类 skill」分类（`sdflow-devenv` 归数据类：Markdown + Python + tests）
- [ ] 9.3 跑 `bash setup.sh` 建 symlink，验证双宿主（`~/.claude/skills/` + `~/.codex/skills/`）装载成功

## 10. 验收（Success Metrics 兑现）

- [ ] 10.1 **SM-3/SM-4**：`pytest sdflow-devenv/tests/` 全绿；五条 lint 在坏输入上全部 fail-closed；`scaffolded` 空 `blocked_by` 被拒〔R-10, R-4〕
- [ ] 10.2 **SM-2（新建模式）**：在一个绿地样例仓（有 SAD、无代码）跑通五步，产出**≥1 条 `verified` 泳道**（通过双向判据）+ 明确待建清单〔R-1..R-12〕
- [ ] 10.3 **SM-1（归位模式回归）**：在 mqtt-console 副本上跑归位模式，产出与人工归位结果**语义一致**、源文件删除集一致、`devenv_lint` 全绿〔R-8〕
- [ ] 10.4 **SM-5**：确认命令/出处/状态仅存于 frontmatter 一处，正文表格带 DO-NOT-EDIT banner 且由 render 生成〔R-11〕

## 11. 测试覆盖图〔TG-18〕

```
code path                          │ 测试类型      │ 用例要点
───────────────────────────────────┼──────────────┼──────────────────────────────────────────
devenv_schema.py  校验              │ 单元(pytest) │ 合法/非法 frontmatter · 枚举越界 · id 重复
───────────────────────────────────┼──────────────┼──────────────────────────────────────────
scaffold._acquire_lock             │ 并发(pytest) │ 两进程竞争 · 陈旧锁提示不静默夺锁
scaffold.atomic_write              │ 单元+故障注入 │ 中断只留 tmp · tmp 名唯一(并发不撞车)
scaffold.log (append-only)         │ 单元          │ 换行符 --line 被拒(防伪造审计行)
───────────────────────────────────┼──────────────┼──────────────────────────────────────────
scaffold.init (分流)               │ 单元          │ exit 3/4/0 各分支 · SAD 缺失写 sad:missing
scaffold.set-lane (迁移表)         │ 单元          │ 表外迁移拒绝 · scaffolded 空 blocked_by 拒
scaffold.render                    │ 单元          │ 幂等 · banner 存在 · 状态变更后重渲染一致
scaffold.inject                    │ 单元+dogfood │ 幂等替换不重复 · **代码块内 marker 不劫持**
                                   │              │   (fence-aware；本仓语料即 dogfood 用例)
                                   │              │ · MUST NOT 触碰 opsx-init 区块
───────────────────────────────────┼──────────────┼──────────────────────────────────────────
negative control 执行器            │ 集成          │ vacuous smoke 被拒 · 真穿过依赖的通过
                                   │              │ · deps:[] 豁免 · 优雅降级依赖 → 记 blocked_by
───────────────────────────────────┼──────────────┼──────────────────────────────────────────
devenv_lint 五条                   │ 单元          │ 每条各造一个坏输入 fail-closed
devenv_lint 分档核验               │ 单元          │ planned 不因无 source 误报
───────────────────────────────────┼──────────────┼──────────────────────────────────────────
端到端(新建模式)                    │ 集成(手动)    │ SM-2：绿地样例仓 → ≥1 条 verified 泳道
端到端(归位模式)                    │ 集成(手动)    │ SM-1：mqtt-console 副本 → 与人工归位一致
───────────────────────────────────┴──────────────┴──────────────────────────────────────────

无自动化覆盖（诚实登记）：
· SKILL.md 的编排纪律（时序/人门/冷审）——模型行为，无确定性信号 → 归 spec-review + code-review
· 语义恒真的 vacuous smoke → 归冷审镜（机械绝无可能抓到，见 design ADR-4）
· covers 声明的正确性（declared 是否真命中）→ 归冷审（同 adr/0018）
```
