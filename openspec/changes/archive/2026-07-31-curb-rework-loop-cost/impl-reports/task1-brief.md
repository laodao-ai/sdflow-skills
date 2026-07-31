### Task 1: 配置分档与单一盘面条款（①②）

**Blocked-by:** none
**R-ID:** IO-1

在 sdflow-implement 和 sdflow-init/sdflow-devenv 中落地 test-suites 成本分档（②）与中间轮/收口轮范围分离（①）。

配置模板侧：sdflow-init 的 config.template.yaml 增加 test-suites 的 quick/full 两档示例与注释，保持字符串形状为合法子集。

消费语义侧：sdflow-implement SKILL.md 的「聚合套件发现契约」写入分档消费规则——字符串 ⇒ 两档同命令；映射 ⇒ 读 quick/full，缺 quick 记该层无 quick 档（unit 层例外：缺 quick 取 full，MUST NOT 跳过），缺 full 视为未分档（quick=full）。具体命令由 sdflow-devenv 运行时调研写入，本处只定义消费规则。

单一盘面条款侧：改写 sdflow-implement SKILL.md 的中间轮/收口轮范围——中间 fix 轮 = unit 全层 + 上轮失败用例（⊂ unit 层，结果仅供诊断）；收口 = 全量且所有通过行锚同一最终 SHA。写入「范围 MUST NOT 由『哪层受影响』判断界定」且「要求为该判断写明依据不构成缓解」。全仓 grep 清除「受影响层」提法。

devenv 侧：sdflow-devenv SKILL.md 增加 test-suites 发现与写入能力段落——运行时调研项目的测试基础设施，推荐 quick/full 分档命令写入 config.yaml 的 test-suites；已有配置时保留不覆盖。

- [ ] config.template.yaml 增 test-suites quick/full 两档示例
- [ ] sdflow-implement 聚合套件发现契约写入分档消费语义（含 unit 层例外）
- [ ] sdflow-implement 单一盘面条款改写（中间轮/收口轮分离 + 取消受影响层）
- [ ] sdflow-devenv SKILL.md 增 test-suites 发现与写入能力段落
- [ ] 全仓 grep 确认无残存「受影响层」提法

