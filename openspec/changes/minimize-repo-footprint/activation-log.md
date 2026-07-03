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

## Task10 激活验证

> 执行位置：本仓（开发 checkout）`/Users/cheneyzhao/Documents/04-sdflow-skills`。⚠ Step 2 起，`~/.claude/skills/*` 与 `~/.codex/skills/*` 软链临时从 Task1 建立的运行 checkout `~/.skills/sdflow-skills` 改指回本开发 checkout（知情临时指 dev，design.md §五许可）——**合并后须在 `~/.skills/sdflow-skills` 重跑 `bash setup.sh` 还原**，已写入 hand-off 供 opsx-done 收尾提醒。

### Step 1: 同步本仓 instance（5.6 执行）

命令：
```
python3 opsx-project-init/scripts/init.py update --dev --root .
diff -q openspec/workflow/workflow.md opsx-project-init/assets/workflow/workflow.md
```

原始输出：
```
✓ opsx-project-init update 完成 @ /Users/cheneyzhao/Documents/04-sdflow-skills

  - 铺 bundle：openspec/workflow/（--dev 整刷）（34 文件，覆盖）
  - 铺 review 根锚：openspec/review.html + openspec/serve.sh（2 文件，覆盖；tools/ 随 bundle 入 openspec/workflow/tools/）
  - hack 脚本：不再铺进仓（checkpoint 已全局化 → ~/.sdflow/hack/，由 setup.sh 安装）
  - 全局 hooks：
  · ff0-branch-guard.py：脚本已最新；已注册（全局）
  · change-review-stub.py：脚本已最新；已注册（全局）
  - ⚠ openspec/workflow/ 残留规则副本（workflow.md、spec-checklists、code-checklists）——遮蔽全局 bundle 且不再被 update 刷新：想跟全局最新 → 手动删净；想 pin 这一版 → 留着（显式逃生口）
  - ⚠ hack/checkpoint-commit.sh 为旧版仓内副本（checkpoint 已全局化 → ~/.sdflow/hack/）：本仓无规则副本 → 可删改用全局；若保留本地 workflow.md 副本（pin）且其仍引用仓内路径 → 勿删
  - config.yaml：update 不动 config.yaml（如模版有变，模型按需合并通用段/rules）
  - openspec/INDEX.md：更新托管区块
  - CLAUDE.md：更新托管区块
  - AGENTS.md：更新托管区块
```

`diff -q` 无任何输出（退出码 0）——instance 与 assets 权威源已一致，dogfood 悖论消除，符合 Expected。

注：update 输出中的两条 `⚠` 遮蔽/孤儿告警是 4.1/4.2 通用陈旧遮蔽检测的固定文案，对**本仓自身**（既是权威源又是消费仓的 dogfood 场景）属误报噪声——`git diff --stat` 证实 `workflow.md`/`config.template.yaml` 已被 `--dev` 整刷覆盖为最新内容，非"遮蔽不刷新"；`hack/checkpoint-commit.sh` 提示同理，本仓根 `hack/` 是 §六表中钉死的三副本之一（本仓 dogfood 实例），非孤儿。

变更文件（`git diff --stat`）：
```
 AGENTS.md                              |  8 ++++----
 CLAUDE.md                              |  8 ++++----
 openspec/INDEX.md                      |  2 ++
 openspec/review.html                   |  2 +-
 openspec/workflow/config.template.yaml |  5 +++--
 openspec/workflow/workflow.md          | 15 +++++++++------
 6 files changed, 23 insertions(+), 17 deletions(-)
```

### Step 2: 建全局家（知情临时指 dev）

命令：
```
bash setup.sh
ls -la ~/.sdflow/ ~/.sdflow/hack/
```

