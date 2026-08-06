---
ship-gate:
  verify: PASS
  reviewed_sha: 4539d9f4d482d76a55a3d1e590b6a691c9d54c2e
---

# verify 报告 — absorb-gstack-review

- **日期**：2026-08-06
- **change**：`absorb-gstack-review`
- **DIFF_BASE**：`9a7e09dfc58bfd0d51afacbe442e2c34d483b017`（merge-base with main）
- **核验盘面**：`4539d9f4d482d76a55a3d1e590b6a691c9d54c2e`
- **实现管线**：`tickets`（权威源双证：仓 `openspec/config.yaml:64` `impl-pipeline: tickets` + `tickets.md` frontmatter `impl-pipeline: tickets`）

## 结论

**PASS** —— 23 条 tasks 全部有可机验证据锚点；3 个 capability 的 delta 需求全部在代码/资产/测试中落地；
全仓 pytest 2466 passed / 10 skipped（已知环境隔离项），`openspec validate --strict` 绿，`anchor_lint` 对本
change 的 code-review 报告判 CLEAN。**无核心缺口**；一条 Minor 缺口（仓根孤儿副本残留）为设计内显式 defer（T269）。

> 本次核验**未信任**任何复选框状态与既有报告措辞：tasks.md 的 23/23 勾选被视作零信息量，逐条另找 diff/测试/实跑锚。

## 逐需求核对表

### 1. Step1 自持化（P0 · SKILL.md）

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 1.1 Step1 重写为 fresh 子代理 scope 审计协议（四件套意图源 + diff；prompt 原文带四条通则 + 禁 AskUserQuestion） | `sdflow-code-review/SKILL.md:236-249`（「第一步：自持 scope 审计」；:247-249 输入=proposal/tasks/design+diff、「prompt MUST 原文携带 `sdflow:principles` 整段」「不要 AskUserQuestion，返回结构化 findings」）；gstack 原生/simulated 分支已删（全文件 `grep -n gstack` 退出码 1） | ✅ |
| 1.1（amendment）探针挪至第零步、每轮恰一次、Step1/Step2 共用 | `SKILL.md:208`（「能力探针（本轮恰好一次，与档位解析同位，Step1 与 Step2 共用同一次结果）」）、:218-220（「MUST NOT 为 Step1 另探落第二条锚」）、:298（Step2「已于第零步完成……不另探」） | ✅ |
| 1.1（amendment）dispatch 并行边界（EXEMPT 候选阻塞等 Step1；非白名单形状才并行） | `SKILL.md:243-246`（Step1「并行边界」）+ `SKILL.md:287-289`（Step2 前置「免除判定 MUST 阻塞等待 Step1 结果收齐」/ NOT_EXEMPT 时 MAY 并行） | ✅ |
| 1.2 审计两轴（scope-drift + 完成度五态，判定纪律逐条）+ 逐 task 五态表 + 不勾 tasks.md/不替代 verify + Step4 复审纳入 scope-drift | `SKILL.md:250-256`（两轴 + PARTIAL/NOT DONE 定义）、:257-265（条件轴三：EXEMPT 时逐行读 hunk 查隐藏逻辑）、:266-272（五态表 + 结构化 findings + 「MUST NOT 勾改 tasks.md 复选框、MUST NOT 替代 sdflow-done verify 终审」+ Step4 复审纳 scope-drift） | ✅ |
| 1.3 锚 mode 枚举改 `subagent\|main-session`；降级分支 + 「⚠️ scope 审计降级」标注；恒跑守卫保留 | `SKILL.md:277-279`（锚行 + 新枚举 + 旧值退役 + 「anchor_lint 零改动」）、:273-274（降级标注原文）、:275-276（恒跑守卫 + EXEMPT 作废） | ✅ |
| 1.4 报告格式区：命中范围删 gstack、mirrors 扩 broad、`hits[].raw`=`scope-audit`（roster 保 canonical `broad`）、TG-27→llm.md、分工表改写 | `SKILL.md:606`（「Step1 自持 scope 审计: scope-drift/完成度 结论」）、:608 与 :227（`mirrors="domain,adversarial,history,broad\|—"`）、:618-623（broad 行 raw=`scope-audit`、roster 恒 canonical）、:294（「TG-27 → domains/llm.md」）、:647-656（分工表改为「与官方 code-review 的分工」，无 gstack 提法） | ✅ |

