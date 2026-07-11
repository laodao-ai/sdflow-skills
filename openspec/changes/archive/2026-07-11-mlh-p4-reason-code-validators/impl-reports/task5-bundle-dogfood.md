# Task 5 — bundle 回灌 + 验收 dogfood（impl report）

**状态：DONE**（末票；三校验器已回灌下游、权威源全套件全绿 0 warning、三校验器对本仓真实产物只读 dogfood 无误报）
**R-ID：** OVG, HRT, RDC · **Blocked-by：** 4（已满足）

---

## 1. setup.sh 同步 canonical

```
$ bash setup.sh
sdflow-skills v0.9.0 ready → ~/.claude/skills ~/.codex/skills
  installed (34): … 全部 ✓
  ✓ workflow @ ~/.sdflow — 接管：~/.skills/sdflow-skills/.../assets/workflow
                            → /Users/cheneyzhao/Documents/04-sdflow-skills/sdflow-init/assets/workflow
  mode: symlink (Unix)
```

要点：无错。全局 canonical `~/.sdflow/workflow` 已「接管」指向**本 dev checkout** 的 `sdflow-init/assets/workflow`（dev checkout 纪律：测完/合并后运行 checkout 重跑 setup 还原）。

## 2. sdflow-init update 推下游（实际调用方式）

按 `sdflow-init/SKILL.md` update 范式，**直接调脚本**（非交互、非 CLI 子命令），plain `update`（非 `--dev`，故排除 `tests/`）：

```
$ python3 sdflow-init/scripts/init.py update --root .
✓ sdflow-init update 完成 @ /Users/cheneyzhao/Documents/04-sdflow-skills
  - 铺 bundle：openspec/workflow/（12 文件，覆盖）
  - 铺 review 根锚：openspec/review.html + openspec/serve.sh（2 文件，覆盖；tools/ 随 bundle 入 openspec/workflow/tools/）
  - config.yaml：update 不动
  - openspec/INDEX.md / CLAUDE.md / AGENTS.md：更新托管区块
```

