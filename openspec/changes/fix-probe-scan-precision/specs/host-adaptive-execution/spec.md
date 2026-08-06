## REMOVED Requirements

### Requirement: 落锚/调 emitter 前探 tools 能力，陈旧则 fail-loud 降级〔spec-review-r2 C3+D1 统一 skew 策略〕

**Reason**：该需求的**保护对象已不存在**。它防的是「bundle 内 SKILL（symlink 即时生效）与 tools（copy，须 `sdflow-init update` 刷新）更新不原子」窗口，而本 change 取消了消费仓的 `tools/` 副本与 resolver 的仓内优先步 ⇒ tools 与 SKILL 此后恒来自**同一个运行 checkout 的文件树**（`~/.sdflow/workflow` 在 Unix 是指向它的软链、在 Windows 是存其路径的指针文件），`git pull` 一次两者同时变。**没有「拷贝」这个动作，就没有「忘了拷」这件事** ⇒ 无窗口可探。

三条补充理由（详见 `adr/0039`）：
- **它不是正确性机制，是省钱机制**。窗口真发生时，旧 tools 会自己 fail-closed 退出（`anchor_lint.py` 契约块读不出 → exit 2「绝不回落硬编码」；`hr_tg_intersect.py` catalog 段缺失 → `EmitError`「不静默按空集放行」）⇒ 评审结果不会错，代价只是跑到末步才发现。该需求的全部价值是把这个「响」从末步提前到起手，省一轮算力。
- **其净收益为负**。一个省钱机制误报一次的代价 = 成功一次的收益（都是一轮评审）；该探测至今**真阳 0 次、假阳 1 次**（`T270`：信号②的 `sed` 无行首锚定命中散文，假阴，差点硬停整轮评审而 bundle 实际是新的）。
- **它结构上无法被机械守**。判据是写在 SKILL 散文里的 grep 命令，验证「命令还对不对」需从 markdown 抠命令 = 手写 markdown 解析器（撞 CLAUDE.md 基准 5）。

**Migration**：
1. 两个评审 SKILL（`sdflow-code-review` / `sdflow-spec-review`）第零步的 skew 探测段**整段删除，不做任何替代**。删除 MUST 早于「停止铺设 `tools/`」（见 design.md 的 Migration Plan）——反序会让每个消费仓每轮评审永久硬停。
2. **残余失效模式由 tools 自身的 fail-closed 承接**，不再有起手拦截。该降级是**有意的**：把「省一轮算力」这个从未兑现的收益，换掉「探测器自身误报」这个已实证一次的代价。
3. **`--host` / `runner="none"` 两个具体罢工症状不再需要专门探测**——它们只在「旧 tools × 新 SKILL」下出现，而该组合此后不可达。同 Requirement 内关于新 emitter `parse_known_args` 受控 fail-closed 的约束**已在其自身位置独立成立**（护「新 emitter × 旧调用方」方向），不随本需求移除而失效。
4. **Windows 上「旧 SKILL × 新 canonical tools」不被本需求或任何替代机制覆盖**——Windows 无 symlink，`setup.sh` 用 `cp -r` 装 SKILL ⇒ SKILL 是 setup 时快照而 canonical 指活 checkout。该面**结构上不可自举**（检查者只能是 SKILL 自己或 `~/.sdflow/hack/` 的 helper，二者同为一次 `cp -r` 的产物，没跑 `setup.sh` 就一起旧）。**已知且接受的边界，MUST 如实登记，MUST NOT 声称本 change 消灭了全部分发链失鲜。**
