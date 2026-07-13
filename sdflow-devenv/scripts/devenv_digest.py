"""出处锚与验证证据的时效锚 —— digest 按文件类型分治。

【为什么 MUST NOT 用行号】：source: "Makefile:11-14" + lint「查那行存不存在」——
「第 11-14 行存不存在」对任何长度 >=14 行的文件【恒为真】。用户在顶部插三行 ⇒ 锚点
全部错位、lint 全绿、命令表继续声称出自那四行。这是【设计好的假绿】。

【为什么 MUST 按文件类型分治】（round-3 领域镜实证）：
  Makefile recipe —— tab 有语法意义，必须保留；空白/空行是噪声，可以剥
  YAML/JSON/lockfile —— 【行首缩进本身就是语义】。若套用 Makefile 的「剥去行首空白」，
    两份缩进不同、语义完全不同的 YAML 会算出同一个 digest ⇒ 与「行号锚」同构的假绿。
  ⇒ 除 Makefile recipe 外，一律【对原始字节 sha256】，不做任何规范化。

【诚实边界（R-DATA / 全局约束 #3）】：method_digest 只是「自记录以来这段内容没变过」
的时效锚，不是「这个方法真的跑过 / 真的有效」的通行证。它的覆盖范围MUST NOT 包含
被测实现代码本身——lane.status == "verified" 的意思仅仅是 verified-at <sha>（一条
历史执行记录），不是「当前状态是绿的」。任何注释/文档措辞都不得暗示后者。
"""
import hashlib
import re

from devenv_paths import contain

# Makefile target 行：行首是合法 target 名字符（不含空白），随后紧跟单/双冒号，
# 且冒号后不是 `=`（用来排除 `VAR := value` / `VAR=value` 这类赋值行）。
# group(1) = target 名，group(2) = ":" 或 "::"
_TARGET_RE = re.compile(r"^([A-Za-z0-9_.\-/%$()]+)\s*(::?)(?!=)")

# target-specific 变量赋值行的「疑似」判据：冒号后紧跟 `IDENT = / := / += / ?= value`。
# 这与「target: 一堆前置依赖」在字面上无法可靠区分（Make 自身的语法也是靠语义消歧），
# parser 不猜——命中就拒绝。
_ASSIGN_REMAINDER_RE = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_]*\s*[:+?]?=(?!=)")


class DigestInputInvalid(Exception):
    """method_digest / find_make_target 的入参形状不对。

    source / smoke / fixtures / method 全是模型自由填的字段——用前必须验类型，
    不能让 AttributeError/TypeError 逃出契约（同 devenv_schema 的坏输入纪律）。
    """


class MakefileSelectorError(Exception):
    """selector 重定位失败的公共基类——调用方可用它统一 catch。"""


class MakeTargetNotFound(MakefileSelectorError):
    """target 未找到 / Makefile 不存在 / selector 为空——fail-closed，不当作「空 recipe」。

    MUST NOT 静默退化为空字符串再算 digest：那样得到的是「hash(空字符串)」这个恒定
    值，往后 recipe 真的被改了也测不出来——与「行号锚」同构的假绿，只是换了个壳。
    """


class MakefileUnsupported(MakefileSelectorError):
    """命中已知、拒绝猜测的 Makefile 语法（双冒号规则 / 多 target 一行 /
    target-specific 变量赋值行等）。parser 宁可显式拒绝，也不猜错误地少扫或多扫。
    """


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _require_str(v, field):
    if not isinstance(v, str):
        raise DigestInputInvalid(f"{field} 须为 string，实际是 {type(v).__name__}")
    return v


def _require_dict_or_none(v, field):
    if v is not None and not isinstance(v, dict):
        raise DigestInputInvalid(f"{field} 须为 object 或 None，实际是 {type(v).__name__}")
    return v


def _require_list_or_none(v, field):
    if v is not None and not isinstance(v, list):
        raise DigestInputInvalid(f"{field} 须为数组或 None，实际是 {type(v).__name__}")
    return v


