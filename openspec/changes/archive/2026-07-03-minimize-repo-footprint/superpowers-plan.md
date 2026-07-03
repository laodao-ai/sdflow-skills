# minimize-repo-footprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 workflow 部署从"整 bundle 复制进消费仓"改为"规则全局解析（resolver 脚本）+ 消费仓最小副本（仅 tools/）+ checkpoint 全局化"，并迁移运行 checkout 到 sdflow-skills 新仓。

**Architecture:** 三层——①`setup.sh` 建全局家 `~/.sdflow/`（canonical 软链/指针 + hack 脚本）；②新增确定性脚本 `resolve-workflow.sh` 实现三步解析链（本地 any-of pin → 全局 canonical → 退出码 2 显式降级），skills 只调用；③`init.py` 部署分层（copy_bundle 只铺 tools/、handle_config 改读 BUNDLE_SRC、update 陈旧遮蔽告警 + `--dev` 整刷）。

**Tech Stack:** bash（setup.sh / resolve-workflow.sh）、Python3 + pytest（init.py 及测试）、Markdown（SKILL.md / snippets / 新 skill sdflow-upgrade）。

## Global Constraints

（逐字来自 design.md §三/§五/§七 + spec-review-report D1–D10 + 设计门拍板，每任务隐含遵守）

- resolver 契约：`--root` 缺省 `git rev-parse --show-toplevel`；env `${SDFLOW_HOME:-$HOME/.sdflow}`；步① **any-of 即 pin** + 部分残留 stderr 专门告警；步② 命中后最小健全性检查（workflow.md 非空 + spec-checklists/ + code-checklists/ 存在，不过检按缺失处理）；步③ = **退出码 2 + stderr 固定告警文案**；`--explain` 输出来源诊断；stdout = 规则根路径（唯一 stdout）。
- 调用方：先 `[ -x ]` 判**脚本自身缺失**（专属"重跑 setup"文案）——与步③ bundle 缺失是两个不同告警，MUST NOT 混同；MUST NOT 静默吞非零退出码；MUST NOT 在指令内自行重实现三步链。
- 测试一律经 `SDFLOW_HOME` / `HOME` / `CLAUDE_CONFIG_DIR` 重定向到 `tmp_path`，**绝不写真实 `$HOME`**（先例：test_init.py:106 `monkeypatch.setenv("CLAUDE_CONFIG_DIR", ...)`）。
- 迁移**绝不自动删**消费仓文件（残留规则、旧 hack/ 副本都只告警）。
- `[checkpoint]` 约定等规则文本改动**只改 `opsx-project-init/assets/workflow/`（权威源）**；本仓 `openspec/workflow/` instance 勿手改（同步走 Task 6 的 `update --dev`，在 Task 10 执行）。
- canonical 建链**所有权检查**：只接管自属软链/指针；`~/.sdflow/workflow` 为真实目录（异物）→ 停手告警不覆盖；`~/.sdflow/` 其余视为本工具独占命名空间。
- 子代理 **Edit 前必须先 Read 目标文件**（否则报 "Error editing file"）。
- 每任务末：跑该任务的 pytest（及全量 `python3 -m pytest opsx-project-init/tests/ -q` 回归）确认通过无 warning → `bash hack/checkpoint-commit.sh <task-id> "<描述>"`（注意：用本仓 `hack/checkpoint-commit.sh`，它 `git add -A` 后按固定格式提交）。
- 激活验证（Task 10）的 ✅ 证据锚点 = **真实调用输出**（`resolve-workflow.sh --explain` 的 stderr/stdout 原文），禁用"文本已改"。

---

### Task 1: 迁移运行 checkout（0.1，最先，未完成禁止 Task 3 的 canonical 建链上线）

**Files:**
- Create: `openspec/changes/minimize-repo-footprint/activation-log.md`（证据锚点收集文件）

**Interfaces:**
- Produces: `~/.skills/sdflow-skills/`（后续所有"运行 checkout"所指）；activation-log.md（Task 10 继续追加）

- [ ] **Step 1: clone 新仓到运行位**

```bash
git clone https://github.com/laodao-ai/sdflow-skills.git ~/.skills/sdflow-skills
```
Expected: clone 成功。若目录已存在则 `git -C ~/.skills/sdflow-skills remote get-url origin` 必须输出 `https://github.com/laodao-ai/sdflow-skills.git`，否则停止并报告。

- [ ] **Step 2: 在新运行 checkout 跑 setup**

```bash
cd ~/.skills/sdflow-skills && bash setup.sh
```
Expected: 输出 `installed (N)` 列表。setup.sh:51-59 的所有权守卫只保护"非软链真实目录"，旧 symlink（指向 laodao-skills）会被 `ln -snf` 直接替换——这是预期行为。

- [ ] **Step 3: 验证软链已切换**

```bash
readlink ~/.claude/skills/spec-review; readlink ~/.codex/skills/spec-review
```
Expected: 均输出 `/Users/cheneyzhao/.skills/sdflow-skills/spec-review`。旧 `~/.skills/laodao-skills` **保留不删**（处置归 extract-sdflow-repo）。

- [ ] **Step 4: 把三条命令的实际输出写入 activation-log.md**（新建文件，标题 `# activation-log — 真实调用证据锚点`，一段 `## Task1 运行 checkout 迁移` 贴原始输出）

- [ ] **Step 5: Commit**

```bash
bash hack/checkpoint-commit.sh task1-migrate-runtime "迁移运行 checkout → ~/.skills/sdflow-skills（0.1，含验证输出）"
```

### Task 2: resolve-workflow.sh 主链（3.1 前半：契约 + 三条 happy path）

**Files:**
- Create: `opsx-project-init/assets/hack/resolve-workflow.sh`
- Test: `opsx-project-init/tests/test_resolve_workflow.py`

