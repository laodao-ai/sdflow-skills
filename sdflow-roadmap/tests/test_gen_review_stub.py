"""
Tests for gen_review_stub.py — generates openspec/roadmaps/<name>/review.html.
Run with: python3 -m pytest sdflow-roadmap/tests/test_gen_review_stub.py -v
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from gen_review_stub import gen_review_stub


# Placeholder template content used by the fixture below. gen_review_stub substitutes
# __PROJECT_NAME__ with the project root's basename (in addition to otherwise being a
# plain copy — no other token/scope substitution happens).
STUB_TEMPLATE = (
    '<script>window.location.pathname; /* review stub fixture */</script>\n'
    '<script>window.__OPENSPEC_PROJECT_NAME__ = "__PROJECT_NAME__";</script>'
)


def make_project(tmp_path, with_review_tool=True, with_roadmap_dir=True):
    osroot = tmp_path / "openspec"
    if with_roadmap_dir:
        (osroot / "roadmaps" / "my-feature").mkdir(parents=True)
    if with_review_tool:
        (osroot / "workflow" / "tools").mkdir(parents=True, exist_ok=True)
        (osroot / "workflow" / "tools" / "review-stub.html").write_text(STUB_TEMPLATE, encoding="utf-8")
        (osroot / "review.html").write_text("root", encoding="utf-8")
    return tmp_path


class TestGenReviewStub:
    def test_writes_stub_matching_template(self, tmp_path):
        make_project(tmp_path)
        dst = gen_review_stub(str(tmp_path), "my-feature")
        content = Path(dst).read_text(encoding="utf-8")
        # __PROJECT_NAME__ substituted with the project root's basename …
        assert "__PROJECT_NAME__" not in content
        assert content == STUB_TEMPLATE.replace("__PROJECT_NAME__", tmp_path.name)
        # … while the template source itself (openspec/workflow/tools/review-stub.html) stays raw.
        template_src = tmp_path / "openspec" / "workflow" / "tools" / "review-stub.html"
        assert "__PROJECT_NAME__" in template_src.read_text(encoding="utf-8")

    def test_raises_when_review_tool_missing(self, tmp_path):
        make_project(tmp_path, with_review_tool=False)
        with pytest.raises(FileNotFoundError, match="review 工具"):
            gen_review_stub(str(tmp_path), "my-feature")

    def test_raises_when_roadmap_dir_missing(self, tmp_path):
        make_project(tmp_path, with_roadmap_dir=False)
        with pytest.raises(FileNotFoundError, match="目录不存在"):
            gen_review_stub(str(tmp_path), "my-feature")
