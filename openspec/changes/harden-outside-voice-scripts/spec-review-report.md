# spec-review-report — harden-outside-voice-scripts

> 评审模式：原生 autoplan（广审）+ 并行多镜（接地 + 对抗 ×2）+ 跨模型 outside-voice（design-voice）
> host=claude | 子代理=available | 所有镜前台/后台完成，无降级

<!-- sdflow:step1-broad-review v1 mode="native" -->

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="none" declared="" evidence="" -->

---

## 合并 findings（7 个独立 voice 合池去重，按严重度排序）

### 采纳

#### F1 · 致命 — `--timeout 00/000` 绕过零值拒绝 [spec-review-amendment]

**命中镜**：broad(autoplan-CEO-Codex, Eng-Claude, Eng-Codex) + adversarial(镜1-F1, 镜2-F1) + outside-voice(design-voice-F1) = **6/7 voice 收敛**

D1 设计用 shell `case` 的 `0)` 分支拒绝 timeout=0。但 bash `case` 的 `0)` 只精确匹配字面字符串 `"0"`，不匹配 `"00"` / `"000"`。前置校验 `''|*[!0-9]*` 只排除非数字，`"00"` 是纯数字串能通过，原样传给 GNU timeout → DURATION=0 = 禁用超时 = 进程挂死。

**实测验证**（对抗镜 1/2 均已本机 gtimeout 复现）：`gtimeout 00 sleep 2` 完整跑满 2s（超时被禁用），行为与 `gtimeout 0` 完全一致。

**裁决**：**采纳。** design.md D1 MUST 修订——改字符串匹配为数值判等。推荐：通过纯数字校验后加 `[ "$((10#$2))" -eq 0 ] && usage`（`10#` 强制十进制，防前导零八进制解析）。decision-memo D1、承重约束 C1 相应更新。

#### F2 · 高 — 出境截断 wc -c 失败时 fail-open [spec-review-amendment]

**命中镜**：broad(autoplan-CEO-Codex, Eng-Claude, Eng-Codex) + adversarial(镜1-F3, 镜2-F2) = **5/7 voice 收敛**

D2 设计代码 `${ov_outsize:-0}` 在 `wc -c` 失败时默认为 0 → `0 -gt LIMIT` 为假 → 走 `else cat` 全量输出。与入境侧（outside-voice.sh:443-449）的 fail-loud 处理直接相悖。

**裁决**：**采纳。** design.md D2 MUST 修订——镜像入境侧，对 `ov_outsize` 做格式校验：空/非数字时走安全默认（强制截断 + stderr 哨兵 `OV_OUTPUT_SIZE_CHECK_FAILED=1`），而非静默放行。

#### F3 · 高 — 新代码路径缺专门测试 [spec-review-amendment]

**命中镜**：broad(autoplan-CEO-Claude, CEO-Codex, Eng-Claude, Eng-Codex) + adversarial(镜1-F4) = **5/7 voice 收敛**

tasks.md 只有"3.1 回归验证：既有测试全绿"。D1 新增 case 分支、D2 新增条件块——既有测试无法覆盖新行为。

**裁决**：**采纳。** tasks.md MUST 补测试任务：
- `--timeout 0` / `--timeout 00` / `--timeout 000` 均 exit 2
- 保留非零前导零值（如 `--timeout 01`）兼容性
- 出境 stdout ≥ OV_MAX_CONTEXT_BYTES 时截断 + stderr 告警
- 出境 stdout = OV_MAX_CONTEXT_BYTES 边界条件

#### F4 · 中 — "模型输出大概率 ASCII" 前提不准确 [spec-review-amendment]

**命中镜**：broad(autoplan-CEO-Claude, Eng-Claude, Eng-Codex) + adversarial(镜1-F2, 镜2-F3) = **5/7 voice 收敛**

本项目 CLAUDE.md 强制中文回复，评审 findings 惯例中文。`head -c` 在 CJK 边界劈开概率 ≈ 2/3。对抗镜 1 已对本 change 自身 context 文件实测截断出现非法 UTF-8。

**裁决**：**采纳（修正前提，不强制复用回扫）。** decision-memo 的"接受的边角"措辞修正：概率非"低"而是"中等"，但影响确实低——截断只影响 200KB 边界处末尾 1-3 字节，下游 `errors="replace"` 不会崩溃。不强制复用 `utf8_head_trim`（出境 stdout 协议不同，且影响范围极小——④简化合理）。

#### F5 · 低 — T178 CI 覆盖声称不准 [spec-review-amendment]

