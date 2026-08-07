> **顺序不可颠倒**——见 `design.md` 的 Migration Plan。第 1 节必须早于第 3 节：反序（先停铺、SKILL 仍探测）
> 会让仍处旧 resolver/pin 状态的存量仓在失效提示下硬停（精确口径见 design Risks「半态危险」条）。
>
> **验收模型**（design「验收三判据」节）：本 change 删除的是一个概念，完整性验收 = ① 概念词表 sweep 归零
> （7.6）② 全仓 pytest 绿且 4 条反向锚在场（7.1）③ 三态真跑（7.3–7.5）。以下各节的 grep 仅是**定位辅助**，
> **必红测试集一律以 pytest 实跑红名单为准，MUST NOT 以 grep 零命中推断「无消费者」**（grep 对 pathlib
> 拼接 / `full=False` / 目录范围外文件结构性失明——spec-review F10–F14 实证）。

## 1. 删除 SKILL 侧 skew 探测段〔Req: host-adaptive-execution · REMOVED「落锚/调 emitter 前探 tools 能力」〕

- [x] 1.1 删除 `sdflow-code-review/SKILL.md` 第零步的 skew 探测整段（现 `:206` 四条信号），其后步序号顺延
- [x] 1.2 删除 `sdflow-spec-review/SKILL.md` 第零步的 skew 探测整段（现 `:180` 两条信号），同样顺延步序号
- [x] 1.3 清理悬空指代〔F24 订正位置〕：真正的悬空指代在**档位解析步**（`sdflow-code-review/SKILL.md:204` / `sdflow-spec-review/SKILL.md:179`）——「空值/unknown 分家判据同下方『skew 探测』的 fail-loud 精神——三处均为…」随探测段删除失去指代对象，改写为不引用已删段（原 tasks 描述的「能力探针步『MUST 排在 skew 探测之后』时序理由」在两个 SKILL 中不存在——该文字在探测段自身内部、随段删除，无需单独处置）
- [x] 1.4 两个 SKILL 中「退出码 2 → 显式降级」的既有分支**保持不变**；逐字比对确认未被误改
- [x] 1.5 验收 grep〔F46 订正豁免清单〕：`grep -n "skew 探测\|lens-metric-enums\|scope-audit:\|_MIRRORS_LEGAL" sdflow-code-review/SKILL.md sdflow-spec-review/SKILL.md` 删段后的剩余命中 MUST 恰为**每文件一处**——各自锚行自检段对契约机读块的**合法**引用（改前位于 `sdflow-code-review:421` / `sdflow-spec-review:271`，删段后行号前移，**以「命中数 = 各 1」为验收，勿按行号**；契约仍在 canonical，该表述 change 后依然成立，保留不动）；1.3 处置后档位解析步不再含「skew 探测」字样
- [x] 1.6 🔴 「两条分发链不可互相替代」段订正为单链表述（改前位于 `sdflow-code-review/SKILL.md:557` / `sdflow-spec-review/SKILL.md:490`，删探测段后行号前移，按文字定位；manifest skew 的修法「回运行 checkout 跑 `bash setup.sh`」保留）。〔F47〕该两行位于 `sdflow:async-branch` marker 区间**内**（以 marker 行定位，勿按行号），受 `hack/check_async_branch_parity.py` 逐字节等值门约束（CI `mechanical-gates` 在跑）：MUST 两文件同改；且 `hack/tests/test_async_branch_parity.py:464` 的断言 `"sdflow-init update" in seg` MUST 同批改写为断言新文案关键词〔F13〕，否则等值门/golden 必红

## 2. resolver 收缩为两步链〔Req: spec-workflow · MODIFIED「规则全局解析 resolver（全局 canonical → 显式降级）」〕

