# 设计评审报告 · fix-probe-scan-precision

> 阶段二 `/sdflow-spec-review` 编排评审。**本轮针对 commit `0f8b0a3`（相位 C 重写四件套）后的盘面**——
> 上一轮报告（18:48）早于四件套重写（23:16），其结论不予复用。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="TG-07,TG-17" declared="TG-07,TG-10,TG-12,TG-14,TG-17,TG-18,TG-19,TG-20,TG-22,TG-23,TG-25" evidence="resolver 的 stdout 来源语义由『目标仓或全局』收缩为『仅全局』(TG-07)；删步①后 $RULES_ROOT/tools/*.py 不再可能来自被评审仓自身，信任边界改变 (TG-17)" -->
<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="codex" reason_code="ok" findings="2" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="6" sev="致1/高3/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="36" 采纳="34" 裁掉="1" defer="1" 独立="34" sev="致3/高12/中17/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="2" sev="致0/高1/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="3" sev="致0/高1/中2/低0" -->

---

## 一句话结论

**方向成立、范围成立、论证与落地清单不成立。**

本 change 的方向（消灭被探测的对象，而不是把探测做得更准）经 **11 个独立视角**审视后无一反对；
范围由人明确拍板（D13 证据锚），不予改动。不成立的是两样东西：

1. **承重论证里有五处可证伪的事实陈述**（F1 / F3 / F26 / F48 / F49），其中两处已写进**将被归档进主 spec 的 Requirement 正文**；
2. **落地清单是点补而非面治**——tasks 用 `grep` 枚举受影响的消费者，而 grep 对 Python path-join、`full=False`、
   函数名下划线写法、以及**目录范围之外**的文件结构性失明。已实证漏掉 **6 个必红测试文件、4 份主 spec、1 个 CI 等值门**。

**建议：不进设计 HARD-GATE，先修 P0 清单（下方 §必修）再拍板。** 这不是"阻断"——是把拍板往后挪一步，
因为**拍板批准的是盘面**，而当前盘面里有两条假陈述正要进归档记录。

---

## 评审规模（诚实登记）

| 层 | 数量 | 说明 |
|---|---|---|
| Step1 广审（autoplan，原生执行） | 6 声 | CEO/Eng/DX 三阶段 × (codex 声 + Claude 独立子代理)，无一降级、无一代笔 |
| Step2 领域镜 | **0** | config.yaml 明写本仓不命中 `backend·go`/`embedded`/`frontend`；TG-01/02/03 判定一致。**依据充分的判定，非省略** |
| Step2 对抗镜 | 3 | A=证伪已有 findings（裁决镜）· B=实现期爆炸 · C=乐观估计与边界声明 |
| Step2 接地镜 | 1 | dispatch①，与 Step1 并行；85+ 条代码事实核验 |
| outside-voice | 2 站点 | `design-voice` + `hr-tg`（HR-TG∩≠∅），均跨模型（host=claude / runner=codex）、exit 0 |
| **合计独立视角** | **11** | 主 session 另做了 12 处亲验（含 3 次真实变异实验） |

**复用守卫**：`outside_voice_guard.py` 判 `section-not-found`（exit 1）⇒ **显式降级、自跑设计 voice**，未静默吞。

**基线**：`/usr/bin/python3 -m pytest` = 2469 passed / 10 skipped（全绿）；`openspec validate --strict` = valid。

---

## 决策登记区

```
  ┌──────────────────────────────────────────────────────────────────┐
  │ [自动决策] A1–A12   已按 6 原则决，默认接受，可在设计门覆盖        │
  │ [需拍板]  Q1–Q5     人在 HARD-GATE 一次性决                      │
  │ [已裁掉]  X-1–X-8   reviewer 原始发现 + 裁掉理由，可审计不静默丢   │
  └──────────────────────────────────────────────────────────────────┘
```

### 需拍板（5 条）

