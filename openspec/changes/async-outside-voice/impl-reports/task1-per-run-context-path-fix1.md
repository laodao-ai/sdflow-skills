# Task 1 返修轮 1 — per-run context 路径双轴审 2 条 Important

**范围**：`sdflow-spec-review/SKILL.md` + `sdflow-code-review/SKILL.md` 的 context 构造块（Task 1 新增行）。
按 ADR-5，该块**留在 `sdflow:async-branch` marker 外**，本次未加 marker。
未动 change 四件套（`proposal.md:27` 残留 = T157，archive 阶段处理）。

## Important 1 — run-id 秒级粒度不足以闭「并行评审互踩」

**问题**：run-id 原为 `date -u +%Y%m%dT%H%M%SZ`，1 秒分辨率、无 PID/随机位。目标态下脚本/编排
触发的两次 dispatch 落在同一秒完全可达 ⇒ 两轮共写同一 run 目录，per-run **不可变**承诺当场破。

**修法**（两层，缺一不可）：

1. **run-id 加唯一位** — `$(date -u +%Y%m%dT%H%M%SZ)-$$-$RANDOM`（时间戳 + PID + 随机位）。
2. **让 OS 自己判唯一性**（基准⑤：无界不手搓，让工具自己回答）— run 目录用 **`mkdir` 不带 `-p`** 建，
   已存在即非零退出即换新 id 重试：

   ```
   mkdir -p {change_dir}/.outside-voice
   until RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$-$RANDOM"; mkdir "{change_dir}/.outside-voice/$RUN_ID" 2>/dev/null; do :; done
   ```

   父目录 `.outside-voice/` 用 `mkdir -p`（须存在，且 G5 要求 context 父目录仍在该层级下，
   保住 `.gitignore:19` 的 `**/.outside-voice/` 递归覆盖）；**唯独 run 目录那一层 MUST NOT 加 `-p`**
   —— `-p` 会把「已存在」变成静默成功，而「已存在必须失败」正是此处承载的语义。

   指令中明确写出这一点，防后续维护者"顺手补 -p"。

**效果**：「run-id 是否真每轮换新」由**纯诚实边界**降级为**由 OS 判定的机械事实**。

## Important 2 — manifest 行格式含裸 `\t`，指令不可机械落地

**问题**：原文写 ``格式 `<site>\t<task_id>\t<UTC ISO8601>` ``。这是读给模型的 Markdown 指令，
模型产出字面 `\t` 还是真制表符**不确定**；而该文件被声明为「是否真派发某站点」的唯一权威。

**修法**：写死落盘手段为 `printf`（把 `\t` 解释成真制表符），并显式禁 `echo` / 手拼字符串；
时间戳格式**定死与 run-id 一致**（`%Y%m%dT%H%M%SZ`），消除"UTC ISO8601"的自由裁量：

```
printf '%s\t%s\t%s\n' "<site>" "<task_id>" "$(date -u +%Y%m%dT%H%M%SZ)" >> "{change_dir}/.outside-voice/$RUN_ID/dispatch-manifest.tsv"
```

`<task_id>` 语义（后台派发填后台任务标识 / 同步 exec 填字面 `sync`）从格式串里拆出来单独成句。

## 顺带修正（本轮引入即修）

首版把两段命令写成嵌套 ``` fence，而整个 outside-voice 协议节**本身就在一个 ``` fence 内** ——
嵌套 fence 会提前闭合外层块（`grep -n '^```'` 实测 spec-review 出现奇数错位）。
改为**缩进 + 行内反引号**呈现，两文件 fence 计数恢复为偶数（spec 8 / code 12）。

## 改动位置

| 文件 | 位置 |
|---|---|
| `sdflow-spec-review/SKILL.md` | outside-voice 调用协议 → `context 构造` 块 |
| `sdflow-code-review/SKILL.md` | 同上 |

两段保持**逐字一致**，仅站点枚举行不同（design-voice/hr-tg vs code-voice/hr-tg）。

## 验证

### 1. 两段逐字一致（除站点行）

```
$ diff <(sed -n '/^context 构造/,/^exec：/p' sdflow-spec-review/SKILL.md) \
       <(sed -n '/^context 构造/,/^exec：/p' sdflow-code-review/SKILL.md)
10,11c10,11
<   site=design-voice → proposal「What Changes」+ design「Decisions」全文
<   site=hr-tg       → 命中 TG 判据触发点 + 相关 diff hunk
---
>   site=code-voice → git diff $DIFF_BASE..HEAD 全量
>   site=hr-tg      → 命中 TG 判据触发点 + 相关 diff hunk
```

差异仅站点枚举行 ✅

### 2. 两段命令真跑（scratchpad 沙盒）

```
RUN_ID=20260718T091106Z-93947-22192
--- manifest with tabs shown as ^I ---
hr-tg^Isync^I20260718T091106Z
design-voice^Ibg_12ab^I20260718T091106Z
--- awk field count (3 = real tabs) ---
3
3
--- collision test: same second, second run must get a DIFFERENT dir ---
RUN_ID2=20260718T091106Z-93947-28032
DISTINCT OK
--- mkdir without -p on existing dir must FAIL ---
exit=1  (expect non-zero)
with -p exit=0  (expect 0 = why -p is banned)
```

- `awk -F'\t'` 得 NF=3 ⇒ 落盘的是**真制表符**，非字面 `\t` ✅
- 同秒同 PID 两次占坑得到**不同目录**（`$RANDOM` 分开）✅
- `mkdir` 不带 `-p` 对已存在目录 **exit=1**；带 `-p` 则 **exit=0** —— 实证 `-p` 会吞掉本条款依赖的失败 ✅

### 3. 门禁

```
$ /usr/bin/python3 -m pytest -q
1619 passed, 2 skipped in 72.14s (0:01:12)

$ python3 hack/sync_principles.py --check
[sync_principles] ✅ 20 个投放面全部与真相源一致
exit=0
```

> 注：仓根 `python3`（`~/.local/bin/python3`）与 homebrew python3 均无 pytest，
> 本机 pytest 8.4.2 在 `/usr/bin/python3`。

## 未触碰（Non-Goals 遵守）

`outside-voice.sh` 本体 / 四旗承重墙 / 出境安全三件套 · `anchor_lint` 合法组合矩阵 · 锚行契约 ·
`sdflow:principles` 托管块 · change 四件套。
