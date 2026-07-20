import json, subprocess, sys
from pathlib import Path
from conftest import commit_all, mkchange, head_sha, write_report

GATE = Path(__file__).resolve().parents[1] / "scripts" / "ship_gate.py"

def run_gate(root, change="demo"):
    r = subprocess.run([sys.executable, str(GATE), "--change", change,
                        "--root", str(root)], capture_output=True, text=True)
    lines = r.stdout.strip().splitlines()
    payload = json.loads(lines[-1]) if lines else {}
    return r.returncode, payload, lines[0] if lines else ""

def test_refuse_when_report_missing(repo):
    mkchange(repo); commit_all(repo, "seed")
    code, js, human = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    assert "补锚" in js["reason"]  # exit3 文案含人工补锚指引（D2）

def test_refuse_when_anchor_missing(repo):
    d = mkchange(repo)
    (d / "spec-review-report.md").write_text("# 报告\n结论：通过\n", encoding="utf-8")
    commit_all(repo, "seed")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

def test_pass_gate_when_anchor_present(repo):
    # [mlh-p5 Task5] live 迁 frontmatter（原 inline design-approved 锚）
    # [harden-gate-git-layer Task1] 两段提交：先有盘面可锚，报告才写得出 reviewed_sha
    d = mkchange(repo)
    commit_all(repo, "seed")
    write_report(d, "spec-review-report.md", head_sha(repo),
                 body="# 报告\n", design_approved="true")
    commit_all(repo, "spec-review report")
    code, js, human = run_gate(repo)
    assert code == 0 and js["verdict"] != "REFUSE_START"
    assert human.startswith("[ship-gate]")  # D2 首行人读

def test_verify_conflict_anchors_unknown(repo):
    # [mlh-p5 Task5] live 迁 frontmatter：frontmatter 世界里"两个互斥锚并存"的等价形态是
    # 顶层同字段重复键（duplicate-key）——inline 的 PASS+FAIL 并存判据在 Task 6 退役
    # live inline 读半场（对应函数 T75 一并删除）后不再可达，迁移后改用 duplicate-key 复现"歧义 verify 状态→UNKNOWN"
    # 同一不变量（verdict/exit/reason 含"verify"均不变；与 test_frontmatter_live_read.py::
    # test_live_dup_key_unknown 覆盖重叠，属有意——两处分别锚 preflight 早检入口与
    # frontmatter 解析器本身，双证据不算冗余）。
    d = mkchange(repo)
    commit_all(repo, "seed")
    write_report(d, "spec-review-report.md", head_sha(repo),
                 body="# 报告\n", design_approved="true")
    (d / "verify-report.md").write_text(
        "---\nship-gate:\n  verify: PASS\n  verify: FAIL\n---\n# 验证报告\n",
        encoding="utf-8")
    commit_all(repo, "reports")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "verify" in js["reason"]

def test_gbk_report_no_crash(repo):
    # [impl-review-fix] 裁决项8：非 UTF-8（GBK）报告不应让 gate 崩溃（traceback）。
    # 锚行本身是 ASCII，跨编码字节一致；中文正文用 GBK 编码拼接进 bytes 写盘，
    # 断言只需不 traceback、能正常给出 verdict（errors="replace" 兜底解码）。
    # [mlh-p5 Task5] live 迁 frontmatter：GBK 鲁棒性改在 frontmatter 解析路径
    # （parse_ship_gate_frontmatter 内 read_text errors="replace"）上验证，
    # Task 6 退役 inline 读点后此覆盖仍有效。
    d = mkchange(repo)
    commit_all(repo, "seed")
    head = f"---\nship-gate:\n  design_approved: true\n  reviewed_sha: {head_sha(repo)}\n---\n"
    (d / "spec-review-report.md").write_bytes(
        head.encode("ascii") + "设计门拍板".encode("gbk") + b"\n")
    commit_all(repo, "spec-review report")
    code, js, _ = run_gate(repo)
    assert code in (0, 3, 4, 5, 6)  # 合法退出码集合，排除 traceback 导致的 1
    assert "verdict" in js and js["verdict"]  # 正常给出 verdict（未因解码异常崩溃）
