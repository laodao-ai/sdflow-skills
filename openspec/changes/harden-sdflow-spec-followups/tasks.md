## 1. FF-0 未判定路径（spec-workflow）

- [x] 1.1 [FF-0 未判定路径] [spec-review-amendment] 实现完整匹配的单条直接 literal 调用 allowlist；未命中但含创建字样时统一输出带 `command-unverifiable` 的 `additionalContext`，无 `permissionDecision`，且不解析 shell 或推测细分原因；删除 `undecided_reason`、动态 marker、双分支说明及仅为旧分类存在的正则，保留 `CHANGE_NAME_RE` 的 stacking 用途与多调用 deny。
- [x] 1.2 [FF-0 未判定路径] [spec-review-amendment] 同步 `sdflow-init/tests/test_ff0_branch_guard.py` 与 `hack/tests/test_canonical_entry_sync.py`：直接 grammar 的空白/引号/`--json` 进入原门禁；非直接形态的代表性 `cd`/wrapper/compound/decoy/变量/替换/glob 统一断言单一 `command-unverifiable`、无 `permissionDecision`；保留原三分支/哨兵/多调用行为，不维护 shell 形态交叉分类矩阵或旧原因码兼容断言。
- [x] 1.3 [FF-0 未判定路径] 同步 canonical workflow 与入口文案，说明未判定行为及其边界。

## 2. `sdflow-spec` 入口与规则收口（spec-authoring）

- [x] 2.1 [SA-01] 核验并记录 Codex 当前仅能观察到用户显式触发、无模型 Skill 调用接口的证据边界；修正文案与回归锚。
- [x] 2.2 [SA-06] 将终审追溯范围改为整个 change 目录，明确 `decision-memo.md` 和 design 指针是合法路径，并测试该口径。
- [x] 2.3 [SA-15] [spec-review-amendment] 只订正 T132/T234 的 A/B 收敛信号、漂移行号与未来 gate 输入契约；添加台账/契约回归锚，明确不得在本 change 实现或关闭 T132。
- [x] 2.4 [SA-16] 拆出未启用外派协议、详细诊断、演进依据为按需 references；入口保留必驻执行契约与加载条件。
- [x] 2.5 [SA-16] [spec-review-amendment] 新增入口体量/resident-contract/reference 完整性测试：按 Python Unicode 字符数强制 `SKILL.md` ≤ 18,000，并逐项锚 frontmatter、Phase 0/A/B/C、C.1 四判、终审、strict validate、两个 checkpoint、出口三步及每个 reference 的加载条件/相对路径。

## 3. 台账与规格同步（spec-authoring）

- [x] 3.1 [FF-0, SA-01, SA-06, SA-16, SA-15] [spec-review-amendment] 将 delta 同步进主规格，并按 closure matrix 更新台账：T232/T238/T240/T241 仅在归档 artifact 证据复核通过后关闭；T233–T237/T242 仅在本 change 对应实现与测试通过后关闭；T234 在 A/B 输入订正后关闭；T132 保持 OPEN、T239 保持未处理。
- [x] 3.2 [FF-0, SA-01, SA-06, SA-16, SA-15] [spec-review-amendment] 增加逐 ID 的 focused 断言，核状态、证据备注与 T132/T239 不得关闭，防 schema/reindex 通过但语义误关。

## 4. 验证与安装

- [x] 4.1 [FF-0 未判定路径, SA-16] 跑 hook、canonical-entry、sdflow-spec failure/agent、体量门与 issue 相关 focused pytest。
- [x] 4.2 [FF-0 未判定路径, SA-16] [spec-review-amendment] 跑 `python3 hack/sync_principles.py --check`、`python3 sdflow-init/scripts/init.py update --root . --dev`、`bash setup.sh`、`git diff --check`；比对 canonical hook 与 `~/.claude/hooks/` 内容/settings 注册、Claude/Codex skill symlink（Windows 比内容/hash）。相关 `skipped` 或不一致均判失败。
- [x] 4.3 [FF-0 未判定路径, SA-16] 跑全量 `uv run --with pytest pytest`，记录实际结果与任何既有失败。

## Test Coverage Map

```text
[spec-review-amendment] FF-0
├── direct literal grammar ─────────────── allowlist variants + original branch/ack tests
├── multiple calls ────────────────────── existing stacking deny regression
└── command unverifiable ──────────────── cd/wrapper/compound/decoy/variable/substitution/glob → same context only

[spec-review-amendment] sdflow-spec resident contract
├── len(SKILL.md) <= 18,000 ───────────── boundary fail/pass
├── resident token map ────────────────── each mandatory semantic anchor required
└── references ────────────────────────── path exists + loading condition remains in entry

[spec-review-amendment] ledger/install
├── T132/T232-T242 closure matrix ─────── per-ID status/evidence assertions
├── init.py update --dev ──────────────── hook copy + settings registration
└── setup.sh ──────────────────────────── skill symlink/copy + skipped treated as failure
```
