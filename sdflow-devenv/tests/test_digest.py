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


# ---------------------------------------------------------------------------
# task-4 面治：find_make_target 每条返回路径逐条核对（评审只点了 2 条，
# 这一节把「parser 遇到没预料的语法时会不会静默返回一个恒定/错误 recipe」
# 挨个测一遍——真正防假绿的测法是「两份内容不同的同名 target → digest 必须
# 不同」，不是只测「能不能解析」。
# ---------------------------------------------------------------------------


# ---- [Critical] 内联 `;` recipe：MUST 正确支持，不能静默算成空 ----


def test_find_make_target_inline_semicolon_recipe_captured():
    text = "foo: ; echo hi\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert "echo hi" in loc[2]


def test_find_make_target_inline_semicolon_recipe_change_detected():
    """两份内容不同的内联 ; recipe —— digest 必须不同（这是 Critical bug 本尊：
    以前两者都算出 hash("")，是与「行号锚」同构的假绿）。"""
    a = "foo: ; echo hi\n"
    b = "foo: ; echo TOTALLY DIFFERENT DANGEROUS COMMAND\n"
    _, _, ra = find_make_target(a, "foo")
    _, _, rb = find_make_target(b, "foo")
    assert ra.strip() != "" and rb.strip() != "", "MUST NOT 静默算成空 recipe"
    assert digest_make_recipe(ra) != digest_make_recipe(rb)


def test_find_make_target_inline_semicolon_with_deps_before_it():
    """`;` 前是依赖列表，`;` 后才是 recipe 首行（real make 实测确认的语义）。"""
    text = "foo: a b ; echo real-recipe\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert "echo real-recipe" in loc[2]


def test_find_make_target_inline_semicolon_plus_following_tab_lines():
    """Make 语义：一个 target 可以同时有内联 recipe 和后续 tab 行，两者都属于
    该 recipe（不是互斥关系）。"""
    text = "foo: ; echo first\n\techo second\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert "echo first" in loc[2]
    assert "echo second" in loc[2]


def test_find_make_target_inline_semicolon_ambiguous_nesting_raises():
    """`;` 出现在无法安全判定深度的形态里（未闭合的 `$(` 嵌套）——
    fail-closed 拒绝猜测，MUST NOT 猜一个位置当 recipe 边界。"""
    text = "foo: $(shell echo a ; echo b\n\techo hi\n"
    with pytest.raises(MakefileUnsupported):
        find_make_target(text, "foo")


def test_find_make_target_inline_semicolon_ambiguous_unclosed_quote_raises():
    text = "foo: \"a ; b\n\techo hi\n"
    with pytest.raises(MakefileUnsupported):
        find_make_target(text, "foo")


def test_find_make_target_inline_semicolon_inside_balanced_paren_not_split():
    """`;` 在配平的 `$(...)` 内部不是顶层 `;`，不应被当成 recipe 分隔符——
    这里整行都还是依赖列表，没有内联 recipe。"""
    text = "foo: $(shell echo a ; echo b)\n\techo real\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert loc[2].strip() == "echo real"


def test_method_digest_inline_semicolon_recipe_end_to_end(tmp_path):
    """method_digest 顶层验证同一件事：内联 ; recipe 的内容变化必须反映到
    最终 digest（不仅仅是 find_make_target 这一层）。"""
    src = {"file": "Makefile", "kind": "make-target", "selector": "foo"}
    (tmp_path / "Makefile").write_text("foo: ; echo hi\n")
    d1 = method_digest(tmp_path, "make foo", None, [], src)
    (tmp_path / "Makefile").write_text("foo: ; echo DANGEROUS\n")
    d2 = method_digest(tmp_path, "make foo", None, [], src)
    assert d1 != d2


# ---- [Important] 变量赋值行误判为「多 target 一行」----


def test_find_make_target_assignment_line_before_real_target_not_misdetected():
    text = "test := go test ./...\n\ntest:\n\techo real-target\n"
    loc = find_make_target(text, "test")
    assert loc is not None
    assert "echo real-target" in loc[2]


def test_find_make_target_export_assignment_line_not_misdetected():
    """`export VAR := value` 同样是整行变量赋值，不是规则头——覆盖同一条
    Important bug 的 `export` 前缀变体（面治，不只补审查点穿的那一种写法）。"""
    text = "export test := go test ./...\n\ntest:\n\techo real-target\n"
    loc = find_make_target(text, "test")
    assert loc is not None
    assert "echo real-target" in loc[2]


def test_find_make_target_plain_equals_assignment_not_misdetected():
    text = "test = go test ./...\ntest:\n\techo real\n"
    loc = find_make_target(text, "test")
    assert loc is not None


