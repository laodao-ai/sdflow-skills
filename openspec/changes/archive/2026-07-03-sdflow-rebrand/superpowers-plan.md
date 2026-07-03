# sdflow-rebrand Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 9 个 skill 目录全量 sdflow- 前缀化（含触发词重写与品牌收拢），并先修好它依赖的两块坏地基（cleanup_orphans dangling 枚举 / inject() marker 匹配）。

**Architecture:** ⓪先修地基（TDD）→ ①git mv + 机械路径修复一次回绿 → ②文本 sweep（六类引用面显式清单）→ ③触发词与品牌 → ④断言与测试 → ⑤instance 同步后反向断言 → ⑥文档收尾。真实激活不在本计划内（merge+push 后新会话 /sdflow-upgrade，hand-off 承载）。

**Tech Stack:** bash（setup.sh）、Python3 + pytest（init.py / issues.py / 测试）、Markdown。

## Global Constraints

（逐字来自 design D1-D8 + 设计门拍板，每任务隐含遵守）

- **RENAME-MAP（唯一数据源，9 改 3 留）**：opsx-project-init→sdflow-init · opsx-done→sdflow-done · opsx-maintain→sdflow-maintain · opsx-roadmap-planner→sdflow-roadmap · spec-review→sdflow-spec-review · impl-review→sdflow-code-review · buglist-recorder→sdflow-buglist · todolist-recorder→sdflow-todolist · issues-recorder→sdflow-issues；保留 embedded-test-sop / openspec-upgrade / sdflow-upgrade。
- **实现期禁跑真实 `setup.sh`**（D4 激活改道）：一切 setup 行为验证走假 HOME/SDFLOW_HOME 沙箱测试；本 session 后续评审步继续用运行 checkout 的旧名 skill。
- **文档性白名单不改**：`openspec/adr/`、ROADMAP 历史行、`openspec/CONTEXT.md`、`openspec/changes/archive/`、`openspec/issues/`、`.superpowers/`、本 change 目录（报告/评审文件里的旧名 = 评审历史）。
- 托管区块（CLAUDE.md/AGENTS.md/INDEX.md 的 `opsx-init:*` 区块）**不手改**——Task 8 经 `update --dev` 重注入。
- 触发等价（D2/D6）：9 个新 description 必须保留旧 description 的全部中文触发短语（机械断言核验），只换 slash 名与自称。
- marker 兼容收窄（D5）：`.laodao-skills` 仅对目录名 ∈ RENAME-MAP 旧名∪新名∪保留名单识别为自属；名单外 skip。
- 行为零变化：除 0 组两个 bug 修复外，一切改动为改名/文案；全量 pytest 是锚点。
- 子代理 Edit 前必须先 Read；每任务末跑对应 pytest + 全量回归，然后 `bash hack/checkpoint-commit.sh <task-id> "<描述>"`（本仓 dogfood 实例脚本）。

---

### Task 1: 修 cleanup_orphans dangling 枚举（0.1，TDD）

**Files:**
- Modify: `setup.sh`（cleanup_orphans 函数，现 :66-103 一带）
- Test: `opsx-project-init/tests/test_setup_sdflow.py`（追加类）

**Interfaces:**
- Produces: cleanup_orphans 能枚举 dangling 软链（后续 Task 6 的跨改名测试依赖）

- [ ] **Step 1: 写失败测试（追加）**

```python
class TestCleanupOrphansDangling:
    """0.1：尾斜杠 glob 看不见 dangling 链（POSIX 语义）——修为 find 枚举后必须能清。"""

    def test_dangling_own_link_is_cleaned(self, tmp_path):
        home = tmp_path / "home"
        skills = home / ".claude" / "skills"
        skills.mkdir(parents=True)
        # 自属 dangling：目标路径含本仓名（basename REPO）但已不存在——模拟改名后的旧链
        (skills / "spec-review").symlink_to(REPO / "spec-review-GONE")
        env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
        r = subprocess.run(["bash", str(REPO / "setup.sh")], env=env, capture_output=True, text=True)
        assert r.returncode == 0
        assert not (skills / "spec-review").is_symlink()          # dangling 自属链被清
        assert "spec-review" in (r.stdout + r.stderr)              # cleaned orphans 榜上有名

    def test_foreign_dangling_link_is_kept(self, tmp_path):
        home = tmp_path / "home"
        skills = home / ".claude" / "skills"
        skills.mkdir(parents=True)
        (skills / "alien-skill").symlink_to("/nonexistent/other-tool/alien-skill")
        env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
        subprocess.run(["bash", str(REPO / "setup.sh")], env=env, capture_output=True, text=True)
        assert (skills / "alien-skill").is_symlink()               # 非自属不动（红线）
```