**Interfaces:**
- Produces: `resolve-workflow.sh [--root DIR] [--explain]`；stdout=规则根路径；exit 0/2/64；env `SDFLOW_HOME`。后续任务（4/8/10）依赖此契约原样。

- [ ] **Step 1: 写失败测试（本地 pin / 全局软链 / 全局指针 三条 happy path）**

```python
"""Tests for resolve-workflow.sh（三步链契约）。SDFLOW_HOME 一律重定向，绝不写真实 $HOME。"""
import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "assets" / "hack" / "resolve-workflow.sh"


def run_resolve(cwd, sdflow_home, args=()):
    env = dict(os.environ, SDFLOW_HOME=str(sdflow_home))
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=str(cwd), env=env, capture_output=True, text=True)


def make_bundle(path):
    """一个健全的 bundle：workflow.md 非空 + 两个清单目录。"""
    path.mkdir(parents=True)
    (path / "workflow.md").write_text("# wf\n", encoding="utf-8")
    (path / "spec-checklists").mkdir()
    (path / "code-checklists").mkdir()
    return path


def make_repo(path, with_rules=False):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    wf = path / "openspec" / "workflow"
    (wf / "tools").mkdir(parents=True)          # tools/ 恒存在——判据必须查规则本体
    if with_rules:
        (wf / "workflow.md").write_text("# pinned\n", encoding="utf-8")
        (wf / "spec-checklists").mkdir()
        (wf / "code-checklists").mkdir()
    return path


class TestHappyPaths:
    def test_local_pin_hit(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=True)
        r = run_resolve(repo, tmp_path / "nonexistent-sdflow")
        assert r.returncode == 0
        assert r.stdout.strip() == str(repo / "openspec" / "workflow")

    def test_tools_only_repo_falls_to_global_symlink(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=False)
        bundle = make_bundle(tmp_path / "bundle")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        (sdflow / "workflow").symlink_to(bundle)
        r = run_resolve(repo, sdflow)
        assert r.returncode == 0
        assert Path(r.stdout.strip()).resolve() == bundle.resolve()

    def test_pointer_file_fallback(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=False)
        bundle = make_bundle(tmp_path / "bundle")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        (sdflow / "workflow-path").write_text(str(bundle) + "\n", encoding="utf-8")
        r = run_resolve(repo, sdflow)
        assert r.returncode == 0
        assert r.stdout.strip() == str(bundle)

    def test_script_is_executable(self):
        assert SCRIPT.stat().st_mode & stat.S_IXUSR
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest opsx-project-init/tests/test_resolve_workflow.py -v`
Expected: FAIL（脚本不存在 → subprocess 找不到文件 / returncode 非 0）

- [ ] **Step 3: 写脚本（完整实现，含步③与告警——边界测试在 Task 3 补）**

```bash
#!/usr/bin/env bash
# resolve-workflow.sh — workflow 规则根解析器（三步链的确定性执行体）
# 契约（minimize-repo-footprint R-MRF-2 / adr-0006 机队锚定：机械协议脚本化，skill 只调用）：
#   stdout : 规则根路径（唯一 stdout 输出）
#   exit 0 : 解析成功（本地 pin 或全局 canonical）
#   exit 2 : 全局 bundle 不可达/不完整 → 调用方显式降级通用评审 + 转发本脚本 stderr 告警
#   exit 64: 用法错误
# env: SDFLOW_HOME（缺省 ~/.sdflow；测试用它重定向，绝不写真实 $HOME）
set -euo pipefail

SDFLOW_HOME="${SDFLOW_HOME:-$HOME/.sdflow}"
ROOT=""
EXPLAIN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --root)    ROOT="${2:-}"; shift 2 ;;
    --explain) EXPLAIN=1; shift ;;
    *) echo "resolve-workflow: unknown arg: $1" >&2; exit 64 ;;
  esac
done

if [ -z "$ROOT" ]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

explain() {
  if [ "$EXPLAIN" -eq 1 ]; then echo "resolve-workflow: source=$1 path=$2" >&2; fi
}

# 步1：查本地"规则文件本体"（any-of 即 pin）。不查 openspec/workflow/ 目录——tools/ 使其恒存在。
LOCAL="$ROOT/openspec/workflow"
has_wf=0; has_spec=0; has_code=0
[ -f "$LOCAL/workflow.md" ] && has_wf=1
[ -d "$LOCAL/spec-checklists" ] && has_spec=1
[ -d "$LOCAL/code-checklists" ] && has_code=1
total=$((has_wf + has_spec + has_code))
if [ "$total" -gt 0 ]; then
  if [ "$total" -lt 3 ]; then
    echo "resolve-workflow: ⚠ 本仓规则副本部分残留（workflow.md=$has_wf spec-checklists=$has_spec code-checklists=$has_code）——按 pin 处理；想跟全局请删净、想 pin 请补齐" >&2
  fi
  explain "local-pin" "$LOCAL"
  echo "$LOCAL"
  exit 0
fi

# 步2：全局 canonical——试目录（Unix 软链透明命中）→ 否则读指针文件（Windows）。平台判断在此，skill 不判平台。
CANON=""
if [ -d "$SDFLOW_HOME/workflow" ]; then
  CANON="$SDFLOW_HOME/workflow"
elif [ -f "$SDFLOW_HOME/workflow-path" ]; then
  CANON="$(head -n1 "$SDFLOW_HOME/workflow-path" | tr -d '\r' | sed -e 's/[[:space:]]*$//')"
fi

sane() {  # 最小健全性检查：防 pull 半坏态静默广播（spec-review D2）
  [ -n "$1" ] && [ -s "$1/workflow.md" ] && [ -d "$1/spec-checklists" ] && [ -d "$1/code-checklists" ]
}

if sane "$CANON"; then
  explain "global-canonical" "$CANON"
  echo "$CANON"
  exit 0
fi

# 步3：显式降级（反静默守卫）——绝不静默当"本项目无此评审层"
echo "resolve-workflow: ✗ 全局 workflow bundle 不可达或不完整（SDFLOW_HOME=$SDFLOW_HOME）。skill 应显式降级为通用评审并告警。修复：在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh" >&2
exit 2
```

