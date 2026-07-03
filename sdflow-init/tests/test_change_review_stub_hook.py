"""
Tests for the change-review-stub.py PostToolUse hook.
Run with: python3 -m pytest sdflow-init/tests/test_change_review_stub_hook.py -v
"""
import json
import subprocess
import sys
from pathlib import Path

HOOK = str(Path(__file__).parent.parent / "assets" / "hooks" / "change-review-stub.py")

# Placeholder template content used by the fixture below. The hook substitutes
# __PROJECT_NAME__ with the project root's basename (in addition to otherwise being a
# plain copy — no other token/scope substitution happens).
STUB_TEMPLATE = (
    '<script>window.location.pathname; /* review stub fixture */</script>\n'
    '<script>window.__OPENSPEC_PROJECT_NAME__ = "__PROJECT_NAME__";</script>'
)


def run_hook(payload, cwd):
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(payload),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=5,
    )


def make_project(tmp_path, with_review_tool=True):
    osroot = tmp_path / "openspec"
    (osroot / "changes" / "add-widget").mkdir(parents=True)
    if with_review_tool:
        (osroot / "workflow" / "tools").mkdir(parents=True, exist_ok=True)
        (osroot / "workflow" / "tools" / "review-stub.html").write_text(STUB_TEMPLATE, encoding="utf-8")
        (osroot / "review.html").write_text("root", encoding="utf-8")
    return tmp_path


class TestChangeReviewStubHook:
    def test_writes_stub_when_change_dir_and_review_tool_exist(self, tmp_path):
        make_project(tmp_path)
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "openspec new change add-widget"},
            "cwd": str(tmp_path),
        }
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0
        stub = tmp_path / "openspec" / "changes" / "add-widget" / "review.html"
        assert stub.is_file()
        rendered = stub.read_text(encoding="utf-8")
        # __PROJECT_NAME__ substituted with the project root's (cwd's) basename …
        assert "__PROJECT_NAME__" not in rendered
        assert rendered == STUB_TEMPLATE.replace("__PROJECT_NAME__", tmp_path.name)
        # … while the template source itself (openspec/workflow/tools/review-stub.html) stays raw.
        template_src = tmp_path / "openspec" / "workflow" / "tools" / "review-stub.html"
        assert "__PROJECT_NAME__" in template_src.read_text(encoding="utf-8")

    def test_skips_silently_when_review_tool_not_installed(self, tmp_path):
        make_project(tmp_path, with_review_tool=False)
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "openspec new change add-widget"},
            "cwd": str(tmp_path),
        }
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0
        assert not (tmp_path / "openspec" / "changes" / "add-widget" / "review.html").exists()

    def test_skips_silently_when_change_dir_does_not_exist(self, tmp_path):
        make_project(tmp_path)
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "openspec new change never-created"},
            "cwd": str(tmp_path),
        }
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0
        assert not (tmp_path / "openspec" / "changes" / "never-created").exists()

    def test_ignores_non_bash_tools(self, tmp_path):
        make_project(tmp_path)
        payload = {"tool_name": "Write", "tool_input": {}, "cwd": str(tmp_path)}
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0

    def test_ignores_unrelated_bash_commands(self, tmp_path):
        make_project(tmp_path)
        payload = {"tool_name": "Bash", "tool_input": {"command": "git status"}, "cwd": str(tmp_path)}
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0

    def test_idempotent_rerun_does_not_error(self, tmp_path):
        make_project(tmp_path)
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "openspec new change add-widget"},
            "cwd": str(tmp_path),
        }
        run_hook(payload, tmp_path)
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0

    def test_handles_garbage_stdin_by_exiting_zero(self, tmp_path):
        make_project(tmp_path)
        result = subprocess.run(
            [sys.executable, HOOK], input="not json", cwd=str(tmp_path),
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0

    def test_handles_directory_at_destination_gracefully(self, tmp_path):
        """
        When dst path is pre-created as a directory (not a file),
        the hook should not crash when trying to read it.
        It should exit 0 (fail-open).
        """
        make_project(tmp_path)
        # Pre-create the destination as a directory instead of a file
        review_dir = tmp_path / "openspec" / "changes" / "add-widget" / "review.html"
        review_dir.mkdir(parents=True)
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "openspec new change add-widget"},
            "cwd": str(tmp_path),
        }
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0

    def test_handles_invalid_utf8_in_existing_file(self, tmp_path):
        """
        When the destination file contains invalid UTF-8 bytes,
        the hook should not crash. It should treat it as "no existing file",
        write the fresh content (overwriting the broken file), and exit 0.
        """
        make_project(tmp_path)
        # Pre-create the destination with invalid UTF-8 bytes
        review_file = tmp_path / "openspec" / "changes" / "add-widget" / "review.html"
        review_file.parent.mkdir(parents=True, exist_ok=True)
        review_file.write_bytes(b"\xff\xfe invalid utf-8")
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "openspec new change add-widget"},
            "cwd": str(tmp_path),
        }
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0
        # Verify the file now contains valid content (fresh, substituted copy of the template)
        content = review_file.read_text(encoding="utf-8")
        assert content == STUB_TEMPLATE.replace("__PROJECT_NAME__", tmp_path.name)