### 2. 机械消费点同步（P0）

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 2.1 contract 折叠块 `gstack-adv: broad` → `scope-audit: broad` + prose 同步 | `sdflow-init/assets/workflow/lens-metric-contract.md:66`（机读块 `scope-audit: broad`）、:44 + :47-48（折叠表 prose + 变更注记） | ✅ |
| 2.2 anchor_lint mirrors 合法集扩 broad；计数集不含 broad（**两常量拆开**） | `tools/anchor_lint.py:674-677`（`_FANOUT_MIRRORS` 计数域不含 broad + `_MIRRORS_LEGAL = _FANOUT_MIRRORS \| {"broad"}`）、:700-701（`_parse_mirrors` 改判 `_MIRRORS_LEGAL`）、:774（`check_fanout_consistency` 仍交 `_FANOUT_MIRRORS`） | ✅ |
| 2.3 golden 四用例（broad 合法 / unavailable+broad,history 不触发 / +domain 仍触发 / `mode="subagent"` 通过） | `tools/tests/test_anchor_lint.py`：`test_parse_mirrors_broad_token_valid`、`test_fanout_unavailable_broad_history_not_dead_fanout`、`test_fanout_unavailable_broad_domain_history_still_dead_fanout`、`test_step1_broad_review_mode_subagent_lint_passes`（另加 `test_mirrors_legal_and_fanout_constants_split` 锁常量拆分） | ✅ |
| 2.4 step8 提示词删 gstack + needle 断言同步 | `assets/workflow/prompts/step8-code-review.md:1`（「Step1 自持 scope 审计的 scope-drift+完成度审计」）+ `hack/tests/test_workflow_split.py:49`（fingerprint 同步为同一措辞，与 5.1 workflow.md 改述一致） | ✅ |
| 2.5 skew 探测两新信号 + 两处报错文案追加 update 指引（含测试） | `SKILL.md:206` 信号③（contract `lens-metric-fold` 块含 `scope-audit:`）+ 信号④（anchor_lint 支持 `broad`，等价信号 `_MIRRORS_LEGAL` 含 broad），任一探不到硬停；`anchor_lint.py:680` `_MIRRORS_UPGRADE_HINT` + :770-771 挂在 `unknown-token` 分支；`lens_metric_emit.py:101-105` 未知 raw 报错追加指引；测试 `test_fanout_mirrors_unknown_token_hint_mentions_sdflow_init_update`、`test_fold_hit_unknown_raw_error_mentions_update_hint` | ✅ |

### 3. checklist 吸收（P1）

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 3.1 CR-10（命令/代码注入）+ CR-11（枚举完备性，必须读 diff 外代码） | `code-checklists/code-review-base.md:19-20`（新号不复用，接 CR-09） | ✅ |
| 3.2 CR-BE-03（DB 层竞态四点）+ CR-BE-02 追加 XSS | `code-checklists/domains/backend.md:11`（CR-BE-02 追加服务端模板 XSS + 显式声明不覆盖客户端框架）、:12（CR-BE-03） | ✅ |
| 3.3 新建 `domains/llm.md`（CR-LLM-01/02）+ README 注册表加行 | `code-checklists/domains/llm.md`（新文件，14 行，两条规则齐全）+ `code-checklists/README.md:66`（注册表行）+ :45（ID 约定 `CR-LLM-NN`） | ✅ |
| 3.4 trigger-catalog TG-27 行（含排除句 + code-review-only 注）+ HR-TG 成员追加 | `trigger-catalog.md:47`（TG-27 行，排除句「评审工作流自身读取/校验同会话内受信任 agent 自报的控制面锚不算」+「code-review-only domain」）、:131（HR-TG 成员行含 TG-27）；动态 parse 实证：`tools/tests/test_hr_tg_intersect.py::test_reads_real_catalog_members` 断言真实 catalog 解出 9 成员（绿） | ✅ |
| 3.5 README「选用规则」示例块补 `TG-27 → llm.md` | `code-checklists/README.md:34` | ✅ |

