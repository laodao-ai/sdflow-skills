"""评审页 DOM 回归测试的 pytest 包装（harden-review-page-followups · tasks 1.3）。

真正的断言在 dom/review_page_dom.test.js（node --test + Playwright 的 chromium）。
本文件只做两件事：检查依赖是否齐全；齐全就跑 node 并把输出带回 pytest。

缺依赖时：SDFLOW_REQUIRE_DOM=1（CI 设置）判 FAIL，否则 skip。
本地裸跑 pytest 只显示 s，加 -rs 才打印 skip 理由。
"""
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

import pytest

DOM_DIR = Path(__file__).resolve().parent / "dom"
JS_TEST = DOM_DIR / "review_page_dom.test.js"
NODE_TIMEOUT_S = 600

FIX_NODE = "未找到 node：安装 Node 20 或更新版本后重跑"
FIX_NPM_CI = "cd sdflow-init/tests/dom && npm ci"
FIX_BROWSER = "cd sdflow-init/tests/dom && npx playwright install chromium"


def _missing_dependency():
    """返回 (缺的是什么, 可粘贴的修复命令)；依赖齐全返回 None。"""
    node = shutil.which("node")
    if node is None:
        return "node 不在 PATH 上", FIX_NODE
    for pkg in ("playwright", "mermaid"):
        if not (DOM_DIR / "node_modules" / pkg).is_dir():
            return "sdflow-init/tests/dom/node_modules/%s 不存在" % pkg, FIX_NPM_CI
    # 真实 launch 一次 chromium：只查 executablePath() 查不到 headless shell 缺失。
    # 探针超时按「依赖不可用」处理，与缺依赖同一语义（skip / REQUIRE 下 FAIL）。
    launch_js = (
        "const {chromium}=require('playwright');"
        "(async()=>{const b=await chromium.launch();await b.close();})()"
        ".catch(e=>{process.stderr.write(String(e.message||e));process.exit(1);})"
    )
    try:
        probe = subprocess.run(
            [node, "-e", launch_js],
            cwd=str(DOM_DIR), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
    except subprocess.TimeoutExpired:
        return "Playwright 的 chromium 启动探针 60 秒超时", FIX_BROWSER
    if probe.returncode != 0:
        return "Playwright 的 chromium 无法启动（%s）" % (probe.stderr.strip()[:200] or "无输出"), FIX_BROWSER
    return None


def _run_node_test(cmd, env):
    """跑 node --test；超时则杀整个进程组（chromium 是 node 的子孙，只杀 node 会留孤儿）。

    返回 (returncode, stdout, stderr)；超时返回 returncode=None。
    Windows 无 killpg / start_new_session，退回 proc.kill()。
    """
    posix = os.name == "posix"
    proc = subprocess.Popen(
        cmd, cwd=str(DOM_DIR), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", start_new_session=posix,
    )
    try:
        out, err = proc.communicate(timeout=NODE_TIMEOUT_S)
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        if posix:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            except ProcessLookupError:
                pass
            try:
                os.killpg(proc.pid, signal.SIGKILL)  # 组内残留（chromium）一并清掉
            except ProcessLookupError:
                pass
        else:
            proc.kill()
        out, err = proc.communicate()
        return None, out, err


def test_review_page_dom_regression():
    missing = _missing_dependency()
    if missing is not None:
        what, fix = missing
        reason = "评审页 DOM 回归测试缺依赖：%s。修复：%s" % (what, fix)
        if os.environ.get("SDFLOW_REQUIRE_DOM") == "1":
            pytest.fail(reason)
        pytest.skip(reason)

    env = dict(os.environ, SDFLOW_DOM_PYTHON=sys.executable)
    code, out, err = _run_node_test(
        [shutil.which("node"), "--test", str(JS_TEST)],  # node 24 下传目录会判失败，必须传文件路径
        env,
    )
    if code is None:
        pytest.fail("node --test 超过 %d 秒，已杀进程组\n" % NODE_TIMEOUT_S + (out or "")[-3000:] + (err or "")[-1000:])
    assert code == 0, out[-6000:] + err[-2000:]
