#!/usr/bin/env python3
"""init.py — 把 openspec/workflow/ bundle 铺进一个项目（或更新已铺过的项目）。

skill `sdflow-init` 的执行核心。权威源 = 本 skill 的 assets/workflow/（单一源）。
两种模式：
  init   —— 空项目首次铺设：建目录骨架、拷 bundle、从模版生成 config.yaml、注入
           INDEX.md / CLAUDE.md / AGENTS.md 的托管区块。
  update —— 已铺过的项目重拉最新 bundle：覆盖 workflow/ 托管文件、重注入托管区块；
           **不动 config.yaml 的本项目段、不覆盖用户内容**。

确定性操作交脚本（拷贝、建目录、标记区块幂等注入）；需判断的（填 config 的「本项目」段、
合并已存在的 config.yaml）留给模型，见 SKILL.md。

标记区块（HTML 注释包裹，幂等替换；用户勿手改区块内）：
  CLAUDE.md / AGENTS.md : <!-- opsx-init:start --> ... <!-- opsx-init:end -->
  INDEX.md             : <!-- opsx-init:rules:start --> ... <!-- opsx-init:rules:end -->

用法见 `python init.py --help`。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import re

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
import tempfile

# [T48] 本模块用 f-string，需 Python 3.6+。**版本把关在调用侧**（setup.sh 的 `$_py` 探测
# 实际按 3.7+ 卡——那个解释器还要跑 outside-voice-job.py，闸门取两个消费者的上确界）：
# 整模块编译先于任何语句执行，f-string 在 py<3.6 上是解析期 SyntaxError——模块内加
# `sys.version_info` 守卫无从拦截自身 parse，故这里只声明契约、不放无功能的假守卫。

try:
    import fcntl  # POSIX 独有；Windows 无 → T49 锁降级为 best-effort 无锁
except ImportError:  # pragma: no cover （沙箱恒 POSIX，Windows 分支无法在此覆盖）
    fcntl = None

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SKILL_DIR, "assets")
BUNDLE_SRC = os.path.join(ASSETS, "workflow")
SCHEMAS_SRC = os.path.join(ASSETS, "schemas")
SNIPPETS = os.path.join(ASSETS, "snippets")
PROJECT_SCHEMA = "sdflow-spec-driven"
BUILTIN_SCHEMA = "spec-driven"
VALID_CHANGE_MARKER_SCHEMAS = {BUILTIN_SCHEMA, PROJECT_SCHEMA}
MIN_SCHEMA_CLI = (1, 7, 0)

MARK_DOC = ("<!-- opsx-init:start —— 由 sdflow-init 维护，勿手改本区块 -->",
            "<!-- opsx-init:end -->")
MARK_IDX = ("<!-- opsx-init:rules:start —— 由 sdflow-init 维护，勿手改本区块 -->",
            "<!-- opsx-init:rules:end -->")

def _find_all_marker_lines(text, token):
    """[T21] 逐行累加 offset，产出 text 中**所有** marker 行的 (start, end) offset。
    「marker 行」= 含 token ∧ lstrip 后以 "<!--" 起。`_find_marker_line` 取其首个作安全
    offset 定位。注：判据尚非 fence-aware（会命中 ``` 代码块内演示的 marker）——多块收敛的
    fence-aware + 配对校验版本已 defer todolist（本仓满是 marker 示例，naive 收敛会劫持注入）。"""
    off = 0
    for line in text.splitlines(keepends=True):
        if token in line and line.lstrip().startswith("<!--"):
            yield off, off + len(line)
        off += len(line)


def _find_marker_line(text, token):
    """按 token 定位**第一个** marker 整行（返回该行起止 offset），找不到返回 None。
    [T21] 逐行累加 offset 定位（经 _find_all_marker_lines），**非** `text.index(line)`
    子串查找——marker 串若在真 marker 行之前以行内嵌入（非行首）出现，text.index 会锚到
    那个 inline 子串位置（错位、破坏区块替换）。"""
    for start, end in _find_all_marker_lines(text, token):
        return start, end
    return None

CORE_DIRS = ["changes", "specs"]  # openspec 核心；buglists/todolists 由各自 recorder skill 首用时建

# 全局 hooks：通用功能，全局安装一次（~/.claude/），跨所有项目生效，不随 per-project bundle 铺设。
HOOKS = [
    {
        "name": "ff0-branch-guard.py",
        "src": os.path.join(ASSETS, "hooks", "ff0-branch-guard.py"),
        "event": "PreToolUse",
        "matcher": "Bash",
        "cmd": 'python3 "$HOME/.claude/hooks/ff0-branch-guard.py"',
    },
]

# 退役 hook 名单（ADR-1）：hook 安装本是「只增不减」，退役一个 hook 时存量安装的
# ~/.claude/settings.json 会留孤儿注册 + ~/.claude/hooks/ 残留脚本 → 之后每次 Bash 触发失败
# hook。retire_hooks() 在 init/update 每次跑时自愈：外科式摘 settings 注册 + 删脚本；
# fresh 安装无残留则全 no-op。后续任何 hook 退役都往这里加名即可。
RETIRED_HOOKS = ["change-review-stub.py"]

# 退役部署文件名单（drop-review-html-viewer）：曾由 sdflow-init 铺进消费仓 openspec/ 根、现已
# 废弃的文件。停止铺设后它们会变孤儿（不在 tools/ 整删重拷范围内），须显式清理。**签名门控删除**：
# 仅当目标文件内容含该文件的 bundle 部署签名时才删——防误删用户自建同名文件（承 adr/0022：只删
# 自己确知铺设过的、不猜用户文件内容）。tools/ 下的查看器资产（engine.js/css、vendor/、
# review-stub.html）**不入此名单**——它们随 copy_bundle 对 tools/ 的「整删重拷」自动清除。
# 每项 = (相对 openspec/ 的路径, bundle 部署签名子串)。后续任何根锚部署文件退役都往这里加。
RETIRED_DEPLOY_FILES = [
    ("review.html", "__OPENSPEC_PROJECT_NAME__"),   # 查看器模板渲染 token 的宿主变量名，查看器独有
    ("serve.sh", "openspec-review-serve-"),          # 查看器 serve.sh 的 PIDFILE key 前缀，查看器独有
]


def merge_runtime_gitignore(root, snippet):
    """Merge runtime-only ignore entries without rewriting user bytes."""
    if isinstance(snippet, str):
        snippet = snippet.encode("utf-8")
    entries = [line for line in snippet.splitlines() if line]
    if not entries or any(b"\r" in line or b"\n" in line for line in entries):
        raise ValueError("runtime gitignore snippet 非法")
    path = os.path.join(root, ".gitignore")
    try:
        with open(path, "rb") as handle:
            original = handle.read()
    except FileNotFoundError:
        original = b""
    lines = original.splitlines()
    missing = []
    for entry in entries:
        count = sum(line == entry for line in lines)
        if count > 1:
            raise ValueError(f"runtime gitignore 条目重复，拒绝擅删用户内容：{entry.decode('utf-8')}")
        if count == 0:
            missing.append(entry)
    if not missing:
        return "已有（byte-noop）"
    merged = original
    if merged and not merged.endswith((b"\n", b"\r")):
        merged += b"\n"
    merged += b"".join(entry + b"\n" for entry in missing)
    os.makedirs(root, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=root, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            written = handle.write(merged)
            if written != len(merged):
                raise OSError("runtime gitignore write was incomplete")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            mode = os.stat(path).st_mode & 0o777
        except FileNotFoundError:
            mode = 0o644
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return "追加 " + " ".join(entry.decode("utf-8") for entry in missing)


# ── 标记区块幂等注入 ─────────────────────────────────────────

def inject(path, start, end, content, header=""):
    """有标记则按 token 定位既有区块（含历史 marker 文案，如旧 skill 名）并原位替换为新
    marker + 新内容；无标记则追加；文件不存在则以 header 起头新建。返回动作描述。

    定位用 token（如 "opsx-init:start"）而非全串精确匹配——marker 文案随 skill 改名演化时
    （如 opsx-project-init → sdflow-init），旧区块仍需被命中替换，而不是被判定"未找到"而追加
    出重复区块。token 从 start/end 的 marker 文案中提取：格式固定为
    "<!-- <token> —— ... -->"（start）/ "<!-- <token> -->"（end），token 即第二个空白分隔词。
    """
    start_token = start.split()[1]
    end_token = end.split()[1]
    # 只有嵌套的 principles 托管块要求外层 marker 后的分隔空行，才能与
    # sync_principles.py 的 canonical render 保持字节一致。普通 MARK_IDX 等布局
    # 保持原有的紧邻格式，避免每次 update 都改写所有消费仓的无关空行。
    separator = "\n" if content.startswith("<!-- sdflow:principles:start") else ""
    block = f"{start}\n{separator}{content.rstrip()}\n{end}\n"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        s_loc = _find_marker_line(text, start_token)
        e_loc = _find_marker_line(text, end_token)
        if s_loc and e_loc and s_loc[0] <= e_loc[0]:
            # [T21] 仅替换**第一对** start..end（经安全的逐行 offset 定位，见 _find_marker_line）。
            # 注：多重复托管块只收敛首块（次块残留），是**已知残差**——正确的多块收敛须
            # fence-aware（不误命中 ``` 代码块内演示的 marker）+ start/end 配对校验（不跨孤儿
            # marker 吞用户内容），否则在本仓这类满是 marker 示例的 workflow-doc 仓会劫持注入/
            # 静默丢内容（code-review adv 镜实证 F1/F2）。已 defer todolist，非本轻量批 scope。
            pre = text[:s_loc[0]]
            post = text[e_loc[1]:]
            new = pre + block.rstrip("\n") + "\n" + post.lstrip("\n")
            if not new.endswith("\n"):
                new += "\n"
            action = "更新托管区块"
        else:
            new = text.rstrip("\n") + "\n\n" + block
            action = "追加托管区块"
    else:
        new = (header.rstrip("\n") + "\n\n" if header else "") + block
        action = "新建并写入"
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return action


