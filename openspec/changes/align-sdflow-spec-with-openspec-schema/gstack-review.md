# autoplan 广审 · align-sdflow-spec-with-openspec-schema

<!-- sdflow:step1-broad-review v1 mode="native" -->

> 原生执行 autoplan（CEO + Eng 双镜，各由 fresh-context 子代理独立完成）。
> 佐证：两个子代理分别在独立上下文中读四件套 + 实际代码，无交叉。
> Codex 不可用（CLI auth 命令不兼容），标记 `[subagent-only]`。
> UI scope: 否。DX scope: 否。Phase 2 (Design) 与 Phase 3.5 (DX) 跳过。

## Findings

### F1 [CRITICAL] `handle_config()` 的 update 模式 no-op 与迁移方案的「自动切换」叙事直接矛盾

**命中镜**: CEO + Eng（独立命中，高置信）

**证据**: `sdflow-init/scripts/init.py:311-320`：
```python
def handle_config(root, mode):
    """init: 缺则从模版生成，存在则报告需合并。update: 不动。"""
    if mode == "update":
        return ("skip", "update 不动 config.yaml…")
```
测试 `test_plain_update_does_not_deploy_rules` 亦守此不变量。

然而 proposal.md 第 34 行写「下游随下次 `sdflow-init update` 自然切换」；design.md 的决策图（88-114 行）显示 update 无条件「铺 schemas/ + 切 config.schema」。tasks.md 2.1-2.6 也未列「改写 `handle_config` 的 update 分支以 patch `schema:` 键」。

**影响**: 所有已初始化的下游项目（正常情况）跑 `sdflow-init update` 后 `schema:` 键不会变——静默失效。Success Metrics 1/2 对预存消费仓永远无法达成。本仓 dogfood 步骤（task 4.2）同样受影响——本仓已有 config.yaml，`mode=update`。D1 决策"成本极低"的事实基础被动摇。

**建议**: 实现前补一段设计，明确 `schema:` 键的机械改写机制（如 marker 区块局部覆写），并加对应 task + 测试。

### F2 [HIGH] hook 拦截方案（本仓已有先例）从未被列入候选集

**命中镜**: CEO

**证据**: `ff0-branch-guard.py` 是一个 PreToolUse hook 机械拦截先例（fail-closed）。decision-memo 列了 6 个候选，唯独缺「用 hook 拦截 `/opsx:ff` 调用」——这对「不会想到去查」失效模式恰恰是最直接的机械解法。

**建议**: 补进候选集并写取舍理由。若两者互补（schema 覆盖 Codex，hook 在 Claude 提供机械层），应明确说明。

### F3 [HIGH] Success Metrics 只证「管道通」不证「问题解决」

**命中镜**: CEO

**证据**: 5 条指标中唯一测行为的 #2 只有一次性手工试跑（task 4.4），而假设表自己承认「无实测锚，属提示层」。一次成功不能对概率性行为提供统计置信度。

**建议**: 坦白说明「本次验收只证管道机制正确」，或补多模型/多次抽样指标。

### F4 [HIGH] 无消费侧 schema 验证——只有版本地板，没有后向核验

**命中镜**: CEO + Eng

**证据**: `schema validate` 只在 bundle 作者侧跑一次。下游 CLI 升级到 2.x 可能改变 `schema.yaml` 解读方式，冻结的 fork 会静默失效。F1-F7 表和 5.1-5.7 测试均未覆盖此场景。

**建议**: 在 `sdflow-init` copy_bundle 后加 best-effort `openspec schema validate <name>`（非 fatal），surfacing diagnostic。或在 bundle 留 CLI 验证版本注记 + 主版本升级时重验 C1-C14。

### F5 [HIGH] 回滚说明无机械守卫——已钉死的在途 change 会被 schema 目录删除静默打坏

**命中镜**: Eng

**证据**: design.md 194 行的「回滚…MUST 保留 schema 目录直至 change 归档」是纯 prose MUST，无 enforcement。`git revert` 会删 `openspec/schemas/sdflow-spec-driven/`，而已钉死的 `.openspec.yaml` 仍指向它。

