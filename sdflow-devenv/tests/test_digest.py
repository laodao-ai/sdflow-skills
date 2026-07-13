import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from devenv_digest import (
    digest_file,
    find_make_target,
    digest_make_recipe,
    method_digest,
    MakeTargetNotFound,
    MakefileUnsupported,
    DigestInputInvalid,
)
from devenv_paths import PathEscape

MAKEFILE = """\
.PHONY: integration
# 这是注释，MUST NOT 被剥掉（注释可能载有语义）
integration:
\thack/ctl.sh start
\tMQTT_PORT=1883 go test ./... ; status=$$? ; \\
\thack/ctl.sh stop ; exit $$status

.PHONY: unit
unit:
\tgo test -short ./...
"""


# ---------------------------------------------------------------------------
# Step 1 测试（brief 逐字照抄）
# ---------------------------------------------------------------------------


def test_find_make_target(tmp_path):
    loc = find_make_target(MAKEFILE, "integration")
    assert loc is not None
    start, end, recipe = loc
    assert "ctl.sh start" in recipe
    assert "ctl.sh stop" in recipe
    assert "go test -short" not in recipe      # 不能吃到下一个 target


def test_find_make_target_missing():
    assert find_make_target(MAKEFILE, "nonexistent") is None


def test_selector_survives_line_shift(tmp_path):
    """在文件顶部插三行 —— digest 必须【不变】（行号锚会全部错位，digest 不会）"""
    shifted = "VAR1 = a\nVAR2 = b\nVAR3 = c\n" + MAKEFILE
    _, _, r1 = find_make_target(MAKEFILE, "integration")
    _, _, r2 = find_make_target(shifted, "integration")
    assert digest_make_recipe(r1) == digest_make_recipe(r2)


def test_recipe_content_change_detected(tmp_path):
    """内容变了 digest 必须变 —— 这才是要抓的东西（命令表说谎）"""
    changed = MAKEFILE.replace("MQTT_PORT=1883", "MQTT_PORT=9999")
    _, _, r1 = find_make_target(MAKEFILE, "integration")
    _, _, r2 = find_make_target(changed, "integration")
    assert digest_make_recipe(r1) != digest_make_recipe(r2)


def test_makefile_normalization_keeps_tab():
    """tab 有语法意义 —— MUST NOT 被规范化抹掉"""
    with_tab = "\tgo test ./...\n"
    with_spaces = "    go test ./...\n"
    assert digest_make_recipe(with_tab) != digest_make_recipe(with_spaces)


def test_makefile_normalization_keeps_comments():
    a = "\t# 重要注释\n\tgo test\n"
    b = "\tgo test\n"
    assert digest_make_recipe(a) != digest_make_recipe(b)


def test_makefile_normalization_ignores_trailing_ws_and_blank_lines():
    a = "\tgo test ./...   \n\n"
    b = "\tgo test ./...\n"
    assert digest_make_recipe(a) == digest_make_recipe(b)


# ---- ⚠️ 核心红线：YAML 缩进即语义 ----


def test_yaml_indent_change_IS_detected(tmp_path):
    """YAML 的行首缩进决定嵌套层级 —— 若套用 Makefile 的「剥去行首空白」规则，
    两份【语义完全不同】的 YAML 会算出同一个 digest = 与「行号锚」同构的假绿。"""
    root = tmp_path
    (root / "compose.yml").write_text(
        "services:\n  broker:\n    image: eclipse-mosquitto\n    ports:\n      - 1883:1883\n"
    )
    d1 = digest_file(root, "compose.yml")

    # 改缩进层级：ports 从 broker 的子级变成 services 的子级 —— 语义完全变了
    (root / "compose.yml").write_text(
        "services:\n  broker:\n    image: eclipse-mosquitto\n  ports:\n      - 1883:1883\n"
    )
    d2 = digest_file(root, "compose.yml")
    assert d1 != d2, "YAML 缩进变化必须被 digest 捕获！MUST NOT 对 YAML 做空白规范化"


def test_json_byte_exact(tmp_path):
    (tmp_path / "package-lock.json").write_text('{"a": 1}\n')
    d1 = digest_file(tmp_path, "package-lock.json")
    (tmp_path / "package-lock.json").write_text('{"a":1}\n')     # 只是空格差异
    d2 = digest_file(tmp_path, "package-lock.json")
    assert d1 != d2, "lockfile 必须逐字节 —— 不做任何规范化"