def read_snippet(name):
    with open(os.path.join(SNIPPETS, name), encoding="utf-8") as f:
        return f.read()


# ── bundle 铺设 ──────────────────────────────────────────────

# 本机跑工具留下的残渣，MUST NOT 当 bundle 资产铺进项目仓。
#
# 成因（不是"跨机器污染"——.pyc/.pytest_cache 都不入库，git pull 拉不到）：canonical
# `~/.sdflow/workflow` 指向运行 checkout 的 `assets/workflow`，那里的 `tools/*.py` 一被执行/
# 被 pytest 收集，就在**资产侧**堆出这些目录；copytree 再把它们搬进项目仓 `openspec/workflow/`。
#
# 危害很小（都被 .gitignore 挡在库外，.pyc 还带解释器版本 tag、不匹配不会被误用），但有一个
# **可观测症状**：`update` 报告的"铺 bundle N 文件"随「从哪个 checkout 跑」漂移
# （实测 30 vs 19 → 修 __pycache__ 后仍 18 vs 13 ← 剩的正是 .pytest_cache）。
#
# 🔴 这是**拒绝清单**，不是穷举证明：新工具随时会发明新的缓存目录名，漏一个不会 fail-closed，
# 只会让上面那个计数重新开始漂。**发现计数又不稳，先来这里加名字，别再去逐个现场补。**
LOCAL_TOOL_CACHES = frozenset({
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".DS_Store",
})


def copy_bundle(root, full=False, include_schema=True):
    """R-MRF-1 分层部署：默认只铺 tools/ 子树（规则经全局 canonical 解析，不复制进消费仓）。
    full=True 整 bundle 铺设——仅供 toolkit 源仓 `update --dev` dogfood 刷新 instance 用；同样
    不部署 `tools/tests/`，因为它们是 toolkit 自测而非运行时 bundle。

    非 full 模式收敛性：拷贝前若 dst/tools 已存在则先 rmtree 再 copytree——tools/ 是随
    workflow bundle 托管的子树（update 覆盖刷新语义），不落入"绝不自动删消费仓文件"红线；
    清后拷保收敛，上游删文件不再残留（B2-F4）。full 模式维持 dirs_exist_ok 现状不变。

    `tools/tests/` 是 tools 脚本（如 trivial_shape.py）的内部 pytest，只服务 toolkit 源仓
    自身开发；任何派生到 `openspec/workflow/` 的副本都不应含它。否则 `update --dev` 会把同名
    测试模块复制到本仓 dogfood instance，仓根 pytest 会收集两份并报 import file mismatch。
    脚本本体仍随 tools/ 正常部署。full 模式也要清除既有遗留副本，保证重复执行收敛。"""
    def ignore_tools_tests(source, _names):
        """仅忽略 bundle tools/ 直属 tests；其他运行时 tests 必须随完整 bundle 铺设。
        另忽略 LOCAL_TOOL_CACHES（本机跑工具的残渣，不是 bundle 资产）——见其定义处。"""
        if os.path.normpath(source) == os.path.normpath(os.path.join(BUNDLE_SRC, "tools")):
            return {"tests"} | LOCAL_TOOL_CACHES
        return set(LOCAL_TOOL_CACHES)

    schema_src = os.path.join(SCHEMAS_SRC, PROJECT_SCHEMA)
    if include_schema:
        _validate_schema_authority(schema_src)

    dst = os.path.join(root, "openspec", "workflow")
    if full:
        shutil.copytree(BUNDLE_SRC, dst, dirs_exist_ok=True,
                        ignore=ignore_tools_tests)
        tests_dst = os.path.join(dst, "tools", "tests")
        if os.path.isdir(tests_dst):
            shutil.rmtree(tests_dst)
    else:
        tools_dst = os.path.join(dst, "tools")
        if os.path.isdir(tools_dst):
            shutil.rmtree(tools_dst)
        shutil.copytree(os.path.join(BUNDLE_SRC, "tools"), tools_dst,
                         ignore=ignore_tools_tests)
        # [mlh-p2-anchor-lint] 契约是 tools/anchor_lint.py 的运行时机读依赖（读 lens-metric-enums 块），
        # 须与 tools/ 同批刷新，否则本地 pin 消费仓 update 后「新脚本+旧契约无块」永久 fail-closed。
        contract_src = os.path.join(BUNDLE_SRC, "lens-metric-contract.md")
        if os.path.isfile(contract_src):
            shutil.copy2(contract_src, os.path.join(dst, "lens-metric-contract.md"))

        # WORKFLOW-GUIDE.md —— 【给人看的】完整手册（每步 prompt 全文内联）。
        # 规则本身不铺进消费仓（走全局 canonical），但【人】需要一份不用跳文件的完整参考，
        # 且它得在自己的仓里、随仓走。它是 hack/gen_workflow_guide.py 的生成物（DO NOT EDIT），
        # 单一源仍是 prompts/ + workflow.md —— 拷过来的是产物，不是新的真相源。
        guide_src = os.path.join(BUNDLE_SRC, "WORKFLOW-GUIDE.md")
        if os.path.isfile(guide_src):
            shutil.copy2(guide_src, os.path.join(dst, "WORKFLOW-GUIDE.md"))
    if include_schema:
        schemas_dst = os.path.join(root, "openspec", "schemas")
        schema_dst = os.path.join(schemas_dst, PROJECT_SCHEMA)
        # 只托管本工具的 fork。消费仓可在 schemas/ 下维护其它 project-local schema，
        # update 不得删除它们。
        if os.path.isdir(schema_dst):
            shutil.rmtree(schema_dst)
        shutil.copytree(schema_src, schema_dst)
        if not os.path.isfile(os.path.join(schema_dst, "schema.yaml")):
            raise RuntimeError("project-local schema 复制后缺少 schema.yaml")
    n = sum(len(fs) for _, _, fs in os.walk(dst))
    schemas_dst = os.path.join(root, "openspec", "schemas")
    if include_schema and os.path.isdir(schemas_dst):
        n += sum(len(fs) for _, _, fs in os.walk(schemas_dst))
    return dst, n


