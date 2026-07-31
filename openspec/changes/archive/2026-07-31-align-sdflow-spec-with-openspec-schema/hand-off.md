# Hand-off · align-sdflow-spec-with-openspec-schema

日期：2026-07-31

## ✅ 完成了什么

- project-local schema `sdflow-spec-driven` 已落到 canonical bundle 并下发到 dogfood 副本；四个 artifact 的
  `id`/`generates`、委派区块与目标依赖边可在 `sdflow-init/assets/schemas/sdflow-spec-driven/schema.yaml:5-69`、
  `:228-242`、`:283-349` 核验，真实 `openspec schema validate sdflow-spec-driven` 退出 0。
- `sdflow-init` 已具备数值 semver 版本门、在途 change 原子补写、先迁移后切配置、managed fork 整删重拷、
  权威模板完整性检查及 schema 单键字节保真改写；锚见 `sdflow-init/scripts/init.py:212-314`、`:372-507`、
  `:1019-1070`。
- `sdflow-spec` 相位 C 已覆盖 dependencies 对象列表、requires 优先/fallback、委派段剥离、glob 目标、
  existingOutputPaths、skipped 与具体路径净化；锚见 `sdflow-spec/SKILL.md:412-464`。
- 当前盘面独立定向聚合：`127 passed, 1 skipped`；真实 CLI 的 schema/status/specs instructions/tasks
  instructions 与 change strict validate 均退出 0。证据盘面：`dc67af388a471acbe36d95a83ac7eab65948c304`。
- 人读文档、roadmap P1 与 fork 漂移边界已同步；canonical/dogfood schema 树与 generation-process 当前字节一致。

## ⏳ 未完成 / 延后

- issues sweep 已将本 change 的延后项归入批次
  `align-sdflow-spec-with-openspec-schema`：见 `openspec/issues/batches.md:275` 与
  `openspec/issues/INDEX.md:30`。当前成员为 T264（fork 漂移检测 / 自动 rebase）。
- Task 3.8：终审已写成“判断层兜底”，但尚未明写“降级前提是 schema 已切换”；这是 Minor 文案修补。
- Task 5.6：仅有孤儿清理用例的 mutation red/green 留证，无法证明每条新增用例均先红。
- Task 5.7：全量 `pytest` 历史 90 秒超时 exit 124，用户明确批准停止等待并跳过；**未通过、未假绿**。
- 自动化 e2e：仓内没有可发现的本 change e2e runner；真实 CLI 集成通过不等于 e2e 通过。
- 最新一次 `setup.sh` 重跑曾超时 exit 124；此前 Task 5 有一次 Git Bash setup exit 0，且当前复制结果字节一致，
  但不把后一次超时改写为成功。
- 延后方案决策 1：fork 漂移机械门 / 自动 rebase 本次不做，当前选择一次性 fork + T264 跟踪；原因是 schema
  接口仍 experimental，漂移策略需独立设计。
- 延后方案决策 2：委派遵守不做机械保证，当前选择“STOP + 提示人触发 `/sdflow-spec`”的提示层；原因是
  `disable-model-invocation` 保持不变，自动回流没有可靠宿主级机械信号。

## ▶ 下一阶段建议

- 建议先开一个窄文档修补 change，补齐 Task 3.8 的“schema 已切换”前提，并为该措辞新增精确契约测试。
- T264 建议保持 P2，待 OpenSpec schema 上游发生实际变更或 fork 首次漂移时再开独立 change；不要并入本次收尾。
- 若要消除发布验证残差，单开测试基础设施 change：定位全量 pytest 挂起根因，并定义真实 e2e runner；在此之前
  继续把 full-suite 124 与 e2e 未覆盖显式带到发布说明。
- Roadmap 回填草稿占位：助手返回 exit 3 `NO_ASSOCIATION`，未检测到本 change 的 roadmap 关联标记，因此未生成
  机械草稿。若需回填 `openspec-1.7.0-followup`，请由人确认 P1 行与上述 deferred 后再更新。

## 收尾边界

本次仅完成 Verify 与 hand-off。未 archive、未 commit、未 merge、未 push。
