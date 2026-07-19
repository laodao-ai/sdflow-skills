## 0. 清理污染环境（**MUST 先于一切实现与验证**）

- [ ] 0.1 删除仓根 4 棵 JSON 命名的垃圾目录树（`find . -maxdepth 1 -name '{*'`，删前先列出确认）
      〔Success Metric 5；design Risks「自我掩盖」〕
- [ ] 0.2 确认干净：`find . -maxdepth 1 -name '{*'` 无输出
      **为什么必须最先做**：`os.path.isdir` 按 cwd 解析相对路径，这 4 棵树会让坏值通过校验
      （ADR-2 实测：`isdir`-only 在仓根 4 passed、在空 cwd 4 failed）。在被污染的环境里得到的
      任何绿都不可信。

## 1. repo_root 分流校验（三份同步）

- [ ] 1.1 三份 recorder 的 `repo_root` **同一提交内**逐字同步改为三分支：
      git 抛异常/rc≠0 → `return os.path.abspath(start)`（不变）；
      `top = out.stdout.strip()` 且 `top and os.path.isabs(top) and os.path.isdir(top)` →
      `return top`；否则 `raise ValueError(...)`（消息含被拒值截断 80 字节 + `cause:` + `fix:`）。
      MUST NOT 在 helper 内 `sys.exit`，MUST NOT 写 stdout
      〔Req: recorder 仓根解析对外部进程输出 fail-closed / 三份逐字一致；ADR-1、ADR-2、ADR-4〕
      - `sdflow-issues/scripts/issues.py:1132-1150`
      - `sdflow-buglist/scripts/buglist.py:581-590`
      - `sdflow-todolist/scripts/todolist.py:581-590`
- [ ] 1.2 三份各加负例测试：git rc=0 但 stdout 为「非绝对路径 / 绝对但不存在 / 空串 / 纯空白」
      时抛 `ValueError`，**且断言该值对应路径未被创建**（用 `tmp_path` 构造真实存在/不存在的
      路径，MUST NOT mock `os.path.isabs` / `os.path.isdir`——mock 掉判据本身等于没测）
      〔Req: recorder 仓根解析对外部进程输出 fail-closed；design Risks「isdir 引入 IO」〕
- [ ] 1.3 **cwd 不变性测试**：坏值为「在 cwd 下恰好存在的相对路径」时仍抛 `ValueError`；
      同一用例在仓内 cwd 与仓外 cwd 下结果一致
      〔Req: Scenario「坏值恰好匹配 cwd 下的既存目录」；ADR-2 的实测反例〕
- [ ] 1.4 正向回归：git 返回合法绝对目录时行为不变；git 抛异常/非 0 退出时回落不变；
      非 git 仓库下 CLI 命令仍 exit 0 正常完成
      〔Req: Scenario「git 返回合法仓根」「git 命令失败」〕
- [ ] 1.5 **调用点契约测试（CLI 真跑，三份各一条）**：以子进程真跑
      `python <script> --root <坏根> <cmd>`，断言 `exit == 2` 且 stderr **不含** `Traceback`
      且含诊断关键字。MUST NOT 用 AST/源码扫描去判断「调用点是否在 try 内」——
      那是语法结构问题，手搓判断会掉进「嵌套 try / 装饰器 / 多重 except」的补丁循环
      （基准 5）；让 Python 自己回答异常有没有被接住
      （`issues.py:2324` / `buglist.py:1594` / `todolist.py:1568`）
      〔Req: Scenario「抛出点在调用方的异常出口内」；ADR-4 代价缓解〕
- [ ] 1.6 跑 determinism-guards 的 recorder 镜像一致性测试，确认 `repo_root` 三向 AST 等价仍绿
      〔Req: fail-closed 校验在三份 recorder 间逐字一致〕

## 2. 假绿测试修复

- [ ] 2.1 修 `sdflow-issues/tests/test_task4_rename_snapshot.py:149`
      `test_reindex_cli_non_string_id_is_controlled_and_preserves_derived_bytes`：
      让 root 解析不受 monkeypatch 全局 `subprocess.run` 污染（mock 收窄到 `_scan_pool` 的
      调用点，或让 mock 对 `git rev-parse` 透传真实行为），使 reindex 真正作用于 `tmp_path`
      〔Req: 坏 root 下的 reindex 不得静默通过派生字节校验〕
- [ ] 2.2 **变异验证**：故意让 reindex 向 `tmp_path` 的 `INDEX.md`/`batches.md` 写入，确认该
      测试**变红**；恢复后确认变绿。当前它对该变异恒绿，正是假绿判据
      〔Req: 坏 root 下的 reindex 不得静默通过派生字节校验，Scenario「变异验证——写入即变红」；Success Metric 2〕
- [ ] 2.3 补齐该用例的完整断言集：exit=2 + **stderr 含 `scan item[0].id`** + 派生字节不变
      + **cwd 无新增条目**。MUST NOT 仅凭 exit 2 判定通过——坏 root 与坏 scan id 都产生 exit 2
      〔Req: Scenario「坏 scan 输出被受控拒绝且不误伤派生字节」「拒绝理由必须可区分」〕