def find_make_target(text, selector):
    """按 target 名重定位，返回 (start_line, end_line, recipe_text) 或 None（未找到）。

    行号【仅供 render 时生成给人看】，不作真相——真相是 recipe 的 digest（顶部插行
    不影响返回内容，见 test_selector_survives_line_shift）。

    recipe = target 行之后、所有以 tab 开头的行（Make 的语法硬要求：recipe 行必须
    tab 开头，空格不行），直到遇到第一个非 tab 开头的非空行为止；recipe 内部的空行
    只要后面还有 tab 行就算内部空行，不算结束。

    遇到已知无法可靠区分语义的语法（双冒号规则 / 多 target 一行 / target-specific
    变量赋值行）且命中 selector 时，raise MakefileUnsupported——不猜、不当哑巴。
    """
    if not isinstance(text, str):
        raise DigestInputInvalid(f"text 须为 str，实际是 {type(text).__name__}")
    if not isinstance(selector, str):
        raise DigestInputInvalid(f"selector 须为 str，实际是 {type(selector).__name__}")

    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith(("\t", " ", "#")):
            continue

        m = _TARGET_RE.match(line)
        if m:
            name, colon = m.group(1), m.group(2)
            if name != selector:
                continue
            if colon == "::":
                raise MakefileUnsupported(
                    f"target {selector!r} 使用双冒号规则（`{line.strip()}`）——"
                    f"同一 target 可能有多条独立规则块，单遍首匹配扫描会漏掉其余块，"
                    f"parser 不支持，fail-closed 拒绝猜测"
                )
            remainder = line[m.end():]
            if _ASSIGN_REMAINDER_RE.match(remainder):
                raise MakefileUnsupported(
                    f"target {selector!r} 疑似 target-specific 变量赋值行"
                    f"（`{line.strip()}`）——与「target 定义 + 内联赋值型前置依赖」在"
                    f"字面上无法可靠区分，parser 不支持，fail-closed 拒绝猜测"
                )

            j = i + 1
            recipe = []
            while j < len(lines):
                ln = lines[j]
                if ln.startswith("\t"):
                    recipe.append(ln)
                    j += 1
                elif ln.strip() == "":
                    # 空行：可能是 recipe 内部的空行，也可能是 recipe 结束。
                    # 向前看：若后面还有 tab 行则算 recipe 内部，否则结束。
                    k = j
                    while k < len(lines) and lines[k].strip() == "":
                        k += 1
                    if k < len(lines) and lines[k].startswith("\t"):
                        recipe.extend(lines[j:k])
                        j = k
                    else:
                        break
                else:
                    break
            return (i + 1, j, "".join(recipe))

        # 严格单-target 形态没匹配上：可能是多 target 一行（`a b: dep`）之类
        # parser 不认的规则头。只在它明确命中我们要找的 selector 时才拒绝——
        # 无关行放过，不让别的 target 的定位也被这类噪声炸掉。
        head = line.split("#", 1)[0]
        if ":" in head:
            before_colon = head.split(":", 1)[0]
            names = before_colon.split()
            if selector in names:
                raise MakefileUnsupported(
                    f"target {selector!r} 出现在 parser 不支持的规则头"
                    f"（`{line.strip()}`：多 target 一行 / 语法不明）——"
                    f"fail-closed 拒绝猜测"
                )
    return None


def digest_make_recipe(recipe_text):
    """Makefile recipe 的规范化 digest。

    剥：行尾空白 · 纯空行（都是噪声，跨环境/编辑器常见的无意义抖动）
    保留：【tab 缩进】（recipe 行的硬语法，抹掉即改变「这是不是一行 recipe」本身）
         · 【注释】（可能载有语义，例如临时禁用某条命令）
    """
    if not isinstance(recipe_text, str):
        raise DigestInputInvalid(
            f"recipe_text 须为 str，实际是 {type(recipe_text).__name__}"
        )
    out = []
    for ln in recipe_text.splitlines():
        stripped = ln.rstrip()
        if not stripped.strip():
            continue                       # 纯空行：噪声
        out.append(stripped)               # 保留行首 tab，只剥行尾
    return _sha("\n".join(out).encode("utf-8"))


