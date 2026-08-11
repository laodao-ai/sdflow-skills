# Task 2 impl-report: 四源采集器 + facts 输出 + advance 门

**R-ID:** R1, R2, R3
**Ticket:** Task 2（tickets.md，Blocked-by 1）
**范围声明**：在 Task 1 骨架上实现四源采集逻辑（gstack / matt / superpowers / openspec）、
facts JSON 输出、`advance` 报告+facts 双参数绑定门。SKILL 编排正文、`sdflow-upgrade` 消费端、
README 登记属 Task 3，未在本票触碰。

## 做了什么

### 1. 通用 git 子进程小工具

- `_rev_parse` / `_assert_is_ancestor` / `_git_log_delta`（`--pretty=%H\t%s` 可控格式串 +
  `--name-only` 提取，零解析上游内容，基准 5）。
- `_ensure_bare_cache(cache_dir, upstream_url)`：matt / superpowers 共用的 blobless bare
  缓存层。**关键实测坐实**（design.md TD2 文字写的是「HEAD」语义）：bare clone **不会**
  自动配置 `remote.origin.fetch` refspec，裸调用 `git fetch origin`（无 refspec）只落
  `FETCH_HEAD`、**不会**前移本地 `refs/heads/*`——若照此实现，`log 锚..HEAD` 永远读不到新
  提交（HEAD 语义死锁）。实测验证后改为显式 `fetch origin '+refs/heads/*:refs/heads/*'`
  （`+` 前缀允许非快进强制更新，对齐「上游可能 force-push」场景），令裸仓 `HEAD` 真实前移。
  fetch 失败 → 删缓存重 clone 一次自愈，再失败才 `CollectError`（原因文案含缓存路径）。

### 2. gstack 采集器（`collect_gstack`）

既有 checkout `fetch origin` + `merge-base --is-ancestor` 锚祖先守卫 +
`log --name-only 锚..FETCH_HEAD`。checkout 缺失 → `CollectError`「本地 checkout 不存在」。
无持久锚（首轮）→ 以本地 checkout 现有 `HEAD` 为天然锚，出真 delta。

### 3. matt 采集器（`collect_matt`）

bare 缓存 `log --name-only 锚..HEAD` + `.skill-lock.json` 键路径断言（仅校验
`source == "mattpocock/skills"` 的条目须含 `skillFolderHash`，其余来源的 skill 不是断言
目标——避免把 vercel-labs/skills 等其他来源的形状差异误报成 matt 的格式漂移）。
`.skill-lock.json` 文件缺失 = 无辅助信息（非错误，与「格式漂移」是两条不同分支）。
无持久锚 → 「无锚 ⇒ 当前上游态即基线」零 delta。

### 4. superpowers 采集器（`collect_superpowers`）

`installed_plugins.json` 键路径断言 + 多 scope 取值策略（优先 `scope=user`，无则
`_version_sort_key` 数值化 token 排序取最大——特意用 `"1.9.0"` vs `"1.10.0"` 的测试用例
证明不是词典序，因为词典序会把 `"1.9.0"` 误判为更大）+ marketplace bare 缓存追踪：
`log --reverse 锚..HEAD -- .claude-plugin/marketplace.json` 圈定触碰该文件的 commit
（**MUST NOT 用 `plugins/superpowers` 路径过滤**——design.md 已实查坐实该仓不 vendor 插件
内容，该路径永远不存在），逐 commit `git show <sha>:.claude-plugin/marketplace.json` 读取
superpowers 条目的 `source.sha` 字段（有界 JSON 字段提取，非手搓解析）。`commits` 字段
（advance 门读取转录校验的对象）= marketplace 仓自身的 commit sha 序列；
`source_sha_sequence` = 提取出的 obra/superpowers 被打包 commit 序列（供报告引用，不参与
advance 门校验，因为它不是「facts 里的 commit sha」而是文件字段值）。

### 5. openspec 采集器（`collect_openspec`）

`openspec --version` vs `npm view @fission-ai/openspec version` 版本对照 +
fork 目录（`sdflow-init/assets/schemas/sdflow-spec-driven/`）vs `npm root -g` 定位的上游
安装目录逐文件整字节 sha256 对比（`_diff_dirs_sha256`，changed/added/removed 三分类，方向
按 spec Scenario 明定：`added` = 上游有 fork 没有，`removed` = fork 有上游没有）。
**子项独立降级**：上游 schema 目录定位失败只让 `schema_drift` 子项标 degraded，外层
`status`（版本对照）不受影响——直接对应 spec Scenario「上游 schema 目录定位失败降级」。

### 6. facts 编排 + `collect` 子命令

`collect_all(anchors, *, repo_root, home=None)`：四源经 `_collect_source_safe` 隔离
（`CollectError` / `subprocess.TimeoutExpired` / `OSError` 均转 `{status: degraded, reason}`，
单源失败不传染）。`cmd_collect` 落 `openspec/upstream/.facts/<UTC时间戳>.json`
（`schema_version` + `collected_at` + `sources`），已加 `.gitignore`（根 `.gitignore` 新增
`/openspec/upstream/.facts/`）。

