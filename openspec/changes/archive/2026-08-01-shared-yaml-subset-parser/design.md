# Design · shared-yaml-subset-parser

## Overview

```
现状（7 份各自漂移的手搓解析器）          目标态（统一 yq subprocess 调用）
┌───────────┐ ┌───────────┐             ┌────────────────────────────┐
│ init.py   │ │ship_gate  │             │       yq (v4.53+)         │
│ 175 行    │ │  106 行   │             │   单一二进制，全局安装      │
│ YAML 解析 │ │ FM 解析   │             └────────────┬───────────────┘
├───────────┤ ├───────────┤                          │ subprocess
│impl_route │ │anchor_lint│    ──────▶   ┌───────────┴───────────────┐
│  72 行    │ │  23×2 行  │              │  各脚本 _yq() 薄封装      │
├───────────┤ ├───────────┤              │  ~10 行/脚本              │
│roadmap_wb │ │sad_schema │              │  json.loads(stdout)       │
│  35 行    │ │  45 行    │              └───────────────────────────┘
└───────────┘ └───────────┘
   ~456 行 手搓                            0 行 手搓
```

## 1. yq 调用封装

每个消费脚本内放一个 `_yq()` 薄封装（不跨脚本共享——各脚本零依赖不变量不允许互 import，
而 ~10 行的封装也不值得共享）：

```python
import subprocess, json, shutil, sys, os

_yq_bin = None  # 进程内缓存

def _yq(expression, file, *, front_matter=False, in_place=False, default=None):
    global _yq_bin
    if _yq_bin is None:
        yq = shutil.which("yq")
        if not yq:
            print(f"ERROR: yq 未安装。安装方式：\n"
                  f"  macOS:   brew install yq\n"
                  f"  Windows: winget install --id MikeFarah.yq\n"
                  f"  Linux:   snap install yq\n", file=sys.stderr)
            sys.exit(1)
        # 身份校验：确认是 mikefarah/yq [spec-review-amendment F6]
        vr = subprocess.run([yq, "--version"], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
        if "mikefarah" not in vr.stdout:
            print(f"ERROR: 检测到的 yq 不是 mikefarah/yq（可能是 kislyuk/yq）。\n"
                  f"  请卸载后安装正确版本：\n"
                  f"  macOS:   brew install yq\n"
                  f"  Windows: winget install --id MikeFarah.yq\n"
                  f"  Linux:   snap install yq\n", file=sys.stderr)
            sys.exit(1)
        _yq_bin = yq
    cmd = [_yq_bin]
    if front_matter:
        cmd += [f"--front-matter={'process' if in_place else 'extract'}"]
    if in_place:
        cmd.append("-i")
    else:
        cmd += ["-o", "json"]
    cmd += [expression, str(file)]
    # 写操作通过环境变量传值 [spec-review-amendment F7]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")  # [spec-review-amendment F10]
    if r.returncode != 0:
        # exit≠0 = 解析失败，必须 raise，不吞 [spec-review-amendment F2]
        raise RuntimeError(f"yq failed on {file}: {r.stderr.strip()}")
    if in_place:
        return None
    raw = r.stdout.strip()
    if not raw or raw == "null":
        return default
    parsed = json.loads(raw)
    # frontmatter 模式下校验顶层类型 [spec-review-amendment F4]
    if front_matter and not in_place and default is not None:
        if not isinstance(parsed, dict):
            return default
    return parsed
```

### 写操作值传递 [spec-review-amendment F7]

写操作 MUST NOT 用 f-string 插值。改用环境变量：

```python
# 旧（有注入风险）：_yq(f'.schema = "{new_schema}"', config_path, in_place=True)
# 新（安全）：
os.environ["_YQ_VAL"] = new_schema
_yq('.schema = strenv(_YQ_VAL)', config_path, in_place=True)
```

### 读操作示例

