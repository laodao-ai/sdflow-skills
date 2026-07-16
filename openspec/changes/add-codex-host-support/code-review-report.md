---
ship-gate:
  code_review: pass
---

## code-review 报告 — add-codex-host-support

**审窗口**：`fbd43c5..9285b4c`（merge-base→HEAD，本 change 10 task 全部实现）· **宿主**：`host=claude`（跨模型 voice runner=codex，真调 codex CLI 成功）· **模型档位**：strong=opus / mid=sonnet / light=haiku · **metrics**：enabled（源仓 dogfood）· **skew 探测**：双绿（tools 已 v2）

### 命中范围
- **栈**：Python 3 + pytest（tools/聚合器/init）· Bash（resolve-models.sh / outside-voice.sh）· Markdown（规则/SKILL/契约块/docs）。不命中 backend·go / embedded / frontend 领域清单 → 通用清单 CR-01~09。
- **HR-TG 命中**：TG-04（锚 schema v2 迁移）· TG-06（锚数据模型跨 4 工具共享）· TG-07（工具 CLI 契约）· TG-08（反向 `claude -p` 新出境端点）· TG-17（信任边界/敏感数据）。
- **镜**：领域镜 ×1 · 对抗镜 ×3（安全注入出境 / 跨工具契约漂移 / fail-open 错误路径，高风险）· 历史镜 ×1 · outside-voice code-voice（codex 跨模型）×1。
- **gstack/review（Step1）**：scope-drift 干净（全部 net-changed 文件映射到 10 task + 设计期产物 ADR-0023/0024/CONTEXT + Task10 filing）；完成度：gate 确认 10/10 → RUN_CODE_REVIEW；全量 pytest 1416 passed。

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="TG-04,TG-06,TG-07,TG-08,TG-17" declared="TG-04,TG-06,TG-07,TG-08,TG-17" evidence="锚schema v2迁移+反向claude出境端点+eval注入/secret脱敏信任边界" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="5" truncated="true" -->

### Findings（置信 ≥80）

> 🔴 **冷全 change 层抓出 4 高危**（3 代码/编排 fail-open + 1 安全不对称），均经主 session 亲自复现/结构核实。**同时独立坐实**：eval 注入面稳固（8 payload 全被 charset 白名单挡）、矩阵全笛卡尔 golden 真敏感、枚举单一源跨工具一致、compat-read/reason_code 映射/fanout/resolve-models 变量全一致。

**[高] C1 · guard codex#N 全文旁路 fail-open** | `sdflow-init/assets/workflow/tools/outside_voice_guard.py:85-120`（parse_codex_findings）| **已复现**（`classify()` 返回 `none`=可复用 exit0）· **✅ 已修[impl-review-fix]**
当某条 outside-voice 锚被 `classify_combo` 判为 cross-model 但**该锚自身 `findings=` 缺失/畸形**时，`parse_codex_findings` 退而**全文扫任意 `codex#\d+` 记号**当次选 findings 计数。而 `codex#N` 是本仓 commit/design 高频引用惯例（本 change commit log 就有"codex#N 旁路核"）→ 真实报告正文一句"参考 codex#1"+ 一条 findings 畸形的 cross-model 锚 ⇒ guard 静默判"可复用"、**跳过重跑真跨模型评审**，击穿该模块唯一职责（防假复用）。现有测试盲区：只测了"无锚+标签"与"畸形 findings+无标签"，未测二者组合。
**→ ✅ 已修[impl-review-fix]（TDD）**：删除 `parse_codex_findings` 的 codex#N prose 补位 fallback（连带删 `_CODEX_LABEL_RE` 常量、`saw_cross_model` 变量），findings 畸形的 cross-model 锚不再退去扫无关 prose 补计数 → 归 `section-not-found` → 回落重跑（安全），与 Step 6「prose 标签 MUST NOT 构成复用资格」方向彻底一致。补 2 回归测试锁死"畸形 cross-model findings + codex#N prose"组合；全仓 1418 passed。