**Q1｜删掉探测器后，仅存的 `~/.sdflow/hack/` 拷贝链要不要留一条机验？**
三镜（CEO×2、Eng-codex）独立给出同一建议：扩 `capability-manifest` 成员到安装目录全体 + 第零步无条件验一次（<10 行 + 一条 pytest）。
- **推荐：不做**（DEFER 记 todo），**但 F1 的事实错误 MUST 订正**——design 那句「该链由 capability-manifest 独立守」改为「该链目前无守，登记为诚实边界」。
- 三镜：**系统镜** 做=新增跨 change 的机验依赖；不做=仅存链无守，但失败形态是**响的**（旧 resolver 语义未变，`sane()`/`exit 2` 照常）。**用户镜** 做=窗口期得 actionable 硬停；不做=pin 仓窗口期从"起手硬停"降为"末步裸崩"（本机 1 个仓）。**开发循环镜** 做=多一个 change 的 scope；不做=零成本。
- **主次：开发循环镜为主**——受害面 = 1 个仓 × 一个可由「pull → **立即** setup」纪律关闭的窗口。

**Q2｜要不要在停铺前做「最后一次托管子树清删」（X3）？**
- **推荐：做。** 红线（"不自动删除"）的对象经实读确认是**规则文件本体**（`spec-workflow/spec.md:300`），`tools/` 是**托管子树**、
  "整删重拷"已是 spec 明文授权的既有 Scenario（`:194/:202`）。
- 🔴 **对抗镜 A 的成本修正**：X3 **不是免费的**——task 3.1 删掉的正是唯一能执行清删的那段 `rmtree`，
  采纳 X3 必须**显式新增一次性清删逻辑**，不能指望"既有机制顺带跑一次"。
- 三镜：**系统镜** 终态零死码 vs 每仓永久留一份可执行死 `.py`；**用户镜** 少一次"这些文件要不要删"的判断；
  **开发循环镜** 多写 ~5 行 + 一条测试（回滚后需重跑 update，而 `design.md:172` **已经**要求这一步，代价为零新增）。
- **主次：系统镜为主。** 备选（照原样）：接受每仓永久死码 + 靠告警提示。

**Q3｜`adr/0038` 留还是删？**
它在**本分支**新建（commit `164bb88`）、从未进 main、其 Decision（版本对比机制）**从未实现**，现在同一 change 内标 Superseded。
而 tasks 6.5 已要求 0039 的取舍段涵盖被砍候选（含版本戳）⇒ 内容会重复一份。
- **推荐：删除 0038，只落 0039**，理由写进 0039 取舍段。
- 三镜：**系统镜** 少一份"描述从未存在过的机制"的档案；**用户镜** 未来读者不被一条 born-superseded 的 ADR 误导；**开发循环镜** 少一次 supersede 记账。**主次：用户镜为主**（DOC-1「正文即最终态」同构）。
- **备选**（保留并标 Superseded）：ADR 追加不删是常规。**若选此，理由 MUST 改为「起手前提被证伪 ⇒ 决策撤销，机制从未实现」，MUST NOT 写「问题域消失」**（F32）。

**Q4｜`SDFLOW_HOME` 这条「冻结规则版本」的 SHALL，是修还是撤？**
- ⚠️ 本条经对抗镜 A 修正后**弱于初判**：该 SHALL 的主语是**操作者**（人手动设 env），design Non-Goals 已明写不提供新机制 ⇒ "无仓级 producer"不构成有效指控（F5 已裁掉降 low）。
- 但两条**站得住的**残余仍在：**F4**（`SDFLOW_HOME` 复用为 `setup.sh` 安装根，在"冻结源本身由某个 checkout 的 setup.sh 生成"这一自然搭建方式下会被静默解冻）+ **F42**（实测：`SDFLOW_HOME=<被评审仓>/openspec` 让两步链 resolver 返回**被评审仓自己的** workflow 目录，并标 `source=global-canonical`，直接证伪 delta `:14` 那条「仓内副本 MUST NOT 影响解析结果」）。
- **推荐：保留能力、收紧断言**——① delta `:14` 的绝对句加限定（"在未显式设置 `SDFLOW_HOME` 覆盖的前提下"）；② `SDFLOW_HOME` 的语义在 spec 里明写为「受信任操作者的特权覆盖」；③ 可发现性缺口（F30）记 todo。
- **备选 A**：撤销该 SHALL、写进 Non-Goals（代价：CLAUDE.md 测试三层第②层需另写替代）。**备选 B**：`realpath` 后拒绝 canonical 落在被评审 `--root` 内（新增机制，属加宽，不推荐）。
- 三镜：**系统镜** 收紧断言=删一个假不变量，零新机制；**用户镜** 冻结能力保留；**开发循环镜** 零成本。**主次：系统镜为主。**

