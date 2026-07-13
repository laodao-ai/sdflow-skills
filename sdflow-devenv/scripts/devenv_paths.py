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

    raise PathEscape 于：空路径 / 含空字节 / 折叠后指向仓根自身（"." "./" 等）/
                        绝对路径 / 含 `..` / symlink 祖先或自身 /
                        无法判定 symlink（OS 层拒绝，fail-closed）/
                        最终 realpath 落在 root 之外

    非法输入【一律】raise PathEscape——调用方只需 except PathEscape 即可接住
    全部拒绝分支，不会有原始 OSError/ValueError 漏出。
    """
    root = Path(root).resolve()

    if not rel or not str(rel).strip():
        raise PathEscape("空路径")

    # 空字节没有任何合法用途——在入口就显式拒绝，归一为 PathEscape，
    # 而不是让它一路走到 os.lstat/os.readlink 触发未捕获的 ValueError
    # （embedded null byte）逃出契约（调用方只 except PathEscape）。
    if "\x00" in str(rel):
        raise PathEscape(f"拒绝含空字节的路径: {rel!r}")

    p = PurePosixPath(str(rel).replace(os.sep, "/"))

    # p.parts 为空 == 折叠后指向仓根自身/空路径（覆盖 "."、"./"、"././." 等
    # 全部退化形态——PurePosixPath 会自动折叠掉这些，无需逐个枚举字符串）。
    # 注意：`.` 作为【中间】part（如 "a/./b"）会被折叠掉，是安全的，不受影响；
    # 这里拒绝的只是折叠后【整体为空】的情况。
    if not p.parts:
        raise PathEscape(f"拒绝指向仓根自身/空路径: {rel!r}")
    if p.is_absolute():
        raise PathEscape(f"拒绝绝对路径: {rel}")
    if any(part == ".." for part in p.parts):
        raise PathEscape(f"拒绝含 `..` 的路径: {rel}")

    # 逐级 lstat：任一层（含目标自身）是 symlink 即拒绝。
    # 注意用 lstat 不用 exists —— 不存在的路径是合法的（写新文件），
    # 但【存在且是 symlink】就必须拒。
    # fail-closed：is_symlink() 底层 os.lstat 遇到异常路径（如空字节、
    # 过长路径等 OS 层拒绝）也归一为 PathEscape——查不了就不放行，
    # 不让原始 OSError/ValueError 逃出契约。
    cur = root
    for part in p.parts:
        cur = cur / part
        try:
            is_link = cur.is_symlink()
        except (OSError, ValueError) as exc:
            raise PathEscape(f"无法校验路径（判定 symlink 失败）: {cur} ({exc})")
        if is_link:
            raise PathEscape(f"拒绝 symlink（自身或祖先）: {cur.relative_to(root)}")

    # 最终 realpath 必须仍在 root 内（防 symlink 之外的逃逸路径，如挂载点）
    final = Path(os.path.realpath(str(cur)))
    try:
        final.relative_to(root)
    except ValueError:
        raise PathEscape(f"路径解析后落在消费仓之外: {rel} -> {final}")

    return cur.resolve()
