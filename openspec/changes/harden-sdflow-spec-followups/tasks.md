## 1. FF-0 未判定路径（spec-workflow）

- [ ] 1.1 [FF-0 未判定路径] 为跨仓目录切换与不可读 change 名增加有界识别，输出无 `permissionDecision` 的 `additionalContext` 审计，且不解析 shell。
- [ ] 1.2 [FF-0 未判定路径] 扩展 hook 单测：错仓不 deny、动态名不静默、审计不自动 `allow`、原三分支和哨兵仍保持。
- [ ] 1.3 [FF-0 未判定路径] 同步 canonical workflow 与入口文案，说明未判定行为及其边界。

## 2. `sdflow-spec` 入口与规则收口（spec-authoring）

- [ ] 2.1 [SA-01] 核验并记录 Codex 当前仅能观察到用户显式触发、无模型 Skill 调用接口的证据边界；修正文案与回归锚。
- [ ] 2.2 [SA-06] 将终审追溯范围改为整个 change 目录，明确 `decision-memo.md` 和 design 指针是合法路径，并测试该口径。
- [ ] 2.3 [SA-15] 订正 T132 的 A/B 收敛信号与漂移行号引用；实现或更新其机械门所需的输入和测试。
- [ ] 2.4 [SA-14] 拆出未启用外派协议、详细诊断、演进依据为按需 references；入口保留必驻执行契约与加载条件。
- [ ] 2.5 [SA-14] 新增入口体量/必驻章节/reference 完整性测试，按 Python Unicode 字符数强制 `SKILL.md` ≤ 18,000。

## 3. 台账与规格同步（spec-authoring）

- [ ] 3.1 [SA-01, SA-06, SA-14, SA-15] 将本 change 的 delta 同步进 `openspec/specs/`，并更新 T232–T238、T240–T242 的状态/备注；T239 保持未处理。
- [ ] 3.2 [SA-01, SA-06] 复核归档期已修正的 T232、T238、T240、T241，确保台账只关闭真实完成项。

## 4. 验证与安装

- [ ] 4.1 [FF-0 未判定路径, SA-14] 跑 hook、canonical-entry、sdflow-spec failure/agent、体量门与 issue 相关 focused pytest。
- [ ] 4.2 [FF-0 未判定路径, SA-14] 跑 `python3 hack/sync_principles.py --check`、`bash setup.sh`、`git diff --check`，核验全局安装后的 hook/skill 状态。
- [ ] 4.3 [FF-0 未判定路径, SA-14] 跑全量 `uv run --with pytest pytest`，记录实际结果与任何既有失败。
