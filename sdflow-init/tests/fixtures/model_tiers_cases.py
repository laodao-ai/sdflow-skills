"""共享畸形输入语料（add-codex-host-support Task 6，design D10）。

`resolve-models.sh`（纯 shell，ADR-1）与 `config_lint`（`init.py::lint_config`，Python）是两个
独立工具、跨语言无法共享同一实现（`config_lint` MUST NOT import yaml，resolver MUST 纯 shell）。
用一份共享畸形输入语料替代"共用解析实现"：`test_resolve_models.py` 与 `test_config_lint.py`
均从本文件读取同一组用例，各自断言 accept/reject 判据一致——任一侧漂移即两测试集同时挖出。

新增/改判据（合法字符集、机队分键结构）MUST 同步更新两侧消费方式，不得只改一侧。
`CASES` 每条：
  name                用例标识
  yaml_block          附加在 `model-tiers:` 顶层键之后的 YAML 片段（含 `model-tiers:` 行本身）
  lint_clean          config_lint 期望的整洁性（True=exit 0，False=exit!=0）
  lint_reason_substrs 不整洁时 stderr 须含的子串列表（顺序不拘）
  resolver            每条 = {host, strong, mid, light}：该 host 下 resolve-models.sh 最终解析
                       出的三档位期望值（覆盖生效则为覆盖值，否则为该机队缺省）
  injection_marker    可选：若这条用例是恶意值回归，marker 文件名——断言 eval 后该文件未被创建
"""

CASES = [
    dict(
        name="nested_valid",
        yaml_block="""model-tiers:
  claude:
    strong: claude-strong-x
    mid: claude-mid-x
  codex:
    strong: codex-strong-x
""",
        lint_clean=True,
        lint_reason_substrs=[],
        resolver=[
            dict(host="claude", strong="claude-strong-x", mid="claude-mid-x", light="haiku"),
            dict(host="codex", strong="codex-strong-x", mid="gpt-5.6-terra", light="gpt-5.6-luna"),
        ],
    ),
    dict(
        name="flat_valid_claude_only",
        yaml_block="""model-tiers:
  strong: legacy-strong
  mid: legacy-mid
""",
        lint_clean=True,
        lint_reason_substrs=[],
        resolver=[
            # 扁平旧格式兼容读作 Claude 机队覆盖（ADR-8）
            dict(host="claude", strong="legacy-strong", mid="legacy-mid", light="haiku"),
            # Codex 机队 MUST NOT 读扁平覆盖 —— 回落 Codex 机队缺省
            dict(host="codex", strong="gpt-5.6-sol", mid="gpt-5.6-terra", light="gpt-5.6-luna"),
        ],
    ),
    dict(
        name="unknown_subkey",
        yaml_block="""model-tiers:
  strong: ok-model
  bogus: nope
""",
        lint_clean=False,
        lint_reason_substrs=["bogus", "model-tiers"],
        resolver=[
            # resolver 对未知子键宽容跳过（不崩），仍读到合法的 strong 覆盖
            dict(host="claude", strong="ok-model", mid="sonnet", light="haiku"),
            dict(host="codex", strong="gpt-5.6-sol", mid="gpt-5.6-terra", light="gpt-5.6-luna"),
        ],
    ),
    dict(
        name="injection_dollar_paren",
        yaml_block="""model-tiers:
  claude:
    strong: $(touch INJECTED_A)
""",
        lint_clean=False,
        lint_reason_substrs=["claude.strong"],
        resolver=[
            dict(host="claude", strong="opus", mid="sonnet", light="haiku"),
        ],
        injection_marker="INJECTED_A",
    ),
    dict(
        name="injection_backtick",
        yaml_block="""model-tiers:
  codex:
    strong: `touch INJECTED_B`
""",
        lint_clean=False,
        lint_reason_substrs=["codex.strong"],
        resolver=[
            dict(host="codex", strong="gpt-5.6-sol", mid="gpt-5.6-terra", light="gpt-5.6-luna"),
        ],
        injection_marker="INJECTED_B",
    ),
    dict(
        name="injection_semicolon_space",
        yaml_block="""model-tiers:
  claude:
    mid: sonnet; touch INJECTED_C
""",
        lint_clean=False,
        lint_reason_substrs=["claude.mid"],
        resolver=[
            dict(host="claude", strong="opus", mid="sonnet", light="haiku"),
        ],
        injection_marker="INJECTED_C",
    ),
    dict(
        name="injection_double_quote",
        yaml_block='''model-tiers:
  claude:
    light: "haiku" && touch INJECTED_D
''',
        lint_clean=False,
        lint_reason_substrs=["claude.light"],
        resolver=[
            dict(host="claude", strong="opus", mid="sonnet", light="haiku"),
        ],
        injection_marker="INJECTED_D",
    ),
    dict(
        name="empty_value",
        yaml_block="""model-tiers:
  claude:
    strong:
""",
        lint_clean=False,
        lint_reason_substrs=["claude.strong"],
        resolver=[
            dict(host="claude", strong="opus", mid="sonnet", light="haiku"),
        ],
    ),
]