def test_digest_file_goes_through_containment(tmp_path):
    with pytest.raises(PathEscape):
        digest_file(tmp_path, "../../etc/passwd")


def test_method_digest_changes_when_fixture_changes(tmp_path):
    """改 fixture 让断言失效 —— 是 vacuous 的主要引入路径，必须被捕获"""
    (tmp_path / "Makefile").write_text(MAKEFILE)
    (tmp_path / "smoke_test.go").write_text("package x\n")
    (tmp_path / "fixture.json").write_text('{"v": 1}\n')
    src = {"file": "Makefile", "kind": "make-target", "selector": "integration"}

    d1 = method_digest(tmp_path, "make integration", "smoke_test.go", ["fixture.json"], src)
    (tmp_path / "fixture.json").write_text('{"v": 2}\n')
    d2 = method_digest(tmp_path, "make integration", "smoke_test.go", ["fixture.json"], src)
    assert d1 != d2


def test_method_digest_stable_when_nothing_changes(tmp_path):
    (tmp_path / "Makefile").write_text(MAKEFILE)
    (tmp_path / "smoke_test.go").write_text("package x\n")
    src = {"file": "Makefile", "kind": "make-target", "selector": "integration"}
    d1 = method_digest(tmp_path, "make integration", "smoke_test.go", [], src)
    d2 = method_digest(tmp_path, "make integration", "smoke_test.go", [], src)
    assert d1 == d2


# ---------------------------------------------------------------------------
# 额外覆盖（本任务指令要求，超出 brief Step1 字面测试）
# ---------------------------------------------------------------------------


# ---- selector 坏输入：fail-closed 到明确异常 ----


def test_method_digest_raises_when_target_missing(tmp_path):
    """selector 在文件里找不到 —— MUST NOT 静默退化成「空 recipe」的稳定 digest
    （那会让「命令表说谎」永远测不出来，是本任务要抓的假绿同款病）。"""
    (tmp_path / "Makefile").write_text(MAKEFILE)
    src = {"file": "Makefile", "kind": "make-target", "selector": "nonexistent"}
    with pytest.raises(MakeTargetNotFound):
        method_digest(tmp_path, "make nonexistent", None, [], src)


def test_method_digest_raises_when_makefile_missing(tmp_path):
    src = {"file": "Makefile", "kind": "make-target", "selector": "integration"}
    with pytest.raises(MakeTargetNotFound):
        method_digest(tmp_path, "make integration", None, [], src)


def test_method_digest_raises_on_empty_makefile(tmp_path):
    (tmp_path / "Makefile").write_text("")
    src = {"file": "Makefile", "kind": "make-target", "selector": "integration"}
    with pytest.raises(MakeTargetNotFound):
        method_digest(tmp_path, "make integration", None, [], src)


def test_method_digest_raises_on_empty_selector(tmp_path):
    (tmp_path / "Makefile").write_text(MAKEFILE)
    src = {"file": "Makefile", "kind": "make-target", "selector": ""}
    with pytest.raises(MakeTargetNotFound):
        method_digest(tmp_path, "make ''", None, [], src)


def test_method_digest_generic_source_missing_file_raises(tmp_path):
    """非 make-target 的 source 指向不存在的文件 —— digest_file 的原始字节读取
    天然 FileNotFoundError，已经是明确异常，不需要额外包一层。"""
    src = {"file": "does-not-exist.yml"}
    with pytest.raises(FileNotFoundError):
        method_digest(tmp_path, "some command", None, [], src)


# ---- Makefile selector 的坑：不能猜的语法要明确拒绝 ----


def test_find_make_target_rejects_multi_target_line():
    """`a b: dep` —— 一行定义多个 target，parser 不去猜哪部分属于 selector。"""
    text = "a b:\n\techo hi\n"
    with pytest.raises(MakefileUnsupported):
        find_make_target(text, "a")


def test_find_make_target_rejects_multi_target_line_other_name():
    text = "a b:\n\techo hi\n"
    with pytest.raises(MakefileUnsupported):
        find_make_target(text, "b")


def test_find_make_target_ignores_multi_target_line_when_unrelated():
    """多 target 一行的坑只在【命中我们的 selector】时才拒绝——
    完全无关的行不应该让别的 target 也炸。"""
    text = "a b:\n\techo hi\n\nreal:\n\techo real\n"
    loc = find_make_target(text, "real")
    assert loc is not None
    assert "echo real" in loc[2]


