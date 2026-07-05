# Tasks — review-tool-followups

> 追溯：任务 ↔ 需求。本 change 只改一个 Requirement「workflow bundle 改在权威源、经部署下发」的两处（review UI 深链 / retire 路径覆盖）。
> 场景锚：`T44` = Scenario「工具链升级路径 setup.sh 亦触发…」+「setup.sh 缺 python3 时 fail-safe…」；`T45` = Scenario「hash 深链落 scoped 首屏」+「空/跨源 hash 回落」+「陈旧深链 404 回落并显形」〔grill〕。

## 1. T44 — retire 自愈接进 setup.sh（P2，基础设施）

- [ ] 1.1 **TDD 红**：在 `sdflow-init/tests/` 加 retire 子命令 CLI 层用例——`init.py retire-hooks` 只调 `retire_hooks()`、不需 `openspec/`、不铺 bundle；断言存量残留被清、fresh 为 no-op、坏 JSON/缺文件 fail-safe。（对应 Scenario「setup.sh 亦触发退役 hook 自愈」的逻辑内核）
- [ ] 1.2 **绿**：`init.py` 给 argparse `mode` choices 增 `retire-hooks`；路由该 mode 到只调 `retire_hooks()` 的分支——**MUST 在 `main()` 或 `run()` 顶早分支、先于 `osroot` 检查（init.py:356-360 `_die` exit 1）**〔A4/NEW-3：setup 默认 `--root "."`，若从无 `openspec/` 的 cwd 跑、分支又晚于 osroot 检查 → `_die` 叠加 set -e 中止 setup〕。clean 无残留时该路径**静默/单行 dim**、不打印满 banner（A9/BR-8）。跑 1.1 转绿 + 全量 `pytest sdflow-init/tests/` 零回归。
- [ ] 1.3 `setup.sh`：canonical/hack 刷新后、Summary 前加一步，构造 MUST 为 `{ command -v <py> >/dev/null 2>&1 && <py> "$REPO_DIR/sdflow-init/scripts/init.py" retire-hooks ; } || echo "提示"`——**尾 `|| echo` 收尾必需**（`set -e` 下仅 `command -v` 门控或 if-guard 挡不住 present-but-nonzero，then-body 仍被中止，A5/F-A）；**探测 `python3 || python`**（MUST NOT 假设 `python3`——Windows/Git-Bash 常名 `python`，否则 Windows 系统性漏 retire，A6/BE-10/Q-D2）。（对应 Scenario「缺 python3 时 fail-safe」）
- [ ] 1.4b 〔Q-D1·NEW-2·**待设计门批准**〕`_deregister_hook_in_settings`（init.py:313）改**原子写**（temp 文件 + `os.replace`）——T44 把该写接进 `/sdflow-upgrade`、常与活跃 Claude Code 会话并发写 `~/.claude/settings.json`，非原子写有丢更新/撕裂 JSON 风险，且崩后坏 JSON 被 retire 的 fail-safe 读静默 no-op 掩盖。补 1 条测试。（若设计门选 defer → 转 todolist、删本任务）
- [ ] 1.4 文档：README 记一句「`setup.sh`（`/sdflow-upgrade`）现也触发退役 hook 自愈」；如涉 CLAUDE.md `setup.sh` 安装机制段则同步一句（不改托管区块内部）。
- [ ] 1.5 〔spec-review OV-4/BR-1：setup.sh 集成覆盖缺口〕加 2 个 shell 集成测试到 `sdflow-init/tests/`：① temp `$HOME/.claude` 有残留 → `bash setup.sh` 后被清；② PATH 中 fake `python3` 返回非零 → `setup.sh` 仍 `exit 0` 并打印提示（守死 A5 的 `set -e` fail-safe，CLI 层 TDD 覆不到这条集成风险）。

## 2. T45 — engine.js 恢复 scoped 深链（P3，功能增强）

- [ ] 2.1 `sdflow-init/assets/workflow/tools/engine.js` `bootstrap()`（`~line 265`）：起手读 `location.hash`，非空则 `new URL(rawHash, origin)` → **同一 origin 检查**（`.origin === location.origin`）→ **取 `.pathname`**（A3：MUST 抽 pathname 喂 scope，非 raw hash 原样；顺带归一 `%2F`）作 initialDir 候选；空/跨源回落 `pathname`。**范围=任意同源路径**（非仅 change/roadmap）。`initialDir` const→computed/let，一处算 `hash→守卫→pathname` 供 `currentPath`+`popstate` 共用（A8）。〔grill Q1 + spec-review A3/A8〕（对应 Scenario「hash 深链落 scoped 首屏」）
- [ ] 2.2 安全：同一 origin 检查拒绝跨源/协议相对 hash（`#//evil.com/x`）；路径遍历（`#/etc/passwd`）由服务器根兜住返 404、不额外白名单。`#/` → pathname `'/'` MUST 走 `initialDir==='/'` 的 INDEX 分支（非 `navigate('/')` 裸列表），与无-hash 一致（A7/NEW-4）。〔grill Q1 + spec-review A7〕（对应 Scenario「空/跨源 hash 回落」）
- [ ] 2.3 陈旧深链 404〔grill Q3 + spec-review A1/A2/F-D 加固机制，MUST 严格照走〕：**(a) 自派发**——bootstrap 于自己 try/catch 里按 `endsWith('/')` 调 `loadDir`/`loadDoc`（复制 currentPath/pushState 记账），**不能用 `await navigate(hash)`**（navigate 吞错返 undefined、收不到 404 信号，F-B）；**(b) 防递归**——catch 后走 `initialDir==='/'` 的 INDEX 路径、**MUST NOT 重调 `bootstrap()`**，回落前 `history.replaceState({path:'/'},'',location.pathname)` 清坏 hash；**(c) 显式提示**——在回落渲染**之后**、以**专用 DOM 节点** `insertAdjacentHTML`/`appendChild` 注入「深链未找到（可能已归档）」，**MUST NOT `contentBody.innerHTML=`**（会被 loadDoc/loadDir 擦掉 → 提示静默蒸发，NEW-1）。（对应 Scenario「陈旧深链 404 回落并显形」）
      〔grill Q2：原「导航回写 hash」任务删——`navigate(...,true)` 已 `pushState('#${path}')`（engine.js:217），写入侧本就完整，非待做项〕

## 3. 验证与收尾

- [ ] 3.1 **开发 checkout 重跑 `bash setup.sh`**（触及 `assets/workflow/tools/engine.js` 与 `setup.sh` 本身，须重跑才测得到）；确认 retire 步执行、engine.js 已下发。
- [ ] 3.2 T45 手测 / `embedded-test-sop`：`serve.sh` 起服务后断言四态——① `#/changes/…/` 首屏 scoped；② `#/specs/…md` 等任意同源路径亦深链（宽目标）；③ 无 hash / `#//evil.com` 跨源 → 回落全树、不越界 fetch；④ `#/changes/已归档名/` 404 → 回落 INDEX + 显式提示、不卡死。（engine.js 无 pytest，验证方式在此显式兜）
- [ ] 3.3 全量 `pytest`（仓级）零回归。
- [ ] 3.4 issues 回写：T44 / T45 → DONE（关联本 change + commit）；批次 `drop-per-dir-review-stub` 经 `sdflow-issues` reindex 推进完成度。
