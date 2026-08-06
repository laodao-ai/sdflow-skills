> **顺序不可颠倒**——见 `design.md` 的 Migration Plan。第 1 节必须早于第 3 节：
> 反序（先停铺 `tools/`、SKILL 仍探测）⇒ **每个消费仓每轮评审永久硬停**。

## 1. 删除 SKILL 侧 skew 探测段〔Req: host-adaptive-execution · REMOVED「落锚/调 emitter 前探 tools 能力」〕

- [ ] 1.1 删除 `sdflow-code-review/SKILL.md` 第零步的 skew 探测整段（现 `:206` 四条信号），并把其后的步序号顺延；保留其后「能力探针」步及其「MUST 排在 skew 探测之后」的时序理由所依赖的其余约束（该理由中对 skew 探测的引用一并移除，MUST NOT 留悬空指代）
- [ ] 1.2 删除 `sdflow-spec-review/SKILL.md` 第零步的 skew 探测整段（现 `:180` 两条信号），同样顺延步序号、清理悬空指代
- [ ] 1.3 两个 SKILL 中「退出码 2 → 显式降级」的既有分支**保持不变**（本 change 不改它，只是让更多情形落到它）；逐字比对确认未被误改
- [ ] 1.4 `grep -n "skew 探测\|lens-metric-enums\|scope-audit:\|_MIRRORS_LEGAL" sdflow-code-review/SKILL.md sdflow-spec-review/SKILL.md` —— 第零步段内归零（其它段落的合法引用如 `:557`/`:490` 的两条分发链说明不计，但其中关于 `openspec/workflow/tools/` 走 `sdflow-init update` 的表述 MUST 同步订正）

## 2. resolver 收缩为两步链〔Req: spec-workflow · MODIFIED「规则全局解析 resolver（全局 canonical → 显式降级）」〕

- [ ] 2.1 在 **bundle 权威源** `sdflow-init/assets/hack/resolve-workflow.sh` 删除步①（本地 pin 判定，现 `:37-51`）：删 `LOCAL` / `has_wf` / `has_spec` / `has_code` / `total` 及其 any-of 分支与部分残留告警；解析直接从 canonical 开始
- [ ] 2.2 确认退出码集**未变**（`0` / `2` / `64`），`--root`、`--explain`、`SDFLOW_HOME` 三个入参契约原样保留；`explain()` 的 `source=` 取值此后只剩 `global-canonical`
- [ ] 2.3 `hack/tests/` 新增/改写「假 HOME 真跑 bash」用例：**仓内放全套规则副本 + `tools/`，断言 stdout 仍等于全局 canonical 路径**（这是 D13 的核心不变量；旧实现在此必红）
- [ ] 2.4 新增用例：`SDFLOW_HOME` 指向自备 canonical 时解析命中它并过 `sane()`（守「冻结规则版本的唯一受支持路径」）
- [ ] 2.5 删除/改写原有断言"仓内副本命中 local-pin"的用例（`grep -rn "local-pin" hack/tests/ sdflow-init/tests/` 逐个处置，MUST NOT 留下与新契约矛盾的绿测试）

## 3. 停止铺设 tools/contract，退役 `--dev` 与 full 模式〔Req: spec-workflow · MODIFIED「workflow bundle 改在权威源、经部署下发」〕

- [ ] 3.1 `sdflow-init/scripts/init.py` `copy_bundle()`：删除非-full 分支的 `tools/` 整删重拷与 `lens-metric-contract.md` 复制；**只保留** `WORKFLOW-GUIDE.md` 复制与 `include_schema` 的 schema 下发
- [ ] 3.2 删除 `full=True` 分支、`ignore_tools_tests()`、`LOCAL_TOOL_CACHES`（确认无其它调用方后再删——先 `grep -rn "LOCAL_TOOL_CACHES\|ignore_tools_tests" .`），并把 `copy_bundle(root, full=dev, …)`（`:1127`）的 `full` 参数一并去掉
- [ ] 3.3 退役 `--dev` 参数及其 toolkit-仓根守卫（`:1096-1100`）与 T15 为它开的 `stale_shadow_warnings` 豁免（`:1125`）；`argparse` 中移除 `--dev`
- [ ] 3.4 `sdflow-init/tests/` 改写：断言 `init` 后消费仓 `openspec/workflow/` 下**只有 `WORKFLOW-GUIDE.md`**（文件全集断言，非"包含"断言——否则多铺文件测不出）；断言 `openspec/schemas/<PROJECT_SCHEMA>` 仍在
- [ ] 3.5 删除/改写测试中对 `--dev`、`full=True`、`tools/` 部署的既有断言（`grep -rn "full=True\|--dev\|workflow/tools" sdflow-init/tests/`）