原始输出：
```
laodao-skills vunknown ready → /Users/cheneyzhao/.claude/skills /Users/cheneyzhao/.codex/skills

  installed (27):
    ✓ buglist-recorder @ /Users/cheneyzhao/.claude/skills
    ✓ embedded-test-sop @ /Users/cheneyzhao/.claude/skills
    ✓ impl-review @ /Users/cheneyzhao/.claude/skills
    ✓ issues-recorder @ /Users/cheneyzhao/.claude/skills
    ✓ openspec-upgrade @ /Users/cheneyzhao/.claude/skills
    ✓ opsx-done @ /Users/cheneyzhao/.claude/skills
    ✓ opsx-maintain @ /Users/cheneyzhao/.claude/skills
    ✓ opsx-project-init @ /Users/cheneyzhao/.claude/skills
    ✓ opsx-roadmap-planner @ /Users/cheneyzhao/.claude/skills
    ✓ sdflow-upgrade @ /Users/cheneyzhao/.claude/skills
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
    ✓ sdflow-upgrade @ /Users/cheneyzhao/.codex/skills
    ✓ spec-review @ /Users/cheneyzhao/.codex/skills
    ✓ todolist-recorder @ /Users/cheneyzhao/.codex/skills
    ✓ workflow @ /Users/cheneyzhao/.sdflow
    ✓ hack/checkpoint-commit.sh @ /Users/cheneyzhao/.sdflow
    ✓ hack/resolve-workflow.sh @ /Users/cheneyzhao/.sdflow

  mode: symlink (Unix)

/Users/cheneyzhao/.sdflow/:
total 0
drwxr-xr-x@  4 cheneyzhao  staff   128 Jul  3 15:44 .
drwxr-x---+ 66 cheneyzhao  staff  2112 Jul  3 15:44 ..
drwxr-xr-x@  4 cheneyzhao  staff   128 Jul  3 15:44 hack
lrwxr-xr-x@  1 cheneyzhao  staff    78 Jul  3 15:44 workflow -> /Users/cheneyzhao/Documents/04-sdflow-skills/opsx-project-init/assets/workflow

/Users/cheneyzhao/.sdflow/hack/:
total 16
drwxr-xr-x@ 4 cheneyzhao  staff   128 Jul  3 15:44 .
drwxr-xr-x@ 4 cheneyzhao  staff   128 Jul  3 15:44 ..
-rwxr-xr-x@ 1 cheneyzhao  staff  1871 Jul  3 15:44 checkpoint-commit.sh
-rwxr-xr-x@ 1 cheneyzhao  staff  2829 Jul  3 15:44 resolve-workflow.sh
```

均与 Expected 一致：`~/.sdflow/workflow` 软链指向本仓 `opsx-project-init/assets/workflow`；`hack/` 下两脚本 `-rwxr-xr-x` 可执行。

### Step 3: 真实调用验证（5.7 证据锚点）

命令（三场景一次 shell 内串联，保证 `$TMP` 跨命令有效）：
```
~/.sdflow/hack/resolve-workflow.sh --root . --explain

TMP=$(mktemp -d)
python3 opsx-project-init/scripts/init.py init --root "$TMP"
(cd "$TMP" && git init -q . && ~/.sdflow/hack/resolve-workflow.sh --explain)

find "$TMP/openspec/workflow" -name "*.md" -not -path "*/tools/*" | wc -l
find "$TMP/openspec/workflow" -maxdepth 2
rm -rf "$TMP"
```