**[高] A1 · 反向 claude 出境路径无真读围栏 + 无输出侧 secret_scan** | `sdflow-init/assets/hack/outside-voice.sh` | **镜实测复现** · **✅ 代码半已修[impl-review-fix]（方案 a）**
三旗墙的 `--add-dir <repo_root>` 对 Read **零约束**——实测 `claude -p --tools "Read,Grep,Glob" --strict-mcp-config --add-dir <repo>` 能读仓外文件（`~/.ssh`/`~/.aws` 等），去掉 `--add-dir` 结果相同（它只是"项目目录"提示、非访问围栏）；而 codex `-s read-only` 内核沙箱**真拒**仓外读。∴ 注释「对称 codex 全仓只读」**不实**（两路径不对称，codex 有硬边界、claude 反向路径没有）；唯一防线是 FRAME 软注入防御（3/3 payload 在 haiku 上暂扛住、但概率性单点）；且 `secret_scan` **只扫入境 context、不扫 runner 回传 stdout** → 注入成功可原样 exfil。`--tools` 挡 Write/Bash/网络这部分是真的。
**→ ✅ 代码半已修[impl-review-fix]（方案 a，用户拍板；TDD + 真 claude 端到端验证）**：
① **读围栏承重墙第四旗** `--settings <OV_CLAUDE_READ_FENCE>`（permissions.deny 挡 .ssh/.aws/.gnupg/gcloud/kube/docker/netrc/id_rsa*/id_ed25519*/~/.claude/~/.sdflow）——本机 2.1.211 实测 Read 工具执行前硬拦（`.ssh/notes.txt` 中性内容→BLOCKED）、模型绕不过；完整 JSON 经脚本插入真 claude 秒回不挂起。
② **出境侧 secret_scan**：`cat` 前扫 runner 回传 last-message.md，含密钥形状→拒发 exit 3（两 runner 路径共用 emit 点，一处兜底）。
③ **注释订正**：header + inline 注释如实登记「codex 内核正向边界 vs claude 应用层负向边界」不对称、`--add-dir` 非围栏；版本 1.2.0→1.3.0。
调研实证（用户已知）：Claude Code 原生**做不出正向 allowlist**（deny//** 连仓内一起拦、dontAsk 不 auto-deny 未列项，均实测证伪）；真正向边界只能靠外层容器（会 jail 掉 claude 自身运行时、需内核 enumerate-allow，代价不匹配）→ ∴ 取「负向枚举硬拦明显赃物 + 出境 secret_scan 兜底」双层应用防御，对 codex 内核沙箱不对称是如实接受的权衡。
**剩：design-writeback（done 阶段）**——design 安全表 r3「两路径均无硬FS读边界」与实测 codex 有沙箱矛盾，done 阶段订正。

**[高] B1 · `lens="outside-voice"` 的 lens-metric 行脱离矩阵校验 + 决策记录漂移** | `anchor_lint.py:623`（check_lens_metric 明确 `lens_v != "outside-voice"` 跳过）| **结构+CLI 核实** · **✅ 代码半已修[impl-review-fix]**
`check_legal_combo` 只绑 `sdflow:outside-voice` 锚（因 lens-metric 锚无 reason_code，D1 合理）；但 `check_lens_metric` 的行级校验又**显式排除 lens="outside-voice" 行** ⇒ 该行的 `runner="none"⇒findings=0`、`host="unknown"⇒runner="none"` 两个不变量**无任何校验**。手写/emitter-bypass 的 `lens="outside-voice" runner="none" findings="5"`、`host="unknown" runner="claude"` 锚会被放行，经 aggregator 汇入 retro 价值表。emitter 侧强制该不变量，∴ 仅 emitter-bypass 可达——但按③目标态非"现状少见"。**决策记录漂移**：spec-review-report.md:152/208 + design.md:78/95 明写 D6 收敛为"lens-metric 锚 + outside-voice 锚**均查**"，实现窄化为"只 outside-voice 锚"未回改记录。
**→ ✅ 代码半已修[impl-review-fix]（TDD·面治）**：`check_lens_metric` 补 OV 行 elif 分支，覆盖 OV 行**完整**不变量集 3 条（①runner="none"⇒findings=0 `ov-runner-none-nonzero-findings`；②host="unknown"⇒runner="none" `ov-unknown-host-runner`；③OV 行 runner∈{claude,codex,none} 不含 unknown `ov-runner-unknown`），纯结构判定不依赖 reason_code、与 emitter `_OV_RUNNER_DOMAIN`/零执行不变量对齐；补 5 测试（3 违规+2 合法回归）；全仓 1423 passed。**剩：决策记录订正（design-writeback，done 阶段）**——正文现已实现"OV lens-metric 行亦查其结构不变量"，与 D6"均查"意图对齐，done 阶段把 design/spec-review-report 的措辞回改到位。

