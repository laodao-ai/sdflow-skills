# activation-log — 真实调用证据锚点

## Task1 运行 checkout 迁移

### Step 1: clone 新仓到运行位

命令：
```
git clone https://github.com/laodao-ai/sdflow-skills.git ~/.skills/sdflow-skills
```

原始输出：
```
Cloning into '/Users/cheneyzhao/.skills/sdflow-skills'...
```

验证（clone 后目录内容 + remote + log，确认非空且历史正确）：
```
$ ls -la ~/.skills/sdflow-skills
total 72
drwxr-xr-x@ 25 cheneyzhao  staff   800 Jul  3 14:55 .
drwxr-xr-x@ 12 cheneyzhao  staff   384 Jul  3 14:55 ..
drwxr-xr-x@  4 cheneyzhao  staff   128 Jul  3 14:55 .claude
drwxr-xr-x@  3 cheneyzhao  staff    96 Jul  3 14:55 .codex
drwxr-xr-x@ 12 cheneyzhao  staff   384 Jul  3 14:55 .git
-rw-r--r--@  1 cheneyzhao  staff   277 Jul  3 14:55 .gitattributes
-rw-r--r--@  1 cheneyzhao  staff   176 Jul  3 14:55 .gitignore
-rw-r--r--@  1 cheneyzhao  staff  2060 Jul  3 14:55 AGENTS.md
drwxr-xr-x@  5 cheneyzhao  staff   160 Jul  3 14:55 buglist-recorder
-rw-r--r--@  1 cheneyzhao  staff  7185 Jul  3 14:55 CLAUDE.md
drwxr-xr-x@  4 cheneyzhao  staff   128 Jul  3 14:55 docs
drwxr-xr-x@  3 cheneyzhao  staff    96 Jul  3 14:55 embedded-test-sop
drwxr-xr-x@  3 cheneyzhao  staff    96 Jul  3 14:55 hack
drwxr-xr-x@  3 cheneyzhao  staff    96 Jul  3 14:55 impl-review
drwxr-xr-x@  5 cheneyzhao  staff   160 Jul  3 14:55 issues-recorder
drwxr-xr-x@ 13 cheneyzhao  staff   416 Jul  3 14:55 openspec
drwxr-xr-x@  3 cheneyzhao  staff    96 Jul  3 14:55 openspec-upgrade
drwxr-xr-x@  3 cheneyzhao  staff    96 Jul  3 14:55 opsx-done
drwxr-xr-x@  4 cheneyzhao  staff   128 Jul  3 14:55 opsx-maintain

$ git -C ~/.skills/sdflow-skills remote get-url origin
https://github.com/laodao-ai/sdflow-skills.git

$ git -C ~/.skills/sdflow-skills log --oneline -5
fcbe3a3 docs: 补写 README、完善 CLAUDE.md，刷新 issues INDEX
db3c824 chore: 初始化 sdflow-skills（OpenSpec 工作流 + 配套 skills）
```

### Step 2: 在新运行 checkout 跑 setup

命令：
```
cd ~/.skills/sdflow-skills && bash setup.sh
```

原始输出：
```
laodao-skills vunknown ready → /Users/cheneyzhao/.claude/skills /Users/cheneyzhao/.codex/skills

  installed (22):
    ✓ buglist-recorder @ /Users/cheneyzhao/.claude/skills
    ✓ embedded-test-sop @ /Users/cheneyzhao/.claude/skills
    ✓ impl-review @ /Users/cheneyzhao/.claude/skills
    ✓ issues-recorder @ /Users/cheneyzhao/.claude/skills
    ✓ openspec-upgrade @ /Users/cheneyzhao/.claude/skills
    ✓ opsx-done @ /Users/cheneyzhao/.claude/skills
    ✓ opsx-maintain @ /Users/cheneyzhao/.claude/skills
    ✓ opsx-project-init @ /Users/cheneyzhao/.claude/skills
    ✓ opsx-roadmap-planner @ /Users/cheneyzhao/.claude/skills
    ✓ spec-review @ /Users/cheneyzhao/.claude/skills
    ✓ todolist-recorder @ /Users/cheneyzhao/.claude/skills
    ✓ buglist-recorder @ /Users/cheneyzhao/.codex/skills
    ✓ embedded-test-sop @ /Users/cheneyzhao/.codex/skills
    ✓ impl-review @ /Users/cheneyzhao/.codex/skills
    ✓ issues-recorder @ /Users/cheneyzhao/.codex/skills
    ✓ openspec-upgrade @ /Users/cheneyzhao/.codex/skills
    ✓ opsx-done @ /Users/cheneyzhao/.codex/skills
    ✓ opsx-maintain @ /Users/cheneyzhao/.codex/skills
    ✓ opsx-project-init @ /Users/cheneyzhao/.codex/skills
    ✓ opsx-roadmap-planner @ /Users/cheneyzhao/.codex/skills
    ✓ spec-review @ /Users/cheneyzhao/.codex/skills
    ✓ todolist-recorder @ /Users/cheneyzhao/.codex/skills

  mode: symlink (Unix)
```

注：输出首行 `laodao-skills vunknown ready` 是 setup.sh 内固定文案（未参数化仓库名），`vunknown` 因本仓库未包含 `VERSION` 文件（CLAUDE.md 已注明此为已知现象）。软链数量为 22（11 个 skill × 2 个运行时），与本仓库 skill 目录数一致。

### Step 3: 验证软链已切换

命令：
```
readlink ~/.claude/skills/spec-review; readlink ~/.codex/skills/spec-review
```

原始输出：
```
/Users/cheneyzhao/.skills/sdflow-skills/spec-review
/Users/cheneyzhao/.skills/sdflow-skills/spec-review
```

均与 Expected 一致：`/Users/cheneyzhao/.skills/sdflow-skills/spec-review`。

### 附加验证：旧运行 checkout 原封未动

命令：
```
ls -la ~/.skills/laodao-skills | head -5
git -C ~/.skills/laodao-skills remote get-url origin
git -C ~/.skills/laodao-skills status --short
```

原始输出：
```
total 96
drwx------@ 48 cheneyzhao  staff  1536 Jul  2 22:26 .
drwxr-xr-x@ 12 cheneyzhao  staff   384 Jul  3 14:55 ..
drwxr-xr-x@  5 cheneyzhao  staff   160 Jul  2 17:40 .claude
drwxr-xr-x@  3 cheneyzhao  staff    96 Jul  2 17:40 .codex
---
https://github.com/laodao-ai/laodao-skills.git
---
(空，无未提交变更)
```

`~/.skills/laodao-skills` 的 mtime（Jul 2 22:26）早于本次操作时间（Jul 3 14:55），remote 仍指向旧仓 `laodao-ai/laodao-skills.git`，工作区无脏变更——确认本任务未触碰该目录，符合"旧 checkout 绝不删除"的约束。
