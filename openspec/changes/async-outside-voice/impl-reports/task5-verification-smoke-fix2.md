# Task 5 fix2 — 对抗镜证伪后的补证轮

> **本轮起因**：编排层曾推荐「三条未达成项作为已登记残余、打标签继续推进」。
> **对抗镜证伪了该推荐**，并给出可执行反证：注入点是 PATH 级的——`outside-voice.sh:209/221`
> 调的是**裸命令名** `codex`/`claude`，前置 shim 目录即可**只控制 runner 何时返回**，
> 而整条编排路径（SKILL host 分支 → run_in_background dispatch → 真 `timeout -k 10 900`
> → 真哨兵 envelope → 真通知驱动 collect barrier）**全真**。
> ∴ 原「模型推理时长无可控注入点」的依据**不成立**——是「没找」，不是「做不到」。
>
> 这是基准 5 的反向应用：**别去猜模型思考多久，让被测的那一层自己回答**（控 runner 返回时刻）。

## 方法（可复现）

```bash
mkdir -p /tmp/ovshim && cat > /tmp/ovshim/codex <<'SH'
#!/usr/bin/env bash
sleep "${OVSHIM_SLEEP:-420}"
out=""; while [ $# -gt 0 ]; do case "$1" in --output-last-message) out="$2"; shift 2;; *) shift;; esac; done
cat > /dev/null
printf '%s\n' "SHIM-VOICE finding 1: ..." > "${out:-/dev/stdout}"
exit 0
SH
chmod +x /tmp/ovshim/codex

PATH=/tmp/ovshim:$PATH OVSHIM_SLEEP=420 SDFLOW_VOICE_RUNNER=codex SDFLOW_VOICE_MODEL=gpt-5 \
  bash sdflow-init/assets/hack/outside-voice.sh exec --context-file <ctx> --timeout 900
```

**MUST 在主 session 跑**（B8：子代理轮次终结会回收在飞的后台任务）。

## 证据

### #3 真实评审 smoke：R1 Scenario 1 的 WHEN 首次被满足 ✅

```
DISPATCH_T0=11:44:19Z
TERMINAL_T =11:51:20Z  rc=0        ⇒ voice 实耗 421s
```

- **421s > 300s 同步窗口** ⇒ 该次 voice 在**同步分支下会被内层 300s 超时杀掉**
  （reason_code=timeout，即本 change 要消灭的 efficacy=0）；**async 让它跑到 exit 0**。
- 这是本 change 收益面的**首次端到端实证**（首轮报告的 262s < 300s，从未进入该场景）。

### #4 barrier 真处 RUNNING 等待态 ✅

主 session 在 [11:44:19, 11:51:20] 全程**让出轮次等通知**，任务存活并正常送达终态。
∴「barrier 未早退」不再是「没机会早退」，而是**真的处于 RUNNING 等待态且未早退落 timeout**。

### 哨兵 envelope 三条实证 ✅

```
$ grep -cE '^<<<SDFLOW_EXEC_EXIT>>>[0-9]+$' stdout.txt
1
```
整行锚定**恰命中 1 行**（0 行或 ≥2 行 → exec-error 的判据前提成立）；
voice 正文与哨兵行**未粘连**（`printf '\n…'` 强制前置换行生效）。

### #5 fan-out 墙钟 vs voice：重叠非叠加 ✅

| 事件 | 时刻 |
|---|---|
| voice 窗口 | 11:44:19 → 11:51:20（421s）|
| fan-out 镜（真实安全审，非空转）| 11:45:25 → 11:45:49（24s）|

fan-out **完全落在 voice 窗口内** ⇒ 串行需 445s，实际 span 421s。
**诚实边界**：本轮 fan-out（24s）远短于 voice（421s），故省下的绝对量小；
证成的是「重叠成立」这一**方向**，不是「省了很多」。

### §4.5 真 exit 124：端到端触发 ✅（此前仅合成用例覆盖）

```
T124_DISPATCH=11:44:28Z
T124_TERMINAL=11:59:28Z  rc=124        ⇒ 实耗恰 900s，撞 --timeout 天花板
$ grep -cE '^<<<SDFLOW_EXEC_EXIT>>>[0-9]+$' stdout124.txt
1                                       # envelope 整行锚定恰 1 行
$ tail -1 stdout124.txt
<<<SDFLOW_EXEC_EXIT>>>124
```

`timeout -k 10 900` 真实触发，退出码 **124** 经哨兵 envelope 结构化送达。
∴ ADR-3 的「`reason_code="timeout"` 只允许由实际观测到的 `exit 124` 产生」
**首次有真 124 作为输入端实证**，不再只是合成用例的映射断言。

## 本轮附带产出：一条真安全发现（已修）

fan-out 安全镜在等待期挖出：collect 的缓解句在禁止「把 stderr 当 findings」之后，
**紧接着放行「摘要写进锚行外正文」**——而报告是 git-tracked、随 checkpoint 永久入库，
这段 stderr **未过出境 secret_scan** ⇒ 逐字转录 = 把可能含凭证的未扫描文本永久写进版本库。

**已修**（两 SKILL marker 段内，等值门覆盖）：锚行外正文**只许写结构化字段**
（reason_code / 退出码 / stderr 行数字节数），**MUST NOT 逐字转录、摘录、复述 stderr 内容文本**；
要诊断细节去读后台任务输出文件本身（不入库）。
