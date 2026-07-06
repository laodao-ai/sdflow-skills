## code-review 报告 — sdflow-init-hardening

冷独立强制主审（每次全跑）。diff base = 分支点 `fdaab8b`（origin/main 落后本地 main，显式取分支点排除 P0 roadmap 噪声）。

### 命中范围
- 栈: dev-tooling + python 数据类 skill。清单: 通用 CR-01~09 + python 数据类项。
- **trivial_shape 判器**: NOT_EXEMPT（`init.py`/`setup.sh` 有 logic-line）→ 照跑多镜。
- **gstack/review（Step1 原生）**: scope-drift 无（6 文件全在 T21/T22/T48/T49 声明 scope 内，无顺手多改）；完成度 = 4 项计划全建。
- **HR-TG 判定**: 命中 **TG-26（并发/共享可变状态）**——T49 settings.json 跨进程读-改-写正是入选判据（数据损坏、难回退）→ 单开领域 cross-model（codex, site=hr-tg）。
- 镜: 领域×1 + 对抗×3（并发/资源/错误路径）+ 历史×1 + code outside-voice(codex) + hr-tg cross-model(codex)。
- config `metrics.enabled=true` → 落 lens-metric 锚。

### Findings（置信 ≥80）

| # | 严重度 | 问题 | 证据 | 裁决 |
|---|---|---|---|---|
| **F-A** | 高 | **T21 naive collapse 不安全**：`inject` 收敛 first-start..last-end 在本仓（marker-示例满仓的 workflow-doc 仓）会 ① 命中 ``` 代码块内演示的 marker → **劫持注入**（注入块塞进 fence、演示内容销毁，同 MEMORY `gate-substring-detection-dogfood` 类）② 孤儿 start 无配对 end 时二次 run **跨吞用户内容**（静默数据丢失）③ 反序 end 残留。**实证坐实** F1/F3。 | `init.py:inject`；adv3+codex#1+domain 三源收敛 | **采纳**[impl-review-fix]：**回退 collapse**，保留安全的 offset-misanchor 修 + 单块替换；正确的 fence-aware+配对多块收敛 **defer→T63**（本仓 fence-aware 解析已有，复用之） |
| **F-B** | 高 | **`ensure_global_hook` 畸形 settings 裸崩**：注册遍历 `entry.get`/`h.get`/`name in (...or"")` 遇非 dict entry/非 str command → AttributeError/TypeError，而 `run()` 每次 init/update 都调它 → 崩安装流程。与 `_deregister` 的 CR-F1 守卫**不对称**。**实证坐实**（AttributeError: 'str' object has no attribute 'get'）。 | `init.py` 注册遍历；codex code-voice#2（独家） | **采纳**[impl-review-fix]：抽 `_register_hook_in_settings_locked`，遍历用 `isinstance` 守卫 + `_hook_command`（对齐 CR-F1 口径） |
| **F-C** | 高 | **T49 锁只覆盖 deregister 半边**：`ensure_global_hook`（register）仍**非原子**（`open("w")` 先 truncate 再写 → 进程中途死丢 settings.json）+ **不持锁**（与 deregister 并发 lost-update：基于旧 snapshot 写回 → 复活退役 hook/丢当前 hook）。 | `init.py` register 写路径；hr-tg(高)+codex#3+adv2-B+domain 四源收敛 | **采纳**[impl-review-fix]：抽共享 `_atomic_write_settings`（tmp+os.replace）；register 也走 `_acquire/_release_settings_lock` + 原子写，与 deregister 同口径对称硬化 |
| **F-F** | 中 | **setup.sh 只校验首个候选**：python3 存在但版本不符时直接跳过、不 fallback 到合格的 `python`。 | `setup.sh`；codex code-voice#4（独家） | **采纳**[impl-review-fix]：改**逐候选迭代**（python3→python）取首个 3.6+ |
| **F-D** | 低 | `_release_settings_lock` 的 `flock(LOCK_UN)`/`os.close` 罕见 OSError（EBADF/EINTR）可逃逸——retire-hooks CLI 模式无 `run()` 外层兜底 → 打断 RETIRED_HOOKS 循环 + 裸 traceback。 | `init.py:_release_settings_lock`；adv2-C（独家） | **采纳**[impl-review-fix]：swallow OSError（`os.close` 恒 finally 执行，fail-safe 与 FB-3 一致） |
| **F-E** | 低 | T48 f-string 版本契约注释紧贴 T49 `import fcntl`，视觉上像在注释该 import（两不同关注点）。 | `init.py` 头；domain#1（独家） | **采纳**[impl-review-fix]：两块间加空行分隔 |

### 已裁掉（反静默压制，可审计）
- **X1**（adv3，信息级）：setup.sh 中 python 因非版本原因崩溃（segfault/坏 wrapper）时被文案标"非 3.6+"——**裁掉**：结果正确且 fail-safe（安全跳过、非致命），仅文案不精确；adv3 自身判"非 bug、可不改"。属保守正确行为。
- 各对抗镜「refuted」的攻击点（lockfile 串行化失效/unlink 竞态/fd 泄漏/with-open use-after-close/自死锁）：全部经实证或代码追踪证伪，一行带过、不静默丢——**锁设计经三镜攻击未破**。

### 修复 / defer 台账
- **自动修 6 项[impl-review-fix]**：F-A（回退不安全 collapse）· F-B（register 崩溃守卫）· F-C（register 锁+原子写对称硬化，抽 `_atomic_write_settings`/`_register_hook_in_settings_locked`）· F-D（`_release` fail-safe）· F-E（注释空行）· F-F（setup.sh 候选迭代）。
- **defer 2 项 → todolist（批次 sdflow-init-hardening）**：
  - **T63**：inject 多块收敛须 fence-aware + start/end 配对校验（修 F1/F2/F3 根因，复用本仓 fence-aware 解析）。
  - **T64**：`_atomic_write_settings` tmp 改 `tempfile.mkstemp` 唯一名（关闭无锁降级路径并发 tmp 撕裂，低优先）。
- **T10 三级协议**：F-A 的「回退 vs 就地做安全 collapse」——有客观判据（回退后既有 TestInjectMarkerMigration + 新单块测试全绿、且不引入 F1/F2 数据丢失面），自动选**回退+defer 正确实现**（三镜：系统=不 ship 比病更糟的药；用户=杜绝本仓劫持注入/丢内容；开发循环=fence-aware 实现留完整 change 做，不塞进轻量批）。主：安全优先于功能完整。
- **测试**：新增/改 F-A 单块测 · F-B 畸形不崩 · F-C register 持锁+原子 · F-F fallback；全量 `-W error` 119 passed 零 warning；全仓 479 passed / 1 pre-existing（B5，main 亦红，worktree 核实）。

### 度量锚（lens-metric，config `metrics.enabled=true`）
<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="TG-26" evidence="T49 settings.json 跨进程读-改-写-replace = 并发共享可变状态,数据损坏难回退" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="" findings="4" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="codex" reason_code="" findings="1" truncated="false" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="1" sev="致0/高2/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="5" 采纳="3" 裁掉="1" defer="1" 独立="1" sev="致0/高2/中0/低2" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="2" sev="致0/高3/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="hr-tg" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中0/低0" -->

### 结论
- ☑ 建议进 `/sdflow-done`（verify → hand-off → archive → commit → merge）。
- ☑ defer 残差已入 todolist（T63/T64，批次 sdflow-init-hardening，hand-off 会引用）。
- **冷主审 load-bearing 再次兑现**：初版 4 项 scope 中，T21 collapse 是「比病更糟的药」（被冷对抗镜实证 F1/F2 揪出），且冷镜四源收敛揪出 T49 只做半边（register 未硬化）+ ensure_global_hook 崩溃面——热生成循环全未察觉。

<!-- ship-gate: code-review=pass -->
