---
ship-gate:
  verify: PASS
  reviewed_sha: 49a7f388d7586e93c27b11899c54ff7018fc0fac
---

# Verify Report: fix-windows-encoding-crash

## 结论

**PASS — 可归档。**

Do Not Trust the Report：本轮从当前源码、delta spec、tasks 与实际命令重新取证，没有把
Task 5 或代码审报告的结论直接当证据。核验 HEAD 为
`49a7f388d7586e93c27b11899c54ff7018fc0fac`。

最终新增的 `_scan_pool` 动态 `**kwargs` 解码站点已显式使用 UTF-8/replace；旧 GBK
解码故障已在 code page 936 下复现，新实现及安装后的 `issues.py sweep/reindex` 均通过。
其余编码门、Windows 同构 probe、19-test 聚合和 strict validate 全部通过，未发现新的核心
缺口。

## Pipeline 与最终源码盘面

- Pipeline：`tickets`。机器锚：`tickets.md:2` 的 frontmatter
  `impl-pipeline: tickets`。
- 最终源码 SHA：`867c97566ca9990d55015ced7bf2ccf5ad1605ba`。
- `git diff --quiet 867c975..HEAD -- . ':!openspec/changes/fix-windows-encoding-crash'`
  退出 0；`867c975..HEAD` 仅修改 change 四件套、Task 5 报告和代码审报告，没有源码变化。
- 本轮开始前工作树已有 `openspec/issues/batches.md` 与
  `openspec/issues/todolist/2026-07-todolist.md` 修改（上游收尾 sweep 产物）；本验证未触碰
  真实 issues 台账，只在临时仓运行 sweep/reindex。除本报告外未新增仓内修改。

## 逐项终验

### 1. 旧 `_scan_pool` GBK 解码故障复现 — PASS（故障机理已证实）

在 Windows Git Bash 执行 `chcp.com 936` 后，让子进程输出含中文的 UTF-8 JSON，并以旧式
GBK 文本解码读取，得到：

```text
OLD_GBK_DECODE=REPRODUCED(stdout=None after reader UnicodeDecodeError)
Exception in thread Thread-1 (_readerthread):
UnicodeDecodeError: 'gbk' codec can't decode byte 0xad ...
```

同一载荷改为 `encoding="utf-8", errors="replace"` 后：

```text
NEW_UTF8_DECODE=PASS
```

这直接证明此前动态 kwargs 站点会落回 Windows locale 解码并崩溃，而显式 UTF-8 修复消除
该故障；不是只靠源码目测。

### 2. 新 `_scan_pool` 实现与回归 — PASS

实现锚：`sdflow-issues/scripts/issues.py:441-465`。`_scan_pool` 的动态 kwargs 明确包含：

```python
"capture_output": True,
"text": True,
"encoding": "utf-8",
"errors": "replace",
```

随后才按 recorder token 动态追加 `env`，并以 `**kwargs` 调用 `subprocess.run`。

回归锚：`sdflow-issues/tests/test_task5_delivery_contract.py:317-332` 的
`test_reindex_nested_scan_decodes_child_json_as_utf8` 实际调用 `_scan_pool`，断言动态 kwargs
中的 text/encoding/errors 三项值。

### 3. 安装后的 issues sweep/reindex，cp936 真实执行 — PASS

先在 code page 936 下运行当前 `setup.sh` 刷新 Windows copy-mode 安装副本，再创建临时仓：

```text
chcp.com 936
env -u PYTHONIOENCODING bash setup.sh
python3 ~/.codex/skills/sdflow-issues/scripts/issues.py \
  --root <temp> sweep --change verify-installed-sweep
python3 ~/.codex/skills/sdflow-issues/scripts/issues.py \
  --root <temp> reindex --strict

CP936_SETUP=PASS
INSTALLED_SWEEP=PASS
INSTALLED_REINDEX=PASS
```

sweep/reindex 日志均不含 `UnicodeDecodeError`、`UnicodeEncodeError` 或 `Traceback`，且临时
仓成功生成 `openspec/issues/INDEX.md`。真实仓的 issues 文件未被测试修改。

