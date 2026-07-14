"""出处锚与验证证据的时效锚。

【A21 · 本模块 MUST 零 make 知识】

digest 一律 = sha256(文件原始字节)，所有文件类型一视同仁，零规范化。

MUST NOT 在这里加：
  - GNU make 解析（按 selector 重定位 target / 提取 recipe body）
  - 「target 存在性」正则
  - 任何 normalize()

【为什么】GNU make 的语法面无界（ifeq / define / 双冒号 / 模式规则 / 续行 /
内联 ; / target-specific 变量 …）。手搓解析器必然带一堆「语法不支持」的罢工
分支，而它罢工一次就击穿本 skill 的核心承诺——「不管什么项目，都能给用户一份
三层测试与验证的框架」。前一版就是这么长到 562 行、留下 7 个罢工分支的：每轮
review 都挖出一个新的语法角落，补丁循环从不收敛。

【为什么 MUST NOT 用行号】：source: "Makefile:11-14" + lint「查那行存不存在」——
「第 11-14 行存不存在」对任何长度 >=14 行的文件【恒为真】。这是设计好的假绿。
整文件字节 digest 天然覆盖它（插三行 ⇒ 字节变 ⇒ 失配）。

【「target 存在且能跑」谁来保证】
  - selector 拼错 / target 不存在
        → verify-lane 真 fork 跑 `make <selector>`
        → make 报 "No rule to make target" → exit != 0
        → 泳道进不了 verified。
        make 自己解释自己的语法 —— 100% 覆盖，零解析器，零维护。
  - target 后来被删 / 改名
        → Makefile 字节变了 → file_digests 失配 → lint 报「已改动，请重跑」。

一般化规则：机械层想知道「某个 make/shell/语言构造是什么意思」，正解是让那个
工具自己回答（真跑一遍 / make -n），MUST NOT 手搓解析器去猜。本 skill 的核心
机制恰好就是「尽可能跑一遍确认」—— 跑一遍，就是最强的解析器。

【时效锚的诚实边界】file_digests 覆盖 source.file + smoke + 显式声明的
fixtures[]，不覆盖被测实现（覆盖它需跨语言 import 图静态分析，零依赖做不到——
07 附录 A19）。故 verified 是 `verified-at <sha>`：一次历史执行的记录，不是
「当前状态的绿灯」。业务代码一改，那个绿灯就在说谎。

命令字符串本身的时效锚是 evidence.method_at_verify（A21 面治补口，由
devenv_schema 校验）—— 本模块只管文件。

【失配 = 提醒，不是抓贼】允许多报：改了 Makefile 里【别的】target 也会触发。
刻意如此 —— 多报的代价是重跑一次 smoke，消除多报的代价是 300 行解析器。
防漏宁可多报。
"""
import hashlib

from devenv_paths import contain

__all__ = ["file_digest", "lane_file_digests", "stale_files"]


def file_digest(root, rel):
    """sha256(文件原始字节)。零规范化 —— 所有文件类型一视同仁。

    零规范化不只是「够用」，它比按文件类型分治【严格更强且不可能踩错】：
    分治规则（Makefile 剥空白保 tab / YAML 原始字节）之所以存在，纯粹是因为要
    提取 recipe body 才会引入缩进噪声。不提取 ⇒ 无噪声 ⇒ 无需 normalize ⇒
    「一个通用 normalize() 把两份缩进不同、语义不同的 YAML 算出同一 digest」这个
    假绿【在结构上不可能发生】。

    raise PathEscape —— 路径逃逸（安全问题，MUST 冒泡到调用方）
    raise OSError    —— 文件不存在 / 是目录 / 不可读（调用方按语义处理）
    """
    return hashlib.sha256(contain(root, rel).read_bytes()).hexdigest()


def _tracked_paths(lane):
    """本泳道时效锚覆盖的文件清单（相对路径，去重排序）。"""
    paths = set()

    source = lane.get("source") or {}
    src_file = source.get("file")
    # "-" = toolchain 类出处（如 `go test ./...`），没有对应的出处文件
    if src_file and src_file != "-":
        paths.add(src_file)

    smoke = lane.get("smoke")
    if smoke:
        paths.add(smoke)

    paths.update(lane.get("fixtures") or [])
    return sorted(paths)


def lane_file_digests(root, lane):
    """{rel_path: sha256} —— 写进 evidence.file_digests 的内容。

    只由【执行者本人】在产出证据时调用（verify-lane / confirm-lane）。
    """
    return {rel: file_digest(root, rel) for rel in _tracked_paths(lane)}


def stale_files(root, lane):
    """返回失配的文件清单（排序）。空列表 = 未失配。

    lint 据此报「验证证据已过期：<file> 已改动，请重跑」。

    文件被删 / 变成目录 → 算失配，MUST NOT 抛异常（lint 要能跑完其余检查）。
    路径逃逸 → PathEscape 照常冒泡（那是安全问题，不是「文件没了」）。
    """
    verification = lane.get("verification") or {}
    evidence = verification.get("evidence") or {}
    recorded = evidence.get("file_digests") or {}
    if not recorded:
        # planned 泳道：没验证过 ⇒ 无从比对（spec：planned 不核验命令出处）
        return []

    stale = []
    for rel, want in sorted(recorded.items()):
        try:
            got = file_digest(root, rel)
        except OSError:
            stale.append(rel)  # 文件没了 / 不可读 = 失配
            continue
        if got != want:
            stale.append(rel)
    return stale