然后 `chmod +x opsx-project-init/assets/hack/resolve-workflow.sh`。

- [ ] **Step 4: 跑测确认通过**

Run: `python3 -m pytest opsx-project-init/tests/test_resolve_workflow.py -v`
Expected: 4 PASS，无 warning

- [ ] **Step 5: Commit**

```bash
bash hack/checkpoint-commit.sh task2-resolver-core "resolve-workflow.sh 三步链主体 + happy path 单测（3.1）"
```

### Task 3: resolver 边界用例（3.1 后半）

**Files:**
- Modify: `opsx-project-init/tests/test_resolve_workflow.py`（追加类）
- Modify（仅当测试暴露 bug 时）: `opsx-project-init/assets/hack/resolve-workflow.sh`

- [ ] **Step 1: 写失败/验证测试（追加到 test_resolve_workflow.py）**

```python
class TestEdgeCases:
    def test_partial_residue_pins_and_warns(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=False)
        (repo / "openspec" / "workflow" / "spec-checklists").mkdir()  # 只残留一个单元
        r = run_resolve(repo, tmp_path / "no-sdflow")
        assert r.returncode == 0                      # any-of 即 pin
        assert r.stdout.strip() == str(repo / "openspec" / "workflow")
        assert "部分残留" in r.stderr                  # 专门告警，不静默

    def test_global_missing_exits_2_with_guard_message(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=False)
        r = run_resolve(repo, tmp_path / "no-sdflow")
        assert r.returncode == 2
        assert r.stdout == ""
        assert "显式降级" in r.stderr and "setup.sh" in r.stderr

    def test_insane_bundle_treated_as_missing(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=False)
        bundle = tmp_path / "bundle"                  # 半坏：workflow.md 为空文件
        bundle.mkdir()
        (bundle / "workflow.md").touch()
        (bundle / "spec-checklists").mkdir()
        (bundle / "code-checklists").mkdir()
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        (sdflow / "workflow").symlink_to(bundle)
        r = run_resolve(repo, sdflow)
        assert r.returncode == 2                      # 健全性不过检 = 缺失

    def test_pointer_with_trailing_crlf_and_spaces(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=False)
        bundle = make_bundle(tmp_path / "bun dle")    # 路径含空格
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        (sdflow / "workflow-path").write_text(str(bundle) + "  \r\n", encoding="utf-8")
        r = run_resolve(repo, sdflow)
        assert r.returncode == 0
        assert r.stdout.strip() == str(bundle)

    def test_root_flag_overrides_cwd(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=True)
        sub = repo / "some" / "deep" / "dir"
        sub.mkdir(parents=True)
        r = run_resolve(sub, tmp_path / "no-sdflow", args=("--root", str(repo)))
        assert r.returncode == 0
        assert r.stdout.strip() == str(repo / "openspec" / "workflow")

    def test_explain_reports_source(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=True)
        r = run_resolve(repo, tmp_path / "no-sdflow", args=("--explain",))
        assert "source=local-pin" in r.stderr

    def test_unknown_arg_exits_64(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=True)
        r = run_resolve(repo, tmp_path / "no-sdflow", args=("--bogus",))
        assert r.returncode == 64
```

- [ ] **Step 2: 跑测**

Run: `python3 -m pytest opsx-project-init/tests/test_resolve_workflow.py -v`
Expected: 全 PASS（Task 2 的实现已覆盖这些行为；任一 FAIL 则修脚本至绿，修改处不得违反 Global Constraints 契约）

- [ ] **Step 3: Commit**

```bash
bash hack/checkpoint-commit.sh task3-resolver-edges "resolver 边界单测：部分残留/健全性/指针CRLF/--root/--explain/退出码（5.3）"
```

### Task 4: setup.sh 建 ~/.sdflow（1.1/1.2 + hack 全局装）

**Files:**
- Modify: `setup.sh`（在 `cleanup_orphans` 函数后、`for d in "${TARGET_DIRS[@]}"` 循环前插入函数；循环后调用）
- Test: `opsx-project-init/tests/test_setup_sdflow.py`

**Interfaces:**
- Consumes: `opsx-project-init/assets/hack/resolve-workflow.sh`（Task 2）
- Produces: `$SDFLOW_HOME/workflow`（软链，Unix）/ `$SDFLOW_HOME/workflow-path`（指针，Windows）/ `$SDFLOW_HOME/hack/{checkpoint-commit.sh,resolve-workflow.sh}`（可执行拷贝）

- [ ] **Step 1: 写失败测试**