仓库脚本也在独立临时仓按相同 cp936 环境运行：sweep RC=0，reindex RC=0，确认修复不依赖
安装目录偶然状态。

### 4. subprocess / write_text 契约盘面 — PASS

- 四件套已统一为 **16 个文本模式 subprocess 站点 / 15 个编辑点**：15 个直接
  `text=True` 站点加 `_scan_pool` 动态 `**kwargs` 站点。任务锚：`tasks.md:2,45-59`。
- CI 实际路径覆盖 **8/16**（含 reindex → `_scan_pool` 嵌套 scan）；任务与测试覆盖图锚：
  `tasks.md:82-83,113`。
- `hack/tests/test_subprocess_encoding_contract.py:38-75` 继续守 15 个直接站点与
  `ship_gate` 原始字节路径；动态第 16 站点由上述 `_scan_pool` 专项测试守护。
- delta spec 的总契约锚：`specs/encoding-hygiene/spec.md:78-90`。

### 5. 当前源码聚焦聚合 — PASS

命令：

```text
python -m pytest -q -rs \
  hack/tests/test_encoding_hygiene.py \
  hack/tests/test_subprocess_encoding_contract.py \
  sdflow-issues/tests/test_task5_delivery_contract.py \
  -k "not upgraded_install_known_consumer_smoke"
```

结果：`19 passed, 1 deselected in 0.93s`。

### 6. Task 5 同 SHA 证据 — PASS

`impl-reports/task5-implementation-validation.md:11-35` 的全量、19-test 聚合、GBK setup、
encoding-hygiene 门、strict validate、V-1 probe、6.5 workflow/chcp 及嵌套 scan 解码均记录
同一最终源码 SHA `867c97566ca9990d55015ced7bf2ccf5ad1605ba`；`:44` 明确汇总同 SHA。

### 7. init → GBK update 同构 probe — PASS

workflow 锚：`.github/workflows/windows-recorder-smoke.yml:57-64`。当前源码实跑：

```text
INIT_RC=0 UPDATE_GBK_RC=0
```

两段日志均不含 `UnicodeEncodeError` 或 `Traceback`。

### 8. cp936 console + redirected setup — PASS

workflow 锚：`.github/workflows/windows-recorder-smoke.yml:76-82`，使用 Git Bash 可执行的
`chcp.com 936`，随后直接运行 fail-closed hygiene 门，再运行 redirected setup 并 grep
异常。本轮完整执行退出 0：

```text
CP936_SETUP=PASS
[encoding-hygiene] 所有入口脚本均满足编码前导契约
```

### 9. OpenSpec 与机械门 — PASS

```text
openspec validate fix-windows-encoding-crash --strict --type change
Change 'fix-windows-encoding-crash' is valid

python hack/check_encoding_hygiene.py
[encoding-hygiene] ✅ 所有入口脚本均满足编码前导契约
```

`git diff --check` 退出 0（仅提示既有 `batches.md` CRLF 将来规范化，不是 whitespace error）。

## 已知 gap（不阻断）

### 全量 pytest：两项既有 Windows/Python 3.14 收集错误

当前 HEAD 的 `python -m pytest -q -rs` 于收集期退出 1：

```text
sdflow-init/tests/test_outside_voice_child_lifecycle.py:199
AttributeError: module 'signal' has no attribute 'SIGHUP'

sdflow-ship/tests/test_gate_freshness.py:1044
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff ...

2 errors during collection
```

`git merge-base HEAD main` 为 `3b4f838b99f2ccd3bf7a246e8ab675a9b6c40943`；上述两文件
相对该 merge-base 的 `git diff --quiet` 退出 0，确认是既有平台兼容缺口，并非本 change
引入。按已批准契约，相关聚焦层全部通过时不阻断归档。

### 远端 Windows e2e 未覆盖

`windows-latest` 尚未实际运行；Task 5 在
`impl-reports/task5-implementation-validation.md:39,45` 如实记“未覆盖”。本轮已在同类
Windows Git Bash 本机真实执行最承重的 GBK/cp936、安装副本 sweep/reindex 与 init/update
路径；按已批准套件发现契约，远端缺层不升级为 blocker，也不伪报为通过。

## 归档判定

**PASS，可继续 archive。**