- [x] 2.1 在 **bundle 权威源** `sdflow-init/assets/hack/resolve-workflow.sh` 删除步①（本地 pin 判定，现 `:37-51`）：删 `LOCAL` / `has_wf` / `has_spec` / `has_code` / `total` 及其 any-of 分支与部分残留告警；解析直接从 canonical 开始。〔F34〕头部契约注释 `:2`（「三步链」）与 `:5`（「本地 pin 或全局 canonical」）同批订正为两步链表述
- [x] 2.2 确认退出码集**未变**（`0` / `2` / `64`），`--root`、`--explain`、`SDFLOW_HOME` 三个入参契约原样保留（`SDFLOW_HOME` 语义 = 既有测试隔离契约，见 delta）；`explain()` 的 `source=` 取值此后只剩 `global-canonical`
- [x] 2.3 `hack/tests/` 新增/改写「假 HOME 真跑 bash」用例：**仓内放全套规则副本 + `tools/`，断言 stdout 仍等于全局 canonical 路径**（D13 核心不变量的反向锚；旧实现在此必红）
- [x] 2.4 用例：`SDFLOW_HOME` 指向自备 canonical 时解析命中它并过 `sane()`（守既有**测试隔离契约**——非「冻结」承诺〔设计门 Q4〕）
- [x] 2.5 `sane()` 扩面〔A5 · 形状级判据〕：追加 `tools/` 目录存在且非空 + `lens-metric-contract.md` 非空两条检查；**MUST NOT 枚举具体 `.py` 成员**（理由见 design「sane() 扩面决策」——成员清单会在守卫里复活补丁螺旋）；配反向锚用例：canonical 缺 `tools/` 或 contract → `exit 2`。🔴 **连带（复核补）**：一切「造假 canonical 过 sane()」的既有/新写 fixture MUST 同步补非空 `tools/` + contract——已核实 `sdflow-init/tests/test_resolve_workflow.py` 的 `make_bundle`（`:33-35`，只造 workflow.md + 两 checklists）在扩面后必红；2.4 与 2.6 的新 fixture 同理；CLAUDE.md 测试三层第 2 层的 `SDFLOW_HOME` 沙盒描述（task 6.5②）也须写明这一要求
- [x] 2.6 存量测试处置——**先跑 `/usr/bin/python3 -m pytest sdflow-init/tests/ hack/tests/ sdflow-maintain/tests/` 看谁红，以实跑红名单为准**。已核实的必红项〔F10/F11〕：
  - `sdflow-init/tests/test_resolve_workflow.py:136`（断言 `source=local-pin`）→ 改写为两步链契约
  - `sdflow-init/tests/test_resolve_models.py`（26 用例，`make_bundle_repo` fixture 造 local-pin bundle、`run_resolve` 把 `SDFLOW_HOME` 指向不存在路径）→ fixture 改为把 bundle 放进假 `SDFLOW_HOME` 的 `workflow/` 下、`run_resolve` 指向它（语义不变：测的是 model-tiers 解析，不是 pin）
  - `sdflow-maintain/tests/test_marker_consistency.py:38-48`（`test_resolve_workflow_bash_markers_match_python` 从 resolver 正则提取 `$LOCAL/` 标记）→ **整条删除**（resolver 内联的第 3 份 RULE_MARKERS 副本随步①消失，守卫失去对象——DRY 正向收益）

## 3. 停止铺设 tools/contract，退役 `--dev` 与 full 模式〔Req: spec-workflow · MODIFIED「workflow bundle 改在权威源、经部署下发」〕