**Q5｜Windows 边界的措辞怎么改？（新增，由对抗镜 C 触发）**
四件套五处宣称「本仓对 Windows 分支**结构性无测试面**」，据此把 Windows 失鲜列为"死结、不做任何缓解"。**该陈述已被仓内 CI 证伪**（见 F48）。
- **推荐：只订正措辞、不新增 CI 测试。** 把"结构性无测试面"改为准确表述：「**运行时自检**不可能（检查者与被检查者同为一次 `cp -r` 产物，此论证成立）；**CI 层面可测但目前未测**」。
- 三镜：**系统镜** 订正=零成本，补 CI 回归=~30 行 yaml；**用户镜** 无感知差异；**开发循环镜** 订正后未来读者不会把"没做"误读成"做不到"。**主次：用户镜为主**（该假陈述正要进归档 spec）。
- **备选**：顺带补一条 CI 回归（checkout 旧 → setup → checkout 新 → 断言失败是响的）——按通则④五问，概率低 × 失败形态是响的 ⇒ **记 todo 即可，不在本 change 做**；但前提是文档如实写"未做"而非"不可能"。

### 自动决策（12 条，默认接受）

| # | 决策 | 分类 | 依据 |
|---|---|---|---|
| A1 | 模式 = SELECTIVE EXPANSION | Mechanical | autoplan override |
| A2 | Design 阶段跳过 | Mechanical | 无 UI scope（grep 证据） |
| A3 | DX 阶段执行 | Mechanical | DX scope 命中 |
| A4 | 实现路径 = **APPROACH B**（照原样交付 + 零新机制的三处收口） | Taste | 只修假陈述与目标态缺口，不动 scope |
| A5 | X2（扩 `sane()` 覆盖 tools/contract）**进 scope** | Taste | canonical 成唯一 tools 源 ⇒ 健全性面必须跟着扩，不扩=缩水（通则③） |
| A6 | X4（`--dev` 留一版 tombstone）**进 scope** | Mechanical | ~5 行；否则老用法只得 argparse generic error |
| A7 | X1（扩 capability-manifest）**DEFER 记 todo** | Taste | 属 hack 链，Non-Goals 已声明不动；本 change 只需**不谎称它已被守** |
| A8 | X5（resolver 加 `--help`）**DEFER 记 todo** | Mechanical | 与本 change 目标正交 |
| A9 | `workflow-release` 键 + 版本化原子安装 **拒绝** | Taste | 加宽；人拍的板是"去掉 pin、规则共享"（通则③） |
| A10 | "拆 5 个 release 分阶段迁移" **拒绝** | Taste | 其第 3 步（保留探测跑一版）在 global-only 解析下探测**恒过**，零收益（通则④） |
| A11 | Eng-Claude「pin 仓不算退化」vs CEO「降级」**分治采纳** | Taste | 非 pin 仓前者对；pin 仓窗口期后者对（解析**结果**不变，**失败形态**从起手硬停降为末步裸崩） |
| A12 | 「其余 tools 未验 fail-closed」前提**当场结掉** | Mechanical | 通则①：6 个 tool 全 argparse `required=True` 无静默默认；运行时真读版本化契约的只有 3 个（`anchor_lint`/`hr_tg_intersect`/`lens_metric_emit`），恰为已核那 3 个 |

### 已裁掉（反静默压制 · 8 条）