### 4. pre-emit 引文纪律 + Suppressions（P1）

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 4.1 Step2 子代理 prompt 追加引文纪律（单行引文 / 非局部走可复核证据包 / 引不出 ≤50） | `SKILL.md:317-326`（含两维诚实边界：引文真实性无核验 + 「这条是否真属非局部类」的分类判断同样自报） | ✅ |
| 4.2 Step3 置信过滤追加无引文封顶 ≤50 → 滤出 + 已裁掉区留痕；Suppressions 扩两条；声明非机械门 | `SKILL.md:337`（Suppressions 扩「阈值/常量取值不强制求注释」「无害冗余不标」）、:338-340（引文纪律裁决 + 「已裁掉」区留痕 + 不作用于 Step1）、:344（反静默压制既有条款）、报告格式 :613 已裁掉区措辞同步 | ✅ |

### 5. docs 同步（P2）

| 需求/任务 | 代码出处 | 状态 |
|---|---|---|
| 5.1 `workflow.md` 三处改述 | `assets/workflow/workflow.md:76`（§B 编排器描述）、:91（§三.6 代码侧质量层）、:123（checklist 勾选项） | ✅ |
| 5.2 `reference/quality-layering.md` 相关行同步 | `quality-layering.md:33`、:36（重复度表两行）、:105-106（shift-left 段）、:131（checklist 行） | ✅ |
| 5.3 docs/ 全面提法更新（含 .html 显式点名）+ 全量 grep 复核 | `docs/workflow-skills/sdflow-code-review.md`（一句话 / mermaid S1 / 步骤表 / 被调表 / 强制性表 / 小结六处）、`docs/workflow-skills/gstack-review.md:3-5`（改述为「非运行时依赖的第三方 skill 参考」，文件按设计门 Q4 保留）、`docs/external-dependencies.md:73-84 & :133`、`docs/workflow-overview.md:12-13 & :167 & :225`、`docs/workflow-console.html:398 区块删除 + :431`、`docs/workflow-map.md:140`（`step1-broad-review.mode` 值域改新枚举）、`docs/sdflow-fable5/02-module-reference.md:129 & :286`、`docs/workflow-skills/gstack-document-generate.md:6-8`；本仓 CLAUDE.md 无 gstack 提法（grep 无命中） | ✅ |

### 6. 验证与收尾

| 需求/任务 | 证据锚点 | 状态 |
|---|---|---|
| 6.1 全仓 pytest 绿 | 本次亲跑 `/usr/bin/python3 -m pytest -q`：**2466 passed, 10 skipped in 295.79s**（10 skip 为真机模型探针 / Windows 本地磁盘 / 磁盘写满等已知环境隔离项，非本 change 引入） | ✅ |
| 6.2 Success Metrics（SKILL gstack 严格归零 + validate --strict 绿 + 缺席 Scenario 静态证成） | 本次亲跑 `grep -rn "gstack" sdflow-code-review/SKILL.md` → 无输出、exit 1（严格归零，无「历史注记」豁免）；`openspec validate absorb-gstack-review --strict` → `Change 'absorb-gstack-review' is valid`；「gstack 不在场可跑通」按 amendment 约定以 grep 归零静态证成 | ✅ |
| 6.3 issues 池记三条 todo（显式传 change 字段） | `openspec/issues/open/todo/T267.md`（python.md domain）/ `T268.md`（spec-review 侧 autoplan 姊妹依赖）/ `T269.md`（仓根 `openspec/workflow/` 孤儿副本清理），三者 frontmatter 均 `source_change: "absorb-gstack-review"`、`status: OPEN`；`openspec/issues/INDEX.md` 已同步（另有 T270 为 code-review 期新增，非本条要求） | ✅ |
| 6.4 dogfood 前置开窗 + 本 change 自跑 code-review 并核三锚 | 开窗实证：`readlink ~/.sdflow/workflow` → `/Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-init/assets/workflow`（本次亲验，指向开发树）；实跑产物 `code-review-report.md:32` `<!-- sdflow:step1-broad-review v1 mode="subagent" -->`、:81 `lens="broad"` 行（`hits[].raw="scope-audit"` 归约）、:26 `fanout-capability` 锚 `mirrors="broad,domain,adversarial,history"`；`anchor_lint` 本次亲跑该报告 → `[anchor_lint] CLEAN`（rc=0） | ✅ |
| **实现期聚合覆盖（tickets 轨专属）** | `impl-reports/task6-impl-verification.md`（`R-ID: all` 收尾票）：三层证据 schema 齐全——unit `\|/usr/bin/python3 -m pytest -q -rs\|0\|458d44d338843f2b7a94b4501de96335990a7f63`；integration / e2e **未覆盖**（本仓无该分层，判定依据 CLAUDE.md + CI `mechanical-gates.yml` 只定义单一聚合命令，报告 §1 已实测论证）。**SHA 一致性核验**：仅 unit 一层判「通过」，其锚 SHA 单一；`git cat-file` 确认 `458d44d` 为真实 commit 且 `--is-ancestor HEAD` 成立。**锚语义 = 实现期结束时聚合套件通过**（该票执行于 code-review 及其自动修复循环之前，时效缺口为已知且接受的残余风险，报告 §定位声明已如实登记） | ✅ |