- [ ] **Step 2: 跑红** `python3 -m pytest opsx-project-init/tests/test_setup_sdflow.py -v -k Dangling` — Expected: `test_dangling_own_link_is_cleaned` FAIL（链仍在——glob 枚举不到）
- [ ] **Step 3: 修 setup.sh**——cleanup_orphans 的枚举行替换：

```bash
  # 旧：for entry in "$dest"/*/; do            ← 尾斜杠 glob 枚举不到 dangling 软链（死代码根因）
  # 新：find 枚举一切一级条目（含悬空链）
  local entry entry_name
  while IFS= read -r entry; do
    [ -n "$entry" ] || continue
    entry_name="$(basename "$entry")"
    ...   # 原循环体不变（is_ours 判断 / gone 判断 / rm）
  done < <(find "$dest" -mindepth 1 -maxdepth 1)
```

保持原循环体逻辑逐行不动（只换枚举方式）；`[ -e "$entry" ] || continue` 这类会跳过 dangling 的 guard 一并梳理掉（dangling 恰是要处理的对象）。

- [ ] **Step 4: 跑绿 + 全量** `python3 -m pytest opsx-project-init/tests/ -q` — Expected: 全 PASS 无 warning
- [ ] **Step 5: Commit** `bash hack/checkpoint-commit.sh task1-orphan-fix "修 cleanup_orphans dangling 枚举（find 替代尾斜杠 glob）+ 双向测试（0.1）"`

### Task 2: inject() marker token 迁移（0.2，TDD）

**Files:**
- Modify: `opsx-project-init/scripts/init.py`（MARK_DOC/MARK_IDX :34-37、inject() :62-82）
- Test: `opsx-project-init/tests/test_init.py`（追加类）

**Interfaces:**
- Produces: `inject()` 以 token 行定位区块；`MARK_DOC`/`MARK_IDX` 文案改为 "由 sdflow-init 维护"；旧文案区块被原位替换。Task 8 的 update --dev 依赖此行为。

- [ ] **Step 1: 写失败测试**

```python
class TestInjectMarkerMigration:
    """0.2：inject() 改 token 基定位——旧 marker 文案（opsx-project-init）区块被替换而非追加重复。"""

    OLD_BLOCK = ("<!-- opsx-init:start —— 由 opsx-project-init 维护，勿手改本区块 -->\n"
                 "旧内容\n<!-- opsx-init:end -->\n")

    def test_old_marker_block_replaced_not_duplicated(self, tmp_path):
        f = tmp_path / "CLAUDE.md"
        f.write_text("# 头\n\n" + self.OLD_BLOCK + "\n尾部用户内容\n", encoding="utf-8")
        init_mod.inject(str(f), *init_mod.MARK_DOC, "新内容")
        text = f.read_text(encoding="utf-8")
        assert text.count("opsx-init:start") == 1        # 只有一个区块（替换，非追加）
        assert "新内容" in text and "旧内容" not in text
        assert "sdflow-init 维护" in text                 # marker 文案已随替换更新
        assert "尾部用户内容" in text                     # 区块外内容无损

    def test_fresh_file_gets_new_marker(self, tmp_path):
        f = tmp_path / "CLAUDE.md"
        init_mod.inject(str(f), *init_mod.MARK_DOC, "内容", header="# H")
        assert "sdflow-init 维护" in f.read_text(encoding="utf-8")
```

- [ ] **Step 2: 跑红** — Expected: FAIL（现 inject 全串精确匹配旧文案找不到 → 追加出第二个区块 / marker 未更新）
- [ ] **Step 3: 改 init.py**——常量与定位逻辑：

```python
MARK_DOC = ("<!-- opsx-init:start —— 由 sdflow-init 维护，勿手改本区块 -->",
            "<!-- opsx-init:end -->")
MARK_IDX = ("<!-- opsx-init:rules:start —— 由 sdflow-init 维护，勿手改本区块 -->",
            "<!-- opsx-init:rules:end -->")

MARK_TOKENS = {  # token → 完整新 marker；定位按 token（历史 marker 文案含旧 skill 名，全串匹配会漏）
    "opsx-init:start": MARK_DOC, "opsx-init:rules:start": MARK_IDX,
}


def _find_marker_line(text, token):
    """按 token 定位 marker 整行（返回该行起止 offset），找不到返回 None。"""
    for line in text.splitlines(keepends=True):
        if token in line and line.lstrip().startswith("<!--"):
            start = text.index(line)
            return start, start + len(line)
    return None
```

