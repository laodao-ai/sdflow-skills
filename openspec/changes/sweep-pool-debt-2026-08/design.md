# Design · sweep-pool-debt-2026-08

## Context

动机见 proposal.md「Why」。本文只写实现路径需要的现状事实（全部已核验，锚见 decision-memo C1–C12）：

- `ship_gate.py`（2183 行，argparse CLI，自述「只读判官」，逸出契约 {0,3,4,5,6}）的失鲜域 `is_stale`（:874-966）已经是内容比较：取 `git ls-tree -r -z <ref> -- proposal.md design.md tasks.md specs/` 的 `path→(mode,type,oid)` 映射做等值；`reviewed_sha`（40 位 commit OID，产出方 SKILL 指令让 LLM 跑 `git rev-parse HEAD` 后手写进报告 frontmatter）只充当取锚侧内容的把手。rebase 重写 commit SHA ⇒ 把手失效 ⇒ UNKNOWN(6)。
- tasks.md 勾选框豁免层：`_normalize_checkbox_lines`（:810-846，37 行）+ `_tasks_content_exempt`（:849-871，23 行）+ `is_stale` 内「差异仅在 tasks.md」支路。**fence 词法单一源（`fence_delim`/`FenceTracker`，:664-735）是四处共用件**（`_normalize_checkbox_lines` / `_line_scoped_hits` / `_parse_plan` / 锚扫描），且仓内明文归类为有界可手写（基准 5 合法件）——**不在删除面内**。T292 todo 所称「~140 行」含此共用件，实际可删面约 60–80 行 + 对应测试。
- 监视集常量 `DESIGN_WATCHED_NAMES = ("proposal.md", "design.md", "tasks.md")`（:548），specs/ 在 ls-tree pathspec 中单列。
- 产出方 SKILL 调 sibling 脚本的既有约定：`~/.claude/skills/<skill>/scripts/<name>.py`（done SKILL §2.1/§2.2 同款）。
- 仓内已无「MUST NOT rebase」条款文本（grep 全仓核实）；该纪律只存在于会话记忆层，消掉它 = 不再需要任何人记得它。
- 〔spec-review-amendment，订正 memo C12〕gate 端 `checkpoint(impl-review)` subject 豁免与 BR-7 真值表**代码已于先前 impl-review-fix change 物理删除**（`ship_gate.py:118-123` 退役注释；`test_gate_freshness.py::test_impl_review_subject_no_longer_buys_any_exemption` 钉死回归；四镜独立复核一致）。现行 `openspec/specs/spec-workflow/spec.md:468-497` 对该通道的描述是滞后于代码的死文字——memo C12 的核验锚只读了 spec 原文，核验源选错。∴ D9 的实际工作量 = spec 死文字清理 + `sdflow-code-review` **新建**（非「补」）impl-review 重锚协议；`is_stale` 现无任何 subject/walk 代码可删。

## Goals / Non-Goals

**Goals（设计层边界，proposal 范围之外不重复）**

- 锚的**计算逻辑单一源**：producer 写锚与 gate 验锚跑同一个函数（物理同文件），杜绝两端口径漂移面。
- `ship_gate.py` 判官 CLI 保持只读语义：写锚动作放独立 sibling 脚本，不给判官加写 verb。

**Non-Goals**

- 见 proposal「Non-Goals」；另加：不动 fence 词法单一源及其另外三个消费方；不重构 is_stale 之外的 gate 域。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)（D1–D9）。以下为 memo 之下的设计层技术选择：