- [x] 3.1 `sdflow-init/scripts/init.py` `copy_bundle()`：删除非-full 分支的 `tools/` 整删重拷与 `lens-metric-contract.md` 复制；**只保留** `WORKFLOW-GUIDE.md` 复制与 `include_schema` 的 schema 下发。🔴〔F15〕GUIDE `copy2` 前 MUST 加 `os.makedirs(dst, exist_ok=True)`——现状 `openspec/workflow/` 由 tools `copytree` 隐式创建，删掉后 fresh init 必抛 `FileNotFoundError`（`ensure_dirs` 的 `CORE_DIRS` 只有 `changes`/`specs`）
- [x] 3.2 删除 `full=True` 分支、`ignore_tools_tests()`、`LOCAL_TOOL_CACHES`（先 `grep -rn "LOCAL_TOOL_CACHES\|ignore_tools_tests" .` 确认无其它调用方），并把 `copy_bundle(root, full=dev, …)` 的 `full` 参数一并去掉
- [x] 3.3 退役 `--dev`：argparse 移除 + toolkit-仓根守卫（`:1096-1100`）+ `stale_shadow_warnings` 豁免（〔F33 订正〕实为 `:1144-1146` 的 `if not dev:` 门，非 `:1125`）。〔A6〕留一版 **tombstone**：识别到 `--dev` 参数 → fail-loud 提示「`--dev` 已退役：源仓 dogfood 同样走全局 canonical，无需本地 instance」（否则老用法只得 argparse generic error）
- [x] 3.4 `sdflow-init/tests/` 改写：断言 `init` 后消费仓 `openspec/workflow/` 下**只有 `WORKFLOW-GUIDE.md`**（文件全集断言，非"包含"断言）；断言 `openspec/schemas/<PROJECT_SCHEMA>` 仍在；断言 fresh init（裸 `tmp_path`）不抛异常（F15 的回归锚）
- [x] 3.5 存量测试处置——**先跑 pytest 看谁红**。已核实的必红项〔F12，原 grep 对 pathlib 拼接/`full=False` 零命中〕：
  - `test_init.py` 的 `TestBundleToolsOnly` / `TestPinConsumerUpdateInvariant` 等 `wf / "tools"` 断言群（`:93-112` 等）与 `full=True` 用例群（`:120-172`、`:551+`、`:711`、`:804`）
  - `test_init_contract_sync.py` 整文件（`full=False` + contract 断言）
  - `test_task5_regression.py:39`
  - 其余以实跑红名单为准，逐个改写/删除，MUST NOT 留与新契约矛盾的绿测试

## 4. 告警语义改写〔Req: spec-workflow · MODIFIED「存量消费仓迁移不自动删、残留副本须告警」〕

- [x] 4.1 `init.py` `stale_shadow_warnings()`（`:346`）：〔F22 订正——原「判据函数不动」与「范围扩到 tools」自相矛盾，以本条为准〕**判据扩员**：`RULE_MARKERS` 三项之外增查残留 `tools/` 目录与 `lens-metric-contract.md`；文案改写为**带前置条件的死件表述** + **可复制删除命令**（见 delta「残留副本须告警」Requirement 的文案要求），MUST NOT 输出无条件的「已无任何生效路径」〔F3〕；MUST NOT 新增一次性自动清删代码〔设计门 Q2：人执行命令即达终态零死件〕
- [x] 4.2 〔F25〕第二条告警（checkpoint 孤儿，`:355-358`）的「若保留本地 workflow.md 副本（pin）且其仍引用仓内路径 → 勿删」pin 措辞同批清理（pin 语义已取消，该分支条件不再成立）
- [x] 4.3 `sdflow-maintain` 兜底扫描同步〔Req: maintain-scan · MODIFIED〕：判据扩员 + 死件文案（语义等价即可）；〔F14〕`sdflow-maintain/tests/test_maintain_scan.py:220-229` `test_stale_shadow_only_tools_clean` 按新语义**断言反转**（tools-only 残留 → 现在 SHALL 报死件告警）
- [x] 4.4 文案测试正反双断言：**不含** `显式 pin` / `遮蔽全局` 字样、**含**新死件文案关键词与前置条件提示（只断言"含新词"会让旧文案叠加新词也通过）

## 5. `ship_gate` 失鲜腿退役〔Req: spec-workflow · MODIFIED「workflow bundle 改在权威源」的部署形态后果〕

