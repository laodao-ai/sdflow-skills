### Task 3: token 快照采集

**Blocked-by:** none
**R-ID:** R-TS1, R-TS2, R-TS3

新增 `token_snapshot.py` helper 并在 `checkpoint-commit.sh` 接线，实现 checkpoint 级 token 快照采集。

行为描述：
- 新增 `sdflow-init/assets/hack/token_snapshot.py`（带 4 行 `reconfigure` 前导）
- transcript 定位序：`$CLAUDE_CODE_SESSION_ID` 精确命中 `~/.claude/projects/<munged-cwd>/<id>.jsonl` → munged-cwd 目录 mtime 最新 jsonl 回退 → 无则 `no-transcript` 降级行；session-id 文法校验（basename + `^[0-9a-fA-F-]+$`）后才拼路径
- usage 四计数 + messages 累加（非负整数校验，不过则 `parse-error` 降级行）；字段封闭 schema（只写 spec 列明字段）
- change 目录由分支名解析（无落点静默跳过）
- 追加 v1 行 schema 到 `token-log.jsonl`（整行 buffer 后单次 O_APPEND write）
- 内部自设执行超时（10s，超时放弃采集）
- 全程 try/except 到降级行
- `sdflow-init/assets/hack/checkpoint-commit.sh` 接线：判空 gate 之后、`git add -A` 之前插入 `python3 ~/.sdflow/hack/token_snapshot.py --step "$step" || true`
- 测试（`hack/tests/`）假 HOME 沙盒真跑 bash：正常采集入同一 commit / 无 transcript 写 `no-transcript` 行 / helper 缺席与崩溃时 checkpoint 照常提交 / 无 change 落点零写入 / 连续 checkpoint 只追加且累计单调不减 / 干净树+helper 在场仍 no-op 不建 commit / canary transcript 断言输出面无泄漏
- 重跑 `bash setup.sh` 分发，dogfood 验收：本 change 下一次真实 checkpoint 产出 anchor=true 快照行

- [ ] token_snapshot.py 实现（定位/累加/v1 行/降级/超时/文法校验/封闭 schema）
- [ ] checkpoint-commit.sh 接线（gate 后 add 前）
- [ ] 假 HOME 沙盒集成测试（7 场景）
- [ ] [e2e] setup.sh 分发后 dogfood 验收：真实 checkpoint 产出 anchor=true 快照行
