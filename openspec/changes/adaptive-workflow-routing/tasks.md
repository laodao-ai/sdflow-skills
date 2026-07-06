# Tasks — adaptive-workflow-routing（Q1=A 收敛版）

> 变更性质：一个语言感知的「无逻辑面形状」判器（Python + pytest）+ `sdflow-code-review/SKILL.md` Step2 接入 + `spec-workflow` code-review 需求 MODIFIED。
> 〔Q1=A〕原前向机制任务（route.py 三层归口/四谓词/托管块/calibrator）**已随设计门收敛删除**。
> 每任务 commit 用 `bash ~/.sdflow/hack/checkpoint-commit.sh adaptive-workflow-routing:task<N>-<slug>`。

## 1. 无逻辑面形状判器（核心）

- [ ] 1.1 新建判器脚本 `sdflow-init/assets/workflow/tools/<判器>.py`：读 `git diff <base>..HEAD`，**语言感知**判三白名单形状（①注释/纯文档-only ②仅新增 `tests/`（排除生产码 import 的 helper）③纯展示版本常量整行匹配拒附加 token）；**行为面路径豁免清单**（`assets/workflow/**`/编排评审 `SKILL.md`/`workflow.md`/`ship_gate.py`/判器自身 → NOT 无逻辑面）；沿 `ship_gate.py` 纪律（只读/git-harden `core.quotePath=false`+`errors=replace`/双输出 human+JSON/`--change`+`--root` 纯参数无写盘）；**保守默认**：不支持的语言/拿不准 → 判 NOT 无逻辑面 [spec-workflow: code-review 两层（MODIFIED）]
- [ ] 1.2 pytest 反例矩阵：注释+逻辑混改 hunk 不误判无逻辑面（块注释/多行字符串边界）；**改 `SKILL.md`/`workflow.md` 一行→行为面路径命中→NOT 无逻辑面**；`API_VERSION=2`/`SCHEMA_VERSION`（load-bearing）不判版本常量；`conftest.py`/被 import 的 test helper 不入 tests/ 豁免；纯注释-only/纯 tests/-only/纯展示版本号→命中；不支持语言→保守 NOT [spec-workflow: code-review 两层]

## 2. SKILL 接入

- [ ] 2.1 `sdflow-code-review/SKILL.md`：Step2 fan-out 前调判器——命中白名单形状 ∧ Step1 scope-drift 无隐藏逻辑 → 免 Step2（报告注明「无逻辑面豁免」）；否则 Step2 照跑；措辞明确「默认开、仅机判无逻辑面才关，非高风险才跑」+ Step1 恒跑守卫 [spec-workflow: code-review 两层]

## 3. delta 复核 + 部署

- [ ] 3.1 按代码实况核 `specs/spec-workflow/spec.md` delta（MODIFIED 沿用原标题「sdflow-code-review 为每次全跑的独立强制主审」，保 OpenSpec 定位）与落点一致；`openspec validate adaptive-workflow-routing` 通过 [spec-workflow]
- [ ] 3.2 开发 checkout 跑 `bash setup.sh`（改 assets/workflow 才让全局 canonical 生效、测得到）；hand-off 记「merge 后 push→运行 checkout /sdflow-upgrade」[spec-workflow: bundle 权威源]
- [ ] 3.3 issues sweep：把 Q1=A 放弃的前向机制里仍有价值的想法（如「更宽轻量化需先解 diff-时序/HR-TG 机判」）+ 冷审 defer 项记入 todolist 留档 [/sdflow-todolist]

## 测试覆盖图（TG-18）

| code path | 测试类型 | 用例 |
|---|---|---|
| 语言感知形状判定 | 单元·反例矩阵 | 1.2：注释+逻辑混改/块注释/多行字符串 |
| 行为面路径豁免 | 单元·反例 | 1.2：改 SKILL.md/workflow.md → NOT |
| 版本常量 load-bearing 守卫 | 单元·反例 | 1.2：API_VERSION/SCHEMA_VERSION |
| tests/ helper 排除 | 单元·反例 | 1.2：conftest.py |
| 白名单正例 | 单元·正例 | 1.2：纯注释/纯tests/纯版本号 |
| SKILL Step2 接入 | 人工·走查 | 2.1（Markdown 编排类无自动化） |
