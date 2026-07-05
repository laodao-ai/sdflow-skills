# review-tool-followups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 收尾 drop-per-dir-review-stub 的两残差——T44 把退役 hook 自愈接进 setup.sh、T45 让 review.html 恢复 scoped 深链。

**Architecture:** T44 给 `init.py` 加独立 `retire-hooks` CLI mode（早分支、复用 `retire_hooks()`），`setup.sh` fail-safe 调之；`_deregister` 改原子写。T45 改 `engine.js` bootstrap 读 hash 定初始 scope，自派发渲染 + 404 回落显形。

**Tech Stack:** Python 3（init.py，pytest）· Bash（setup.sh）· 原生 JS（engine.js，无 pytest→手测）。

## Global Constraints

- 每个任务的 commit 步 MUST 用 `bash ~/.sdflow/hack/checkpoint-commit.sh review-tool-followups:task<N>-<slug>`（命名空间格式，gate 只认本 change 标签）。
- 改 `init.py` → 必跑 `python3 -m pytest sdflow-init/tests/ -q` 零回归。
- 测试沿用 `sdflow-init/tests/test_init.py` 既有范式：`sys.path.insert` + `import init as init_mod`；临时目录 `home = tmp_path/"home"; home.mkdir(); monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))`。
- **改 `assets/workflow/tools/engine.js` 或 `setup.sh` 后须在开发 checkout 重跑一次 `bash setup.sh` 才测得到**（dev checkout 纪律）。
- 机制细节真相源 = `tasks.md` + `design.md`（ADR-1/2）+ `spec-review-report.md`（A1–A9、Q-D1/D2/D3）。**勿重新发明，照 A 编号机制走。**

---

### Task 1: init.py `retire-hooks` CLI mode（T44 · A4）

**Files:**
- Modify: `sdflow-init/scripts/init.py`（`main()` ~424-432 加早分支；argparse mode choices ~426）
- Test: `sdflow-init/tests/test_init.py`（追加 `TestRetireHooksCli` 类）

**Interfaces:**
- Consumes: 既有 `retire_hooks()`（init.py:319，返回多行汇总字符串）、`_home_claude()`（读 `CLAUDE_CONFIG_DIR or ~/.claude`）。
- Produces: `init.py retire-hooks` CLI 入口——只调 `retire_hooks()` 并 print，**不碰 `openspec/`、不铺 bundle**。

- [ ] **Step 1: Write the failing tests**

追加到 `sdflow-init/tests/test_init.py`：

```python
class TestRetireHooksCli:
    """T44: `init.py retire-hooks` 独立 mode——只调 retire_hooks()，不需 openspec/。"""

    def test_retire_hooks_mode_cleans_stale_hook(self, tmp_path, monkeypatch, capsys):
        home = tmp_path / "home"
        (home / "hooks").mkdir(parents=True)
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        (home / "hooks" / "change-review-stub.py").write_text("# stale\n", encoding="utf-8")
        (home / "settings.json").write_text(json.dumps({"hooks": {"PostToolUse": [
            {"matcher": "Bash", "hooks": [
                {"type": "command", "command": 'python3 "$HOME/.claude/hooks/change-review-stub.py"'}]}
        ]}}), encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["init.py", "retire-hooks"])
        init_mod.main()
        assert not (home / "hooks" / "change-review-stub.py").exists()
        data = json.loads((home / "settings.json").read_text(encoding="utf-8"))
        assert data["hooks"]["PostToolUse"] == []          # 仅剩退役 hook 的 entry 被整条丢弃
        assert "change-review-stub.py" in capsys.readouterr().out

    def test_retire_hooks_mode_needs_no_openspec(self, tmp_path, monkeypatch, capsys):
        # 关键：retire-hooks 分支须在 osroot 检查之前，从无 openspec/ 的 cwd 跑也不 _die
        home = tmp_path / "home"; home.mkdir()
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        monkeypatch.chdir(tmp_path)                         # cwd 无 openspec/
        monkeypatch.setattr(sys, "argv", ["init.py", "retire-hooks"])
        init_mod.main()                                    # 不得 SystemExit
        assert "无退役 hook 残留" in capsys.readouterr().out  # fresh → no-op
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest sdflow-init/tests/test_init.py::TestRetireHooksCli -v`
Expected: FAIL —— `main()` 现在 argparse `choices=["init","update"]`，`retire-hooks` 被拒（SystemExit 2）。

