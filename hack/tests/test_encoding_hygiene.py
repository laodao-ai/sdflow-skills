"""`check_encoding_hygiene` 的行为回归测试。"""
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_encoding_hygiene as hygiene  # noqa: E402


def _write(root, relative, body):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_complete_prelude_is_green(tmp_path, capsys):
    _write(
        tmp_path,
        "hack/entry.py",
        '''import sys
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
if __name__ == "__main__":
    pass
''',
    )

    assert hygiene.main(tmp_path) == 0
    assert "满足编码前导契约" in capsys.readouterr().out


def test_missing_prelude_reports_every_contract_and_repair_pointer(tmp_path, capsys):
    _write(tmp_path, "hack/entry.py", 'if __name__ == "__main__":\n    pass\n')

    assert hygiene.main(tmp_path) == 1
    stderr = capsys.readouterr().err
    assert "hack/entry.py" in stderr
    assert "stdout reconfigure" in stderr
    assert "stderr reconfigure" in stderr
    assert 'errors="replace"' in stderr
    assert "修：" in stderr
    assert "CLAUDE.md" in stderr


def test_stdout_only_prelude_reports_missing_stderr(tmp_path, capsys):
    _write(
        tmp_path,
        "hack/entry.py",
        '''import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if __name__ == "__main__":
    pass
''',
    )

    assert hygiene.main(tmp_path) == 1
    stderr = capsys.readouterr().err
    assert "stderr reconfigure" in stderr
    assert "stdout reconfigure" not in stderr


def test_prelude_without_replace_strategy_reports_missing_contract(tmp_path, capsys):
    _write(
        tmp_path,
        "hack/entry.py",
        '''import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
if __name__ == "__main__":
    pass
''',
    )

    assert hygiene.main(tmp_path) == 1
    stderr = capsys.readouterr().err
    assert 'errors="replace"' in stderr
    assert "stdout reconfigure" not in stderr
    assert "stderr reconfigure" not in stderr


def test_canonical_bundle_source_is_not_excluded_with_its_mirror(tmp_path, capsys):
    _write(
        tmp_path,
        "sdflow-init/assets/workflow/tools/source.py",
        'if __name__ == "__main__":\n    pass\n',
    )
    _write(
        tmp_path,
        "openspec/workflow/tools/mirror.py",
        'if __name__ == "__main__":\n    pass\n',
    )

    assert hygiene.main(tmp_path) == 1
    stderr = capsys.readouterr().err
    assert "sdflow-init/assets/workflow/tools/source.py" in stderr
    assert "openspec/workflow/tools/mirror.py" not in stderr


def test_complete_prelude_after_line_190_is_green(tmp_path, capsys):
    _write(
        tmp_path,
        "sdflow-ship/scripts/entry.py",
        '"""long module prelude"""\n' * 191
        + '''import sys
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
if __name__ == "__main__":
    pass
''',
    )

    assert hygiene.main(tmp_path) == 0
    assert "满足编码前导契约" in capsys.readouterr().out


def test_checker_itself_satisfies_its_contract():
    assert hygiene.missing_contracts(Path(hygiene.__file__)) == []


def test_cli_rejects_apply_mode():
    result = subprocess.run(
        [sys.executable, str(Path(hygiene.__file__)), "--apply"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode != 0
    assert "不支持 --apply" in result.stderr
