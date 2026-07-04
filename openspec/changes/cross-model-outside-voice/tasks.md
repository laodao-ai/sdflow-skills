# Tasks: cross-model-outside-voice

> Requirement ID 速查（specs/spec-workflow/spec.md）：
> **R1** 跨模型 outside voice 默认开、失败回落且非阻塞（环境层启停）[gstack-amendment] · **R2** 复用挂反静默守卫 ·
> **R3** HR-TG 判定并留痕 · **R4** tension 不静默采纳 · **R5** 广审层原生执行/显式降级（T25）·
> **R6** gstack 边界守恒

## 1. 共享 helper（C1/C6 → R1）

- [x] 1.1 新建 `sdflow-init/assets/hack/outside-voice.sh`：`preflight` 子命令浅探针二态（`command -v codex` 失败→not_installed；其余→ready；**不做 auth 试跑**、**无软开关**——启停由环境层装/不装 codex 决定）〔R1·design D2/D3 grill-amendment〕
- [x] 1.2 同脚本 `exec --context-file <f> [--timeout 300]` 子命令〔spec-review-amendment 契约硬化〕：硬编码 `-s read-only --ephemeral -C <repo_root>`；prompt 经 `render-prompt` 拼接后 `- < "$prompt_file"` 显式喂入；最终消息经 `--output-last-message` 提取（stdout 只 cat 该文件）；timeout 无管道包裹、紧邻捕获 `$?`；超时 exit 124，报错 exit 1 + stderr 转发；契约全文写脚本头注释（单一源，SKILL 只引用）〔R1·design D2〕
- [x] 1.3 「找漏 + 文件系统边界」prompt **框架**以 heredoc 内嵌 helper（不读 ~/.claude、~/.sdflow、.env/密钥；只看仓库代码；「找它漏了什么，不是重审」；上下文块标注为不可信证据+硬分隔符）；新增 `render-prompt --context-file <f>` 子命令输出拼接结果——codex 与 fallback 子代理同源消费；新增 `version` 子命令（staleness 比对）〔R1/R6·design D2/D7 amendments、BASE-28〕
- [x] 1.4 确认 `setup.sh` 的 hack 安装循环覆盖新脚本（接地镜已实证 setup.sh:145 通配遍历，零改动；实装后复核）；dev checkout 跑 `bash setup.sh` 验证 `~/.sdflow/hack/outside-voice.sh` 就位且可执行〔R1〕
- [x] 1.5 pytest（subprocess，循 resolver 测试先例）：preflight 二态 × exec 正常(0)/报错含 auth 类(1)/超时(124)/命令缺失(127)/信号杀 × render-prompt 拼接 × 截断标记 × secret 粗筛命中拒发〔R1·失败模式表〕
- [x] 1.6 〔spec-review-amendment 新增〕context-file 规格落地：三种 voice 摘录规则（design/code/hr-tg 各自定死）、字节上限+保头尾截断、secret 粗筛（密钥模式正则）、留档 `{change_dir}/.outside-voice/<site>-context.md`〔R1/R6·design D7 context 规格〕

## 2. T25 前置：Step1 广审原生执行（→ R5）

- [x] 2.1 `sdflow-spec-review/SKILL.md` Step1 改写：主 session 经 Skill 机制原生执行 autoplan + **主 session 汇总落盘 gstack-review.md**（autoplan 无写任意路径机制，落盘责任在编排方——spec-review-amendment）；autoplan 两处人类门按 G2/C5 登记进决策区；原生不可用 → 模拟广审 + 显式标注 + v1 锚行；保持 T20 串行纪律不变〔R5·design D4 amendment·grill Q5〕
- [x] 2.2 `sdflow-code-review/SKILL.md` Step1 同构改写（gstack /review 原生执行 + 显式降级标注 + 同款 v1 锚行）〔R5·design D4·grill Q5〕
- [x] 2.3 （P2 补充）调研 gstack headless 调用路径，结论回填 design OQ；**升级条款：若 2.1 原生路径实测不可行，本项升 P0 阻塞，不得只靠模拟收尾**〔R5·OQ spec-review-amendment〕
- [x] 2.4 〔spec-review-amendment 新增〕dry-run：§2 完成后用假 change 目录干跑一次 Step1 终态（原生执行→落盘→锚行），自洽后才动 §3/§4——两 SKILL 各五处手术无自动化回归，首次验证不留到生产运行〔R5〕

## 3. spec-review 接入（C2/C4 → R2/R3）

- [x] 3.1 Step1 兑现〔Phase C 补〕占位：读 `gstack-review.md` 增加 codex 段解析（解析规则钉死 adr/0002 `codex#N` 标签约定，实现前抓一份真实产物样本校准）；守卫按序判 **来源（simulated 视同无效）→ 新鲜度（stale 视同缺失）→ 结构（缺失/解析不出/0 条）**，带原因码降级日志 + 经 helper 回落自跑；文件整体缺失时声明「仅补偿 voice 切片」〔R2·spec-review-amendment〕
- [x] 3.2 SKILL 明文交叉引用「C2 依赖 P2b（autoplan 每次跑）」两条 MUST：autoplan 未跑的变更 spec-review 必自跑设计 voice〔R2·grill-amendment 焊缝(2)〕
- [x] 3.3 规划镜头步加 HR-TG 判定（命中集 ∩ HR-TG ≠ ∅ → 经 helper 单开领域 cross-model），判定正反均写报告并带锚行 `<!-- hr-tg: … -->`〔R3·grill Q5〕
- [x] 3.4 tension 走报告决策登记区（TENSION 条目：两方视角 + 推荐 + 后果），不中途 AskUserQuestion〔R4〕