```python
"""setup.sh 的 ~/.sdflow 建链测试。HOME/SDFLOW_HOME 全部重定向 tmp_path。"""
import os
import stat
import subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent.parent


def run_setup(tmp_path):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
    r = subprocess.run(["bash", str(REPO / "setup.sh")],
                       env=env, capture_output=True, text=True)
    return r, home / ".sdflow"


class TestInstallSdflow:
    def test_creates_canonical_symlink_and_hack_scripts(self, tmp_path):
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0
        link = sdflow / "workflow"
        assert link.is_symlink()
        assert link.resolve() == (REPO / "opsx-project-init" / "assets" / "workflow").resolve()
        for name in ("checkpoint-commit.sh", "resolve-workflow.sh"):
            f = sdflow / "hack" / name
            assert f.is_file() and not f.is_symlink()      # 拷贝，非软链
            assert f.stat().st_mode & stat.S_IXUSR          # exec 位一次设好

    def test_idempotent_rerun(self, tmp_path):
        run_setup(tmp_path)
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0
        assert (sdflow / "workflow").is_symlink()

    def test_foreign_real_dir_not_clobbered(self, tmp_path):
        home = tmp_path / "home"
        (home / ".sdflow" / "workflow").mkdir(parents=True)   # 异物：真实目录
        (home / ".sdflow" / "workflow" / "alien.txt").write_text("x", encoding="utf-8")
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0
        assert not (sdflow / "workflow").is_symlink()          # 未接管
        assert (sdflow / "workflow" / "alien.txt").exists()    # 数据未破坏
        assert "未接管" in (r.stdout + r.stderr)               # 停手告警显形
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest opsx-project-init/tests/test_setup_sdflow.py -v`
Expected: FAIL（`~/.sdflow` 未被创建）

- [ ] **Step 3: 改 setup.sh——插入函数（放 cleanup_orphans 之后）并在主循环后调用**

```bash
# ─── sdflow global home: canonical bundle anchor + hack scripts ──
# canonical 只接管自属软链/指针（对齐 skills 的所有权守卫）；~/.sdflow 其余视为本工具独占命名空间。
install_sdflow() {
  local sdflow="${SDFLOW_HOME:-$HOME/.sdflow}"
  local bundle="$REPO_DIR/opsx-project-init/assets/workflow"
  mkdir -p "$sdflow/hack"

  if [ "$IS_WINDOWS" -eq 1 ]; then
    printf '%s\n' "$bundle" > "$sdflow/workflow-path"
    installed+=("workflow-path @ $sdflow")
  else
    if [ -e "$sdflow/workflow" ] && [ ! -L "$sdflow/workflow" ]; then
      skipped+=("workflow @ $sdflow — 真实目录非本工具软链，未接管")
    else
      ln -snf "$bundle" "$sdflow/workflow"
      installed+=("workflow @ $sdflow")
    fi
  fi

  local f base
  for f in "$REPO_DIR/opsx-project-init/assets/hack/"*.sh; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    cp "$f" "$sdflow/hack/$base"
    chmod +x "$sdflow/hack/$base"
    installed+=("hack/$base @ $sdflow")
  done
}
```

调用点（原主循环之后）：

```bash
for d in "${TARGET_DIRS[@]}"; do
  install_into "$d"
  cleanup_orphans "$d"
done
install_sdflow
```

- [ ] **Step 4: 跑测确认通过 + 全量回归**

Run: `python3 -m pytest opsx-project-init/tests/ -q`
Expected: 全 PASS 无 warning

- [ ] **Step 5: Commit**

```bash
bash hack/checkpoint-commit.sh task4-setup-sdflow "setup.sh 建 ~/.sdflow canonical(所有权守卫)+hack 全局装（1.1/1.2/2.2 安装侧）"
```

### Task 5: init.py 部署分层（2.1 只铺 tools / 2.2 不再进仓 hack / 2.5 handle_config 读 BUNDLE_SRC）

**Files:**
- Modify: `opsx-project-init/scripts/init.py:91-95`（copy_bundle）、`:132-151`（删 copy_hack）、`:165-174`（handle_config）、`:241-296`（run 内对应调用与文案）
- Modify: `opsx-project-init/tests/test_init.py:83-96`（TestCopyHack 改写）
- Test: 追加 `opsx-project-init/tests/test_init.py` 新类

- [ ] **Step 1: 写失败测试（追加到 test_init.py；同时把 TestCopyHack 整类替换为下面的 TestNoConsumerHack）**

```python
class TestNoConsumerHack:
    """checkpoint 全局化（~/.sdflow/hack/，由 setup.sh 安装）：init/update 不再往消费仓铺 hack/。"""

    def test_init_module_has_no_copy_hack(self):
        assert not hasattr(init_mod, "copy_hack")

    def test_run_does_not_create_consumer_hack_dir(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "fake-claude"))
        init_mod.run(str(tmp_path / "proj"), "init")
        assert not (tmp_path / "proj" / "hack").exists()


class TestBundleToolsOnly:
    """R-MRF-1：copy_bundle 只部署 tools/ 子树，规则文件数 = 0。"""

    def test_deploys_only_tools_subtree(self, tmp_path):
        dst, n = copy_bundle(str(tmp_path))
        wf = tmp_path / "openspec" / "workflow"
        assert (wf / "tools" / "engine.js").is_file()
        assert not (wf / "workflow.md").exists()
        assert not (wf / "spec-checklists").exists()
        assert not (wf / "code-checklists").exists()
        md_rules = [p for p in wf.rglob("*.md") if "tools" not in p.parts]
        assert md_rules == []                      # 规则文件数 = 0

    def test_full_flag_restores_whole_bundle(self, tmp_path):
        init_mod.copy_bundle(str(tmp_path), full=True)
        wf = tmp_path / "openspec" / "workflow"
        assert (wf / "workflow.md").is_file()      # --dev 整刷用（Task 7）


class TestHandleConfigFromBundleSrc:
    """2.5：config 模版改读 BUNDLE_SRC——消费仓无规则副本时 init 不得 FileNotFoundError。"""

    def test_init_creates_config_without_consumer_template(self, tmp_path):
        root = tmp_path / "proj"
        (root / "openspec").mkdir(parents=True)    # 无 workflow/config.template.yaml
        status, _ = init_mod.handle_config(str(root), "init")
        assert status == "created"
        assert (root / "openspec" / "config.yaml").is_file()
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest opsx-project-init/tests/test_init.py -v -k "NoConsumerHack or BundleToolsOnly or HandleConfigFromBundleSrc"`
Expected: FAIL（copy_hack 尚存在、copy_bundle 仍整拷、handle_config 读消费仓路径抛 FileNotFoundError）

