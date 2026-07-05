# Verify Report — review-tool-followups

- 日期：2026-07-05
- Change：`review-tool-followups`（T44 retire 自愈接进 setup.sh · T45 engine.js 恢复 scoped 深链）

## 结论：PASS

<!-- ship-gate: verify=PASS -->

冷启动、不信复选框/报告措辞，逐条对码核验。T44/T45 的核心功能与 spec 的 8 条新增 Scenario
均有可机验证据锚点；`python3 -m pytest sdflow-init/tests/` **106 passed**；T45 无 pytest 部分由
真浏览器四态实测（chrome-devtools MCP）兜住。3 项 defer（FB-1/FB-5/CV-2）为有意裁减，不计缺口。

## 逐需求核对表

### T44 — retire 自愈接进 setup.sh

| 需求/任务 | 代码出处 file:line / 测试 | 状态 |
|---|---|---|
| `retire-hooks` mode 早分支，先于 osroot/dev（A4/NEW-3） | `init.py:434`（choices 增 `retire-hooks`）+ `init.py:440-442`（早 return，先于 `run()` 内 osroot 检查 356-368） | ✅ |
| clean 无残留静默/单行（A9/BR-8） | `init.py:352` 返回 `无退役 hook 残留`；测 `test_retire_hooks_mode_needs_no_openspec`（init.py 无 banner） | ✅ |
| `_deregister_hook_in_settings` 原子写（temp+`os.replace`，Q-D1/设计门A） | `init.py:316-321`（tmp 写 + `os.replace`） | ✅ |
| 写路径 OSError fail-safe（不裸抛、不断循环，FB-3） | `init.py:322-323`（`except OSError: return False`）；测 `test_deregister_write_failsafe_on_oserror` (test_init.py:580) | ✅ |
| 原子写无 `.tmp` 残渣 / 未撕裂 | 测 `test_settings_write_is_atomic_no_tmp_residue` (test_init.py:568) | ✅ |
| CLI 层：`retire-hooks` 只调 `retire_hooks()`、不需 openspec/ | 测 `TestRetireHooksCli::test_retire_hooks_mode_cleans_stale_hook` + `..._needs_no_openspec` (test_init.py:544,560) | ✅ |
| retire_hooks 存量清除/fresh no-op/坏JSON/缺文件 fail-safe | `TestRetiredHooks`（test_init.py:374-540，含 bad_json/no_settings/malformed/non_string） | ✅ |
| setup.sh：`python3 \|\| python` 探测（A6/BE-10） | `setup.sh:164-166`（`_py` 探测 python3 后 python） | ✅ |
| setup.sh：`\|\| echo` 尾式 fail-safe（A5/F-A，set -e 下 present-but-nonzero 不中止） | `setup.sh:167-171`（`{ "$_py" … retire-hooks ; } \|\| echo …`） | ✅ |
| setup.sh 集成：缺 python3 时 fail-safe / python 探测 / 绑真文件 | test_setup_failsafe.py:4,22,41（`test_retire_snippet_failsafe_under_set_e` / `..._probes_python…` / `..._binds_to_real_construct`，末者断言真 setup.sh 含 `retire-hooks`/`\|\| echo`/`_py=python`） | ✅ |
| 安装侧 `ensure_global_hooks` MUST NOT 进 setup.sh（不对称原则，Scenario 9） | `grep -c ensure_global_hooks setup.sh` = 0；仅在 `init.py:387` | ✅ |
| 文档：README 记 setup.sh/`/sdflow-upgrade` 触发 retire | README.md:66 | ✅ |

### T45 — engine.js 恢复 scoped 深链

