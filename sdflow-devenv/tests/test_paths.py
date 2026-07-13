import os, sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from devenv_paths import contain, PathEscape


def test_accepts_plain_relative(tmp_path):
    (tmp_path / "Makefile").write_text("x\n")
    got = contain(tmp_path, "Makefile")
    assert got == (tmp_path / "Makefile").resolve()


def test_rejects_absolute(tmp_path):
    with pytest.raises(PathEscape):
        contain(tmp_path, "/etc/passwd")


def test_rejects_dotdot(tmp_path):
    with pytest.raises(PathEscape):
        contain(tmp_path, "../outside.txt")


def test_rejects_dotdot_in_middle(tmp_path):
    with pytest.raises(PathEscape):
        contain(tmp_path, "a/../../outside.txt")


def test_rejects_symlink_ancestor(tmp_path):
    outside = tmp_path.parent / "outside_dir"
    outside.mkdir()
    (outside / "loot.txt").write_text("secret\n")
    (tmp_path / "link").symlink_to(outside, target_is_directory=True)
    # 目标文件本身不是 symlink，但它的【祖先】是 —— 前一版只查目标本身，会漏
    with pytest.raises(PathEscape):
        contain(tmp_path, "link/loot.txt")


def test_rejects_symlink_target_itself(tmp_path):
    outside = tmp_path.parent / "outside2.txt"
    outside.write_text("x\n")
    (tmp_path / "sneaky").symlink_to(outside)
    with pytest.raises(PathEscape):
        contain(tmp_path, "sneaky")


def test_nonexistent_path_ok_if_contained(tmp_path):
    # 写入新文件时目标还不存在 —— 必须允许（否则 skill 写不了新 smoke）
    got = contain(tmp_path, "internal/new_smoke_test.go")
    assert got == (tmp_path / "internal/new_smoke_test.go").resolve()


def test_rejects_empty(tmp_path):
    with pytest.raises(PathEscape):
        contain(tmp_path, "")


def test_rejects_dot(tmp_path):
    # "." 折叠后 parts 为空 —— 必须拒绝，否则等同放行仓根本身
    with pytest.raises(PathEscape):
        contain(tmp_path, ".")


def test_rejects_dot_slash(tmp_path):
    with pytest.raises(PathEscape):
        contain(tmp_path, "./")


def test_rejects_dot_dot_dot_degenerate(tmp_path):
    # "././." 同样折叠为空 parts
    with pytest.raises(PathEscape):
        contain(tmp_path, "././.")


def test_rejects_embedded_null_byte_as_path_escape(tmp_path):
    # 含 \x00 的路径必须归一为 PathEscape，而不是让 os.lstat 抛出的
    # 原始 ValueError("embedded null byte") 逃出契约
    with pytest.raises(PathEscape):
        contain(tmp_path, "foo\x00bar")
