# code-review 报告 — review-tool-followups

> 阶段三代码评审（sdflow-code-review 编排，每次全跑·独立冷主审）。DIFF_BASE=`2a17eae`(main)..HEAD。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="zero-findings" runner="codex" reason_code="exec-error" findings="0" truncated="false" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="claude-fallback" reason_code="codex-zero-findings" findings="5" truncated="false" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="TG-03/19/23 均不在 HR-TG 子集，不开领域 cross-model" -->

## 命中范围

- **栈**：Python（init.py 原子写 + retire CLI）· Bash（setup.sh fail-safe）· JS（engine.js 深链）。清单：CR-01~09 base + frontend。
- **Step1 gstack/review（native）**：scope-drift **无**（init.py 改动全在计划内）；完成度**齐**（retire 接线 / 深链 / 原子写全 present，spec 6 Scenario 对码通过）。
- **Step2 多镜**：领域/对抗/历史合并镜（CR 全过 + 实测 301 重定向 + git blame）· **code outside voice**：codex（xcrun/git sandbox 失败→空输出→反静默守卫回落）+ claude-fallback。
- **接地**：代码即 ground truth（无接地镜）；engine.js 另有真浏览器四态实测（`verify-manual-t45.md` + 本轮 CV-1/FB-2 复验）。

## Findings（置信 ≥80，全部已修 [impl-review-fix]）

| # | 严重度 | CR | 问题 | 证据 | 处置 |
|---|--------|----|------|------|------|
| CV-1 | Medium | CR-02/对抗 | 无尾斜杠目录 hash（`#/changes/x` 漏尾斜杠，合理输入）→ bootstrap 误判文档 loadDoc → 服务器 301 跟随 res.ok → 渲染目录列表乱码 + 侧栏错显父目录 + 不触发 notice（fetch 视角 200）。**新引入**（旧 pathname 路径保证目录形态） | engine.js resolveInitialDir + bootstrap 分派；实测 301 | ✅ **已修**：bootstrap probe 取重定向后真实路径按形态分派；浏览器复验无尾斜杠→正确 loadDir |
| FB-2 | Medium | 状态一致性 | 404 回落 `replaceState({path:'/'})` 在 loadDoc INDEX 前，成功后 currentPath='/INDEX.md' 但 state.path='/' 不一致 → 点走再 Back，popstate 读 '/' 把 INDEX 静默换裸目录列表 | engine.js:291-294 | ✅ **已修**：回落成功后同步 `replaceState({path:'/INDEX.md'})`；浏览器复验 state.path='/INDEX.md' |
| FB-3 | Medium | CR-01 | `_deregister` 写路径（os.replace）无 try/except，`main()` retire-hooks 分支也无外层守卫 → 只读/满盘 OSError 裸抛 traceback + 中断整个 RETIRED 循环，违「fail-safe 绝不中止」初衷 | init.py:312-317 vs 读路径 fail-safe | ✅ **已修**：写路径捕获 OSError→返 False（与读路径一致）；+ 测试 test_deregister_write_failsafe_on_oserror |
| FB-4 | Medium | CR-09 | test_setup_failsafe 测手抄 snippet 副本、非真 setup.sh → 漂移（改 setup.sh 丢 `\|\| echo` 测试仍绿）。两镜均提 | test_setup_failsafe.py:20-42 | ✅ **已修**：加 test_setup_sh_retire_block_binds_to_real_construct 绑定真文件断言 `\|\| echo`+`python3\|\|python` |

## 已裁掉 / 降级（反静默压制，可审计）

| # | 原始发现 | 裁定 | 理由 |
|---|----------|------|------|
| FB-1 | [HIGH] engine.js 新逻辑零单测 | **降级 → defer todolist** | 真 gap 但**已缓解**：tasks 3.2 明记「engine.js 无 pytest，验证方式显式兜」+ verify-manual-t45 浏览器四态实测 + 本轮 CV-1/FB-2 复验。抽 resolveInitialDir 单测=改进非 bug，defer |
| FB-5 | [LOW] python 探测无版本校验（可能 Python 2） | **裁掉 → defer todolist** | 镜自认系统性既有缺口（全仓 python 调用皆无版本守卫、init.py 本身也无），**非本 diff 引入**；不扩本 change scope，记系统性 todo |
| CV-2 | [conf 40] 原子写仍有并发 lost-update TOCTOU | **<80 过滤 → defer todolist** | temp+replace 已解「撕裂 JSON」（本次目标）；lost-update 因 RETIRED 幂等下次重收敛、低影响；真解需文件锁=过度工程 |
| codex code-voice | 空输出 | **降级非采信** | xcrun/git sandbox 失败=降级伪装 0-findings，按反静默守卫回落 claude-fallback，未当"干净"跳过 |

## 修复 / defer 台账

- **自动修 4 项 [impl-review-fix]**：CV-1（engine.js probe 分派）· FB-2（engine.js 回落 state 同步）· FB-3（init.py 写 fail-safe + 测试）· FB-4（setup.sh 绑定测试）。
- **defer 3 项 → todolist**：FB-1（engine.js 单测覆盖）· FB-5（python 版本守卫系统性审计）· CV-2（settings 并发 lost-update）。
- **voice 分桶（M4 采纳率数据源）**：codex 采纳 0 / 裁掉 0 / defer 0（**降级失败，guard=zero-findings**，未产可用 findings）· claude-fallback 采纳 2[FB-2/FB-3]（FB-4 亦采纳共 3）/ 裁掉 0 / defer 2[FB-1/FB-5]。领域/对抗镜：采纳 1[CV-1] / defer 1[CV-2]。
- **回归**：`pytest sdflow-init/tests/` **106 passed**（+FB-3/FB-4 两测，零回归）；engine.js `node --check` ok + 浏览器四态 + CV-1 无尾斜杠 + FB-2 state 全实测通过。

## 结论

- 4 条 ≥80 findings 全当场修复 [impl-review-fix] 并复验；3 项改进/系统性/低置信 defer todolist（hand-off 会引用）。无未解 blocker。
- 建议进 `/sdflow-done`（verify → hand-off → archive → commit → merge）。

<!-- ship-gate: code-review=pass -->
