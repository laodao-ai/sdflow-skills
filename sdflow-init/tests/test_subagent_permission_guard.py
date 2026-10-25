"""subagent-permission-guard.py 的行为测试。

接缝：子进程真跑 hook 脚本，stdin 喂 JSON，读 stdout 与退出码。
期望值来自 design.md「拒绝输出」与 spec HAE-23…HAE-26 的字面要求，不从脚本导入。
"""
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "assets" / "hooks" / "subagent-permission-guard.py"

# design.md「拒绝输出」节的消息全文，{tool_name} 为占位。
EXPECTED_MESSAGE = (
    "[sdflow-permission-guard] 已自动拒绝这次 {tool_name} 调用。\n"
    "原因：你是 sdflow 派发的无人值守子代理，这次调用需要人工确认，不会有人来点确认。\n"
    "处理：\n"
    "1. 如果是删除类 Bash 命令：先查看展开后的删除目标，确认它在本任务的工作目录或你自建的临时目录内，"
    "再把目标写成字面路径，或用 ${VAR:?} 守卫变量。删除单独写成一条命令，不和其他操作写在一起。\n"
    "2. 不得换别的工具或写法绕开同一检查，例如 python -c 'shutil.rmtree(...)'、"
    "find … -delete 搭配拼接出来的路径。\n"
    "3. 其他工具，或核对不了目标、改写不了的情况：跳过这一步，在报告里写明被拒的调用和原因，"
    "并把该步标为未完成，交给主 session 处理。\n"
    "4. 同一操作第二次被拒：不要再试，按第 3 条处理。"
)


def run_raw(stdin_text):
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    )
    # 所有用例共用此入口：任何输入下 stdout 都不得出现 allow。
    assert "allow" not in proc.stdout
    return proc


def run(payload):
    return run_raw(json.dumps(payload))


def sdflow_payload(**over):
    payload = {
        "hook_event_name": "PermissionRequest",
        "permission_mode": "default",
        "agent_id": "agent-abc123",
        "agent_type": "sdflow-effort-high",
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf /tmp/x"},
    }
    payload.update(over)
    return payload


def assert_silent(proc):
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == ""


def assert_denied(proc, tool_name):
    assert proc.returncode == 0, proc.stderr
    spec = json.loads(proc.stdout)["hookSpecificOutput"]
    assert spec["hookEventName"] == "PermissionRequest"
    decision = spec["decision"]
    assert decision["behavior"] == "deny"
    assert "interrupt" not in decision
    assert decision["message"] == EXPECTED_MESSAGE.replace("{tool_name}", tool_name)
    return decision["message"]


def test_bash_delete_denied_with_exact_shape():
    assert_denied(run(sdflow_payload()), "Bash")


def test_write_denied_message_names_tool_and_skip_guidance():
    msg = assert_denied(run(sdflow_payload(tool_name="Write", tool_input={"file_path": "/x"})), "Write")
    assert "Write" in msg and "跳过" in msg and "未完成" in msg


def test_denied_in_every_permission_mode():
    for mode in ("default", "bypassPermissions", "auto"):
        assert_denied(run(sdflow_payload(permission_mode=mode)), "Bash")


def test_missing_tool_name_still_denied_as_unknown():
    payload = sdflow_payload()
    del payload["tool_name"]
    msg = assert_denied(run(payload), "unknown")
    assert "unknown" in msg


def test_non_string_tool_name_denied_as_unknown():
    for bad in (123, {"a": 1}, None, ["Bash"]):
        assert_denied(run(sdflow_payload(tool_name=bad)), "unknown")


def test_main_session_without_agent_id_is_silent():
    payload = sdflow_payload()
    del payload["agent_id"]
    assert_silent(run(payload))


def test_empty_agent_id_is_silent():
    assert_silent(run(sdflow_payload(agent_id="")))


def test_agent_type_without_agent_id_is_silent():
    # `--agent sdflow-*` 启动的主 session：有 agent_type、无 agent_id
    payload = sdflow_payload(agent_type="sdflow-effort-high")
    del payload["agent_id"]
    assert_silent(run(payload))


def test_non_sdflow_subagent_is_silent():
    assert_silent(run(sdflow_payload(agent_type="general-purpose")))


def test_near_prefix_agent_types_are_silent():
    for bad in ("Sdflow-effort-low", "sdflow", "sdfloweffort", " sdflow-x"):
        assert_silent(run(sdflow_payload(agent_type=bad)))


def test_message_contains_required_guidance():
    # 与 assert_denied 的整串相等断言重叠；保留是为对应 tasks 1.2 的逐项要求。
    msg = assert_denied(run(sdflow_payload()), "Bash")
    assert msg.startswith("[sdflow-permission-guard]")
    for needle in ("${VAR:?}", "确认它在本任务的工作目录或你自建的临时目录内", "shutil.rmtree",
                   "find", "跳过", "报告", "未完成", "第二次被拒"):
        assert needle in msg, needle


def test_invalid_inputs_are_silent():
    assert_silent(run_raw(""))  # 零字节
    assert_silent(run_raw("not json {"))
    assert_silent(run_raw("[1, 2, 3]"))
    assert_silent(run(sdflow_payload(agent_id=123)))
    assert_silent(run(sdflow_payload(agent_type=None)))
    assert_silent(run(sdflow_payload(agent_type=123)))


def test_deeply_nested_json_is_silent():
    # 解析层抛 RecursionError 之类异常时，整个 main 的 try 须兜住。
    assert_silent(run_raw("[" * 100000 + "]" * 100000))


def test_never_allows():
    """源码侧不含 "allow"；stdout 侧由 run_raw 统一断言。下面各输入只是让 run_raw 多走几条路径。"""
    procs = [
        run(sdflow_payload()),
        run(sdflow_payload(tool_name="Write")),
        run(sdflow_payload(permission_mode="bypassPermissions")),
        run(sdflow_payload(tool_name=None)),
        run(sdflow_payload(agent_id="")),
        run(sdflow_payload(agent_type="general-purpose")),
        run_raw("[]"),
        run_raw(""),
    ]
    assert len(procs) == 8
    assert "allow" not in HOOK.read_text(encoding="utf-8")


def test_closed_stdout_pipe_exits_zero_with_empty_stderr():
    """读端先关闭：hook 写 stdout 失败也要 exit 0 且 stderr 为空（不得以 120 退出）。"""
    proc = subprocess.Popen(
        [sys.executable, str(HOOK)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    proc.stdout.close()
    proc.stdin.write(json.dumps(sdflow_payload()))
    proc.stdin.close()
    stderr = proc.stderr.read()
    proc.stderr.close()
    assert proc.wait(timeout=20) == 0, stderr
    assert stderr == ""
