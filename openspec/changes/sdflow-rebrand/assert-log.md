# Task 8 断言留档：instance 同步 + 白名单反向断言

顺序：Step 1（`update --dev` 同步）先跑，Step 2（逐名反向 grep 断言）后跑，硬约束不可倒。

## Step 1：`python3 sdflow-init/scripts/init.py update --dev --root .`

命令输出（`update --dev` 的伴随变更——tools/ 刷新、review.html、告警区的「陈旧遮蔽」噪声——属预期，
是本仓自身 dogfood 出来的 `openspec/workflow/` 本地规则副本 pin 场景，不是本次改动引入）：

```
✓ sdflow-init update 完成 @ /Users/cheneyzhao/Documents/04-sdflow-skills

  - 铺 bundle：openspec/workflow/（--dev 整刷）（34 文件，覆盖）
  - 铺 review 根锚：openspec/review.html + openspec/serve.sh（2 文件，覆盖；tools/ 随 bundle 入 openspec/workflow/tools/）
  - hack 脚本：不再铺进仓（checkpoint 已全局化 → ~/.sdflow/hack/，由 setup.sh 安装）
  - 全局 hooks：
  · ff0-branch-guard.py：脚本已最新；已注册（全局）
  · change-review-stub.py：脚本已更新 /Users/cheneyzhao/.claude/hooks/change-review-stub.py；已注册（全局）
  - ⚠ openspec/workflow/ 残留规则副本（workflow.md、spec-checklists、code-checklists）——遮蔽全局 bundle 且不再被 update 刷新：想跟全局最新 → 手动删净；想 pin 这一版 → 留着（显式逃生口）
  - ⚠ hack/checkpoint-commit.sh 为旧版仓内副本（checkpoint 已全局化 → ~/.sdflow/hack/）：本仓无规则副本 → 可删改用全局；若保留本地 workflow.md 副本（pin）且其仍引用仓内路径 → 勿删
  - config.yaml：update 不动 config.yaml（如模版有变，模型按需合并通用段/rules）
  - openspec/INDEX.md：更新托管区块
  - CLAUDE.md：更新托管区块
  - AGENTS.md：更新托管区块
```

### 验证结果

| 检查 | 命令 | 结果 |
|---|---|---|
| workflow.md 与权威源逐字节一致 | `diff -q openspec/workflow/workflow.md sdflow-init/assets/workflow/workflow.md` | 无输出（一致） |
| CLAUDE.md 托管区块唯一 | `grep -c "opsx-init:start" CLAUDE.md` | `1` |
| AGENTS.md 托管区块唯一 | `grep -c "opsx-init:start" AGENTS.md` | `1` |
| INDEX.md 托管区块唯一 | `grep -c "opsx-init:rules:start" openspec/INDEX.md` | `1` |
| 托管区块内容已是新名 | `grep -n "sdflow-spec-review" CLAUDE.md AGENTS.md openspec/INDEX.md` | 命中 4 处（CLAUDE.md 区块内 ×2、AGENTS.md ×2、INDEX.md ×0），均为新名（CLAUDE.md 全文 4 处其中 2 处区块外为 Task 4 既有） |

**Task 2 的 marker token 迁移在此实测生效**：CLAUDE.md / AGENTS.md / INDEX.md 三个文件的旧
`<!-- opsx-init:start —— 由 opsx-project-init 维护 -->` / `<!-- opsx-init:rules:start —— 由
opsx-project-init 维护 -->` 区块被原位替换为新文案（`sdflow-init 维护`），计数均为 1（替换非追加）。

---

## Step 2：逐名反向断言（9 pattern，白名单过滤）

命令（与 brief 给定一致）：

```bash
WL='openspec/adr/|openspec/ROADMAP.md|openspec/CONTEXT.md|openspec/changes/archive/|openspec/issues/|openspec/changes/sdflow-rebrand/|\.superpowers/|docs/|memo-'
for pat in 'opsx-project-init' 'opsx-done' 'opsx-maintain' 'opsx-roadmap-planner' \
           '(^|[^-])spec-review' '(^|[^-])impl-review' \
           'buglist-recorder' 'todolist-recorder' 'issues-recorder'; do
  echo "== $pat =="
  grep -rEn "$pat" . --exclude-dir=.git --exclude-dir=node_modules 2>/dev/null | grep -Ev "$WL" || echo "  clean"
done
```

### 第一轮（修复前，原始输出）

发现两类白名单外命中需要修复（详见下方「修复记录」），其余命中经判读均属合法既有设计。完整原始输出：