def _validate_schema_authority(schema_src):
    """Fail before replacing the managed fork when its source is incomplete.

    `template:` 键嵌套在 `artifacts[].template`（非顶层）——`[.artifacts[].template]`
    包一层数组是刻意的：不包裹时 yq 对多个匹配值逐个吐独立 JSON 标量（换行拼接），会被
    `_yq()` 的 F3 多文档防御误判成「多文档 YAML」而 raise；包成单一 JSON 数组回避这个假阳，
    一次调用取回全部 template 引用。"""
    schema_asset = os.path.join(schema_src, "schema.yaml")
    if not os.path.isfile(schema_asset):
        raise RuntimeError(
            "project-local schema 权威资产缺失："
            f"{schema_asset}"
        )

    try:
        templates = _yq("[.artifacts[].template]", schema_asset, default=[])
    except RuntimeError as exc:
        raise RuntimeError(
            "project-local schema 权威资产不可读取："
            f"{schema_asset}"
        ) from exc
    if not isinstance(templates, list):
        templates = []

    missing = []
    template_root = os.path.normpath(os.path.join(schema_src, "templates"))
    for template in templates:
        if not isinstance(template, str) or not template.strip():
            missing.append(template if isinstance(template, str) and template else "<empty template reference>")
            continue
        template = template.strip()
        template_path = os.path.normpath(os.path.join(template_root, template))
        try:
            inside_templates = os.path.commonpath([template_root, template_path]) == template_root
        except ValueError:
            inside_templates = False
        if not inside_templates or not os.path.isfile(template_path):
            missing.append(template)

    if missing:
        rendered = ", ".join(f"templates/{template}" for template in missing)
        raise RuntimeError(
            "project-local schema 权威资产缺失模板："
            f"{rendered}"
        )


RULE_MARKERS = ("workflow.md", "spec-checklists", "code-checklists")


def stale_shadow_warnings(root):
    """反静默守卫·陈旧遮蔽（R-MRF-3）：update 内联为主 + sdflow-maintain 兜底（同款判据）。只告警，绝不删。"""
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


def retire_deploy_files(root):
    """清理退役的部署文件（drop-review-html-viewer，与 retire_hooks 同构、fail-safe）：
    对 RETIRED_DEPLOY_FILES 每项，仅当 openspec/<path> 存在且内容含其 bundle 部署签名时删除；
    签名不匹配（用户自建同名文件）或读不了（权限/二进制）→ 保守跳过、原样保留（承 adr/0022：
    只删自己确知铺设过的、不猜用户文件内容）。幂等、存量安装自愈、fresh 安装 no-op。返回动作汇总。"""
    osroot = os.path.join(root, "openspec")
    acts = []
    for rel, signature in RETIRED_DEPLOY_FILES:
        path = os.path.join(osroot, rel)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            continue   # 读不了 → 保守跳过，不猜、不删
        if signature not in content:
            continue   # 无 bundle 签名 = 用户自建同名文件，MUST NOT 删
        try:
            os.remove(path)
            acts.append(f"删退役查看器根锚 openspec/{rel}")
        except OSError:
            pass   # fail-safe：删不掉不中止（fail-safe 与 retire_hooks 一致）
    return "\n".join(f"  · {a}" for a in acts) if acts else "  · 无退役部署文件残留"


def ensure_dirs(root):
    made = []
    for d in CORE_DIRS:
        p = os.path.join(root, "openspec", d)
        if not os.path.isdir(p):
            os.makedirs(p, exist_ok=True)
            open(os.path.join(p, ".gitkeep"), "a").close()
            made.append(f"openspec/{d}/")
    return made


# ── yq(mikefarah) subprocess 薄封装（shared-yaml-subset-parser）─────────────────
#
# 本文件此前手搓 ~175 行 YAML 解析（_strip_inline_comment / _find_top_level_block /
# _second_level_keys / _parse_model_tiers_block 等）。语法层（缩进/冒号/引号/注释剥离/
# 多文档判定）全部委托外部 yq 二进制（mikefarah/yq，同 git 的外部二进制先例）；Python 侧
# 只做业务判断（fleet/tier 键集校验、越域键检测、畸形头检测）。零依赖不变量（MUST NOT
# `import yaml`/PyYAML——本脚本被 symlink 进消费仓，消费仓多数无 PyYAML，import 会
# ImportError 崩溃，与 fail-closed 相悖）因此收窄为「不 import 解析库」而非「不依赖外部
# YAML 工具」，代价见 openspec/adr/0036。

_YQ_INSTALL_HINT = (
    "安装方式：\n"
    "  macOS:   brew install yq\n"
    "  Windows: winget install --id MikeFarah.yq\n"
    "  Linux:   snap install yq"
)

_yq_bin = None  # 进程内缓存


