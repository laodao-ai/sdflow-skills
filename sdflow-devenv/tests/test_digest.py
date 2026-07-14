"""devenv_digest 测试 —— A21 重写版。

前一版（562 行脚本 / 753 行测试）测的是一个手搓 GNU make 解析器：按 selector
重定位 target、提取 recipe body、按文件类型分治做规范化。那条路已被 07 附录
A21 否决——make 语法面无界，补丁循环不收敛，最终留下 7 个「语法不支持」的
fail-closed 罢工分支，而每个罢工分支都是对核心承诺（「不管什么项目都能给一份
三层框架」）的一次背叛。

本文件的两条红线：
  - test_complex_makefile_never_raises      核心承诺守卫（复杂 Makefile 不罢工）
  - test_no_make_parsing_symbols_exist      防 parser 从后门爬回来
"""
import ast
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from devenv_digest import file_digest, lane_file_digests, stale_files
from devenv_paths import PathEscape


# ── 复杂 Makefile 语料：A21 的核心回归守卫 ────────────────────────────
# 前一版的 parser 在这份语料上有 7 种罢工姿势（每种都曾是一轮 review 的产物）。
# 现在 digest 是整文件字节 —— 语法再复杂也【不可能】罢工。
COMPLEX_MAKEFILE = """\
SHELL := /bin/bash
MQTT_PORT ?= 1883

ifeq ($(CI),true)
integration: deps           # ifeq 包裹的 target（前一版：静默截断 recipe → 假绿）
\tgo test -tags=integration ./...
else
integration: deps
\tMQTT_PORT=$(MQTT_PORT) go test -tags=integration ./...
endif

lint vet:: fmt              # 一行多 target + 双冒号（前一版：MakefileUnsupported）
\tgo vet ./...

integration: EXTRA := -v    # target-specific 变量（前一版：误判为重复定义）

define run_smoke            # define 块（前一版：吞掉后续 target）
\t@echo running
endef

deps: ; @echo deps          # 内联 ; recipe（前一版：算出空 digest → 假绿）

long: \\
\tdeps                      # 续行（前一版：截断）
\t@echo long
"""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _lane(**kw):
    lane = {
        "id": "integration",
        "source": {"file": "Makefile", "kind": "make-target", "selector": "integration"},
        "smoke": "smoke_test.go",
        "fixtures": [],
        "verification": {"evidence": {}},
    }
    lane.update(kw)
    return lane


def _seed(root, makefile=COMPLEX_MAKEFILE):
    (root / "Makefile").write_text(makefile, encoding="utf-8")
    (root / "smoke_test.go").write_text("package x\n", encoding="utf-8")


# ── file_digest：原始字节，零规范化 ───────────────────────────────────

def test_file_digest_is_raw_bytes(tmp_path):
    (tmp_path / "Makefile").write_text(COMPLEX_MAKEFILE, encoding="utf-8")
    assert file_digest(tmp_path, "Makefile") == _sha(COMPLEX_MAKEFILE.encode("utf-8"))


def test_file_digest_no_normalization_at_all(tmp_path):
    """A21：所有类型一视同仁、零规范化。

    这一条同时保证了旧「分治」规则想保证的东西（YAML 缩进即语义），
    且【在结构上不可能踩错】—— 因为根本不存在 normalize()。
    """
    p = tmp_path / "compose.yml"
    p.write_text("services:\n  broker:\n    image: eclipse-mosquitto\n")
    d1 = file_digest(tmp_path, "compose.yml")
    p.write_text("services:\n    broker:\n        image: eclipse-mosquitto\n")  # 缩进变=语义变
    assert d1 != file_digest(tmp_path, "compose.yml"), "YAML 缩进变化必须被捕获"


def test_file_digest_tab_vs_spaces_differ(tmp_path):
    """tab 有语法意义。原始字节天然区分它 —— 无需任何「保留 tab」的特殊规则。"""
    p = tmp_path / "Makefile"
    p.write_text("t:\n\tgo test\n")
    d_tab = file_digest(tmp_path, "Makefile")
    p.write_text("t:\n    go test\n")
    assert d_tab != file_digest(tmp_path, "Makefile")


