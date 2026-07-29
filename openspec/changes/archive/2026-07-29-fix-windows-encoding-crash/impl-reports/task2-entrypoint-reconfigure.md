# Task 2 实现报告：入口标准流编码保护

## 交付

- 按 `hack/check_encoding_hygiene.py` 的初始真实缺失集合，为全部 28 个 Python 入口脚本加入统一的模块顶层前导：

  ```python
  for _s in (sys.stdout, sys.stderr):
      try: _s.reconfigure(encoding="utf-8", errors="replace")
      except Exception: pass
  ```

  前导都位于 `import sys` 之后、首个业务逻辑之前，不在 `__main__` 守卫内。它同时保护 stdout 和 stderr，使用 UTF-8 加替换容错；缺少 `reconfigure` 的流会被既定的 `except Exception` 静默降级。
- 对 canonical bundle 的 6 个 `sdflow-init/assets/workflow/tools/*.py` 仅修改源文件；随后运行 `python3 sdflow-init/scripts/init.py update --root .`，正式刷新了 `openspec/workflow/tools/*.py` 镜像。
- 同步后比较 canonical 和镜像的 tools 文件集及逐文件 SHA-256，二者完全一致；同步产生的版本控制差异仅为这 6 个预期镜像。`CLAUDE.md` 在同步前已处于修改状态、且无本票内容 diff，未纳入本票。

## TDD 与测试

- 前置常驻行为测试已由 Task 1 建立；本票将其作为入口前导契约的公共 seam，未新增耦合实现细节的测试。
- `python3 -m pytest hack/tests/test_encoding_hygiene.py -q` → `8 passed`。
- `python3 hack/check_encoding_hygiene.py` → 退出 0，缺失集合归零。
- 对本票 34 个变更 Python 文件执行 `python3 -m py_compile` → 全部通过。
- `git diff --check` → 通过。

## 范围与后续

- 本票仅实现 EH-ENTRY 的入口流保护及镜像同步；`subprocess text=True` 编码、CI 与 setup 接线属于后续票，未修改。
- 前导中 `except Exception` 的运行时触发分支没有专门自动化测试；这是设计已记录的静默降级边角，机械门验证所有 28 个入口均具备该契约。