`inject(path, start, end, content, header="")` 内部：用 `start` 中的 token（`opsx-init:start` / `opsx-init:rules:start`）与 `end` 的 token（`opsx-init:end` / `opsx-init:rules:end`）经 `_find_marker_line` 定位既有区块首尾行；命中则用**新** marker 全行 + 新内容原位替换（旧文案行随之消失）；未命中走原追加/新建逻辑。函数签名与调用点不变。

- [ ] **Step 4: 跑绿 + 全量** — Expected: 全 PASS（既有 inject 测试如有全串断言需同步改为新文案）
- [ ] **Step 5: Commit** `bash hack/checkpoint-commit.sh task2-marker-token "inject() token 基定位 + marker 文案迁 sdflow-init + 防重复区块测试（0.2）"`

### Task 3: git mv ×9 + 机械路径修复一次回绿（1.1/1.3/1.2 承重路径）

**Files:**
- Rename: 9 个目录（RENAME-MAP）
- Modify: `setup.sh`（:109/:133 一带 `opsx-project-init/assets/...` → `sdflow-init/assets/...`，共 2 处承重路径）
- Modify: `sdflow-issues/scripts/issues.py`（原 :64-65 目录名 join）
- Modify: 测试文件路径引用：`sdflow-init/tests/test_setup_sdflow.py`（`REPO / "opsx-project-init"`）、`test_resolve_workflow.py`（SCRIPT 路径）、`test_init.py`（如有）、三 recorder/issues tests 内的 sibling 目录名

- [ ] **Step 1:** `git mv opsx-project-init sdflow-init && git mv opsx-done sdflow-done && git mv opsx-maintain sdflow-maintain && git mv opsx-roadmap-planner sdflow-roadmap && git mv spec-review sdflow-spec-review && git mv impl-review sdflow-code-review && git mv buglist-recorder sdflow-buglist && git mv todolist-recorder sdflow-todolist && git mv issues-recorder sdflow-issues`
- [ ] **Step 2:** 机械修复（先 `grep -rn "opsx-project-init\|buglist-recorder\|todolist-recorder\|issues-recorder" --include="*.py" --include="*.sh" sdflow-init/ sdflow-issues/ sdflow-buglist/ sdflow-todolist/ setup.sh` 列全命中，逐条按 RENAME-MAP 替换）：setup.sh 两处承重路径；issues.py BUGLIST_SCRIPT/TODOLIST_SCRIPT 目录名与 :57-59 注释；各测试文件 `REPO / "..."` 与 sibling 路径
- [ ] **Step 3:** 全量回绿 `python3 -m pytest -q` — Expected: 全 PASS（本 Task 结束仓库必须回到全绿，禁带红进 Task 4）
- [ ] **Step 4: Commit** `bash hack/checkpoint-commit.sh task3-rename "git mv ×9 + 承重路径/sibling/测试机械修复回绿（1.1/1.3）"`

### Task 4: 文本 sweep（1.2 六类显式清单 + 1.4）

**Files:**
- Modify: `sdflow-init/assets/workflow/workflow.md`（步骤表 /spec-review→/sdflow-spec-review、/impl-review→/sdflow-code-review、/opsx-done→/sdflow-done 等；`/opsx:ff` 官方名不动）
- Modify: `sdflow-init/assets/snippets/claude-section.md` + `index-section.md`（配套 skill 表 + 安装句）
- Modify: 第⑥类规则方法论文档：`sdflow-init/assets/workflow/spec-review.md`、`ff-generation-constraints.md`、`reference/quality-layering.md`、`reference/README.md`、`reference/Token_Saving_Strategies.md`、`tools/vendor/NOTICE.md`（仅自撰 `re-run opsx-project-init update` 行）
- Modify: `openspec/config.yaml` context 字段（"opsx-project-init update 推到各使用项目"句）
- Modify: `sdflow-init/scripts/init.py`（:4 自称、:313 提示句）、`sdflow-init/scripts/gen_review_stub.py:24` 报错文案、`sdflow-init/assets/hooks/change-review-stub.py` 注释自称
- Modify: `sdflow-done/SKILL.md` §2.1 三行路径 + find 兜底句（1.4）；`README.md` Skills 列表 9 行 + 附改名对照表；`CLAUDE.md` **正文**（托管区块勿动）
- Modify: 12 个 SKILL.md 正文互引（description 重写留给 Task 5，本 task 只改正文互相点名）

