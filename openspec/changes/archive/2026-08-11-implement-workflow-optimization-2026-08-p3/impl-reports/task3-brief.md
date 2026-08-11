### Task 3: SKILL 编排层 + 消费端

**Blocked-by:** 2
**R-ID:** R4, R5, R6

实现 SKILL.md 编排正文（模型驱动分诊报告成文）与 sdflow-upgrade 提醒段：

1. SKILL.md 编排正文：collect → 模型读 facts 写报告（`reports/<UTC时间戳>.md` 不覆盖既有报告；按源分节 + 三分诊 + 每源采集状态行 + degraded 节「原因 + 上游 URL」不罢工 + 格式漂移分支指本地文件与键路径 + 吸收候选附预生成 recorder add 命令含 source_change）→ advance（报告+facts 双参数）→ 呈报人。
2. 首轮 seed 条款：报告 SHALL 含 T245/T246/T267 分诊条目；T245/T246 注明共享「解除 D8 mid 档钉死」前置人工决定。
3. 入池衔接条款：人拍板「吸」→ recorder add 显式 source_change（报告内预生成命令模板）；watch MUST NOT 直接改池；frontmatter description 触发词收敛 + 声明单仓专用。
4. `sdflow-upgrade/SKILL.md` 追加第 5 步提醒段：读 `~/.skills/sdflow-skills/openspec/upstream/anchors.yaml` 的 `last_run` + 阈值比较，缺失/不可解析静默跳过，零网络。
5. README「Skills 列表」加 `sdflow-upstream-watch` 行（注明单仓专用）。

- [ ] SKILL.md 编排正文完整（collect→报告→advance→呈报全路径）
- [ ] 报告模板含三分诊、每源状态行、degraded 不罢工展示、格式漂移指本地路径
- [ ] 吸收候选条目附预生成 recorder add 命令（含 source_change）
- [ ] 首轮 seed 含 T245/T246/T267 条目
- [ ] frontmatter description 触发词不与 sdflow-upgrade/sdflow-maintain 冲突、声明单仓专用
- [ ] sdflow-upgrade 第 5 步提醒段：超阈值提醒/缺失静默跳过/未超阈值不提醒
- [ ] README Skills 列表已更新

