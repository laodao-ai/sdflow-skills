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

# 变量赋值行的判据：可选 `export` 前缀 + `IDENT = / := / += / ?= value`。
# 两处复用：① target-specific 变量赋值（`target: VAR = value`，判 target 冒号后的
# remainder）；② 整行变量赋值（`VAR := value`，判整行——用来把它从「多 target 一行」
# 的兜底分支里摘出去，见 find_make_target 的 Important bug 修复）。
# 这与「target: 一堆前置依赖」在字面上无法可靠区分的部分（target-specific 用法），
# Make 自身的语法也是靠语义消歧，parser 不猜——命中就拒绝（MakefileUnsupported）。
_ASSIGN_REMAINDER_RE = re.compile(
    r"^\s*(?:export\s+)?[A-Za-z_][A-Za-z0-9_]*\s*[:+?]?=(?!=)"
)


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


def _is_continuation_line(raw_line):
    """物理行（含结尾换行）是否以续行符 `\\` 结尾（Make 的行续接语法）。

    `\\\\`（转义反斜杠，字面双斜杠）不算续行——保守判断，宁可当作「不续行」，
    真遇到这种字面反斜杠的怪 Makefile，后续解析大概率还是会因为找不到 recipe
    而走到别的 fail-closed 分支，不会静默出错。
    """
    stripped = raw_line.rstrip("\n").rstrip("\r")
    return stripped.endswith("\\") and not stripped.endswith("\\\\")


def _find_toplevel_semicolon(remainder):
    """在 target 行「冒号后的剩余文本」（可能已跨多个续行拼接）里找【结束依赖列表、
    开始内联 recipe】的那个 `;`——即括号/引号嵌套深度为 0 的第一个 `;`
    （real GNU make 验证：`foo: a;b` 里 `;` 前是依赖 "a"、`;` 后是 recipe "b"，
    第一个顶层 `;` 之后的原样文本就是 recipe 首行，不会再被二次拆分）。

    返回 (index, ambiguous)：
      (int, False)  —— 找到，index 是该 `;` 在 remainder 里的位置
      (None, False) —— 没有顶层 `;`（正常：没有内联 recipe）
      (None, True)  —— 遇到未闭合的引号 / `$()` `${}` 嵌套，无法安全判定，
                        调用方必须 fail-closed（MUST NOT 猜一个位置）
    """
    depth = 0
    quote = None
    i = 0
    n = len(remainder)
    while i < n:
        c = remainder[i]
        if quote:
            if c == quote:
                quote = None
            i += 1
            continue
        if c in ("'", '"'):
            quote = c
            i += 1
            continue
        if c == "$" and i + 1 < n and remainder[i + 1] in "({":
            depth += 1
            i += 2
            continue
        if c in ")}" and depth > 0:
            depth -= 1
            i += 1
            continue
        if c == ";" and depth == 0:
            return i, False
        i += 1
    if quote is not None or depth != 0:
        return None, True
    return None, False