| # | 原始发现（镜） | 裁掉理由 |
|---|---|---|
| X-1 | codex-CEO：改用 `~/.sdflow/releases/<id>/` + `current` 原子指针 | 加宽。人拍板方向是"去掉 pin、规则共享"，不是建版本化发布系统（通则③） |
| X-2 | codex-CEO：分 5 个 release staged migration | 其第 3 步在 global-only 解析下探测恒过 ⇒ 多一个 release 周期换零收益（通则④） |
| X-3 | codex-CEO：pin 有 6 条属性、`SDFLOW_HOME` 全不满足 ⇒ 应保留 pin | 属性对比成立（已并入 Q4 论据），但**结论**不采纳：删 pin 是人的明确指示（D13） |
| X-4 | codex-eng / codex-DX：blocking，先修完再批准 | "阻断"是建议不是裁决。本报告改为把清单列为**拍板前必修**，人拍板即放行——流程等价、不越权 |
| X-5 | Eng-Claude：pin 仓"不算退化" | **部分裁掉**：解析结果确实不变（保留），但失败形态退化（不保留）。见 A11 分治 |
| X-6 | codex-DX：`stale_shadow_warnings` 应实调 resolver 验 `source=` 再宣称死件 | 降为备选。让告警函数 exec 另一脚本引入新耦合；更简等价解 = 文案不写绝对断言（通则④） |
| X-7 | codex-eng：`setup.sh` 关键项 skipped 应非零退出 | 超本 change scope（改 `setup.sh` 失败语义是独立 change）。记 todo |
| X-8 | 主 session 初判 F5「`SDFLOW_HOME` 无仓级 producer 是缺陷」 | **被对抗镜 A 打掉**：该 SHALL 主语是操作者、Non-Goals 已声明不提供机制；且我把"harness 内 export 不跨调用"与"启动前 shell export 可继承"混为一谈。降 low，残余并入 F30/Q4 |

---

## 必修清单（拍板前）

### P0 · 假陈述（会进归档记录）

| ID | 位置 | 现状 | 应改为 |
|---|---|---|---|
| **F1** | `design.md:109-111` | 「`~/.sdflow/hack/` 那条链由 `capability-manifest.json` **独立守**」 | 「该链目前**无守**（manifest 成员仅 `outside-voice-job.py`/`outside-voice.sh`/`skill-principles.md` 三项，不含 `resolve-workflow.sh`，且只在 codex 宿主后台 voice 分支被消费），登记为诚实边界」 |
| **F49** | `specs/spec-workflow/spec.md:65`（**MODIFIED Requirement 正文**） | 「消费仓副本是 skew 的**唯一**成因」 | 「消费仓副本是**当前已知的主要** skew 成因；取消复制消灭该类问题**在完整 `git pull` + `bash setup.sh` 之后生效**，不消灭 `~/.sdflow/hack/` 拷贝链与 Windows SKILL 快照的失鲜」 |
| **F48** | `specs/host-adaptive-execution/spec.md:16` + `proposal.md:133` + `design.md:144-145` + `decision-memo.md:98-101/281-282` | 「本仓对 Windows 分支**结构性无测试面**」 | 「**运行时自检**不可能（检查者与被检查者同为一次 `cp -r` 产物）；**CI 层面可测但目前未测**」 |
| **F26** | `specs/encoding-hygiene/spec.md:46-49` + `tasks.md 6.3` | 「镜像消失后该排除分支成死代码」 | 「该分支**现在就已**不可达（`TARGET_GLOBS` 五条全 root-anchored，从不把 `openspec/workflow/tools/**` 纳入候选集），本 change 顺带清掉这个**既存**死码」；其守卫用例是**恒真锚**，应删除或改为对 `TARGET_GLOBS` 锚定性的**正向**断言 |
| **F3** | `tasks.md 4.1` 规定的新文案 | 「已无**任何**生效路径」 | 去掉绝对断言 + 给动作：「评审一律走全局规则；**若你刚 `git pull` 还没跑 `bash setup.sh`，先跑 setup 再判断**。删=清理死件 / 留=无害但无用」 |
| **F42** | `specs/spec-workflow/spec.md:14` | 「仓内 `openspec/workflow/` …**都 MUST NOT 影响解析结果**」 | 加限定：「**在未显式设置 `SDFLOW_HOME` 覆盖的前提下**…」（实测反例见下） |

### P0 · 漏掉的必红测试（tasks 的检测方法结构性失明）

