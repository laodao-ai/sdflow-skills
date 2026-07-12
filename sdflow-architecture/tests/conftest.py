import textwrap

def make_sad(status="draft", schema=1, facts=None, cache=0, assumptions=(),
             slice_section=False, subsystems=("采集端",), extra=""):
    """构造结构合法的 SAD 文本。assumptions=[(编号,处置)]，同时产内联与表行。"""
    facts = facts or {"positioning": "missing", "external_systems": "missing",
                      "hard_constraints": "missing"}
    fm = ["---", f"sad_schema: {schema}", f"sad_status: {status}", "facts:"]
    fm += [f"  {k}: {v}" for k, v in facts.items()]
    fm += [f"assumptions_open: {cache}", "---", ""]
    body = ["# SAD", ""]
    inline = " ".join(f"[假设-{n}]" for n, _ in assumptions) or "无假设。"
    sections = {
        "## 1. 目标与质量属性": "1. 可靠性\n2. 可维护性",
        "## 2. 约束": f"栈已定〔人拍〕 {inline}",
        "## 3. 外边界": "N/A — 单机无外部系统",
        "## 4. 架构策略与 ADR 索引": "见 openspec/adr/",
        "## 5. 子系统分解与 contract": "\n".join(
            f"### 5.{i+1} {s}\n- contract[draft] {s}接口：语法/语义/错误语义主干"
            for i, s in enumerate(subsystems)),
        "## 6. 运行场景": "场景A：启动→采集→上报",
        "## 7. 部署": "单机 binary",
        "## 8. 横切概念": "N/A — v1 无横切面",
        "## 9. 风险登记": "无已知风险",
        "## 10. 词汇表引用": "见 openspec/CONTEXT.md",
    }
    for anchor, content in sections.items():
        body += [anchor, "", content, ""]
    if slice_section:
        body += ["## 骨架切片建议", ""]
        body += [f"- 穿越点[{s}]：§5 contract 条目" for s in subsystems]
        body += ["- 骨架 DoD：每条 L1 contract 被一次真实调用穿过 + 部署链路走通",
                 "- 建议 change 名：skeleton-demo", ""]
    body += ["## 附录：假设清单", "", "| 编号 | 位置 | 内容 | 依据 | 处置 |",
             "|---|---|---|---|---|"]
    body += [f"| 假设-{n} | §2 | 某推测 | 类比 | {d} |" for n, d in assumptions]
    return "\n".join(fm + body) + ("\n" + extra if extra else "") + "\n"