def _check_yq():
    """轻量探测 yq 可用性 + 身份（不触碰 `_yq()` 的进程内缓存 `_yq_bin`——两者是独立探测
    路径），专供 `lint_config` 入口前调用（design.md §3）：`lint_config` 的公开契约是「返回
    reason 字符串列表」而非崩溃/退出，yq 缺失时需要一条能塞进 reasons 列表的人读提示，而不是
    任由 `_yq()` 首次调用时的 RuntimeError 未被捕获地穿透（`cmd_config_lint`/`main()` 均不
    catch 异常）。`run()`（init/update）路径不需要这道门——那条路径下 `_yq()` 失败自然被既有
    的 `except (..., RuntimeError): _die(...)` 统一兜底，与其它文件系统错误同一套处理。
    返回 (ok, reason)：ok=True 时 reason=None。"""
    yq = shutil.which("yq")
    if not yq:
        return False, f"yq 未安装。{_YQ_INSTALL_HINT}"
    vr = subprocess.run([yq, "--version"], capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    if "mikefarah" not in vr.stdout:
        return False, (
            "检测到的 yq 不是 mikefarah/yq（可能是 kislyuk/yq），请卸载后安装正确版本。"
            f"{_YQ_INSTALL_HINT}")
    return True, None


def _yq(expression, file, *, front_matter=False, in_place=False, default=None):
    """yq(mikefarah) subprocess 薄封装（design.md §1 参考实现 + spec-review F3 多文档防御——
    对齐 ship_gate.py/impl_route.py 的加固版，而非 anchor_lint.py 的早期版：config.yaml 的
    `context:` 块字面量段若贴入时丢缩进可意外产生多文档，是本文件的直接风险场景 [F3/D2 HIGH]）。

    本文件目前只读、且只用于「工具自己控制形状」的 YAML（marker 文件 / schema.yaml 资产 /
    `lint_config` 的结构校验）——`_schema_from_config`/`_set_schema_key` 这对 schema 字段
    读写搭档刻意保留既有字节级正则实现、未接入这里（见二者各自 docstring 的实测证据：yq
    在「文档起始 `--- # 注释`」这类用户可能手写的 config.yaml 形状上，读写两侧都有尚未找到
    统一规避手段的缺陷，超出 spec-review F14 已接受的「CRLF→LF 一次性 diff 噪音」范围）。
    `front_matter`/`in_place` 参数因此保留但未被本文件任何调用点以 True 传入——保留是为了
    与其余脚本的 `_yq()` 参考签名一致（Task 5 golden test 的比对面），非死码堆料。

    [R7] exit≠0 恒 raise RuntimeError（不吞、不因 default 静默）——「键不存在」（exit 0 +
    stdout=null，走 default）与「解析失败」（exit≠0，含 yq 未安装/身份不对/文件不可读/语法
    错误）是两条不同分支。
    [F3] 多文档防御：stdout 含一个以上 JSON 值（疑似多文档 YAML）→ raise，不静默只取第一个。

    `--header-preprocess=false`〔实测证据，见 impl-report〕：mikefarah/yq 默认
    `--header-preprocess=true` 在「文档起始 `--- # 注释`」后紧跟内容行的场景下有静默吞行 bug
    ——`--- # local config\nschema: x\ncontext: keep\n` 用默认设置查 `.schema` 得到 `null`
    （`schema` 键被吞掉，`context` 幸存），本仓真实存在这种「模版首行是带注释的 `---`」
    config.yaml 写法（见 `config.template.yaml`/相关测试）。禁用该预处理后两个键都能正确读到，
    代价仅是不再特殊处理文档头部注释与 `---` 分隔符的位置关系——本文件不消费那类位置信息。
    """
    global _yq_bin
    if _yq_bin is None:
        yq = shutil.which("yq")
        if not yq:
            raise RuntimeError(f"yq 未安装。{_YQ_INSTALL_HINT}")
        vr = subprocess.run([yq, "--version"], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
        if "mikefarah" not in vr.stdout:
            raise RuntimeError(
                "检测到的 yq 不是 mikefarah/yq（可能是 kislyuk/yq），请卸载后安装正确版本。"
                f"{_YQ_INSTALL_HINT}")
        _yq_bin = yq
    cmd = [_yq_bin, "--header-preprocess=false"]
    if front_matter:
        cmd += [f"--front-matter={'process' if in_place else 'extract'}"]
    if in_place:
        cmd.append("-i")
    else:
        cmd += ["-o", "json"]
    cmd += [expression, str(file)]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"yq failed on {file}: {r.stderr.strip()}")
    if in_place:
        return None
    raw = r.stdout.strip()
    if not raw or raw == "null":
        return default
    decoder = json.JSONDecoder()
    parsed, idx = decoder.raw_decode(raw)
    if raw[idx:].strip():
        raise RuntimeError(f"yq 输出多个 JSON 值（疑似多文档 YAML，不支持）: {raw[:200]!r}")
    if front_matter and not in_place and default is not None:
        if not isinstance(parsed, dict):
            return default
    return parsed


def _schema_from_config(root):
    """〔实测证据，见 impl-report——本函数刻意未迁 yq〕`config.yaml` 是用户可自由编辑的任意
    YAML（区别于本文件其余 yq 消费点：marker 文件/schema.yaml 都是工具自己写的简单单层
    YAML），已知会出现文档起始 `--- # 注释` 这类写法（`_set_schema_key` 下方就有专门维护
    该写法的字节级测试）。mikefarah/yq v4.53.3 的 `--header-preprocess` 在这类输入上有一类
    尚未找到统一规避手段的缺陷：默认 `true` 时会把 `--- # 注释` 之后的第一行内容**吞并进
    注释**（该行在解析结果里彻底消失，不只是格式差异）；显式 `false` 又会让含 `%YAML`/`%TAG`
    文档指令的文件直接解析失败（`found incompatible YAML document`）——两个设置各打破一类
    本文件已有测试锁定的真实场景，没有能同时满足两者的单一 flag。`_schema_from_config` 与
    `_set_schema_key` 是一对读写搭档（update 决定「要不要写」的比较基准），保持两者同为既有
    的字节级正则实现（对「schema:」这一个已知字面前缀做定位，非通用 YAML 解析，基准5警戒的
    是无界语法面手搓，这里的语法面是「一个固定字面量键」，有界）。"""
    cfg = os.path.join(root, "openspec", "config.yaml")
    try:
        # Treat a UTF-8 BOM as an encoding prefix, not as part of the first YAML key.
        with open(cfg, encoding="utf-8-sig") as f:
            for line in f:
                match = re.match(r"^schema\s*:\s*([^#\s]+)", line)
                if match:
                    return match.group(1)
    except (OSError, UnicodeDecodeError):
        pass
    return BUILTIN_SCHEMA


def _set_schema_key(root, schema):
    """Patch only the first top-level schema key, preserving every other byte."""
    cfg = os.path.join(root, "openspec", "config.yaml")
    with open(cfg, "rb") as f:
        raw = f.read()
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    body = raw[len(bom):]
    lines = body.splitlines(keepends=True)
    for i, line in enumerate(lines):
        # 仅替换 value；冒号后的空白、inline comment、行尾及其它字节原样保留。
        match = re.match(rb"^(schema[ \t]*:)([ \t]*)(.*?)(\r?\n)?$", line)
        if match:
            prefix, spacing, content, newline = match.groups()
            if content.startswith(b"#"):
                # YAML 注释前须有空白；保留冒号后的原缩进，再在目标值与注释之间补一格。
                suffix = b" " + content
            else:
                value_match = re.match(rb"([^ \t#\r\n]+)(.*)$", content)
                suffix = value_match.group(2) if value_match else b""
            lines[i] = prefix + spacing + schema.encode("utf-8") + suffix + (newline or b"")
            new = bom + b"".join(lines)
            if new != raw:
                _atomic_write(cfg, new, ".config.")
            return True

    newline = b"\r\n" if b"\r\n" in raw else b"\n"
    insert_at = 0
    offset = 0
    for candidate in lines:
        stripped = candidate.strip()
        if not stripped or stripped.startswith(b"#") or stripped.startswith(b"%"):
            offset += len(candidate)
            continue
        if re.match(rb"^---(?:[ \t]*(?:#.*)?)?(?:\r?\n)?$", candidate):
            insert_at = offset + len(candidate)
        break
    new = bom + body[:insert_at] + b"schema: " + schema.encode("utf-8") + newline + body[insert_at:]
    _atomic_write(cfg, new, ".config.")
    return True


def _atomic_write(path, content, prefix):
    """Publish complete bytes atomically from a temporary file in the target directory."""
    fd, tmp = tempfile.mkstemp(prefix=prefix, dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def handle_config(root, mode, schema=None):
    """init: 缺则从模版生成；update 只窄改 schema 单键。返回 (状态, 提示)。"""
    cfg = os.path.join(root, "openspec", "config.yaml")
    tmpl = os.path.join(BUNDLE_SRC, "config.template.yaml")
    if mode == "update":
        if schema and os.path.exists(cfg) and _schema_from_config(root) != schema:
            if not _set_schema_key(root, schema):
                raise RuntimeError("无法更新 config.yaml 的顶层 schema 键")
            return ("updated", f"update 仅改写 config.yaml 的 schema: → {schema}")
        return ("skip", "update 保持 config.yaml（schema 已是目标值）")
    if os.path.exists(cfg):
        if schema and _schema_from_config(root) != schema:
            _set_schema_key(root, schema)
        return ("exists", "config.yaml 已存在 → 保留用户内容，仅确保 schema 单键符合版本门")
    shutil.copyfile(tmpl, cfg)
    if schema and schema != PROJECT_SCHEMA:
        _set_schema_key(root, schema)
    return ("created", "已从 config.template.yaml 生成 config.yaml → 填写「本项目」context 段")


def _openspec_cli_version():
    cli = shutil.which("openspec") or shutil.which("openspec.cmd") or "openspec"
    try:
        proc = subprocess.run([cli, "--version"], capture_output=True, text=True,
                              check=False, encoding="utf-8", errors="replace")
    except OSError as exc:
        return None, f"命令不可用（{exc}）"
    if proc.returncode != 0:
        return None, f"命令退出码 {proc.returncode}"
    match = re.search(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)", proc.stdout or "")
    if not match:
        return None, "输出不是可解析的 semver"
    return tuple(int(x) for x in match.groups()), None


def _schema_gate(root):
    version, error = _openspec_cli_version()
    if version is None or version < MIN_SCHEMA_CLI:
        reason = error or f"版本 {'.'.join(map(str, version))} < 1.7.0"
        return False, f"版本门：不铺 project-local schema（{reason}），保持内置 {BUILTIN_SCHEMA}"
    return True, f"版本门：铺设 project-local schema（openspec {'.'.join(map(str, version))}）"


def migrate_changes(root, schema=BUILTIN_SCHEMA):
    """为仅含 proposal.md 的在途 change 补写当前旧 schema；失败必须向上抛。

    这里把“stray 目录”定义为 changes 下没有 proposal.md 的目录；它们不是
    change，不参与迁移。archive 目录则是另一类明确排除项。
    """
    changes = os.path.join(root, "openspec", "changes")
    count = 0
    if not os.path.isdir(changes):
        return count
    for name in os.listdir(changes):
        if name == "archive":
            continue
        path = os.path.join(changes, name)
        if not os.path.isdir(path) or not os.path.isfile(os.path.join(path, "proposal.md")):
            continue
        marker = os.path.join(path, ".openspec.yaml")
        if os.path.exists(marker):
            if _marker_schema(marker) not in VALID_CHANGE_MARKER_SCHEMAS:
                raise RuntimeError(f"在途 change 的 schema marker 非法或不匹配：{marker}")
            continue
        _atomic_write(marker, f"schema: {schema}\n".encode("utf-8"), ".openspec.")
        count += 1
    return count


def _marker_schema(marker):
    """Return the single schema value in a migration marker, or fail loudly.

    Marker 文件永远是 `migrate_changes` 自己写的单行 `schema: <value>\\n`（见 `_atomic_write`
    调用点）——这里的解析是防用户手工改坏该文件的防御性校验，MUST 恰好一个 `schema` 键、
    值非空字符串，语义同旧版手搓正则（拒绝额外键/空值/多余非注释内容）。"""
    try:
        data = _yq(".", marker, default={})
    except RuntimeError as exc:
        raise RuntimeError(f"schema marker 不可解析：{marker}: {exc}") from exc
    if not isinstance(data, dict) or set(data.keys()) != {"schema"}:
        raise RuntimeError(f"schema marker 不可解析：{marker}")
    value = data.get("schema")
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"schema marker 不可解析：{marker}")
    return value


# ── config-lint（mlh-p3-determ-guards Task 2；解析层 shared-yaml-subset-parser 迁 yq）──
#
# openspec/config.yaml 结构 fail-closed 校验门：只校验结构（顶层键存在 / 子键归属），
# 不碰内容文案。语法层（缩进/冒号/引号/注释剥离/多文档判定）全部委托 `_yq('.', cfg_path)`
# **一次性**读出整份文档的 dict——不再按键路径逐个调用（`.schema` / `.rules` / ...）：
# yq 是整份文档解析，document 内任何一处语法错误（如越权测试语料里的漏冒号叶子）都会让
# **同一份文件的任何查询表达式**同等失败，分别调用只会重复触发同一次失败，一次读出更简单
# 也更快。顶层块（model-tiers / metrics）「先探测存在再校验」，块整段缺失一律条件化放行
# （mlh-p2 假阳教训，memory dogfood-blind-spot-source-config：sdflow-init update 从不注入
# 新顶层键，故 100% 存量消费仓 config 无这些块，缺块是正常态、不是违规）；绝不裸
# `cfg["k"]["j"]` 式取键，坏了是 KeyError 裸 traceback，不是人可读 reason。
#
# 〔与旧版行级扫描器的诊断精度差异，见 impl-report〕整份文档语法错误（如 `model-tiers:` 块内
# 一处漏冒号）此前能被旧扫描器局部容错、精确点名哪一行；yq 是真解析器，会让**整份文件**判定
# 解析失败，`lint_config` 只能报一条笼统的「解析失败」reason（含 yq 原始诊断）。这是 yq 委托
# 的既定代价（spec-review F9/decision-memo），不是本次改动引入的新缺陷。

TIER_ALLOWED_SUBKEYS = {"strong", "mid", "light"}
TIER_FLEET_KEYS = {"claude", "codex"}          # add-codex-host-support ADR-8：按机队分键
RULES_REQUIRED_SUBKEYS = ("proposal", "specs", "design", "tasks")


def _valid_model_id(v):
    """model-tiers 值的合法字符集校验（与 resolve-models.sh::_valid_model_id 同一有界口径，
    跨语言各自本地重实现——add-codex-host-support D5/D10：值只准 [A-Za-z0-9._-]、首字符字母
    数字、非空，拒绝换行/控制字符/shell 元字符，防 eval 注入面的值经消费仓 config 回灌到
    resolve-models.sh 的输出。"""
    if not v:
        return False
    if not (v[0].isalnum() and v[0].isascii()):
        return False
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    return all(c in allowed for c in v)


def _model_tiers_from_dict(raw):
    """model-tiers 顶层块的业务校验（fleet 键集识别/越域键检测/畸形头检测），在 yq 已解析出
    的 dict 上执行——语法层（缩进/冒号/引号/注释）全部由 yq 负责，本函数只做键集/值形态判断。
    机队分键 `{claude,codex}.{strong,mid,light}` 与扁平旧格式 `{strong,mid,light}`（ADR-8）
    两种写法。返回 (entries, bad_subkeys, bad_headers)，语义同旧版 `_parse_model_tiers_block`：
      entries: {"claude.strong": "opus", "flat.mid": "sonnet", ...}（值转 str；yq 的 null
                （空值叶子）映射为空串，保留旧版「空值即无效模型ID」的语义，_valid_model_id
                对空串恒返回 False）
      bad_subkeys: 越域键集合（顶层非法二级键 + 机队子块下的三级越域叶子键）
      bad_headers: 机队头值非 dict（标量误用，如 `claude: rogue` 单独一行、无更深嵌套）

    〔与旧版行级扫描器的差异，见 impl-report〕旧版还需处理「漏冒号叶子」「机队头带尾随内容
    且带更深缩进子块」这两类——它们在真 YAML 语法下是**非法文档**（`mapping values are not
    allowed in this context`），yq 对整份 config.yaml 直接判定解析失败，根本到不了本函数；
    `lint_config` 在读取阶段已把它们收作「config.yaml 解析失败」，故本函数不再需要旧版那套
    靠行扫描器容错、局部诊断的 fleet_ctx 状态机与逐层 reset 规则。"""
    entries, bad, bad_headers = {}, set(), []
    if not isinstance(raw, dict):
        return entries, bad, bad_headers
    for k, v in raw.items():
        if k in TIER_FLEET_KEYS:
            if not isinstance(v, dict):
                bad_headers.append(f"{k}: {v}")   # 机队名当标量误用（如 `claude: rogue`）
                continue
            for tk, tv in v.items():
                if tk in TIER_ALLOWED_SUBKEYS:
                    entries[f"{k}.{tk}"] = "" if tv is None else str(tv)
                else:
                    bad.add(f"{k}.{tk}")
        elif k in TIER_ALLOWED_SUBKEYS:
            entries[f"flat.{k}"] = "" if v is None else str(v)
        else:
            bad.add(k)
    return entries, bad, bad_headers


def _detect_duplicate_top_keys(cfg_path):
    """行级扫描 YAML 顶层键（缩进=0 的 key: 行），返回重复键列表。"""
    seen = {}
    try:
        with open(cfg_path, encoding="utf-8-sig") as f:
            for lineno, line in enumerate(f, 1):
                if line and not line[0].isspace() and not line.startswith("#"):
                    m = re.match(r"([A-Za-z_][\w-]*):", line)
                    if m:
                        key = m.group(1)
                        seen.setdefault(key, []).append(lineno)
    except (OSError, UnicodeDecodeError):
        return []
    return [f"{k}（行 {','.join(map(str, lns))}）" for k, lns in seen.items() if len(lns) > 1]


def lint_config(root):
    """校验 <root>/openspec/config.yaml 的结构，返回 reason 字符串列表（空 = 干净）。
    校验项：① 顶层 `schema:` 键存在 ② 顶层 `rules:` 块存在且含 proposal/specs/design/tasks
    四子键（无条件必填） ③ 顶层 `model-tiers:`（若存在）——机队分键 `{claude,codex}.{strong,mid,
    light}` 或扁平旧格式 `{strong,mid,light}`（ADR-8），二级键须 ⊆ {claude,codex,strong,mid,light}，
    且叶子键的**值**须为合法模型 ID（add-codex-host-support D5：拒绝空值/非法字符，防 eval 注入面
    经消费仓 config 回灌） ④ 顶层 `metrics:`（若存在）`enabled:` 值 ∈ {true,false}。

    yq 不可用（未装/非 mikefarah）→ `_check_yq()` 前置门给出一条带安装指引的 reason（不崩溃/
    不退出，`lint_config` 的公开契约就是「返回 reason 列表」）。config.yaml 缺失/不可读/整份
    语法错误（含非 UTF-8）→ 单条 reason（`_yq()` 的原始诊断，不再是精确定位到哪一行/哪个标量
    的手搓诊断）。"""
    ok, reason = _check_yq()
    if not ok:
        return [reason]

    cfg_path = os.path.join(root, "openspec", "config.yaml")
    dups = _detect_duplicate_top_keys(cfg_path)
    if dups:
        return [f"config.yaml 顶层键重复: {'; '.join(dups)}（yq 会 last-wins 静默合并）"]
    try:
        cfg = _yq(".", cfg_path, default={})
    except RuntimeError as e:
        return [f"config.yaml 不可读或解析失败: {cfg_path}: {e}"]
    if cfg is None:
        cfg = {}
    if not isinstance(cfg, dict):
        return [f"config.yaml 顶层结构非 dict: {cfg_path}"]

    reasons = []

    if "schema" not in cfg:
        reasons.append("缺顶层 schema: 键")

    rules = cfg.get("rules")
    if not isinstance(rules, dict):
        reasons.append("缺顶层 rules: 块")
    else:
        missing = [k for k in RULES_REQUIRED_SUBKEYS if k not in rules]
        if missing:
            reasons.append(f"rules: 缺子键 {missing}（须含 proposal/specs/design/tasks）")

    if cfg.get("model-tiers") is not None:  # 条件化：块整段缺失 → 跳过（放行）
        entries, bad, bad_headers = _model_tiers_from_dict(cfg["model-tiers"])
        if bad:
            reasons.append(
                f"model-tiers: 子键越域 {sorted(bad)}"
                f"（顶层须 ⊆ {{claude,codex,strong,mid,light}}，机队子块叶子键须 ⊆ {{strong,mid,light}}）")
        if bad_headers:
            # 〔Task 6 复评 Critical〕机队头带非空尾随内容（fleet 名当标量误用），是 fleet 归属
            # 串扰入口——报违规，与 resolve-models.sh 的 reset 语义一致（GC-6/D10）。
            reasons.append(
                f"model-tiers: 机队头带尾随内容 {sorted(bad_headers)}"
                f"（`claude:`/`codex:` 须为空的嵌套块头，值另起 strong/mid/light 缩进行；纯注释头合法）")
        bad_values = [f"{k}={v!r}" for k, v in sorted(entries.items()) if not _valid_model_id(v)]
        if bad_values:
            reasons.append(f"model-tiers: 值非法模型ID {bad_values}（须为 [A-Za-z0-9._-]+，首字符字母数字）")

    metrics = cfg.get("metrics")
    if metrics is not None:  # 条件化：块整段缺失 → 跳过（放行）
        enabled = metrics.get("enabled") if isinstance(metrics, dict) else None
        if not isinstance(enabled, bool):
            reasons.append("metrics: enabled 值非法或缺失（须为 true|false）")

    return reasons


def cmd_config_lint(root):
    """跑 lint_config 并落 stdout/stderr + 退出码：干净 0，违规非零、reason 逐条 stderr。"""
    reasons = lint_config(root)
    if reasons:
        for r in reasons:
            print(f"[config-lint] VIOLATION: {r}", file=sys.stderr)
        return 1
    print("[config-lint] CLEAN", file=sys.stderr)
    return 0


def _git_root_or_dot():
    """config-lint 专用 --root 缺省探测：`git rev-parse --show-toplevel` 探 git 仓根；
    非 git 仓 / 命令失败 → 降级当前目录 "."（M7）。**不复用** init/update/retire-hooks 的
    `default="."`——那三个 mode 的 "." 语义是「就地铺设/操作当前目录」，config-lint 校验的是
    openspec/config.yaml，在 git 仓子目录里跑时应回溯到仓根而非误判"当前子目录没有 openspec/"。"""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
            encoding="utf-8", errors="replace",
        )
        top = out.stdout.strip()
        return top if top else "."
    except (OSError, subprocess.CalledProcessError):
        return "."