- [ ] **Step 3: Add the mode + early branch**

`sdflow-init/scripts/init.py` `main()`——argparse choices 加 `retire-hooks`，并在 `parse_args()` 后**最早处**分支（先于 `--dev` 检查与 `run()`，故绕过 `run()` 的 osroot 检查）：

```python
def main():
    p = argparse.ArgumentParser(description="把 openspec/workflow bundle 铺进项目")
    p.add_argument("mode", choices=["init", "update", "retire-hooks"], help="init=首次铺设 / update=重拉最新 bundle / retire-hooks=只反注册退役 hook（自愈，不碰 openspec/）")
    p.add_argument("--root", default=".", help="目标项目根（默认当前目录）")
    p.add_argument("--dev", action="store_true",
                   help="update 专用：整 bundle 刷新（toolkit 源仓 dogfood 用，消费仓勿用）")
    args = p.parse_args()
    if args.mode == "retire-hooks":       # A4: 早分支，先于 osroot/dev——只自愈全局 hook，与项目无关
        print("退役 hook 清理：\n" + retire_hooks())
        return
    if args.dev and args.mode != "update":
        _die("--dev 仅配 update 使用")
    run(args.root, args.mode, dev=args.dev)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest sdflow-init/tests/test_init.py::TestRetireHooksCli -v`
Expected: PASS（2 passed）。

- [ ] **Step 5: Full regression**

Run: `python3 -m pytest sdflow-init/tests/ -q`
Expected: 全绿零回归。

- [ ] **Step 6: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh review-tool-followups:task1-retire-cli
```

---

### Task 2: settings.json 原子写（T44 · Q-D1 · NEW-2）

**Files:**
- Modify: `sdflow-init/scripts/init.py`（`_deregister_hook_in_settings` 的写块 ~313-315）
- Test: `sdflow-init/tests/test_init.py`（`TestRetireHooksCli` 追加）

**Interfaces:**
- Produces: `_deregister` 用 temp 文件 + `os.replace` 原子落 settings.json（消除撕裂 JSON / 丢更新，且防坏 JSON 被 fail-safe 读静默 no-op 掩盖）。

- [ ] **Step 1: Write the failing test**

```python
    def test_settings_write_is_atomic_no_tmp_residue(self, tmp_path, monkeypatch):
        home = tmp_path / "home"; (home / "hooks").mkdir(parents=True)
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        settings = home / "settings.json"
        settings.write_text(json.dumps({"hooks": {"PostToolUse": [
            {"matcher": "Bash", "hooks": [
                {"type": "command", "command": 'python3 "$HOME/.claude/hooks/change-review-stub.py"'}]}
        ]}}), encoding="utf-8")
        assert init_mod._deregister_hook_in_settings(str(settings), "change-review-stub.py") is True
        # 原子落地：结果是合法 JSON，且不留 .tmp 残渣
        json.loads(settings.read_text(encoding="utf-8"))          # 不抛 = 未撕裂
        assert not (home / "settings.json.tmp").exists()
        assert list(home.glob("*.tmp")) == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m pytest sdflow-init/tests/test_init.py::TestRetireHooksCli::test_settings_write_is_atomic_no_tmp_residue -v`
Expected: 现实现是 in-place `open(settings,"w")`——测试对 `.tmp` 的断言此刻会通过（无 tmp），但本步的意义是**锁住原子契约**；若担心空测，先临时把实现改成写 `settings+".tmp"` 但**不** replace 来验证测试能抓到残渣（可选），再进 Step 3。

- [ ] **Step 3: Atomic write**

`_deregister_hook_in_settings` 尾部写块（~313-315）改为：

```python
    if changed:
        tmp = settings + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, settings)   # 原子替换（POSIX + Windows 同名卷内保证）
    return changed
