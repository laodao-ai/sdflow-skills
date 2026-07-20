import os
import subprocess
import pytest


# ── [harden-gate-git-layer Task3 fix1 · F3] fixture 的 git 调用**不读**用户 global/system config ──
# 理由与生产侧 `ship_gate.py::_git_env` **同一条**：判定输入不得受这台机器的 config 摆布。
# 生产侧封的是「被判仓的读取口径」，这里封的是「测试基座造出来的盘面本身」——
# 两者一旦分叉，测试造的仓就不是它断言的那个仓。
#
# 触发面是真的、不是假想：`core.autocrlf` / `core.fileMode` 在消费机上两种取值都存在
# （Windows 上 autocrlf=true 是安装默认；部分文件系统上 fileMode 被 git 自动置 false）。
# 帧比较整簇退役后，纯复选框翻转类用例依赖 `tasks.md` 的**字节原样回环**（同字节长度改动，
# autocrlf 一开就 CRLF↔LF 悄悄改字节）；而 `test_mode_only_change_on_tasks_is_stale` 依赖
# chmod 真进 git（fileMode 一关就失去区分力）。旧的退役用例曾各自显式补偿这两项，
# **补偿随退役一并消失** ⇒ 补偿必须上移到基座，且按面治（整片禁读）而非逐项点名。
#
# 🔴 锚目标态，不是「我这台机器上没事」：本机 global config 恰好没设这两项，不构成保证。
_DEVNULL_CONFIG = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}


def _git_env():
    env = os.environ.copy()
    for key in [k for k in env if k.startswith("GIT_")]:
        del env[key]
    env.update(_DEVNULL_CONFIG)
    return env


def _git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True,
                   capture_output=True, text=True, env=_git_env())

@pytest.fixture
def repo(tmp_path):
    _git_init = ["init", "-q", "-b", "main"]
    subprocess.run(["git", "-C", str(tmp_path), *_git_init], check=True,
                   capture_output=True, text=True, env=_git_env())
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "config", "user.email", "t@t")
    # 整片禁读之外**再钉死这两项**：`GIT_CONFIG_*=/dev/null` 只管 fixture 自己起的进程，
    # 而被测代码（以及 test 里直连 subprocess 的少数点）另有各自的 env 口径 ⇒ 把两个
    # 关键取值写进 repo-local `.git/config`，使盘面语义对**任何**读取者都一致。
    _git(tmp_path, "config", "core.autocrlf", "false")
    _git(tmp_path, "config", "core.fileMode", "true")
    return tmp_path

def commit_all(root, msg):
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", msg, "--allow-empty")

def mkchange(root, name="demo"):
    d = root / "openspec" / "changes" / name
    d.mkdir(parents=True, exist_ok=True)
    return d

# ── [harden-gate-git-layer Task1 · tasks 4.1] 录锚模型的测试基座 ────────────────
# 旧 fixture 一次 commit_all 把「报告」与「它审查的对象」放进同一个根提交 ⇒ 结构上不存在
# 先于报告的盘面可供落锚。新模型要求报告 frontmatter 带 reviewed_sha，故 fixture MUST 能
# 表达「四件套先落盘 → 读出 sha → 报告后落盘」的两段提交。

def head_sha(root):
    out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                         check=True, capture_output=True, text=True)
    return out.stdout.strip()

def sg_frontmatter(sha=None, **fields):
    """构造报告头部 ship-gate frontmatter 文本。

    sha=None 时**不写** reviewed_sha 字段（供「缺锚」负例用）。字段顺序 = 结论字段在前、
    锚在后，与三个 producer 模板逐字对齐（顶层 `ship-gate:` 列 0，字段缩进 2 空格）。
    """
    lines = ["---", "ship-gate:"]
    for k, v in fields.items():
        lines.append(f"  {k}: {v}")
    if sha is not None:
        lines.append(f"  reviewed_sha: {sha}")
    lines.append("---")
    return "\n".join(lines) + "\n"

def write_report(d, name, sha=None, body=None, **fields):
    """写一份带锚的报告（不提交）。返回该文件路径。"""
    body = body if body is not None else f"# {name}\n"
    (d / name).write_text(sg_frontmatter(sha, **fields) + body, encoding="utf-8")
    return d / name
