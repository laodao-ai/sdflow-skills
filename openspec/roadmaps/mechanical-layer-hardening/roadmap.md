# workflow 机械层固化 实施路线图

> 版本：v1（2026-07-07）
>
> 相关文档（全部位于 `openspec/roadmaps/mechanical-layer-hardening/`）：
> - 需求综述：`requirements.md` · 整体设计：`design.md` · 任务日志：`task-log.md`

## 概览

两腿六阶段。**Leg 1（脚本化）先行**——就绪、高 ROI、低爆炸半径，阶段 1-4 各自独立可交付、可并行（除共享文件外）。**Leg 2（去字符串化）就绪度分级**——阶段 5（S1 gate 锚）就绪但前置 ROI 评估门 + 高仪式；阶段 6（S2 recorder 索引）**north-star 不排期**，ROI 触发才起。

> **进度里程碑（2026-07-08）**：**Leg 1 高 ROI 三阶段 P1/P2/P3 全交付**（sweep / anchor-lint / determ-guards）+ **Leg 2 P5 gate 锚→frontmatter 已交付**（change `mlh-p5-gate-frontmatter`，merge `1b069a7`）+ **P5 尾巴 T74/T75 已清结**（change `mlh-p5-parser-cleanup`，merge `007b00d`：parser 首行 `---` 无闭合改判 absent + `unterminated` 死类别退役 + live inline 死符号删除）——机械层「脚本化」主干 + 「去字符串化」家族① 均已立且尾巴清尽。余 P4（编排步下沉）+ Leg 2 P6（recorder 索引）。**目标态重评（2026-07-08）**：P4 从「按需 0/7」翻为「★5 项该做未做（4.C/4.B/4.D.1/2/4）+ ◐2 项该做待 embedded 契约（4.A/4.D.3）」，判据锚目标态非现状快照；P6 从「north-star 不排期」经端态复核**拍板 = 端态 A**（根治：迁 frontmatter 使 `｜` 腐蚀类结构上不可能；否决 B 治标；约束①历史不迁使成本≈P5 dual-read；压轴排 ★P4 后）——详见各阶段前置的目标态重评订正块 + 建议批次 todolist `mlh-p4-target-state`。

| 阶段 | 腿 | 里程碑 | 就绪度 |
|---|---|---|---|
| **P1** · `issues.py sweep --change X` | Leg 1 | done sweep 4 步手循环 → 一个原子子命令 | ✅ **已交付**（ca66d60） |
| **P2** · anchor-lint 产出侧校验器 | Leg 1 | 每轮 review 手 grep+肉眼核 enum → 机验门 | ✅ **已交付**（e43460c） |
| **P3** · 确定性守卫补全 | Leg 1 | recorder 镜像一致性测试 + config/batches lint | ✅ **已交付**（a6a2adc，change `mlh-p3-determ-guards`；冷审 F5 守卫覆盖 8→14 helper） |
| **P4** · 编排 SKILL 机械步下沉 | Leg 1 | 4.A-4.D.4 按目标态逐项脚本化 | 就绪（★5 项该做 · ◐2 项待 embedded 契约；批次 `mlh-p4-target-state`） |
| **P5** · 家族① gate 锚 → frontmatter | Leg 2 | 删 `_line_scoped_hits` **live 解析半场**、正文提及不误判、归档 dual-read 永久保留 | ✅ **已交付**（change `mlh-p5-gate-frontmatter`，merge `1b069a7`；spec-review 六镜拦 1致命+3高 / impl-review 抓 2 真 bug；662 passed·dogfood CLEAN） |
| **P6** · 家族② recorder 索引 → frontmatter | Leg 2 | 腐蚀蒸发（写侧）+ 新数据可查询基底 | **端态 A 已定**（根治；约束①使成本≈P5 dual-read；压轴排 P4 后；T85） |