## 4. 告警文案改写〔Req: spec-workflow · MODIFIED「存量消费仓迁移不自动删、残留副本须告警」〕

- [ ] 4.1 `init.py` `stale_shadow_warnings()`（`:346`）：**检测行为不变**（判据函数不动），改写告警文案 —— 从"遮蔽全局且不再被刷新，删=跟全局 / 留=显式 pin"改为"已无任何生效路径（评审一律走全局），删=清理死件 / 留=无害但无用"；检测范围扩到仓内残留 `tools/` 与 `lens-metric-contract.md`
- [ ] 4.2 `sdflow-maintain` 的兜底扫描同步改文案（`openspec/specs/maintain-scan/spec.md:61` 的 `RULE_MARKERS` 判据本身不改）
- [ ] 4.3 测试断言新文案**不含** `显式 pin` 字样、**含** `已无任何生效路径`（正反双断言；只断言"含新词"会让旧文案叠加新词也通过）

## 5. `ship_gate` 失鲜腿退役〔Req: spec-workflow · MODIFIED「workflow bundle 改在权威源」的部署形态后果〕

- [ ] 5.1 删除 `sdflow-ship/scripts/ship_gate.py:955-959` 的 `tools_spec` 比较腿（含其两行注释）
- [ ] 5.2 在删除处留一行注释说明退役理由：tools 权威源位于顶层条目 `sdflow-init` 之下，已被 `:947-950` 的顶层腿覆盖；该腿唯一多抓的情形（直接改消费仓镜像）在副本取消后不可能发生
- [ ] 5.3 新增/改写测试：**改 `sdflow-init/assets/workflow/tools/` 下任一文件后，失鲜判定仍为 `stale`**（证明顶层腿确实覆盖，而非删掉一条腿就漏判）；这条是 5.1 的正当性锚，MUST NOT 省略

## 6. 清理本仓死件 + 文档与记录订正

- [ ] 6.1 删除本仓 `openspec/workflow/` 下 7 个文件：`tools/` 全部 6 个 `.py` + `lens-metric-contract.md`；**只留 `WORKFLOW-GUIDE.md`**
- [ ] 6.2 `hack/tests/test_yq_wrapper_consistency.py`：从 `TARGETS`（`:57`）删除 `openspec/workflow/tools/anchor_lint.py` 条目——该文件由 6.1 删除，不删条目则测试必红。权威源条目 `sdflow-init/assets/workflow/tools/anchor_lint.py` **保留**〔Req: encoding-hygiene〕
- [ ] 6.3 `hack/check_encoding_hygiene.py`：删除 `:83` 的 `if relative.startswith("openspec/workflow/tools/"): continue` 排除分支（镜像消失后是死代码，且留着会把已消失的尾段连坐风险面留在原地）；跑 `hack/tests/test_encoding_hygiene.py` 确认其中引用`openspec/workflow/tools/mirror.py` 的用例（`:91`/`:98`）同步处置〔Req: encoding-hygiene〕
- [ ] 6.4 `CLAUDE.md` 订正：①「`openspec/workflow/` 只保留 `tools/`」段改为实际形态；②「开发期测试三层」第 2 层（`:226-228`）把"拷规则副本形成本地 pin"改为 `SDFLOW_HOME` 重定向；③ `:237` 的"pin 免疫全局翻动逃生口"改为 `SDFLOW_HOME`；④ `:419` 的「INDEX 同步（仅规则副本 pin 仓/toolkit 源仓适用）」订正
- [ ] 6.5 新落 `openspec/adr/0039-eliminate-dual-distribution-chain.md`：涵盖 skew 唯一成因、pin 两用途的 `SDFLOW_HOME` 替代、`ship_gate` 腿退役推理、`WORKFLOW-GUIDE.md` 例外；砍掉的候选（版本戳 / 字节比对 / pin-only 判据）连同砍因写在取舍段
- [ ] 6.6 `openspec/adr/0038` 头部标 **Superseded by 0039**，注明理由是「问题域消失」而非「结论被推翻」
- [ ] 6.7 `openspec/CONTEXT.md` 补 `skew` 术语定义（本该同代的两个组件因更新方式不同而处于不同版本；本仓在本 change 后只剩 `manifest skew` 一处）；**`pin` 不入 CONTEXT**（机制已删，历史在 0039）
- [ ] 6.8 `T269` 分治关闭：`lens-metric-contract.md` 半**成立**（随 6.1 删除）、`WORKFLOW-GUIDE.md` 半**误判**（保留）；`T270` 关闭理由写「skew 探测段整体移除，问题对象消失」，**MUST NOT 写成"已修复"**
- [ ] 6.9 `docs/workflow-map.md:161/234` 的「两条分发链」表述订正为单链

