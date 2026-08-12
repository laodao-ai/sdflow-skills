"""Regression guard for repository-wide text subprocess encoding."""

import ast
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SUBPROCESS_APIS = {"run", "Popen", "check_output", "check_call"}


def _constant_keywords(call: ast.Call) -> dict[str, object]:
    return {
        keyword.arg: keyword.value.value
        for keyword in call.keywords
        if keyword.arg is not None and isinstance(keyword.value, ast.Constant)
    }


def _dict_assignments(tree: ast.AST) -> dict[str, dict[str, object]]:
    """Collect simple kwargs dictionaries and later literal subscript writes."""
    dictionaries: dict[str, dict[str, object]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            for target in targets:
                if isinstance(target, ast.Name) and isinstance(value, ast.Dict):
                    dictionaries[target.id] = {
                        key.value: item.value
                        for key, item in zip(value.keys, value.values)
                        if isinstance(key, ast.Constant) and isinstance(item, ast.Constant)
                    }
                elif (
                    isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Name)
                    and isinstance(target.slice, ast.Constant)
                    and isinstance(value, ast.Constant)
                ):
                    dictionaries.setdefault(target.value.id, {})[target.slice.value] = value.value
    return dictionaries


def _effective_keywords(call: ast.Call, dictionaries: dict[str, dict[str, object]]) -> dict[str, object]:
    values: dict[str, object] = {}
    for keyword in call.keywords:
        if keyword.arg is None and isinstance(keyword.value, ast.Name):
            values.update(dictionaries.get(keyword.value.id, {}))
        elif keyword.arg is not None and isinstance(keyword.value, ast.Constant):
            values[keyword.arg] = keyword.value.value
    return values


def _is_subprocess_call(call: ast.Call) -> bool:
    return (
        isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "subprocess"
        and call.func.attr in SUBPROCESS_APIS
    )


def _python_files(root: Path):
    """Yield authored Python, including tests but excluding generated/local trees."""
    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        if relative.parts[0] in {".git", ".worktrees", ".claude", "openspec"}:
            continue
        yield path


def _scan(paths, display_root: Path) -> tuple[int, list[str]]:
    sites = 0
    misses: list[str] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        dictionaries = _dict_assignments(tree)
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call) or not _is_subprocess_call(call):
                continue
            values = _effective_keywords(call, dictionaries)
            if values.get("text") is not True and values.get("universal_newlines") is not True:
                continue
            sites += 1
            missing = [
                name
                for name, expected in (("encoding", "utf-8"), ("errors", "replace"))
                if values.get(name) != expected
            ]
            if missing:
                misses.append(f"{path.relative_to(display_root)}:{call.lineno}: {', '.join(missing)}")
    return sites, misses


def test_text_mode_subprocesses_declare_utf8_and_replace():
    """Every authored text subprocess site is locale-independent and loss-tolerant."""
    sites, misses = _scan(_python_files(REPO), REPO)

    # 本行是**防塌陷哨兵**，不是清点契约：它只防「扫描器坏了 / 文件发现坏了 ⇒ sites≈0 ⇒
    # `not misses` 恒真通过」。真契约是下面那条。绝对值会随归档删文件自然下走
    # （曾 200+，simplify-workflow / refactor-roadmap-internalize-deps 归档后为 189），
    # 故取一个留足余量的下限；**MUST NOT 把它当「本仓应有多少个站点」来维护**——
    # 每次删文件都回来抬数字，只会让这条哨兵变成周期性假红。
    assert sites >= 120, f"repository scan unexpectedly missed most subprocess sites (got {sites})"
    assert not misses, "\n".join(misses)


def test_scanner_rejects_direct_dynamic_and_wrapper_outlets(tmp_path):
    samples = {
        "direct.py": "import subprocess\nsubprocess.run(['x'], text=True)\n",
        "dynamic.py": (
            "import subprocess\n"
            "kwargs = {'text': True}\n"
            "subprocess.check_output(['x'], **kwargs)\n"
        ),
        "wrapper.py": (
            "import subprocess\n"
            "def text_runner(argv):\n"
            "    return subprocess.Popen(argv, universal_newlines=True)\n"
        ),
    }
    paths = []
    for name, source in samples.items():
        path = tmp_path / name
        path.write_text(source, encoding="utf-8")
        paths.append(path)

    sites, misses = _scan(paths, tmp_path)

    assert sites == 3
    assert {miss.split(":", 1)[0] for miss in misses} == set(samples)


def test_scanner_accepts_hardened_dynamic_kwargs(tmp_path):
    path = tmp_path / "hardened.py"
    path.write_text(
        "import subprocess\n"
        "kwargs = {'text': True, 'encoding': 'utf-8'}\n"
        "kwargs['errors'] = 'replace'\n"
        "subprocess.check_call(['x'], **kwargs)\n",
        encoding="utf-8",
    )

    sites, misses = _scan([path], tmp_path)

    assert sites == 1
    assert not misses


def test_ship_gate_text_wrapper_is_hardened_without_touching_byte_reads():
    """Text helpers inherit kwargs at their single outlet; byte helper stays raw."""
    path = REPO / "sdflow-ship/scripts/ship_gate.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    text_branch = next(
        node for node in ast.walk(functions["_git_run"])
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "text"
    )
    assignments = {
        statement.targets[0].slice.value: statement.value.value
        for statement in text_branch.body
        if (isinstance(statement, ast.Assign) and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Subscript)
                and isinstance(statement.targets[0].value, ast.Name)
                and statement.targets[0].value.id == "kwargs"
                and isinstance(statement.targets[0].slice, ast.Constant)
                and isinstance(statement.value, ast.Constant))
    }
    assert assignments["encoding"] == "utf-8"
    assert assignments["errors"] == "replace"

    byte_calls = [
        node for node in ast.walk(functions["run_git_bytes"])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_git_run"
    ]
    assert len(byte_calls) == 1
    assert _constant_keywords(byte_calls[0])["text"] is False