def ensure_global_hook(spec):
    """幂等把单个全局 hook 装好：脚本拷进 ~/.claude/hooks/ + 注册进 ~/.claude/settings.json
    对应 event 的 hooks 列表。spec 形如 HOOKS 里的一项。返回动作描述。
    """
    home_claude = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    acts = []

    hooks_dir = os.path.join(home_claude, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    dst = os.path.join(hooks_dir, spec["name"])
    if not os.path.exists(spec["src"]):
        return f"跳过（hook 源缺失：{spec['src']}）"
    with open(spec["src"], encoding="utf-8") as f:
        new_src = f.read()
    old_src = None
    if os.path.exists(dst):
        with open(dst, encoding="utf-8") as f:
            old_src = f.read()
    if old_src != new_src:
        shutil.copyfile(spec["src"], dst)
        acts.append("脚本已" + ("更新" if old_src is not None else "安装") + f" {dst}")
    else:
        acts.append("脚本已最新")

    # [F-C] settings 注册走 <settings>.lock（与 deregister 同一把锁）——register×deregister
    # 跨进程并发不再互相 lost-update（否则一进程基于旧 snapshot 写回会复活退役 hook / 丢当前 hook）。
    settings = os.path.join(home_claude, "settings.json")
    lock_fd = _acquire_settings_lock(settings)
    try:
        acts.append(_register_hook_in_settings_locked(settings, spec))
    finally:
        _release_settings_lock(lock_fd)
    return "；".join(acts)


def _register_hook_in_settings_locked(settings, spec):
    """在持 <settings>.lock 下把 spec 幂等注册进 settings.json，返回注册状态描述。
    [F-B] 遍历既有条目用 isinstance 守卫 + `_hook_command`——畸形 settings（非 dict entry /
    非 str command，用户/三方工具可写）不再裸抛 AttributeError/TypeError（原 `entry.get`/
    `h.get`/`name in (... or "")` 会崩，与 _deregister 的 CR-F1 口径不对称，此处对齐）。
    [F-C] 写走共享 _atomic_write_settings（tmp+os.replace，与 deregister 同口径）。"""
    if os.path.exists(settings):
        try:
            with open(settings, encoding="utf-8") as f:
                data = json.load(f)
        except (ValueError, OSError):
            return "跳过注册（~/.claude/settings.json 非合法 JSON，请手动注册）"
        if not isinstance(data, dict):
            return "跳过注册（~/.claude/settings.json 顶层非对象）"
    else:
        data = {}

    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        data["hooks"] = hooks
    event_list = hooks.get(spec["event"])
    if not isinstance(event_list, list):
        event_list = []
        hooks[spec["event"]] = event_list

    for entry in event_list:
        inner = entry.get("hooks") if isinstance(entry, dict) else None
        for h in (inner or []):
            if spec["name"] in _hook_command(h):
                return "已注册（全局）"

    event_list.append({
        "matcher": spec["matcher"],
        "hooks": [{"type": "command", "command": spec["cmd"]}],
    })
    if _atomic_write_settings(settings, data):
        return f"已注册 → ~/.claude/settings.json（{spec['event']}）"
    return "跳过注册（settings.json 写失败，请手动注册）"


def ensure_global_hooks():
    """按 HOOKS 逐个幂等安装，返回多行汇总。"""
    lines = [f"  · {spec['name']}：{ensure_global_hook(spec)}" for spec in HOOKS]
    codex_home = os.path.expanduser("~/.codex")
    if os.path.isdir(codex_home):
        lines.append("  ⚠ 检测到 Codex 环境，如使用 Codex 会话请注意：hook 仅 Claude 侧生效")
    return "\n".join(lines)


def _home_claude():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")


def _hook_command(h):
    """安全取一个 hook entry 的 command 字符串：h 非 dict、或 command 非 str（含缺失）
    一律回 ''——让调用方的 `name in ...` 判为不匹配、原样保留。settings.json 用户/三方
    工具可写，畸形条目（非 dict 元素 / 非 str command）不得让反注册抛异常（[impl-review-fix] CR-F1）。"""
    if not isinstance(h, dict):
        return ""
    c = h.get("command")
    return c if isinstance(c, str) else ""


def _acquire_settings_lock(settings):
    """T49：在独立 lockfile `<settings>.lock` 上取 fcntl.flock(LOCK_EX)，串行化整个
    读-改-写-replace 临界区——杜绝并发 deregister「各基于旧内容读→写→replace，一次修改
    被静默覆盖」的 lost-update。lockfile 独立于 settings.json（后者被 os.replace 换 inode，
    锁须挂在不被替换的稳定 inode 上）且**不 unlink**（unlink-while-locked 经典竞态会破坏互斥）。
    fcntl 仅 POSIX——Windows（fcntl 缺失）或加锁失败 → 返回 None，best-effort 降级为无锁
    （保持既有行为、不新增崩溃面，局限：Windows 上并发 lost-update 窗口仍在）。返回持锁 fd 或 None。"""
    if fcntl is None:
        return None
    try:
        fd = os.open(settings + ".lock", os.O_CREAT | os.O_RDWR, 0o600)
    except OSError:
        return None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
    except OSError:
        os.close(fd)
        return None
    return fd


def _release_settings_lock(fd):
    """释放 _acquire_settings_lock 取得的锁并关 fd（fd 为 None 时 no-op）。
    [F-D] flock(LOCK_UN)/os.close 的 OSError（EBADF/EINTR 等罕见态）一律吞——retire-hooks
    CLI 模式无 run() 的外层 try 兜底，此处裸抛会打断 RETIRED_HOOKS 循环 + 留裸 traceback，
    违「绝不中止、坏则跳过」（fail-safe 与 FB-3 一致）。os.close 恒在 finally 执行。"""
    if fd is None:
        return
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
    except OSError:
        pass


def _atomic_write_settings(settings, data):
    """[F-C] 原子写 settings.json（tmp + os.replace）——deregister 与 register 共用同一写口径。
    **须在持 <settings>.lock 下调用**。写成功返回 True；OSError（只读/满盘/权限）→ 不裸抛、
    返回 False（FB-3：绝不中止 retire_hooks 循环 / setup.sh，坏则跳过）。"""
    try:
        fd, tmp = tempfile.mkstemp(prefix=".settings-", dir=os.path.dirname(settings))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, settings)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except OSError:
        return False
    return True