| ID | 文件 | 为什么 tasks 的 grep 看不见 |
|---|---|---|
| **F10** | `sdflow-init/tests/test_resolve_models.py`（**24/26 用例**） | fixture 用 local-pin 注入测试 bundle、`SDFLOW_HOME` 故意指向不存在路径；两条 prescribed grep **只命中第 39 行一条中文注释** |
| **F11** | `sdflow-maintain/tests/test_marker_consistency.py:38-48` | 从 resolver 正则提取 `$LOCAL/` 三个标记；**该目录不在 task 2.5 的 grep 范围内** |
| **F12** | `test_init.py`（`TestBundleToolsOnly` / `TestPinConsumerUpdateInvariant`）· `test_init_contract_sync.py`（整文件）· `test_task5_regression.py:39` | 断言写成 `wf / "tools"`（pathlib）与 `full=False`；task 3.5 的 grep 实跑**零命中** |
| **F14** | `sdflow-maintain/tests/test_maintain_scan.py:220-229` | `test_stale_shadow_only_tools_clean` 与 task 4.x 新语义冲突 |
| **F13** | `hack/tests/test_async_branch_parity.py:464` | 断言 `"sdflow-init update" in seg`；task 1.4 若整句删除即红（**取决于改写方式**，非"必红"） |
| **F47** | 同上文件的**等值门本体** | task 1.4 要改的 `:557`/`:490` 落在 `sdflow:async-branch` marker 区间内，该区间被 `check_async_branch_parity.py` 断言**两文件逐字节相同**且**在 CI 里跑**；tasks/design/proposal 三份文档零次提及 |

🔴 **面级修法**（不是逐条补）：把 tasks 2.x/3.x 的验收动作从「跑 grep 枚举」改为「**先跑一遍相关目录的 pytest 看谁红**」。
这是 CLAUDE.md **基准 5** 的同构应用——grep 是在用字符串匹配**猜**"哪些断言依赖将被删的东西"，正解是**让 pytest 自己回答**。

### P0 · 未声明的主 spec 分叉（归档后自相矛盾）

| ID | spec | 冲突点 |
|---|---|---|
| **F6** | `spec-workflow/spec.md:871` + Scenario `:935-938` | 另一条 Requirement（「评审报告锚自检由确定性脚本判定」）仍规定 contract 与 tools 经 `sdflow-init update` **同批下发** + local-pin Scenario。**不在 delta 内** |
| **F7** | `maintain-scan/spec.md:61/63` + Scenario「workflow 仅剩 tools → 判干净」 | 与 task 4.2 要求的新告警语义**直接冲突**。未声明 delta |
| **F8** | `workflow-metrics/spec.md:62` | 明写 `ignore_patterns("tests")` **MUST 保留**；task 3.2 要删 `ignore_tools_tests()`。未声明 delta |
| **F9** | `yq-yaml-operations/spec.md:4-6` + `:228` | 「**7 个**脚本」计数在 task 6.2 删 TARGETS 条目后失真。未声明 delta |

🔴 **根因是 F40，不是这四条**：本 change **命中 TG-25**（版本化多文件协议 / 契约文档套件变更——"改一处契约牵连一组文档"），
其必填槽是 `design: 协议文档套件 scope-check 表（BASE-29）`，而 `design.md` 里该表出现 **0 次**。
**那张表正是"改这条契约会牵连哪组文档"的枚举器**——它的缺席是 F6–F9 与 F17–F21 整簇的共同根因。
**补上 BASE-29 表，这两簇一起消失**；逐条补则下轮还会漏。

### P0 · 实现层具体缺陷

| ID | 缺陷 | 严重度裁定 |
|---|---|---|
| **F15** | task 3.1 删 tools copytree 后，`openspec/workflow/` **无人创建**（`ensure_dirs` 的 `CORE_DIRS` 只有 `changes`/`specs`），`copy2(GUIDE)` 必抛 `FileNotFoundError`，**每个新装消费仓的 fresh init 都会撞** | 对抗镜 A 建议升 critical（影响面=全部新增消费仓）；主 session 裁定 **high**——现有测试 `copy_bundle(str(tmp_path))`（`test_init.py:91/128/220`）在**裸 tmp_path** 上调用 ⇒ 第一次 pytest 就红，**不会静默出厂**。修法：3.1 原文加 `os.makedirs(dst, exist_ok=True)` |
| **F16** | `sane()` 只查 `workflow.md` + 两个 checklists，**不查它此后独家交付的 `tools/`+contract** ⇒ 半坏 canonical 仍 exit 0，故障延迟到实际调工具时裸崩 | high。目标态下 canonical 从"来源之一"变成"独家来源"，健全性面必须跟着扩（已由 **A5** 接受进 scope） |
| **F44** | `ship_gate` 退役 `tools_spec` 腿的论证（"tools 权威源在顶层条目 `sdflow-init` 之下"）**只在 toolkit 源仓成立**——实测消费仓 `10-michi` 顶层**无** `sdflow-init` 条目；change 后 canonical 在仓外，**两条腿都看不见**评审机械层在 code-review 与 done 之间变了 | high。至少写进 Risks；或在 code-review 报告落 canonical bundle identity 供 done 比对 |
| **F23** | task 5.3 的测试是**单向锚**——留着 `tools_spec` 腿也照绿，证不出退役 | medium。补反向用例：只改遗留镜像 → 判 `fresh` |
| **F46** | task 1.4 的豁免清单**点错了**：那条 grep 根本不命中 `:557`/`:490`；真正残留的是 `:271`/`:421`（`anchor_lint` 自检段对 `lens-metric-enums` 的**合法**引用）⇒ 照字面验收可能反手误删合法描述 | high |
| **F24** | tasks 1.1/1.2 **错标悬空指代位置**：所谓"能力探针步的『MUST 排在 skew 探测之后』时序理由"在两个 SKILL 里**都不存在**；真正的悬空引用在 `code-review:204` / `spec-review:179` 的**档位解析步** | medium |
| **F22** | task 4.1 **自相矛盾**：「检测行为不变（判据函数不动）」vs「检测范围扩到 `tools/` 与 contract」——后者必须动 `RULE_MARKERS` | medium |