- [ ] **Step 1:** 按上列清单逐文件 Read→Edit（RENAME-MAP 驱动；白名单文件绝不碰）
- [ ] **Step 2:** 粗验 `grep -rn "opsx-done\|opsx-project-init" sdflow-init/assets/ openspec/config.yaml README.md | grep -v archive` — Expected: 仅剩白名单性质残留（如有意保留的历史叙述），逐条说明
- [ ] **Step 3: Commit** `bash hack/checkpoint-commit.sh task4-sweep "六类引用面文本 sweep + sdflow-done sibling 路径 + README 对照表（1.2/1.4）"`

### Task 5: 触发词重写 + trigger-map + 机械断言（2.1/2.2）

**Files:**
- Modify: 9 个改名 skill 的 `SKILL.md` frontmatter description
- Create: `openspec/changes/sdflow-rebrand/trigger-map.md`

- [ ] **Step 1:** 逐 skill：Read 旧 description → 抽出全部中文触发短语（引号内触发语句 + "当用户说…"清单 + `/旧名` slash）→ 重写：slash 换新名、自称换新名、**触发短语逐条保留**、酌情补新名短语（如"sdflow 代码审"）
- [ ] **Step 2:** 写 trigger-map.md：每 skill 一节，两列表（旧短语 → 新 description 中对应位置/原样保留），slash 旧→新一行
- [ ] **Step 3: 机械断言**：对每个 skill 用循环核验旧短语 ⊆ 新 description（`python3 - <<EOF` 读 trigger-map 的旧短语列表逐条 `in` 新 frontmatter 文本 EOF），输出全 PASS 结果追加到 trigger-map.md 末尾（留档）
- [ ] **Step 4: Commit** `bash hack/checkpoint-commit.sh task5-triggers "9 description 重写 + trigger-map.md + 触发等价机械断言留档（2.1/2.2）"`

### Task 6: 品牌三件 + marker 收窄（3.1/3.2/3.3，TDD）

**Files:**
- Create: `VERSION`（内容 `0.9.0`）
- Modify: `setup.sh`（品牌输出行 `laodao-skills v${version}` → `sdflow-skills v${version}`；marker 判断 5 处收窄；头注释品牌句）
- Modify: snippets/README/CLAUDE.md 正文残余 "laodao-skills" 品牌叙述（"均来自 laodao-skills" 等）
- Test: `sdflow-init/tests/test_setup_sdflow.py`（追加类）

- [ ] **Step 1: 写失败测试**

```python
OUR_NAMES = {  # RENAME-MAP 旧名∪新名∪保留名单（marker 兼容边界，D5）
    "opsx-project-init","opsx-done","opsx-maintain","opsx-roadmap-planner",
    "spec-review","impl-review","buglist-recorder","todolist-recorder","issues-recorder",
    "sdflow-init","sdflow-done","sdflow-maintain","sdflow-roadmap","sdflow-spec-review",
    "sdflow-code-review","sdflow-buglist","sdflow-todolist","sdflow-issues",
    "embedded-test-sop","openspec-upgrade","sdflow-upgrade",
}

class TestBrandAndMarkerNarrowing:
    def test_version_line_branded(self, tmp_path):
        r, _ = run_setup(tmp_path)          # 复用本文件既有 helper
        assert "sdflow-skills v0.9.0" in r.stdout

    def test_legacy_marker_recognized_only_for_our_names(self, tmp_path):
        # 沙箱内直接构造两个带 .laodao-skills marker 的目录（模拟 Windows copy 存量）
        home = tmp_path / "home"; skills = home / ".claude" / "skills"; skills.mkdir(parents=True)
        for name, ours in [("spec-review", True), ("bilibili-research", False)]:
            d = skills / name; d.mkdir(); (d / "SKILL.md").write_text("x", encoding="utf-8")
            (d / ".laodao-skills").write_text("legacyhash", encoding="utf-8")
        env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
        r = subprocess.run(["bash", str(REPO / "setup.sh")], env=env, capture_output=True, text=True)
        # 名单内（spec-review 属旧名）：识别自属 → 在 Unix 下被替换为软链（rm -rf 后 ln）
        assert (skills / "spec-review").is_symlink()
        # 名单外（bilibili-research 是 laodao misc 财产）：skip 不动
        alien = skills / "bilibili-research"
        assert alien.is_dir() and not alien.is_symlink()
        assert (alien / ".laodao-skills").exists()
```