> 每阶段开独立 OpenSpec 变更（`implement-mechanical-layer-hardening-pN-<theme>`），归档后进下一个。
> **并行 caveat**：阶段 1（issues.py）与阶段 3 的 recorder 部分、阶段 5 的 producer SKILL 部分**改文件集不同可并行**；但阶段 2（anchor-lint 触 spec-review/code-review SKILL）与阶段 4 的 P7/P8（同触两审 SKILL）、阶段 5（S1 也改 producer SKILL）**若同期改 SKILL.md 须串行**，开并行前先核文件集是否相交。
> **全局红线（贯穿每阶段）**：新脚本/结构 fail-closed + 可观测，pytest 覆盖坏输入断言非零退出；判断部分显式保留给模型/人，脚本不越权（design §决策 5）。

---

## 阶段 1 · `issues.py sweep --change X`（Leg 1 开路）

### 前置条件
- [ ] 无（纯新增，零依赖）

### 目标
- 把 `sdflow-done` §2.1 的 issues sweep 4 步手循环（scan 两池 → 逐 id triage → batch add → reindex）收成 `issues.py` 一个原子子命令，模型只提供 `--change` 名。

### 子任务
#### 1.A issues.py sweep 子命令
- [x] 1.A.1 `issues.py sweep --change X`：内部 scan buglist+todolist 两池 → 按 change 过滤 OPEN 项 → 逐项 triage 入批次（bug/todo 各走对应脚本，幂等：已 PROPOSED no-op）→ `batch add X`（已存在跳过）→ `reindex`，一路做完。
- [x] 1.A.2 `test_issues.py` 扩 sweep 用例（含幂等重跑、空 change、孤儿项不纳入的边界）。
- [x] 1.A.3 `sdflow-done/SKILL.md` §2.1 改为调 `sweep`（把手循环 prose 替换为一行命令；保留「孤儿项不归本 sweep」边界声明）。

### 验收标准
- [x] `sweep --change X` 幂等（重跑无副作用）；只圈 `源==X ∧ 非终态 ∧ 批次空` 项；孤儿（源="")不纳入。
- [x] `pytest sdflow-issues/tests/` 全绿；新增 sweep 用例覆盖边界。
- [x] done SKILL §2.1 不再要求模型手跑 4 步 bash。

### 交付物
- `issues.py sweep` 子命令 + 测试；`sdflow-done/SKILL.md` §2.1 精简。

---

## 阶段 2 · anchor-lint 产出侧校验器（Leg 1，高频门禁）

### 前置条件
- [ ] 无（复用现成纯函数）

### 目标
- 把 spec-review Step3 / code-review Step5 的「出报告后手 grep 四类 v1 锚行 + 肉眼核 `layer`/`lens`/`runner`/`sev` enum/子格式」降为确定性脚本门。

### 子任务
#### 2.A anchor_lint 脚本
- [x] 2.A.1 `anchor_lint.py --report <path> --layer spec-review|code-review`：扫四类锚（outside-voice/hr-tg/step1-broad-review/lens-metric）存在性 + enum/字段/子格式合法性（enum 从 `lens-metric-contract.md` 单一源读，不复制清单）；缺锚/越域即非零退出。遵 F1 实质（度量锚变长 KV 走前缀匹配、**不用** `ship_gate._line_scoped_hits` 定长整行原语）；因 anchor_lint 作 bundle tools/ 经 update 铺进消费仓、而 `sdflow-retro/scripts` 不在消费仓，`import lens_metric_aggregate` 运行时 break，故**脚本内重实现同款 fence-aware + 前缀 kv 逻辑**（非 import 复用）〔mlh-p2-anchor-lint 调和〕。
- [x] 2.A.2 测试：喂缺字段/越域/缺锚/fence 内示范锚的样本报告，断言退出码。
- [x] 2.A.3 两审 SKILL 的锚自检步改为调 `anchor_lint`；**保留声明**「`findings=N` 与合并池实收数的数值一致性仍是主 session 信任边界、非机械可验」（脚本不谎称能保证数值正确）。

### 验收标准
- [x] 坏样本（缺锚/越域 enum/缺字段）→ 非零退出；干净样本 → 0。
- [x] 受 `config.yaml metrics.enabled` 门控：关闭时 lens-metric 一类不校验不阻塞（与 SKILL 现有门控一致）。
- [x] 两审 SKILL 自检步不再是「模型手 grep」而是调脚本；数值一致性边界诚实保留。

### 交付物
- `anchor_lint.py` + 测试；spec-review/code-review SKILL 自检步接脚本。

