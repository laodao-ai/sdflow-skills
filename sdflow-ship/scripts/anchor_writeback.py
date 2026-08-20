#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""anchor_writeback.py — sdflow-ship 权威写锚脚本（`ship_gate.py` 的 sibling，只写不判）。

〔sweep-pool-debt D3/D4〕producer 写锚与 `ship_gate.py` 验锚跑**同一份指纹函数**（`import
ship_gate` 复用 `ls_tree_map` / `design_pathspecs` / `change_base` / `fingerprint_entries`），
物理同源杜绝两端口径漂移。本脚本把报告 frontmatter 的 `reviewed_sha`（监视域 manifest 的
sha256，64-hex）+ `reviewed_manifest`（manifest 规范字节流的单行 base64）与（可选的）评审
结论字段（`--set field=value`，可重复）在**同一次原子写入**中落盘——MUST NOT 先手写结论
字段、再补跑本脚本，中间态会被 `ship_gate.py` 判「结论已落但锚缺」而 fail-closed。

**判官只读语义不破**：`ship_gate.py` 保持零副作用；一切写操作收敛在本文件。

**监视域枚举失败 / 为空 → fail-loud 拒写**（不落一个空集摘要——空集摘要会与"监视域从无到
有"的变化产生假等值，且掩盖枚举参数本身写错的可能）。

**脏树守卫**〔spec-review-amendment R2〕：监视集路径存在未提交改动
（`git status --porcelain -- <监视集>` 非空）时 fail-loud 拒写——锚取自 HEAD（committed
blob），脏树写锚 = 锚绑定不含在场未提交修订的盘面，结论落盘后首次判定即失鲜自锁（原「二次
修订 MUST 先单独落盘」的书面纪律由此收进机械层）。

**逃生口 `--allow-dirty`**：跳过脏树守卫。仅供**显式越权留痕**场景使用（如紧急人工重锚且
确认脏树内容与被批准盘面无关）——git 提交历史仍会记录这次写入，可审计（adr/0008 防御纵深
立场）。默认路径 MUST NOT 使用本逃生口；本条即「已知不覆盖」登记（越权本身不被机械拦截，
拦截的是"不显式声明就越权"）。

用法：
    python3 anchor_writeback.py --root <repo> --change <name> --report <文件名> \\
        --domain {design,code} [--set field=value ...] [--allow-dirty]

    --report 为报告文件名，相对 `openspec/changes/<change>/`（如 `spec-review-report.md`）。
    --domain design ⇒ 监视集 = change 目录内 proposal.md/design.md/specs/（tasks.md 不在内，
        与 `ship_gate.design_pathspecs` 同口径）；--domain code ⇒ 监视集 = 仓库顶层条目
        （排除 openspec），与 `ship_gate.is_stale` 的 code 分支同口径。
    --set 可重复，如 `--set design_approved=true`、`--set verify=PASS --set code_review=pass`。
        字段须是 `ship_gate.FIELD_ENUMS` 已知的结论字段之一；未传的既有字段原样保留
        （只增/改传入的字段，不清空报告里其它既有结论）。
