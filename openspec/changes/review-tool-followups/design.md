## Context

`drop-per-dir-review-stub`（archived 2026-07-05）合并时 defer 了两项 code-review 残差（CR-V1→T44、CR-V2→T45），入 todolist 并挂批次 `drop-per-dir-review-stub`。本 change 是该批次收尾。

现状约束：
- **retire 自愈**：`retire_hooks()`（`init.py:319`，ADR-1）已实现——外科式摘 `~/.claude/settings.json` 注册 + 删 `~/.claude/hooks/<name>`，幂等、fail-safe（坏 JSON / 缺文件不崩）、fresh 无残留则 no-op。名单 `RETIRED_HOOKS = ["change-review-stub.py"]`。**唯一调用点**在 `run()`（`init.py:382`，`init`/`update` 都跑）。`setup.sh` 目前**完全不调 init.py**（仅软链 skills + 刷 `~/.sdflow` canonical/hack）。
- **engine scope**：`engine.js:100` 用 `window.location.pathname.replace(/[^/]*$/,'')` 定 initialDir；shell 页自身 location 不变、历史走 hash（`engine.js:105/234`）。故初始 scope 恒为 shell 根（scope=""），不读 hash。
- **CLI 形态**：`init.py` argparse，`mode` 为 positional `choices=["init","update"]`（`init.py:426`）。
- **dev/runtime checkout 纪律**：改 `assets/workflow/tools/`、`setup.sh` 后须在开发 checkout 重跑 `setup.sh` 才测得到。

利益相关方：装了 sdflow-skills 的开发/运行 checkout 机器（受 T44 影响）；跑 review UI 的用户（受 T45 影响）；纯消费机（无 setup.sh，**不受** T44 影响，仍靠 init/update）。

## Goals / Non-Goals

**Goals:**
- 退役 hook 自愈覆盖工具链升级路径（`setup.sh`），堵住 `/sdflow-upgrade` 后到下次 `sdflow-init update` 之间的窗口期。
- 恢复 review UI 根锚的 scoped 深链（`/review.html#/changes|roadmaps/X/` → scoped 首屏），兑现 `drop-per-dir-review-stub` 标注的后续增强。
- 两条 retire 触发路径复用**同一** `retire_hooks()`，零逻辑重写。

**Non-Goals:**
- 不改 `retire_hooks()` 现有清理逻辑与 `RETIRED_HOOKS` 名单语义。
- 不给纯消费机新增 retire 触发路径（它们无 `setup.sh`，现状 init/update 已覆盖）。
- 不回退根锚全树浏览能力；不恢复「每目录物理 stub」（`drop-per-dir-review-stub` 的删除结论不动）。
- 不重建 hash 双向同步的完整路由框架——T45 最小闭环 = **bootstrap 读 hash 定初始 scope**（写入侧 `navigate` 早已回写，见 ADR-2〔grill Q2〕；非待做项）。

## Decisions

### ADR-0〔打包〕T44+T45 合一个 cleanup change（而非拆两套）

**决策**：两项装进同一 change 交付。**三镜 + 主次**：
- **系统镜**：两项功能无耦合（后端自愈 / 前端深链），合一不增系统耦合——各改各的 codepath。
- **用户镜**：对最终用户无差别（都是收尾补齐），合拆不影响感知。
- **开发循环镜**：合一 = 一轮四件套 / 一次评审 / 一次 merge；拆两套要跑两轮、开销翻倍。
- **主次**：本问题是「批次收尾清账」，**开发循环镜（低开销）** 主导，且系统镜无耦合风险背书——故合一。

### ADR-1〔T44〕retire 自愈的路径覆盖 = init.py 独立子命令 + setup.sh 调用

**决策**：给 `init.py` 增独立 mode `retire-hooks`——只调 `retire_hooks()` 并打印其汇总，**不走 `run()` 的 `osroot` 检查 / bundle 铺设**（retire 只动全局 hook 目录，与项目 `openspec/` 无关，早返回分支）。`argparse` 的 `mode` choices 加 `retire-hooks`；`--root` 对该 mode 无意义（可忽略）。`setup.sh` 在 canonical/hack 刷新之后、Summary 之前调用一次 `python3 "$REPO_DIR/sdflow-init/scripts/init.py" retire-hooks`。

**代码事实核验〔grill〕**（design 主张已对 `init.py` 现码验真）：retire 目标目录 = `_home_claude()` = `CLAUDE_CONFIG_DIR or ~/.claude`（init.py:265），**与 hook 安装目标同源**、尊重自定义配置目录（故非死写 `~/.claude`）；`_deregister_hook_in_settings` **仅 `if changed` 才回写** settings.json（init.py:313），clean 机器不重写、无 mtime 抖动 / 并发写风险，「no-op on clean」在文件写层面成立；坏 JSON / 缺文件 / 结构异常均 `return False` fail-safe。