### P1 · 托管块与文档面（面治，不是点补）

| ID | 面 | 说明 |
|---|---|---|
| **F17** | `sdflow-init/assets/snippets/claude-section.md:71/74/89` | **推给每个消费仓的托管块权威源**仍写「仓内规则副本优先」「pin 仓 INDEX 同步」。且 `CLAUDE.md:401/404/419` 那几行**在托管块内** ⇒ 只改 CLAUDE.md，下次 `update` 会把旧文字**原样注入回来** |
| **F18** | `AGENTS.md:109/218/221/236` | 四处同义描述，task 6.4 只字未提 |
| **F19** | `docs/workflow-map.html`(5 处) · `docs/workflow-map.md`(另 2 处) · `docs/sdflow-fable5/02-module-reference.md` · `docs/workflow-skills/sdflow-spec-review.md:83` · `openspec/ROADMAP.md:34` | task 6.9 只点了 2 个行号。**建议改为 grep 扫描而非写死行号**（写死行号本身违反本仓"别硬编码数字、让脚本自己报"的取向） |
| **F20** | `adr/0003`(:8/:37/:44) · `adr/0005`(:5/:19) · `adr/0019`(:36) · `adr/0036` | 核心结论仍是 local-first / tools 副本 / pin；只 supersede `0038` 不够 |
| **F21** | `lens_metric_emit.py:104` · `resolve-models.sh:74` · `sdflow-upgrade/SKILL.md:160` · `README.md:119` | 「修法文案」面仍指向 `sdflow-init update`，而该命令 change 后对 workflow 已**无作用**。口径应只剩一个：「回运行 checkout 跑 `bash setup.sh`」 |

### P1 · DX（6 维中 5 项 CONFIRMED-NO，综合 2.4/10）

| ID | 问题 |
|---|---|
| **F28** | design 要求的「revert 说明」**无任何任务产出**，且 design.md 归档后不是应急回滚时会翻的地方 ⇒ 应写进 `CLAUDE.md` 的"回滚"节或 `adr/0039` |
| **F30** | `WORKFLOW-GUIDE.md`（消费仓**唯一常驻**人读文档）对 `SDFLOW_HOME` **零次提及**（实测 `grep -c` = 0）⇒ 逃生口对消费仓的人不可发现 |
| **F45** | 该手册有 6+ 条指向同目录文件的相对链接（`./ff-generation-constraints.md`、`./reference/quality-layering.md`×4、`./workflow-history.md`），目标态下**全部断链** ⇒ D14 保留它的**唯一理由**（"不用跳文件的完整参考、随仓走"）恰恰被击穿 |
| **F29** | `--dev` 直接从 argparse 删除 ⇒ 老用法只得 generic error，无迁移引导（已由 **A6** 接受 tombstone 进 scope） |
| **F31** | resolver `exit 2` 固定文案在 `SDFLOW_HOME` 自定义场景**指错方向**（"跑 setup.sh"对修一个自建目录毫无帮助） |
| **F25** | `stale_shadow_warnings` 的**第二条**告警（checkpoint 孤儿）仍含 pin 措辞；task 4.1/4.3 只覆盖第一条 |
| **F43** | 两个 SKILL 与 `sdflow-roadmap` 里 `$RULES_ROOT/...` **未加引号**；`test_resolve_workflow.py:115-123` 已测 resolver 侧支持含空格路径，但**消费者侧会被拆 argv**（测了生产者、没测消费者） |