### 7. `advance` 报告+facts 双参数门

`advance <report-path> <facts-path>`（`argparse` 两个 `nargs="?"` 可选位置参数——**未做成
`required` 位置参数**：guard_cwd() 必须永远是第一道检查，Task 1 既有 CLI 测试断言非本仓 cwd
下裸 `advance`（零参）仍走 `CwdGuardError` 分支而非 argparse usage-error；若做成 required，
argparse 会在 `guard_cwd()` 执行前就因缺参报错，破坏既有测试契约）。前置校验：报告存在、
facts 存在且可解析、报告文本包含 facts 中**每源全部** commit sha（零解析子串校验，逐条列出
缺失的 `source:sha`）。校验通过后仅推进 `status=ok` 源的锚（`_observed_anchor`：git 三源写
`anchor_sha=head_sha`；openspec 写 `anchor_version=installed_version`；superpowers 额外携带
`installed_version` 辅助信息），degraded 源逐字保留，更新 `last_run`。`main()` 新增
`AdvanceGateError`（exit 3）与 `AnchorsError`（exit 1，此前 Task 1 遗留未捕获路径一并补上）
两条异常处理分支。

## Global Constraints 对应

- **零解析上游内容**：全部 delta 事实来自 `git log`/`git show`/`npm view`/`npm root -g`/
  sha256 自身输出；`_extract_superpowers_source_sha` 是有界 JSON 字段读取（`json.loads` +
  取键），不是手搓 marketplace.json 语法解析器。
- **advance 双参数绑定**：见上「7」。
- **采集失败按源降级、fail-loud、不互相传染**：`_collect_source_safe` 逐源隔离；
  `test_collect_all_single_source_unreachable_others_unaffected` 直接验证。
- **统一数字化超时**：全部新增子进程调用均走既有 `_run()`（唯一入口），沿用
  `SUBPROCESS_TIMEOUT_SECONDS`；`_collect_source_safe` 捕获 `TimeoutExpired` → degraded
  「原因=超时」。
- **is-ancestor 锚祖先守卫**：三个 git 源（gstack/matt/superpowers）取 log 前均先
  `_assert_is_ancestor`；非祖先 → degraded「锚失效」。
- **bare 缓存自愈**：`_ensure_bare_cache` fetch 失败→删缓存重 clone 一次，再失败才 degraded。
- **`installed_plugins.json` 多 scope 取值**：优先 `scope=user`，无则版本最大
  （`_version_sort_key`）。
- **superpowers MUST NOT 路径过滤**：追踪 `marketplace.json` 的 `source.sha` 字段变化序列，
  未使用 `plugins/superpowers` 路径。
- **facts 落 `.facts/` 且 `.gitignore`**：已加。
- **advance 只读 facts、禁网络**：`cmd_advance` 全程只读 `report_path`/`facts_path`/
  `anchors_path` 三个本地文件，未调用 `_run`。
- **git 跟踪产物本机路径 tilde 记法**：本票未产出任何含真实本机绝对路径的 git 跟踪内容
  （测试全部走 `tmp_path`，`anchors.yaml` 实例仅测试临时文件）。
- **测试沙盒化**：四源采集器测试均用真实本地 git 仓（`_make_bare_upstream` 等 fixture，
  非 bare 但可正常被 `--bare` clone，行为等价远程仓、零网络）；仅 openspec 采集器（依赖真实
  安装的 `openspec` CLI / npm registry）用 `monkeypatch` 桩子进程调用，不落地真实网络请求。

## 关键实现决策（design.md 之外，实现级、非承重）

- **advance 的 report/facts 参数用可选位置参数而非 required**：见「7」的详细论证，纯粹是
  为了不破坏 Task 1 既有的「guard_cwd 永远最先检查」CLI 契约，不是对 design.md 的偏离
  （design.md 未规定 argparse 层实现细节）。
- **openspec schema drift 未持久化聚合 digest**：design.md 数据模型段提到
  `schema_fork_digest: <fork 目录聚合 sha256>` 作为 anchors.yaml 字段，但 spec Requirement
  与验收 Scenario 只要求 changed/added/removed 三清单**正确**，未要求持久化聚合指纹作为
  「是否要重新对比」的门控（本实现每轮都全量对比，从不跳过）。按基准 4（不为未测试的推断
  字段增加复杂度）略去该字段，仅推进 `anchor_version`。如后续报告成文/`sdflow-upgrade`
  提醒需要该聚合指纹，属 Task 3 或后续增量，非本票遗漏——已如实在此记录，供后续 Task 判断
  是否需要补。

## 测试

`sdflow-upstream-watch/tests/test_upstream_watch.py`，**58 个用例**（Task 1 原 19 个全部
保留且更新了 1 个因行为变化而需重写的用例，Task 2 新增 39 个），全部沙盒化：