```
== opsx-project-init ==
setup.sh:26:OUR_LEGACY_NAMES=" opsx-project-init opsx-done opsx-maintain opsx-roadmap-planner spec-review impl-review buglist-recorder todolist-recorder issues-recorder sdflow-init sdflow-done sdflow-maintain sdflow-roadmap sdflow-spec-review sdflow-code-review sdflow-buglist sdflow-todolist sdflow-issues embedded-test-sop openspec-upgrade sdflow-upgrade "
README.md:34:> | `opsx-project-init` | `sdflow-init` |
sdflow-init/tests/test_setup_sdflow.py:95:        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
sdflow-init/tests/test_setup_sdflow.py:99:        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
sdflow-init/tests/test_setup_sdflow.py:113:    "opsx-project-init","opsx-done","opsx-maintain","opsx-roadmap-planner",
sdflow-init/tests/test_init.py:131:        monkeypatch.setattr(init_mod, "SKILL_DIR", str(root / "opsx-project-init"))
sdflow-init/tests/test_init.py:283:        fake_skill_dir = tmp_path / "some-repo" / "opsx-project-init"
sdflow-init/tests/test_init.py:340:    """0.2：inject() 改 token 基定位——旧 marker 文案（opsx-project-init）区块被替换而非追加重复。"""
sdflow-init/tests/test_init.py:342:    OLD_BLOCK = ("<!-- opsx-init:start —— 由 opsx-project-init 维护，勿手改本区块 -->\n"
sdflow-init/tests/test_init.py:360:    OLD_IDX_BLOCK = ("<!-- opsx-init:rules:start —— 由 opsx-project-init 维护，勿手改本区块 -->\n"
sdflow-init/scripts/init.py:79:    （如 opsx-project-init → sdflow-init），旧区块仍需被命中替换，而不是被判定"未找到"而追加
== opsx-done ==
setup.sh:26:OUR_LEGACY_NAMES=" opsx-project-init opsx-done opsx-maintain opsx-roadmap-planner spec-review impl-review buglist-recorder todolist-recorder issues-recorder sdflow-init sdflow-done sdflow-maintain sdflow-roadmap sdflow-spec-review sdflow-code-review sdflow-buglist sdflow-todolist sdflow-issues embedded-test-sop openspec-upgrade sdflow-upgrade "
README.md:35:> | `opsx-done` | `sdflow-done` |
sdflow-done/SKILL.md:57:> 用 Sonnet 而非 Haiku：verify 是**质量门**且要 grep 代码判 PASS/FAIL、辨核心 vs Minor 缺口，judgment 活，弱模型易误判 PASS 放不完整的活进归档。opsx-done 低频，省那点 token 不值。
sdflow-done/SKILL.md:100:> **为何独立成步、不并进 verify 或 archive**：verify 判"完整性"、hand-off 是"给人的高层交接 + 下阶段种子"，altitude 不同；时机必须在 verify **之后**（引其权威结论）、archive **之前**（随归档留档）。opsx-done 是自制 skill，加此步无碍。
sdflow-init/tests/test_setup_sdflow.py:95:        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
sdflow-init/tests/test_setup_sdflow.py:99:        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
sdflow-init/tests/test_setup_sdflow.py:113:    "opsx-project-init","opsx-done","opsx-maintain","opsx-roadmap-planner",
== opsx-maintain ==
README.md:36:> | `opsx-maintain` | `sdflow-maintain` |
setup.sh:26:OUR_LEGACY_NAMES=" opsx-project-init opsx-done opsx-maintain opsx-roadmap-planner spec-review impl-review buglist-recorder todolist-recorder issues-recorder sdflow-init sdflow-done sdflow-maintain sdflow-roadmap sdflow-spec-review sdflow-code-review sdflow-buglist sdflow-todolist sdflow-issues embedded-test-sop openspec-upgrade sdflow-upgrade "
sdflow-init/tests/test_setup_sdflow.py:113:    "opsx-project-init","opsx-done","opsx-maintain","opsx-roadmap-planner",
== opsx-roadmap-planner ==
setup.sh:26:OUR_LEGACY_NAMES=" opsx-project-init opsx-done opsx-maintain opsx-roadmap-planner spec-review impl-review buglist-recorder todolist-recorder issues-recorder sdflow-init sdflow-done sdflow-maintain sdflow-roadmap sdflow-spec-review sdflow-code-review sdflow-buglist sdflow-todolist sdflow-issues embedded-test-sop openspec-upgrade sdflow-upgrade "
README.md:37:> | `opsx-roadmap-planner` | `sdflow-roadmap` |
sdflow-init/tests/test_setup_sdflow.py:113:    "opsx-project-init","opsx-done","opsx-maintain","opsx-roadmap-planner",
== (^|[^-])spec-review ==
setup.sh:26:OUR_LEGACY_NAMES=" opsx-project-init opsx-done opsx-maintain opsx-roadmap-planner spec-review impl-review buglist-recorder todolist-recorder issues-recorder sdflow-init sdflow-done sdflow-maintain sdflow-roadmap sdflow-spec-review sdflow-code-review sdflow-buglist sdflow-todolist sdflow-issues embedded-test-sop openspec-upgrade sdflow-upgrade "
README.md:18:| 评审（主审） | `sdflow-spec-review` | 阶段二·设计审主审：并行多镜（领域+对抗+接地读码）→ 一份 spec-review-report |
README.md:38:> | `spec-review` | `sdflow-spec-review` |
CLAUDE.md:109:`ff-generation-constraints.md` · `design-diagrams.md` · `spec-review.md` · `generation-process.md`。
AGENTS.md:10:`ff-generation-constraints.md` · `design-diagrams.md` · `spec-review.md` · `generation-process.md`。
hack/checkpoint-commit.sh:17:#   checkpoint-commit.sh spec-review
hack/checkpoint-commit.sh:18:#     → commit: "checkpoint(spec-review)"
sdflow-spec-review/SKILL.md:5:  编排成一次连续跑、产出**一份** spec-review-report.md 的评审。主 session（强模型）协调：Step1 跑
sdflow-spec-review/SKILL.md:10:  与 autoplan 互补不重复（autoplan 已含 eng 镜）。出报告标 [spec-review-amendment]。也可说"sdflow 设计审"。
sdflow-spec-review/SKILL.md:16:把 workflow 规则集的 `spec-review.md`（经 resolve-workflow.sh 解析，Detection 方法论）+ `spec-checklists/domains/`（领域 R 项）
sdflow-spec-review/SKILL.md:18:**一份** `spec-review-report.md`。取代旧"autoplan + spec-review 各出报告 + 人工手动合并（旧 step 7）"三步。
sdflow-spec-review/SKILL.md:31:2. 规则根解析：`[ -x ~/.sdflow/hack/resolve-workflow.sh ]` 不成立 → 提示「resolve-workflow.sh 未安装——先在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh」并降级通用评审；否则 `RULES_ROOT=$(~/.sdflow/hack/resolve-workflow.sh --root "$(git rev-parse --show-toplevel)")`——退出码 2 → 显式降级通用评审并原样转发脚本 stderr 告警（绝不静默当"本项目无此评审层"）；成功 → 读 `$RULES_ROOT/spec-review.md`（方法论）、`$RULES_ROOT/trigger-catalog.md`（触发）。禁止自行重实现三步链。
sdflow-spec-review/SKILL.md:39:4. **checkpoint 提交（P2c 第 1 次）**：`~/.sdflow/hack/checkpoint-commit.sh spec-review-autoplan "autoplan 广审 + gstack-amendment"`。
sdflow-spec-review/SKILL.md:68:- **checkpoint 提交（P2c 第 2 次）**：产出报告 + amendments 后 → `~/.sdflow/hack/checkpoint-commit.sh spec-review "并行多镜审 + 合并报告 + spec-review-amendment"`。
sdflow-spec-review/SKILL.md:73:  spec-review-report.md · 决策登记区
sdflow-spec-review/SKILL.md:84:- 写 `{change_dir}/spec-review-report.md`：**决策登记区**（自动决策 / 需拍板 / 已裁掉）+ 各镜 findings（带置信/严重度，低置信项一行带过、可审计不静默丢）+ 裁决。
sdflow-spec-review/SKILL.md:85:- 据此更新 design/specs，改动处标 `[spec-review-amendment]`。
sdflow-init/SKILL.md:74:│   ├── generation-process.md design-diagrams.md spec-review.md
sdflow-init/tests/test_setup_sdflow.py:70:        # 注意：entry_name 必须不撞真实现存 skill 名（如 "spec-review"）——否则
sdflow-init/tests/test_setup_sdflow.py:74:        (skills / "spec-review-legacy").symlink_to(REPO / "spec-review-legacy-GONE")
sdflow-init/tests/test_setup_sdflow.py:78:        assert not (skills / "spec-review-legacy").is_symlink()   # dangling 自属链被清
sdflow-init/tests/test_setup_sdflow.py:79:        assert "spec-review-legacy" in (r.stdout + r.stderr)       # cleaned orphans 榜上有名
sdflow-init/tests/test_setup_sdflow.py:95:        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
sdflow-init/tests/test_setup_sdflow.py:99:        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
sdflow-init/tests/test_setup_sdflow.py:114:    "spec-review","impl-review","buglist-recorder","todolist-recorder","issues-recorder",
sdflow-init/tests/test_setup_sdflow.py:128:        for name, ours in [("spec-review", True), ("bilibili-research", False)]:
sdflow-init/tests/test_setup_sdflow.py:133:        # 名单内（spec-review 属旧名，源目录已 git mv 改名为 sdflow-spec-review，不再存在于
sdflow-init/tests/test_setup_sdflow.py:137:        assert not (skills / "spec-review").exists()
sdflow-init/tests/test_checkpoint_commit.py:57:        assert _run(repo, "spec-review").returncode == 0
sdflow-init/tests/test_checkpoint_commit.py:58:        assert _subject(repo) == "checkpoint(spec-review)"
sdflow-init/assets/snippets/claude-section.md:5:`ff-generation-constraints.md` · `design-diagrams.md` · `spec-review.md` · `generation-process.md`。
sdflow-init/assets/snippets/index-section.md:15:| `spec-review` | [workflow/spec-review.md](./workflow/spec-review.md) | spec 评审（Detection 层）：只做 prevention 残差，trigger 驱动 + 独立 + 读码核验 |
sdflow-init/assets/hack/checkpoint-commit.sh:17:#   checkpoint-commit.sh spec-review
sdflow-init/assets/hack/checkpoint-commit.sh:18:#     → commit: "checkpoint(spec-review)"
sdflow-init/assets/hack/resolve-workflow.sh:69:sane() {  # 最小健全性检查：防 pull 半坏态静默广播（spec-review D2）；两个清单目录须非空（CR-F1）
sdflow-init/assets/review-tool/serve.sh:19:PIDFILE="/tmp/openspec-review-serve-${KEY}.pid"
sdflow-init/assets/review-tool/serve.sh:20:LOGFILE="/tmp/openspec-review-serve-${KEY}.log"
sdflow-init/assets/workflow/workflow.md:29:   〔HARD-GATE：用户批准设计〕            ★全流程唯一人类门——过一份 spec-review-report.md 拍板
sdflow-init/assets/workflow/workflow.md:69:| 二 | 4 | /sdflow-spec-review | `/sdflow-spec-review 独立审查 {change dir}` | spec-review-report.md | 编排器：内部 autoplan→并行多镜→**一份**报告；中途不 AskUserQuestion（决策登记进报告）；fresh 子代理替代 /clear；内部 2×checkpoint；改动标 [spec-review-amendment]。**非平凡必跑（主审）** |
sdflow-init/assets/workflow/workflow.md:70:| 二 | 5 | HARD-GATE | 人工过 **一份** `spec-review-report.md`（决策登记区已摊开选项+推荐+两方后果）→ 批准设计 | （人工：批准后才进实现） | generation-process 门；**★全流程唯一人类门** |
sdflow-init/assets/workflow/workflow.md:120:*流程 v2（三阶段连续化）· 配套 generation-process.md（生成）/ spec-review.md（评审）/ trigger-catalog.md（深度）/ reference/quality-layering.md（分层）*
sdflow-init/assets/workflow/reference/README.md:8:> `ff-generation-constraints.md` / `generation-process.md` / `spec-review.md` / `workflow.md`。
sdflow-init/assets/workflow/reference/quality-layering.md:4:> **把标准前移进生成期已有的审查口，消掉事后 review 的冗余**。与 [`spec-review.md`](../spec-review.md)
sdflow-init/assets/workflow/reference/quality-layering.md:119:*方法论 v2（P3c：sdflow-code-review 每次全跑强制主审）· 项目无关 · 配套 spec-review.md（设计侧残差）/ code-checklists/（领域清单）/ workflow.md（编排）*
sdflow-issues/scripts/issues.py:326:# batches.md 每批一条，字段级 grammar（Q3 spec-review-amendment 裁决）：
openspec/INDEX.md:20:| `spec-review` | [workflow/spec-review.md](./workflow/spec-review.md) | spec 评审（Detection 层）：只做 prevention 残差，trigger 驱动 + 独立 + 读码核验 |
openspec/serve.sh:19:PIDFILE="/tmp/openspec-review-serve-${KEY}.pid"
openspec/serve.sh:20:LOGFILE="/tmp/openspec-review-serve-${KEY}.log"
openspec/specs/spec-workflow/spec.md:24:- **THEN** 编排器把它写入 spec-review-report.md 决策登记区并继续，不中途弹 AskUserQuestion
openspec/specs/spec-workflow/spec.md:28:阶段二 SHALL 由 `sdflow-spec-review` 编排器串起 autoplan 与 sdflow-spec-review 并产出**单一** `spec-review-report.md`，MUST NOT 要求人工手动合并多份报告。
openspec/specs/spec-workflow/spec.md:32:- **THEN** 编排器输出一份已去重合并、含决策登记区的 spec-review-report.md，供设计 HARD-GATE 人工一次性评审
openspec/specs/spec-workflow/spec.md:119:批次 SHALL 有第一类身份记录于 `issues/batches.md`（`PLANNED→IN_PROGRESS→DONE`，条目薄，批次 key = 清理 change 名）；每个 change 收尾时 sweep MUST 以 `源==本change` 为界只分诊本 change 新增的 OPEN 项入批次（源为空的孤儿项不归本次 sweep，交独立的通用 `--open-ungrouped` 清理流程处理）；`reindex` MUST 拿 item 池当 ground truth 同步批次状态——批次**成员数 ≥ 1 且全部进入各自 recorder 的终态集**（bug: `FIXED`/`WONTFIX`；todo: `DONE`/`WONTDO`，含 WONT\* 合法闭合）→ 批次判 `DONE`（0 成员批次 MUST 保持 `PLANNED`，防 vacuous-truth 假 DONE〔spec-review-amendment: D1〕），状态与成员不一致则标出纠正〔grill-amendment: B-Q1〕，MUST NOT 主动计算逾期或催办（改为被动摊清 + open 项下次清理自然纳入）。
openspec/specs/spec-workflow/spec.md:129:#### Scenario: 0 成员批次不被 vacuous 判 DONE〔spec-review-amendment: D1〕
openspec/specs/spec-workflow/spec.md:139:〔spec-review-amendment〕契约补强：步① 判据粒度 MUST 为 **any-of**（三顶层单元任一存在即判本地 pin），部分残留时 MUST 输出专门告警（提示补齐或删净），MUST NOT 隐式选择 any/all 语义；脚本 MUST 支持 `--root <仓根>`（缺省 `git rev-parse --show-toplevel`）与 `${SDFLOW_HOME:-$HOME/.sdflow}` 环境覆盖（测试隔离）；步② 命中后 MUST 做最小健全性检查（`workflow.md` 非空 + `spec-checklists/`、`code-checklists/` 两个清单目录均非空，`sane()` 判据，不过检按缺失处理）；调用方 MUST 先以 `[ -x ]` 判脚本自身存在——脚本缺失（未跑 setup）与步③ bundle 缺失是**两个不同告警**，MUST NOT 混同。
openspec/specs/spec-workflow/spec.md:183:〔spec-review-amendment / impl-review-fix 935eb42〕告警触发点 = **`init` 与 `update` 两种模式均内联检测**（同一判据函数：新项目 fresh init 自然零残留、零告警；老仓被误当新项目跑 `init` 时也不因模式不同而假绿放过残留）+ **`sdflow-maintain` 兜底扫描**（覆盖常年不跑 `init`/`update` 的仓）；检测范围 MUST 同时覆盖旧版仓内 `hack/checkpoint-commit.sh` **孤儿副本**（checkpoint 全局化后不再被任何机制刷新），并给对称提示（删=用全局 / 本地 workflow.md 副本仍引用它则勿删）。
openspec/workflow/workflow.md:29:   〔HARD-GATE：用户批准设计〕            ★全流程唯一人类门——过一份 spec-review-report.md 拍板
openspec/workflow/workflow.md:69:| 二 | 4 | /sdflow-spec-review | `/sdflow-spec-review 独立审查 {change dir}` | spec-review-report.md | 编排器：内部 autoplan→并行多镜→**一份**报告；中途不 AskUserQuestion（决策登记进报告）；fresh 子代理替代 /clear；内部 2×checkpoint；改动标 [spec-review-amendment]。**非平凡必跑（主审）** |
openspec/workflow/workflow.md:70:| 二 | 5 | HARD-GATE | 人工过 **一份** `spec-review-report.md`（决策登记区已摊开选项+推荐+两方后果）→ 批准设计 | （人工：批准后才进实现） | generation-process 门；**★全流程唯一人类门** |
openspec/workflow/workflow.md:120:*流程 v2（三阶段连续化）· 配套 generation-process.md（生成）/ spec-review.md（评审）/ trigger-catalog.md（深度）/ reference/quality-layering.md（分层）*
openspec/workflow/reference/README.md:8:> `ff-generation-constraints.md` / `generation-process.md` / `spec-review.md` / `workflow.md`。
openspec/workflow/reference/quality-layering.md:4:> **把标准前移进生成期已有的审查口，消掉事后 review 的冗余**。与 [`spec-review.md`](../spec-review.md)
openspec/workflow/reference/quality-layering.md:119:*方法论 v2（P3c：sdflow-code-review 每次全跑强制主审）· 项目无关 · 配套 spec-review.md（设计侧残差）/ code-checklists/（领域清单）/ workflow.md（编排）*
== (^|[^-])impl-review ==
setup.sh:26:OUR_LEGACY_NAMES=" opsx-project-init opsx-done opsx-maintain opsx-roadmap-planner spec-review impl-review buglist-recorder todolist-recorder issues-recorder sdflow-init sdflow-done sdflow-maintain sdflow-roadmap sdflow-spec-review sdflow-code-review sdflow-buglist sdflow-todolist sdflow-issues embedded-test-sop openspec-upgrade sdflow-upgrade "
README.md:39:> | `impl-review` | `sdflow-code-review` |
sdflow-code-review/SKILL.md:7:  Step3 置信过滤（<80 滤除）+ 对抗裁决，Step4 **能修的自动修**（标 [impl-review-fix]）、≥2 方案有把握自动
sdflow-code-review/SKILL.md:11:  [impl-review-fix]。也可说"sdflow 代码审"。Trigger with /sdflow-code-review。
sdflow-code-review/SKILL.md:21:> `quality-layering.md §五` 的结论，**已被否决**。impl-review 是**每次全跑的独立强制主审**：实测能抓出
sdflow-code-review/SKILL.md:23:> 合并成一个编排器，产出一份 `code-review-report.md`（取代旧 staff-review-report.md + impl-review-report.md 分裂）。
sdflow-code-review/SKILL.md:38:  第一遍: subagent-dev 终审 + 注入点B        第二遍: 本 skill（事后 impl-review）
sdflow-code-review/SKILL.md:80:> 〔Phase C 补〕impl-review **自带 code outside voice**（跨模型 codex，always）+ 命中 HR-TG 单开领域 cross-model
sdflow-code-review/SKILL.md:94:- **能修的自动修**：标 `[impl-review-fix]`，**不进延后池**。
sdflow-code-review/SKILL.md:103:- 修复代码，改动处标 `[impl-review-fix]`。
sdflow-code-review/SKILL.md:104:- **checkpoint 提交**：产出报告 + 自动修复后 → `~/.sdflow/hack/checkpoint-commit.sh impl-review "多镜代码审 + 自动修 + 报告"`。
sdflow-code-review/SKILL.md:116:  [严重度] CR-04 资源泄漏 | file.go:42 | 错误路径未释放 conn | 置信 90 | 已修[impl-review-fix] / defer→buglist
sdflow-code-review/SKILL.md:120:  自动修 N 项[impl-review-fix]；自动选推荐 M 项(附理由)；defer K 项 → buglist/todolist
sdflow-init/tests/test_setup_sdflow.py:95:        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
sdflow-init/tests/test_setup_sdflow.py:99:        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
sdflow-init/tests/test_setup_sdflow.py:114:    "spec-review","impl-review","buglist-recorder","todolist-recorder","issues-recorder",
sdflow-init/assets/workflow/workflow.md:40:     └─ 能修自动修[impl-review-fix]、修不了/拿不准 defer→buglist/todolist；一份 code-review-report.md
sdflow-init/assets/workflow/workflow.md:74:| 三 | 8 | /sdflow-code-review | `/sdflow-code-review 每次全跑独立审查 {change dir} 的代码变更（并入 gstack/review 的 scope-drift+完成度审计；能修的自动修标 [impl-review-fix]、修不了/拿不准的记 buglists/todolists；汇总一份 code-review-report.md）。完成后 checkpoint-commit sdflow-code-review。` | code-review-report.md | 编排器：**每次全跑·独立冷·强制主审**（P3c，非高风险才跑）；清单逐条+对抗+历史镜+置信过滤；阶段三无人类门（自动修/裁/defer，不 AskUserQuestion） |
openspec/specs/spec-workflow/spec.md:141:〔impl-review-fix / 935eb42〕退出码与入参校验契约：脚本 MUST 用 **exit 64** 标记用法错误——`--root` 缺值、`--root` 后紧跟形如 `-*` 的疑似 flag 值、未知参数，以及**默认 cwd 解析失败**（`git rev-parse --show-toplevel` 与 `pwd` 均失败，如 cwd 已被删除）且未显式传 `--root` 兜底的场景；MUST 用 **exit 2** 标记全局 bundle 不可达/不完整（步③降级）；MUST 用 **exit 0** 标记解析成功（本地 pin 或全局 canonical）。`SDFLOW_HOME` MUST 校验为绝对路径，非绝对路径 MUST 告警并忽略该值（不参与步②解析，直接判全局不可达），MUST NOT 静默当相对路径拼接使用。
openspec/specs/spec-workflow/spec.md:183:〔spec-review-amendment / impl-review-fix 935eb42〕告警触发点 = **`init` 与 `update` 两种模式均内联检测**（同一判据函数：新项目 fresh init 自然零残留、零告警；老仓被误当新项目跑 `init` 时也不因模式不同而假绿放过残留）+ **`sdflow-maintain` 兜底扫描**（覆盖常年不跑 `init`/`update` 的仓）；检测范围 MUST 同时覆盖旧版仓内 `hack/checkpoint-commit.sh` **孤儿副本**（checkpoint 全局化后不再被任何机制刷新），并给对称提示（删=用全局 / 本地 workflow.md 副本仍引用它则勿删）。
openspec/workflow/workflow.md:40:     └─ 能修自动修[impl-review-fix]、修不了/拿不准 defer→buglist/todolist；一份 code-review-report.md
openspec/workflow/workflow.md:74:| 三 | 8 | /sdflow-code-review | `/sdflow-code-review 每次全跑独立审查 {change dir} 的代码变更（并入 gstack/review 的 scope-drift+完成度审计；能修的自动修标 [impl-review-fix]、修不了/拿不准的记 buglists/todolists；汇总一份 code-review-report.md）。完成后 checkpoint-commit sdflow-code-review。` | code-review-report.md | 编排器：**每次全跑·独立冷·强制主审**（P3c，非高风险才跑）；清单逐条+对抗+历史镜+置信过滤；阶段三无人类门（自动修/裁/defer，不 AskUserQuestion） |
== buglist-recorder ==
setup.sh:26:OUR_LEGACY_NAMES=" opsx-project-init opsx-done opsx-maintain opsx-roadmap-planner spec-review impl-review buglist-recorder todolist-recorder issues-recorder sdflow-init sdflow-done sdflow-maintain sdflow-roadmap sdflow-spec-review sdflow-code-review sdflow-buglist sdflow-todolist sdflow-issues embedded-test-sop openspec-upgrade sdflow-upgrade "
README.md:40:> | `buglist-recorder` | `sdflow-buglist` |
sdflow-init/tests/test_setup_sdflow.py:95:        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
sdflow-init/tests/test_setup_sdflow.py:99:        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
sdflow-init/tests/test_setup_sdflow.py:114:    "spec-review","impl-review","buglist-recorder","todolist-recorder","issues-recorder",
== todolist-recorder ==
setup.sh:26:OUR_LEGACY_NAMES=" opsx-project-init opsx-done opsx-maintain opsx-roadmap-planner spec-review impl-review buglist-recorder todolist-recorder issues-recorder sdflow-init sdflow-done sdflow-maintain sdflow-roadmap sdflow-spec-review sdflow-code-review sdflow-buglist sdflow-todolist sdflow-issues embedded-test-sop openspec-upgrade sdflow-upgrade "
README.md:41:> | `todolist-recorder` | `sdflow-todolist` |
sdflow-init/tests/test_setup_sdflow.py:114:    "spec-review","impl-review","buglist-recorder","todolist-recorder","issues-recorder",
== issues-recorder ==
setup.sh:26:OUR_LEGACY_NAMES=" opsx-project-init opsx-done opsx-maintain opsx-roadmap-planner spec-review impl-review buglist-recorder todolist-recorder issues-recorder sdflow-init sdflow-done sdflow-maintain sdflow-roadmap sdflow-spec-review sdflow-code-review sdflow-buglist sdflow-todolist sdflow-issues embedded-test-sop openspec-upgrade sdflow-upgrade "
README.md:42:> | `issues-recorder` | `sdflow-issues` |
sdflow-init/tests/test_setup_sdflow.py:114:    "spec-review","impl-review","buglist-recorder","todolist-recorder","issues-recorder",
```