def find_make_target(text, selector):
    """按 target 名重定位，返回 (start_line, end_line, recipe_text) 或 None（未找到）。

    行号【仅供 render 时生成给人看】，不作真相——真相是 recipe 的 digest（顶部插行
    不影响返回内容，见 test_selector_survives_line_shift）。

    recipe 的来源（Make 语义，均已用 GNU make 实测核对）：
      - 内联 `;` recipe：冒号后第一个【顶层】`;`（不在 `$()/${}` 嵌套或引号内）
        之后的文本就是 recipe 首行；
      - 该行之后所有以 tab 开头的行也属于同一 recipe（tab 是 Make 的硬语法要求）；
      - 内联 recipe 首行 / 任意 tab 行若以 `\\` 续行，下一物理行【无论是否 tab
        开头】都仍属于该 recipe（real make 验证：续行只看有没有转义换行符，
        与「新逻辑行必须 tab 开头」的规则无关）；
      - target 定义行本身（冒号前后的依赖列表）也可能用 `\\` 续行成多物理行，
        必须先拼成一个逻辑行再判定内联 `;` / recipe 起点，否则续行的第二行会被
        误当成「非 tab 非空行」提前截断扫描，把真实存在的 recipe 静默判成空。
      - recipe 内部的空行只要后面还有 tab 行就算内部空行，不算结束。

    同名 target 在文件中出现多次时（Make 允许，语义是「依赖合并 + 后一个非空
    recipe 覆盖前面」——real make 实测：多个非空 recipe 会 warning 后用最后一个
    生效，多个空 recipe 定义不会互相覆盖）：本 parser 不猜「哪个是最后生效的」，
    只在【明确无歧义】时才给出结果——全文只有 0 或 1 处非空 recipe（其余定义都是
    纯依赖声明）时直接用那一处；出现 ≥2 处内容不同的非空 recipe 时 fail-closed
    raise MakefileUnsupported。

    遇到已知无法可靠区分语义的语法（双冒号规则 / 多 target 一行 / target-specific
    变量赋值行 / 无法判定嵌套深度的内联 `;` / 续行符后文件截断 / 同名 target 多处
    冲突 recipe）且命中 selector 时，raise MakefileUnsupported——不猜、不当哑巴，
    MUST NOT 静默退化为「空 recipe」。
    """
    if not isinstance(text, str):
        raise DigestInputInvalid(f"text 须为 str，实际是 {type(text).__name__}")
    if not isinstance(selector, str):
        raise DigestInputInvalid(f"selector 须为 str，实际是 {type(selector).__name__}")

    lines = text.splitlines(keepends=True)
    n = len(lines)
    matches = []
    i = 0
    while i < n:
        line = lines[i]
        if line.startswith(("\t", " ", "#")):
            i += 1
            continue

        m = _TARGET_RE.match(line)
        if m:
            name, colon = m.group(1), m.group(2)
            if name != selector:
                i += 1
                continue
            if colon == "::":
                raise MakefileUnsupported(
                    f"target {selector!r} 使用双冒号规则（`{line.strip()}`）——"
                    f"同一 target 可能有多条独立规则块，单遍首匹配扫描会漏掉其余块，"
                    f"parser 不支持，fail-closed 拒绝猜测"
                )

            # 拼接 target 行头本身的续行（`foo: dep1 \` + 下一行 `dep2`），
            # 否则续行的第二行会被 recipe 扫描误判为「非 tab 非空行」而提前
            # 截断——这正是本次修复要根除的「静默空 recipe」同款病。
            header_lines = [line]
            j = i
            while _is_continuation_line(header_lines[-1]):
                j += 1
                if j >= n:
                    raise MakefileUnsupported(
                        f"target {selector!r} 的规则头以续行符 `\\` 结尾但文件"
                        f"在此截断——fail-closed 拒绝猜测"
                    )
                header_lines.append(lines[j])
            remainder = "".join(header_lines)[m.end():]

            if _ASSIGN_REMAINDER_RE.match(remainder):
                raise MakefileUnsupported(
                    f"target {selector!r} 疑似 target-specific 变量赋值行"
                    f"（`{line.strip()}`）——与「target 定义 + 内联赋值型前置依赖」在"
                    f"字面上无法可靠区分，parser 不支持，fail-closed 拒绝猜测"
                )

            semi_idx, ambiguous = _find_toplevel_semicolon(remainder)
            if ambiguous:
                raise MakefileUnsupported(
                    f"target {selector!r} 的规则头里 `;` / 引号 / `$()`/`${{}}` "
                    f"嵌套无法安全判定（`{line.strip()}`）——fail-closed 拒绝猜测，"
                    f"以防误判内联 recipe 的边界"
                )

            recipe = []
            scan_from = j + 1
            if semi_idx is not None:
                # 冒号后第一个顶层 `;` 之后的文本就是内联 recipe 首行（Make
                # 标准语法，foo: ; echo hi 与 foo:\n\techo hi 语义等价）——
                # 这是本次修复的 Critical bug：以前这段文本被完全忽略，
                # 两份内容不同的内联 recipe 会算出同一个（空）digest。
                recipe.append(remainder[semi_idx + 1:])
                while recipe and _is_continuation_line(recipe[-1]):
                    if scan_from >= n:
                        raise MakefileUnsupported(
                            f"target {selector!r} 的内联 recipe 以续行符 `\\` "
                            f"结尾但文件在此截断——fail-closed 拒绝猜测"
                        )
                    recipe.append(lines[scan_from])
                    scan_from += 1

            k = scan_from
            while k < n:
                ln = lines[k]
                if ln.startswith("\t"):
                    recipe.append(ln)
                    k += 1
                    # recipe 行本身的续行：下一物理行【无论是否 tab 开头】都仍
                    # 属于同一条 recipe 命令（real make 实测确认）。
                    while recipe and _is_continuation_line(recipe[-1]):
                        if k >= n:
                            raise MakefileUnsupported(
                                f"target {selector!r} 的 recipe 行以续行符 `\\` "
                                f"结尾但文件在此截断——fail-closed 拒绝猜测"
                            )
                        recipe.append(lines[k])
                        k += 1
                elif ln.strip() == "":
                    # 空行：可能是 recipe 内部的空行，也可能是 recipe 结束。
                    # 向前看：若后面还有 tab 行则算 recipe 内部，否则结束。
                    p = k
                    while p < n and lines[p].strip() == "":
                        p += 1
                    if p < n and lines[p].startswith("\t"):
                        recipe.extend(lines[k:p])
                        k = p
                    else:
                        break
                else:
                    break

            matches.append((i + 1, k, "".join(recipe)))
            # 跳过本次已消费的行（含可能不以 tab 开头的续行 recipe 内容）——
            # 不跳过的话，续行 recipe 里若恰好含 `:` 字面文本，会被外层循环
            # 误当成又一个规则头去扫描。
            i = k
            continue

        # 严格单-target 形态没匹配上：可能是变量赋值行（`VAR := value`），
        # 也可能是多 target 一行（`a b: dep`）之类 parser 不认的规则头。
        head = line.split("#", 1)[0]
        if _ASSIGN_REMAINDER_RE.match(head):
            # Important bug 修复：整行变量赋值（如 `test := go test ./...`）
            # 曾被下面的「冒号 + 空白分词」兜底逻辑误判成「多 target 一行」，
            # 对同名变量+target 的常见 Makefile（小写变量命名习惯）造成误伤。
            i += 1
            continue
        if ":" in head:
            before_colon = head.split(":", 1)[0]
            names = before_colon.split()
            if selector in names:
                raise MakefileUnsupported(
                    f"target {selector!r} 出现在 parser 不支持的规则头"
                    f"（`{line.strip()}`：多 target 一行 / 语法不明）——"
                    f"fail-closed 拒绝猜测"
                )
        i += 1

    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]

    nonempty = [mm for mm in matches if mm[2].strip() != ""]
    if len(nonempty) > 1:
        distinct_recipes = {mm[2] for mm in nonempty}
        if len(distinct_recipes) == 1:
            # 内容完全相同的重复定义——用哪一处都不影响 digest，不算冲突。
            return nonempty[-1]
        raise MakefileUnsupported(
            f"target {selector!r} 在文件中出现 {len(matches)} 次，其中 "
            f"{len(nonempty)} 处 recipe 非空且内容不同——Make 语义是「后一个非空 "
            f"recipe 覆盖前面」，但 parser 不猜哪个是最终生效版本，"
            f"fail-closed 拒绝猜测"
        )
    if len(nonempty) == 1:
        # 多次出现但只有一处非空 recipe（其余是纯依赖声明）——real make 实测：
        # 无 recipe 的重复定义不会清空已有 recipe，直接用那唯一的非空版本。
        return nonempty[0]
    # 全部出现处 recipe 都是空的——合法的「无命令 target」（如 .PHONY 聚合器）。
    return matches[0]


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