原始输出：
```
=== Step 3a: local-pin ===
resolve-workflow: source=local-pin path=./openspec/workflow
./openspec/workflow
=== Step 3b: init temp consumer repo ===
TMP=/var/folders/xl/9k0bckk50kj4krpr8lx74mn00000gn/T/tmp.cE0d8XKMWe
✓ opsx-project-init init 完成 @ /var/folders/xl/9k0bckk50kj4krpr8lx74mn00000gn/T/tmp.cE0d8XKMWe

  - 建目录：openspec/changes/ openspec/specs/
  - 铺 bundle：openspec/workflow/（5 文件，写入）
  - 铺 review 根锚：openspec/review.html + openspec/serve.sh（2 文件，写入；tools/ 随 bundle 入 openspec/workflow/tools/）
  - hack 脚本：不再铺进仓（checkpoint 已全局化 → ~/.sdflow/hack/，由 setup.sh 安装）
  - 全局 hooks：
  · ff0-branch-guard.py：脚本已最新；已注册（全局）
  · change-review-stub.py：脚本已最新；已注册（全局）
  - config.yaml：已从 config.template.yaml 生成 config.yaml → 填写「本项目」context 段
  - openspec/INDEX.md：新建并写入
  - CLAUDE.md：新建并写入
  - AGENTS.md：新建并写入

下一步（模型/人工）：
  · 编辑 openspec/config.yaml 的「## 本项目」context 段，填本项目 tech stack/约定
  · 安装配套 skill：bash ~/.skills/sdflow-skills/setup.sh（/spec-review /impl-review /opsx-done）
=== Step 3b cont: git init + resolver (expect global-canonical) ===
resolve-workflow: source=global-canonical path=/Users/cheneyzhao/.sdflow/workflow
/Users/cheneyzhao/.sdflow/workflow
=== Step 3c: rule md file count (expect 0) ===
       0
=== Step 3c listing (evidence) ===
/var/folders/xl/9k0bckk50kj4krpr8lx74mn00000gn/T/tmp.cE0d8XKMWe/openspec/workflow
/var/folders/xl/9k0bckk50kj4krpr8lx74mn00000gn/T/tmp.cE0d8XKMWe/openspec/workflow/tools
/var/folders/xl/9k0bckk50kj4krpr8lx74mn00000gn/T/tmp.cE0d8XKMWe/openspec/workflow/tools/review-stub.html
/var/folders/xl/9k0bckk50kj4krpr8lx74mn00000gn/T/tmp.cE0d8XKMWe/openspec/workflow/tools/engine.css
/var/folders/xl/9k0bckk50kj4krpr8lx74mn00000gn/T/tmp.cE0d8XKMWe/openspec/workflow/tools/engine.js
/var/folders/xl/9k0bckk50kj4krpr8lx74mn00000gn/T/tmp.cE0d8XKMWe/openspec/workflow/tools/vendor
=== cleanup ===
done, TMP removed
```

三场景均与 Expected 一致：①本仓 `source=local-pin`；②临时消费仓 `git init` 后缺省 `--root` 生效，`source=global-canonical` 指向 `~/.sdflow/workflow`；③新 init 仓规则 `.md` 数 = 0（只落 `tools/` 4 个文件：`review-stub.html`/`engine.css`/`engine.js`/`vendor/`）。

### Step 4: Codex 侧实测（A1-P5）

命令：
```
codex exec 'bash ~/.sdflow/hack/resolve-workflow.sh --root . --explain' 2>&1 | tail -5
```

原始输出：
```
./openspec/workflow
resolve-workflow: source=local-pin path=./openspec/workflow
```

结论：当前项目使用本仓内 pin 的 `./openspec/workflow`，不是全局 `~/.sdflow/workflow`。
```

Codex CLI（`codex-cli 0.142.5`，`/opt/homebrew/bin/codex`）成功调用 `resolve-workflow.sh`，输出含 `source=local-pin`，与 Expected 一致——**A1-P5 沙盒拒绝假设未命中**，本机 Codex 沙盒放行了对开发 checkout（本仓）及 `$HOME/.sdflow` 的读取；未触发降级记录分支，故本任务未追加 todolist 条目。

## impl-review 第零步：经评审 skill 真实触发 resolver（tasks 5.7 半句证据，2026-07-03 16:0x）

```
$ [ -x ~/.sdflow/hack/resolve-workflow.sh ] && echo RESOLVER_EXECUTABLE=yes
RESOLVER_EXECUTABLE=yes
$ RULES_ROOT=$(~/.sdflow/hack/resolve-workflow.sh --root "$(git rev-parse --show-toplevel)" --explain)
exit_code=0
stdout: /Users/cheneyzhao/Documents/04-sdflow-skills/openspec/workflow
stderr: resolve-workflow: source=local-pin path=/Users/cheneyzhao/Documents/04-sdflow-skills/openspec/workflow
```

> 调用方 = /impl-review SKILL.md 第零步（更新后的读点协议），非直接 bash 取证——闭合 subagent-dev 终审 Important#1。
