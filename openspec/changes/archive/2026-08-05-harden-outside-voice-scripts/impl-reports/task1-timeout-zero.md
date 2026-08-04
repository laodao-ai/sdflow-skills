# Task 1: --timeout 0 拒绝 + 专项测试

## 变更

`sdflow-init/assets/hack/outside-voice.sh` `render-prompt|exec)` 分支的 `--timeout` 参数解析
（既有纯数字校验 `case "$2" in ''|*[!0-9]*) usage ;; esac` 之后、`tmo="$2"` 赋值之前）新增一行：

```sh
[ "$((10#$2))" -eq 0 ] && usage
```

`10#` 前缀强制 shell 算术按十进制解析 `$2`，正确捕获 `0`/`00`/`000` 等所有前导零变体（不加
`10#` 会被 bash 算术当八进制解析，`008`/`009` 这类值会直接算术求值报错而非按预期落进 usage()）。
命中即 `usage()` → `exit 2`，与既有非法值（空/含非数字字符）行为一致（承重约束 C1）。

## 测试

在 `sdflow-init/tests/test_outside_voice.py` 新增 4 个用例（B2 usage negatives 段落之后）：

- `test_usage_exec_timeout_zero_exit2`（parametrize `0`/`00`/`000`）—— PATH 故意不放任何假
  runner；若解析未在 `usage()` 前拦下会走到 `do_exec` 并因 `timeout/gtimeout 未安装` 报 exit 1
  （另一种失败形态），故 exit 2 只可能来自 `usage()` 本身，结构上即证明 runner 从未启动。
- `test_exec_timeout_leading_zero_accepted`（`--timeout 01`）—— 用 `FAKE_CODEX_MODE=hang` 跑满
  真超时（exit 124），证明 `01`（十进制 = 1，非零）被解析放行并把值传给了 runner，不误拒。
- `test_exec_timeout_normal_value_unaffected`（`--timeout 300` + ok 模式）—— 既有正常值行为
  不受新增零值校验影响。

### Red → Green

修复前跑新增的 3 个零值用例：均以 `AssertionError: assert 1 == 2` 失败（实际 exit 1
`timeout/gtimeout 未安装`，证明当时确实放行到了 `do_exec`），确认测试有效捕获缺陷后再实现修复。

修复后：

```
$ /usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice.py -v -k "timeout"
...
9 passed, 58 deselected in 5.36s
```

```
$ /usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice.py
...
65 passed, 2 skipped in 19.89s
```

2 个 skip 为既有的系统 timeout/gtimeout 存在时才跳过的分支测试（与本次改动无关，pre-existing）。

## 范围声明

Task 2（出境 stdout 大小限制）与 Task 3（收尾验证）不在本票范围内，未涉及。