### 修复记录（白名单外命中 → 判定为真残留 → 已修复）

以下 7 处判定为「本该已改名但漏改的自我指称」（不是迁移测试/映射表/历史注记等合法既有设计），修复后重跑至 clean：

| # | 文件:行 | 修复前 | 修复后 | 理由 |
|---|---|---|---|---|
| 1 | `sdflow-done/SKILL.md:57` | `opsx-done 低频，省那点 token 不值` | `sdflow-done 低频，省那点 token 不值` | 正文以旧名自称本 skill（非迁移测试/映射表/tag），Task 4 sweep 漏改 |
| 2 | `sdflow-done/SKILL.md:100` | `opsx-done 是自制 skill` | `sdflow-done 是自制 skill` | 同上 |
| 3 | `sdflow-code-review/SKILL.md:21` | `impl-review 是**每次全跑的独立强制主审**` | `sdflow-code-review 是**每次全跑的独立强制主审**` | 正文以旧名自称本 skill，且缺"旧"字限定词（对比同文件 L23"旧 staff-review-report.md"有限定词、此处无），易读成"当前仍名 impl-review" |
| 4 | `sdflow-code-review/SKILL.md:38` | `第二遍: 本 skill（事后 impl-review）` | `第二遍: 本 skill（事后 sdflow-code-review）` | 同上，紧邻"本 skill"的括注用旧名会产生自相矛盾 |
| 5 | `sdflow-code-review/SKILL.md:80` | `impl-review **自带 code outside voice**` | `sdflow-code-review **自带 code outside voice**` | 同上 |
| 6 | `sdflow-init/tests/test_init.py:131` | `SKILL_DIR = str(root / "opsx-project-init")` | `SKILL_DIR = str(root / "sdflow-init")` | 该 fixture 只是 `--dev` 身份校验用的任意子目录名（校验逻辑只看 `dirname(SKILL_DIR)`，与 basename 无关），不是像 `TestInjectMarkerMigration`/`test_setup_sdflow.py` 那样"故意测旧名迁移/清理"的用例，属改名前遗留的无意义旧名残留 |
| 7 | `sdflow-init/tests/test_init.py:283` | `fake_skill_dir = tmp_path / "some-repo" / "opsx-project-init"` | `fake_skill_dir = tmp_path / "some-repo" / "sdflow-init"` | 同上 |

