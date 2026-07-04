# Tasks: cross-model-outside-voice

> Requirement ID 速查（specs/spec-workflow/spec.md）：
> **R1** 跨模型 outside voice 默认开、可关、失败回落且非阻塞 · **R2** 复用挂反静默守卫 ·
> **R3** HR-TG 判定并留痕 · **R4** tension 不静默采纳 · **R5** 广审层原生执行/显式降级（T25）·
> **R6** gstack 边界守恒

## 1. 共享 helper（C1/C6 → R1）

- [ ] 1.1 新建 `sdflow-init/assets/hack/outside-voice.sh`：`preflight` 子命令（env `SDFLOW_CODEX_VOICE=off`→disabled；`command -v codex`→not_installed；试跑超时/auth 错→not_authed；通过→ready）〔R1·design D2/D3〕
- [ ] 1.2 同脚本 `exec --prompt-file <f> [--timeout 300]` 子命令：codex 调用包装，findings→stdout，超时 exit 124，报错 exit 1 + stderr 转发〔R1·design D2〕
- [ ] 1.3 「找漏 + 文件系统边界」prompt 模板以 heredoc 内嵌 helper（不读 ~/.claude、~/.sdflow、.env/密钥；只看仓库代码；「找它漏了什么，不是重审」）〔R1/R6·design D7、BASE-28〕
- [ ] 1.4 确认 `setup.sh` 的 hack 安装循环覆盖新脚本（按现有 assets/hack/* 遍历则零改动，逐字核实后记录结论）；dev checkout 跑 `bash setup.sh` 验证 `~/.sdflow/hack/outside-voice.sh` 就位且可执行〔R1〕
- [ ] 1.5 pytest（subprocess，循 resolver 测试先例）：preflight 四态 × exec 超时(124)/报错(1)/正常(0) × off-switch 优先级〔R1·失败模式表前 5 行〕

## 2. T25 前置：Step1 广审原生执行（→ R5）

- [ ] 2.1 `sdflow-spec-review/SKILL.md` Step1 改写：主 session 经 Skill 机制原生执行 autoplan（指令直接进主 session，非子代理转述）；原生不可用 → 模拟广审 + 报告显式标注「模拟广审（降级模式）」；保持 T20 串行纪律（checkpoint 后才 fan-out）不变〔R5·design D4〕
- [ ] 2.2 `sdflow-code-review/SKILL.md` Step1 同构改写（gstack /review 原生执行 + 显式降级标注）〔R5·design D4〕
- [ ] 2.3 （P2 补充，不阻塞）调研 gstack headless 调用路径，结论回填 design Open Questions〔R5·OQ〕

## 3. spec-review 接入（C2/C4 → R2/R3）

- [ ] 3.1 Step1 兑现〔Phase C 补〕占位：读 `gstack-review.md` 增加 codex 段解析；缺失/解析不出/0 条 → 显式降级日志 + 经 helper 回落自跑设计 outside voice〔R2〕
- [ ] 3.2 SKILL 明文交叉引用「C2 依赖 P2b（autoplan 每次跑）」两条 MUST：autoplan 未跑的变更 spec-review 必自跑设计 voice〔R2·grill-amendment 焊缝(2)〕
- [ ] 3.3 规划镜头步加 HR-TG 判定（命中集 ∩ HR-TG ≠ ∅ → 经 helper 单开领域 cross-model），判定正反均写报告〔R3〕
- [ ] 3.4 tension 走报告决策登记区（TENSION 条目：两方视角 + 推荐 + 后果），不中途 AskUserQuestion〔R4〕

## 4. code-review 接入（C3/C4/C5 → R1/R3/R4）

- [ ] 4.1 新增 outside-voice 子步：always 经 helper 跑 code voice（preflight→exec→fallback 链按 exit code 分支），findings 进 Step3 合并池〔R1〕
- [ ] 4.2 SKILL 加 helper 前置检查 `[ -x ~/.sdflow/hack/outside-voice.sh ]`，缺失 → 显式提示「先在运行 checkout 跑 setup.sh」+ 回落子代理（同 resolve-workflow.sh 既有模式，禁静默）〔R1·失败模式表「helper 缺失」行〕
- [ ] 4.3 规划镜头步加 HR-TG 判定 + 留痕（同 3.3）〔R3〕
- [ ] 4.4 tension 适配：有把握自动裁决记理由 / 拿不准 defer 进 issues 池 + hand-off；报告 outside-voice 段四态必填（已跑/回落/关闭/守卫降级）〔R4·BASE-11〕

## 5. trigger-catalog 与契约套件（C4/§7.5 → R3）

- [ ] 5.1 `sdflow-init/assets/workflow/trigger-catalog.md`：D. 行为/状态 加 TG-26 行（四列按 design D6）+ 新增「HR-TG 子集」附录段（成员 + 入选判据，单一源）〔R3·design D5/D6〕
- [ ] 5.2 `sdflow-init/assets/workflow/design-diagrams.md`：触发条件表加 TG-26 → 序列图（竞态交互时序）引用行〔R3·scope-check 表〕
- [ ] 5.3 核对 `code-checklists/domains` 并发 CR 项现状，按需补 TG-26 引用行，结论回填 design scope-check 表 ⚠ 行〔R3·OQ〕
- [ ] 5.4 `sdflow-init/assets/workflow/workflow.md` 阶段二/三步表追加 outside-voice 子步引用（归档 ROADMAP 约束1；只引用编号不复制定义）〔R1〕
- [ ] 5.5 本仓 `openspec/INDEX.md:16` TG 计数改「TG-01~26」（顺带修 TG-25 既有漂移）〔R3·scope-check 表〕

## 6. 边界核验与冒烟（§8.3/8.4 → R6）

- [ ] 6.1 C7 冒烟：实现 diff 零 gstack 内部文件；`grep` helper 源码无 gstack 内部路径引用〔R6〕
- [ ] 6.2 fallback 冒烟：模拟「无 codex」（PATH 摘除）跑通两评审 skill 的 outside-voice 链——回落子代理、报告留痕、评审不中断〔R1/R6·Success Metric 3〕
- [ ] 6.3 off-switch 冒烟：`SDFLOW_CODEX_VOICE=off` 下报告出现「已显式关闭」标注〔R1〕

## 7. 收尾同步

- [ ] 7.1 dev checkout 重跑 `bash setup.sh` + 全量 pytest；`README.md` skill 说明如受影响则同步〔—〕
- [ ] 7.2 `openspec/ROADMAP.md` Phase C 行状态推进 + `CONTEXT.md` 如需补术语（HR-TG）〔—〕
- [ ] 7.3 sdflow-todolist 回写：T25 → DONE（关联本 change + commit）〔R5〕

## 测试覆盖图（TG-18）

```
  code path                          测试类型
  ─────────────────────────────      ─────────────────────────
  preflight 四态                  →  pytest subprocess（1.5）
  exec 正常/超时/报错退出码        →  pytest subprocess（1.5）
  off-switch 优先级               →  pytest（1.5）+ 冒烟（6.3）
  无 codex fallback 链全程        →  冒烟（6.2）
  守卫回落（产物缺失/0条）         →  冒烟（6.2 场景内）
  gstack 边界零触碰               →  diff/grep 核验（6.1）
  Step1 原生执行/降级标注          →  下次真实评审运行核对（Success Metric 2）
```

> 双向追溯自检：R1←{1.1-1.5, 4.1, 4.2, 4.4, 5.4, 6.2, 6.3}；R2←{3.1, 3.2}；R3←{3.3, 4.3, 5.1, 5.2, 5.3, 5.5}；R4←{3.4, 4.4}；R5←{2.1, 2.2, 2.3, 7.3}；R6←{1.3, 6.1, 6.2}——六条 Requirement 全覆盖，无幽灵任务。