def test_find_make_target_rejects_double_colon_rule():
    """`a:: dep` —— 双冒号规则允许同一 target 出现多条独立规则，
    单遍首匹配扫描会漏掉后续规则块，parser 明确拒绝而不是悄悄漏一半。"""
    text = "a:: dep\n\techo one\n"
    with pytest.raises(MakefileUnsupported):
        find_make_target(text, "a")


def test_find_make_target_rejects_target_specific_variable_line():
    """`foo: VAR=x` —— target-specific 变量赋值和「target 定义 + 内联 recipe」
    在字面上无法可靠区分，parser 不猜。"""
    text = "foo: VAR=x\n\techo hi\n"
    with pytest.raises(MakefileUnsupported):
        find_make_target(text, "foo")


# ---- 路径过 contain()：绝对路径 / .. / symlink ----


def test_method_digest_source_file_path_escape(tmp_path):
    src = {"file": "../../etc/passwd"}
    with pytest.raises(PathEscape):
        method_digest(tmp_path, "cmd", None, [], src)


def test_method_digest_smoke_path_escape(tmp_path):
    (tmp_path / "Makefile").write_text(MAKEFILE)
    with pytest.raises(PathEscape):
        method_digest(tmp_path, "cmd", "/etc/passwd", [], None)


def test_method_digest_fixture_path_escape(tmp_path):
    with pytest.raises(PathEscape):
        method_digest(tmp_path, "cmd", None, ["../../etc/passwd"], None)


def test_find_make_target_symlink_ancestor_rejected(tmp_path):
    """selector 定位本身只吃 text，不碰路径；path containment 在 digest_file /
    method_digest 层做。这里改用 method_digest 验证 symlink 祖先目录被拒。"""
    outside = tmp_path.parent / "outside_link_target"
    outside.mkdir(exist_ok=True)
    (outside / "Makefile").write_text(MAKEFILE)
    link = tmp_path / "link"
    link.symlink_to(outside)
    src = {"file": "link/Makefile", "kind": "make-target", "selector": "integration"}
    with pytest.raises(PathEscape):
        method_digest(tmp_path, "make integration", None, [], src)


# ---- 二进制 / 非 UTF-8 字节：不崩 ----


def test_digest_file_binary_no_crash(tmp_path):
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01\xff\xfe\x80\x81")
    d = digest_file(tmp_path, "blob.bin")
    assert isinstance(d, str) and len(d) == 64


def test_method_digest_binary_fixture_no_crash(tmp_path):
    (tmp_path / "Makefile").write_text(MAKEFILE)
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01\xff\xfe\x80\x81")
    src = {"file": "Makefile", "kind": "make-target", "selector": "integration"}
    d = method_digest(tmp_path, "make integration", None, ["blob.bin"], src)
    assert isinstance(d, str) and len(d) == 64


def test_makefile_non_utf8_bytes_no_crash(tmp_path):
    """Makefile 本身含非法 UTF-8 字节 —— method_digest 读取 recipe 时 MUST NOT 崩。"""
    raw = b".PHONY: integration\nintegration:\n\t\xff\xfe echo hi\n"
    (tmp_path / "Makefile").write_bytes(raw)
    src = {"file": "Makefile", "kind": "make-target", "selector": "integration"}
    d = method_digest(tmp_path, "make integration", None, [], src)
    assert isinstance(d, str) and len(d) == 64


# ---- method_digest 坏输入类型：fail-closed（同 devenv_schema 的类型前置校验纪律）----


def test_method_digest_rejects_non_dict_source(tmp_path):
    with pytest.raises(DigestInputInvalid):
        method_digest(tmp_path, "cmd", None, [], "not-a-dict")


def test_method_digest_rejects_non_list_fixtures(tmp_path):
    with pytest.raises(DigestInputInvalid):
        method_digest(tmp_path, "cmd", None, "not-a-list", None)


def test_method_digest_rejects_non_str_method(tmp_path):
    with pytest.raises(DigestInputInvalid):
        method_digest(tmp_path, 123, None, [], None)


def test_method_digest_rejects_non_str_fixture_element(tmp_path):
    with pytest.raises(DigestInputInvalid):
        method_digest(tmp_path, "cmd", None, [123], None)