### 第二轮（修复后重跑，全部 clean 或判定为合法既有设计）

重跑同一命令，命中总行数从 128 降到 112（减少 16 行）；`pattern 无命中直接落 "clean"` 分支的
只有 `opsx-maintain` `opsx-roadmap-planner` `buglist-recorder` `todolist-recorder` `issues-recorder` 这 5 个
（其原始命中本身就都在下方「clean 判定理由」表覆盖范围内，无需二次修复）。逐名结果：

- `opsx-project-init`：白名单外剩 9 处命中，全部落入下方「clean 判定理由」①③④
- `opsx-done`：白名单外剩 5 处，全部落入①③
- `opsx-maintain`：白名单外剩 3 处，全部落入①③
- `opsx-roadmap-planner`：白名单外剩 3 处，全部落入①③
- `(^|[^-])spec-review`：白名单外剩 62 处，全部落入①②③④⑤⑥
- `(^|[^-])impl-review`：白名单外剩 19 处，全部落入①②③④⑥
- `buglist-recorder`：白名单外剩 5 处，全部落入①③
- `todolist-recorder`：白名单外剩 3 处，全部落入①③
- `issues-recorder`：白名单外剩 3 处，全部落入①③

**无一条命中判定为"待修的真残留"——本轮反向断言到此收敛为 clean。**

