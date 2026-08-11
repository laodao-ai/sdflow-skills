### Task 2: 合法组合扩展 + Roster 条件化 + 处置系统

**Blocked-by:** none
**R-ID:** R-roster, R-裁决, R-处置

实现 DD2 合法组合矩阵扩展 + DD1 处置记录 + DD6 roster 条件化 + retro_report.py 处置注记——四件串联成一条「让镜可以条件化跳过且跳过可审计」的垂直切片。

**A. 合法组合矩阵扩展（DD2/设计门 Q1）**：
- lens-metric contract 升版本，新增合法组合「普通镜行 `runner="none"` ∧ `findings=0`」
- emitter 非-outside-voice 分支接受该组合（原强制 `runner==host` 加旁路）
- anchor_lint 普通镜行校验同步接受该组合
- emitter 输入侧兼容（findings JSON 含置信字段时不报错）

**B. 处置记录（DD1）**：
- 创建处置数据文件（yaml，DD1 schema: `{layer, lens, host, runner, site, disposition, condition, date, rationale}`）
- 填入 DD6 拍板后的 13 面镜处置（1 降采样 + 11 保留 + 1 不适用，grounding 恒跑）

**C. SKILL roster 段条件化（DD6）**：
- 两评审 SKILL roster 段：降采样镜（code-review history）加派发条件行，给出阈值具体取值与判定命令
- 条件跳过轮落锚 `runner="none" findings="0"` + 报告一行说明

**D. retro_report.py 处置注记（DD1 消费）**：
- 读处置数据文件，命中镜行内追加处置注记
- 错误语义分治：缺失=零注记 / 坏yaml=fail-loud / 未命中键=告警不阻断
- 解析走 yq（MUST NOT `import yaml`）

- [ ] contract 含新合法组合且版本号已递增
- [ ] emitter 接受 `runner="none" ∧ findings=0` 普通镜行不报错
- [ ] anchor_lint 对该组合判合法
- [ ] emitter 对含置信字段的 findings JSON 兼容
- [ ] 处置数据文件含 13 面镜完整记录且 schema 合规
- [ ] 降采样镜条件阈值为具体数值与命令，非定性词
- [ ] retro_report.py 对命中镜行追加处置注记
- [ ] retro_report.py 对缺失/坏yaml/未命中键三态各正确处置
- [ ] pytest 覆盖 retro_report.py 处置注记四态

