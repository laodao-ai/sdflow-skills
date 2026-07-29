# Task 4 delivery — Windows CI sweep path fix

## 交付

- `windows-recorder-smoke.yml` 的 GBK 子进程段由 `issues.py reindex` 改为运行受控盘面的真实 `sweep` 行为测试。
- 新测试先通过真实 `buglist.py add` 生成临时 fixture，再直接执行 `issues.py sweep`；记录并断言调用图实际经过两次 `scan`、一次 `triage`、一次 `batch add` 与一次 `reindex`，并逐调用断言 `text=True`、`encoding="utf-8"`、`errors="replace"`。
- 非法字节 replacement fixture 保持不变。

## 验证

```text
$env:PYTHONIOENCODING='gbk'; py -m pytest -q \
  sdflow-issues/tests/test_task5_delivery_contract.py::test_windows_smoke_workflow_is_persistent_and_branch_agnostic \
  sdflow-issues/tests/test_task5_delivery_contract.py::test_sweep_cli_executes_all_four_utf8_subprocess_sites -W error
2 passed
```

`git diff --check` 通过。
