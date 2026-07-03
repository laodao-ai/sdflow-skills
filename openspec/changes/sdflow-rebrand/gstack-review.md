# GSTACK REVIEW REPORT — sdflow-rebrand（/autoplan 广审）

> 评审对象：`openspec/changes/sdflow-rebrand/`（proposal / design / tasks / specs/spec-workflow/spec.md）
> 执行：autoplan 自动决策模式（spawned session，无人交互；所有门以自动决策 + 理由留档替代，偏离清单见文末）
> 日期：2026-07-03 · 分支：main · 声部：主审（接地读码）+ Claude 独立冷镜 ×3（CEO/Eng/DX，fresh context）+ Codex 对抗声部（codex-cli 0.142.5, read-only）
> 接地面：setup.sh · issues.py · init.py · assets/snippets · assets/workflow · README · 现役 `~/.claude/skills` 链实况 · **glob 行为沙箱实证**

---

## 结论一览

**总评：方向与时机成立、RENAME-MAP + 反向断言的机械化取向正确——但两处 CRITICAL（孤儿清理死代码、托管区块 marker 失配）+ 三处 HIGH（断言子串碰撞、断言顺序倒挂、setup.sh 承重路径被误标为文案）会让 change 按现文执行时在自己的验收步上翻车或在消费仓造成静默残留。全部可低成本修正，建议修 tasks/design 后再进实现。**

| 镜 | 评分 | 一句话 |
|---|---|---|
| CEO（战略/范围） | 7/10 | premise 大体成立（已核验归档与 ROADMAP）；「最佳窗口」表述应去伪量化；保留名单与 no-stub 决策需补记录 |
| Design（命名/信息设计，缩减执行） | 7/10 | 命名系统一致；`sdflow-code-review` 与宿主内建 `/code-review` 的邻域需显式消歧 |
| Eng（机械正确性） | 4/10 | **2 CRITICAL + 3 HIGH**，全部有 file:line 证据与实证；均为确定性断裂而非风格分歧 |
| DX（迁移体验） | 7/10 | 失效多数是响的；触发等价验证薄（3 条抽查 vs 硬 MUST）；激活步 checkout 归属未写死 |

---

## 合并后 Findings（按严重度；置信 = 接地/实证程度；标注声部共识）

### CRITICAL

- **F0 `cleanup_orphans` 对 Unix dangling 链是死代码——改名的核心成功指标建立在从未生效的机制上。**〔Codex 首发；主审沙箱实证确认；置信 98〕
  `setup.sh:69` 用 `for entry in "$dest"/*/` 枚举——bash 中 `*/` 只匹配可解析为目录的条目，dangling 链不被枚举；即便改成 `*`，`setup.sh:70` 的 `[ -e "$entry" ] || continue` 也会把 dangling 链跳过。实证：沙箱中 `dest/*/` 只列出 goodlink、danglink 完全不可见。故 `:92-93` 的 dangling 清理分支（Unix）从未可达；现状只有 Windows marker copy 分支（:94-95）真正生效。design §三「旧名链 = 自属 dangling → cleanup_orphans 收走」与 Success Metric「旧名链被孤儿清理收走」按现有代码**不成立**；4.1 的新测试会当场红，但修 setup.sh 枚举逻辑是行为变更，未列入任何 task。
  **修**：task 3.x 增补——`install_into`/`cleanup_orphans` 枚举改 `"$dest"/*` + `[ -e ] || [ -L ] || continue`；4.1 测试保持（正好锚定该修复）；此改动与「行为零变化」承诺的关系在 proposal 里说明（是修 bug 不是改行为语义）。