---

## clean 判定理由（逐类，不静默）

brief 已明确给出两条判定细则（②③），以下补充完整分类，覆盖第二轮全部白名单外命中：

1. **`setup.sh:26` `OUR_LEGACY_NAMES` 列表** —— 机制上明确需要同时列出旧名+新名，用于识别/清理跨改名遗留的
   自属 symlink（`cleanup_orphans`）。旧名在此处是**功能输入**，不是自我指称，clean。
2. **`README.md` 旧名→新名映射表**（如 `> | opsx-project-init | sdflow-init |`）—— 专门记录本次改名对照关系
   的文档区块，供用户查旧名对应新名，clean。
3. **`sdflow-init/tests/test_setup_sdflow.py`、`test_checkpoint_commit.py` 中的旧名字面量** —— 均在显式测试
   "旧名 symlink 清理"“跨改名端到端”“legacy marker 识别”等迁移/兼容行为的用例内（`TestRenameEndToEnd`、
   `TestCleanupOrphansDangling`、`TestBrandAndMarkerNarrowing` 等），旧名是被测对象本身，clean。
4. **`sdflow-init/tests/test_init.py` 的 `TestInjectMarkerMigration`（含本次新增的 MARK_IDX 对称用例）** ——
   显式测试"旧 marker 文案区块被替换而非追加"的迁移逻辑，`OLD_BLOCK`/`OLD_IDX_BLOCK` 常量必须包含旧名字面量
   才能构造迁移前状态，clean。