```

- [ ] **Step 4: Run + regression**

Run: `python3 -m pytest sdflow-init/tests/ -q`
Expected: 全绿。

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh review-tool-followups:task2-atomic-settings
```

---

### Task 3: setup.sh 接线 + 集成测试（T44 · A5 · A6）

**Files:**
- Modify: `setup.sh`（`install_sdflow` 调用后 ~158、Summary ~160 之前插入）
- Test: `sdflow-init/tests/test_setup_failsafe.py`（新建）

**Interfaces:**
- Consumes: `init.py retire-hooks`（Task 1）；`$REPO_DIR`（setup.sh:8）。

- [ ] **Step 1: Write the failing fail-safe test**

新建 `sdflow-init/tests/test_setup_failsafe.py`：

```python
import subprocess
from pathlib import Path

def test_retire_snippet_failsafe_under_set_e(tmp_path):
    """A5: set -e 下 python 非零退出仍不中止（尾 || echo 收尾）。"""
    fakebin = tmp_path / "bin"; fakebin.mkdir()
    py = fakebin / "python3"
    py.write_text("#!/bin/sh\nexit 1\n"); py.chmod(0o755)   # 假 python3 恒非零
    snippet = (
        'set -e\n'
        '_py=""\n'
        'command -v python3 >/dev/null 2>&1 && _py=python3\n'
        '[ -z "$_py" ] && command -v python >/dev/null 2>&1 && _py=python\n'
        'if [ -n "$_py" ]; then { "$_py" /nonexistent retire-hooks ; } || echo skipped; fi\n'
    )
    r = subprocess.run(["bash", "-c", snippet],
                       env={"PATH": f"{fakebin}:/usr/bin:/bin"},
                       capture_output=True, text=True)
    assert r.returncode == 0            # set -e 未中止
    assert "skipped" in r.stdout

def test_retire_snippet_probes_python_when_no_python3(tmp_path):
    """A6: 只有 `python`（无 `python3`）时也能跑（Windows/Git-Bash 命名）。"""
    fakebin = tmp_path / "bin"; fakebin.mkdir()
    py = fakebin / "python"
    py.write_text("#!/bin/sh\necho RAN_$*\n"); py.chmod(0o755)  # 只有 python
    snippet = (
        '_py=""\n'
        'command -v python3 >/dev/null 2>&1 && _py=python3\n'
        '[ -z "$_py" ] && command -v python >/dev/null 2>&1 && _py=python\n'
        'if [ -n "$_py" ]; then { "$_py" retire-hooks ; } || echo skipped; fi\n'
    )
    r = subprocess.run(["bash", "-c", snippet],
                       env={"PATH": f"{fakebin}"},          # 无 python3
                       capture_output=True, text=True)
    assert "RAN_retire-hooks" in r.stdout                    # 回落到 python
```

- [ ] **Step 2: Run to verify fail** (test file present, but confirm the snippet shape)

Run: `python3 -m pytest sdflow-init/tests/test_setup_failsafe.py -v`
Expected: PASS（这两测直接验 A5/A6 的 shell 构造本身；它们锁住 Step 3 要写进 setup.sh 的确切构造）。若 FAIL，说明构造不对，先修构造。

- [ ] **Step 3: Wire into setup.sh**

`setup.sh` 在 `install_sdflow`（line 158）之后、`# ─── Summary`（line 160）之前插入：

```bash
# ─── retire deregistered global hooks (T44) ─────────────────────
# 死 hook（change-review-stub.py）每次 Bash 调用都 fire 报错，直到被反注册。把自愈焊进
# 工具链升级路径，令 /sdflow-upgrade 即时清掉，不必等某项目跑 sdflow-init update。
# fail-safe：绝不中止 setup（清理是尽力而为，非安装必要步）。
_py=""
command -v python3 >/dev/null 2>&1 && _py=python3
[ -z "$_py" ] && command -v python >/dev/null 2>&1 && _py=python
if [ -n "$_py" ]; then
  { "$_py" "$REPO_DIR/sdflow-init/scripts/init.py" retire-hooks ; } || echo "  ⚠ retire-hooks 跳过（非致命）"
else
  echo "  ⚠ retire-hooks 跳过：PATH 无 python3/python（非致命）"
fi
```