- [ ] 2.4 若 2.1 修复后暴露此前从未执行过的 reindex 分支失败 → **当场 fold 修掉**，不 defer
      〔design Risks「修完假绿测试后覆盖仍不足」〕

## 3. cwd 泄漏回归断言

- [ ] 3.1 新建**仓根单一份** `conftest.py`：autouse fixture 比对每个用例运行前后的 cwd 条目集，
      新增条目即失败并报出条目名（`.pytest_cache` 等 pytest 自身产物除外）。
      MUST NOT 在各 skill 的 `tests/` 下复制副本（ADR-3：会构成第四组无守护镜像）
      〔Req: 测试套件不得在当前工作目录留下副作用；ADR-3〕
- [ ] 3.2 覆盖面验证：12 个 skill + hack 各自在干净临时目录跑一遍，确认 fixture 全部生效
      且**无误报**（实测基线：本 change 前均 0 残留）
      〔Req: Scenario「覆盖面为全仓而非仅 recorder」〕
- [ ] 3.3 反向验证 fixture 真的会红：临时插一个在 cwd 建目录的用例，确认被捕获并报出条目名
      〔Req: Scenario「泄漏被回归断言捕获」〕

## 4. 清理与收尾

- [ ] 4.1 回归确认垃圾树未再生：实现全部完成后 `find . -maxdepth 1 -name '{*'` 仍无输出
      （Task 0 已删除；本条验证的是「修完之后不会重新长出来」）
      〔Success Metric 5〕
- [ ] 4.2 验证锚：在干净临时目录跑 `pytest sdflow-issues/tests/`，确认条目数 = 0
      〔Req: 测试套件不得在当前工作目录留下副作用；Success Metric 3〕
- [ ] 4.3 在 `CLAUDE.md` 的 `openspec/rules/` 段登记 `premise-verification.md` 的编号 + 路径
      指针（**只写编号 + 路径，MUST NOT 复制规则文本**——该段的既定约定）
      〔proposal P2〕
- [ ] 4.4 同步 `CLAUDE.md` 的「运行测试」段：「没有根级 pytest 配置——测试各 skill 自包含」
      一句已被 Task 3.1 的根级 `conftest.py` 证伪，改为「测试各 skill 自包含在
      `<skill>/tests/`；仓根有唯一一份 `conftest.py`，只承载全仓通用的 cwd 副作用断言」
      〔ADR-3 代价；不改即为本变更自己制造的文档漂移〕
- [ ] 4.5 记 buglist：`sdflow-init/tests/test_outside_voice.py::test_exec_claude_reverse_path_three_flags_golden`
      全量跑 FAILED / 单独跑 PASSED（order-dependent 或负载敏感），显式传 `change` 字段
      〔proposal Non-Goals〕
- [ ] 4.6 全仓跑一遍 `pytest`，确认无回归

## 测试覆盖图（TG-18）

| code path | 测试类型 | 落点 | 对应 Requirement |
|---|---|---|---|
| `repo_root` git rc=0 + 合法绝对目录 | 单元（正向） | 三份各一 · 1.4 | fail-closed 解析 |
| `repo_root` git rc=0 + 非绝对/绝对不存在/空/空白 | 单元（负例 ×4 值） | 三份各一 · 1.2 | fail-closed 解析 |
| `repo_root` 坏值命中 cwd 同名目录 | 单元（**cwd 不变性**） | 1.3 | 坏值恰好匹配 cwd 既存目录 |
| `repo_root` git 异常/非 0 退出 | 单元（回归） | 三份各一 · 1.4 | fail-closed 解析 |
| 非 git 仓库下 CLI 仍 exit 0 | 集成（CLI） | 1.4 | fail-closed 解析 |
| 坏 root 经 CLI → exit 2 + stderr 非 traceback | 集成（调用点契约） | 1.5 | 抛出点在异常出口内 |
| 三份 `repo_root` AST 等价 | 一致性（既有） | determinism-guards · 1.6 | 三份逐字一致 |
| `reindex` 坏 scan id → exit 2 + 派生字节不变 | 集成（CLI） | 2.1 / 2.3 | reindex 不得假绿 |
| `reindex` 写入 `tmp_path` → 测试必红 | **变异验证** | 2.2 | reindex 不得假绿 |
| 任意用例的 cwd 副作用 | autouse fixture | 3.1 / 3.2 | 测试套件无 cwd 副作用 |
| fixture 自身有效性 | 反向验证（故意泄漏） | 3.3 | 测试套件无 cwd 副作用 |

## 追溯核对

| Requirement | 覆盖任务 |
|---|---|
| recorder 仓根解析对外部进程输出 fail-closed | 1.1, 1.2, 1.3, 1.4, 1.5 |
| fail-closed 校验在三份 recorder 间逐字一致 | 1.1, 1.6 |
| 测试套件不得在当前工作目录留下副作用 | 0.1, 0.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2 |
| 坏 root 下的 reindex 不得静默通过派生字节校验 | 2.1, 2.2, 2.3, 2.4 |

无幽灵任务：4.3 锚 proposal P2；4.4 锚 ADR-3 的代价（根级 conftest 使 CLAUDE.md 现有表述失真）；
4.5 锚 proposal Non-Goals；4.6 为全局回归。均在 proposal/design 中有出处。