"""
import argparse
import base64
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ship_gate as sg  # noqa: E402  （sibling import，复用同一指纹实现，物理同源）


def _fail(msg):
    print(f"[anchor_writeback] {msg}", file=sys.stderr)
    sys.exit(1)


def _split_frontmatter_block(text):
    """`(has_block, body_text)`——只识别文件首行 `---`（去 BOM 后）起到下一行 `---` 止的
    唯一首块，与 `ship_gate.parse_ship_gate_frontmatter` 的「D2 只认文件首块」同一识别口径
    （首块无闭合 `---` ⇒ 不成立，整份文本视为正文）。仅做**块边界切分**，不做取值——取值仍
    交给 `ship_gate.parse_ship_gate_frontmatter` 做（单一源，不在此手搓第二个解析器）。
    """
    t = text[1:] if text.startswith("﻿") else text
    lines = t.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return False, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return False, text
    return True, "".join(lines[end + 1:])


def _coerce_set_value(field, raw):
    """把 `--set field=value` 的原始字符串按 `ship_gate.FIELD_ENUMS` 校验/转换为可渲染值。
    未知字段 / 越域值 → fail-loud（脚本不代 producer 决定该写什么结论，只保证格式合法）。
    """
    if field not in sg.FIELD_ENUMS:
        _fail(f"--set 的字段 {field!r} 不是已知结论字段"
              f"（须是 {sorted(sg.FIELD_ENUMS)} 之一）")
    if field == "design_approved":
        if raw.lower() in ("true", "false"):
            return raw.lower() == "true"
        _fail(f"--set design_approved 的值 {raw!r} 非法（须 true/false）")
    allowed = sg.FIELD_ENUMS[field]
    if raw not in allowed:
        _fail(f"--set {field} 的值 {raw!r} 非法（须是 {allowed} 之一）")
    return raw


def _render_value(field, value):
    if field == "design_approved":
        return "true" if value else "false"
    return str(value)


# 结论字段的展示序（可读性——与三个 producer 既有模板逐字对齐：结论字段在前，锚在后）。
_FIELD_ORDER = ("design_approved", "verify", "code_review")


def _compute_domain_entries(root, change, domain):
    """监视域枚举，返回 `(entries, dirty_pathspecs)`：
      - dirty_pathspecs：供脏树守卫用的**正向** pathspec 列表（design 域直接是监视集本身）；
        code 域改用整仓 `git status --porcelain` 全量扫描后在 Python 侧按条目名排除
        `openspec`（同 `ship_gate.is_stale` code 分支的既有口径：MUST NOT 用负向 pathspec，
        继承外部可控 `GIT_ICASE_PATHSPECS`，已实测证伪；见 ship_gate.py 头注释）。
    枚举失败（`GateIndeterminate`）由调用方捕获、映射为 fail-loud 拒写。
    """
    if domain == "design":
        base = sg.change_base(change)
        specs = sg.design_pathspecs(base)
        entries = sg.ls_tree_map(root, "HEAD", specs)
        return entries, specs
    # domain == "code"
    top = sg.ls_tree_map(root, "HEAD", recursive=False)
    entries = {p: v for p, v in top.items() if p != b"openspec"}
    return entries, None   # None ⇒ 调用方走「整仓扫描 + Python 侧排除 openspec」分支


def _git_status_porcelain_raw(root, pathspecs):
    """`git status --porcelain` 原样输出（**不** `.strip()`）——`ship_gate.run_git` 会
    `.strip()` 整段输出，porcelain 每行开头的状态码可能是空格（如 ` M path`），
    整段 strip 会啃掉首行状态码的首字符、致后续 `line[3:]` 切分错位。本函数专供
    脏树守卫使用，原样保留每行前导字符。
    """
    cmd = ["git", "-C", str(root), *sg._GIT_HARDEN, "status", "--porcelain"]
    if pathspecs:
        cmd += ["--", *pathspecs]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                        errors="replace", env=sg._git_env())
    return r.stdout if r.returncode == 0 else ""


def _dirty_paths(root, domain, dirty_pathspecs):
    """返回监视域内存在未提交改动的路径清单（用于脏树守卫判定与诊断展示）。"""
    if domain == "design":
        out = _git_status_porcelain_raw(root, dirty_pathspecs)
    else:
        out = _git_status_porcelain_raw(root, ())
    dirty = []
    for line in out.splitlines():
        if not line:
            continue
        # `git status --porcelain` 每行前两字符是状态码（可含空格）、随后一个空格、再是路径
        # （rename 形态为 `old -> new`，此处只需判断"是否落在 openspec 之外"，取整行足够）。
        path = line[3:] if len(line) > 3 else line
        if domain == "code" and (path == "openspec" or path.startswith("openspec/")):
            continue
        dirty.append(path)
    return dirty


def main(argv=None):
    p = argparse.ArgumentParser(
        description="sdflow-ship 权威写锚脚本：原子写入内容锚（+ 可选结论字段）")
    p.add_argument("--root", default=None)
    p.add_argument("--change", required=True)
    p.add_argument("--report", required=True,
                    help="报告文件名，相对 openspec/changes/<change>/（如 spec-review-report.md）")
    p.add_argument("--domain", required=True, choices=("design", "code"))
    p.add_argument("--set", dest="set_fields", action="append", default=[],
                    metavar="field=value", help="同批写入的结论字段，可重复")
    p.add_argument("--allow-dirty", action="store_true",
                    help="显式越权：跳过监视集脏树守卫（越权留痕，见本文件头注释）")
    a = p.parse_args(argv)

    root = Path(a.root) if a.root else Path(
        sg.run_git(Path.cwd(), "rev-parse", "--show-toplevel") or Path.cwd())

    if not sg.run_git(root, "rev-parse", "--git-dir"):
        _fail("git 不可用或 --root 非 git 仓，无法写锚")

    report_path = root / "openspec" / "changes" / a.change / a.report
    if not report_path.is_file():
        _fail(f"报告不存在：{report_path}")

    # ── 监视域枚举（复用 ship_gate 单一源；失败/为空 → fail-loud）──
    try:
        entries, dirty_pathspecs = _compute_domain_entries(root, a.change, a.domain)
    except sg.GateIndeterminate as exc:
        _fail(f"监视域枚举失败：{exc.cause}")
    if not entries:
        _fail("监视域枚举结果为空集，拒绝写入空集摘要锚"
              "（空集锚会使后续「监视域从无到有」的变化被误判为等值，也可能是参数写错）")

    # ── 脏树守卫〔spec-review-amendment R2〕──
    if not a.allow_dirty:
        dirty = _dirty_paths(root, a.domain, dirty_pathspecs)
        if dirty:
            _fail("监视集路径存在未提交改动，拒绝写锚——锚取自 HEAD，脏树写锚会使结论落盘后"
                  "首次判定即失鲜自锁。先提交修订再写锚，或确认越权后加 --allow-dirty。"
                  "未提交路径：" + "；".join(dirty))

    # ── 计算内容指纹（与 ship_gate.is_stale 物理同源）──
    manifest_bytes, digest = sg.fingerprint_entries(entries)
    manifest_b64 = base64.b64encode(manifest_bytes).decode("ascii")

    # ── 读旧报告、切出首块 frontmatter（若有）与既有结论状态、合并 --set 覆盖 ──
    old_text = report_path.read_text(encoding="utf-8", errors="replace")
    _has_block, body = _split_frontmatter_block(old_text)
    old_state, err = sg.parse_ship_gate_frontmatter(old_text)
    if err is not None:
        field, cat = err
        _fail(f"报告现有 frontmatter 已损坏（字段={field} 类别={cat}），拒绝在坏块上合并写入"
              "——请先人工修复或清空该报告的 ship-gate frontmatter 后重跑")

    new_state = dict(old_state)
    new_state.pop("reviewed_sha", None)
    new_state.pop("reviewed_manifest", None)
    for kv in a.set_fields:
        if "=" not in kv:
            _fail(f"--set 参数格式错误（须 field=value）：{kv!r}")
        field, _, raw = kv.partition("=")
        field = field.strip()
        new_state[field] = _coerce_set_value(field, raw.strip())

    lines = ["---", "ship-gate:"]
    for field in _FIELD_ORDER:
        if field in new_state:
            lines.append(f"  {field}: {_render_value(field, new_state[field])}")
    # 未落在既定展示序里的已知字段（理论上不会发生，FIELD_ENUMS 已含三者）兜底追加
    for field, value in new_state.items():
        if field not in _FIELD_ORDER:
            lines.append(f"  {field}: {_render_value(field, value)}")
    lines.append(f"  reviewed_sha: {digest}")
    lines.append(f"  reviewed_manifest: {manifest_b64}")
    lines.append("---")
    new_text = "\n".join(lines) + "\n" + body

    # ── 原子替换写入 ──
    tmp_path = report_path.with_suffix(report_path.suffix + ".anchor-writeback.tmp")
    tmp_path.write_text(new_text, encoding="utf-8")
    tmp_path.replace(report_path)

    print(f"[anchor_writeback] 已写入 {report_path}"
          f"（domain={a.domain} reviewed_sha={digest} 监视域条目数={len(entries)}）")


if __name__ == "__main__":
    main()