## 7. 全链路验证

- [ ] 7.1 `/usr/bin/python3 -m pytest`（全仓）绿
- [ ] 7.2 `openspec validate fix-probe-scan-precision --strict --type change` 绿
- [ ] 7.3 **真跑三态**（本机 Darwin，如实记录）：① 正常仓解析 → `global-canonical`；② 仓内放全套规则副本 → **仍** `global-canonical`；③ `SDFLOW_HOME` 指向空目录 → `exit 2` + 告警
- [ ] 7.4 在开发 checkout 跑 `bash setup.sh`（测试三层的第 3 层，时间盒）后，真跑一次 `/sdflow-spec-review` 或 `/sdflow-code-review` 确认无 skew 探测步、无硬停；**完成后在运行 checkout 重跑 `setup.sh` 还原**
- [ ] 7.5 对 `05-sarvelo`（本机唯一存量 pin 仓）跑一次 `resolve-workflow.sh --explain`，确认输出 `source=global-canonical`（迁移行为的实证锚）

## 测试覆盖图（TG-18）

| code path | 测试类型 | 用例位置 | 错实现会不会红 |
|---|---|---|---|
| resolver 忽略仓内副本 | pytest（假 HOME 真跑 bash） | `hack/tests/` · task 2.3 | ✅ 保留步① 的旧实现在此必红 |
| `SDFLOW_HOME` 冻结路径 | pytest（同上） | `hack/tests/` · task 2.4 | ✅ 未支持则解析不到自备 canonical |
| `copy_bundle` 只铺 GUIDE | pytest（`tmp_path` + monkeypatch `BUNDLE_SRC`） | `sdflow-init/tests/` · task 3.4 | ✅ **文件全集断言**——多铺 `tools/` 即红 |
| 告警新文案 | pytest 正反双断言 | `sdflow-init/tests/` · task 4.3 | ✅ 旧文案叠加新词也会被"不含 `显式 pin`"拦下 |
| `ship_gate` 顶层腿覆盖 tools | pytest | `sdflow-ship/tests/` · task 5.3 | ✅ 若顶层腿实际不覆盖，删腿后该用例变绿→红 |
| 镜像删除的连带（yq 一致性门 / 编码门） | pytest | `hack/tests/` · task 6.2–6.3 | ✅ 不处置则 `test_yq_wrapper_consistency` 因文件不存在必红 |
| SKILL 探测段已删 | grep 断言 | task 1.4 | ⚠️ 文本级，**非行为级**——SKILL 是指令资产，无可执行路径可测（诚实边界） |
| 真跑三态 / 全链路 | 人工实跑 | task 7.3–7.5 | ⚠️ 人工，非机械门 |

**诚实边界**：
- SKILL.md 是**指令资产**，其"是否照做"由执行方自报 ⇒ 1.x 的验证只能到 grep 文本级。这是本仓一贯的结构性限制（同 `decision-memo.md` C5），**MUST NOT 声称已机械保证**。
- **Windows 分支全程未被自动化覆盖**——`IS_WINDOWS` 由 `uname -s` 决定、无环境变量覆盖入口（`hack/tests/test_install_agents.py:14` 自述）。3.x/4.x 中与平台相关的部分在本机（Darwin）测不到。
