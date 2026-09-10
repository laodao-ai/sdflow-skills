# 未启用外派协议

> 仅当真人用户明确要求重新评估或启用 `sdflow-spec` 外派时读取。默认阶段一不外派；
> 本文件存在不代表外派已启用，执行方 MUST NOT 自行启用。

## 1. 当前状态与启用边界

SA-07 派发链路实测可用，但同一真实 change 的 A/B 比较未观察到外派更便宜，且冷审 finding
不优于薄编排；验收门因此回退到主 session 亲查、亲写。三个 agent 定义与 installer 守卫仅作为
未启用资产保留。样本为 N=1，不具统计显著性。

`sdflow-spec/agents/` 仍会被 `setup.sh` 铺进全局 `~/.claude/agents/`；未启用只约束本管线，
不代表定义不可见。移除定义时必须先删源目录，再在新版 installer 上运行 `bash setup.sh` 清理孤儿链接。

## 2. 名册与派发契约

| 用途 | `subagent_type` | 档位 | 工具边界 |
|---|---|---|---|
| 仓内检索 | `sdflow-local-researcher` | light | 无联网工具 |
| 联网调研 | `sdflow-web-researcher` | light | 无仓库读取、无 `Bash` |
| 单产物成文 | `sdflow-spec-writer` | mid | 无判断权；缺口返回 blocker |

启用后每次派发必须满足：

1. 使用 `subagent_type`，**MUST NOT 用 `agentType`**。
2. `model` 填 resolver 输出的字面值；Agent 工具实测只接受 `sonnet|opus|haiku|fable`。
   完整版本化 id 会触发 `InputValidationError`；MUST NOT 猜别名，MUST NOT 填变量名。
3. 每一次派发的 prompt 除本次任务外，MUST 把完整托管区块（`sdflow:principles` 从 `start` 到 `end`）
   原文整段复制进去；MUST NOT 转述、摘要或只给指针，MUST NOT 依赖 agent 定义中的副本。

判断层永不外派：方案推荐、承重约束是否站稳、纪要撰写与终审裁决仍由主 session 完成。

## 3. 联网查询的出境边界

给 `sdflow-web-researcher` 的查询 MUST 只含公开问题本身，**MUST NOT 含**仓库路径、代码片段、
内部标识符、项目或客户专名、配置值与凭证；结合本仓代码的推理由主 session 完成。

查询先写入临时文件，再预检并扫描：

```bash
[ -x ~/.sdflow/hack/outside-voice.sh ]
~/.sdflow/hack/outside-voice.sh secret-scan --context-file <查询文件>
```

- helper 不可执行：拒发，先在运行 checkout 运行 `bash setup.sh`。
- `exit 0`：唯一放行码。
- `exit 3`：拒发，且 MUST NOT fallback；重写查询后再扫。
- `exit 2`：扫描未完成，拒发；**没扫成 ≠ 干净**。
- **其余任何非 0 退出码一律拒发**；**MUST NOT 把「不是 3」读成「没命中」**。

复用上述共享 scanner，MUST NOT 在 `sdflow-spec` 内维护第二份密钥规则表。

## 4. 降级与名册诊断

agent 定义不可用时由主 session 亲查或亲写，**MUST NOT 用通用子代理**；通用 agent 工具面更宽，
这种 fallback 等于降级即提权。

若定义已由 `setup.sh` 铺设但当前 session 报 not found，原因可能是 agent 名册在 session 启动时加载。
先在运行 checkout 运行 `bash setup.sh`，然后新开一个 session，二者缺一无效。完整问题归因与报告格式见
[`degradation-ladder.md`](degradation-ladder.md)。