5. **`sdflow-init/scripts/init.py:79` 注释**（`如 opsx-project-init → sdflow-init`）—— 解释 `inject()` 为何按
   token 定位而非全串匹配的设计理由，用真实发生过的改名做例证，带"如...→..."限定词，非自我指称，clean。
6. **`spec-review.md` / `impl-review` 相关的产出物名、方法论文件名、tag 约定**（brief 已给的两条细则 + 本轮
   扩展判读一致对待的同类项）：
   - 方法论文件名 `spec-review.md`（`openspec/workflow/`、`sdflow-init/assets/workflow/` 及其 `reference/`
     下的引用/超链接）—— 文件本身不改名，clean（brief 细则一）。
   - 产出物文件名 `spec-review-report.md` / `code-review-report.md` —— 工作流约定的报告文件名，不随 skill
     改名而改，clean（brief 细则二）。
   - 变更标签 `[spec-review-amendment]` / `[impl-review-fix]` —— 工作流通用约定的改动标记 tag，含义是"由
     spec/impl 评审环节产生的修订"，与当前 skill 短名无耦合，clean（brief 细则二引申）。
   - **checkpoint 提交 label**（`~/.sdflow/hack/checkpoint-commit.sh spec-review ...` /
     `... impl-review ...`，含 `hack/checkpoint-commit.sh` 头部注释示例、`test_checkpoint_commit.py` 断言）——
     是 `checkpoint(<label>)` commit 消息里的短语义标签，历史上就与 skill 全名解耦（如 `spec-review-autoplan`
     并非任何 skill 的正式名字），修改会牵连既有 commit 历史读法且无功能必要，归入"工作流通用约定"同类判 clean。
     **本条为 brief 未列举细则的扩展判读，特此标出供复核**——若认为应统一改为 `sdflow-spec-review` /
     `sdflow-code-review`，属可选的一致性打磨（非"遗留旧名 bug"），不在本次 rebrand 的强制范围内。
   - `openspec/specs/spec-workflow/spec.md` 中引用上述 tag/文件名的 spec 正文（如"由 sdflow-spec-review 编排器
     串起...并产出 spec-review-report.md”）—— 同理，clean。