- **F1 托管区块 marker 失配 → 消费仓 update 追加重复区块、旧区块永久失管。**〔主审 + Eng 冷镜 + Codex 三方独立发现；置信 95〕
  `init.py:33-35` 的 MARK_DOC/MARK_IDX 全串含「由 opsx-project-init 维护」；`inject()`（init.py:66-75）按**全串精确匹配**定位旧区块，找不到即走「追加」分支。init.py 不在白名单 → 断言逼改 marker 字面 → 存量消费仓与本仓（AGENTS.md:5、openspec/INDEX.md:5、CLAUDE.md）的旧 marker 永远匹配不上 → `sdflow-init update` 在每个消费仓**追加第二块**，旧块（满是旧 slash 名）静默残留且永不再被任何 marker 匹配。tasks/design 完全未提 marker。
  **修**：inject() 增加旧 marker 对识别迁移（命中旧 start/end 则以新 marker 替换整块，~5 行）；或 marker 字面冻结（改为机制中性措辞并入白名单）。二选一须进 tasks + 补「预置旧 marker 文档 → update → 断言单区块新 marker」测试。

### HIGH

- **F2 反向 grep 断言（4.3/D1）按原文不可实现。**〔主审 + Eng 冷镜 + Codex 三方；置信 95〕
  三重破绽：①子串碰撞——`spec-review` 是 `sdflow-spec-review` 的字面子串（连字符非 word 边界，`\b` 救不了）；Eng 冷镜实测当前全仓 `spec-review` 264 处命中、改名后每处新名引用都会假阳。②同名规则文档——`workflow/spec-review.md` 是规则文件（非 skill），改名后合法存在且被 snippets/INDEX 引用，白名单未覆盖。③断言命令本身未定义（tasks.md:29 只说「全仓 grep」），最要紧的 pattern 决策被推迟到执行期。
  **修**：D1 增补「逐名定制 pattern」条款（如 `grep -P '(?<!sdflow-)spec-review'` 或管道排除新名），并决策规则文档 `spec-review.md` 改名与否；断言脚本在 design 期写死、随 change 留档。

- **F3 断言（4.3）先于重注入（5.4）执行必然 FAIL。**〔主审 + Eng 冷镜 + Codex 三方；置信 95〕
  本仓 `openspec/workflow/` instance（Eng 冷镜验证与 assets 逐字节一致、约定禁手改）7 个文件含旧名，CLAUDE/AGENTS/INDEX 托管区块同理——它们只能由 5.4 `update --dev` 刷新，但 4.3 排在前且未白名单化 → 纯时序性假 FAIL，或诱导手改托管区块（违约定）。design §七 ⑤⑦ 同序。
  **修**：5.4 提到 4.3 前；或断言跑两轮（中期宽 / 5.4 后终验严）。推荐两轮法——防 update 本身失灵漏检。

- **F4 setup.sh:109/:133 是承重路径字面，被 tasks 1.2 归为「提示文案」。**〔主审 + Eng 冷镜 + Codex 三方；置信 95〕
  `install_sdflow()` 的 `bundle="$REPO_DIR/opsx-project-init/assets/workflow"`（→ `ln -snf` 建 `~/.sdflow/workflow` 全局 canonical）与 `"$REPO_DIR/opsx-project-init/assets/hack/"*.sh`（→ `~/.sdflow/hack` 拷贝）。`ln -snf` 不校验源存在——漏改即全网消费仓 resolver 步② dangling（响的降级，但可避免）。`test_setup_sdflow.py:25` 断言该路径，会逼修，但组件清单应显式承重定位。另：proposal「`~/.sdflow` canonical 不受影响（路径无 skill 名）」表述不准——canonical **软链目标**含旧名，pull 后未重跑 setup 存在 dangling 窗口。
  **修**：design §六 setup.sh 行补两处 file:line；增 post-mv 冒烟（`bash setup.sh && readlink -f ~/.sdflow/workflow` 可解析）；hand-off 写明 pull 与 setup 同轮（/sdflow-upgrade 语义）。