- [ ] **Step 4: Manually sanity-run**

Run: `bash setup.sh 2>&1 | grep -i retire || echo "(clean machine: no-op, ok)"`
Expected: 无残留则 retire_hooks 打印"无退役 hook 残留"或本机已清则 no-op；setup 正常收尾、exit 0。

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh review-tool-followups:task3-setup-wire
```

---

### Task 4: README 文档（T44 · tasks 1.4）

**Files:**
- Modify: `README.md`（安装/更新 skills 段）

- [ ] **Step 1: Add the line**

在 README 描述 `setup.sh` / `/sdflow-upgrade` 处补一句：

> `setup.sh`（含 `/sdflow-upgrade`）现也触发退役 hook 自愈——升级工具链即清理存量死 hook（`change-review-stub.py`），不必等某项目跑 `sdflow-init update`。

（若 `CLAUDE.md` 的 `setup.sh 安装机制` 段需同步，补一句即可，**勿改托管区块内部**。）

- [ ] **Step 2: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh review-tool-followups:task4-readme
```

---

### Task 5: engine.js bootstrap 读 hash 深链（T45 · A1/A2/A3/A7/A8/F-D）

**Files:**
- Modify: `sdflow-init/assets/workflow/tools/engine.js`（`initialDir` ~100、`bootstrap()` ~265-278）
- Modify: `sdflow-init/assets/workflow/tools/engine.css`（加 `.deep-link-notice` 样式）
- Test: 无 pytest → 手测（Task 6 的四态）

**Interfaces:**
- Consumes: 既有 `loadDir(path)`、`loadDoc(path)`、`content`/`contentBody` DOM、`currentPath`、`window.location`。
- Produces: bootstrap 支持 `#<同源路径>` 深链首屏 + 陈旧 404 回落显形。

- [ ] **Step 1: Replace `initialDir` const with hash-aware resolver (A3/A8/A7)**

engine.js:100 `const initialDir = window.location.pathname.replace(/[^/]*$/, '');` 改为：

```js
    // A3: 深链来源优先级 hash → pathname。hash 经同一 origin 检查后**取 url.pathname**
    // （非 raw hash 原样——`#http://host/changes/X/` 同源但非 /path 形态；提取 pathname
    // 顺带归一 %2F 编码）。跨源 / 畸形 hash 回落 pathname。A8: let（供 currentPath+popstate 共用）。
    function resolveInitialDir() {
      const raw = window.location.hash.slice(1);   // 去前导 '#'
      if (raw) {
        try {
          const u = new URL(raw, window.location.origin);
          if (u.origin === window.location.origin) return u.pathname;
        } catch (e) { /* 畸形 hash → 回落 */ }
      }
      return window.location.pathname.replace(/[^/]*$/, '');
    }
    let initialDir = resolveInitialDir();
```

（`#/` → `raw='/'` → `new URL('/',origin).pathname === '/'` → initialDir `'/'` → 走下方 INDEX 分支，与无-hash 一致，A7。）

- [ ] **Step 2: Rewrite `bootstrap()` — self-dispatch + anti-recursion + notice (A1/A2/F-D)**

engine.js:265-278 `bootstrap()` 改为：

```js
    async function bootstrap() {
      if (initialDir === '/') {
        try { await loadDoc('/INDEX.md'); currentPath = '/INDEX.md'; return; }
        catch (err) { await navigate('/', false); return; }   // 既有根回落
      }
      // A1: 自派发——不能用 `await navigate(hash)`，navigate 自吞 fetch 错、成功/失败都返
      // undefined，bootstrap 收不到 404 信号。这里自己 try/catch 调 loadDir/loadDoc。
      try {
        if (initialDir.endsWith('/')) await loadDir(initialDir);
        else await loadDoc(initialDir);
        currentPath = initialDir;
        history.replaceState({ path: initialDir }, '', window.location.hash);  // A8/OV-2: Back 回深链
      } catch (err) {
        // F-D 防递归：清坏 hash（无 hashchange 监听，安全），MUST NOT 重调 bootstrap()
        history.replaceState({ path: '/' }, '', window.location.pathname);
        initialDir = '/';
        try { await loadDoc('/INDEX.md'); currentPath = '/INDEX.md'; }
        catch (e) { await navigate('/', false); }
        // A2/NEW-1: notice 在回落渲染**之后**、专用 DOM 节点、作 contentBody 的兄弟插入
        // （MUST NOT contentBody.innerHTML= —— 会被 loadDoc/loadDir 擦掉 → 提示静默蒸发）
        const notice = document.createElement('div');
        notice.className = 'deep-link-notice';
        notice.textContent = '深链未找到（可能已归档），已回首页。';
        content.insertBefore(notice, contentBody);
      }
    }

    bootstrap();
```