- [x] 5.1 删除 `sdflow-ship/scripts/ship_gate.py:955-959` 的 `tools_spec` 比较腿（含其两行注释）
- [x] 5.2 〔F44 订正〕退役理由注释**按仓型分开写**：toolkit 源仓——tools 权威源位于顶层条目 `sdflow-init` 之下，已被 `:947-950` 顶层腿覆盖；消费仓——镜像不复存在，「直接改镜像」动作不可能发生。MUST NOT 用「顶层腿覆盖」概括消费仓（消费仓顶层无 `sdflow-init` 条目，实证 `10-michi`）；消费仓侧「canonical 在 review 与 done 之间变更不可见」为 change 前即存在的盲区，已在 design Risks 登记接受
- [x] 5.3 正向锚：改 `sdflow-init/assets/workflow/tools/` 下任一文件后，失鲜判定仍为 `stale`（证明 toolkit 源仓路径由顶层腿覆盖）
- [x] 5.4 〔F23〕反向锚（MUST NOT 省略）：fixture 仓在 `openspec/workflow/tools/` 下造/改一个文件（其余不动）→ 判 `fresh`（证明腿真退役；留着旧腿则此用例红）

## 6. 清理本仓死件 + 面级文档订正（验收 = 7.6 sweep 闭环，MUST NOT 以写死行号为验收）

- [x] 6.1 删除本仓 `openspec/workflow/` 下 7 个文件：`tools/` 全部 6 个 `.py` + `lens-metric-contract.md`；**只留 `WORKFLOW-GUIDE.md`**
- [x] 6.2 `hack/tests/test_yq_wrapper_consistency.py`：从 `TARGETS`（`:57`）删除 `openspec/workflow/tools/anchor_lint.py` 条目；权威源条目保留〔Req: yq-yaml-operations · R12 去计数〕；主 spec `yq-yaml-operations` 的 Purpose 脚本枚举同批订正（Purpose 非 Requirement，直接改主 spec 文件）
- [x] 6.3 `hack/check_encoding_hygiene.py`：删除 `:83` 排除分支。〔F26 定性〕该分支**现在就已不可达**（`TARGET_GLOBS` 五条全 root-anchored），本 change 是顺带清**既存**死码；`hack/tests/test_encoding_hygiene.py` 引用 `openspec/workflow/tools/mirror.py` 的用例（`:91`/`:98`）为**恒真锚**——删除或改写为对 `TARGET_GLOBS` root-anchored 锚定性的正向断言（判据：定点删门必须红）〔Req: encoding-hygiene〕
- [x] 6.4 〔F17〕托管块**权威源**订正（动作对象是源，MUST NOT 直改本仓 CLAUDE.md 托管块——会被下次 update 覆写回）：`sdflow-init/assets/snippets/claude-section.md` 的「本仓有 `openspec/workflow/` 规则副本则用之」×3（`:70/:71/:74`）与「INDEX 同步（仅规则副本 pin 仓…）」（`:89`）；改后对本仓跑 `sdflow-init update` 刷新托管块落地
- [x] 6.5 本仓项目指令非托管区订正：`CLAUDE.md` ①「`openspec/workflow/` 只保留 `tools/`」段改为实际形态；②「开发期测试三层」第 2 层改为 `SDFLOW_HOME` 重定向（测试隔离语义）；③「pin 免疫全局翻动逃生口」表述移除；④ 回滚节补 revert 顺序（`git revert` → 每台机重跑 `setup.sh` → 各仓重跑 `update`，承 design Migration「回滚」段〔F28〕）。〔F18〕`AGENTS.md` 四处同义描述（`:109/:218/:221/:236`）同批订正
- [x] 6.6 〔F21〕「修法文案」面统一口径为「回运行 checkout 跑 `bash setup.sh`」：`sdflow-init/assets/workflow/tools/lens_metric_emit.py:104` · `sdflow-init/assets/hack/resolve-models.sh:74` · `sdflow-upgrade/SKILL.md`（frontmatter `:3` 与 `:160`）· `README.md:119`（GUIDE/schema 用途的 `sdflow-init update` 表述合法保留）
- [x] 6.7 〔F19〕docs 面按 7.6 sweep 命中处置（已知面：`docs/workflow-map.md`「两条分发链」`:234` 等 · `docs/workflow-map.html` · `docs/sdflow-fable5/02-module-reference.md` · `docs/workflow-skills/sdflow-spec-review.md` · `openspec/ROADMAP.md`）
- [x] 6.8 ADR 面：〔F20〕`0003` / `0005` / `0019` / `0036` 各加状态注记（「本条所述 local-pin / 仓内 tools 副本机制已由 adr/0039 取消」指针注记，不重写历史正文）；〔设计门 Q3〕`0038` **删除**（本分支新建、从未进 main、机制从未实现——其候选与砍因写进 0039 取舍段，引用砍因 MUST 写「起手前提被证伪 ⇒ 决策撤销」，MUST NOT 写「问题域消失」〔F32〕）；新落 `openspec/adr/0039-eliminate-dual-distribution-chain.md`：skew 成因（bundle 拷贝链口径 + hack 链/Windows 快照两个残余失鲜面）、pin 两用途分流（测试隔离走 SDFLOW_HOME 既有契约、冻结不立承诺）、`ship_gate` 腿退役推理（按仓型分开）、`WORKFLOW-GUIDE.md` 例外、**回滚步骤**（应急载体之一〔F28〕）、取舍段（版本戳 / 字节比对 / pin-only 判据 / 0038 版本对比）
- [x] 6.9 `openspec/CONTEXT.md` 补 `skew` 术语定义（本该同代的两个组件因更新方式不同而处于不同版本；本 change 后仓内仅剩 `manifest skew` 一处在用）；**`pin` 不入 CONTEXT**（机制已删，历史在 0039）。`T269` 分治关闭：`lens-metric-contract.md` 半**成立**（随 6.1 删除）、`WORKFLOW-GUIDE.md` 半**误判**（保留）；`T270` 关闭理由写「skew 探测段整体移除，问题对象消失」，**MUST NOT 写成"已修复"**
- [x] 6.10 〔F45〕`hack/gen_workflow_guide.py`：把 GUIDE 中指向 sibling 规则文件的相对链接（`./ff-generation-constraints.md` · `./reference/quality-layering.md`×4 · `./workflow-history.md`）降为文字引用或内联对应小节，重新生成 `WORKFLOW-GUIDE.md`——GUIDE **照旧铺进消费仓**（D14 不动，人已确认），但消费仓只有 GUIDE 一个文件，相对链接目标态全断链
- [x] 6.11 记 todo（`sdflow-issues`，用**开发 checkout** 脚本、显式传 change 字段）：① 根因项「hack 链 symlink 化（Unix）」——部署窗口（F2）/ 窗口内告警失真（F3）/ hack 链无守（Q1）三症状同源，`capability-manifest` 扩员（X1）为其备选方案记在同条；② resolver `--help`（X5）；③ `setup.sh` 关键项 skipped 应非零退出（X7）；④ Windows 失鲜 CI 回归用例（Q5 备选）