**建议**: 加预回滚检查脚本（grep 在途 `.openspec.yaml` 中的 fork schema 名），文档化为步骤而非 prose MUST。

### F6 [MEDIUM-HIGH] 委派区块剥离——被称「确定性操作」却零自动化测试

**命中镜**: Eng

**证据**: SA-17(a) 称剥离是「确定性操作」（基准 1），但它实现在 SKILL.md 指令层，无 `scripts/`。tasks.md 自己承认「诚实边界…没有自动化测试面」。未来 SKILL.md 编辑可能静默打坏 marker 字面量或顺序。

**建议**: 至少对静态 fork schema 内容加 CI 可检的不变量（marker 对存在于恰好 4 个 artifact），部分弥补指令层无测试的缺口。

### F7 [MEDIUM] 优先级标注不一致——`requires` 改密标 P1 但自认价值「变薄」

**命中镜**: CEO

**证据**: proposal.md TG-19 标 P1；decision-memo D6 写「CLI 图密不密在实际产出路径上无影响」。实质是防御纵深（P2 附近），非核心价值。

**建议**: 调整措辞或降级标注。

### F8 [MEDIUM] CLI 版本字符串比较未定义——semver 解析与 edge case 未 spec

**命中镜**: Eng

**证据**: task 2.1 只写 `< 1.7.0`，未定义解析规则。naive 字串比较会误判 `1.10.0` vs `1.7.0`。binary 缺失 / 非数字输出 / rc 后缀的行为也未定义。

**建议**: spec 里明确 semver 三段比较 + 不可判定时 fail-closed + 加测试。

### F9 [MEDIUM] 迁移扫描可能误补非 change 目录

**命中镜**: Eng

**证据**: 扫描 `openspec/changes/*/` 只检查缺 `.openspec.yaml`，不验证目录是否为真实 change。tasks.md 5.2 只测 happy path。

**建议**: 补一道门（如检查 `proposal.md` 存在）；加一个 stray 目录不被触碰的测试。

### F10 [MEDIUM] Codex 宿主委派有效性是开放问题，被推迟到设计门之后

**命中镜**: CEO

**证据**: 开放问题表写「Codex 宿主下…未验」，截止=实现期首个 ticket 前。但 bundle 面向所有宿主下发。

**建议**: 提前到设计门内做一次手工试跑锚，或明确把 Codex 侧效果划入 Non-Goals。

### F11 [MEDIUM] 根问题（绕过拷问）无真实事故引用

**命中镜**: CEO

**证据**: Why 全文是失效模式推演，未引用一次真实发生的绕过事故。D6 已承认收益「变薄」。

**建议**: 补真实事故引用，或把改动定性为「低成本保险」而非「修复已发生失效」。

### F12 [LOW-MEDIUM] glob artifact 的 capability-name → path 推导缺规范化规则

**命中镜**: Eng

**证据**: SA-17(b) 从 proposal Capabilities 标题推导路径，无 slug 化规则。空格/非 ASCII/`..` 可能造出非预期目录名。Windows 大小写折叠也是风险面。

**建议**: 定义一条规范化规则 + 加冲突测试。

## 自动决策登记

| # | 决策 | 分类 | 原则 | 理由 |
|---|------|------|------|------|
| D1 | 接受 CEO+Eng 双镜的 F1 判定 | mechanical | P1(completeness) | 两镜独立命中同一代码路径，置信极高 |
| D2 | 接受无 Codex 降级（subagent-only） | mechanical | P6(bias toward action) | Codex CLI auth 不可用，Claude 子代理已覆盖 |
| D3 | 跳过 Design/DX 阶段 | mechanical | P3(pragmatic) | 本仓无 UI/前端/DX scope |

## 降级记录

- Codex voice: `[codex-unavailable]`（CLI auth 命令不兼容）
- 模式: `[subagent-only]`（CEO + Eng 各一个 Claude fresh-context 子代理）