---

## 阶段 3 · 确定性守卫补全（Leg 1）

### 前置条件
- [ ] 无

### 目标
- 补两处「应有机械校验却靠约定/人自觉」的守卫：recorder 镜像 helper 漂移、config/batches 人写字段。

### 子任务
#### 3.A recorder 镜像 helper 一致性测试（= P3）
- [x] 3.A.1 对 verbatim helper 加源码级一致性断言——**契约订正（grill Path B）**：由 `inspect.getsource` byte 全等改为**剥 docstring 后 AST 等价**（9/11 helper 仅 docstring 合法分化，byte 全等会假阳）。拓扑：**3 向**（buglist/todolist/issues）= `atomic_write`/`repo_root`/`_reject_cell_unsafe`；**2 向**（buglist↔todolist）= 原 8 个 + **冷审 F5 扩 6 个**（`_id_sort_key`/`validate_doc_paths`/`all_ids`/`next_id`/`_die`/`_load_json`，实测 byte-identical）= 14 个。顺手归一 todolist `split_sections`/`block_ranges` 2 处逻辑异写（零回归）。**不抽公共模块**（D4）。
- [x] 3.A.2 故意逻辑分叉证伪（`test_logic_drift_is_caught`）+ helper 删除证伪（裸 getattr 无吞 AttributeError）验证守卫生效。

#### 3.B config.yaml + batches.md lint（= P4）
- [x] 3.B.1 `config_lint`（`init.py` **第 4 个 mode**，**手写 stdlib 行扫描不 import yaml**——follow anchor_lint 范式，零依赖惯例）：`schema`/`rules`（proposal/specs/design/tasks 四段）必填 + `model-tiers`（若存在）子键枚举 ⊆ {strong/mid/light} + `metrics`（若存在）`enabled` bool；**顶层块缺失条件化放行**（防 mlh-p2 假阳）。含冷审 F2（UnicodeDecodeError fail-closed）。
- [x] 3.B.2 `issues.py batch lint`：`优先级` 前导 token ∈ PRIORITIES∪{—}（**冷审 F3 正则 `^(P[0-4](?!\d)|—)` 拒 P10/P40**，后缀不校验容 `P1 ★`）、占位符 `<待填>` 双字段豁免、`计划` 非占位时非空；复用 `_split_batches_entries` 只读校验。含冷审 F1（缺 batches.md→非零 fail-closed）。
- [x] 3.B.3 各自测试（坏 config / 坏 batch 字段 → 非零退出）。

### 验收标准
- [x] 改任一 verbatim helper 未同步 → 一致性测试红（`test_logic_drift_is_caught` 证伪实证）。
- [x] 坏 config.yaml（打错 tier 子键/缺必填段/metrics 非 bool）→ `config_lint` 非零退出。
- [x] batches.md `优先级` 非法 / `计划` 空 → `batch lint` 报错；现存真实数据零假阳。
- [x] `pytest` 全绿（4 目录 396 passed，全仓 627）。

### 交付物
- recorder 镜像一致性测试；`config_lint` + `issues.py batch lint` + 测试。

> 3.A / 3.B 可各作一次 change（粒度都 ≈ 一次 `/opsx:new`），也可合批（同属「确定性守卫补全」、低耦合低增量）——落地时按 batch-triage 判据定。

---

## 阶段 4 · 编排 SKILL 机械步下沉（Leg 1）

> **⚠️ 目标态重评订正（2026-07-08，用户拍板）**：原「中 ROI 按痛点做子集 / 不追求全做 / 起手重评哪些当下真痛」的口径**是拿现状快照（现在痛不痛）反推目标不该做——已否决**。开发阶段应锚**目标态**（requirements §1.3 愿景「机械活归脚本，模型不再手 grep/手数/手循环」+ adr/0006 硬约束「凡机械 prose 协议 MUST 脚本化」）判「该做未做 / 可不做」。据此重评：P4 从「按需 0/7」翻成——
> - **★ 该做未做**（目标态该做，原被快照压住）：4.C `lens_metric_emit`（**最高**，直闭 §1.2 痛点#2「手数信任边界」）· 4.B `maintain_scan`（纯机械 set-diff、每次 maintain 都跑）· 4.D.1 · 4.D.2 · 4.D.4。
> - **◐ 该做·正当排后**（**producer 契约就绪度**，非痛感）：4.A `log_check` · 4.D.3——本仓无 embedded producer 契约可 dogfood，待真实 embedded 消费仓需求再起手。
> - 建议批次 = todolist `mlh-p4-target-state`（T78-T84；`openspec/issues/batches.md`）。排序判据 = 目标态 + producer 就绪度，**不是当下痛点**。