- [ ] **Step 3: 改 init.py**

copy_bundle 替换为：

```python
def copy_bundle(root, full=False):
    """R-MRF-1 分层部署：默认只铺 tools/ 子树（规则经全局 canonical 解析，不复制进消费仓）。
    full=True 整 bundle 铺设——仅供 toolkit 源仓 `update --dev` dogfood 刷新 instance 用。"""
    dst = os.path.join(root, "openspec", "workflow")
    if full:
        shutil.copytree(BUNDLE_SRC, dst, dirs_exist_ok=True)
    else:
        shutil.copytree(os.path.join(BUNDLE_SRC, "tools"),
                        os.path.join(dst, "tools"), dirs_exist_ok=True)
    n = sum(len(fs) for _, _, fs in os.walk(dst))
    return dst, n
```

删除整个 `copy_hack` 函数（:132-151）与 run() 中的调用块（:262-266），调用处改为一行 report：

```python
    report.append("hack 脚本：不再铺进仓（checkpoint 已全局化 → ~/.sdflow/hack/，由 setup.sh 安装）")
```

handle_config 的 tmpl 行（:168）改为：

```python
    tmpl = os.path.join(BUNDLE_SRC, "config.template.yaml")
```

run() 末尾提示行（:296）改为：

```python
        print("  · 安装配套 skill：bash ~/.skills/sdflow-skills/setup.sh（/spec-review /impl-review /opsx-done）")
```

- [ ] **Step 4: 跑测确认通过 + 全量回归**

Run: `python3 -m pytest opsx-project-init/tests/ -q`
Expected: 全 PASS（TestReviewToolDeployment 不受影响——copy_bundle 默认仍铺 tools/，review-stub.html 在 tools/ 内）

- [ ] **Step 5: Commit**

```bash
bash hack/checkpoint-commit.sh task5-init-layered "init.py 部署分层：copy_bundle 只 tools/(+full)/去 copy_hack/handle_config 读 BUNDLE_SRC（2.1/2.2/2.5）"
```

### Task 6: update 陈旧遮蔽告警（4.1/4.2）

**Files:**
- Modify: `opsx-project-init/scripts/init.py`（新增 `stale_shadow_warnings`；run() update 分支打印）
- Test: 追加 `opsx-project-init/tests/test_init.py`

- [ ] **Step 1: 写失败测试**

```python
class TestStaleShadowWarnings:
    """R-MRF-3：残留规则/孤儿 checkpoint 只告警绝不删（反静默守卫·陈旧遮蔽变体）。"""

    def _legacy_consumer(self, tmp_path):
        root = tmp_path / "old"
        wf = root / "openspec" / "workflow"
        wf.mkdir(parents=True)
        (wf / "workflow.md").write_text("# old rules\n", encoding="utf-8")
        (root / "hack").mkdir()
        (root / "hack" / "checkpoint-commit.sh").write_text("#!/bin/bash\n", encoding="utf-8")
        return root

    def test_warns_on_residual_rules_and_orphan_hack_without_deleting(self, tmp_path):
        root = self._legacy_consumer(tmp_path)
        warns = init_mod.stale_shadow_warnings(str(root))
        assert any("遮蔽" in w for w in warns)
        assert any("checkpoint-commit.sh" in w for w in warns)
        assert (root / "openspec" / "workflow" / "workflow.md").exists()   # 绝不删
        assert (root / "hack" / "checkpoint-commit.sh").exists()

    def test_clean_consumer_no_warnings(self, tmp_path):
        root = tmp_path / "clean"
        (root / "openspec" / "workflow" / "tools").mkdir(parents=True)
        assert init_mod.stale_shadow_warnings(str(root)) == []

    def test_update_prints_warnings(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "fake-claude"))
        root = self._legacy_consumer(tmp_path)
        init_mod.run(str(root), "update")
        out = capsys.readouterr().out
        assert "遮蔽" in out
        assert (root / "openspec" / "workflow" / "workflow.md").exists()
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest opsx-project-init/tests/test_init.py -v -k StaleShadow`
Expected: FAIL（stale_shadow_warnings 不存在）

- [ ] **Step 3: 实现（copy_bundle 函数后插入；run() 在 `cstat, cmsg = handle_config(...)` 前、update 模式下收集并入 report）**

```python
RULE_MARKERS = ("workflow.md", "spec-checklists", "code-checklists")


def stale_shadow_warnings(root):
    """反静默守卫·陈旧遮蔽（R-MRF-3）：update 内联为主 + opsx-maintain 兜底（同款判据）。只告警，绝不删。"""
    warns = []
    wf = os.path.join(root, "openspec", "workflow")
    found = [m for m in RULE_MARKERS if os.path.exists(os.path.join(wf, m))]
    if found:
        warns.append(
            "⚠ openspec/workflow/ 残留规则副本（" + "、".join(found) + "）——遮蔽全局 bundle 且不再被 update 刷新："
            "想跟全局最新 → 手动删净；想 pin 这一版 → 留着（显式逃生口）")
    if os.path.isfile(os.path.join(root, "hack", "checkpoint-commit.sh")):
        warns.append(
            "⚠ hack/checkpoint-commit.sh 为旧版仓内副本（checkpoint 已全局化 → ~/.sdflow/hack/）："
            "本仓无规则副本 → 可删改用全局；若保留本地 workflow.md 副本（pin）且其仍引用仓内路径 → 勿删")
    return warns
```

run() 中（update 分支）：

```python
    if mode == "update":
        for w in stale_shadow_warnings(root):
            report.append(w)
```

- [ ] **Step 4: 跑测 + 全量回归**

Run: `python3 -m pytest opsx-project-init/tests/ -q`
Expected: 全 PASS