```python
# config.yaml 顶层键
schema = _yq(".schema", config_path, default="spec-driven")
pipeline = _yq('."impl-pipeline"', config_path, default="superpowers")

# config.yaml 嵌套
tiers = _yq(".model-tiers", config_path, default={})
# tiers = {"claude": {"strong": "opus", ...}} 或 {} 或 {"strong": "opus"} (扁平旧格式)

# Markdown frontmatter
gate = _yq(".ship-gate", report_path, front_matter=True, default={})
# gate = {"design_approved": True, "reviewed_sha": "abc123"}
```

### 写操作示例 [spec-review-amendment F7]

```python
import os

# config.yaml 写入（保留注释，通过环境变量传值避免注入）
os.environ["_YQ_VAL"] = new_schema
_yq('.schema = strenv(_YQ_VAL)', config_path, in_place=True)

# Markdown frontmatter 写入（保留正文，布尔值无需环境变量）
_yq('.ship-gate.design_approved = true', report_path, front_matter=True, in_place=True)
```

## 2. 各脚本改动清单

| 脚本 | 删除 | 替换为 | 特殊处理 |
|---|---|---|---|
| `init.py` | `_strip_inline_comment` / `_find_top_level_block` / `_second_level_keys` / `_schema_from_config` / `_set_schema_key` / `_marker_schema` / `_parse_model_tiers_block` / `_valid_model_id` / `_validate_schema_authority` / `lint_config` 的 YAML 部分 | `_yq()` 调用 | `_parse_model_tiers_block` 的**业务逻辑**（fleet_ctx 状态机、越域键检测、畸形头检测）从 YAML 解析中分离：yq 读到 JSON dict 后，Python 侧做键集验证 |
| `ship_gate.py` | `parse_ship_gate_frontmatter` 的 YAML 解析核心（`---` 定位 / 缩进扫描 / 注释剥离），**但保留 duplicate-key/tab-indent 原始文本预扫描** | `_yq(".ship-gate", path, front_matter=True)` | **业务逻辑保留**：`FIELD_VALIDATORS` 校验、`_coerce_ship_gate_value`、`bad-type` 等。**duplicate-key/tab-indent 预扫描保留在 yq 读取之前**（R11）——yq 对重复键静默取最后值，dict 不保留重复信息，故此检测不可委托给 yq [spec-review-amendment F1·Q1] |
| `impl_route.py` | `_extract_scalar` / `read_config_pipeline` 的 YAML 扫描 / `read_plan_marker` 的 frontmatter 解析 | `_yq()` 调用 | `damaged` 标量检测（未闭合引号等）——yq 会直接报错（非零退出码），映射为 `RouteStop` |
| `anchor_lint.py` (×2) | `read_metrics_enabled` | `_yq(".metrics.enabled", config_path, default=False)` | 最简单的替换 |
| `roadmap_writeback_draft.py` | `read_verify_state` 的 frontmatter 解析 | `_yq(".ship-gate.verify", path, front_matter=True)` | 保留 `PASS`/`FAIL` 枚举校验 |
| `sad_schema.py` | `frontmatter_end` / `parse_frontmatter` | `_yq(".", path, front_matter=True)` | 保留 `TOP_KEYS` / `FACT_KEYS` / `FACT_VALUES` 白名单校验（yq 读出 dict 后验证） |

### `_parse_model_tiers_block` 分离设计

现状（~85 行，YAML 解析与业务逻辑混合）：

```
扫描行 → 判缩进 → 识别 fleet 头 → 提取 tier 值 → 检测越域键 → 检测畸形头
         ~~~~~~~~YAML 层~~~~~~~~   ~~~~~~~~~~~~业务逻辑层~~~~~~~~~~~~
```

目标态（YAML 层 → yq，业务逻辑层 → Python dict 验证）：

```python
raw = _yq(".model-tiers", config_path, default=None)
if raw is None:
    return {}, set(), []  # 段不存在或被注释

entries, bad_subkeys, bad_headers = {}, set(), []
if isinstance(raw, dict):
    for k, v in raw.items():
        if k in TIER_FLEET_KEYS:  # claude, codex
            if not isinstance(v, dict):
                bad_headers.append(f"{k}: {v}")  # fleet 名当标量误用
                continue
            for tk, tv in v.items():
                if tk in TIER_ALLOWED_SUBKEYS:
                    entries[f"{k}.{tk}"] = str(tv)
                else:
                    bad_subkeys.add(f"{k}.{tk}")
        elif k in TIER_ALLOWED_SUBKEYS:  # 扁平旧格式
            entries[f"flat.{k}"] = str(v)
        else:
            bad_subkeys.add(k)
return entries, bad_subkeys, bad_headers
```