| 需求/任务 | 代码出处 file:line / 测试 | 状态 |
|---|---|---|
| `resolveInitialDir`：读 hash → `new URL(raw,origin)` → 同源检查 → 取 `.pathname`（A3） | `engine.js:104-114`（`u.origin===location.origin` → `return u.pathname`；空/跨源回落 pathname） | ✅ |
| initialDir const→computed/let，供 currentPath+popstate 共用（A8） | `engine.js:114`（`let initialDir`）+ `:124` currentPath + `:264-265` popstate 读 initialDir | ✅ |
| `#/`→pathname `'/'`→INDEX 分支（非裸列表，A7/NEW-4） | `engine.js:280-283`（`initialDir==='/'` → `loadDoc('/INDEX.md')`） | ✅ |
| 同源守卫拒跨源/协议相对（`#//evil.com/x`） | `engine.js:108-109`（同源比较，跨源不返 pathname 候选，回落 line 112） | ✅ |
| 自派发调 loadDir/loadDoc（非 `await navigate`，F-B 收 404 信号）；probe 归一目录尾斜杠（CV-1） | `engine.js:286-296`（`fetch(initialDir)`→`!probe.ok throw`→按 resolved.endsWith('/') 分派 loadDir/loadDoc） | ✅ |
| 404 防递归：走 INDEX、MUST NOT 重调 bootstrap、`replaceState` 清坏 hash（F-D） | `engine.js:298-306`（catch → `replaceState({path:'/'},'',pathname)` 清 hash → initialDir='/' → loadDoc INDEX，无 bootstrap() 重调） | ✅ |
| 显式提示专用 DOM 节点、回落渲染后注入、MUST NOT `contentBody.innerHTML=`（NEW-1） | `engine.js:309-312`（`createElement('div')` `.deep-link-notice` + `content.insertBefore(notice, contentBody)`） | ✅ |
| 行为级四态验证（engine.js 无 pytest） | verify-manual-t45.md（chrome-devtools 实测 ①scoped ②任意同源 ③跨源守卫 ④404显形，全 ✅） | ✅ |

### spec.md 8 条新增 Scenario 映射

| Scenario | 出处 | 状态 |
|---|---|---|
| 退役 hook 在存量安装被反注册自愈 | `TestRetiredHooks`（test_init.py:374+） | ✅ |
| 工具链升级路径 setup.sh 亦触发退役 hook 自愈〔T44〕 | setup.sh:160-171 + `TestRetireHooksCli` + `test_setup_sh_retire_block_binds_to_real_construct` | ✅ |
| setup.sh 缺 python3 时 fail-safe〔T44 边界〕 | setup.sh:167-171 + `test_retire_snippet_failsafe_under_set_e` | ✅ |
| setup.sh 只 eager 清退役、不推安装侧拦截钩子〔不对称〕 | `ensure_global_hooks` 0 次现于 setup.sh（仅 init.py:387） | ✅ |
| review UI 根锚 hash 深链落 scoped 首屏〔T45〕 | engine.js:104-114 + verify-manual-t45 态① | ✅ |
| 空 hash 或跨源 hash 回落根锚全树〔T45〕 | engine.js:108-112 + verify-manual-t45 态③ | ✅ |
| 陈旧深链 404 回落根锚并显形〔T45〕 | engine.js:298-313 + verify-manual-t45 态④ | ✅ |
| （承载需求既有：修改规则/新 init/update收敛/--dev/建change不落stub） | 既有测试 test_init.py:98,123,272,309 等，未回归（106 passed） | ✅ |

## 缺口清单

### 核心缺失
- 无。

### Minor（PASS 但注明）
- **完整端到端 setup.sh 集成测（task 1.5 ①：真跑 `bash setup.sh` 后 `$HOME/.claude` 残留被清）**：
  当前以 snippet fail-safe 测 + 绑真 setup.sh 构造测（`test_setup_sh_retire_block_binds_to_real_construct`）
  + CLI 层 `TestRetireHooksCli`（清除逻辑）覆盖，未单独驱动整个 setup.sh 跑一遍验残留清除。清除逻辑本身已被
  CLI 测充分覆盖，属 Minor 测试组织差异，不影响功能正确性。

### 有意 defer（不计缺口，见 code-review-report「已裁掉/降级」区）
- **FB-1**：engine.js 新逻辑抽 `resolveInitialDir` 单测 → defer todolist（已由 verify-manual-t45 浏览器四态实测缓解）。
- **FB-5**：python 探测无版本守卫（系统性既有缺口，非本 diff 引入）→ defer todolist。
- **CV-2**：settings 原子写仍有并发 lost-update TOCTOU（置信 40，<80 过滤；幂等下次重收敛）→ defer todolist。

## 验证证据
- `python3 -m pytest sdflow-init/tests/ -q` → **106 passed in 8.94s**（零回归）。
- T45 真浏览器四态实测 → verify-manual-t45.md 全 ✅。

PASS