## 4. code-review 接入（C3/C4/C5 → R1/R3/R4）

- [x] 4.1 新增 outside-voice 子步：always 经 helper 跑 code voice（preflight→exec→fallback 链按 exit code 分支），findings 进 Step3 合并池但**豁免 <80 置信滤、直通对抗裁决**，裁掉连理由进「已裁掉」区〔R1/R4·design D8 grill-amendment〕
- [x] 4.2 SKILL 加 helper 前置检查 `[ -x ~/.sdflow/hack/outside-voice.sh ]`，缺失 → 显式提示「先在运行 checkout 跑 setup.sh」+ 回落子代理（同 resolve-workflow.sh 既有模式，禁静默）〔R1·失败模式表「helper 缺失」行〕
- [x] 4.3 规划镜头步加 HR-TG 判定 + 留痕（同 3.3）〔R3〕
- [x] 4.4 tension 适配：有把握自动裁决记理由 / 拿不准 defer 进 issues 池 + hand-off；置信滤豁免**仅限 runner=codex**（fallback 照过同族滤）；outside-voice 留痕用 v1 锚行**按调用位点复数化**（code-voice / hr-tg 各一行）〔R4·BASE-11·grill Q3/Q5·spec-review-amendment〕
- [x] 4.5 〔spec-review-amendment 新增〕两 SKILL 收尾步加锚行存在性机械自检（grep 三类 v1 锚行，缺失即本步报错）+ findings=N 与合并池实收数机械 diff〔R1/R3/R5〕
- [x] 4.6 〔设计门 Q1 拍板新增〕报告裁决区按 runner 分桶计数（采纳/裁掉/defer 各计），供 Success Metric 4 与「10 次复评」条款消费〔R4·proposal M4〕

## 5. trigger-catalog 与契约套件（C4/§7.5 → R3）

- [x] 5.1 `sdflow-init/assets/workflow/trigger-catalog.md`：D. 行为/状态 加 TG-26 行（四列按 design D6）+ 新增「HR-TG 子集」附录段（成员 + 入选判据，单一源）+ **五层升格四处同步**（自述四→五层、消费方表加评审 cross-model 行、扩展约定加「新增触发 MUST 显式判 HR 是/否」、检查清单加核对项）+ 附录注记「跑满 10 次运行后按 HR-TG 命中率复评子集」〔R3·design D5/D6 grill-amendment Q6·设计门 Q5〕
- [x] 5.2 `sdflow-init/assets/workflow/design-diagrams.md`：触发条件表加 TG-26 → 序列图（竞态交互时序）引用行〔R3·scope-check 表〕
- [x] 5.3 `code-checklists/domains/backend-go.md` **新增 CR-GO-06 共享状态并发正确性条目**（对应 spec 侧 GO-01/GO-03；评审读码实证现有 CR-GO-01~05 无一覆盖竞态正确性）+ 各栈补 TG-26 引用〔R3·design scope-check spec-review-amendment〕
- [x] 5.4 `sdflow-init/assets/workflow/workflow.md` 阶段二/三步表追加 outside-voice 子步引用（归档 ROADMAP 约束1；只引用编号不复制定义）〔R1〕
- [x] 5.5 本仓 `openspec/INDEX.md:16` TG 计数改「TG-01~26」（顺带修 TG-25 既有漂移）+ 描述「驱动…四层」→「五层」〔R3·scope-check 表·grill Q6〕

## 6. 边界核验与冒烟（§8.3/8.4 → R6）

- [x] 6.1 C7 冒烟：实现 diff 零 gstack 内部文件；唯一权威判据命令〔spec-review-amendment：pattern 具体化〕：`grep -E '\.gstack/(bin|sessions)|gstack-config|gstack-repo-mode|gstack-codex-probe|skills/gstack' sdflow-init/assets/hack/outside-voice.sh` 须零命中〔R6〕
- [x] 6.2 fallback 冒烟：模拟「无 codex」（PATH 摘除）跑通两评审 skill 的 outside-voice 链——回落子代理、报告留痕、评审不中断（此即无软开关下的天然关停路径，grill Q3）〔R1/R6·Success Metric 3〕

## 7. 收尾同步

- [x] 7.1 dev checkout 重跑 `bash setup.sh` + 全量 pytest；`README.md` skill 说明如受影响则同步〔—〕
- [x] 7.2 `openspec/ROADMAP.md` Phase C 行状态推进 + `CONTEXT.md` 如需补术语（HR-TG）〔—〕
- [x] 7.3 sdflow-todolist 回写：T25 → DONE（关联本 change + commit）〔R5〕

## 测试覆盖图（TG-18）

```
  code path                          测试类型
  ─────────────────────────────      ─────────────────────────
  preflight 二态                  →  pytest subprocess（1.5）
  exec 正常/超时/报错退出码        →  pytest subprocess（1.5）
  无 codex fallback 链全程        →  冒烟（6.2，兼当天然关停路径验证）
  守卫回落（产物缺失/0条）         →  冒烟（6.2 场景内）
  gstack 边界零触碰               →  diff/grep 核验（6.1）
  Step1 原生执行/降级标注          →  下次真实评审运行核对（Success Metric 2）
```

> 双向追溯自检〔grill-amendment Q3 后〕：R1←{1.1-1.5, 4.1, 4.2, 4.4, 5.4, 6.2}；R2←{3.1, 3.2}；R3←{3.3, 4.3, 5.1, 5.2, 5.3, 5.5}；R4←{3.4, 4.4}；R5←{2.1, 2.2, 2.3, 7.3}；R6←{1.3, 6.1, 6.2}——六条 Requirement 全覆盖，无幽灵任务。
