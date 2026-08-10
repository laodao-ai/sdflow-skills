### Task 4: retro token 列渲染

**Blocked-by:** 3
**R-ID:** R-WR2

在 `sdflow-retro/scripts/retro_report.py` 新增 token-log.jsonl 读取与 per-change token 列渲染。

行为描述：
- 读 token-log.jsonl：先扫全部 change 目录（活动 + 归档）的 token-log.jsonl，按 `session` 全局分组
- Δ 归属口径：跨 change 时后一文件首行对前一文件末行差分、Δ 落行所在 change，消除跨 change 双计数；仅全局首行全额计入；anchor=false 行不入计数
- 逐行防御解析：无法解析的行按 anchor=false 等价处理，不中断该 change 及其余 change 的报告生成
- per-change 表 tokens 列渲染：`out 12.3k / in 4.5k / cc 89k / cr 1.2M` 四计数紧凑串（MUST NOT 合成总分）；无锚显「—」
- 列旁恒加脚注「数值为各会话累计口径聚合，tickets 管线下多为独立短会话的首行全额之和，非严格阶段增量」
- 测试（`sdflow-retro/scripts/tests/`）：合成 token-log 用例（多 session/跨 change 同 session 不双计数/降级行/缺文件/含损坏行不崩）+ 全仓再生冒烟（存量 change 全「—」不崩）

- [ ] token-log 读取与 Δ 归属计算（全局 session 分组 + 差分）
- [ ] per-change tokens 列渲染（四计数紧凑串 + 脚注）
- [ ] 测试：合成 jsonl 单元 + 全仓再生冒烟