def test_file_digest_comment_change_detected(tmp_path):
    """改注释也算改动 —— 允许多报，刻意如此（防漏宁可多报）。"""
    p = tmp_path / "Makefile"
    p.write_text("t:\n\tgo test  # fast\n")
    d1 = file_digest(tmp_path, "Makefile")
    p.write_text("t:\n\tgo test  # slow\n")
    assert d1 != file_digest(tmp_path, "Makefile")


def test_file_digest_lockfile_byte_exact(tmp_path):
    p = tmp_path / "package-lock.json"
    p.write_text('{"a": 1}\n')
    d1 = file_digest(tmp_path, "package-lock.json")
    p.write_text('{"a":  1}\n')  # 只多一个空格
    assert d1 != file_digest(tmp_path, "package-lock.json")


def test_file_digest_goes_through_containment(tmp_path):
    with pytest.raises(PathEscape):
        file_digest(tmp_path, "../../etc/passwd")


# ── ⭐ A21 红线一：复杂 Makefile MUST NOT 罢工 ───────────────────────

def test_complex_makefile_never_raises(tmp_path):
    """核心承诺「不管什么项目」的守卫。

    前一版的 parser 在这份语料上有 7 种 MakefileUnsupported 罢工姿势。
    现在：digest 是整文件字节 —— 语法再复杂也不可能罢工。
    """
    _seed(tmp_path)
    digests = lane_file_digests(tmp_path, _lane())  # MUST NOT raise
    assert digests["Makefile"] == _sha(COMPLEX_MAKEFILE.encode("utf-8"))


# ── ⭐ A21 红线二：防 parser 从后门爬回来 ────────────────────────────

def test_no_make_parsing_symbols_exist():
    """契约测试：本模块 MUST 零 make 知识。

    若未来有人把解析器加回来（哪怕只是「查一下 target 存不存在」的正则），
    这条当场红。「target 能不能跑」由 verify-lane 真跑一遍让 make 自己判。
    """
    import devenv_digest as m

    banned = (
        "find_make_target",
        "digest_make_recipe",
        "method_digest",
        "digest_file",
        "normalize",
        "MakefileUnsupported",
        "MakeTargetNotFound",
    )
    for name in banned:
        assert not hasattr(m, name), (
            f"{name} 不该存在 —— A21：devenv_digest MUST 零 make 知识。"
            "「target 能不能跑」由 verify-lane 真跑一遍让 make 自己判。"
        )

    # 只看【真实代码】：docstring 与注释里大量出现 "recipe"，正是在解释「为什么
    # 不提取它」—— 用文本扫描会把这些解释本身判成违规（假阳）。故走 AST：剥掉所有
    # docstring（注释在 AST 里天然不存在），再看剩下的代码。
    tree = ast.parse(Path(m.__file__).read_text(encoding="utf-8"))

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module)
    assert "re" not in imported, (
        "MUST NOT import re —— A21：不用正则去猜 make 语法。"
        "「target 能不能跑」由 verify-lane 真跑一遍让 make 自己判。"
    )

    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body.pop(0)
    code = ast.unparse(tree).lower()
    for token in ("recipe", "makefile", "target"):
        assert token not in code, f"实现代码里不该出现 {token!r} —— 本模块只知道字节"


# ── lane_file_digests：覆盖面 ─────────────────────────────────────────

def test_lane_file_digests_covers_source_smoke_fixtures(tmp_path):
    _seed(tmp_path, "integration:\n\tgo test\n")
    (tmp_path / "fixture.json").write_text("{}\n")
    d = lane_file_digests(tmp_path, _lane(fixtures=["fixture.json"]))
    assert set(d) == {"Makefile", "smoke_test.go", "fixture.json"}


def test_lane_file_digests_skips_toolchain_source(tmp_path):
    """source.file == "-"（toolchain 类，如 `go test ./...`）→ 不进 digest。"""
    (tmp_path / "smoke_test.go").write_text("package x\n")
    lane = _lane(source={"file": "-", "kind": "toolchain", "selector": "go test"})
    assert set(lane_file_digests(tmp_path, lane)) == {"smoke_test.go"}


