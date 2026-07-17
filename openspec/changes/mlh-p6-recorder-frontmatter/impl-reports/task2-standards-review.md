# Task 2 Standards Review — semantic ID / repository lock

结论：**FAIL（commit `9f9adc6427254030166f4ca00281081bec13cf33`，审查区间 `ec8c38c..9f9adc6`）**

## Critical

无。

## Important

### 1. lock metadata 初始化失败会遗留本进程自己的 stale lock，并把真实 I/O 错误误报成 ownership-lost

- 位置：`sdflow-buglist/scripts/buglist.py:169-192`；同逻辑镜像于 `sdflow-todolist/scripts/todolist.py`、`sdflow-issues/scripts/issues.py`。
- `state` 在 metadata 成功写完前就已建立；`os.write()` 既未处理 short write，也可能与 `os.fsync()` 一样抛错。此时 `finally` 只能解析完整 metadata 才认定 owns，因空白/部分 JSON 解析失败而进入 `ownership lost`，保留本进程刚创建的 inode。
- 实测 monkeypatch `os.write` 抛 `OSError("write failed")` 后，最终异常是 `RecorderLockError ... ownership lost`，且 `.recorder.lock` 仍存在、size=0。后续全部 recorder 被永久阻断，必须人工 break-glass；原始 I/O 根因也被覆盖。
- 这不满足异常退出释放本进程 lock 的目标。应把 metadata publication 作为独立阶段：可靠 write-all；初始化失败时依据仍持有 fd / inode identity 安全删除自己创建的 path；只有 metadata 已发布后观察到 identity/token 替换，才保留 replacement lock。补 `os.write` short/raise、`fsync`/`close` fault injection。

### 2. invalid participant capability 被吞掉并静默升级为新 owner

- 位置：`sdflow-buglist/scripts/buglist.py:152-160`；同逻辑三向镜像。
- 环境中只要有 `SDFLOW_RECORDER_LOCK_TOKEN`，validation 失败就被 `except RecorderLockError: participant = None` 吞掉，随后走正常 `O_EXCL` acquire。目标 repo 当前无 lock 时，伪造、过期或 cross-repo token 不会 fail-loud，而会以 owner 身份进入 core。
- 实测 `SDFLOW_RECORDER_LOCK_TOKEN=expired ... buglist.py scan --json` 在空 repo 返回 exit 0。实现报告“伪造、过期、cross-repo 均 fail-loud”与真实 CLI 行为不符。
- capability 边界应以“env 是否存在”区分 participant attempt 与普通 top-level owner：env 存在但校验失败必须直接传播错误；只有 env 缺失才 acquire owner。测试必须走真实 CLI，而不是只直接调用 `validate_recorder_participant()`。

### 3. read-only lock 仍包住过滤、JSON 序列化和 StringIO 输出，未收窄到 immutable snapshot materialize

- 位置：`sdflow-buglist/scripts/buglist.py:1303-1309`、`sdflow-todolist/scripts/todolist.py:1278-1284`、`sdflow-issues/scripts/issues.py:1820-1828`。
- dispatch 在 `with recorder_lock(...), redirect_stdout(output)` 内执行完整 `args.func(args)`；`cmd_scan` 在锁内继续过滤、排序、`json.dumps(indent=2)` 并写 `StringIO`。它只把最终 OS stdout write 移到 unlock 后，没有做到规格要求的“snapshot 固化后先释放，再格式化/输出”。大仓 scan 的序列化 CPU 与内存拷贝仍延长 exclusive lock。
- 应让只读 core 返回 immutable result/snapshot，退出 lock 后再 render/write；mutation 命令仍持锁到最后一次 replace。现有测试没有断言 renderer/`json.dumps` 发生在 release 后。

### 4. runtime `.gitignore` 合并采用 `open(..., "wb")` 原地截断，写失败可损坏用户文件

- 位置：`sdflow-init/scripts/init.py:90-119`。
- 成功路径能保留 CRLF bytes，但写入不是 atomic：文件在 `open("wb")` 时先截断，随后磁盘满、权限/设备错误、进程终止或 short write 都可能留下空文件/半文件；`run()` 捕获异常也无法恢复 original bytes。
- 这是 init/update 修改用户自有 `.gitignore` 的数据安全缺口，也与本仓其它关键写路径使用同目录 tmp + `os.replace` 的维护标准不一致。应使用同目录唯一临时文件、完整写入/flush 后 replace，并补 write/replace failure 时 original bytes 不变的 fault tests。

### 5. 验证报告显著超出实际测试证据，关键 lock 协议场景未被守护

- `test_task2_semantic_lock.py` 实际只有 5 个 test 函数（参数化后 7 cases）；`test_runtime_gitignore.py` 只有 2 个 success/duplicate cases。
- 新测试没有覆盖 task/spec 明列的 reader↔writer 双向 barrier、两 namespace producer document-lock barrier、真实 nested delegation、真实非 allowlist subprocess token stripping、expired-token CLI、stdout/render release ordering、lock metadata write/fsync fault、`.gitignore` write/replace fault。20-process 用例也只断言返回成功的 ID 唯一与 lock 最终不存在，未核验最终文件包含全部成功项、无 lost update/半写。
- 因而“故障验收覆盖”与 DONE 结论不能作为这些协议的可信证据；上面 1-4 正是绿套件未发现的回归。应按每个 failure mode 建可判别测试，再更新实现报告。

## Minor

### 1. three-way AST guard 不保护决定行为的共享常量/类型

- 位置：`sdflow-buglist/tests/test_mirror_consistency.py:64-77`。
- helper AST 只看到全局名字，不会比较 `RECORDER_LOCK_ENV`、`RECORDER_PARTICIPANT_ALLOWLIST`、`CANONICAL_ID_RE` 的值，也不比较 `RecorderLockState` / `RecorderLockError` 定义；任一脚本改 allowlist 或 env 名，`recorder_lock`/`recorder_child_env` AST 仍可全绿。
- 当前三份值一致，但“机械防漂移”不完整。应显式断言共享常量与相关 class AST/字段一致。

## 领域清单

领域清单未覆盖：无匹配 Python CLI checklist。规则根解析为 `/Users/cheneyzhao/.sdflow/workflow`，现有 domains 仅 backend、backend-go、embedded、embedded-esp32、embedded-ml307c；本轮未静默宣称领域清单通过，按仓内标准、目标规格与 Fowler 级可维护性完成审查。

## Verification

- 固定输入：`openspec/changes/mlh-p6-recorder-frontmatter/impl-reports/task2-review-package.diff`（63,700 bytes）及 `task2-semantic-id-lock.md`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task2_semantic_lock.py sdflow-init/tests/test_runtime_gitignore.py sdflow-buglist/tests/test_mirror_consistency.py -W error` → `16 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ sdflow-init/tests/test_runtime_gitignore.py -W error` → `308 passed`。
- 手工 fault probe：`os.write` 抛错后得到错误的 `ownership lost` 且遗留 0-byte lock；expired token CLI 在空 repo exit 0。二者证明现有绿测不足以支撑 DONE。