### 前置条件
- [ ] 阶段 1-3 完成（高 ROI 项先落）
- [ ] 起手时按**目标态**（非当下痛感）确认 producer 契约就绪度——★ 组随时可起；◐ 组待 embedded 契约

### 目标
- 把 survey 的编排机械步候选（4.A-4.D.4）**按目标态逐项脚本化**，模型不再手做确定性判定；每子项独立一次 change 粒度，按 producer 就绪度排序（**非**按当下痛点取子集）。

### 子任务（每项 ≈ 一次 change，按痛点取子集）
#### 4.A `log_check.py`（P5）
- [ ] 4.A.1 embedded-test-sop 模式 B：`log_check.py --log serial.log --rules *-log-checks.yaml` 解释器（时间窗 + `must_contain`/`must_not_contain`/`must_contain_before` + severity rollup），输出同款 PASS/FAIL 报告；保留 yaml 标「需人眼」的平台侧项给模型。
#### 4.B `maintain_scan.py`（P6）
- [ ] 4.B.1 maintain INDEX↔文件系统 set-diff + CLAUDE.md 过时引用 + bundle 陈旧告警只读报告；保留「新 spec 归哪组 / 是否修复」给模型/人。
#### 4.C `lens_metric_emit.py`（P7）
- [ ] 4.C.1 吃结构化 findings（每条带命中镜集 + 裁决 + sev）→ 归约出格式/字段/enum 正确的 lens-metric 锚行 + 计数；把「数值一致性信任边界」从手数收敛成脚本归约；保留去重 + 对抗裁决给模型。
#### 4.D 小校验器组（P8）
- [ ] 4.D.1 outside-voice 复用守卫（锚 mode + 时间戳 + 结构三判 → reason_code 退出码）。
- [ ] 4.D.2 HR-TG 交集判定（TG 集 ∩ HR-TG 子集 → hit 列表/none + 规范锚串，清单从 trigger-catalog 单一源读；`tg02_hit` 已有先例）。
- [ ] 4.D.3 SOP 模式 A 源码常量/TAG 收割（正则 emit 常量表 name/值/来源:行）。
- [ ] 4.D.4 roadmap Review 处置对账（parse task-log「Review 处置」小节，断言无「未处置」状态）。

### 验收标准
- [ ] 所做子项各有脚本 + 测试；判断部分显式保留；fail-closed。
- [ ] 未做的子项在 task-log 留「本轮不做 + 理由」痕迹（不静默漏）；理由须是**目标态口径**（如「4.A/4.D.3：缺 embedded producer 契约、待就绪」），**不得**用「当下不痛」这类现状快照口径搪塞。

### 交付物
- 按痛点选定的中 ROI 脚本子集 + 测试。

---

## 阶段 5 · 家族① gate 状态锚 → frontmatter（Leg 2）✅ 已交付（change `mlh-p5-gate-frontmatter`，merge `1b069a7`）

