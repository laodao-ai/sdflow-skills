## Overview

三处修复均在 `sdflow-init/scripts/init.py`，互不依赖，可独立实现与测试。

## Decisions

见 [decision-memo.md](decision-memo.md)。

## T64 · `_atomic_write_settings()` mkstemp 唯一名

### 现状

L947-960：`tmp = settings + ".tmp"` 固定名。持锁时安全（串行化），但 Windows / fcntl 失败时降级无锁，固定名 + 无锁 = 并发 tmp 互相覆盖 → JSON 撕裂。

### 修法

对齐同文件 `_atomic_write()` L551 的做法，**但保持本函数的 fail-safe 契约**（OSError → 返回 False，绝不中止 retire_hooks 循环 / setup.sh）：

```python
# [spec-review-amendment] CR-1: mkstemp 必须在 try 内——本函数契约是 fail-open（返回 False），
# 与 _atomic_write 的 fail-closed（finally 清理后裸抛）不同。mkstemp 底层是 open(O_CREAT|O_EXCL)，
# 权限拒绝/只读/满盘时抛 OSError，放在 try 外会让异常逃逸击穿 FB-3 契约。
try:
    fd, tmp = tempfile.mkstemp(prefix=".settings-", dir=os.path.dirname(settings))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, settings)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
except OSError:
    return False
return True
```

- `mkstemp` 在外层 `try` 内——任何 OSError（含 mkstemp 自身失败）都被捕获返回 False
- 内层 `try/except BaseException` 确保 mkstemp 成功后的残留 tmp 被清理
- `flush()` + `os.fsync()` 对齐 `_atomic_write()` 风格 [spec-review-amendment] CR-7
- `os.replace` 语义不变（POSIX + Windows 同卷原子）

## T149 · `lint_config()` 顶层重复键检测

### 现状

L723-784：通过 `_yq(".", cfg_path)` 解析 config.yaml，yq 对重复键 last-wins 静默合并，`lint_config()` 拿到的 dict 已去重，无法检测。

### 修法

在 `_yq` 调用之前，读 config.yaml 原文做行级顶层键扫描：

```python
def _detect_duplicate_top_keys(cfg_path):
    """行级扫描 YAML 顶层键（缩进=0 的 `key:` 行），返回重复键列表。"""
    seen = {}
    try:
        # [spec-review-amendment] CR-3: utf-8-sig 处理 BOM，对齐同文件 _schema_from_config()
        # [spec-review-amendment] CR-2: 捕获 UnicodeDecodeError（非 OSError 子类）
        with open(cfg_path, encoding="utf-8-sig") as f:
            for lineno, line in enumerate(f, 1):
                if line and not line[0].isspace() and not line.startswith("#"):
                    m = re.match(r"([A-Za-z_][\w-]*):", line)
                    if m:
                        key = m.group(1)
                        seen.setdefault(key, []).append(lineno)
    except (OSError, UnicodeDecodeError):
        return []
    return [f"{k}（行 {','.join(map(str, lns))}）" for k, lns in seen.items() if len(lns) > 1]
```

在 `lint_config()` 的 `_yq` 调用之前插入：

```python
dups = _detect_duplicate_top_keys(cfg_path)
if dups:
    reasons.append(f"config.yaml 顶层键重复: {'; '.join(dups)}（yq 会 last-wins 静默合并）")
```

**只扫顶层**（indent=0）：嵌套键重复概率极低、检测需追踪缩进层级，按通则④不做。

## T6 · `ensure_global_hooks()` Codex 降级告警

### 现状

L891-893：逐个调 `ensure_global_hook(spec)` 装到 `~/.claude/`。Codex 无 `hooks/` 机制，静默不生效。

### 修法

在 `ensure_global_hooks()` 末尾追加检测：

```python
# [spec-review-amendment] CR-5: 弱化文案——~/.codex/ 存在仅表示曾安装过，不等于当前活跃会话
codex_home = os.path.expanduser("~/.codex")
if os.path.isdir(codex_home):
    lines.append("  ⚠ 检测到 Codex 环境，如使用 Codex 会话请注意：hook 仅 Claude 侧生效")
```

- 仅当 `~/.codex/` 存在时告警（不存在 = 未装 Codex，无需提醒）
- 已知局限：`~/.codex/` 存在 = 曾安装过（`setup.sh` 会 `mkdir -p ~/.codex/skills`），不等于当前活跃会话；文案用「检测到 Codex 环境，如使用请注意」降低确定性语气，避免狼来了效应
- 不尝试安装到 Codex 侧（无等价机制）
- 告警文本出现在 `sdflow-init init/update` 输出的 hook 安装汇总里

## Compliance

三处修复均在既有函数内部，不改公开接口、不改文件格式、不引入新依赖。`_atomic_write_settings` 的调用方（`_deregister_hook_in_settings`、`_register_hook_in_settings_locked`）无需修改——返回值语义不变（True/False）。
