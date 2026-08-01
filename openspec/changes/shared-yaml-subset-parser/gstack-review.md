# gstack-review · shared-yaml-subset-parser

<!-- sdflow:step1-broad-review v1 mode="native" -->

## autoplan 广审结果（CEO + Eng + DX 综合）

### Codex CEO Voice Findings（10 条）

| # | Finding | 严重度 | 置信度 | 自动决策 |
|---|---------|--------|--------|---------|
| C1 | "零依赖"被重新定义——yq 是运行依赖，setup.sh 不中止=假成功 | HIGH | 高 | [自动决策] 接受 finding，但降级为 MEDIUM：proposal 已明确说明 yq 同 git 是系统工具层级，setup.sh 不中止是套用既有降级范式（skipped[]），非"假成功"——已有其他依赖（python3）亦如此。需拍板：是否改为 fail-closed |
| C2 | 版本约束内部矛盾——design 写 v4.53+，检测只查 mikefarah 不查版本号 | HIGH | 高 | [自动决策] **采纳**。spec 应增加最低版本检查（R1 的 scenario 缺版本门）[spec-review-amendment] |
| C3 | 多文档 YAML——json.loads(stdout) 假设单值 | MEDIUM | 中 | [自动决策] 降级为 INFO：config.yaml 和 frontmatter 都是单文档，spec R3 scenario 已说"yq 正常处理"但本 change 消费的文件均单文档，不影响实际场景 |
| C4 | duplicate-key 检测——dict 丢了重复键溯源 | MEDIUM | 高 | [需拍板] Q1：ship_gate.py 现有 duplicate-key 检测确实在手搓解析时发现，yq 读 dict 后已消失。需确认是否接受此行为退化或增加 yq stderr 解析 |
| C5 | yq -i 是文档重写非精确替换——缺 fidelity contract | LOW | 中 | [自动决策] 接受为已知边角（decision-memo 已记录注释位置微调为接受的边角）|
| C6 | subprocess 开销和失败模式——无超时、无遥测 | LOW | 低 | [自动决策] 降级为 INFO：yq 执行 <100ms，config.yaml 只读一次，不在热路径。按通则④简化处理 |
| C7 | yq 表达式注入风险——f-string 直接插值 | HIGH | 高 | [自动决策] **采纳**。`_yq(f'.schema = "{new_schema}"', ...)` 应改为参数传递或验证。spec 应补 security scenario [spec-review-amendment] |
| C8 | 安装策略忽略企业现实 | LOW | 低 | [自动决策] 降级为 INFO：本工具的目标用户是开发者个人开发机，非企业气隙部署。按通则④低概率低影响 |
| C9 | PyYAML/共享解析器被意识形态否定 | MEDIUM | 中 | [自动决策] 否决 finding：decision-memo D1 已详述三候选比较理由，非意识形态——共享解析器仍需维护手搓代码，PyYAML 消费仓不保证可用。基准5已有判据 |
| C10 | 成功指标优化删除而非可靠性 | MEDIUM | 高 | [自动决策] **部分采纳**。Success Metrics 应增加第5条：yq 安装 + 端到端基本读写验证 [spec-review-amendment] |

### 接地镜 Findings（1 条待验）

| # | Finding | 严重度 | 状态 |
|---|---------|--------|------|
| G1 | yq `--front-matter=extract/process` 选项——本机未安装 yq 无法验证 | MAJOR | ⚠️ 需 impl 首步验证 |

### 自动决策小结

- **采纳**：C2（版本门）、C7（表达式注入）、C10（成功指标）
- **需拍板**：C4（duplicate-key 退化）
- **降级/否决**：C1（降 MEDIUM）、C3（降 INFO）、C5（已知边角）、C6（降 INFO）、C8（降 INFO）、C9（否决）

## [gstack-amendment]

根据自动决策的采纳项，以下修订应在设计门后执行：

1. **spec R1 增加版本门 scenario**：`WHEN yq 版本 < 4.16.0（--front-matter 支持下限）THEN 输出版本过低警告 + 升级指引`
2. **design §1 `_yq()` 封装增加值验证或参数化**：写操作的 expression 中嵌入的 value 应经过验证，或改用 yq 的 `env()` 函数传值
3. **proposal Success Metrics 增加第5条**：`yq 可用时端到端读写验证通过`