**命中镜**：broad(autoplan-CEO-Codex) = **1/7 voice（broad 独家）**

proposal Non-Goals 写"macOS CI 泳道已覆盖"——但 `test_outside_voice_utf8.py:795` 有 `@pytest.mark.skipif(os.environ.get("CI") == "true")`，CI 上不跑。

**裁决**：**采纳。** 修正 proposal 措辞为"本地 macOS 开发机覆盖"。

#### F6 · 低 — T230 scope 定义 [spec-review-amendment]

**命中镜**：broad(autoplan-CEO-Codex) = **1/7 voice（broad 独家）**

D2 截断发生在 runner 已写完 `last-message.md` 之后，只 cap stdout 通道，对磁盘/内存无影响。

**裁决**：**采纳。** design.md 补一句澄清：D2 scope 是"bounded published evidence"非"bounded resource usage"。

### 需拍板

#### Q1 · D3 (fake-timeout) 保留还是 WONTDO？

**命中镜**：broad(autoplan-CEO-Claude, Eng-Claude, Eng-Codex) + outside-voice(design-voice-F2) = **4/7 voice**

生产解析器只允许纯数字 → 测试桩永远不会收到浮点数。且 `printf "%d"` 截断（非四舍五入）：`sec=0.05 → lim=0` → 看门狗立即杀进程。autoplan-CEO-Claude 倾向 WONTDO。

**选项**：
- **(A) 保留 + 加测试 + 改 ceil**：保留 D3 但改 `printf "%d"` 为 `printf "%.0f"`（四舍五入），加 fake-timeout 浮点数测试
- **(B) WONTDO**：删除 D3，T174 从 tasks 中移除，标 WONTDO（与 T173/T178 同处理）
- **推荐**：(B)——当前不可达路径，改一行 awk 的同时引入了截断语义错误（0.05→0），反而不如不改。三镜后果：系统镜（无影响，不可达路径）·用户镜（无影响）·开发循环镜（少一个改动点 = 少一个审查面）。主次判定：开发循环镜胜。

### 已裁掉

| # | 原始发现 | 来源 | 裁掉理由 |
|---|---------|------|---------|
| X1 | T227 deferred without verification deadline | autoplan-CEO-Claude | 超出本 change scope（不加宽，③） |
| X2 | OV_MAX_CONTEXT_BYTES 前导零八进制问题 | autoplan-Eng-Claude | 既有 bug，非本 change 引入（不加宽，③） |
| X3 | --timeout 无上界（999999 被接受） | autoplan-Eng-Claude | 外层超时兜底，低影响（④简化） |
| X4 | D3 awk 在 Windows Git Bash 依赖 | adversarial-镜1-F5 | 低概率 + 已有先例（resolve-models.sh 用 awk 无报红记录） |

---

## 决策登记区

| # | 类型 | 内容 |
|---|------|------|
| [自动决策] D1 | autoplan HOLD SCOPE | Bug fix → HOLD SCOPE，无异议 |
| [自动决策] D2 | 采纳 F1（00 绕过） | 安全面核心修复有漏洞，四声收敛 |
| [自动决策] D3 | 采纳 F2（wc fail-open） | 与入境侧纪律不对称，五声收敛 |
| [自动决策] D4 | 采纳 F3（加测试） | 新代码路径无测试，五声收敛 |
| [自动决策] D5 | 采纳 F4（修正 ASCII 前提） | 保留为接受的边角但修正理由 |
| [需拍板] Q1 | D3 保留 vs WONTDO | 推荐 WONTDO，见上方分析 |

---

## outside-voice

<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="codex" reason_code="ok" findings="2" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->

design-voice（跨模型，codex runner）返回 2 条 findings：
1. `--timeout 00/000` 绕过（与 F1 合并）
2. fake-timeout awk 截断 `sec=0.05 → lim=0`（与 Q1 合并）

---

## 收敛口

本报告采纳 6 条（F1-F6），需拍板 1 条（Q1），已裁掉 4 条（X1-X4）。

**建议进设计 HARD-GATE**：F1-F4 的四件套修订完成后即可拍板。F1（致命）是阻断项，其余为改善项。

---

## lens-metric 度量锚

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="5" 采纳="4" 裁掉="1" defer="0" 独立="0" sev="致1/高2/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="10" 采纳="6" 裁掉="3" defer="1" 独立="2" sev="致1/高2/中1/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="2" 采纳="1" 裁掉="0" defer="1" 独立="0" sev="致1/高0/中0/低0" -->

## 拍板记录区

（设计门拍板后由主 session 填写）
