### Task 4: code-checklists 吸收五类缺口并新建 LLM 领域清单

**Blocked-by:** none
**R-ID:** SW-1

把与第三方 skill 逐条比对后确认的五类真空缺口落进本仓清单体系：base 层补命令/代码注入与
枚举取值完备性两条；backend 领域补 DB 层竞态一条、并给既有条目补上服务端模板渲染的 XSS
检查点；另建 LLM 领域清单收纳「代码消费 LLM 产出」这一面的输出信任边界与 prompt 一致性。
措辞一律语言无关、示例放括号里，避免把清单钉死在某个技术栈上。

新领域要真正被选中，须同时在触发目录里有对应触发条目、在清单注册表里有登记、在选用规则
示例里有映射行——三处缺一它就是孤儿。触发措辞收窄到「代码消费 LLM/agent 产出并持久化/
执行/外呼」，并带排除句，防止本仓每次改自己的锚行工具都字面命中。

ID 一律新号，不复用不重排。

- [ ] base 清单含新条目：命令/代码注入（shell 串插值 → 参数数组；eval/exec 执行模型或外部输入生成的代码须沙箱/白名单）
- [ ] base 清单含新条目：枚举/取值完备性（新值逐消费者 trace 且明写「必须读 diff 外代码」；allowlist 数组核对；case 链 fall-through 到错误默认）
- [ ] backend 领域含新条目：DB 层竞态（find-or-create 无唯一索引 / check-then-set 原子 WHERE / 状态迁移非原子 / 绕过模型校验直写）
- [ ] backend 既有 XSS 相关条目扩点覆盖服务端模板渲染场景，并注明客户端框架面待 frontend domain（不声称覆盖）
- [ ] 新建 LLM 领域清单，含输出信任边界（持久化/外发前格式与 shape 校验、URL allowlist 防 SSRF、入库防存储型 prompt 注入）与 prompt 一致性（1-indexed、工具声明与 wiring 一致、限额单一声明）两条
- [ ] 清单注册表登记 LLM 领域行（extends base，ID 前缀 `CR-LLM-`）
- [ ] 选用规则示例块含 `TG-27 → llm.md` 映射行
- [ ] 触发目录领域清单段含 TG-27 行，措辞为「代码消费 LLM/agent 产出并持久化/执行/外呼」，含排除句，且行内注明 code-review-only domain
- [ ] 触发目录 HR-TG 成员行追加 TG-27，且 `hr_tg_intersect.py` 实跑能正确 parse 出该成员（零代码改动）
- [ ] 全部新条目为新 ID，未复用或重排既有 ID

