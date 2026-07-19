# Task 1 返修第 3 轮 — N1：`exit 2` 让 render 报错被 workdir 静默吞掉

分支 `feat/fix-mechanical-layer-silent-failures`。本轮只治 re-review 新抓的 1 个洞（I1/I2/M5/M6/S1/S2/S3 未动），
**未做 async/backgrounding 改动**，**未提交**。

## N1（Important）成因

`do_exec` 里 `render_prompt "$ctx" > prompt.md 2> "$workdir/render.meta"`，**下一行**才 `cat render.meta >&2`。
`render_prompt` 内的三条 fail-loud 分支（context 不可读 / size 取不到 / secret 命中）都是 **`exit`**——
不套子壳时它直接终止**整个脚本** ⇒ 回灌 `cat` 永不执行，且 EXIT trap 的 `rm -rf $workdir` 抹掉 render.meta
⇒ 操作者拿到 **rc=2 + stdout 0 字节 + stderr 完全为空**，零诊断。

第 301 行的 `-f`/`-r` 预检按定义盖不住 TOCTOU——那正是「检查之后才发生」的那类事。
即：一个专治「exit 非 0 但没人知道为什么」的 change，在自己新开的路径上复活了报错被吞。

## 改动

### 1) `sdflow-init/assets/hack/outside-voice.sh` — 子壳隔离 + 无条件回灌（约 319 行）

```
( render_prompt "$ctx" ) > "$workdir/prompt.md" 2> "$workdir/render.meta"
rc=$?
cat "$workdir/render.meta" >&2
if [ "$rc" -ne 0 ]; then exit "$rc"; fi
```

- 子壳里 `exit` 只终止子壳、rc 可捕获；`( )` 子壳中 EXIT trap 被重置为默认 ⇒ workdir 不会被提前删。
- **无论成败都先回灌**再按 rc 决定终止 ⇒ 成功路径的 `OV_TRUNCATED=` 契约行行为不变（rc=0 时不 exit）。
- 本脚本无 `set -e`，故写成 `if` 块而非 `[ ] && exit`（后者在末尾会污染返回值）。
- 原始 rc **保真透传**（2/3 各自保留），不塌缩成 1。

### 2) 面治：同片形态一次扫全

全脚本 `2> "$file"` 的重定向共 3 处（`render.meta`、codex/claude 的 `stderr.log`）。
逐条核过：`stderr.log` 两处是外部命令（不会 exit 本脚本），rc≠0 与 rc=124 两条分支都已回灌——
**但 rc=0 而最终消息为空的那条分支只 tail `cli.log`、不灌 `stderr.log`**，属同一病：
claude 路径的 `cli.log` 是 last-message 的镜像（此处必空）⇒ 该分支原本给出**零信息**。
已补 `tail -5 stderr.log`（runner 自身 stderr，非 context 正文；另两条分支本就在灌 ⇒ 无新增出境面）。

`render-prompt` 子命令（约 416 行）的调用点无重定向，stderr 直通，无此形态。

## 实跑核实

驱动方式：PATH 前置一个恒 `exit 1` 的 `wc` shim（= 模拟第 301 行预检之后才发生的 TOCTOU），
真跑 `bash outside-voice.sh exec --context-file <ctx>`（`SDFLOW_VOICE_RUNNER=codex`）。

| 版本 | rc | stdout | stderr |
|---|---|---|---|
| 修复前（复现原症） | 2 | 0 字节 | **0 字节** |
| 修复后 | 2 | 0 字节 | 184 字节，含固定字面 `context file size 读取失败（不可读/竞态改动）` |

## 新增断言测试 + 变异验证

`sdflow-init/tests/test_outside_voice_utf8.py::test_exec_render_failure_still_reaches_stderr`
（exec 路径端到端真跑，非 source 接缝）：断言 rc==2 且 stdout 空 且 **stderr 非空** 且含 `size 读取失败`，
并顺带断言 stderr **不含** context 正文探针（`hello ASCII` / `更多中文` / `😀`）——守出境约束。
无 `timeout`/`gtimeout` 时 skip（do_exec 会更早退出）。

**变异验证已实跑**：把 do_exec 的子壳 + rc 回灌还原成裸调用 ⇒ 该测试
`AssertionError: N1 复发：exit 非零但 stderr 全空`（`returncode=2, stderr=''`）转红；还原修复后转绿。

> 顺手修：原 `test_backscan_fallback_emits_visible_marker` 尾部的正文泄漏探针循环在编辑中被
> 带到了新测试下，已归位（该断言仍守 `broken.stderr`，语义未变）。

## 测试结果

- `/usr/bin/python3 -m pytest sdflow-init/tests/ -q` → **264 passed**
- `/usr/bin/python3 -m pytest -q`（全套件）→ **1712 passed, 2 skipped**
- `test_async_branch_parity` → **26 passed**（未受影响）

## 约束自查

- 新增 stderr 只有 runner 自身 stderr 的 tail 与已有固定字面，**无 context 正文**。
- 未碰锚行字段 / `anchor_lint` 矩阵 / recorder / 两层 SKILL 的 async 字节等值 marker 段。
- 未做 async/backgrounding 改动（`do_exec` 子进程生命周期留给 Task 2）。
- 契约通道未变：`OV_TRUNCATED=` 仍经 render.meta 回灌，成功路径行为与改前逐字节一致。

## 遗留（非本轮引入）

工作树里有一个前轮遗留的未跟踪文件 `sdflow-init/assets/hack/.mut3.sh`（变异测试残留），
未擅自删除——建议提交前清掉。
