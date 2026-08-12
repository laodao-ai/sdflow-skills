### Task 3: sdflow-spec-review 报告模版三问小节 + 锚行

**Blocked-by:** 1
**R-ID:** GQ

在 `sdflow-spec-review/SKILL.md` Step4 报告条款中：
- 决策登记区顶部新增「拍板三问」小节模版（每问 = 问题 + 评审侧自答指回证据 + 勾选位）
- 紧邻三问小节放锚行 `<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->`
- SKILL 自检步对该锚报错的提示文案须含 fix 指引（problem/cause/fix 三件套，fix 指回报告模版所在小节）

grep bundle 内 spec-review 规则文件（经 `~/.sdflow/hack/resolve-workflow.sh` 解析取得规则根）是否另有报告结构描述，有则同步（design scope-check 表逐行核对）。

- [ ] 三问小节模版加入 Step4 报告条款（决策登记区顶部）
- [ ] 锚行加入（紧邻三问小节）
- [ ] 自检步报错文案含 problem/cause/fix 指引
- [ ] bundle 内规则文件报告结构描述已同步（或确认无需同步）

