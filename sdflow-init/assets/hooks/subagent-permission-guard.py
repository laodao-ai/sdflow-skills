#!/usr/bin/env python3
"""sdflow 子代理权限确认守卫 —— PermissionRequest hook。

问题：sdflow 编排派发的后台子代理无人值守。子代理的工具调用一旦需要权限确认
（例如 Claude Code 对 `rm -rf "$(...)"` 这类带命令替换的删除总要确认），确认框没人点，
子代理会挂起到时长上限。

判定（只有一个）：
  · `agent_id` 是非空字符串，且 `agent_type` 是以 `sdflow-` 开头的字符串
    ⇒ 立即输出 deny 决策和处理方法，子代理继续运行（不设 `interrupt`）。
  · 其余一切情况（含非法输入、内部异常）⇒ 不输出、exit 0，权限流程照常。

为什么用 `agent_id` 排除主 session：Claude Code 只在子代理内部的调用上带 `agent_id`。
`--agent sdflow-*` 启动的主 session 有 `agent_type` 却没有 `agent_id`，只看 `agent_type`
会把有人在场的主 session 一并拒掉。

为什么不解析命令：shell 语法面无界，手写解析必然漏。本 hook 不读 `tool_input`，
不看 `permission_mode`，不按 `tool_name` 分支；`tool_name` 只写进拒绝消息，便于定位。
`tool_name` 缺失或不是字符串时写 `unknown`，仍然拒绝，避免拼消息时抛异常而落入 fail-open。

为什么 fail-open：本 hook 的失败代价是"退回今天的行为"（照常弹确认），
把无关的主 session 或第三方子代理误拒的代价更高。所以任何异常都不表态。

本 hook 从不放行：它只在"本来就要弹确认"的位置上替无人值守的子代理做出拒绝，
不替任何调用做出放行。

以上关于宿主行为的断言（带命令替换的 rm 总要确认、只有子代理内部调用带 agent_id）
的证据出处：openspec/changes/archive/2026-10-24-add-subagent-permission-guard/impl-reports/task1-interactive-probe.md

铺设/注册：由 `sdflow-init init/update` 装到全局 hooks 目录并注册到 settings.json 的
PermissionRequest（matcher `*`）；不进 `setup.sh`。
"""
import json
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

SUBAGENT_PREFIX = "sdflow-"

# 消息全文取自 change `add-subagent-permission-guard` 的 design.md「拒绝输出」节。
MESSAGE_TEMPLATE = (
    "[sdflow-permission-guard] 已自动拒绝这次 {tool_name} 调用。\n"
    "原因：你是 sdflow 派发的无人值守子代理，这次调用需要人工确认，不会有人来点确认。\n"
    "处理：\n"
    "1. 如果是删除类 Bash 命令：先查看展开后的删除目标，确认它在本任务的工作目录或你自建的临时目录内，"
    "再把目标写成字面路径，或用 ${{VAR:?}} 守卫变量。删除单独写成一条命令，不和其他操作写在一起。\n"
    "2. 不得换别的工具或写法绕开同一检查，例如 python -c 'shutil.rmtree(...)'、"
    "find … -delete 搭配拼接出来的路径。\n"
    "3. 其他工具，或核对不了目标、改写不了的情况：跳过这一步，在报告里写明被拒的调用和原因，"
    "并把该步标为未完成，交给主 session 处理。\n"
    "4. 同一操作第二次被拒：不要再试，按第 3 条处理。"
)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return
        agent_id = payload.get("agent_id")
        agent_type = payload.get("agent_type")
        if not (isinstance(agent_id, str) and agent_id):
            return
        if not (isinstance(agent_type, str) and agent_type.startswith(SUBAGENT_PREFIX)):
            return
        tool_name = payload.get("tool_name")
        if not isinstance(tool_name, str):
            tool_name = "unknown"
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {
                    "behavior": "deny",
                    "message": MESSAGE_TEMPLATE.format(tool_name=tool_name),
                },
            }
        }, ensure_ascii=False))
        # 显式 flush：管道已关时让 BrokenPipeError 在 try 内抛出，而不是解释器退出时抛出（退出码 120）。
        sys.stdout.flush()
    except Exception:
        # 参考 Python 官方文档 signal 模块 SIGPIPE 一节：把 stdout 指向 devnull，
        # 避免解释器退出时再次 flush 失败。
        try:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
        except Exception:
            pass
        return


if __name__ == "__main__":
    main()
    sys.exit(0)