def test_lane_file_digests_paths_are_contained(tmp_path):
    with pytest.raises(PathEscape):
        lane_file_digests(tmp_path, _lane(fixtures=["../../etc/passwd"]))


# ── stale_files：失配检测（lint 的判据）──────────────────────────────

def _verified(root, lane):
    lane["verification"]["evidence"]["file_digests"] = lane_file_digests(root, lane)
    return lane


def test_stale_files_empty_when_unchanged(tmp_path):
    _seed(tmp_path, "integration:\n\tgo test\n")
    assert stale_files(tmp_path, _verified(tmp_path, _lane())) == []


def test_stale_files_detects_changed_smoke(tmp_path):
    _seed(tmp_path, "integration:\n\tgo test\n")
    lane = _verified(tmp_path, _lane())
    (tmp_path / "smoke_test.go").write_text("package x\nfunc TestFoo() {}\n")
    assert stale_files(tmp_path, lane) == ["smoke_test.go"]


def test_stale_files_line_shift_IS_detected(tmp_path):
    """「行还在、内容变了」+ 行号位移 —— 整文件字节，两者都抓。

    对比旧「行号锚」：「第 11-14 行存不存在」对任何 >=14 行的文件恒真 = 假绿。
    """
    _seed(tmp_path, "integration:\n\tgo test\n")
    lane = _verified(tmp_path, _lane())
    (tmp_path / "Makefile").write_text("V1 := 1\nV2 := 2\nV3 := 3\nintegration:\n\tgo test\n")
    assert stale_files(tmp_path, lane) == ["Makefile"]


def test_stale_files_allows_overreport_on_unrelated_target(tmp_path):
    """【刻意的多报】改了 Makefile 里【别的】target 也会报。

    多报代价 = 重跑一次 smoke；消除多报代价 = 300 行 make 解析器。
    方向反了 —— 防漏宁可多报〔A21〕。
    """
    _seed(tmp_path, "integration:\n\tgo test\n\nlint:\n\tgo vet\n")
    lane = _verified(tmp_path, _lane())
    (tmp_path / "Makefile").write_text("integration:\n\tgo test\n\nlint:\n\tgo vet ./...\n")
    assert stale_files(tmp_path, lane) == ["Makefile"], "多报是刻意的，不是 bug"


def test_stale_files_reports_deleted_file(tmp_path):
    """文件被删 → MUST 报失配，MUST NOT 抛异常（lint 要能跑完其余检查）。"""
    _seed(tmp_path, "integration:\n\tgo test\n")
    lane = _verified(tmp_path, _lane())
    (tmp_path / "smoke_test.go").unlink()
    assert stale_files(tmp_path, lane) == ["smoke_test.go"]


def test_stale_files_path_escape_still_raises(tmp_path):
    """路径逃逸是【安全问题】，MUST 冒泡 —— 不能和「文件没了」混为一谈被吞掉。"""
    lane = _lane()
    lane["verification"]["evidence"]["file_digests"] = {"../../etc/passwd": "deadbeef"}
    with pytest.raises(PathEscape):
        stale_files(tmp_path, lane)


def test_stale_files_no_evidence_means_no_digests(tmp_path):
    """planned 泳道（没验证过）—— 无 file_digests ⇒ 无从比对 ⇒ 空。

    spec：planned 不核验命令出处。
    """
    assert stale_files(tmp_path, _lane()) == []


def test_stale_files_complex_makefile_never_raises(tmp_path):
    """A21 守卫：失配检测路径同样不碰 make 语法。"""
    _seed(tmp_path)
    lane = _verified(tmp_path, _lane())
    assert stale_files(tmp_path, lane) == []
    (tmp_path / "Makefile").write_text(COMPLEX_MAKEFILE + "\nextra:\n\t@true\n")
    assert stale_files(tmp_path, lane) == ["Makefile"]