### 前置条件
- [x] **ROI 门（显式阈值，冷审 F4）** — ✅ **已过（2026-07-07，GO 变体 a）**：B4/B5 已同类（子串/prose-inline 混淆）两连发、B5 自认「非根治」→ 已达立项线；**GO = 立项待 P2 完成即启**——P2（`e43460c`）已交付，故取变体 a、不等新事故起手（拍板见 task-log「阶段 5 起手 / ROI 门结论」）。〔变体 b「再出 ≥1 例同类 gate 假过/假红更确证」未采用，留作若 P5 中途受阻的回退依据〕
- [x] **核实 ship_gate.py 真实铺设路径** — ✅ **已核（survey 实测）**：`ship_gate.py` **只在 `sdflow-ship/scripts/`、走 skill symlink，非 bundle 回灌消费仓** → 迁移爆炸半径**大降**（不触 `sdflow-init update` 回灌链、消费仓无 tools/ 侧改动）。**归档 inline 锚精确篇数（F6，已回填实测）**：design 阶段估算「88 文件/168 锚行」；P5 完工后用 `grep -rlE '<!-- ship-gate:' openspec/changes/archive/` 精确复核，**实测 85 文件/153 锚行**——design 数字混入了 3 处 prose 里的 `ship-gate: xxx` 反引号提及（grep 命令示例/文档叙述，非真实 `<!-- ship-gate: ... -->` HTML 注释锚），以此实测数为准；差值不影响 P5 迁移范围（dual-read 覆盖全部真实锚，误差不改变 Task1-7 交付面）。
- [x] 阶段 2（anchor-lint）已完成（`e43460c`）——**注（冷审 F1）**：P2 校验度量锚、与 S1 的 gate 锚**不相干**，非 S1 的锚层前置依赖；此处只是 Leg1 先行的顺序结果，不是「P2 为 S1 补机验」。

### 目标
- gate 状态（design-approved/verify=PASS|FAIL/code-review=pass|blocked）迁报告 YAML frontmatter；正文再提及锚串不被误当标记；删 `_line_scoped_hits` 的 **live 报告解析半场**（**归档读半场永久保留**，冷审 F2）。

### 子任务
#### 5.A frontmatter 状态 schema + 产者迁移
- [x] 5.A.1 定义报告 frontmatter 状态 schema（design_approved: bool / verify: PASS|FAIL / code_review: pass|blocked）。
- [x] 5.A.2 三 producer SKILL（spec-review 拍板回写 / done verify / code-review）改写 frontmatter 而非 inline 锚。
#### 5.B gate 消费侧 dual-read + fail-closed
- [x] 5.B.1 `ship_gate.py` 读 frontmatter（**实现取手写 stdlib `parse_ship_gate_frontmatter` 首块锚定、不 import yaml**——follow anchor_lint 零依赖惯例）；**dual-read** 同时认归档旧 inline 锚（`archived_verify_state` 读归档不断）。**注（冷审 F2）**：归档不可变，此归档读路径**永久保留**、非临时窗口。
- [x] 5.B.2 LLM 写坏 frontmatter → 解析异常 fail-closed（判「无有效状态」→ UNKNOWN 停下报告，绝不静默过门）。
- [x] 5.B.3 更新/迁移 gate 锚契约测试（`test_anchor_contract.py`/`test_producer_parser_contract.py`）+ B5 聚合语料测试到 frontmatter。
#### 5.C 解析机器退役（仅 live 半场，冷审 F2）
- [x] 5.C.1 删 `_line_scoped_hits` 的 **live 报告解析半场**（`anchors_in`/`pick_exclusive`×3/peek/`anchor_set` 熔断 helper 全迁）；**`archived_verify_state` 的归档读 `_line_scoped_hits` 永久保留**（归档 inline 锚不可变）——「删整套」订正为「删 live、保留归档读」（本阶段收尾任务）。

### 验收标准
- [x] 报告正文任意提及锚串 → gate 不误判（根治 B4/B5 类；`test_live_body_mention_immune` 等正文免疫测试覆盖）。
- [x] LLM 写坏 frontmatter → gate fail-closed 停下报告，不静默过门。
- [x] 归档旧 inline 锚（实测 85 文件/153 锚行）仍被 dual-read 正确识别。
- [x] 产者↔gate 契约测试全绿；`_line_scoped_hits` **live 解析半场**删除、**归档读半场保留**（冷审 F2）。
- [x] 行为面路径 N/A：survey 已核实 `ship_gate.py` 只在 `sdflow-ship/scripts/`、非 bundle 回灌消费仓，无 `sdflow-init update` 回灌链改动（前置区已定案）。

### 交付物
- 报告 frontmatter 状态 schema；三 producer SKILL 迁移；gate dual-read + fail-closed；契约测试迁移；（窗口后）解析机器删除。

