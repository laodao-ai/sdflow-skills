# hand-off — review-tool-followups

> verify 之后 / archive 之前产出，随归档留档。异步人类再入口 + 下个 change 种子。

## ✅ 完成了什么（每条经 verify 锚点核实）

- **T44 退役 hook 自愈接进 setup.sh**（P2）：
  - `init.py` 加 `retire-hooks` CLI mode，**早分支先于 osroot 检查**（`init.py:434` choices + `:440-442` 早 return，早于 `run()` 的 `_die`）——从无 `openspec/` 的 cwd 跑也不崩（A4/NEW-3）。
  - `_deregister_hook_in_settings` 改**原子写**（temp + `os.replace`）+ 写路径 **OSError fail-safe**（`init.py:316-323`，FB-3 加固）。
  - `setup.sh:164-171` retire 段：`python3 || python` 探测（A6，Windows）+ `{ … } || echo` 尾式 fail-safe（A5，set -e 不中止）。
  - **不对称原则**：安装侧 `ensure_global_hooks` 未随之进 setup.sh（清除主动伤害 eager / 新增拦截钩子 opt-in）——`grep -c`=0 验证。
  - 测试：`TestRetireHooksCli` + 原子写/OSError fail-safe + `test_setup_failsafe.py`（3 测含绑真 setup.sh 的漂移守卫）。
- **T45 engine.js 恢复 scoped 深链**（P3）：`resolveInitialDir` 同源守卫抽 pathname（A3）+ `#/`→INDEX（A7）+ bootstrap **自派发** loadDir/loadDoc（F-B）+ **probe 归一无尾斜杠目录**（CV-1）+ 404 清坏 hash 防递归（F-D）+ **回落 state 同步**（FB-2）+ notice 专用 DOM 节点（NEW-1）。**真浏览器四态实测**（`verify-manual-t45.md` + code-review 复验 CV-1/FB-2 via chrome-devtools）。
- **回归**：`pytest sdflow-init/tests/` **106 passed** 零回归。
- **verify**：PASS，核心缺口 0（`verify-report.md`）。

## ⏳ 未完成 / 延后

- **批次 `review-tool-followups`**（`openspec/issues/batches.md` + `issues/INDEX.md`，状态 PLANNED，成员 **T47/T48/T49**）——均 code-review 有意 defer：
  - **T47**（代码质量）engine.js 深链逻辑零单测——抽 `resolveInitialDir`/bootstrap 分派为可注入 mock 补单测。现靠浏览器四态实测兜，无回归网。
  - **T48**（基础设施）`python3||python` 探测无版本校验（可能落 Python2）——**全仓系统性**既有缺口，非本 change 引入。
  - **T49**（代码质量，低）settings.json 原子写仍有并发 lost-update TOCTOU 窗口——RETIRED 幂等下次重收敛，低影响；真解需文件锁。
- **verify Minor 缺口 1 项**：task 1.5① 完整端到端 `bash setup.sh` 残留清除测未单独驱动（清除逻辑已由 CLI 层 + 绑真文件构造测覆盖），可接受。
- **无被延后的 ≥2 方案决策**：设计门 Q-D1/D2/D3 均已批准 A 并实现，非延后。

## ▶ 下一阶段建议

- **批次 `review-tool-followups`（T47/T48/T49）** 可开一个 cleanup change 一起清；优先级 T47（深链回归网，engine.js 唯一验证是手测）> T49（并发 lost-update）> T48（系统性 python 版本守卫，跨多 skill，宜单独规划）。
- T48 是**跨 skill 系统性**项（全仓 python 调用无版本守卫），不宜塞进小 cleanup，建议单列或并入一次工具链健壮性专项。
- 源 change `drop-per-dir-review-stub` 的批次至此**清空**（T44/T45→DONE），该批次可标完成。