7. **`serve.sh:19-20`（`openspec/serve.sh`、`sdflow-init/assets/review-tool/serve.sh`）的 `PIDFILE`/`LOGFILE`
   路径** —— `openspec-review-serve` 是正则误撞：`(^|[^-])spec-review` 命中的是 `openspec-review` 里
   `n` + `spec-review` 子串（`open` + `spec-review`），与旧 skill 名无关，是"openspec 的 review-serve 服务"命名，
   clean（正则假阳性，非语义命中）。
8. **`sdflow-init/assets/hack/resolve-workflow.sh:69`** `sane() { ... 防 pull 半坏态静默广播（spec-review D2）`
   —— 注释里的 "spec-review D2" 是历史决策编号引用（design.md 决策项 D2 的简写出处标注），非技能自我指称，clean。
9. **`sdflow-issues/scripts/issues.py:326`** `Q3 spec-review-amendment 裁决` —— 引用历史评审决策编号，同⑧，clean。

---

## Step 3：全量回归

```
python3 -m pytest -q
```

预期与实际：233 passed（232 既有 + 本次新增 `test_old_idx_marker_block_replaced_not_duplicated` 1 例）。

## Step 4：checkpoint

```
bash hack/checkpoint-commit.sh task8-assert "update --dev 同步(marker 迁移实测) + 逐名反向断言留档（5.4/4.3）"
```