- **F5 白名单缺口：真实仓状态里还有三类旧名载体不在白名单。**〔Eng 冷镜 + Codex；置信 90〕
  ①`docs/superpowers/plans/...`（历史实现计划，60+ 命中）与 `opsx-project-init/memo-review-html-tool.md`——同属「历史记录」精神但路径不在白名单（`.superpowers/` ≠ `docs/superpowers/`）；②`openspec/issues/` 池内条目文本（如 2026-07-todolist.md）含旧模块名——既非 archive 也非 ADR；③`openspec/config.yaml` 两处描述。改历史 issue 文本不可取 → 必须白名单决策先行。
  **修**：白名单显式扩：`docs/`、`opsx-project-init/memo-*.md`、`openspec/issues/`（池内历史文本），config.yaml 归功能面改之。

### MEDIUM

- **F6 引用面被 tasks 1.2/1.3 系统性低估。**〔四声部合流；置信 95〕1.2 之外的实际功能命中：`ff-generation-constraints.md`、`workflow/spec-review.md` 正文、`reference/*.md`、`tools/engine.js:262`、`tools/vendor/NOTICE.md:16`、`AGENTS.md`（与 CLAUDE.md 平行却未点名）、`assets/hooks/change-review-stub.py` 注释、**`opsx-roadmap-planner/scripts/gen_review_stub.py:24` 的用户可见运行时报错文案**（漏改 = 报错教用户跑一个不存在的命令）、`sdflow-upgrade/SKILL.md:3,18`；1.3 只点名 3 个测试文件，实际 7 个含旧名（test_init.py / test_setup_sdflow.py / test_checkpoint_commit.py / test_change_review_stub_hook.py 漏列，而它们恰覆盖 F1 的 inject 逻辑）。**修**：1.2 改述「断言驱动、清单仅为至少含」；1.3 补 4 文件。
- **F7 激活步 checkout 归属未写死 + 时序矛盾。**〔主审；置信 85〕`cleanup_orphans` 按 REPO_NAME（脚本所在目录名）匹配链目标；现役旧链目标为 `~/.skills/sdflow-skills/<旧名>`。5.3 若在 dev checkout（`04-sdflow-skills`）跑 setup：旧链不被识别（仓名不匹配）→ 不清，且新链错指 dev checkout（违 adr/0005）。而运行 checkout 拿到改名须先 merge——与 5.3 位于 opsx-done 之前矛盾。**修**：5.3 拆两半——本仓验证用假 HOME 测试承担；真机激活改为 merge 后在运行 checkout 跑 `/sdflow-upgrade`，挪进 hand-off。
- **F8 D3「永久兼容 `.laodao-skills`」在 Windows 双仓共存下会反向误伤。**〔主审；CEO 冷镜从品牌侧独立触及（laodao 旧仓并存）；置信 80〕marker 只判存在不判归属（setup.sh:84）；laodao 旧仓（留守 misc）同用 `.laodao-skills` → 本仓 `cleanup_orphans` 会把 laodao misc skill 的 Windows 拷贝判自属、因源不在本仓而 `rm -rf`（:94-98）。存量互踩隐患被 D3 永久化。**修**：兼容集收窄为「entry 名 ∈ RENAME-MAP 旧名 ∪ 本仓现名」；spec R-SR-2 补反例 Scenario（laodao misc 拷贝不接管不删）。
- **F9 触发等价验证强度与硬 MUST 不匹配，且与本仓 adr/0006 方法论自相矛盾。**〔CEO + Eng + DX 三冷镜合流；置信 85〕spec 写硬 MUST「原触发场景语句集全保留」，验证却只有人工 3 条抽查；adr/0006 自己主张 prose 判断不可靠、机械活交脚本。**修**：加机械校验——从新旧 description 提取引号内触发短语集断言 旧 ⊆ 新∪trigger-map 映射行，破缺即 FAIL；抽查语句直接取自 trigger-map「验证语句」列。
- **F10 回滚承诺过强。**〔Eng + Codex + CEO 合流；置信 85〕「纯可逆」仅在「无消费仓已 update + 单提交」窗口内成立；已 update 的消费仓不随源仓 revert 还原；§七 ①-⑦ 多提交时 revert 非单步。**修**：§七 补适用边界与多提交 revert 程序一句。
- **F11 消费仓迁移无验收任务。**〔CEO 冷镜；置信 80〕已知至少 04-iot-tools 一个真实消费仓，tasks 只有 5.5 文字提醒；change 可判「完成」而外部破坏未验证。**修**：hand-off 升格为带时限 todolist 项，或收尾前在一个真实消费仓跑 `sdflow-init update` 验证托管区块（顺带成为 F1 修复的真机验证）。
- **F12 安装态集成测试缺口。**〔Codex；置信 75〕issues.py 按目录名子进程调兄弟脚本——4.2 的仓内 pytest 若只测源码布局，证不了安装布局（`~/.claude/skills/sdflow-*`）下 reindex 仍通。**修**：4.1 增一条安装布局仿真（假 HOME 建链后跑 reindex）。
- **F13 Windows copy 分支无测试锚。**〔DX 冷镜；置信 75〕4.1 用语全是「链」（Unix）；marker 兼容/刷新的 copy 分支代码路径不同（rm -rf + cp -r）。**修**：测试内伪造 `IS_WINDOWS=1`（或抽函数测）；做不到则显式记「人工验证/已知未测」。