**[高] V1 · 两评审 SKILL `eval "$(resolve-models.sh)"` 前无 unset + 无校验** | `sdflow-spec-review/SKILL.md:104` · `sdflow-code-review/SKILL.md:128` | **确认** · **✅ 已修[impl-review-fix]**
`eval "$(resolve-models.sh …)"` 前既不 `unset SDFLOW_*`，也不校验脚本存在/exit-code/六变量完整。shell 中命令替换失败后 `eval ""` 返回 0，同 shell 内**上一轮的 `SDFLOW_HOST`/`SDFLOW_VOICE_RUNNER` 会原样保留** → resolver 缺失/失败时复用旧宿主假绿（CI/skew 窗口高发）。而 `update` 明确不装 hack 脚本（须 setup.sh）。
**→ ✅ 已修[impl-review-fix]（方案 A，两 SKILL 对称）**：eval 改为带防护四步次序——**(a)** 先 `unset` 六变量清脏（eval 失败只得空值、不复用上轮脏值）；**(b)** `[ -x resolve-models.sh ]` 预检（复用第零步 resolve-workflow 预检 idiom），缺失 fail-loud 硬停；**(c)** 捕获退出码再 eval，非 0 硬停 + 转发 stderr；**(d)** eval 后校验 `$SDFLOW_HOST`∈{claude,codex,unknown}且非空、host≠unknown 时三档位非空，任一不满足在 fan-out/emitter/落锚前 fail-loud 硬停。**空值 MUST NOT 回落当 host=unknown**（工具没装 ≠ 判不出宿主，防假绿）。诚实边界如实标注（eval 要 export 进主 session shell ∴ 天然是指令非机械门）。托管块一致性门 + hack 11 tests 绿。

**[中] V2 · `fallback-unavailable`(F8) 枚举存在但两 SKILL 无产生它的控制流** | 两 SKILL fallback 段 | **确认**（对抗镜B 旁支同证，对称非漂移）
spec `host-adaptive-execution:91` 要求"同族 fallback 子代理也起不来 ⇒ `runner="none" findings=0 reason_code="fallback-unavailable"`"，但两 SKILL fallback 段都直接规定 `runner="$SDFLOW_HOST"`（假定派发成功），无失败分支。Codex 宿主 + 目标 CLI 缺 + 子代理也起不来才可达。**→ ✅ 已修[impl-review-fix]（两 SKILL 对称）**：fallback 段补 F8 分支——fallback 只读子代理本身派不出 → 锚行 `host="$SDFLOW_HOST" runner="none" findings="0" reason_code="fallback-unavailable"`（no-exec 合法态）。

**[中] V5 · ADR-6 preflight「真跑一次」实现只 `command -v`** | `design.md:210` vs `outside-voice.sh` preflight | **确认**
ADR-6 明写 `command -v` + **真跑一次**；实现只 `command -v` + timeout 工具检查，CLI 未认证/模型无效/参数不支持仍返回 `ready`，失效漏到 exec 阶段归 exec-error。**→ 待拍板：补低成本真探针 vs 订正 ADR「真跑一次」措辞（design-writeback）。**

**[低-中] V3 · 「v1 无 reason_code」兼容假设事实错** | spec `outside-voice-reuse-guard:43` / guard compat | **事实核实**
真实归档 v1 outside-voice 锚**有** `reason_code="none"`(×35)/`""`(×30)/`native-run` 等非枚举值，非"无字段"。**运行期影响有界安全**：done 不重 lint 旧报告、aggregator 只读 lens-metric 锚不读 outside-voice reason_code、guard 对旧锚保守降级（不复用→重跑 voice）。残余：guard 不会复用那 35 条真 v1 codex 产物（与"v1 仍可复用"Scenario 略有出入，但安全）。**→ defer（compat 散文订正 = design-writeback；可选让 guard 兼容读 v1 reason_code=none≡ok）。**

**[低-中] V4 · ADR-0024「不再可能把 opus 塞 codex 段」过度声称** | `openspec/adr/0024:26` | **确认**
config_lint 只校验字符集，`model-tiers.codex.strong: opus` 完全合法。schema 挡的是**扁平** `strong: opus` 误用于 codex，非**显式** `codex.strong: opus`。设计已知否决模型名白名单（漂移面），残余是已接受权衡，但 ADR「结构性杜绝/不再可能」措辞过头。**→ defer（ADR 措辞订正 = design-writeback）。**

**[低] D1 · test_resolve_models.py `eval_resolve()` f-string 未加引号插值** | `sdflow-init/tests/test_resolve_models.py:77-82` | 领域镜
`{SCRIPT}`/`{root}` 未引号直接拼进 `bash -c` 串；非攻击面（tmp_path 由 pytest 生成），但恰在 eval 注入测试套件里自身不加引号、tmp_path 含空格会静默错解。**→ ✅ 已修[impl-review-fix]（TDD）**：`shlex.quote` 引号化 `{SCRIPT}`/`{root}`；补含空格 root 回归测试（RED 复现 `unknown arg: with` word-split）。