- [ ] **Step 5: Commit**

```bash
bash hack/checkpoint-commit.sh task6-stale-shadow "update 陈旧遮蔽告警(残留规则+checkpoint 孤儿)，绝不自动删（4.1/4.2）"
```

### Task 7: `update --dev` 整刷（5.6 机制）

**Files:**
- Modify: `opsx-project-init/scripts/init.py`（main() 加 `--dev`；run() 签名加 `dev=False` 透传 `copy_bundle(root, full=dev)`）
- Test: 追加 `opsx-project-init/tests/test_init.py`

- [ ] **Step 1: 写失败测试**

```python
class TestUpdateDev:
    """5.6：toolkit 源仓 dogfood 刷新——update --dev 整 bundle 刷 instance；普通 update 只 tools/。"""

    def _seeded(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "fake-claude"))
        root = tmp_path / "proj"
        init_mod.run(str(root), "init")
        return root

    def test_plain_update_does_not_deploy_rules(self, tmp_path, monkeypatch):
        root = self._seeded(tmp_path, monkeypatch)
        init_mod.run(str(root), "update")
        assert not (root / "openspec" / "workflow" / "workflow.md").exists()

    def test_dev_update_deploys_full_bundle(self, tmp_path, monkeypatch):
        root = self._seeded(tmp_path, monkeypatch)
        init_mod.run(str(root), "update", dev=True)
        assert (root / "openspec" / "workflow" / "workflow.md").is_file()
        assert (root / "openspec" / "workflow" / "spec-checklists").is_dir()
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest opsx-project-init/tests/test_init.py -v -k UpdateDev`
Expected: FAIL（run() 不接受 dev 参数）

- [ ] **Step 3: 实现**——`def run(root, mode, dev=False)`；copy_bundle 调用改 `dst, n = copy_bundle(root, full=dev)`；report 行加模式说明 `（--dev 整刷）` 当 dev；main()：

```python
    p.add_argument("--dev", action="store_true",
                   help="update 专用：整 bundle 刷新（toolkit 源仓 dogfood 用，消费仓勿用）")
    args = p.parse_args()
    if args.dev and args.mode != "update":
        _die("--dev 仅配 update 使用")
    run(args.root, args.mode, dev=args.dev)
```

- [ ] **Step 4: 跑测 + 全量回归**

Run: `python3 -m pytest opsx-project-init/tests/ -q`
Expected: 全 PASS

- [ ] **Step 5: Commit**

```bash
bash hack/checkpoint-commit.sh task7-update-dev "update --dev 整 bundle 刷新（源仓 dogfood 通道，5.6 机制）"
```

### Task 8: 权威源文案与 SKILL.md 读点改造（2.3 / 3.2 / 3.3 / 3.4）

**Files:**
- Modify: `opsx-project-init/assets/workflow/workflow.md`（两处 checkpoint 路径）
- Modify: `opsx-project-init/assets/workflow/config.template.yaml`（头注 + `@openspec/workflow` 引用说明）
- Modify: `opsx-project-init/assets/snippets/claude-section.md`、`opsx-project-init/assets/snippets/index-section.md`
- Modify: `spec-review/SKILL.md`（读点 3 处 + checkpoint 行）、`impl-review/SKILL.md`（读点 4 处 + checkpoint 行）

（纯 Markdown，无单测；验证 = grep 断言，Edit 前先 Read 目标文件）

- [ ] **Step 1: assets/workflow/workflow.md**——`[checkpoint]` 约定行（"## 二"引言处）：`hack/checkpoint-commit.sh <step>` → `~/.sdflow/hack/checkpoint-commit.sh <step>`，句尾加"（缺失则先在运行 checkout 跑 setup.sh）"；"## 三"决策 5 同句替换 `hack/checkpoint-commit.sh` → `~/.sdflow/hack/checkpoint-commit.sh`。步骤 6/7 prompt 中 `@openspec/workflow/code-checklists/domains/<命中栈>` → `code-checklists/domains/<命中栈>（规则根经 ~/.sdflow/hack/resolve-workflow.sh 解析）`。

- [ ] **Step 2: config.template.yaml**——头注第 4 行"把整个 openspec/workflow/ 拷入新项目（rules 引用其中文件，缺则断链）"改为"规则经全局 canonical（~/.sdflow/workflow）解析，仓内仅 tools/；下文 @openspec/workflow/... 引用在无本地副本的仓中 = 全局 bundle 内同名文件（resolve-workflow.sh 输出根）"。第 21 行"spec 质量规则集见 openspec/workflow/："后加"（无本地副本时为 ~/.sdflow/workflow/，下同）"。38/39/46 行的 `@openspec/workflow/...` 字面保留（有上述总注即可，不逐处改）。

- [ ] **Step 3: snippets**——claude-section.md 第 3 行改"端到端流程见 workflow 规则集 `workflow.md`（真相源；本仓有 `openspec/workflow/` 规则副本则用之，否则在全局 `~/.sdflow/workflow/`）"；第 6 行同款括号注；第 15 行"INDEX 同步"句加前缀"（仅规则副本 pin 仓/toolkit 源仓适用）"。index-section.md 表格上方加一行"> 无本地规则副本的仓：下表文件位于全局 canonical `~/.sdflow/workflow/`，相对链接不可点，以文件名为准。"