## 7. 全链路验证（三判据闭环）

- [x] 7.1 `/usr/bin/python3 -m pytest`（全仓）绿，且 4 条**反向锚**用例在场并在实现中途验证过「会红」〔F50：防「删测试凑绿」〕：2.3 副本忽略 / 2.5 `sane()` 扩面 / 4.4 文案双断言 / 5.4 腿退役反向
- [x] 7.2 `openspec validate fix-probe-scan-precision --strict --type change` 绿
- [x] 7.3 **真跑三态**（本机 Darwin，如实记录）：① 正常仓解析 → `global-canonical`；② 仓内放全套规则副本 → **仍** `global-canonical`；③ `SDFLOW_HOME` 指向空目录 → `exit 2` + 告警
- [x] 7.4 在开发 checkout 跑 `bash setup.sh`（测试三层第 3 层，时间盒）后，真跑一次 `/sdflow-spec-review` 或 `/sdflow-code-review` 确认无 skew 探测步、无硬停；**完成后在运行 checkout 重跑 `setup.sh` 还原**
- [x] 7.5 对 `05-sarvelo`（本机唯一存量 pin 仓）跑 `resolve-workflow.sh --explain`，确认 `source=global-canonical`（迁移行为实证锚）
- [x] 7.6 **概念词表 sweep**（全仓 grep **不带 `--include` 限定**，`.py`/`.sh`/`.yml`/`.md` 全吃）：
  - **归零词**：`local-pin` · `两条分发链` · `显式 pin` · `pin 遮蔽` —— 归零（豁免：`adr/0039` 取舍段、`decision-memo.md`、`openspec/changes/archive/**`、本 change 目录内评审产物）
  - **逐条判词**：`规则副本` · `sdflow-init update` · `openspec/workflow/tools` —— 每个命中要么已处置、要么登记进 design BASE-29 节的豁免清单；MUST NOT 留未登记命中