### P2 · 论证质量（不改结论，改论证）

- **F35** 「真阳 0 · 假阳 1」ROI 无分母、样本 n=1、真阳目标（05-sarvelo）**从未跑过评审** ⇒ 分子被结构性低估。**建议把 ROI 从承重位降为旁证**——结构论证（窗口在主流配置下不存在）已足够支撑删除。
- **F37** 「P0 缺一即每个消费仓每轮永久硬停」**演绎不出来**：半态 (a) 只影响存量 pin 仓（本机 1 个），半态 (b) 探测恒过零影响。捆不捆可照旧（都是删除、量小），但**依据要改**——用假灾难当依据，会在下一轮评审被当成既定事实继承。
- **F50** Success Metric「全仓 pytest 绿」**可被"删测试"而非"补断言"满足**——鉴于 F10–F14 会让大批测试变红，该指标无法区分"正确改写"与"简单删除"。建议下沉到 TG-18 覆盖图的粒度。
- **F32** `adr/0038` 的 Superseded 理由（见 Q3）。
- **F51** 「GUIDE 陈旧无害」的隐藏台阶：`gen_workflow_guide.py --check` 在 `setup.sh` 里是 **warn-only 不阻断**、且**不在 CI 的 mechanical-gates 里**（该 workflow 只跑 `check_async_branch_parity.py` + `sync_principles.py --check` + pytest）⇒ canonical 侧手册自身的新鲜度也只有软兜底。低危、存量问题，**不必在本 change 解决**，但表述可更精确。
- **F27** delta spec 自相矛盾：`:68`/`:83-85` 说查看器资产随 tools **整删重拷**清除，`:73` 又说存量不自动删 + 目标实现**不再触碰** tools ⇒ 该 Scenario 不可达。
- **F33**（接地镜）tasks 3.3 的豁免行号 `:1125` 实为 `:1144-1146`。**F34** `resolve-workflow.sh` 头部契约注释 `:5`/`:37` 未列入 2.1 更新范围。

### 正向发现（建议补记进 proposal）

- **F39** 本 change **收缩了攻击面**：删步①后，对一个不可信仓跑 `/sdflow-code-review` 不再会执行该仓自带的 `openspec/workflow/tools/*.py`。四件套完全没记这一笔，而它是本 change 的**真实收益**之一。
  ⚠️ 但受 **F42** 限定：若把 `SDFLOW_HOME` 指向被评审仓，该性质失效 ⇒ 记录时须带此限定。
- **F41** 命中 TG-17 却**无 BASE-28（安全与数据保护）段**；命中 TG-07 却无契约前后对照。两个槽都该补。

---

## 关键实证（主 session 亲验，非转述）

**① F42 —— 造真两步链复现 `SDFLOW_HOME` 绕回**

```bash
$ sed '37,51d' sdflow-init/assets/hack/resolve-workflow.sh > /tmp/resolve-two-step.sh   # 删步①
$ grep -c "LOCAL\b" /tmp/resolve-two-step.sh
0                                                          # 确认是真两步链
$ SDFLOW_HOME=/tmp/ov_probe/repo/openspec /tmp/resolve-two-step.sh --root /tmp/ov_probe/repo --explain
resolve-workflow: source=global-canonical path=/tmp/ov_probe/repo/openspec/workflow
/tmp/ov_probe/repo/openspec/workflow                       # ← 返回了被评审仓自己的目录，还标成 global-canonical
```

**② F48 —— 仓内确实有 Windows CI**

```bash
$ ls .github/workflows/
mechanical-gates.yml   windows-recorder-smoke.yml
$ grep -n "runs-on\|pytest -q\|bash setup.sh\|init.py init" .github/workflows/windows-recorder-smoke.yml
38:    runs-on: windows-latest
53:        run: py -m pytest -q                    # 全量 pytest，无 skip 限定
71:          output="$(PYTHONIOENCODING=gbk bash setup.sh 2>&1)"
81:          python3 sdflow-init/scripts/init.py init --root "$probe"
```
触发路径含 `setup.sh` / `hack/**` / `sdflow-init/assets/**` / `sdflow-init/scripts/**` / `sdflow-ship/scripts/**`
—— **本 change 改的每个文件都在其中**。