- [ ] **Step 4: spec-review/SKILL.md**——
  - :30 第零步第 2 条整行替换为："2. 规则根解析：`[ -x ~/.sdflow/hack/resolve-workflow.sh ]` 不成立 → 提示「resolve-workflow.sh 未安装——先在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh」并降级通用评审；否则 `RULES_ROOT=$(~/.sdflow/hack/resolve-workflow.sh --root "$(git rev-parse --show-toplevel)")`——退出码 2 → 显式降级通用评审并原样转发脚本 stderr 告警（绝不静默当"本项目无此评审层"）；成功 → 读 `$RULES_ROOT/spec-review.md`（方法论）、`$RULES_ROOT/trigger-catalog.md`（触发）。禁止自行重实现三步链。"
  - :15 描述行 `openspec/workflow/spec-review.md` → "workflow 规则集的 `spec-review.md`（经 resolve-workflow.sh 解析）"；正文其余 `openspec/workflow/spec-checklists` 类引用同款改 `$RULES_ROOT/spec-checklists`。
  - :113 注意项改："项目无关：规则路径一律经 `~/.sdflow/hack/resolve-workflow.sh` 解析（本地 pin 或全局 canonical），不硬编码 `openspec/workflow/`。"
  - checkpoint 注意行改："checkpoint 脚本 = `~/.sdflow/hack/checkpoint-commit.sh`（setup.sh 全局安装）；缺失则先跑 setup，或退化为普通 `git add -A && git commit`。"

- [ ] **Step 5: impl-review/SKILL.md**——同款四类改动：:56-57 第 3 条读点改 `$RULES_ROOT/code-checklists/README.md`、`$RULES_ROOT/.../code-review-base.md`、`$RULES_ROOT/trigger-catalog.md` + 前置 `[ -x ]` / 退出码 2 处理（文字与 Step 4 完全同构）；:16 描述行、:155 注意行、checkpoint 行同款。

- [ ] **Step 6: grep 验证**

```bash
grep -rn "hack/checkpoint-commit.sh" opsx-project-init/assets/workflow/workflow.md   # 只应剩 ~/.sdflow/ 前缀形式
grep -n "resolve-workflow.sh" spec-review/SKILL.md impl-review/SKILL.md              # 每文件 ≥1 处
grep -n "openspec/workflow/" spec-review/SKILL.md impl-review/SKILL.md               # 不应再有硬编码读点（描述性提及除外，逐条人审）
```

- [ ] **Step 7: Commit**

```bash
bash hack/checkpoint-commit.sh task8-readpoints "权威源 checkpoint 路径全局化 + config/snippets 全局解析措辞 + 两 SKILL.md 改调 resolver（2.3/3.2/3.3/3.4）"
```

### Task 9: sdflow-upgrade skill（7.1/7.2）

**Files:**
- Create: `sdflow-upgrade/SKILL.md`
- Modify: `README.md`（Skills 列表加行）

- [ ] **Step 1: 写 SKILL.md（完整内容）**

```markdown
---
name: sdflow-upgrade
description: 升级 sdflow 工具链运行 checkout（~/.skills/sdflow-skills）：git pull → bash setup.sh（skills 软链 + ~/.sdflow canonical/hack 同步刷新，堵 pull→setup 窗口期）→ 显示版本与最新变更，并提示消费仓按需跑 opsx-project-init update。当用户说"升级 sdflow"、"更新 sdflow skills"、"sdflow upgrade"、"sdflow 有新版本吗"、"刷新 sdflow"，或使用 /sdflow-upgrade 时触发。
---

# sdflow-upgrade — 运行 checkout 一键升级

对**运行 checkout** `~/.skills/sdflow-skills/` 执行升级三连。pull 与 setup 必须连跑——
SKILL.md 软链即时生效、`~/.sdflow/hack/` 脚本拷贝生效，只 pull 不 setup 会造成两者版本错位（陈旧遮蔽的脚本变体）。

## 步骤

1. **pull**：`git -C ~/.skills/sdflow-skills pull --ff-only`
   - 非 ff（本地被改过）→ 停下报告，不强推；提示"运行 checkout 只读，改动应发生在开发 checkout"。
2. **setup**：`bash ~/.skills/sdflow-skills/setup.sh`
   - 刷 skills 软链 + `~/.sdflow/workflow` canonical + `~/.sdflow/hack/{checkpoint-commit.sh,resolve-workflow.sh}`。
3. **展示**：`cat ~/.skills/sdflow-skills/VERSION 2>/dev/null || echo unknown` + `git -C ~/.skills/sdflow-skills log --oneline -5`，向用户汇报版本与最新变更。
4. **提示**：各消费仓如需拿最新 tools/ 或看陈旧遮蔽告警 → 在该仓跑 `opsx-project-init update`（本 skill 不代跑）。

## 回滚

推坏一版规则时：`git -C ~/.skills/sdflow-skills checkout <上一已知良好 commit> && bash ~/.skills/sdflow-skills/setup.sh`。

## 注意

- 只动运行 checkout；开发 checkout（编辑规则/skill 的 clone）不归本 skill 管。
- 运行 checkout remote 必须是 `laodao-ai/sdflow-skills.git`——不是则先按 minimize-repo-footprint 的 0.1 迁移。
```

- [ ] **Step 2: README.md Skills 列表加一行**（先 Read README 找到列表表格，按现有格式追加）：`| sdflow-upgrade | 运行 checkout 一键升级：pull → setup → 版本展示（堵 pull→setup 窗口期） |`（列数以实际表格为准）

- [ ] **Step 3: 验证**：`ls sdflow-upgrade/SKILL.md`；`grep -c sdflow-upgrade README.md` ≥ 1。新链接待运行 checkout pull 后由 setup.sh 自动建（本 change 合并后经 /sdflow-upgrade 首跑生效），**不在开发 checkout 跑 setup 建链**。

- [ ] **Step 4: Commit**

```bash
bash hack/checkpoint-commit.sh task9-sdflow-upgrade "新增 sdflow-upgrade skill + README 列表（7.1/7.2）"
```

### Task 10: instance 同步 + 激活验证（5.6 执行 / 5.7 / 6.1）

