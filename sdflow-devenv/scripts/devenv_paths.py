"""路径 containment —— 所有模型提供的路径的唯一入口。

设计约束（spec: R-PATH）：
  source.file / smoke / fixtures[] / 外部配置文件 / touched-files 清单
  全是【模型填的自由文本】。任何读/写/删/digest 之前 MUST 经此校验。

【为什么要逐级查 symlink 祖先】：前一版只拒绝「目标文件本身是 symlink」，
于是 `link/loot.txt`（父目录是指向仓外的 symlink）畅通无阻。
"""
import os
from pathlib import Path, PurePosixPath


class PathEscape(Exception):
    """路径逃逸出消费仓边界。"""


def contain(root, rel):
    """校验 rel 是 root 之内的安全相对路径，返回 resolved 绝对路径。

    root: Path —— 消费仓根（调用方保证它已 resolve）
    rel:  str  —— 模型提供的相对路径

    raise PathEscape 于：空路径 / 绝对路径 / 含 `..` / symlink 祖先或自身 /
                        最终 realpath 落在 root 之外
    """
    root = Path(root).resolve()

    if not rel or not str(rel).strip():
        raise PathEscape("空路径")

    p = PurePosixPath(str(rel).replace(os.sep, "/"))

    if p.is_absolute():
        raise PathEscape(f"拒绝绝对路径: {rel}")
    if any(part == ".." for part in p.parts):
        raise PathEscape(f"拒绝含 `..` 的路径: {rel}")

    # 逐级 lstat：任一层（含目标自身）是 symlink 即拒绝。
    # 注意用 lstat 不用 exists —— 不存在的路径是合法的（写新文件），
    # 但【存在且是 symlink】就必须拒。
    cur = root
    for part in p.parts:
        cur = cur / part
        if cur.is_symlink():
            raise PathEscape(f"拒绝 symlink（自身或祖先）: {cur.relative_to(root)}")

    # 最终 realpath 必须仍在 root 内（防 symlink 之外的逃逸路径，如挂载点）
    final = Path(os.path.realpath(str(cur)))
    try:
        final.relative_to(root)
    except ValueError:
        raise PathEscape(f"路径解析后落在消费仓之外: {rel} -> {final}")

    return cur.resolve()