## 测试覆盖图（TG-18）

| code path | 测试类型 | 用例位置 | 错实现会不会红 |
|---|---|---|---|
| resolver 忽略仓内副本 | pytest（假 HOME 真跑 bash） | `hack/tests/` · task 2.3 | ✅ 保留步① 的旧实现在此必红（反向锚） |
| `SDFLOW_HOME` 测试隔离路径 | pytest（同上） | `hack/tests/` · task 2.4 | ✅ 未支持则解析不到自备 canonical |
| `sane()` 形状级扩面 | pytest | `hack/tests/` · task 2.5 | ✅ canonical 缺 tools/contract 仍 exit 0 即红（反向锚） |
| `copy_bundle` 只铺 GUIDE + fresh init 目录创建 | pytest（`tmp_path` + monkeypatch `BUNDLE_SRC`） | `sdflow-init/tests/` · task 3.4 | ✅ 文件全集断言——多铺 `tools/` 即红；漏 `makedirs` 即 `FileNotFoundError` 红 |
| 告警新文案 + 判据扩员 | pytest 正反双断言 | `sdflow-init/tests/` · task 4.4 | ✅ 旧文案叠加新词也会被"不含 `显式 pin`"拦下（反向锚） |
| `ship_gate` 顶层腿覆盖 tools（toolkit 仓） | pytest | `sdflow-ship/tests/` · task 5.3 | ✅ 若顶层腿实际不覆盖，删腿后该用例红 |
| `ship_gate` `tools_spec` 腿已退役 | pytest | `sdflow-ship/tests/` · task 5.4 | ✅ 留着旧腿则「镜像改动判 fresh」用例红（反向锚） |
| 镜像删除的连带（yq 一致性门 / 编码门） | pytest | `hack/tests/` · task 6.2–6.3 | ✅ 不处置则 `test_yq_wrapper_consistency` 因文件不存在必红 |
| async-branch parity 区间同改 | pytest + CI 等值门 | `hack/tests/test_async_branch_parity.py` · task 1.6 | ✅ 两文件不同改即 CI 红；`:464` 断言不改写即红 |
| SKILL 探测段已删 | grep 断言 | task 1.5 | ⚠️ 文本级，**非行为级**——SKILL 是指令资产，无可执行路径可测（诚实边界） |
| 概念删除完备性 | 词表 sweep | task 7.6 | ⚠️ 机械可复核（命中即未完备），豁免表人工登记 |
| 真跑三态 / 全链路 | 人工实跑 | task 7.3–7.5 | ⚠️ 人工，非机械门 |

**诚实边界**：
- SKILL.md 是**指令资产**，其"是否照做"由执行方自报 ⇒ 1.x 的验证只能到 grep 文本级。这是本仓一贯的结构性限制（同 `decision-memo.md` C5），**MUST NOT 声称已机械保证**。
- **Windows 分支的运行时行为在本机（Darwin）测不到**；CI 层（`windows-recorder-smoke.yml` 全量 pytest）会跑到本 change 的全部脚本面，但「旧 SKILL × 新 tools」失鲜场景本身无 CI 用例（记 todo，task 6.11④）。〔F48 订正：MUST NOT 表述为「结构性无测试面」〕