- [ ] **Step 2: 跑红** — Expected: 两断言 FAIL（品牌行还是 laodao；bilibili-research 被当自属误刷）
- [ ] **Step 3: 改 setup.sh**：品牌行；marker 判定处（Unix :52 与 Windows :37/:41/:45 及 cleanup :84 一带）统一改为 helper：

```bash
# marker 兼容收窄（D5）：.sdflow-skills 一律自属；.laodao-skills 仅限我方名单（防误伤 laodao misc 拷贝）
OUR_LEGACY_NAMES=" opsx-project-init opsx-done opsx-maintain opsx-roadmap-planner spec-review impl-review buglist-recorder todolist-recorder issues-recorder sdflow-init sdflow-done sdflow-maintain sdflow-roadmap sdflow-spec-review sdflow-code-review sdflow-buglist sdflow-todolist sdflow-issues embedded-test-sop openspec-upgrade sdflow-upgrade "
is_our_marker_copy() {  # $1 = 目录路径
  local name="$(basename "$1")"
  [ -f "$1/.sdflow-skills" ] && return 0
  [ -f "$1/.laodao-skills" ] && case "$OUR_LEGACY_NAMES" in *" $name "*) return 0 ;; esac
  return 1
}
```

各判断点 `[ -f "$target/.laodao-skills" ]` → `is_our_marker_copy "$target"`；新写 marker 文件名改 `.sdflow-skills`（Windows 分支）。

- [ ] **Step 4: 跑绿 + 全量** `python3 -m pytest sdflow-init/tests/ -q && python3 -m pytest -q` — Expected: 全 PASS
- [ ] **Step 5: Commit** `bash hack/checkpoint-commit.sh task6-brand "VERSION 0.9.0 + 品牌输出 + marker 收窄兼容(名单制,5判断点) + 双向测试（3.1-3.3）"`

### Task 7: 跨改名场景测试 + 布局冒烟（4.1/4.2 收口）

**Files:**
- Test: `sdflow-init/tests/test_setup_sdflow.py`（追加）

- [ ] **Step 1: 写测试**（Task 1/6 已覆盖 dangling 与 marker；本 task 补两口）：

```python
class TestRenameEndToEnd:
    def test_rename_scenario_old_links_cleaned_new_links_made(self, tmp_path):
        """跨改名端到端：预置 9 个指向本仓已不存在旧目录的自属链 → setup → 旧清新立。"""
        home = tmp_path / "home"; skills = home / ".claude" / "skills"; skills.mkdir(parents=True)
        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
            (skills / old).symlink_to(REPO / old)      # 改名后这些源目录已不存在 → dangling
        env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
        r = subprocess.run(["bash", str(REPO / "setup.sh")], env=env, capture_output=True, text=True)
        for old in ["opsx-project-init","opsx-done","spec-review","impl-review","buglist-recorder"]:
            assert not (skills / old).exists(), old     # 旧链清零
        for new in ["sdflow-init","sdflow-done","sdflow-spec-review","sdflow-code-review","sdflow-buglist"]:
            assert (skills / new).is_symlink(), new     # 新链建立

    def test_layout_smoke(self, tmp_path):
        """布局冒烟：canonical 软链指向改名后的 sdflow-init/assets/workflow；hack 两脚本可执行。"""
        r, sdflow = run_setup(tmp_path)
        assert (sdflow / "workflow").resolve() == (REPO / "sdflow-init" / "assets" / "workflow").resolve()
        for s in ("checkpoint-commit.sh", "resolve-workflow.sh"):
            assert (sdflow / "hack" / s).stat().st_mode & stat.S_IXUSR
```

- [ ] **Step 2: 跑绿 + 全量** — Expected: 全 PASS（若 FAIL 说明 Task 3 承重路径漏改，修 setup.sh 非测试）
- [ ] **Step 3: Commit** `bash hack/checkpoint-commit.sh task7-e2e-tests "跨改名端到端 + 布局冒烟测试（4.1/4.2）"`

### Task 8: instance 同步 + 白名单反向断言（5.4 → 4.3，顺序硬约束）

