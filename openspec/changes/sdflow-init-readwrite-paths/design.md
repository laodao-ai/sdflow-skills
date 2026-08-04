## Overview

三处修复均在 `sdflow-init/scripts/init.py`，互不依赖，可独立实现与测试。

## Decisions

见 [decision-memo.md](decision-memo.md)。

## T64 · `_atomic_write_settings()` mkstemp 唯一名

### 现状

L947-960：`tmp = settings + ".tmp"` 固定名。持锁时安全（串行化），但 Windows / fcntl 失败时降级无锁，固定名 + 无锁 = 并发 tmp 互相覆盖 → JSON 撕裂。

### 修法

对齐同文件 `_atomic_write()` L551 的做法：

```python
fd, tmp = tempfile.mkstemp(prefix=".settings-", dir=os.path.dirname(settings))
try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, settings)
except OSError:
    # 清理残留 tmp（mkstemp 已创建文件）
    try:
        os.unlink(tmp)
    except OSError:
        pass
    return False
return True
```

- `mkstemp` 返回 fd + 唯一路径，`os.fdopen` 包装后写入
- 失败时 `os.unlink(tmp)` 清理残留（固定名方案靠下次覆盖，唯一名方案须显式清理）
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
        with open(cfg_path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                if line and not line[0].isspace() and not line.startswith("#"):
                    m = re.match(r"([A-Za-z_][\w-]*):", line)
                    if m:
                        key = m.group(1)
                        seen.setdefault(key, []).append(lineno)
    except OSError:
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
codex_home = os.path.expanduser("~/.codex")
if os.path.isdir(codex_home):
    lines.append("  ⚠ hook 仅 Claude 侧生效，Codex 会话无 branch-guard")
```

- 仅当 `~/.codex/` 存在时告警（不存在 = 未装 Codex，无需提醒）
- 不尝试安装到 Codex 侧（无等价机制）
- 告警文本出现在 `sdflow-init init/update` 输出的 hook 安装汇总里

## Compliance

三处修复均在既有函数内部，不改公开接口、不改文件格式、不引入新依赖。`_atomic_write_settings` 的调用方（`_deregister_hook_in_settings`、`_register_hook_in_settings_locked`）无需修改——返回值语义不变（True/False）。