**不对称原则〔grill Q4·退役 eager / 安装 opt-in〕**：本 change 把 **retire** 接进 `setup.sh`，却**刻意不**把 `ensure_global_hooks()`（装 ff0-branch-guard）也接进去——这不是遗漏，是设计立场：
> **清除主动伤害可 eager；新增会拦截的能力须 opt-in。**
- retire 清的死 hook（`change-review-stub.py`）每次 Bash 都 fire 报错、对**任何人**是主动伤害 → 该在最上游必跑路径 eager 清（含只为别的 skill 装 sdflow-skills、不用 OpenSpec 的机器）。
- ensure 装的 ff0（**PreToolUse.Bash 拦截钩子**）只对**用 OpenSpec 工作流**的人有意义、对旁人是未经请求的命令拦截 → 留在 `sdflow-init init/update`（用户显式启用工作流时才装），**不**推给每台 `setup.sh` 机器。
- 伤害/获益画像本就不对称，故 setup.sh 只做「eager 清除」半边，不做「完整 reconcile」。

**为何 (A) 而非替代**：

| 方案 | 复用 retire_hooks | 是否靠人 | 责任/面 |
|------|:---:|:---:|------|
| **(A) setup.sh 调 init.py retire 子命令** ✅ 选 | ✅ 是 | ✅ 焊进必跑机械路径 | setup.sh 多一步（轻） |
| (B) 独立 `sdflow-init cleanup` 命令 | ✅ 是 | ✗ 靠用户记着跑 | 命令面变大，窗口期仍在 |
| (C) 仅 README 要求手动 update | 复用 | ✗ 纯靠人 | 零代码，CR-V1 本质未解 |

(A) 把自愈接进「升级必跑、早于一切 sdflow-init」的机械路径，不靠人，且零逻辑重写——正是 CR-V1 想要的。(B)/(C) 都把责任推回给人，窗口期照旧。

**三镜 + 主次判定〔决策框架〕**：
- **系统镜**：(A) 让 setup.sh 引入对 `python3` 的软依赖（以 `command -v` + fail-safe 兜底，不硬耦合）；(B)/(C) 系统面更小但缺口不闭。
- **用户镜**：CR-V1 缺口的本质是「升级后到下次 update 之间，用户每次 Bash 都被指向已删脚本的**失败 hook 打扰**」——(A) 唯一真正消除该打扰；(B)/(C) 用户仍会撞到失败 hook。
- **开发循环镜**：(A) 焊进机械路径、零未来心智；(B)/(C) 靠人记着跑，未来每次升级都可能漏。
- **主次**：本问题里 **用户镜（失败 hook 直接干扰）＋ 开发循环镜（不靠人）** 压倒系统镜的「少一个软依赖」——因为缺口的伤害面正是用户被打扰、且靠人必漏。故选 (A)，系统镜的代价用 fail-safe 探测消化。

**Windows 降级**（回应 Open Question）：`setup.sh` 有 `IS_WINDOWS` 分支。retire 步 MUST **fail-safe**：`python3` 缺失 / 调用非零退出**不阻断** setup（打印提示后继续），因为 retire 本身是尽力而为的清理，不该让工具链安装因它失败。实现上以 `command -v python3` 探测 + `|| echo "提示"` 兜底。

### ADR-2〔T45〕bootstrap 读 hash 定初始 scope〔grill-amendment〕

**目标（grill 溯源 CR-V2 + 钉宽窄）**：兑现 `drop-per-dir-review-stub` 记为「可接受降级」的深链能力——让根锚 `review.html` 支持「打开深链 URL 直接落到对应视图」，免每次从全树 INDEX 手点进。**范围 = 宽（任意路径）**，非仅 change/roadmap：每目录 stub 已**完全退役**（无活跃生成、根锚全覆盖，仅 6 个死 stub 冻在 `changes/archive/`），**不存在「平价恢复」的窄对象**；且 `navigate`（engine.js:217）本就对任意路径写 `#${path}`，honor 全部路径才顺其既有契约。

**决策**：`bootstrap()` 起手读 `location.hash.slice(1)`——非空则作 initialDir 候选，**过 engine.js:244 既有同源守卫**（`new URL(path, origin).origin === location.origin`）后用之；空/跨源则回落现有 `location.pathname` 逻辑。scope 源优先级 = `hash（过同源守卫） → pathname → 根`。

