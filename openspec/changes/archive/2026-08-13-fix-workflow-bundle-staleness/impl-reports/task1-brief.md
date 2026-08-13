### Task 1: bundle 核心规则修正（spec-review / quality-layering / checklists / trigger-catalog）

**Blocked-by:** none
**R-ID:** D1, D2, D3, D6, D9

修正 bundle 核心规则文件中的两处正面矛盾（P3c / G2）、退役机制残留（subagent-dev / writing-plans / 官方 code-review / `/clear +` 措辞）、`/review` 消费方统一改写（8 处）、号段去上界，具体位点：

- `spec-review.md`：:72 AskUserQuestion→决策登记区；:29 删「`/clear` 后重审」；:91 brainstorming→生成期自检；:92 去 BASE 号段上界
- `reference/README.md`：:18 quality-layering 描述改 P3c 口径；:17 删 Token_Saving 行；:6-8 部署观改 canonical 口径
- `reference/quality-layering.md`：:25 `/clear +` 措辞改独立编排器口径；:42 表行改 sdflow-code-review；:84 删 subagent-dev；:38 `CR-01~09` 去上界；**保留 :14 出处标注**
- `spec-checklists/spec-quality-base.md`：:37 writing-plans→出 ticket；`spec-checklists/README.md`：:62 `rules/` 错路径→`../`、:64 R 落点现行化
- `/review` 消费方 8 处统一改写：`code-checklists/README.md`:3,13,28,53,68 + `code-review-base.md`:3 + `domains/llm.md`:5 + `trigger-catalog.md`:108

- [ ] 全部位点按 D1/D2/D3/D6/D9 改写完毕，无遗漏
- [ ] 改后 `quality-layering.md:14` 出处标注仍在
- [ ] 改后 `spec-quality-base.md:7` 来源行仍在