### LOW（收进 adr/0007 或一句话修复）

- **F14** `spec.md:67` 在强制 `sdflow-` 前缀的条款内用旧式名 `opsx-ship` 前向引用（与 design 的 `opsx-ship-orchestrator` 也不一致）——改 `sdflow-ship` 或改泛称。〔DX〕
- **F15** `impl-review → sdflow-code-review` 是 9 项中唯一夹带词根替换（impl→code）的非纯机械映射——adr/0007 单列一句理由。〔CEO〕
- **F16** 保留名单张力：`openspec-upgrade` 与 CLI 生成的 `openspec-*` 官方家族同前缀，恰属本 change 要消灭的混淆类——adr/0007 正面写清豁免理由（它升级的就是 openspec CLI，域名即语义），或纳入改名。〔CEO；登记为决策项 DR-5〕
- **F17** laodao 旧仓 `update` skill（"ld-update"）与 `sdflow-upgrade` 双品牌并存——proposal 措辞降级为「仓内品牌收拢」+ hand-off 记收敛评估。〔CEO〕
- **F18** 「最佳窗口」论证不可证伪（无消费仓数量/成本曲线）——proposal 改为可证伪表述或如实承认「顺手做、无强制窗口」。〔CEO；不阻断——机制前提（全局解析已落地）与消费仓最少点本身是真〕
- **F19** 旧会话内旧 slash 名的失效形态未实证（可能被当普通文本对话式回答 = 静默错误而非响的 skill-not-found）——5.3 实测一次并记录真实行为。〔DX〕
- **F20** `sdflow-init`/`sdflow-upgrade` 首遇可猜性——两 description 互加一行交叉引用。〔DX〕
- **F21** README 增「0.9.0 改名对照表」（rename-map 用户面呈现；trigger-map 是评审面、README 才是 morning-after 查询点）。〔DX + 主审〕

---

## 声部共识表

