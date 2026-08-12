### Task 4: 考古层审计清理（15 个 SKILL.md）

**Blocked-by:** 2,3
**R-ID:** T275

审计通道建立：`{change_dir}/audit/skill-doc1-audit.md` 骨架（15 节，每节删/迁/留三计数 + 边界个案注记格式；名单以 `find . -maxdepth 2 -name SKILL.md` 实测为准）。

7 个超 500 行 SKILL 重点清理（implement 821 / code-review 771 / roadmap 715 / spec-review 593 / done 567 / architecture 562 / spec 528 行）：逐文件过 DOC-1 删除测试，删或迁 `<skill>/references/evolution-notes.md`（design Dd 统一名 + 正文末一行指针；sdflow-spec 已有该文件则追加）；`sdflow:principles` 托管块不触碰。

其余 8 个 SKILL 审计（≤500 行者）：过删除测试，预期改动量小，审计结论同样落 audit 文件（含「零改动」结论也留档）。

每文件清理后即跑该 skill 对应 `tests/` + `hack/tests/`（memo C2 爆破面）+ `python3 hack/sync_principles.py --check`，红了当场修断言或回滚该处删改。

- [ ] `audit/skill-doc1-audit.md` 骨架建立（15 节）
- [ ] 7 个超 500 行 SKILL 逐文件审计清理 + 每文件测试绿
- [ ] 8 个 ≤500 行 SKILL 审计（含零改动留档）
- [ ] `sync_principles.py --check` 全仓通过
- [ ] 全仓 pytest 无回归

