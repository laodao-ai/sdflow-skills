# Tasks — review-tool-followups

> 追溯：任务 ↔ 需求。本 change 只改一个 Requirement「workflow bundle 改在权威源、经部署下发」的两处（review UI 深链 / retire 路径覆盖）。
> 场景锚：`T44` = Scenario「工具链升级路径 setup.sh 亦触发…」+「setup.sh 缺 python3 时 fail-safe…」；`T45` = Scenario「hash 深链落 scoped 首屏」+「空/跨源 hash 回落」+「陈旧深链 404 回落并显形」〔grill〕。

## 1. T44 — retire 自愈接进 setup.sh（P2，基础设施）

- [ ] 1.1 **TDD 红**：在 `sdflow-init/tests/` 加 retire 子命令 CLI 层用例——`init.py retire-hooks` 只调 `retire_hooks()`、不需 `openspec/`、不铺 bundle；断言存量残留被清、fresh 为 no-op、坏 JSON/缺文件 fail-safe。（对应 Scenario「setup.sh 亦触发退役 hook 自愈」的逻辑内核）
- [ ] 1.2 **绿**：`init.py` 给 argparse `mode` choices 增 `retire-hooks`；`run()`/`main()` 路由该 mode 到只调 `retire_hooks()` 的早返回分支（跳过 `osroot` 检查与 `copy_bundle`）。跑 1.1 转绿 + 全量 `pytest sdflow-init/tests/` 零回归。
- [ ] 1.3 `setup.sh`：canonical/hack 刷新之后、Summary 之前加一步 `command -v python3` 探测 → 调 `python3 "$REPO_DIR/sdflow-init/scripts/init.py" retire-hooks`；**fail-safe**——python3 缺失/非零退出打印提示后继续，MUST NOT 因此非零退出或中断安装。（对应 Scenario「缺 python3 时 fail-safe 不阻断安装」）
- [ ] 1.4 文档：README 记一句「`setup.sh`（`/sdflow-upgrade`）现也触发退役 hook 自愈」；如涉 CLAUDE.md `setup.sh` 安装机制段则同步一句（不改托管区块内部）。

## 2. T45 — engine.js 恢复 scoped 深链（P3，功能增强）

- [ ] 2.1 `sdflow-init/assets/workflow/tools/engine.js` `bootstrap()`（`~line 265`）：起手读 `location.hash.slice(1)`，非空则作 initialDir 候选、**过 engine.js:244 既有同源守卫**（`new URL(path, origin).origin === location.origin`）后用之；空/跨源回落现有 `pathname` 逻辑。scope 源优先级 `hash（过守卫） → pathname → 根`。**范围=任意同源路径**（非仅 change/roadmap）。〔grill Q1：删原白名单，复用守卫〕（对应 Scenario「hash 深链落 scoped 首屏」）
- [ ] 2.2 安全：同源守卫拒绝跨源/协议相对 hash（`#//evil.com/x`）；路径遍历（`#/etc/passwd`）由服务器根兜住返 404、不额外白名单。〔grill Q1〕（对应 Scenario「空/跨源 hash 回落」）
- [ ] 2.3 陈旧深链 404：hash 指向已归档/移动目录时 MUST NOT 停在裸报错卡死（侧栏空、无🏠）；回落根 bootstrap（INDEX/全树）**并显式提示**深链失效。〔grill Q3·反静默守卫〕（对应 Scenario「陈旧深链 404 回落并显形」）
      〔grill Q2：原「导航回写 hash」任务删——`navigate(...,true)` 已 `pushState('#${path}')`（engine.js:217），写入侧本就完整，非待做项〕

## 3. 验证与收尾

- [ ] 3.1 **开发 checkout 重跑 `bash setup.sh`**（触及 `assets/workflow/tools/engine.js` 与 `setup.sh` 本身，须重跑才测得到）；确认 retire 步执行、engine.js 已下发。
- [ ] 3.2 T45 手测 / `embedded-test-sop`：`serve.sh` 起服务后断言四态——① `#/changes/…/` 首屏 scoped；② `#/specs/…md` 等任意同源路径亦深链（宽目标）；③ 无 hash / `#//evil.com` 跨源 → 回落全树、不越界 fetch；④ `#/changes/已归档名/` 404 → 回落 INDEX + 显式提示、不卡死。（engine.js 无 pytest，验证方式在此显式兜）
- [ ] 3.3 全量 `pytest`（仓级）零回归。
- [ ] 3.4 issues 回写：T44 / T45 → DONE（关联本 change + commit）；批次 `drop-per-dir-review-stub` 经 `sdflow-issues` reindex 推进完成度。
