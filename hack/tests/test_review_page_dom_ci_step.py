"""CI 里「评审页 DOM 回归测试」step 的静态守卫（harden-review-page-followups · tasks 1.4）。

CI 实跑只能推分支后看日志；本文件锁住 step 的结构：条件、超时、命令、位置。
step 的 `if:` 带 `!cancelled()`，前面的 step 红了也照跑；少了它，前一步一红这条真浏览器门就静默不跑。
workflow 是文本，不引入 yaml 依赖（本仓脚本零依赖），按缩进切 step。
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORKFLOW = REPO / ".github" / "workflows" / "mechanical-gates.yml"
JOB_KEY = "gates"
FULL_SUITE_STEP = "Full test suite"
STEP_NAME = "Gate — 评审页 DOM 回归测试"
EXPECTED_IF = "${{ !cancelled() && matrix.os == 'ubuntu-latest' && matrix.python == '3.12' }}"


def _steps():
    """按 `      - name:` / `      - uses:` 行把 gates job 的 steps 切成块（每块是行列表）。

    限定在 JOB_KEY 这个 job 内：从 `  gates:` 到下一个 2 空格缩进的 job key 为止。
    """
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    job_start = next(i for i, l in enumerate(lines) if l == "  %s:" % JOB_KEY)
    job_end = next(
        (i for i in range(job_start + 1, len(lines)) if re.match(r"^  [A-Za-z0-9_-]+:", lines[i])),
        len(lines),
    )
    job = lines[job_start:job_end]
    start = next(i for i, l in enumerate(job) if l.strip() == "steps:")
    blocks, cur = [], None
    for line in job[start + 1:]:
        if re.match(r"^      - (name|uses):", line):
            cur = [line]
            blocks.append(cur)
        elif cur is not None:
            cur.append(line)
    return blocks


def _dom_step():
    hits = [b for b in _steps() if b[0].strip() == "- name: " + STEP_NAME]
    assert len(hits) == 1, "应恰有一个名为「%s」的 step，实际 %d 个" % (STEP_NAME, len(hits))
    return hits[0]


def test_step_is_after_full_test_suite():
    names = [b[0].strip() for b in _steps()]
    assert "- name: " + FULL_SUITE_STEP in names, names
    assert names.index("- name: " + STEP_NAME) > names.index("- name: " + FULL_SUITE_STEP)


def test_step_if_runs_even_when_earlier_steps_fail():
    block = _dom_step()
    ifs = [l.strip() for l in block if l.startswith("        if:")]
    assert ifs == ["if: " + EXPECTED_IF]


def test_step_has_15_minute_timeout():
    block = _dom_step()
    assert [l.strip() for l in block if l.startswith("        timeout-minutes:")] == ["timeout-minutes: 15"]


def test_step_runs_three_commands_in_order():
    body = "\n".join(_dom_step())
    needles = [
        "cd sdflow-init/tests/dom && npm ci",
        "npx playwright install --with-deps chromium",
        "SDFLOW_REQUIRE_DOM=1 python -m pytest -q -rs sdflow-init/tests/test_review_page_dom.py",
    ]
    positions = [body.find(n) for n in needles]
    assert all(p >= 0 for p in positions), positions
    assert positions == sorted(positions)