def digest_file(root, rel):
    """按文件类型分派。除 Makefile recipe 规范化规则外，一律【原始字节 sha256】。

    非 UTF-8 / 二进制内容：本函数默认分支直接对字节 sha256，天然不需要解码，不会崩。
    Makefile 分支需要按行解析，遇到非法 UTF-8 用 errors="replace" 容错，不崩、不猜。
    """
    p = contain(root, rel)
    raw = p.read_bytes()
    name = p.name.lower()
    if name == "makefile" or name.endswith(".mk"):
        return digest_make_recipe(raw.decode("utf-8", errors="replace"))
    # YAML / JSON / lockfile / .go / .py / 一切其余：逐字节，零规范化
    # （行首缩进/空白在这些格式里可能就是语义，不能替它们决定「哪些空白是噪声」）
    return _sha(raw)


def method_digest(root, method, smoke, fixtures, source):
    """验证证据的时效锚。

    覆盖：验证命令字符串 + Makefile recipe body（若 source 是 make-target）+
    smoke 文件 + lane 显式声明的 fixtures。

    【MUST NOT 追求覆盖「smoke 可达的所有 harness/fixture」】——「可达」需要跨语言
    import 图静态分析，零依赖做不到。用【显式声明】代替静态分析：没声明的 fixture
    不在覆盖范围内，这是有意的设计边界，不是遗漏。

    【诚实边界】：本函数证明的只是「自记录以来，method + source + smoke + 声明的
    fixtures 这几段内容没变过」。它不证明、也不尝试证明「这个方法真的跑过」「跑了会
    绿」「覆盖了它声称覆盖的东西」——那些是 verified 记录本身要如实承认覆盖不到的
    残余，机械层在此止步。
    """
    method = _require_str(method, "method")
    source = _require_dict_or_none(source, "source")
    fixtures = _require_list_or_none(fixtures, "fixtures") or []
    if smoke is not None:
        smoke = _require_str(smoke, "smoke")

    parts = [("method", method.encode("utf-8"))]

    if source and source.get("file"):
        file_rel = _require_str(source.get("file"), "source.file")
        src_path = contain(root, file_rel)
        kind = source.get("kind")

        if kind == "make-target":
            selector = source.get("selector")
            if not isinstance(selector, str) or not selector.strip():
                raise MakeTargetNotFound(
                    f"make-target 声明缺 selector（须为非空字符串）: {source!r}"
                )
            if not src_path.exists():
                raise MakeTargetNotFound(f"Makefile 不存在: {file_rel}")
            text = src_path.read_text(encoding="utf-8", errors="replace")
            loc = find_make_target(text, selector)
            if loc is None:
                raise MakeTargetNotFound(
                    f"target 未找到: selector={selector!r} in {file_rel} —— "
                    f"MUST NOT 悄悄退化为「空 recipe」的稳定 digest"
                )
            parts.append(("recipe", digest_make_recipe(loc[2]).encode()))
        else:
            # 非 make-target：整份文件走 digest_file 的按类型分派（不存在时
            # digest_file 里的 read_bytes() 天然抛 FileNotFoundError，已是
            # 明确异常，不需要在这里再包一层）。
            parts.append(("source", digest_file(root, file_rel).encode()))

    if smoke:
        parts.append(("smoke", digest_file(root, smoke).encode()))

    checked_fixtures = [_require_str(f, "fixtures[]") for f in fixtures]
    for f in sorted(checked_fixtures):
        parts.append((f"fixture:{f}", digest_file(root, f).encode()))

    h = hashlib.sha256()
    for label, blob in parts:
        h.update(label.encode("utf-8"))
        h.update(b"\x00")
        h.update(blob)
        h.update(b"\x00")
    return h.hexdigest()
