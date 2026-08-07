## MODIFIED Requirements

### Requirement: workflow bundle 陈旧遮蔽兜底扫描

`maintain_scan.py` SHALL 检查 `openspec/workflow/` 下是否残留旧版部署产物（判据 = `RULE_MARKERS`：`workflow.md` / `spec-checklists` / `code-checklists` 任一存在，**扩员**〔fix-probe-scan-precision〕：`tools/` 目录与 `lens-metric-contract.md` 残留同为检测对象，及仓根 `hack/checkpoint-commit.sh` 孤儿副本），命中则报告为**残留死件**告警——resolver 已无仓内优先步（见 `spec-workflow`「规则全局解析 resolver」），残留副本对评审不再有生效路径（前置条件：已跑过本版 `setup.sh`；文案 SHALL 带该前置条件，MUST NOT 用无条件绝对断言）。仅报告不删除。judgement（是否删）留人，告警 SHALL 附可直接复制的删除命令。此为 sdflow-init `stale_shadow_warnings` 的**周期性兜底消费者**（init 的检查只在 init/update 动作时跑）。〔grill-amendment〕

**告警文案漂移=已知残差 defer〔spec-review-amendment M3/D6〕**：maintain 抄 init 的告警文案 + checkpoint 孤儿路径（跨脚本复述），R-guard 不机验文案（文案守卫脆），**显式登记为已知残差 defer**（记 todolist），非无声留着。maintain 文案不追求逐字等同 init，只需语义等价（残留死件 + 前置条件 + 删除指引；MUST NOT 含「遮蔽全局 / 显式 pin」旧语义——pin 机制已取消）。

#### Scenario: workflow 下残留规则正文
- **WHEN** `openspec/workflow/workflow.md`（规则本体）存在
- **THEN** 报告「残留死件」小节列出该残留文件，提示其对评审已无生效路径（带「先跑 setup 再判断」前置条件）并附删除指引；MUST NOT 提示「pin 遮蔽全局」

#### Scenario: workflow 仅剩 tools 同样告警
- **WHEN** `openspec/workflow/` 下只有 `tools/`（或 `lens-metric-contract.md`），无规则正文
- **THEN** 「残留死件」小节 SHALL 列出 `tools/` / `lens-metric-contract.md` 残留（判据扩员后不再豁免 tools-only 形态——停铺后它们同为死件，只报规则本体会漏掉最大块的残留）