- [ ] **Step 3: Add notice CSS**

`sdflow-init/assets/workflow/tools/engine.css` 追加：

```css
.deep-link-notice {
  margin: 8px 0;
  padding: 8px 12px;
  border-left: 3px solid #d9a441;
  background: #fdf6e3;
  color: #6b5320;
  font-size: 0.9em;
}
```

- [ ] **Step 4: Redeploy to dev checkout (dev-checkout 纪律)**

Run: `bash setup.sh >/dev/null 2>&1 && echo "redeployed"`
Expected: `redeployed`——engine.js/engine.css 经 canonical 软链即时生效（改 assets 后须重跑才测得到）。

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh review-tool-followups:task5-engine-deeplink
```

---

### Task 6: 验证与收尾（tasks 3.x）

**Files:**
- 无源码改动（验证 + issues 回写）

- [ ] **Step 1: 四态手测（T45，engine.js 无 pytest 的替代网 · BR-9 硬约束）**

```bash
cd openspec && bash serve.sh start 8137 2>/dev/null; sleep 1
```
浏览器（或 curl 取首屏后人工核）逐一验：
1. `http://localhost:8137/review.html#/changes/review-tool-followups/` → 首屏直接 scoped 到该 change（非全树 INDEX）。
2. `http://localhost:8137/review.html#/specs/spec-workflow/spec.md` → 任意同源路径深链亦生效（宽目标）。
3. `http://localhost:8137/review.html#//evil.com/x` 与无 hash → 回落全树 INDEX，无越界 fetch。
4. `http://localhost:8137/review.html#/changes/does-not-exist/` → 回落 INDEX + 出现 `.deep-link-notice`「深链未找到」，不卡死、有🏠。
```bash
cd openspec && bash serve.sh stop 2>/dev/null
```
四态全过 → 记结果；任一不过 → 回 Task 5 修。

- [ ] **Step 2: 全量回归**

Run: `python3 -m pytest sdflow-init/tests/ -q`
Expected: 全绿零回归。

- [ ] **Step 3: issues 回写（收尾，实际由 sdflow-done 的 sweep 承担，此处占位提醒）**

T44/T45 → DONE 的回写、批次 `drop-per-dir-review-stub` 推进，交 `/sdflow-done` 的 issues sweep 子步统一处理（勿在此手改 INDEX）。

- [ ] **Step 4: Commit（若本任务有产物如手测记录）**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh review-tool-followups:task6-verify
```

---

## Self-Review

- **Spec coverage**：T44（retire CLI mode T1 / setup 接线 T3 / 原子写 T2 / 文档 T4 / 集成测试 T3）· T45（engine bootstrap T5，含 A1/A2/A3/A7/A8/F-D）· 验证（T6 四态 + 回归）。spec delta 的 6 个 Scenario：深链首屏(T5/T6①)、空-跨源回落(T5/T6③)、陈旧404回落显形(T5/T6④)、setup.sh 触发自愈(T3)、缺 python3 fail-safe(T3)、只清退役不推安装(现状 setup.sh 不装 ensure，天然满足——无代码任务，验收时 grep 确认 setup.sh 无 ff0 安装即可)。
- **Placeholder scan**：无 TBD；每步含实际代码/命令。
- **Type consistency**：`resolveInitialDir()`→`initialDir(let)`→`bootstrap()` 一致；`retire-hooks` mode 名在 argparse choices、main() 分支、setup.sh 调用、测试 argv 四处字面一致。
