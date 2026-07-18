# Task 2 双轴审返修轮 1 — spec-review async 段

范围：4 条 Important + 1 条 fold 的 Minor。文件 `sdflow-spec-review/SKILL.md` + `openspec/config.yaml`。
**未动 change 四件套**（proposal/design/tasks/specs），避免触 `ship_gate` 设计门失鲜。

---

## Important 1 — marker 分隔行内嵌对方文件专名 ⇒ Task 3 等值门必永红

**修法（择定，Task 3 MUST 遵此约定）**：marker start 分隔行改用**不指名**措辞。

- 前：`与 sdflow-code-review/SKILL.md 同名 marker 段 MUST 字节相同`
- 后：`与另一评审 SKILL 的同名 marker 段 MUST 字节相同`

**为什么这样就对**：「另一评审 SKILL」在 spec-review 里指 code-review、在 code-review 里指 spec-review，
**同一串字节在两处各自语义正确** ⇒ Task 3 整段原样搬运即满足 `check_async_branch_parity.py` 的字节相等断言，
无需在任一侧改写。

> **Task 3 约定（load-bearing）**：marker 圈内 **MUST NOT 出现任一评审 SKILL 的文件名/skill 名**。
> 需要指代对方时一律写「另一评审 SKILL」。搬运时**整段逐字节复制，不得做任何"本地化"改写**。

## Important 2 — `$VOICE_TIMEOUT` 撞「shell 变量不跨调用存活」

**修法（两个手段都上，保持全节记法自洽）**：

1. 记法改占位符：① 标题与 ③ 矩阵 async 行的 `$VOICE_TIMEOUT` → `<VOICE_TIMEOUT>`（与同节 `<T>` / `<f>` / `<run-id>` 占位符记法一致）。
2. ③ 矩阵首行补 🔴 警句：内层秒数一律代入十进制字面值，MUST NOT 写 `$VOICE_TIMEOUT` 之类 shell 变量，
   并显式挂钩同类既有条款（④ 的 `$HELPER`、context 构造节的 run-id），点明 `<VOICE_TIMEOUT>` 是占位符、指 ① 解析出的那个数。

该补充落在 marker 圈**内**（站点无关，Task 3 一并搬运）。

## Important 3 — config.yaml 注释复述校验规则 = 第二份 prose 源

**修法**：`openspec/config.yaml` 的 outside-voice 段注释删去数值与规则复述（1≤v≤3600 / 回落 900 / 不 fail-closed / 各分支恒 300），
只留一句指针 + 示例键：

```
# outside-voice（可选覆盖段）——async 分支内层 --timeout 天花板，单位秒。
# 缺省请勿填。取值域 / 校验 / 回落规则的单一源 = sdflow-spec-review/SKILL.md
# 「outside-voice helper 调用协议」节 ①（此处不复述数值与规则，避免第二份 prose 源）。
# outside-voice:
#   async-timeout-seconds: 900
```

⇒ Task 3 搬运后该常数仍只有**两份** prose 副本，且**两份全在等值门覆盖内**。

## Important 4 — 第三步章节本体无 collect/barrier 触发点

**修法**：第三步首条新增（在「合并去重」**之前**，marker 圈**外**，不影响等值门）：

> 🔴 **进合并去重前 MUST 先完成 outside-voice collect barrier**（见协议节 ⑥⑧）：按 ⑧ 的站点↔任务标识表**逐站点**取，
> 每个**实际 dispatch 过的**站点其结果 MUST 已在手、或已按 ⑦ 降级完毕（仍 RUNNING 的站点 MUST 让出轮次等通知，
> MUST NOT 早退落 `timeout`），方可进下面的合并去重。

按章节顺序执行者现在在 Step3 开头就撞到触发点，不再依赖翻到 300+ 行外的协议节。

## Minor（fold）— 两处 voice 调用点缺「派出即返回」

**修法**：两处各加半句，点明 tasks §1.1「context 就绪即派」的时序意图 +「派出即返回、继续本步余下工作」+ 结果归属 Step3 barrier：

- Step1 第 5 条（site="design-voice"）：「context 就绪即派；async 分支下 dispatch 调用派出即返回，
  MUST 立刻继续本步余下工作（checkpoint、进 Step2 fan-out），结果在 Step3 barrier 处 collect」
- Step2 HR-TG 判定条（site="hr-tg"）：同款，余下工作举例为「能力探针、fan-out 各镜」

---

## 验证证据

**marker 圈内站点无关性自核**（Important 1 的失效类，机械扫一遍）：抽出 marker 之间 50 行，
grep 站点相关词表（`spec-review`/`code-review`/`design-voice`/`hr-tg`/`autoplan`/`领域镜`/`对抗镜`/`接地镜`/`gstack`/`Step2`/`第二步`/`$VOICE_TIMEOUT`/`reuse`/`复用`/`declared`）。
4 处命中，逐条判定**全部良性**：

| 行 | 命中词 | 判定 |
|---|---|---|
| start 分隔行 | `reuse` / `declared` | 是**排除条款**本身（"reuse-guard 门控 / declared-sites 计算 MUST 留在本 marker 之外"），站点无关 |
| ③ 新增警句 | `$VOICE_TIMEOUT` | 正是**禁止**该写法的条文，站点无关 |
| ⑧ 表下注 | `复用` | 泛指"门控/复用态"，无任何站点专名 |

⇒ marker 圈内已无任一评审 SKILL 的专名，可整段搬运。

**测试**：

```
$ /usr/bin/python3 -m pytest -q
1619 passed, 2 skipped in 71.28s

$ /usr/bin/python3 hack/sync_principles.py --check
[sync_principles] ✅ 20 个投放面全部与真相源一致   (exit 0)
```
