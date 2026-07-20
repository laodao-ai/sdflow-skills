import subprocess
import pytest

def _git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True,
                   capture_output=True, text=True)

@pytest.fixture
def repo(tmp_path):
    _git_init = ["init", "-q", "-b", "main"]
    subprocess.run(["git", "-C", str(tmp_path), *_git_init], check=True,
                   capture_output=True, text=True)
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "config", "user.email", "t@t")
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