- **DT-1 锚字段名保留 `reviewed_sha`，值改为 64 位 sha256 hex（监视集内容指纹）**。理由：字段名字面（"被评审盘面的 sha"）对内容 digest 依然成立（它就是一个 sha256）；改名会把 spec-workflow 中所有仅词法提及该字段的 Requirement 全部拖进全文 MODIFIED delta，且 22 个消费文件的 grep 收口面翻倍——语义澄清由值格式差（40→64 hex，视觉可辨）+ 新 ADR 承担。格式校验句同步 40→64（含 done SKILL 预检句）。旧值(40-hex)进新 gate 判 ANCHOR_INVALID → UNKNOWN(6) 可恢复，天然 fail-closed。归档区历史报告文件不动，但〔spec-review-amendment，跨模型 voice 发现并已接地证实〕**gate 读归档**——`archived_verify_state`（ship_gate.py:460）经同一严格 frontmatter 解析核读归档 verify 结论，且 `FIELD_VALIDATORS["reviewed_sha"]`（:1026）校验一切已识别字段；归档区现有 34 份 verify-report 携 40-hex 锚 ⇒ 校验一刀切改 64-hex 会令其全部判坏 frontmatter → `none` → SHIPPED 大面积回归。∴ **校验分层**〔spec-review-amendment R1〕：解析层（`FIELD_VALIDATORS`）对 `reviewed_sha` 只做语法校验并放宽为「40 或 64 位小写 hex」、`reviewed_manifest` 注册单行 base64 语法校验器——解析核不 fork、无归档模式参数（承 A4 共核纪律，对存量行为零回归）；64-hex + manifest 互证的语义强制上移 `read_reviewed_sha`（live 读点），40-hex 判 ANCHOR_INVALID → UNKNOWN(6)，诊断指明「旧格式锚，重跑写锚脚本」；`archived_verify_state` 只消费 `verify` 结论，34 份 40-hex 归档报告自然通过解析（无 fail-open：新鲜度恒要求 digest 等值，40-hex 不可能等于重算 digest）。补「归档 40-hex + verify: PASS → SHIPPED」回归测试。备选（改名 `reviewed_anchor`）被砍：spec/消费面迁移代价翻倍，收益仅命名洁癖。
- **DT-2 锚 = manifest + digest 双字段互锁**。frontmatter 记两个由同一脚本写入的字段：`reviewed_manifest`（监视域 `path→(mode,type,oid)` 规范行清单，按 path 排序）+ `reviewed_sha`（= manifest 规范字节流的 sha256，64-hex）。**等值判定只走 digest**（重算 HEAD 侧 manifest → sha256 → 与锚值比对）；**诊断走 manifest**（digest 不等时对 HEAD 侧枚举求差集 → 点名路径，`git log -1 -- <路径>` 点名提交）——纯 digest 会丢掉既有 spec 的 REFUSE_START 诊断要求（必须指明文件与提交），manifest 补齐它，且与 digest 密码学互锁（篡改 manifest 不改 digest 即自相矛盾，fail-closed）。**监视域按报告分**：design 域 = change 目录内 `proposal.md`/`design.md`/`specs/`（tasks.md 移出，D2）；code/verify 域 = 顶层条目映射（非递归、排除 `openspec`，既有口径）——两域锚值均为 manifest digest，gate MUST NOT 将锚值作 git ref 解析（现 code 分支 `ship_gate.py:950` 以锚 sha 取 `ls_tree_map`，MUST 一并重写为 HEAD 侧重算 digest 等值〔spec-review-amendment〕）。**manifest 规范编码 MUST 字节保真**〔spec-review-amendment，双 voice 收敛〕：记录取 `ls-tree -z` 原始 path 字节（git 路径可含 Tab/换行/非 UTF-8，现实现即以原始字节处理并有含 Tab 路径回归测试），按原始 path 字节序排序；frontmatter 存储用单行字节保真编码（base64 该规范字节流），digest 对解码后原始字节计算；MUST NOT 依赖 YAML 文本行清单的转义/归一化（会致同内容不同 digest 或异路径折叠）；互证 = 解码字节流的 sha256 == `reviewed_sha`。比较端不取锚侧字节 ⇒ 无 dangling-blob 依赖。备选（gstack 整工作树 write-tree 指纹）被砍：全树指纹把监视域外改动全判失鲜，与 scoped 语义不符；备选（纯 digest 无 manifest）被砍：丢失既有诊断契约。
- **DT-3 写锚脚本 = `sdflow-ship/scripts/anchor_writeback.py`（新增 sibling），`import ship_gate` 复用同一指纹函数**，计算后直接改写报告 frontmatter（原子替换）。〔spec-review-amendment〕为满足既有「结论字段与锚 MUST 原子写入」Scenario，脚本 MUST 支持同批写入结论字段（如 `--set design_approved=true` / `--set verify=PASS`），producer 一次调用同时落结论+锚（单次原子替换）；MUST NOT 先手写结论再调脚本补锚（中间态 = 结论在、锚缺 → UNKNOWN）。**脏树守卫**〔spec-review-amendment R2〕：监视集路径存在未提交改动（`git status --porcelain -- <监视集>` 非空）时 MUST fail-loud 拒写并提示「先提交修订再写锚」——把 ADR-7(b)「二次修订先单独落盘」从书面纪律收进机械层；逃生口（如 `--allow-dirty`）仅显式越权留痕场景。D4 诚实边界随之收窄：机械堵「值错 / 不一致篡改 / 未提交盘面写锚」，仍不堵「批准动作本身是否已发生」（该子集无确定性信号）。产出方 SKILL 的回写步骤从「跑 `git rev-parse HEAD` 手抄 40-hex」改为「调本脚本」。判官只读语义不破。脚本带 4 行 `reconfigure` 前导（第五道机械门要求）。备选（ship_gate 加 write 子命令）被砍：破「只读判官」自述契约。
- **DT-4 UNKNOWN 分类学微调**：`CAUSE_ANCHOR_MISSING` / `CAUSE_ANCHOR_INVALID` 语义沿用，INVALID 判据改为「非 64-hex 或 manifest 与 digest 不互证」；原「锚指向对象不存在或非 commit」类随内容锚整体退役（诊断六类→五类，死分支物理删除）。窗口语义（design 报告在 code-review 报告出现后不再被读）原样保留。
- **DT-5 T287 下沉判据**：可下沉 = 「执行到该步才需要展开读的判据表/参考细节」（与既有 6 个 references/ 文件同类）；不可下沉 = 流程骨架、铁律、fail-closed 分支。目标 ≤16,000 字符（余量 ≥2,000）。具体小节实现票内定，红线是 `test_sdflow_spec_resident_contract.py` 既有断言全绿（含 frontmatter/结构断言）。
- **DT-6 T294 执行序**（todo 明定，不可颠倒）：先本地全量收敛（桶B/桶A 对照 git log 回填 + 桶C 改写）→ 本地 `validate --archived` 0 failed → 再改 CI（pin 升 1.9.0 + 加步）。CI 步放既有 openspec 泳道（该泳道已装 node + CLI）。
- **DT-7 impl-review 豁免通道改造（D9 落地形态）**：gate 端 subject 豁免（`checkpoint(impl-review)` 精确式匹配 + 逐提交 walk + BR-7 变体真值表）与勾框内容豁免在 **spec 层一并退役**〔spec-review-amendment：subject 豁免的代码已于先前 impl-review-fix 物理删除，本步该部分 = spec 死文字清理，无 gate 代码可删；勾框豁免代码仍在、真删〕，`is_stale` 缩为「重算指纹 → digest 等值」；`sdflow-code-review` **新建** impl-review 重锚协议段（现 SKILL 无既有协议可「增补」）——修订提交后跑 `anchor_writeback.py` 刷新 spec-review-report 锚（不动结论字段）并随提交落盘。忘重锚 ⇒ REFUSE_START（fail-closed，补跑即恢复）。「手跑重锚绕过二次批准」= 显式越权留痕（adr/0008 同权级），继续在 `ship_gate.py` 头注释「已知不覆盖」登记。