def test_find_make_target_plus_equals_assignment_not_misdetected():
    text = "test += extra\ntest:\n\techo real\n"
    loc = find_make_target(text, "test")
    assert loc is not None


# ---- 续行符 `\`：target 头多行 ----


def test_find_make_target_header_continuation_recipe_found():
    """target 行本身跨多个物理行（依赖列表续行）——recipe 必须从续行结束后的
    那一行开始扫，不能被续行的第二行误判为「非 tab 非空行」而提前截断
    （否则又是一次静默空 recipe）。"""
    text = "foo: dep1 \\\n     dep2\n\techo header-continued-recipe\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert "echo header-continued-recipe" in loc[2]


def test_find_make_target_header_continuation_content_change_detected():
    a = "foo: dep1 \\\n     dep2\n\techo one\n"
    b = "foo: dep1 \\\n     dep2\n\techo two\n"
    _, _, ra = find_make_target(a, "foo")
    _, _, rb = find_make_target(b, "foo")
    assert digest_make_recipe(ra) != digest_make_recipe(rb)


def test_find_make_target_header_continuation_truncated_file_raises():
    """target 头以 `\\` 结尾但文件到此截断——无法安全判定，fail-closed。"""
    text = "foo: dep1 \\\n"
    with pytest.raises(MakefileUnsupported):
        find_make_target(text, "foo")


def test_find_make_target_header_continuation_with_inline_semicolon():
    """续行的依赖列表里藏着内联 `;` recipe —— 必须跨物理行找到它。"""
    text = "foo: dep1 \\\n     dep2 ; echo hi\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert "echo hi" in loc[2]


# ---- 续行符 `\`：recipe 行本身续行 ----


def test_find_make_target_recipe_continuation_non_tab_line_included():
    """recipe 行以 `\\` 续行，下一物理行不以 tab 开头——real make 实测：它仍属于
    该 recipe。以前的 parser 会在这里提前 break，静默丢掉这行内容。"""
    text = "foo:\n\techo line1 ; \\\necho line2-no-tab\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert "echo line1" in loc[2]
    assert "echo line2-no-tab" in loc[2]


def test_find_make_target_recipe_continuation_change_detected():
    """续行内容变化必须反映到 digest —— 防止「续行部分改了但 digest 不变」的
    静默丢失式假绿。"""
    a = "foo:\n\techo line1 ; \\\necho aaa\n"
    b = "foo:\n\techo line1 ; \\\necho bbb\n"
    _, _, ra = find_make_target(a, "foo")
    _, _, rb = find_make_target(b, "foo")
    assert digest_make_recipe(ra) != digest_make_recipe(rb)


def test_find_make_target_recipe_continuation_truncated_file_raises():
    text = "foo:\n\techo line1 ; \\\n"
    with pytest.raises(MakefileUnsupported):
        find_make_target(text, "foo")


# ---- 同名 target 出现两次：合法空 vs 解析失败的空 / 冲突消解 ----


def test_find_make_target_duplicate_conflicting_recipes_raises():
    """两处都是非空且内容不同的 recipe —— real make 用「后一个覆盖」，但本
    parser 不猜哪个最终生效，fail-closed 拒绝。"""
    text = "foo:\n\techo first\n\nfoo:\n\techo second\n"
    with pytest.raises(MakefileUnsupported):
        find_make_target(text, "foo")


def test_find_make_target_duplicate_identical_recipes_no_conflict():
    """两处 recipe 内容完全相同 —— 用哪个都不影响 digest，不算冲突。"""
    text = "foo:\n\techo same\n\nfoo:\n\techo same\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert "echo same" in loc[2]


def test_find_make_target_duplicate_recipe_less_redefinition_merges():
    """第一处只声明依赖、无 recipe，第二处才有 recipe —— real make 实测：
    无 recipe 的重复定义不会清空已有 recipe，唯一的非空版本直接生效。"""
    text = "foo: dep1\nfoo: dep2\n\techo real\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert loc[2].strip() == "echo real"


def test_find_make_target_duplicate_recipe_less_redefinition_reverse_order():
    text = "foo: dep1\n\techo real\nfoo: dep2\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert loc[2].strip() == "echo real"


def test_find_make_target_legit_empty_recipe_single_occurrence():
    """target 存在，但确实【没有任何命令】——这是合法的空 recipe（例如无操作
    的聚合 target），必须原样返回空字符串,不能因为「空」就误判成解析失败。"""
    text = "foo:\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert loc[2] == ""


def test_find_make_target_legit_empty_recipe_multiple_occurrences():
    """多处定义，但全部都没有 recipe —— 依然是合法的空（不是「解析失败导致
    的空」），不应该 raise。"""
    text = "foo: dep1\nfoo: dep2\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert loc[2] == ""


# ---- .PHONY 声明行 / selector 恰好叫 PHONY ----


