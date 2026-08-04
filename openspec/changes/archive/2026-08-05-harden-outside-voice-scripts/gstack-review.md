<!-- sdflow:step1-broad-review v1 mode="native" -->

# autoplan 广审报告 — harden-outside-voice-scripts

> 原生执行 autoplan（CEO + Eng），auto-decide 模式（HOLD SCOPE）。
> 佐证：autoplan 经 Skill 机制原生调用，四声双模型（Claude subagent × 2 + Codex × 2）均前台阻塞完成。

## CEO DUAL VOICES — CONSENSUS TABLE

| 维度 | Claude | Codex | 共识 |
|------|--------|-------|------|
| 前提有效？ | CONFIRMED | CONFIRMED（但修复不完整） | CONFIRMED |
| 正确的问题？ | CONFIRMED | CONFIRMED | CONFIRMED |
| 范围校准？ | CONFIRMED | DISAGREE（T230 scope 标错） | DISAGREE |
| 替代方案充分？ | CONFIRMED | DISAGREE（D2 fail-open） | DISAGREE |
| 测试计划充分？ | DISAGREE | DISAGREE | **CONFIRMED DISAGREE** |
| Non-Goals 准确？ | CONFIRMED | DISAGREE（T178 CI skip） | DISAGREE |

## ENG DUAL VOICES — CONSENSUS TABLE

| 维度 | Claude | Codex | 共识 |
|------|--------|-------|------|
| --timeout 00 绕过 | CRITICAL | HIGH | **CONFIRMED** |
| wc -c 失败 fail-open | HIGH | HIGH | **CONFIRMED** |
| UTF-8 截断风险 | MEDIUM | MEDIUM | **CONFIRMED** |
| 缺新路径测试 | HIGH | HIGH | **CONFIRMED** |
| D3 无可达路径 | LOW | MEDIUM | CONFIRMED |
| timeout 无上界 | LOW | — | N/A |

## Findings（按严重度排序）

### [gstack-amendment] F1 · CRITICAL — `--timeout 00/000` 绕过零值拒绝

**四声收敛（CEO-Codex + Eng-Claude + Eng-Codex）**

D1 设计用 shell `case` 的 `0)` 分支拒绝 timeout=0。但 `0)` 只匹配字面字符串 `"0"`，**不匹配 `"00"` / `"000"`**。GNU timeout 对 `DURATION=00` 的处理等同于 `0`：禁用超时。

**修法**：在通过纯数字校验（`*[!0-9]*`）之后，用算术比较 `[ "$2" -eq 0 ]`——正确捕获所有前导零变体。
**design.md D1 MUST 修订**。

### [gstack-amendment] F2 · HIGH — 出境截断 wc -c 失败时 fail-open

**四声收敛（CEO-Codex + Eng-Claude + Eng-Codex）**

D2 设计代码 `${ov_outsize:-0}` 在 `wc -c` 失败时默认为 0，`-gt` 比较为假 → 走 `cat` 分支全量输出。
与入境侧（line 442-448）的 fail-loud 处理不对称。

**修法**：仿入境侧，对 `ov_outsize` 做格式校验（空/非数字时 warn + 继续 cat，因丢弃已付费结果不合理），但 MUST emit stderr 哨兵 `OV_OUTPUT_SIZE_UNAVAILABLE=1`。
**design.md D2 MUST 修订**。

### [gstack-amendment] F3 · HIGH — 新代码路径缺专门测试

**四声收敛（全部 4 个独立 voice）**

tasks.md 只有 "3.1 回归验证：既有测试全绿"。但 D1 加了新 case 分支、D2 加了新条件块——既有测试无法覆盖新行为。

**应增加的测试**：
- `--timeout 0` / `--timeout 00` / `--timeout 000` 均 exit 2
- 保留非零前导零值（如 `--timeout 01`）兼容性
- 出境 stdout ≥ OV_MAX_CONTEXT_BYTES 时截断 + stderr 告警 `OV_OUTPUT_TRUNCATED=1`
- 出境 stdout = OV_MAX_CONTEXT_BYTES 时完整输出（边界条件）

**tasks.md MUST 修订**。

### F4 · MEDIUM — UTF-8 截断前提不准确

**三声收敛（CEO-Claude + Eng-Claude + Eng-Codex）**

decision-memo 说"模型输出大概率 ASCII"，但项目评审产出包含大量中文。`head -c` 在 CJK 字符边界劈开的概率 ≈ 2/3。

**修法**（两个层级，选一）：
- (a) 复用 `utf8_head_trim` 做 UTF-8 安全截断（design.md 已说明 stdout 协议不同、复用代价不匹配，但 Codex 反驳"不是不能复用文件级 UTF-8 边界计算的理由"）
- (b) 修正 decision-memo 的前提描述：概率非"低"而是"中等"，影响确实低（只影响末尾几个字符）——保留为接受的边角但理由要准确

**建议**：选 (b)——影响范围极小（200KB 截断点仅末尾 1-3 字节），且出境不需要保证 UTF-8 完整性（下游做文本匹配非字节验证）。design.md 和 decision-memo 修正前提描述即可。

### F5 · MEDIUM — T230 的 scope 定义

**Codex CEO 独家**

Codex 指出 D2 的截断发生在 runner 已经写完 `last-message.md` 之后，对磁盘/内存消耗无影响——只 cap 后续 stdout 通道。应明确 D2 的 scope 是"bounded published evidence"而非"bounded resource usage"。

**建议**：design.md 补一句澄清即可（低代价）。

### F6 · LOW — T174 (fake-timeout) 修法没有可达路径测试

**三声收敛（CEO-Claude + Eng-Claude + Eng-Codex）**

生产解析器只允许纯数字 → 测试桩永远不会收到浮点数。且 `printf "%d"` 会向零截断（`0.05` → `lim=0`）。

**建议**：若保留 D3，应加一个直接驱动 fake-timeout 的浮点数测试。或者 WONTDO 此项（CEO-Claude 倾向 WONTDO）。

### F7 · LOW — T178 CI 覆盖声称需修正

**Codex CEO 独家**

proposal Non-Goals 写"macOS CI 泳道已覆盖 hdiutil ramdisk 测试"——但该测试有 `@pytest.mark.skipif(os.environ.get("CI") == "true")`，CI 上并不跑。是本地 macOS 覆盖，非 CI 安全网。

**建议**：修正 proposal Non-Goals 措辞为"本地 macOS 覆盖"。

## 自动决策

| # | 决策 | 分类 | 原则 | 理由 |
|---|------|------|------|------|
| D1 | HOLD SCOPE 模式 | Mechanical | P3 (pragmatic) | Bug fix → HOLD SCOPE |
| D2 | 采纳 F1（00 绕过修复） | Mechanical | P1 (completeness) | 安全面核心修复有漏洞 |
| D3 | 采纳 F3（加测试） | Mechanical | P1 (completeness) | 新代码路径 MUST 有测试 |
| D4 | F4 选方案 (b)（修正前提） | Taste → 需拍板 | P5 (explicit) | 两个修法都合理 |
| D5 | F6 保留 D3 + 加测试 | Taste → 需拍板 | P3 (pragmatic) | WONTDO 也合理 |