## 缺口清单

### 核心缺口（FAIL 项）

**无。**

### Minor 缺口（可接受 / deferred）

1. **仓根 `openspec/workflow/` 孤儿副本仍含旧 `gstack-adv` 提法**（`openspec/workflow/lens-metric-contract.md:44,64`、`WORKFLOW-GUIDE.md:79,94,126`）。
   - 判为 Minor 且**不构成功能缺口**：本次亲跑 `bash ~/.sdflow/hack/resolve-workflow.sh --root .` → `/Users/cheneyzhao/.sdflow/workflow`（全局 canonical，即开发树），
     即该目录**未被识别为本地 pin**（`resolve-workflow.sh:37-38` 明写 pin 判据只查 `workflow.md` / `spec-checklists` / `code-checklists`，`tools/` 与散落副本不算），故不会遮蔽权威源。
   - 已按 tasks 6.3③ 显式 defer 为 `T269`（记明「非 pin 死件、grep 假阳来源」）——属计划内 defer，非漏做。
2. **`docs/skill-authoring-best-practices.md` 等横向提炼文档仍引 gstack review 做案例**（如 :48/:49 引「pre-emit gate」出处）。
   - 这是**对第三方 skill 设计的引用与致谢**，非运行时依赖描述，与 5.3 的「提法更新」目标不冲突；`docs/workflow-skills/gstack-review.md` 按设计门 Q4 明确保留同理。
3. **`tasks.md` 当前为未提交修改态**（`git status` 显示 ` M openspec/changes/absorb-gstack-review/tasks.md`，即 done 流程批量勾选的结果尚未落 commit）。
   - 仅影响提交盘面整洁，由后续 archive/commit 步收口。

## 附：反假绿自检

- 复选框状态**未被采信**——23 条逐条另找 diff 行号 / 测试函数名 / 实跑输出锚。
- 既有报告措辞**未被采信**——`task6-impl-verification.md` 中的 pytest 结果、grep 归零、validate 绿、`readlink` 指向、`anchor_lint` CLEAN 五项均由本次 verify **重新亲跑复现**；其引用的 `458d44d` SHA 经 `git cat-file` + `--is-ancestor` 独立核实存在且在 HEAD 祖先链上。
- `code-review-report.md` 的 `reviewed_sha=4ac1e7b…` 与当前 HEAD 之间仅一条 commit（`4539d9f` 代码审报告本身）+ 一个 issue 文件（`T270.md`），**无生产代码/资产改动**（`git diff --name-only 4ac1e7b..HEAD` 排除 change 目录后仅 `openspec/issues/open/todo/T270.md`）——代码审结论覆盖当前盘面。

PASS