`init.py copy_bundle` 非 `--dev` 分支对 `tools/` 用 `ignore_patterns("tests")` → 下游 `openspec/workflow/tools/` **不含 tests/**（设计要求）。

## 3. 一致性核对（权威源 ↔ 下游脚本本体）

下游 `openspec/workflow/tools/` 列表：含三新校验器 `hr_tg_intersect.py`/`outside_voice_guard.py`/`review_disposition_check.py` + `anchor_lint.py`（已刷新），**无 tests/ 子目录**（`ls tests` → No such file or directory）。

`diff` 逐脚本本体（auth vs downstream）：

```
IDENTICAL: outside_voice_guard.py
IDENTICAL: hr_tg_intersect.py
IDENTICAL: review_disposition_check.py
IDENTICAL: anchor_lint.py
```

四脚本本体逐字一致；下游无 tests/。回灌纪律满足（MUST NOT 只改下游——本票只经权威源→update 推下游，未手改下游）。

## 4. 权威源全套件（承 4.C 门槛）

```
$ python3 -m pytest sdflow-init/assets/workflow/tools/tests/ -W error -q
183 passed in 0.67s
```

全绿、0 warning（`-W error` 下任何 warning 会转 error 使失败，实测 0 失败）。验收门**指向权威源 tests/**（下游无 tests/）。

## 5. 本仓 dogfood（只读，未改任何产物）

### 5.1 outside_voice_guard（T80）— reason_code 合理，fail-closed 归约正确

对本仓真实 archived gstack-review.md 只读跑。按三前置按序归约（来源 mode > 新鲜度 fs-mtime > 结构 codex 段）：

**① 来源前置命中（simulated-source）** — 两个 simulated-mode 归档产物：
```
$ outside_voice_guard --review-path <4.C lens-metric-emit>/gstack-review.md --change-dir <同>   → simulated-source  exit=1
$ outside_voice_guard --review-path <mlh-p3-determ-guards>/gstack-review.md --change-dir <同>    → simulated-source  exit=1
```
核对源锚：两产物 `step1-broad-review v1 mode="simulated"` 属实 → `simulated-source` 是**正确**判定（adr/0002 simulated 视同无效不可复用），非误报。

**② 新鲜度前置命中（stale，fail-safe）** — 三个 native-mode 归档产物：
```
$ outside_voice_guard --review-path <ship-gate-hardening>/gstack-review.md --change-dir <同>     → stale  exit=1
$ outside_voice_guard --review-path <gate-anchor-line-scoped>/gstack-review.md --change-dir <同> → stale  exit=1
$ outside_voice_guard --review-path <review-tool-followups>/gstack-review.md --change-dir <同>   → stale  exit=1
```
**研判：非误报，是 design.md 明列的 fail-safe。** mtime 排序取证（ship-gate-hardening）：产物 mtime `…642.7320678` vs 源最大 mtime `…642.7327764`（tasks.md），差 ~0.0007s（亚毫秒）——纯 git checkout 写序 artifact。design.md Risk 行「[T80 fs-mtime 跨 git 操作] → checkout 重置 mtime … fail-safe 朝 stale（重跑只成本），可接受」正是此场景。归档产物 mtime 是 checkout 制品、无「活跃编辑」语义，守卫朝 stale 保守（重跑成本、绝不假绿）符合预期。对**活跃 spec-review**（未归档、有真实编辑时序）fs-mtime 才有意义。

无崩溃、无假绿；六枚举里命中的两枚（simulated-source/stale）均为诚实且方向安全的判定。

### 5.2 hr_tg_intersect（T81）— hit + 依据模型判定串跑通

用本 change 模型声明的命中 TG 集（proposal `TG-01,TG-22` + design section 锚 `TG-08,TG-11,TG-23`）+ 权威源 trigger-catalog：
```
$ hr_tg_intersect --tg-set 'TG-01,TG-08,TG-11,TG-22,TG-23' --trigger-catalog sdflow-init/assets/workflow/trigger-catalog.md
hit:[TG-08]｜依据模型判定:[TG-01,TG-08,TG-11,TG-22,TG-23]
<!-- sdflow:hr-tg v1 hit="TG-08" declared="TG-01,TG-08,TG-11,TG-22,TG-23" -->
  exit=0
```
研判：HR-TG 子集单一源（`## 七、HR-TG` `> 成员：TG-04,06,07,08,09,16,17,26`）正常 parse；∩ 得 `TG-08`（唯一命中成员）；`依据模型判定` 使模型给的集显式可见（adr/0018）；扩 `declared=` 锚字段就位。exit 0（hit/none 均合法判定）。跑通、无误。

### 5.3 review_disposition_check（T82）— 真实 task-log 不假阳（子串陷阱验证）

对本仓两个真实 roadmap task-log（均含收尾句「无『未处置』…」，正是子串陷阱 memory `gate-substring-detection-dogfood` 的负例形态）：
```
$ review_disposition_check --task-log openspec/roadmaps/mechanical-layer-hardening/task-log.md   → section-ok-DISPOSITION-UNCHECKED  exit=0
$ review_disposition_check --task-log openspec/roadmaps/workflow-cost-optimization/task-log.md   → section-ok-DISPOSITION-UNCHECKED  exit=0
```
**研判：不假阳（关键验收项）。** 两 task-log 的 `## Review 处置` 小节收尾句含「未处置」子串（`mechanical-layer-hardening:53`「本小节无「未处置」状态条目」/`workflow-cost-optimization:69`「…无「未处置」」），naive-grep 会误判——本脚本靠「小节存在 + 去注释后非空」结构判定绕开自指陷阱，正确输出 `section-ok-DISPOSITION-UNCHECKED`（诚实点明逐条未核，非假绿 present），exit 0。

## 6. 验收标准逐条

- [x] dev setup.sh 同步 canonical；`sdflow-init update` 推下游，权威源↔下游脚本本体逐字一致（下游无 tests/）
- [x] 权威源 tools 全套件 `pytest -W error` → 183 passed、0 warning
- [x] 本仓 dogfood：三校验器各对真实产物只读跑；T82 对真实 task-log **不假阳**
- [x] 验收门 pytest 指向权威源 `sdflow-init/assets/workflow/tools/tests/`（非不存在的下游 tests/）

## 7. Concerns

无阻断性缺陷。两点观察（均 design 已预期、非缺陷）：

- **T80 对归档 native 产物恒 stale**：归档态 fs-mtime 是 checkout 写序制品、无活跃编辑语义，守卫 fail-safe 朝 stale（design Risk 行明列，重跑只成本、绝不假绿）。对活跃 spec-review 场景 fs-mtime 才承载真实新鲜度信号。可接受。
- **update 副作用 diff**：`sdflow-init update` 重注入托管区块时把 `CLAUDE.md`/`AGENTS.md` 的 `<!-- opsx-init:end -->` 后一空行归一（各 -1 空行），benign 排版归一；`openspec/workflow/tools/anchor_lint.py` 下游刷新到权威源版本（+18 行，diff 后 IDENTICAL）。均为 update 正常产物，随本票一并 commit。