| 维度 | 主审(接地) | Claude 冷镜 | Codex | 共识 |
|---|---|---|---|---|
| premise/时机 | ✅（附条件） | CEO：表述不可证伪但机制前提真 | 未质疑机制前提 | **CONFIRMED**（改表述，不改方向） |
| 孤儿清理机制 | 沙箱实证死代码 | DX 冷镜误判「as designed 正确」 | **首发 CRITICAL** | **CONFIRMED**（实证裁决压过冷镜误判——F0） |
| 断言可实现性 | ❌ | Eng：264 命中实测 | ❌ | **CONFIRMED**（F2，三方独立同结论） |
| marker/注入确定性 | ❌ | Eng ❌ | ❌ | **CONFIRMED**（F1，三方独立同结论） |
| 断言/注入顺序 | ❌ | Eng ❌（diff -rq 实证 instance 同源） | ❌ | **CONFIRMED**（F3） |
| 引用面完备 | ⚠ | Eng/DX ⚠（+运行时报错文案） | ⚠（+issues 池/白名单缺口） | **CONFIRMED**（F5/F6） |
| 触发等价验证 | 未深挖 | 三冷镜齐飞 ⚠ | — | **CONFIRMED**（F9） |
| 回滚 | ⚠ 基本成立 | Eng/CEO：过强 | ⚠ 未证 | **CONFIRMED 收窄**（F10） |
| no-stub 决策 | 接受（用户方向） | CEO：要补记录；DX：接受 | 建议 stub 或迁移检查 | **DISAGREE → 决策登记 DR-6**（用户方向为默认） |

**对抗裁决记录**：DX 冷镜称孤儿清理「verified correct as designed」——被主审沙箱实证直接否证（`*/` glob 不枚举 dangling 链）。裁决依据是可复现实验而非声部多数：F0 成立。此例正是「冷镜也会顺着注释读代码」的样本，留档。

---

## 面向设计 HARD-GATE 的决策登记区（人工过报告时拍板）

| # | 决策 | 选项与推荐 | 两方后果 |
|---|---|---|---|
| DR-1 | F0 修法 | **A) 枚举改 `*` + `-e/-L` guard 修正（推荐）** B) 另写独立清理循环 | A 最小 diff；B 无必要 |
| DR-2 | F1 marker | **A) inject() 旧 marker 迁移逻辑（推荐）** B) marker 字面冻结+白名单 | A 彻底、需补测试；B 零风险但永留 opsx 字样锚点 |
| DR-3 | F2 断言 pattern | **A) 逐名定制 pattern + 规则文档改中性名（推荐）** B) 规则文档引用整体白名单 | A 保断言强度；B 留盲区 |
| DR-4 | F3 顺序 | **A) 断言两轮（中期宽/5.4 后严，推荐）** B) 仅调序 5.4 前置 | A 兼检 update 失灵；B 简单但 update 坏了漏检 |
| DR-5 | `openspec-upgrade` 豁免 | **A) 保留 + adr/0007 写明豁免理由（推荐）** B) 纳入改名 | A 尊重「升级外部 CLI」域语义；B 更彻底但把 sdflow 前缀贴到非 sdflow 本体上 |
| DR-6 | no-stub | **A) 维持 no-stub（推荐——用户显式方向，失效响）** B) 一版期 stub | Codex 主张 B；单用户 + F21 对照表 + 响失效下 A 成本可接受；需 adr/0007 补决策记录（CEO F4） |
| DR-7 | F8 兼容集 | **A) 收窄为名单判断（推荐）** B) 维持 D3 原文、记 buglist 延后 | A 一行成本堵静默删除；B 留 Windows 双仓互踩残险 |

---

## Decision Audit Trail（自动决策记录）

| # | Phase | 决策 | 分类 | 原则 | 理由 |
|---|---|---|---|---|---|
| AD-1 | CEO | premises 接受（P3「行为零变化」附条件于 F0/F1 修正） | 门（本应人审） | P6 | P1 机制前提已实证；spawned 无人可问，留档替代 |
| AD-2 | CEO | 接受方案 A（全量前缀）；备选表核验完整 | Mechanical | P1/P5 | 已拍板 + plugin/半量否决理由成立 |
| AD-3 | CEO | 模式 = HOLD SCOPE（非 autoplan 默认 SELECTIVE EXPANSION） | Taste | P3/P5 | change Non-Goals 禁扩张；扩张候选转 defer |
| AD-4 | Design | Phase 2 缩减为命名一致性 pass | Mechanical | 规则 | 无 UI scope；父任务要求四镜→缩减执行留档 |
| AD-5 | Eng | F0 定 CRITICAL | Mechanical | 实证 | 沙箱复现 + 成功指标直接依赖 |
| AD-6 | Eng | F8 不扩为本 change 强改，登记 DR-7 | Taste | P2/P3 | 存量隐患非本次引入；血 radius 内一行缓解可顺带 |
| AD-7 | DX | VERSION=0.9.0 / 永久 marker 兼容方向 / 无 stub 三项 OQ 裁定接受（附 DR-6/DR-7 细化） | Mechanical | P6 | 低风险 + 用户已裁 |
| AD-8 | 裁决 | DX 冷镜「孤儿清理正确」判定被否证采 Codex | Mechanical | 实证优先 | 可复现实验 > 声部多数 |

