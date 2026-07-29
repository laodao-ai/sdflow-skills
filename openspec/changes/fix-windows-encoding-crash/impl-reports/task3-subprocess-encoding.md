# Task 3 实现报告：子进程文本编码与 `write_text` 核实

## 结果

完成 `tickets.md` 3.1、3.1a、3.1b 与 3.2 的本票实现范围：15 个 `text=True`
调用站点由 14 个正确编辑点覆盖；`ship_gate` 的两个文本调用仍经单一 `_git_run`
出口继承编码参数，`run_git_bytes(text=False)` 未改动。

## 变更清单

- 就地补齐 `encoding="utf-8", errors="replace"`：
  `sdflow-devenv/scripts/devenv_scaffold.py`（2）、
  `sdflow-done/scripts/roadmap_writeback_draft.py`、
  `sdflow-implement/scripts/impl_route.py`、
  `sdflow-init/assets/hack/outside-voice-job.py`、
  `sdflow-init/assets/hooks/ff0-branch-guard.py`、
  `sdflow-init/scripts/init.py`、
  `sdflow-issues/scripts/issues.py`（4）、
  `sdflow-retro/scripts/retro_report.py`。
- `sdflow-init/assets/workflow/tools/trivial_shape.py` 原已有
  `errors="replace"`，仅补 `encoding="utf-8"`，保留原有容错语义。
- `sdflow-ship/scripts/ship_gate.py` 仅在 `_git_run` 的 `text` 分支补
  `kwargs["encoding"] = "utf-8"`；两个 `run_git`/`run_git_rc` 调用点未加参数，
  `run_git_bytes` 仍传 `text=False` 并返回原始字节。

## 判定路径复核

新增 `errors="replace"` 的站点逐一过目如下。替换仅在子进程输出不是 UTF-8 时发生；正常
UTF-8 协议输出不变。

| 路径 | 后续用途 | 等值/去重/分类结论 |
|---|---|---|
| `devenv_scaffold.py` | HEAD 标识或命令日志 | HEAD 为 ASCII；其余仅呈现，不参与等值判定 |
| `roadmap_writeback_draft.py` | 分支名写入草稿 | 不参与通过/失败、去重或分类 |
| `impl_route.py` | 短 SHA | Git SHA 为 ASCII，不存在替换趋同 |
| `outside-voice-job.py` | 外部 CLI 的诊断输出 | 不作为等值或分类键 |
| `ff0-branch-guard.py` | Git 查询失败回退为空串 | 不把替换结果与成功值等同，异常/失败仍走既有拒绝路径 |
| `init.py` | 仓根路径发现 | 仅用于定位；失败不会被映射为“同一仓根” |
| `issues.py` | 子脚本 JSON 协议、错误诊断 | JSON/triage 失败仍显式报错；替换结果未作去重或分类键 |
| `retro_report.py` | Git 历史文本 | 既有错误分支保留，不以替换文本作历史存在性的等值证明 |

`ship_gate` 与 `trivial_shape` 的 `errors="replace"` 均为既有语义；前者的保真比较
专用 `run_git_bytes` 路径保持原始字节，后者只新增 UTF-8 声明，未改变其既有替换策略。

## `write_text` 核实

以 AST 解析非测试、非 `openspec/` 的 Python 文件，遍历每个 `.write_text()` 调用并读取
keyword AST；结果为 **9 个站点、0 个缺少 `encoding="utf-8"`**。该方法可识别跨行参数，未为
已满足的调用制造修改。相同验证方法与结果已回写 `decision-memo.md` C8。

## 验证

```text
python -m pytest hack/tests/test_subprocess_encoding_contract.py hack/tests/test_encoding_hygiene.py -q
10 passed

python hack/check_encoding_hygiene.py
[encoding-hygiene] ✅ 所有入口脚本均满足编码前导契约

python -m compileall -q <10 个受改脚本>
exit 0

git diff --check
exit 0
```

全量 `python -m pytest -q` 未能完成收集（Windows 环境）：
`sdflow-init/tests/test_outside_voice_child_lifecycle.py` 依赖不存在的
`signal.SIGHUP`，`sdflow-ship/tests/test_gate_freshness.py` 在模块导入时以非 UTF-8
字节构造文件系统字符串而触发 `UnicodeDecodeError`。两项均发生在本票测试执行前的收集阶段，
与本票修改无关；受影响的聚焦回归已单独通过。

新增 `hack/tests/test_subprocess_encoding_contract.py` 以 AST 锁定 tickets 3.1 列出的
13 个直接 `subprocess.run(text=True)` 站点，以及 `ship_gate` 的单出口文本 kwargs 与
原始字节 helper 边界。