### 尾巴清理（change `mlh-p5-parser-cleanup`，merge `007b00d`，2026-07-08）
> 阶段5 主 change 收尾 defer 的 T74/T75 由后续 cleanup change 清结（非阻塞尾巴，独立一次 change 粒度）：
- [x] **T74** — `parse_ship_gate_frontmatter` 首行 `---` 无闭合由 fail-closed `unterminated` 改判 `absent`（弥合「只认首块」与「写坏 fail-closed」两 Scenario 措辞张力、堵 live 硬崩 UNKNOWN(6)）；`unterminated` 死类别退役；加 live 三读点纯结构诊断提示（不改 parse 签名/verdict/退出码）。delta 修订 spec-workflow「阶段三编排台账确定性」Requirement。
- [x] **T75** — 删 5.C.1 退役后只剩 test 引用的孤儿死符号（`anchors_in`/`pick_exclusive`/`ANCHOR_DESIGN`/`ANCHOR_CR_PASS`/`ANCHOR_CR_BLOCKED` + `ALL_ANCHORS` 收缩 verify-only）；归档 dual-read 现役边界（`ANCHOR_VERIFY_PASS`/`ANCHOR_VERIFY_FAIL`/`_line_scoped_hits`）保留不波及。
- **冷审残差 defer**：T76（归档杂交盲区**非语义** lint/监控硬化后续，设计门已接受净负、冷镜给出更锋利可达性论证供未来复评 ROI）、T77（delta spec「过渡期回退 inline」Scenario 迁移窗已闭宜标历史）→ todolist 批次 `mechanical-layer-hardening`。
- **验证**: verify=PASS；`pytest -W error` 157 passed / 0 warning；spec delta validate valid。

---

## 阶段 6 · 家族② recorder 索引 → frontmatter（Leg 2，north-star 不排期）

### 前置条件
- [x] ~~**ROI 触发器满足**（被动，不主动排期）：「recorder 持续出腐蚀 bug」**或**「想在数据上建工具」（ADR 0010 已决 defer 判据）~~ — **已被端态复核取代（2026-07-08）**：不再等 ROI 触发器，改以「根治 + 达成目标」目标态判据直接选定端态 A（见下方 ✅ 端态决策块）。ADR 0010 原「defer/触发才起」= 快照妥协、本次推翻。可查询基底原是触发器②、现降为 A 的附赠而非前置。

> **✅ 目标态端态决策（2026-07-08，用户已拍板 = 端态 A；todolist T85）**：剥掉「现在腐蚀被堵死所以不做」（现状快照）后，本为端态二选一——**用户以「根治 + 达成目标」判据选 A、否决 B**：
> - **端态 A（选定，迁 frontmatter）**：YAML 原生转义 `｜`/换行 → `｜` 腐蚀类**结构上不可能（治本）**，不是被拦住。删**写侧**机器（`_reject_cell_unsafe` 腐蚀守卫 + `_render_item_table` + 双写的表半场）。**约束①「历史文档不迁」使成本骤降**——变成 P5 gate-frontmatter 已 ship 的成熟范式：新写 frontmatter + 历史表 dual-read 永久冻结只读、**零数据改写**。历史读 `parse_table_rows` 冻结保留（同 P5 归档读半场）。
> - **端态 B（否决，reject-over-restructure）**：写入即 fail-closed 拒 `｜`/换行——**治标**：脆弱表基底不变、永久架守卫；且守卫只守脚本写，**人手编辑数据文件塞 `｜` 直接绕过**（arity 检测仅兜列数变化）。ADR 0010 原选此 = 快照妥协，本次目标态复核推翻。
> - **判据落定**：用户要「根治」→ B 按定义治标出局（永久守一个没修好的基底）；「删整类解析机器」从非能 100% 兑现的字面目标（frontmatter 仍解析、历史读半场永久保留），**根治的真实达成 = 「未来腐蚀结构上不可能」，A 100% 达成**。
> - **排期**：A 是全 roadmap 最大 change（改 3 recorder 写路径 + consumer dual-read 读 + 重写测试套），**压轴排 ★ P4 之后**（4.C 等 ROI 更清晰、隔离项先做）；落地复用 P5 的 fail-closed YAML + dual-read 范式。

