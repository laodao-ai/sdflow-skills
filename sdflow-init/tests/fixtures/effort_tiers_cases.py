"""HAE-11 的 resolver/config-lint 共享 effort-tiers 语料。"""

CASES = [
    {
        "name": "complete_fleet_overrides",
        "yaml_block": """effort-tiers:
  claude:
    strong: xhigh
    mid: medium
    light: low
  codex:
    strong: ultra
    mid: xhigh
    light: low
""",
        "lint_clean": True,
        "efforts": {
            "claude": ("xhigh", "medium", "low"),
            "codex": ("ultra", "xhigh", "low"),
        },
    },
    {
        "name": "partial_codex_override",
        "yaml_block": """effort-tiers:
  codex:
    mid: xhigh
""",
        "lint_clean": True,
        "efforts": {
            "claude": ("high", "medium", "low"),
            "codex": ("high", "xhigh", "low"),
        },
    },
    {
        "name": "claude_ultra_rejected",
        "yaml_block": """effort-tiers:
  claude:
    strong: ultra
""",
        "lint_clean": False,
        "efforts": {
            "claude": ("high", "medium", "low"),
            "codex": ("high", "medium", "low"),
        },
    },
    {
        "name": "flat_legacy_rejected",
        "yaml_block": """effort-tiers:
  strong: high
""",
        "lint_clean": False,
        "efforts": {
            "claude": ("high", "medium", "low"),
            "codex": ("high", "medium", "low"),
        },
    },
    {
        "name": "scalar_fleet_header_rejected",
        "yaml_block": """effort-tiers:
  codex: ultra
""",
        "lint_clean": False,
        "efforts": {
            "claude": ("high", "medium", "low"),
            "codex": ("high", "medium", "low"),
        },
    },
    {
        "name": "quoted_values_are_consumed",
        "yaml_block": """effort-tiers:
  claude:
    strong: 'xhigh'
  codex:
    strong: \"ultra\"
""",
        "lint_clean": True,
        "efforts": {
            "claude": ("xhigh", "medium", "low"),
            "codex": ("ultra", "medium", "low"),
        },
    },
    {
        "name": "flow_mapping_consumed",
        "yaml_block": "effort-tiers: {codex: {strong: ultra}}\n",
        "lint_clean": True,
        "efforts": {
            "claude": ("high", "medium", "low"),
            "codex": ("ultra", "medium", "low"),
        },
    },
    {
        "name": "nested_flow_fleet_mapping_consumed",
        "yaml_block": "effort-tiers:\n  codex: {strong: ultra}\n",
        "lint_clean": True,
        "efforts": {
            "claude": ("high", "medium", "low"),
            "codex": ("ultra", "medium", "low"),
        },
    },
    {
        "name": "duplicate_codex_mapping_uses_yq_last_value",
        "yaml_block": """effort-tiers:
  codex:
    strong: xhigh
  codex: {strong: ultra}
""",
        "lint_clean": True,
        "efforts": {
            "claude": ("high", "medium", "low"),
            "codex": ("ultra", "medium", "low"),
        },
    },
    {
        "name": "duplicate_claude_mapping_uses_yq_last_value",
        "yaml_block": """effort-tiers:
  claude:
    strong: xhigh
  claude: {strong: max}
""",
        "lint_clean": True,
        "efforts": {
            "claude": ("max", "medium", "low"),
            "codex": ("high", "medium", "low"),
        },
    },
    {
        "name": "scalar_top_level_rejected",
        "yaml_block": "effort-tiers: ultra\n",
        "lint_clean": False,
        "efforts": {
            "claude": ("high", "medium", "low"),
            "codex": ("high", "medium", "low"),
        },
        "resolver_warns": True,
    },
    {
        "name": "list_top_level_rejected",
        "yaml_block": """effort-tiers:
  - ultra
""",
        "lint_clean": False,
        "efforts": {
            "claude": ("high", "medium", "low"),
            "codex": ("high", "medium", "low"),
        },
        "resolver_warns": True,
    },
    {
        "name": "null_top_level_rejected",
        "yaml_block": "effort-tiers: null\n",
        "lint_clean": False,
        "efforts": {
            "claude": ("high", "medium", "low"),
            "codex": ("high", "medium", "low"),
        },
        "resolver_warns": True,
    },
]