---

## 失败模式登记（Failure Modes Registry）

| 失败模式 | 触发 | 可见性 | 缓解 |
|---|---|---|---|
| 旧链永不被清（F0） | 每次 setup | **静默**（链 dangling 无人报） | 修枚举 + 4.1 测试锚定 |
| 消费仓区块重复（F1） | 消费仓 update | **静默** | marker 迁移 + 测试 |
| 断言永久假阳（F2）/时序假 FAIL（F3） | 4.3 | 响 | pattern 定制 + 两轮 |
| canonical 软链 dangling（F4） | pull 未 setup | 响（resolver 显式降级） | 同轮执行 + 冒烟 |
| 运行时报错教用户跑死命令（F6·gen_review_stub.py:24） | 消费仓缺 workflow | 响但误导 | 入 sweep |
| laodao misc 拷贝被误删（F8，Windows） | 双仓共存 setup | **静默删除** | 兼容集收窄 |
| 触发短语静默丢失（F9） | description 重写 | **静默**（某语句不再触发） | 机械 ⊆ 断言 |
| 旧会话旧名被对话式吞掉（F19) | setup 后旧 session | 可能静默 | 实测 + hand-off |

## NOT in scope（核验 Non-Goals 后确认合理）

官方 `opsx:*` / laodao 旧仓处置（F17 仅要求措辞与 hand-off）/ stub（DR-6 默认维持）/ 历史文档回改 / 行为重构。无静默缺项。

## What already exists（杠杆确认）

cleanup_orphans 骨架（修 F0 后可承重）· install_into 自动拾取 · inject() 注入（补 F1 迁移后可承重）· 全量 pytest · trigger-catalog/snippets 单源结构 · /sdflow-upgrade 的 pull+setup 同轮语义（F4 缓解的现成载体）。

---

## 执行偏离记录（相对 autoplan SKILL.md 原文）

1. 无人交互：premise 门与 Final Approval Gate 以自动决策 + 本报告替代（父任务禁 AskUserQuestion）；终裁移交设计 HARD-GATE 过本报告（决策登记区 DR-1~7）。
2. 产物落点：写本 `gstack-review.md` 而非 plan 文件；restore point / telemetry / review-log / ~/.gstack 工件 / TODOS.md 写入跳过（spawned 规则 + 本仓不用 gstack 状态目录）。
3. Codex 声部合并为 1 次对抗 run（原文 4 phase × 10min）；Claude 冷镜 3 路并行（原文逐 phase 串行——冷镜间无上下文喂入，独立性不受并行影响）。
4. Phase 2 无 UI scope 本应跳过，按父任务以「命名系统」缩减形态执行。
5. plan-ceo/eng-review 的 sections/review-sections.md 按方法论要点执行（premise 表、备选表、依赖图、测试图、失败模式、NOT in scope、审计轨均产出）；未产 gstack 专属 jsonl 任务清单。
6. DX 镜按 plan-devex-review 的 8 维缩至本 change 相关 5 维（TTHW/错误路径/命名 ergonomics/升级路径/文档），其余 3 维（API 设计/交互文档/escape hatches）对纯改名 change 无对应物，已核对无遗漏面。