---

## 勘误附注（task8-fix）

本文档初版在「第一轮」与「第二轮」计数上存在三处自相矛盾，已通过程序化重算修正：

| 项目 | 原数 | 正数 | 理由 |
|---|---|---|---|
| 第一轮总行数 | 128 | 119 | 内嵌 dump 中逐 pattern 实测加总（见下方命令） |
| 第二轮总行数 | 121 | 112 | 修复后重跑同一白名单命令，精确计数 |
| `impl-review` 明细 | 21 | 19 | 第二轮实际仅 19 处，之前误数 |

**勘误方法（程序化计数）**

第一轮验证（逐 pattern 统计）：
```bash
# assert-log.md 内嵌 dump 从 L62-189，逐 section 按 "== pattern ==" 分界统计
# opsx-project-init: 11 行（L63-73）
# opsx-done: 7 行（L75-81）
# opsx-maintain: 3 行（L83-85）
# opsx-roadmap-planner: 3 行（L87-89）
# spec-review: 62 行（L91-152）
# impl-review: 22 行（L154-175）
# buglist-recorder: 5 行（L177-181）
# todolist-recorder: 3 行（L183-185）
# issues-recorder: 3 行（L187-189）
# 加总：11+7+3+3+62+22+5+3+3 = 119 行
```

第二轮验证（重跑修复后命令）：
```bash
WL='openspec/adr/|openspec/ROADMAP.md|openspec/CONTEXT.md|openspec/changes/archive/|openspec/issues/|openspec/changes/sdflow-rebrand/|\.superpowers/|docs/|memo-'
for pat in 'opsx-project-init' 'opsx-done' 'opsx-maintain' 'opsx-roadmap-planner' \
           '(^|[^-])spec-review' '(^|[^-])impl-review' \
           'buglist-recorder' 'todolist-recorder' 'issues-recorder'; do
  grep -rEn "$pat" . --exclude-dir=.git --exclude-dir=node_modules 2>/dev/null | grep -Ev "$WL" | wc -l
done
# 结果：9, 5, 3, 3, 62, 19, 5, 3, 3（逐行输出）
# 加总：9+5+3+3+62+19+5+3+3 = 112 行
```

三处数字已与程序化计数实测结果对齐，未来如需验证可参照上述命令重跑。
