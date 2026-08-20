"""检查 Python 入口脚本的标准流编码保护前导。"""
import ast
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass


TARGET_GLOBS = (
    "hack/**/*.py",
    "sdflow-*/scripts/**/*.py",
    "sdflow-init/assets/hack/**/*.py",
    "sdflow-init/assets/hooks/**/*.py",
    "sdflow-init/assets/workflow/tools/**/*.py",
)
REPO = Path(__file__).resolve().parent.parent


def _stream_name(node):
    if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
            and node.value.id == "sys" and node.attr in {"stdout", "stderr"}):
        return node.attr
    return None


def _reconfigure_calls(tree):
    """Yield a reconfigure call and the streams it directly protects."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "reconfigure":
            continue
        stream = _stream_name(node.func.value)
        yield node, {stream} if stream else set()

    for loop in ast.walk(tree):
        if not isinstance(loop, ast.For) or not isinstance(loop.target, ast.Name):
            continue
        streams = {_stream_name(value) for value in getattr(loop.iter, "elts", ())}
        streams.discard(None)
        if not streams:
            continue
        for node in ast.walk(loop):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "reconfigure"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == loop.target.id):
                yield node, streams


def missing_contracts(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    protected = set()
    has_replace = False
    for call, streams in _reconfigure_calls(tree):
        protected.update(streams)
        has_replace |= any(
            keyword.arg == "errors" and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == "replace"
            for keyword in call.keywords
        )
    missing = []
    if "stdout" not in protected:
        missing.append("stdout reconfigure")
    if "stderr" not in protected:
        missing.append("stderr reconfigure")
    if not has_replace:
        missing.append('errors="replace"')
    return missing


def target_files(root=REPO):
    root = Path(root)
    paths = set()
    for pattern in TARGET_GLOBS:
        paths.update(root.glob(pattern))
    for path in sorted(paths):
        relative = path.relative_to(root).as_posix()
        if "/tests/" in f"/{relative}/":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if any(
            isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__"
            and any(isinstance(value, ast.Constant) and value.value == "__main__"
                    for value in node.test.comparators)
            for node in ast.walk(tree)
        ):
            yield path


def main(root=REPO):
    root = Path(root)
    checked = [(path.relative_to(root).as_posix(), missing_contracts(path))
               for path in target_files(root)]
    # [T295] 空扫描面 MUST 红：glob 漂移（目录改名/迁移）会让某个子面静默变空，
    # 「0 个被检查」与「全部通过」若同样打 ✅ rc=0 则不可区分。只判 0、不写死下限——
    # 下限会随归档删文件自然下走而过期（test_subprocess_encoding_contract 已记此坑）。
    if not checked:
        print("[encoding-hygiene] FAIL: 扫描面为空——TARGET_GLOBS 未命中任何入口脚本"
              "（glob 漂移或 root 指错）", file=sys.stderr)
        return 1
    failures = [(path, missing) for path, missing in checked if missing]
    if not failures:
        print(f"[encoding-hygiene] ✅ {len(checked)} 个入口脚本均满足编码前导契约")
        return 0
    print("[encoding-hygiene] FAIL: 下列入口脚本缺少编码前导契约", file=sys.stderr)
    for path, missing in failures:
        print(f"  - {path}: 缺 {'、'.join(missing)}", file=sys.stderr)
    print("   修：按 CLAUDE.md「修改本仓库的注意」中的 4 行 reconfigure 前导模板补齐",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("[encoding-hygiene] FAIL: 本检查器只支持裸调用，不支持 --apply 或其它参数",
              file=sys.stderr)
        sys.exit(2)
    sys.exit(main())