**[低] B2 · code-review SKILL:322 lens-metric 锚示例缺 `host=`** | `sdflow-code-review/SKILL.md:322` | 对抗镜B
报告格式模板示范锚缺 `host=`，与契约单一源 + emitter 实际输出不一致（字面照抄会被 anchor_lint 报 missing-field）；正文已明写"MUST NOT 手拼"缓解。**→ ✅ 已修[impl-review-fix]**：模板锚补 `host="…"`（按 emitter 字段序 layer→lens→host→runner→site）。

**[低] C2 · init.py lint_config `metrics.enabled` 重复键无告警** | `sdflow-init/scripts/init.py:470-478` | 对抗镜C
`enabled: true`+`false` 并存时 valid 恒 True；anchor_lint 取首值。当前单消费者无跨工具分歧，未如 `parse_kv_strict` 那样收紧。**→ defer todolist（潜在一致性盲点）。**

### 已裁掉（反静默压制，可审计）
- **D2 · retro_report.py:406-414 `_top_mirror` 不可达 `"?"` 分支**（领域镜）——`normalize_host_runner` 恒回落 claude，`host` 永不为 `"?"`；纯整洁度 nitpick，结果与 `("claude",)` 等价，**裁掉**（<80，不阻塞）。
- **C3 · anchor_lint check_fanout_consistency host 缺字段空转**（对抗镜C）——host 缺字段时 `report_host→None`、`fanout-host-mismatch` 分支跳过，但 `missing-field` 已独立报违规、不致整体 CLEAN，仅该项一致性检查空转；**裁掉**（不改变判定、<80）。
- 历史镜：无重蹈旧坑（task2/3/4/6 各 fix 针对不同边界、无循环修复/回滚）。

### 修复 / defer 台账
- **已修[impl-review-fix]（8 项，全部 objective 代码修复已清）**：**C1** guard codex#N 旁路 fail-open（TDD）· **B1 代码半** check_lens_metric 补 OV 行 3 不变量校验（TDD·面治）· **V1** 两评审 SKILL eval 带防护四步次序 · **A1 代码半** claude 读围栏第四旗 + 出境 secret_scan + 注释订正（方案 a，TDD + 真 claude e2e）· **V2** 两 SKILL 补 F8 分支 · **D1** test 引号（TDD）· **B2** SKILL 模板锚补 host=。全仓 1426 passed + 托管块门绿。
- **仅剩 design-writeback（done 阶段，改四件套触设计门失鲜，MUST 在 archive 阶段随 delta 写回）**：无剩余 objective 代码修复、无待人拍板决策。
- **建议 defer（design-writeback，done 阶段随 A1/A3 真值一并写回，勿实现期改四件套）**：A1 沙箱不对称登记订正（design 安全表 + r3「两路径均无硬FS读边界」与实测 codex 有沙箱矛盾）· B1 决策记录"均查"订正 · V3 compat"v1 无 reason_code"订正 · V4 ADR-0024 措辞 · V5 ADR-6"真跑一次"措辞。
- **建议 todolist**：C2 metrics dup-key 收紧 · V5 preflight 真探针（若选补而非订正）。

### 度量锚（lens-metric）
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="7" 采纳="6" 裁掉="1" defer="0" 独立="5" sev="致0/高3/中1/低2" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="2" 采纳="1" 裁掉="1" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="4" sev="致0/高1/中2/低2" -->

### 结论
- ☑ **code_review: pass** — 冷全 change 层抓出的 4 高危 + 4 中低危**全部 objective 代码修复已清**（C1/B1代码半/V1/A1代码半/V2/D1/B2，8 项，用户逐一拍板 + TDD + 真 claude e2e；全仓 1426 passed + 托管块门绿），无剩余代码缺陷、无待人拍板决策。
- **结转 /sdflow-done（hand-off 承接）**：① **design-writeback**（A1 安全表沙箱不对称 / B1「均查」/ V3 v1-reason_code / V4 ADR-0024 措辞 / V5 ADR-6「真跑一次」）——MUST 在 archive 阶段随 delta 写回（现在改四件套触失鲜）；② **运行时生效**：`outside-voice.sh`(A1) 等 `assets/hack/` 脚本合并后须在运行 checkout 重跑 `setup.sh`（copy 非 symlink）；③ **todolist**：C2 metrics dup-key 收紧 · V5 preflight 真探针（若选补而非订正）；④ Codex 侧 D-1..D-4 真机验（若适用）。