def _deregister_hook_in_settings(settings, name):
    """从 settings.json 各 event 列表外科式摘除 command 引用 `name` 脚本的条目：
    entry 内多 hook 时只删匹配的那个、保留兄弟；entry 内 hook 全被删则整条 entry 丢弃；
    保留其余用户/其它 skill 的 hook。改动则回写。坏 JSON / 结构异常一律 fail-safe 跳过。
    返回是否发生了摘除。

    [T49] 整个读-改-写-replace 在 <settings>.lock 的排他 flock 下串行化（并发 lost-update
    收窗）；锁在 POSIX 生效、Windows best-effort 降级无锁。"""
    if not os.path.exists(settings):
        return False
    lock_fd = _acquire_settings_lock(settings)
    try:
        return _deregister_hook_in_settings_locked(settings, name)
    finally:
        _release_settings_lock(lock_fd)


def _deregister_hook_in_settings_locked(settings, name):
    """_deregister_hook_in_settings 的临界区实现（须在持 <settings>.lock 下调用）。"""
    try:
        with open(settings, encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError):
        return False
    if not isinstance(data, dict) or not isinstance(data.get("hooks"), dict):
        return False
    changed = False
    for event, event_list in list(data["hooks"].items()):
        if not isinstance(event_list, list):
            continue
        new_list = []
        for entry in event_list:
            inner = entry.get("hooks") if isinstance(entry, dict) else None
            if isinstance(inner, list):
                kept = [h for h in inner if name not in _hook_command(h)]
                if len(kept) != len(inner):
                    changed = True
                    if kept:
                        entry["hooks"] = kept
                        new_list.append(entry)
                    # kept 为空 → 该 entry 仅剩退役 hook，整条丢弃
                else:
                    new_list.append(entry)
            else:
                new_list.append(entry)
        data["hooks"][event] = new_list
    if changed:
        # [impl-review-fix] FB-3：写路径 fail-safe（与读路径一致），走共享 _atomic_write_settings
        # （tmp+os.replace，OSError→False 不裸抛，不打断 retire_hooks 循环 / setup.sh）。
        if not _atomic_write_settings(settings, data):
            return False
    return changed