```
$ /usr/bin/python3 -m pytest sdflow-upstream-watch/tests/ -q
..........................................................
58 passed in 4.24s
```

覆盖矩阵（对应 brief 验收清单逐条）：

- gstack：checkout 缺失 degraded；首轮天然锚出真 delta；持久锚 delta；零 delta；
  历史重写（`git checkout --orphan` 强制不相关历史，非「在锚上继续提交」那种仍保祖先关系
  的伪重写）degraded「锚失效」。
- bare 缓存层：clone-when-missing；fetch-when-present；fetch 失败自愈重 clone 成功；
  自愈也失败 → `CollectError` 含缓存路径。
- matt：首轮零 delta；持久锚 delta；历史重写 degraded；`.skill-lock.json` 缺失非错误；
  matt 来源条目缺键格式漂移 degraded；非 matt 来源条目缺键**不**误报（作用域正确性）。
- superpowers：`_extract_superpowers_source_sha` 直接单测（命中/未命中两分支）；首轮零
  delta；`source.sha` 变化序列追踪（含一条无关提交验证 path filter 生效排除它）；
  `installed_plugins.json` 缺失/缺版本键 degraded；多 scope 优先 user；无 user 时数值化
  取最大（`1.9.0` vs `1.10.0` 反词典序用例）；历史重写 degraded。
- openspec：版本对照 + drift 清单正确（`_diff_dirs_sha256` 独立单测 changed/added/removed
  三分类）；上游 schema 目录缺失只降级子项、版本对照不受影响；`openspec` CLI 缺失整源
  `CollectError`。
- `collect_all`：单源失败（monkeypatch matt 抛错）其余三源不受影响；
  `_collect_source_safe` 把 `TimeoutExpired` 转 degraded。
- `advance`：报告缺失拒推 + anchors 不变；报告漏转录 sha 拒推 + anchors 不变（错误信息含
  缺失 sha）；正常推进（多源）+ `last_run` 更新；degraded 源锚逐字保留（先建一份既有
  anchors.yaml 含 matt 旧锚，advance 后核对未变）；首轮（anchors.yaml 不存在）建档；CLI
  层零参数（`main(["advance"])`）在合法 cwd 下走新 gate 分支（非 argparse usage error），
  exit 3，anchors.yaml 未创建。
- R5 不改池不变量：`openspec/issues/` 目录树（含既有条目内容）在一轮 `collect` + `advance`
  前后逐路径比对完全一致。
- facts 形状快照：`schema_version`/`collected_at`/四源 key 齐全、`degraded` 源 `reason`
  透传、`schema_drift` 嵌套结构正确。
- `.gitignore` 含 `openspec/upstream/.facts` 的机械断言（读根 `.gitignore` 真实内容，非
  复述）。

**mutation 验证**（对三处安全关键逻辑逐一「破坏 → 确认对应测试红 → 恢复 → 确认绿」）：

1. 注掉 `collect_gstack` 里的 `_assert_is_ancestor` 调用 →
   `test_collect_gstack_rewritten_history_degrades_stale_anchor` 红（虽然报错分支不同——
   `git log` 自身对不相关 range 报 `Invalid revision range` 而非我们的「锚失效」文案——
   但确认了该测试不是恒真断言，移除守卫后行为可观测地改变）。
2. `cmd_advance` 里 `if missing_shas:` 改 `if False and missing_shas:` →
   `test_cmd_advance_rejects_when_report_missing_a_commit_sha` 红（`DID NOT RAISE`）。
3. `cmd_advance` 里丢弃 `entry.get("status") != "ok"` 判据（只保留 `isinstance` 检查）→
   `test_cmd_advance_preserves_degraded_source_anchor_verbatim` 红（degraded 源的锚被错误
   推进为 `None`）。

三处均已恢复，恢复后完整套件重新跑绿（58 passed）。

## 已知 gotcha（供后续维护者参考）

`git clone --bare` **不会**给远端配置默认 fetch refspec（`remote.origin.fetch` 为空）——
裸调用 `git fetch origin` 只更新 `FETCH_HEAD`，**不会**前移本地 `refs/heads/*`，因此裸仓的
`HEAD`（symbolic-ref 指向 clone 时的默认分支）在后续 fetch 后**不会自动前移**。这与非 bare
`git clone` 的日常直觉相反（本地 checkout 也有同款差异——`collect_gstack` 因此显式用
`FETCH_HEAD` 而非 `HEAD`）。本票在 `_ensure_bare_cache` 里用显式
`fetch origin '+refs/heads/*:refs/heads/*'` refspec 解决（`+` 前缀允许强制非快进更新，
天然覆盖「上游 force-push」场景，配合 `_assert_is_ancestor` 检测该场景并 degrade）。
此实测已写入 `_ensure_bare_cache` docstring；design.md TD2 文字里的「`log 锚..HEAD`」字面
描述若脱离本注记单看，容易让后续实现者踩同一个坑（先用 plain fetch 试一版会发现 delta
永远是空的，因为 HEAD 从不前移）。