### 切片建议

四张垂直切片（预算 3–6 内），票间无阻塞边、可任意顺序：

- **票 1（T292，最大）**：ship_gate 内容锚——指纹函数 + `is_stale` 重写（勾框豁免层删除；subject 豁免 walk 无代码可删，系 spec 死文字清理〔spec-review-amendment〕）+ `anchor_writeback.py` + 测试迁移 + 3 产出方 SKILL 回写改调脚本 + code-review impl-review 重锚协议**新建** + 新 ADR + 全仓 grep 收口 + **收尾重锚本 change 自身 spec-review-report（tasks 1.9，防自举自锁〔spec-review-amendment〕）**。〔spec-workflow delta 全部 Requirement〕
- **票 2（T294）**：归档面收敛（桶B/桶A 对照 git log 回填、桶C 改写作废说明段）→ 本地 `validate --archived` 0 failed → CI pin 1.9.0 + 新增校验步。〔archive-validation 两 Requirement〕
- **票 3（T290）**：code-review SKILL Step1 输入清单接入 planning-decisions 偏离对账。〔impl-orchestration ADDED Requirement〕
- **票 4（T287）**：`sdflow-spec/SKILL.md` 判据下沉 references/，字符数 ≤16,000，既有 resident-contract 测试全绿。〔无 spec delta，DT-5〕

### 锚流对照（TG-04 v_old/v_new）

| 维度 | v_old | v_new |
|---|---|---|
| frontmatter 字段 | `reviewed_sha`（40-hex commit OID） | `reviewed_sha`（64-hex manifest sha256）+ `reviewed_manifest`（诊断清单） |
| 值的产生 | LLM 跑 `git rev-parse HEAD` 手抄 | `anchor_writeback.py` 权威计算 + 原子写入 |
| 锚的语义 | 取锚侧内容的 commit 把手 | 监视集内容指纹本身 |
| 失鲜比较 | ls-tree(锚 commit) vs ls-tree(HEAD) 映射等值 + 逐提交豁免 walk | digest(锚值) vs digest(HEAD 重算) 等值，无豁免 walk |
| tasks.md | 在监视集，差异走勾框豁免层 | 不在监视集（豁免层删除） |
| impl-review 修订 | gate 端 subject 豁免（逐提交 walk） | producer 重锚协议（gate 无豁免通道） |
| rebase/amend 后 | 把手失效 → UNKNOWN(6) | 内容不变 ⇒ CURRENT |
| 锚缺失/坏格式 | UNKNOWN(6)（MISSING/INVALID） | 同左，INVALID 判据改 64-hex |