**③ F44 —— 消费仓顶层没有 `sdflow-init`**

```bash
$ ls ~/Documents/10-michi | grep -c "^sdflow-init$"
0
$ ls ~/Documents/10-michi/openspec/workflow/
lens-metric-contract.md  tools
```

**④ A12 —— 「其余 tools 未验 fail-closed」当场可结**

6 个 tool 全部 `argparse` + `required=True` + `sys.exit(main())`，无一静默默认；运行时真读版本化契约的只有 3 个
（`anchor_lint.py` 22 命中 · `hr_tg_intersect.py` 12 · `lens_metric_emit.py` 6；另 3 个为 0，`outside_voice_guard.py` 的唯一命中是注释）
—— **恰是 proposal 已核的那两个 + emitter**（后者的 `parse_known_args` + `if extras: fail-closed` 由 `lens-metric-emit/spec.md:50-51` 规定）。

---

## 经得起撬的边界（如实记，不是弱点）

| 边界 | 判定 |
|---|---|
| 「SKILL.md 验证只能到 grep 文本级」 | ✅ **成立**。全仓唯一引用两个评审 SKILL 路径的测试是 `test_sdflow_spec_agents.py`，与探测段无关；没有任何 pytest 对第零步做行为级验证。C5 的"结构上无法被机械守"论证站得住 |
| 「运行时自检不可能」（Windows） | ✅ **成立**。检查者与被检查者同为一次 `cp -r` 产物。**但"CI 也测不了"不成立**（F48） |
| `openspec/INDEX.md` 无需同步 | ✅ 托管块只列规则 `.md`，不枚举 `tools/*.py` 或 contract |
| delta 的两条 RENAMED FROM 标题 | ✅ 与主 spec `:252`/`:298` **逐字匹配**，归档时可正确解析 |
| `check_tier_resolution_parity.py` 的 marker 段 | ✅ 与探测段**不重叠**（在其之前），task 1.1/1.2 不会碰到 |
| Migration Plan 对**非 pin 仓**的半态安全性 | ✅ 独立成立（旧 resolver 步②/③ 未变，canonical 软链内容已随 pull 变新） |

---

## 收敛口

**建议：暂不进设计 HARD-GATE。** 先处置 **P0 三簇**：
① 五处假陈述（F1/F3/F26/F42/F48/F49）——其中两处正要进归档 Requirement；
② 补 `BASE-29 协议文档套件 scope-check 表`（F40）——它一补，F6–F9 与 F17–F21 两簇一起消失；
③ 把 tasks 2.x/3.x 的检测方法从「grep 枚举」换成「跑 pytest 让工具自己回答」（F10–F14 的面级修法）。

处置后走一次**窄复核**（只审增量），再拍板。

🔴 **拍板前流程纪律**：本报告审的是 commit `0f8b0a3` + `cc5bc1d` 的盘面。人读报告后若要求修改四件套，
那些改动 MUST **先单独 checkpoint 提交**、取得其 sha，**再**回写 `ship-gate.design_approved` 与 `reviewed_sha`
（否则锚会指向不含该修订的更早提交，拍板后第一次跑 gate 就判设计失鲜 `REFUSE_START` 自锁）。

---

## 度量锚诚实边界

- `findings=N` 与合并池实收数的**数值一致性**是主 session 信任边界，非机械可验。
- 报告共 **51 条** findings，度量锚只覆盖 **48 条**——**F24 / F36 / F40 三条由主 session 亲查得出，不属任何镜的产出**，
  故不计入任何 lens 行（`lens-metric` 无"主 session"行键）。此差额为**有意如实登记**，非漏计。
- `采纳`/`裁掉`/`defer` 为**设计门拍板前的临时裁决**，MUST 在拍板回写时最终确定（SR-M，best-effort 无机械兜底）。
- `fanout-capability` 锚的 `subagents="available"` 由主 session 自报观察，**无可信脚本捕获路径**，非机械门。
