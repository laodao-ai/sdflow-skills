# tasks — drop-per-dir-review-stub

> 每个任务 commit 步用命名空间标签：`bash ~/.sdflow/hack/checkpoint-commit.sh drop-per-dir-review-stub:task<N>-<slug> "<msg>"`（gate 主锚契约）。
> 定位脚本用仓根相对路径，勿硬编码绝对路径。仓级 pytest 基线不回归。

## Task 1：init.py `RETIRED_HOOKS` 反注册机制（TDD，ADR-1）

- [ ] **1.1** 写失败测试 `sdflow-init/tests/`（新增或并入 test_init.py）：构造临时 HOME，预置 `~/.claude/hooks/change-review-stub.py` + `~/.claude/settings.json`（PostToolUse.Bash 含该 hook 命令 + 另一条无关 hook）→ 跑反注册 → 断言：该脚本文件删除、settings.json 里该条被摘除、无关 hook 保留。
- [ ] **1.2** 补 edge 测试：settings.json 不存在 → no-op 不崩；fresh（从未装）→ 全 no-op；同一 hook 多条 → 全摘。
- [ ] **1.3** 跑测试确认 FAIL（机制未实现）。
- [ ] **1.4** 实现 `RETIRED_HOOKS = ["change-review-stub.py"]` + `retire_hooks()`（surgical 摘除 + 删文件 + fail-safe on 坏 JSON），在 `run()` 主流程 init/update 都调用；报告追加一行「退役 hook：…」。
- [ ] **1.5** 跑测试确认 PASS。
- [ ] **1.6** commit：`checkpoint-commit.sh drop-per-dir-review-stub:task1-retire-hooks "init: RETIRED_HOOKS 反注册机制 + 测试"`

## Task 2：删 change-review-stub hook（生产者 ①）

- [ ] **2.1** 从 `init.py` `HOOKS` 列表移除 change-review-stub 项（保留 ff0-branch-guard）。
- [ ] **2.2** 删 `sdflow-init/assets/hooks/change-review-stub.py`。
- [ ] **2.3** 删 `sdflow-init/tests/test_change_review_stub_hook.py`；`test_init.py` 里断言该 hook 被**安装**的片段改为断言其被**反注册**（与 Task 1 呼应）。
- [ ] **2.4** 跑 `pytest sdflow-init/tests/` 全绿。
- [ ] **2.5** commit：`checkpoint-commit.sh drop-per-dir-review-stub:task2-drop-hook "移除 change-review-stub hook + 注册项 + 测试"`

## Task 3：删 roadmap gen_review_stub（生产者 ②）

- [ ] **3.1** 删 `sdflow-roadmap/scripts/gen_review_stub.py`。
- [ ] **3.2** 删 `sdflow-roadmap/tests/test_gen_review_stub.py`。
- [ ] **3.3** 改 `sdflow-roadmap/SKILL.md`：去掉调用 gen_review_stub 生成 `roadmaps/<name>/review.html` 的那一步及相关说明（保留 roadmap 其余流程）。
- [ ] **3.4** 跑 `pytest sdflow-roadmap/tests/` 全绿。
- [ ] **3.5** commit：`checkpoint-commit.sh drop-per-dir-review-stub:task3-drop-roadmap-stub "移除 roadmap gen_review_stub + 测试 + SKILL 步"`

## Task 4：文档同步

- [ ] **4.1** 改 `sdflow-init/SKILL.md`：去掉 change-review-stub hook 的铺设/描述；若列全局 hook 处，改为只列 ff0-branch-guard。
- [ ] **4.2** 改 `openspec/ROADMAP.md`（约 36 行）顺带提及 change-review-stub 的那句（改为只提 ff0-branch-guard，或删除该并列）。
- [ ] **4.3** commit：`checkpoint-commit.sh drop-per-dir-review-stub:task4-docs "SKILL/ROADMAP 去每目录 stub 与退役 hook 描述"`

## Task 5：全量回归 + 收敛

- [ ] **5.1** 跑仓级 `pytest`，确认无回归（尤其 init/roadmap 两套）。
- [ ] **5.2** 手验：临时项目 `openspec new change demo` 后 `changes/demo/` 无 review.html；根锚 `serve.sh` 打开仍可导航（能力不退）。
- [ ] **5.3** 回填本文件复选框；commit：`checkpoint-commit.sh drop-per-dir-review-stub:task5-green "全量回归绿 + 复选框回填"`