def test_find_make_target_phony_declaration_line_not_confused_with_target():
    """`.PHONY: foo` 这行不是「定义了 target foo」，selector=foo 时必须继续
    往下找到真正的 `foo:` 定义，不能把 .PHONY 声明行的内容误当 foo 的 recipe。"""
    text = ".PHONY: foo\nfoo:\n\techo real\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert loc[2].strip() == "echo real"


def test_find_make_target_selector_named_phony_does_not_match_dot_phony_line():
    """selector 恰好叫 "PHONY"（不带前导点）—— `.PHONY: x` 这行的 target 名是
    整串 ".PHONY"（含点），字面不等于 "PHONY"，不应被误匹配。"""
    text = ".PHONY: x\n"
    assert find_make_target(text, "PHONY") is None


# ---------------------------------------------------------------------------
# task-4 第二轮面治：recipe 扫描内层 while 循环自己的终止条件
# （评审用真 make -n 实测确认：ifeq/else/endif 分支、行首注释穿插、define 块
# 都曾被旧版 `else: break` 静默截断/误判——真正防假绿的测法是「两份内容不同的
# 同名 target → digest 必须不同」，不是「能不能解析不报错」）。
# ---------------------------------------------------------------------------


# ---- [Critical] ifeq/else/endif 在 recipe 内部：不终止扫描，两分支都计入 ----


def test_find_make_target_ifeq_in_recipe_not_truncated():
    """real make 实测（make -n）：两个分支都在同一个 recipe 区域内，只是按变量
    求值选择执行哪个——静态解析选不出「会执行哪条」，但 recipe 扫描 MUST NOT
    在 ifeq 处就地截断（旧版 `else: break` 的病：把 else 分支的内容悄悄丢了）。"""
    text = (
        "foo:\n"
        "ifeq ($(OS),Linux)\n"
        "\techo linux-branch\n"
        "else\n"
        "\techo mac-branch\n"
        "endif\n"
    )
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert "echo linux-branch" in loc[2]
    assert "echo mac-branch" in loc[2]


def test_find_make_target_ifeq_branch_a_change_detected():
    """改任一分支 —— digest 必须变（旧版 bug：else 分支及以后内容被静默截断成
    空 recipe，两份内容不同的 Makefile 会算出同一个 digest，是本次 Critical
    bug 的实测证据本尊）。"""
    a = (
        "foo:\nifeq ($(OS),Linux)\n\techo linux-branch\nelse\n"
        "\techo mac-branch\nendif\n"
    )
    b = (
        "foo:\nifeq ($(OS),Linux)\n\techo linux-branch\nelse\n"
        "\techo DANGEROUS\nendif\n"
    )
    _, _, ra = find_make_target(a, "foo")
    _, _, rb = find_make_target(b, "foo")
    assert ra.strip() != "" and rb.strip() != ""
    assert digest_make_recipe(ra) != digest_make_recipe(rb)


def test_find_make_target_ifeq_branch_b_change_detected():
    a = (
        "foo:\nifeq ($(OS),Linux)\n\techo linux-branch\nelse\n"
        "\techo mac-branch\nendif\n"
    )
    b = (
        "foo:\nifeq ($(OS),Linux)\n\techo DANGEROUS\nelse\n"
        "\techo mac-branch\nendif\n"
    )
    _, _, ra = find_make_target(a, "foo")
    _, _, rb = find_make_target(b, "foo")
    assert digest_make_recipe(ra) != digest_make_recipe(rb)


def test_find_make_target_ifeq_condition_line_change_detected():
    """条件行本身也要计入 digest —— 改 `ifeq` 判据（生效分支变了）也必须让
    digest 变，不能只盯着两个分支的命令文本。"""
    a = (
        "foo:\nifeq ($(OS),Linux)\n\techo x\nelse\n\techo y\nendif\n"
    )
    b = (
        "foo:\nifeq ($(OS),Darwin)\n\techo x\nelse\n\techo y\nendif\n"
    )
    _, _, ra = find_make_target(a, "foo")
    _, _, rb = find_make_target(b, "foo")
    assert digest_make_recipe(ra) != digest_make_recipe(rb)


def test_method_digest_ifeq_branch_change_end_to_end(tmp_path):
    """method_digest 顶层同样要抓到这件事——不仅 find_make_target 这一层。"""
    src = {"file": "Makefile", "kind": "make-target", "selector": "foo"}
    (tmp_path / "Makefile").write_text(
        "foo:\nifeq ($(OS),Linux)\n\techo a\nelse\n\techo b\nendif\n"
    )
    d1 = method_digest(tmp_path, "make foo", None, [], src)
    (tmp_path / "Makefile").write_text(
        "foo:\nifeq ($(OS),Linux)\n\techo a\nelse\n\techo DANGEROUS\nendif\n"
    )
    d2 = method_digest(tmp_path, "make foo", None, [], src)
    assert d1 != d2


