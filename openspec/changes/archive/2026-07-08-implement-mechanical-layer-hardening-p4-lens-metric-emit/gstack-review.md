<!-- sdflow:step1-broad-review v1 mode="simulated" -->

# 广审记录（Step1）· lens-metric-emit

> **模拟广审（降级模式）**〔mode="simulated"〕：autoplan skill 虽可用（preflight ready、codex ready），但其 1852 行流程与 gstack **plan file** 强耦合（自带 gstack 会话/遥测/learnings/plan 检测），对 openspec change 目录原生跑存在真实阻抗失配。故按 sdflow-spec-review §3 降级：以 **fresh-context 子代理套 CEO/design/eng/DX 四视角**广审 + **真实 codex design-voice**（autoplan 双声中最高价值的独立第二声音，非模拟）。**未伪装原生**。
>
> 侧信道佐证：codex design-voice 经 `~/.sdflow/hack/outside-voice.sh exec` 真实调用（exit 0，`OV_TRUNCATED=false`），非模拟臆造。

## 广审 findings（CEO/design/eng/DX 四视角，已接地读码）

| ID | 视角 | 问题 | 置信 | 严重 |
|----|------|------|------|------|
| F1 | design | `MIN_LENS_ROWS`(anchor_lint.py:135)是**第二份硬编码、不在契约机读块**——emitter 再硬编码一份=第二拷贝，反噬本 change「单一源根治」主张（ADR-2 为折叠表消灭的漂移源、对 MIN_LENS_ROWS 又重犯） | 高 | 高 |
| F2 | eng | roster 只到 lens 粒度，无法表达零-finding 的 outside-voice 多 site，丢 SR-D 区分 | 高 | 高 |
| F3 | design | 「emitter 输出过 anchor_lint 退 0」过度声明——check_existence 强制三类非-lens 锚(outside-voice/hr-tg/step1-broad-review)存在，emitter 不产 | 高 | 中 |
| F4 | eng | 折叠恒等规则未钉死，与「未知镜名 fail-closed」冲突（省略恒等项→canonical 输入被误拒） | 高 | 中 |
| F5 | eng | `--layer` vs per-finding `layer` 双写口径悬（甩给 task 3.3），冗余邀请漂移 | 中 | 中 |
| F6 | eng | emitter 若自读 config metrics 须复刻 anchor_lint 四态 fail-closed，task 3.4 只测「关」漏「坏块」（dogfood 分治盲区） | 中 | 中 |
| F7 | design | verdict/sev 输入枚举未纳入契约机读单一源（脚本内第三份硬编码倾向） | 中 | 低 |
| F8 | DX | 输入 JSON schema 无单一权威定义、键名中英混杂（命中镜集/裁决 vs lenses/verdict），模型每轮现拼易 fail-closed | 中 | 低 |
| F9 | CEO | 值得做、scope 基本正确；但价值集中在残余边界之外，SKILL 侧新增 JSON 构造+roster+fold 机读块是实打实复杂度增量，建议成功指标补「一次 dogfood 端到端实跑」 | 中 | 低 |

## 广审自动决策（供设计门一次拍板）
- **F1+F2（高/高）** → 默认接受、阻断合并：设计层有洞、会让 ADR-4/SR-D 核心保证在实现期破。
- **F3+F4（高/中）** → 默认接受、实现前修（改测试/措辞即可）。
- **F5/F6（中/中）** → 默认接受为「实现前须先在 design 定 ADR」。
- **F7/F8/F9（中或低/低）** → 默认记录、可与实现并行。

> 广审 findings 已并入主报告 `spec-review-report.md` 合并池（去重后见 C1/C5/C6/C8/C15/C16/C17/C19），此处为 Step1 原始留痕。
