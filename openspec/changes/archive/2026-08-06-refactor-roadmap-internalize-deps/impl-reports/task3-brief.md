### Task 3: matt 套件移除与治理面收口

**Blocked-by:** none
**R-ID:** none（治理类，无对应 spec 行为）

`openspec/matt/` 套件及其在项目指令文件中的三个托管区块从本仓消失；本次决策与术语变更在治理面
（ADR / CONTEXT 词条 / INDEX 摘要 / 外部依赖清单 / 活文档 / issue 池）留下一致的记录。

行为上可观察的结果：新 session 读 `CLAUDE.md` / `AGENTS.md` 时不再看到 Issue tracker / Triage
labels / Domain docs 三节，也不再被指向 `openspec/matt/`；查 `openspec/CONTEXT.md` 能查到「历史存档」
与「商业化信号」词条；`docs/external-dependencies.md` 不再声明对 wayfinder / grilling /
domain-modeling 的依赖。

依据：`tasks.md` §3（3.1–3.2）+ §5（5.1–5.7）。

🔴 ADR 的论证 **MUST 按订正后的 D2 写**（历史遗留死配置、独立可删、与本 change 无因果，同批做是
fold 判据），**MUST NOT** 沿用「因本次改动才孤立」的旧因果〔SR-1 / SR-33〕；权衡要写两条（内化
分界线 + 能力承接边界）。
🔴 T134 关闭用 **`WONTDO` + `--reason`**——`OBSOLETE` 不是合法状态码；且须用**本仓**
`sdflow-issues/scripts/`，勿用全局 symlink 旧版（旧 writer 撞号）。

- [ ] `openspec/matt/` 整目录（4 文件）已删除（3.1）
- [ ] `CLAUDE.md` 与 `AGENTS.md` 的 matt 三区块已删、roadmaps 目录描述行去 footage 措辞，两文件同步（3.2）
- [ ] 新增 ADR `0037-`（4 位零填充 + kebab-case，小节结构从现有 ADR 归纳），含两条权衡，matt 论证按订正后 D2（5.1）
- [ ] `openspec/CONTEXT.md` 三处词条到位：历史存档（含「结晶」→「生成」）/ 新增商业化信号 / ticket 词条改历史存档语境（5.2）
- [ ] T134 已关 `WONTDO` 且带 `--reason`，用本仓脚本执行（5.3）
- [ ] `docs/external-dependencies.md` 删 §5 且同步 §8 依赖图，gstack review 节保留（5.4）
- [ ] `openspec/INDEX.md:52` roadmap-planning 摘要行整句重写为新结构（三态路由 / 历史存档 / checklist 四项）（5.5）
- [ ] `docs/sdflow-fable5/02-module-reference.md` §4.6 已按新结构更新（5.6）
- [ ] `docs/drafts/roadmap-refactor-handoff.md` 已删除（5.7）