def retire_hooks():
    """反注册 RETIRED_HOOKS 里的每个退役 hook（自愈存量安装，ADR-1）：
    ① 从 ~/.claude/settings.json 外科式摘除其注册；② 删 ~/.claude/hooks/ 里的脚本。
    幂等、fail-safe（坏 JSON / 缺文件不崩）、fresh 安装无残留则 no-op。返回多行动作汇总。"""
    home_claude = _home_claude()
    settings = os.path.join(home_claude, "settings.json")
    hooks_dir = os.path.join(home_claude, "hooks")
    acts = []
    for name in RETIRED_HOOKS:
        deregistered = _deregister_hook_in_settings(settings, name)
        script = os.path.join(hooks_dir, name)
        removed_file = False
        if os.path.isfile(script):
            try:
                os.remove(script)
                removed_file = True
            except OSError:
                pass
        notes = []
        if deregistered:
            notes.append("摘 settings 注册")
        if removed_file:
            notes.append("删脚本")
        if notes:
            acts.append(f"{name}：" + " + ".join(notes))
    return "\n".join(f"  · {a}" for a in acts) if acts else "  · 无退役 hook 残留"


# ── 主流程 ──────────────────────────────────────────────────

def run(root, mode, dev=False):
    if dev:
        toolkit_root = os.path.realpath(os.path.dirname(SKILL_DIR))
        if os.path.realpath(root) != toolkit_root:
            _die("--dev 仅用于 toolkit 源仓自身（防把整套规则灌进消费仓）；当前 --root 不是本脚本所在仓")

    try:
        osroot = os.path.join(root, "openspec")
        if mode == "init":
            os.makedirs(osroot, exist_ok=True)
        elif not os.path.isdir(osroot):
            _die("openspec/ 不存在——update 需在已铺设的项目里跑；空项目请用 init")

        report = []
        made = ensure_dirs(root)
        if made:
            report.append("建目录：" + " ".join(made))

        schema_enabled, schema_msg = _schema_gate(root)
        report.append(schema_msg)
        target_schema = PROJECT_SCHEMA if schema_enabled else BUILTIN_SCHEMA
        # 迁移必须先于 config 切换：补写方读取的是当前旧 schema；颠倒会把在途
        # change 错钉到 fork。任何一个 change 写失败都中止本次 run，避免半迁移。
        if schema_enabled:
            # 迁移 marker 是本 change 的旧内置 schema 锁；后续重跑时 config 已是 fork，
            # 仍须接受此前成功写入的旧锁，而不是把它误判为异常。
            migrated = migrate_changes(root, BUILTIN_SCHEMA)
            report.append(f"迁移在途 change：补写 {migrated} 个（仅 proposal.md 且无 .openspec.yaml）")
        else:
            report.append("迁移在途 change：跳过（CLI 版本门未通过）")

        dst, n = copy_bundle(root, full=dev, include_schema=schema_enabled)
        dev_suffix = "（--dev 整刷）" if dev else ""
        report.append(f"铺 bundle：openspec/workflow/{dev_suffix}（{n} 文件，{'覆盖' if mode=='update' else '写入'}）")

        report.append("hack 脚本：不再铺进仓（checkpoint 已全局化 → ~/.sdflow/hack/，由 setup.sh 安装）")

        report.append("全局 hooks：\n" + ensure_global_hooks())

        # 退役 hook 反注册（ADR-1）：init 与 update 都跑，自愈存量安装（fresh 则 no-op）。
        report.append("退役 hook 清理：\n" + retire_hooks())

        # 退役部署文件清理（drop-review-html-viewer）：曾铺进消费仓的查看器根锚（serve.sh +
        # review.html），签名门控删除；tools/ 下查看器资产随 copy_bundle 整删重拷自动清除。
        report.append("退役部署文件清理：\n" + retire_deploy_files(root))

        # init 与 update 都跑：fresh init 无残留自然零告警；老仓误跑 init 不再假绿（B2-F3）。
        # T15：--dev 模式跳过——dev 刻意铺规则进 openspec/workflow/，告警是误报。
        if not dev:
            for w in stale_shadow_warnings(root):
                report.append(w)

        cstat, cmsg = handle_config(root, mode, schema=target_schema)
        report.append(f"config.yaml：{cmsg}")

        runtime_snippet = os.path.join(SNIPPETS, "runtime-gitignore.txt")
        with open(runtime_snippet, "rb") as handle:
            runtime_action = merge_runtime_gitignore(root, handle.read())
        report.append(f".gitignore runtime：{runtime_action}")

        # INDEX.md 托管区块
        idx = os.path.join(osroot, "INDEX.md")
        a = inject(idx, *MARK_IDX, read_snippet("index-section.md"),
                   header="# OpenSpec Index\n\n本文件是当前仓库 OpenSpec 资产索引。")
        report.append(f"openspec/INDEX.md：{a}")

        # CLAUDE.md / AGENTS.md 托管区块
        sec = read_snippet("claude-section.md")
        for fn in ("CLAUDE.md", "AGENTS.md"):
            p = os.path.join(root, fn)
            a = inject(p, *MARK_DOC, sec,
                       header=f"# {fn.split('.')[0]}\n\n本文件为项目级 AI 指令。")
            report.append(f"{fn}：{a}")
    except (OSError, shutil.Error, ValueError, RuntimeError) as e:
        _die(f"文件系统操作失败：{e}")

    print(f"✓ sdflow-init {mode} 完成 @ {os.path.abspath(root)}\n")
    for r in report:
        print("  - " + r)
    if cstat in ("created", "exists"):
        print("\n下一步（模型/人工）：")
        if cstat == "created":
            print("  · 编辑 openspec/config.yaml 的「## 本项目」context 段，填本项目 tech stack/约定")
        else:
            print("  · 合并 openspec/config.yaml：把模版的「通用」context 段 + rules 并入，保留你的「本项目」段")
        print("  · 安装配套 skill：bash ~/.skills/sdflow-skills/setup.sh（/sdflow-spec-review /sdflow-code-review /sdflow-done）")