### 目标
- recorder 索引层（ID/module/summary/priority/status/time/change/batch）从 markdown 总览表位置切列迁 YAML frontmatter 索引 + prose 块；腐蚀类蒸发 + 删 recorder ~40 处/文件表解析与双写一致机械。

### 子任务
- [ ] 端态 A 已定，实现时单独 explore/design（复用 P5 fail-closed YAML + dual-read 范式；约束①历史文档不迁、仅新写走 frontmatter，届时按当时实况细化，不在本 roadmap 展开）。

### 验收标准
- [ ] 新写记录字段含 `|`/换行的腐蚀类结构上不可能（YAML 转义）；写侧 `_reject_cell_unsafe`/`_render_item_table`/双写表半场删除；历史表 dual-read 冻结只读正确识别（同 P5 归档读半场）；LLM 写坏 frontmatter → fail-closed 不静默。

### 交付物
- （north-star，触发后交付）

---

## 附录 A · 阶段间依赖图

```
Leg 1（脚本化，先行、多数可并行）
  P1 issues.py sweep ──┐（改 issues.py + done SKILL）
  P2 anchor-lint ──────┤（改两审 SKILL 自检步；校验度量锚，与 P5 gate 锚不相干、非 P5 前置，冷审 F1）
  P3 镜像一致性测试 ────┤（纯增测，独立）
  P4 config/batches lint┘（纯增校验器，独立）
  P4' 编排机械步下沉（P5-P8 中ROI，依赖 P1-P3 先落，按痛点子集）
                    │
Leg 2（去字符串化，就绪度分级）
  P5 家族① gate 锚 → frontmatter ◀── 前置：ROI门 + 核铺设路径 + P2 就绪
                    │
  P6 家族② recorder 索引 → frontmatter ◀── north-star，ROI 触发才起（不排期）

并行红线：凡同期改同一 SKILL.md（P2/P4'/P5 都可能触两审或 producer SKILL）→ 串行；改文件集不相交才并行。
```

## 附录 B · 子任务粒度

| 阶段 | 子任务组 | 一次 change 粒度？ |
|---|---|---|
| 阶段 1 | 1.A（sweep） | 是 |
| 阶段 2 | 2.A（anchor-lint） | 是 |
| 阶段 3 | 3.A（镜像测试）/ 3.B（config·batch lint） | 各是；可合批 |
| 阶段 4 | 4.A-4.D（P5-P8） | 每子项各一次；按痛点取子集 |
| 阶段 5 | 5.A/5.B/5.C（迁移+dual-read+**仅退役 live 解析半场**） | 一次大 change（高仪式；退役只删 live 侧、归档读永久保留，冷审 F2） |
| 阶段 6 | north-star | 触发后另 explore |

## 附录 C · 未来 OpenSpec 变更映射

| 阶段 | 建议变更名 | 规范增量落点 |
|---|---|---|
| 阶段 1 | `implement-mechanical-layer-hardening-p1-issues-sweep` | sdflow-issues 自包含约定（sweep 子命令） |
| 阶段 2 | `implement-mechanical-layer-hardening-p2-anchor-lint` | spec-workflow（review 自检 MODIFIED） |
| 阶段 3 | `implement-mechanical-layer-hardening-p3-determ-guards` | recorder skills 自包含 + config schema |
| 阶段 4 | `implement-mechanical-layer-hardening-p4-<子项>` | 各 skill 自包含 |
| 阶段 5 | `implement-mechanical-layer-hardening-p5-gate-frontmatter` | spec-workflow（ship-gate 锚契约 MODIFIED） |
| 阶段 6 | （north-star，触发后命名） | recorder skills 自包含 |

每个实施变更的 proposal 引用本 `roadmap.md` 对应阶段作背景，design 复用 `design.md`，规范增量扩展 `openspec/specs/spec-workflow` 或各 recorder skill 自包含约定。

## 附录 D · 任务完成追踪

执行过程中同步更新 `task-log.md`：完成一个显著子任务组即追加一条；遇计划外情况（ROI 门结论、gate 路径核实结果、S2 触发）必记；每阶段全部完成追加「阶段 N 完成总结」。详见 `task-log.md` 使用约定。
