# Task 5 · 实现验证（收尾聚合回归）

**R-ID: all** —— 覆盖本 change 全部需求的聚合验证（Spec 轴据此核验，非逐条溯源）。
**定位**：实现期聚合回归门（跑在 `sdflow-code-review` 及其自动修复循环**之前**），回答「全部功能票
实现完毕这一刻，聚合套件是否通过」，**不声称**「最终代码通过聚合套件」。最终门 = `sdflow-done` 的
verify（本票不是 verify、不替代 verify）。

## 聚合套件发现（本仓形态）

本仓为 Claude Code + Codex 自建 Skills 集合仓库（Python 脚本 + Markdown 编排），`openspec/config.yaml`
无 `test-suites` 段。依仓内既有约定判定（CLAUDE.md「常用命令」+ `pytest.ini` + `conftest.py`）：

- **单元 + 集成同属一个 pytest 套件**：本仓无独立 integration target，`pytest` 发现并运行全部
  `test_*.py`（各 skill 自包含 `tests/` + 仓根 `conftest.py`/`pytest.ini` 承载 cwd 副作用断言 +
  `hack/tests/` 的 setup.sh/resolve-workflow **真跑 bash** 集成测试）。单一命令即覆盖两层。
- **e2e 层**：本仓无独立 e2e harness——自动化面 = pytest（含真跑 bash 的集成用例）+ CI
  `mechanical-gates.yml`。判定依据：无 `e2e/` 目录、无独立 e2e runner、README/CI 无 e2e target。

**命令**：`/usr/bin/python3 -m pytest -q`（CLAUDE.md 记「直接跑 pytest」，但本机裸 `pytest` 不存在、
默认 `python3` 未装 pytest ⇒ MUST 用系统 python，见本仓测试环境事实）。

## 证据（`<层> | <命令原文> | <退出码> | <SHA>`）

最终 SHA = `40585ab0b7bbb2db7360c238cb5620f8b9f1a9b6`（全部功能票 + 双轴审返修落地后，收集证据时
`git rev-parse HEAD`；工作树无未提交 code 改动）。全部「通过」行锚同一最终 SHA。

| 层 | 命令原文 | 退出码 | SHA |
|---|---|---|---|
| 单元 | `/usr/bin/python3 -m pytest -q` | 0（2580 passed, 10 skipped） | `40585ab` |
| 集成 | 同上（本仓单元+集成同一 pytest 套件，含 `hack/tests/` 真跑 bash 的 setup.sh/resolve-workflow 集成用例） | 0（同上运行） | `40585ab` |
| e2e | — | 未覆盖 | 本仓无独立 e2e 层（无 `e2e/` 目录、无 e2e runner、CI 仅 pytest + mechanical-gates）；自动化面已由单元+集成 pytest + CI 覆盖 |

跑法：由编排层（ship 主 session）**亲自**在最终 SHA 后台跑一次全量 `pytest`，`buzlw5giu.output`
尾部 = `2580 passed, 10 skipped in 377.21s`，exit code 0。收尾票豁免 red-before-green（不写产品
代码，验收物是本证据非 diff）。

## 无 skip/弱化断言蒙混核验（Standards 轴扩，全 change diff `e58aaaf..HEAD`）

- **新增 skip 标记 1 处**：`test_anchor_contract.py`（或迁移测试）的
  `@pytest.mark.skipif(os.name == "nt", reason="Win32 路径无法含 Tab/非法字符")`——manifest 字节
  保真 round-trip 用例的**合法平台守卫**（Win32 路径不能含 Tab/非法字符，该用例前提在 Windows
  不成立），非掩盖失败。
- **净删 assert（150 删 / 71 增）**：几乎全部来自 `test_gate_freshness.py`（-1092 行）——**勾框豁免层
  （`_normalize_checkbox_lines`/`_tasks_content_exempt`/tasks 内联豁免段）删除后对应测试退役**，是
  design 明文批准的删除功能配套退役（design.md「测试迁移」+ Migration Plan），非弱化断言。新增
  锚（rebase 免疫、归档 40-hex SHIPPED、anchor_writeback 执行级、字节保真 round-trip）均带 mutation
  证明（task1-content-anchor-fix1.md）。
- 结论：无「加 skip / 改测试配置 / 删除或弱化断言」蒙混过关。

## 验收复选框

- [x] 单元测试证据齐全并通过（2580 passed @ 40585ab）
- [x] 集成测试证据齐全并通过（同一 pytest 套件覆盖，含真跑 bash 集成用例 @ 40585ab）
- [x] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）——记「未覆盖（本仓无此层）」+ 判定依据