def _die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="把 openspec/workflow bundle 铺进项目")
    p.add_argument("mode", choices=["init", "update", "retire-hooks", "config-lint"],
                   help="init=首次铺设 / update=重拉最新 bundle / retire-hooks=只反注册退役 hook（自愈，"
                        "不碰 openspec/） / config-lint=校验 openspec/config.yaml 结构（fail-closed）")
    p.add_argument("--root", default=None,
                   help="目标项目根（init/update/retire-hooks 默认当前目录；config-lint 缺省探 git 仓根，"
                        "非 git 仓降级当前目录）")
    p.add_argument("--dev", action="store_true",
                   help="update 专用：整 bundle 刷新（toolkit 源仓 dogfood 用，消费仓勿用）")
    args = p.parse_args()
    if args.mode == "config-lint":         # 早分支：mode 第 4 值，不引入 add_subparsers 重构
        root = args.root if args.root is not None else _git_root_or_dot()
        sys.exit(cmd_config_lint(root))
    if args.mode == "retire-hooks":       # A4: 早分支，先于 osroot/dev——只自愈全局 hook，与项目无关
        print("退役 hook 清理：\n" + retire_hooks())
        return
    if args.dev and args.mode != "update":
        _die("--dev 仅配 update 使用")
    run(args.root if args.root is not None else ".", args.mode, dev=args.dev)


if __name__ == "__main__":
    main()