> 〔spec-review-amendment〕表中「impl-review 修订」行 v_old 描述的是 spec 层契约；gate 代码侧该 subject 豁免已先期删除（见 Context 订正条）。

```
v_old:  报告 frontmatter ──reviewed_sha──▶ git ls-tree <sha> ──map──┐
                                                                    ├─ 等值? ─▶ CURRENT/STALE
        HEAD ────────────────────────────▶ git ls-tree HEAD ──map──┘
        (sha 解析不到 ⇒ UNKNOWN)                └─ tasks.md 差异 ⇒ 勾框豁免层(60-80行)

v_new:  拍板时: anchor_writeback.py ─ fingerprint(HEAD) ─▶ 写入 frontmatter
        ship 时: ship_gate.py ─ fingerprint(HEAD) ─▶ == frontmatter 值? ─▶ CURRENT/STALE
        (同一 fingerprint 函数，物理同源；无锚侧取物，无豁免层)
```

## Risks / Trade-offs（TG-08 失败模式）

| 失败模式 | 后果 | 缓解 |
|---|---|---|
| 批准后实质改 tasks.md（D2 fail-open 面） | 失鲜不触发 | done 0.3 git-log 对账 + code-review Step1 scope 审计（T290 接线后含偏离对账）〔spec-review-amendment 表述收窄：两者核对的是完成度/偏离，非 tasks.md 文本完整性的直接检测〕；残余已由人拍板接受 |
| anchor_writeback 调用时机错（时机仍自报） | 锚到错误盘面 | 诚实边界（D4）；报告与 diff 不符会在评审下游对不上 |
| impl-review 修订后忘跑重锚 | REFUSE_START 误停 | fail-closed 方向安全；诊断点名路径与提交，补跑重锚即恢复 |
| 迁移窗口内旧格式报告在途 | gate 判 UNKNOWN(6) | 〔spec-review-amendment 订正：**本 change 自身即存量**——设计门拍板时以旧版 gate 落 40-hex 锚，票 1 落地后其余票即读旧锚判 UNKNOWN 自锁 ⇒ 票 1 收尾 MUST 重锚本报告（tasks 1.9）〕其余在途 change 无旧报告存量；UNKNOWN 本身可恢复（重跑回写） |
| 迁移漏消费者（22 文件跨 .py/.md/.yml 的格式校验句/语义句残留） | 残留旧口径断言假红/假绿 | 迁移票收口步：`grep -rn reviewed_sha`（不加 --include）全仓清零（归档区除外）；全量 pytest |
| 桶A 回填勾错（把没做的勾上） | 归档记录伪造 | 逐条对照 git log/实现 commit（done 0.3 语义）；确未做的留 `[ ]` + 说明（validate 只在有未勾复选框时红，说明行不影响——桶A 两 change 已 ship，预期全勾） |
| CI pin 1.5.0→1.9.0 改变既有 validate 步行为 | 存量门意外红 | 本地 1.9.0 已全量跑过既有面（预验证，C11） |

## Migration Plan

1. 票 1（T292）：ship_gate 指纹函数 + is_stale 重写（豁免层与 subject 豁免 walk 一并删除）+ anchor_writeback.py + 测试迁移 → 3 个产出方 SKILL 回写步骤改调脚本 + code-review impl-review 协议补重锚步 → 新 ADR（修订 adr/0026）→ 全仓 grep 收口。
2. 票 2（T294）：归档回填/改写 → 本地 0 failed → CI pin + 新步。
3. 票 3（T290）：code-review SKILL Step1 输入清单 + spec delta。
4. 票 4（T287）：SKILL.md 下沉 + 字符数复核。
   票间无依赖（可并行），票 1 最大。**回滚**：单 change revert 即复原（锚格式改动集中、无数据迁移）；CI 步独立可单撤。

## Open Questions

无——全部岔路已拍板（decision-memo D1–D9，含相位 C 期追加拍板的 D9）。

## Compliance

- 遵守 openspec/rules/doc-authoring.md（DOC-1：正文即最终态，本文无演进史层）。
- 遵守 premise-verification：Context 全部事实带核验锚（decision-memo C1–C12 + 本文行号均本日实查）。
- 基准 5：不新增任何 Markdown/语法解析——指纹是零解析字节级 digest；fence 有界词法共用件保留原状。
- 无领域清单命中（非 backend/embedded/frontend）；设计画图规则：已含组件/流程对照图（上节 ASCII）。
