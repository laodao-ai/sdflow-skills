<!-- [spec-review-amendment] Q1=B：原「瘦身文档 + doc 正则测试」任务被证伪，重写为纯测试新增。
     不改 SKILL.md/workflow.md/ship_gate.py；不动既有测试断言。 -->

## 1. producer→parser 集成测试（TDD）

- [ ] 1.1 在 `sdflow-ship/tests/` 新增测试文件，加 sys.path 注入后 `from ship_gate import TAG_RE`（照既有 `GATE = Path(__file__).resolve().parents[1] / "scripts" / "ship_gate.py"` 约定定位 scripts 目录；`ship_gate.py` 有 `__main__` 守卫，import 无副作用）。（对应 design D4）
- [ ] 1.2 集成用例（命名空间）：在临时 git repo（复用 conftest `repo` fixture 或自建 tmp repo）中调用**真实** `sdflow-init/assets/hack/checkpoint-commit.sh demo:task1-slug "msg"`，`git log -1 --format=%s` 读回 subject，断言 `TAG_RE.match(subject)` 成功且 `group(1),group(2)==("demo","1")`。定位脚本用仓根相对路径（`git rev-parse --show-toplevel`/`parents[N]`），勿硬编码绝对路径。（对应 Scenario「真实脚本产出的 subject 被 parser 正确识别」）
- [ ] 1.3 集成用例（裸格式）：同法调用 `checkpoint-commit.sh task1-slug "msg"`，断言 `TAG_RE.match` 成功、`group(1) is None`、`group(2)=="1"`。（对应 Scenario「裸格式经真实脚本产出仍被识别」）——先跑应red（若测试写法有误）/ 实为回归钉，跑通即 green。

## 2. TAG_RE 负例矩阵

- [ ] 2.1 同文件加负例用例：对 `checkpoint(task1slug)`（无尾 dash）、`checkpoint(DEMO:task1-)`（大写命名空间）、`checkpoint(task-1-)`（编号位非数字）、`checkpoint(:task1-)`（空命名空间）逐条断言 `TAG_RE.match(...) is None`。（对应 Scenario「已知放松类被负例矩阵挡住」）
- [ ] 2.2 用参数化或逐条断言均可；每条注明"该挡住的放松类"（照 design D2 表），使后人改 `TAG_RE` 打破边界时知道红在哪。

## 3. 回归确认

- [ ] 3.1 跑 `pytest sdflow-ship/tests/` 全绿——**含既有 `test_workflow_authority.py` 全部断言不变**（本 change 不改 SKILL.md/workflow.md，既有断言必须仍绿；若某条红说明误动了文档，回退）。
- [ ] 3.2 跑仓级 `pytest` 无回归。本 change 无 `assets/` 权威源改动，无需 `sdflow-init update`；无需重跑 `setup.sh`（仅加测试文件）。