## 3. 依赖预检系统

### `setup.sh` 新增 `check_dependencies()`

```bash
check_dependencies() {
  echo "运行依赖预检："
  local missing=()

  # python3 >= 3.7（已有逻辑，移入此函数统一报告）
  if [ -n "$_py" ]; then
    echo "  ✓ python3 ($("$_py" --version 2>&1))"
  else
    echo "  ✗ python3 >= 3.7 — 未找到"
    missing+=("python3")
  fi

  # git
  if command -v git >/dev/null 2>&1; then
    echo "  ✓ git ($(git --version 2>&1 | head -1))"
  else
    echo "  ✗ git — 未找到"
    missing+=("git")
  fi

  # yq (mikefarah/yq)
  if command -v yq >/dev/null 2>&1; then
    local yqv
    yqv="$(yq --version 2>&1 | head -1)"
    if echo "$yqv" | grep -q "mikefarah"; then
      echo "  ✓ yq ($yqv)"
    else
      echo "  ⚠ yq 已安装但不是 mikefarah/yq（可能是 kislyuk/yq）——请卸载后安装正确版本"
      missing+=("yq(mikefarah)")
    fi
  else
    echo "  ✗ yq — 未找到"
    missing+=("yq")
  fi

  # openspec（可选——setup.sh 不强依赖，但提示有助于用户）
  if command -v openspec >/dev/null 2>&1; then
    echo "  ✓ openspec ($(openspec --version 2>&1 | head -1))"
  else
    echo "  · openspec — 未找到（部分 skill 需要：npm i -g @fission-ai/openspec）"
  fi

  # pytest（开发可选）
  if "$_py" -m pytest --version >/dev/null 2>&1; then
    echo "  ✓ pytest ($("$_py" -m pytest --version 2>&1 | head -1))"
  else
    echo "  · pytest — 未找到（跑测试需要：pip install pytest）"
  fi

  if [ ${#missing[@]} -gt 0 ]; then
    echo ""
    echo "  缺少必要依赖：${missing[*]}"
    echo "  yq 安装："
    echo "    macOS:   brew install yq"
    echo "    Windows: winget install --id MikeFarah.yq"
    echo "    Linux:   snap install yq"
  fi
}
```

调用点：`install_sdflow` 之后、门禁检查之前，输出进汇总。**不中止 setup.sh**——降级汇报，与既有
`skipped[]` 范式一致。

### `sdflow-init` 路径

`init.py` 新增 `_check_yq()` 函数：`shutil.which("yq")` + 版本检测（`--version` 含 `mikefarah`）。
在 `lint_config`（读 config.yaml 的入口）前调用：不可用 ⇒ 返回带安装指引的 lint reason（不中止
init 本身——init 的 config 读取改为 yq 后此检测变成前置门）。

## 4. 错误处理策略

| 场景 | yq 行为 | 脚本处理 |
|---|---|---|
| 键不存在 | stdout = `null`，exit 0 | `default` 参数返回 |
| 文件不存在 | exit 1，stderr 报错 | raise / 返回 error |
| YAML 语法错误 | exit 1，stderr 报 parse error | raise（含 yq 原始错误信息——比手搓更好的诊断） |
| 无 frontmatter | exit 0，stdout = `null` | `default` 参数返回 |
| frontmatter 未闭合 | exit 1 | raise（yq 自己报出位置） |
| yq 未安装 | `shutil.which` 返回 None | fail-loud + 安装指引 |

## Compliance

- 零依赖不变量：yq 是外部二进制（同 git），subprocess 调用不违反 `MUST NOT import yaml`
- 基准 5（无界不手搓）：yq 是该基准的正解实例——让工具自己回答自己的语法
- GC-2 边界锁：不受影响——`_yq()` 封装各脚本内联，不跨脚本 import

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)。