- **删白名单**〔grill Q1〕：原设计的 `^/(changes|roadmaps)/` 内容白名单**删除**——它与 `navigate` 写出的 hash 契约自相矛盾（会拒绝 app 自己产的 `#/specs/…`、`#/INDEX.md` 回链），且是 security theater：**路径遍历**已由服务器根（`serve.sh` cd openspec/）兜住（`#/etc/passwd`→404），**真正的洞**是协议相对 URL（`#//evil.com/x` 跨源 fetch）——白名单防不住、既有同源守卫（244）恰好防住。故复用 244、不造新白名单。
- **回写非任务**〔grill Q2〕：`navigate(...,true)` 早已 `history.pushState({path},'','#${path}')`（engine.js:217）——写入侧完整，T45 唯一缺读取侧。原 task 2.3「回写 hash」是幻影任务，删。
- **陈旧 hash 404 → 回落 + 显形**〔grill Q3〕：深链指向已归档/移动的 change 时 hash 404，MUST NOT 停在 navigate 裸报错（loadDoc 先 fetch 抛错、未及 loadSidebar → 侧栏空、无🏠、卡死）；SHALL 回落根 bootstrap（INDEX/全树，恢复完整导航）**并显式提示**「深链 X 未找到（可能已归档），已回首页」。遵 CONTEXT 反静默守卫：结论不静默蒸发，静默回落（吞掉「深链没命中」）与假✅ 同构、禁用。

**为何不重建路由框架**：既有 hash 历史机制已在跑，只在 bootstrap 增「读 hash + 同源守卫 + 404 回落显形」一支，增量最小、不引入新抽象。

**三镜 + 主次判定〔决策框架〕**（宽目标 + 复用守卫 vs 窄白名单）：
- **系统镜**：复用既有同源守卫（244）+ 服务器根兜遍历——一致、少码、无新维护面；窄白名单反要额外写码去掐断 app 自己的 hash 契约。
- **用户镜**：round-trip 对**所有**路径成立（specs/INDEX/changes/roadmaps 一视同仁）；陈旧链不卡死、且知道失效（非以为工具坏）。
- **开发循环镜**：白名单是 security theater（挡不住真洞、误伤真链）；静默回落违反静默守卫（仓库铁律）。删白名单 + Q3 显形，二者都往「与既有契约/铁律一致」收。
- **主次**：**系统镜（顺既有 hash 契约与同源守卫）＋ 开发循环镜（反静默守卫不可违）** 压倒「窄到 change/roadmap 的平价直觉」——宽目标更少码更大用、且更安全。

## Risks / Trade-offs

- **[T44 setup.sh 调 Python 增耦合]** setup.sh 原本纯 shell、不依赖 Python 运行时 → **Mitigation**：以 `command -v python3` 探测 + fail-safe 跳过，缺 Python 不阻断安装；retire 是清理增强，非安装必要步。
- **[T44 纯消费机未覆盖]** 无 setup.sh 的纯消费机仍只靠 init/update → **Mitigation**：这是有意边界（Non-Goal），init/update 现状已覆盖它们，不是回归。
- **[T45 无自动化测试]** engine.js 无 pytest，hash 解析改错不会被 CI 抓 → **Mitigation**：tasks 挂手测 / `embedded-test-sop` 明确验证步（打开 `#/changes/X/` 断言首屏 scoped）；改动局限单文件单分支，面小。
- **[T45 跨源 hash 注入]**〔grill Q1 修订〕 hash 来自 URL，可被塞协议相对值（`#//evil.com/x`）→ **Mitigation**：**复用既有同源守卫**（engine.js:244 `new URL(path,origin).origin===location.origin`）拒绝跨源，**不用内容白名单**（白名单误伤 app 自产的 `#/specs/…` 回链、又防不住协议相对洞）；路径遍历（`#/etc/passwd`）由服务器根（openspec/）兜住返 404。

## Migration Plan

1. 实现 + 单测（T44 init.py 子命令 TDD；T45 engine.js hash 分支）。
2. 在**开发 checkout** 跑一次 `bash setup.sh`（触及 `assets/workflow/tools/engine.js` 与 `setup.sh` 本身，须重跑才测得到），验证 retire 步与深链首屏。
3. 合并后：运行 checkout 走 `/sdflow-upgrade`（pull+setup）即获 retire 自愈；消费仓按需 `sdflow-init update` 拉 engine.js 增强。
4. **回滚**：`git checkout <上一良好 commit>` + 重跑 `setup.sh`（改动均幂等、无数据迁移，回滚无残留）。

## Open Questions

- ~~ADR-2 的「导航回写 hash」增量是否纳入~~ →〔grill Q2 已解〕回写早由 `navigate`（engine.js:217）实现，非任务，无待决。
- 合规声明：本 change 无信任边界 / 敏感数据新增、无性能 NFR、无计费服务——规则/边界合规**声明为不适用**。