**Files:**
- Modify: `openspec/workflow/`、CLAUDE.md/AGENTS.md/INDEX.md 托管区块（经 update --dev，非手改）
- Create: `openspec/changes/sdflow-rebrand/assert-log.md`（断言留档）

- [ ] **Step 1:** `python3 sdflow-init/scripts/init.py update --dev --root .` → `diff -q openspec/workflow/workflow.md sdflow-init/assets/workflow/workflow.md` 无输出；**检查 CLAUDE.md 托管区块唯一**（`grep -c "opsx-init:start" CLAUDE.md` == 1，Task 2 的 marker 迁移在此实测生效）
- [ ] **Step 2: 反向断言（逐名 pattern，白名单外命中即修复后重跑）**：

```bash
WL='openspec/adr/|openspec/ROADMAP.md|openspec/CONTEXT.md|openspec/changes/archive/|openspec/issues/|openspec/changes/sdflow-rebrand/|\.superpowers/|docs/|memo-'
for pat in 'opsx-project-init' 'opsx-done' 'opsx-maintain' 'opsx-roadmap-planner' \
           '(^|[^-])spec-review' '(^|[^-])impl-review' \
           'buglist-recorder' 'todolist-recorder' 'issues-recorder'; do
  echo "== $pat =="
  grep -rEn "$pat" . --exclude-dir=.git --exclude-dir=node_modules 2>/dev/null | grep -Ev "$WL" || echo "  clean"
done
```

注意：`(^|[^-])spec-review` 负向排除 `sdflow-spec-review`；`openspec/workflow/spec-review.md` 与 `assets/workflow/spec-review.md` 的**文件名**命中属方法论文件名（不改名），归 clean 判定但文内不得再有 skill 指称（Task 4 已 sweep，若有漏此处暴露）。全部输出（含 clean 行）写入 assert-log.md。

- [ ] **Step 3:** 全量回归 `python3 -m pytest -q` — Expected: 全 PASS
- [ ] **Step 4: Commit** `bash hack/checkpoint-commit.sh task8-assert "update --dev 同步(marker 迁移实测) + 逐名反向断言留档（5.4/4.3）"`

### Task 9: 文档收尾（5.1/5.2）

**Files:**
- Create: `openspec/adr/0007-sdflow-naming-consolidation.md`
- Modify: `openspec/ROADMAP.md`

- [ ] **Step 1: adr/0007**（决策 + Considered Options + Consequences 三段式，对齐 adr/0006 体例）：全量 sdflow- 前缀 + 去后缀 + 三保留（含 impl→code-review 非机械映射理由、openspec-upgrade 豁免理由）；已评估未选 = plugin 冒号命名空间（Codex 无 plugin，双 agent 否决）、半量改名、留 stub（设计门 Q2 维持 no-stub）；回滚边界 = 本机可逆、消费仓侧非全自动；双品牌过渡（laodao 旧仓 misc 不动）；触发等价约束与机械断言承诺
- [ ] **Step 2: ROADMAP**：`extract-sdflow-repo` 行更名 `sdflow-rebrand`（注 "rescope/supersede：拆库半已发生，剩余=品牌收拢"）+ 状态 "🔵 实现完成（待 code-review/收尾）"；ADR 列表加 0007 行
- [ ] **Step 3: Commit** `bash hack/checkpoint-commit.sh task9-docs "adr/0007 + ROADMAP 更名 supersede（5.1/5.2）"`

---

## Self-Review 结论

- Spec 覆盖：R-SR-1 → Task 3/4/5/8；R-SR-2 → Task 6；R-SR-3 → Task 2/8；两条 MODIFIED（名称随动）→ Task 4/8；tasks.md 0-5 全组有对应（5.3 激活改道 = 计划外交付，hand-off 承载；5.5 = opsx-done 生成 hand-off 时按 tasks 5.5 清单写入）。
- 占位符扫描：无 TBD；bash/python 代码块完整；文案步给了文件清单与判据。
- 一致性：`is_our_marker_copy`（Task 6 定义/使用一致）；`OUR_NAMES`/`OUR_LEGACY_NAMES` 同源 RENAME-MAP；断言 pattern 与 design D1 一致；Task 3 结束必须全绿的约束防止红态传播。
- 顺序：0 组（Task 1/2）先于改名（Task 3）；断言（Task 8）在 instance 同步之后——满足 F3 时序硬约束。