# ---- [Critical] 行首注释穿插 recipe 中间：不终止扫描 ----


def test_find_make_target_col0_comment_inside_recipe_not_truncated():
    """real make 实测（make -n）：`echo before` 和 `echo after` 两行都执行——
    列 0 注释对 recipe 结构透明，不打断。旧版会在注释行就地 break，把
    `echo after` 丢在 recipe 之外，永远测不出它被改动。"""
    text = "foo:\n\techo before\n# comment in the middle\n\techo after\n"
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert "echo before" in loc[2]
    assert "echo after" in loc[2]


def test_find_make_target_comment_then_recipe_change_detected():
    """注释【之后】的 recipe 行改动 —— digest 必须变（这是本次 bug 变体二的
    实测证据：以前这部分内容被静默丢弃，改了也不变）。"""
    a = "foo:\n\techo before\n# comment\n\techo after\n"
    b = "foo:\n\techo before\n# comment\n\techo DANGEROUS\n"
    _, _, ra = find_make_target(a, "foo")
    _, _, rb = find_make_target(b, "foo")
    assert digest_make_recipe(ra) != digest_make_recipe(rb)


def test_method_digest_comment_then_recipe_change_end_to_end(tmp_path):
    src = {"file": "Makefile", "kind": "make-target", "selector": "foo"}
    (tmp_path / "Makefile").write_text(
        "foo:\n\techo before\n# comment\n\techo after\n"
    )
    d1 = method_digest(tmp_path, "make foo", None, [], src)
    (tmp_path / "Makefile").write_text(
        "foo:\n\techo before\n# comment\n\techo DANGEROUS\n"
    )
    d2 = method_digest(tmp_path, "make foo", None, [], src)
    assert d1 != d2


# ---- [Important] define/endef 块里的假 target 不干扰外面真 target ----


def test_find_make_target_define_block_fake_target_ignored():
    """real make 实测（make -n）：`define` 块内的字面 `foo:` 不是规则定义，外面
    真正的 `foo:` 才是。旧版会把两处当成「同名 target 内容冲突」拒绝一份完全
    合法的 Makefile。"""
    text = (
        "define BUILD_SCRIPT\n"
        "foo:\n"
        "\techo fake\n"
        "endef\n"
        "\n"
        "foo:\n"
        "\techo real\n"
    )
    loc = find_make_target(text, "foo")
    assert loc is not None
    assert "echo real" in loc[2]
    assert "echo fake" not in loc[2]


def test_find_make_target_define_block_unterminated_raises():
    text = "define BUILD_SCRIPT\nfoo:\n\techo fake\n"
    with pytest.raises(MakefileUnsupported):
        find_make_target(text, "foo")


def test_method_digest_define_block_fake_target_end_to_end(tmp_path):
    src = {"file": "Makefile", "kind": "make-target", "selector": "foo"}
    (tmp_path / "Makefile").write_text(
        "define BUILD_SCRIPT\nfoo:\n\techo fake\nendef\n\nfoo:\n\techo real\n"
    )
    # MUST NOT raise MakefileUnsupported —— 这是一份合法的 Makefile。
    d = method_digest(tmp_path, "make foo", None, [], src)
    assert isinstance(d, str) and len(d) == 64


# ---- [Important] ifeq/endif 包裹整个 target 头：fail-closed，消息要准确 ----


def test_find_make_target_ifeq_wraps_target_head_raises_with_accurate_message():
    """real make 实测（make -n）：两个分支各自完整重复一份 `foo:` + recipe，
    生效哪个看变量求值。parser 不猜，但错误信息必须点明真实原因（条件块包裹）
    并给出真实存在的逃生路径（source.file 整文件 digest）。"""
    text = (
        "ifeq ($(OS),Linux)\n"
        "foo:\n"
        "\techo linux\n"
        "else\n"
        "foo:\n"
        "\techo mac\n"
        "endif\n"
    )
    with pytest.raises(MakefileUnsupported) as exc_info:
        find_make_target(text, "foo")
    msg = str(exc_info.value)
    assert "条件块" in msg
    assert "file" in msg  # 逃生路径提示：source.file 整文件 digest


# ---- [Minor] source == {"file": ""} 不许被短路跳过 ----


def test_method_digest_empty_source_file_fails_closed(tmp_path):
    """{"file": ""} 是坏输入 —— MUST NOT 被 `if source.get("file")` 短路成
    "这段 source 没提供 file"，必须走到 contain() 的空路径校验去 fail-closed。"""
    from devenv_paths import PathEscape

    src = {"file": ""}
    with pytest.raises(PathEscape):
        method_digest(tmp_path, "cmd", None, [], src)
