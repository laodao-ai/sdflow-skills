# gstack-review — complete-openspec-170-followup

<!-- sdflow:step1-broad-review v1 mode="native" -->

autoplan 原生执行（Skill 机制直接跑，非子代理模拟）。佐证：autoplan preamble 确实执行、codex exec 真实调用。

## CEO Review Findings

### Finding 2a: `--json` 输出稳定性假设未显式声明 [Medium]

P3 从文本解析切到 `archive --json` 读 `warnings[]`。CLI 未声明该 JSON schema 是否为稳定 API。
虽然 JSON 严格优于文本匹配，但应在 design 中注明所依赖的字段名（`warnings`），以便 CLI 升级时定位影响面。

**建议**：design.md 改动 4 加一句注明依赖的 JSON 字段。

### Finding 3a: 中文遗留格式 fallback 无显式 sunset 立场 [Medium]

设计保留中文遗留格式 fallback（D6），但未说明这是永久接受还是独立 roadmap 项。
六个月后会有人问「为何不直接迁移遗留 spec」。

**建议**：Non-Goals 或 decision-memo 加一句迁移立场声明。

### 接地镜结果

8 项代码事实引用全部核验通过，无不符项。

## CEO Consensus

6/6 dimensions CONFIRMED（Claude + Codex 一致）。
Codex voice 未提出额外 strategic concern。

## Decisions (auto-decided, 登记进 spec-review 决策登记区)

- [自动决策] D-AP1: P2+P3+Q2 scope 正确，不拆不合 — P1/P2 principle
- [自动决策] D-AP2: 两个 Medium findings 均为文档缺口，不阻塞 — P6 principle