**Files:**
- Modify: `openspec/workflow/`（经 update --dev 整刷，非手改）
- Modify: `openspec/changes/minimize-repo-footprint/activation-log.md`（追加证据）
- Modify: `openspec/changes/minimize-repo-footprint/design.md`（§六表追加 issues.py 落点决策一行）

- [ ] **Step 1: 同步本仓 instance（5.6 执行）**

```bash
python3 opsx-project-init/scripts/init.py update --dev --root .
diff -q openspec/workflow/workflow.md opsx-project-init/assets/workflow/workflow.md
```
Expected: diff 无输出（instance 与 assets 一致，dogfood 悖论消除）。

- [ ] **Step 2: 建全局家（知情临时指 dev——本机无外部消费者，design §五）**

```bash
bash setup.sh
ls -la ~/.sdflow/ ~/.sdflow/hack/
```
Expected: `~/.sdflow/workflow` 软链 → 本仓 assets/workflow；hack/ 两脚本可执行。⚠ 此步会把 `~/.claude/skills/*` 软链临时指向开发 checkout——**合并后须在运行 checkout 重跑 setup 还原**（写进 hand-off，opsx-done 收尾提醒）。

- [ ] **Step 3: 真实调用验证（5.7 证据锚点）**

```bash
~/.sdflow/hack/resolve-workflow.sh --root . --explain          # 期望: source=local-pin（本仓有规则副本）
TMP=$(mktemp -d) && python3 opsx-project-init/scripts/init.py init --root "$TMP" \
  && (cd "$TMP" && git init -q . && ~/.sdflow/hack/resolve-workflow.sh --explain)   # 期望: source=global-canonical
find "$TMP/openspec/workflow" -name "*.md" -not -path "*/tools/*" | wc -l           # 期望: 0（新 init 仓规则数=0）
rm -rf "$TMP"
```

- [ ] **Step 4: Codex 侧实测（A1-P5）**

```bash
codex exec 'bash ~/.sdflow/hack/resolve-workflow.sh --root . --explain' 2>&1 | tail -5
```
Expected: 输出含 `source=local-pin`。若 Codex 沙盒拒绝读 `~/.sdflow` → 原样记录输出，并用 todolist-recorder 记一条（Codex 沙盒放行问题，关联本 change）。

- [ ] **Step 5: 全部原始输出追加进 activation-log.md**（`## Task10 激活验证` 段），并在 design.md §六组件清单表后追加一行决策记录："issues.py 落点〔6.1 决策〕：留 `issues-recorder/scripts/`（随 skill 软链全局可用，不迁 ~/.sdflow——它是 skill 私有脚本，非跨 skill 共享协议）"。

- [ ] **Step 6: 全量回归**

Run: `python3 -m pytest opsx-project-init/tests/ -q && python3 -m pytest buglist-recorder/tests/ todolist-recorder/tests/ issues-recorder/tests/ -q`
Expected: 全 PASS

- [ ] **Step 7: Commit**

```bash
bash hack/checkpoint-commit.sh task10-activation "update --dev 同步 instance + setup 建 ~/.sdflow + resolver 真实调用验证(local-pin/global/Codex) + 6.1 落点决策"
```

### Task 11: 文档纪律收口（5.1/5.5 + ROADMAP）

**Files:**
- Modify: `CLAUDE.md`（常用命令节 + 新纪律段）
- Modify: `openspec/ROADMAP.md`（footprint 状态）

- [ ] **Step 1: CLAUDE.md**（Read 后改）——
  - 「常用命令」安装节句子"改动 skill 源码后一般无需重跑（symlink 场景）；仅在**新增/删除**顶层 skill 后重跑"追加例外："**改 `opsx-project-init/assets/hack/` 下脚本后也必须重跑 `setup.sh`**（它们拷贝进 `~/.sdflow/hack/`，非 symlink，不重跑 = 新 SKILL 调旧脚本）。"
  - 「架构」区新增小节 `### dev/runtime checkout 纪律（adr/0005 + 设计门拍板）`，内容四句：运行 checkout = `~/.skills/sdflow-skills`（只 pull + setup，日常用 `/sdflow-upgrade`；remote 必须 = `laodao-ai/sdflow-skills.git`）；开发 checkout = 本仓（编辑 + local-first dogfood；改规则免 setup、改 skill/hack 脚本须 setup-from-dev 才测得到）；发布边界 = push → pull → setup（pull 后必须立即 setup）；回滚 = 运行 checkout `git checkout <last-good>` + 重跑 setup。
- [ ] **Step 2: ROADMAP.md**——`minimize-repo-footprint` 行状态改"🔵 实现完成（待 impl-review/opsx-done）"。
- [ ] **Step 3: Commit**

```bash
bash hack/checkpoint-commit.sh task11-docs "CLAUDE.md dev/runtime 纪律段+hack 重跑例外句；ROADMAP 状态（5.1/5.5）"
```

---

## Self-Review 结论

- Spec 覆盖：R-MRF-1 → Task 1/4/5/9/11；R-MRF-2 → Task 2/3/8/10；R-MRF-3 → Task 6；tasks.md 0→7 全部有对应（2.4 serve.sh 保持 = 无操作项，Task 5 回归测试覆盖；5.4 迁移测试并入 Task 6）。
- 占位符扫描：无 TBD/TODO；所有代码步含完整代码；文案步含逐字替换文本。
- 类型/签名一致性：`copy_bundle(root, full=False)`（Task 5 定义，Task 7/10 使用一致）；`run(root, mode, dev=False)`；`stale_shadow_warnings(root)`；resolver 退出码 0/2/64 全文一致。
- 顺序依赖：Task 1（迁移）在前；Task 10 的 setup 依赖 Task 2/4；Task 8 只改 assets，instance 由 Task 10 Step 1 统一同步——满足"只改权威源"约束。
