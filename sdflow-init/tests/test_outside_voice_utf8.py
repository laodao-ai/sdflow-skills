"""守 outside-voice.sh 截断的 UTF-8 字符边界安全〔R1 · design D1〕。

【为什么需要这个测试】
`render_prompt` 的 200KB 截断用 `head -c` / `tail -c` 在【字节】边界切——一个多字节
字符被劈成两半，送给跨模型 runner 时非法字节可致【整个 prompt 被拒收】：voice 静默失效。
判据是【头段与尾段各自】都能严格解码，不是「拼起来合法」——两半被分别嵌进 prompt 的
不同位置（中间夹 TRUNCATED 横幅），从不相邻。

【语法面·基准 ⑤】
只认 UTF-8：序列 ≤4 字节、continuation 字节形态确定（0x80-0xBF）⇒ 【有界】∴ 可手写回扫。
MUST NOT 演化成编码检测/嗅探。非 UTF-8 字节的行为断言在
test_non_utf8_lead_bytes_follow_utf8_semantics_not_sniffing。
"""
import os
import platform
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HELPER = REPO / "sdflow-init" / "assets" / "hack" / "outside-voice.sh"

# 混合语料：ASCII / 2 字节拉丁 / 3 字节 CJK / 4 字节 emoji —— 每类多字节宽度都出现，
# 才能覆盖「切在序列第 1/2/3 个字节之后」的全部残缺形态。
MIXED = ("hello ASCII 中文汉字 café 😀🎉 more text 更多中文 ñ 🚀 tail\n" * 3).encode("utf-8")
ASCII_ONLY = (b"plain ascii line with no multibyte at all\n" * 8)


def _write(tmp_path, name, data: bytes) -> Path:
    p = tmp_path / name
    p.write_bytes(data)
    return p


def _scan(corpus: Path, size: int, *, mutate: bool = False):
    """跑一遍 bash，把【所有】切点 k 的 (head_trim, tail_skip) 一次性取回。

    mutate=True ⇒ source 后把两个回扫函数改成恒返回 0（= 退化回按字节切），
    用于变异验证：证明下面的断言真的由回扫承重，而不是恰好为真。
    """
    override = (
        "utf8_head_trim() { echo 0; }\nutf8_tail_skip() { echo 0; }\n" if mutate else ""
    )
    script = textwrap.dedent(f"""\
        set -u
        _OV_TEST_LIB_ONLY=1 . {HELPER!s}
        {override}
        for (( k=1; k<{size}; k++ )); do
          printf '%s %s %s\\n' "$k" \\
            "$(utf8_head_trim {corpus!s} "$k")" "$(utf8_tail_skip {corpus!s} "$k")"
        done
        """)
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr
    out = {}
    for line in r.stdout.splitlines():
        k, trim, skip = (int(x) for x in line.split())
        out[k] = (trim, skip)
    assert len(out) == size - 1
    return out


def _both_halves_decode(data: bytes, k: int, trim: int, skip: int):
    """返回 (头段 ok?, 尾段 ok?) —— 严格模式解码，errors 一律抛。"""
    head = data[: k - trim]
    tail = data[len(data) - k + skip :]
    ok_h = ok_t = True
    try:
        head.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        ok_h = False
    try:
        tail.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        ok_t = False
    return ok_h, ok_t


# ── ⭐ 核心：全切点扫描 ──────────────────────────────────────────────────────

def test_every_cut_offset_yields_two_valid_utf8_halves(tmp_path):
    """混合语料上，【每一个】切点的头段与尾段分别严格解码成功，失败数为 0。"""
    corpus = _write(tmp_path, "mixed.md", MIXED)
    table = _scan(corpus, len(MIXED))
    failures = [
        k for k, (trim, skip) in table.items()
        if not all(_both_halves_decode(MIXED, k, trim, skip))
    ]
    assert failures == [], f"{len(failures)}/{len(table)} 个切点产出非法 UTF-8: {failures[:20]}"


def test_mutation_constant_zero_backscan_turns_the_scan_red(tmp_path):
    """⭐ 变异验证：回扫恒返回 0（退化回按字节切）⇒ 上面的扫描断言必须转红。

    没有这一条，「全绿」可能只是语料恰好没被切中——那测试不承重。
    """
    corpus = _write(tmp_path, "mixed.md", MIXED)
    table = _scan(corpus, len(MIXED), mutate=True)
    failures = [
        k for k, (trim, skip) in table.items()
        if not all(_both_halves_decode(MIXED, k, trim, skip))
    ]
    assert failures, "变异体竟然全绿 —— 该测试不承重，语料需加强"


def test_backscan_never_over_trims(tmp_path):
    """回扫最多退 3 字节（UTF-8 序列 ≤4）—— 防「无脑多切几个字节」蒙混过关。"""
    corpus = _write(tmp_path, "mixed.md", MIXED)
    for k, (trim, skip) in _scan(corpus, len(MIXED)).items():
        assert 0 <= trim <= 3, (k, trim)
        assert 0 <= skip <= 3, (k, skip)


# ── ASCII 零损耗 ────────────────────────────────────────────────────────────

def test_pure_ascii_loses_zero_bytes(tmp_path):
    """纯 ASCII 语料：任何切点都不额外丢弃一个字节。"""
    corpus = _write(tmp_path, "ascii.md", ASCII_ONLY)
    for k, (trim, skip) in _scan(corpus, len(ASCII_ONLY)).items():
        assert (trim, skip) == (0, 0), f"切点 {k} 在纯 ASCII 上丢了字节: trim={trim} skip={skip}"


# ── 基准 ⑤ 边界：只认 UTF-8，不嗅探 ─────────────────────────────────────────

LATIN1 = b"abc\xe9\xff\xfedef ghi\n" * 4   # 14 字节一轮：0xE9 在轮内 offset 3


def test_non_utf8_lead_bytes_follow_utf8_semantics_not_sniffing(tmp_path):
    """⭐ 锁 D1「只认 UTF-8、MUST NOT 演化成嗅探」—— 逐切点 golden，非区间断言。

    【为什么不能只断言 0<=trim<=3】那个区间任何返回 0-3 的实现都能过（含一个完整的
    编码嗅探器）⇒ 锁不住 D1。这里改成【逐切点 golden 序列】，行为一变即红。

    【golden 从哪来 —— 不是"跑一遍抄下来"，是 UTF-8 规则推出来的】
    语料每 14 字节一轮，0xE9 落在轮内 offset 3。0xE9 是【合法的 3 字节序列首字节】，
    回扫只看首字节形态、不看后续字节是否真构成合法序列（看了就是嗅探）：
      · 切点 k ≡ 4 (mod 14) ⇒ 头段末字节正是 0xE9，avail=1 < len=3 ⇒ trim=1
      · 其余切点末字节非 continuation 且自身完整 ⇒ trim=0
      · 0xFF/0xFE 不在 0x80-0xBF ⇒ 从不被当 continuation 跳过 ⇒ skip 恒 0
    ∴ 「left alone（字节原样保留）」是【假的】——0xE9 处确实退了 1 字节，这正是
    UTF-8 语义的正确结果，不是缺陷。旧测试名与该事实不符，已改名。

    【它真的锁住了嗅探吗】锁住了：一个识别出 Latin-1 的实现会认定"这些都是单字节字符、
    无需回退" ⇒ 全表 trim=0 ⇒ k=4 处断言当场红。
    """
    corpus = _write(tmp_path, "latin1.md", LATIN1)
    table = _scan(corpus, len(LATIN1))
    expected = {k: (1 if k % 14 == 4 else 0, 0) for k in table}
    assert table == expected, {
        k: (got, expected[k]) for k, got in table.items() if got != expected[k]
    }


def test_non_utf8_backscan_never_over_trims(tmp_path):
    """非 UTF-8 语料上回扫仍不越界（≤3）—— 与上面的 golden 互补的粗粒度护栏。"""
    corpus = _write(tmp_path, "latin1.md", LATIN1)
    for k, (trim, skip) in _scan(corpus, len(LATIN1)).items():
        assert 0 <= trim <= 3, (k, trim)
        assert 0 <= skip <= 3, (k, skip)


# ── 测试接缝本身不得成为静默失效面〔I1〕 ────────────────────────────────────

def test_lib_only_seam_is_source_only_and_fails_loud_when_executed(tmp_path):
    """⭐ `_OV_TEST_LIB_ONLY` 从环境泄漏到【执行态】时 MUST fail-loud，MUST NOT 静默 exit 0。

    泄漏路径真实存在（子代理 / CI / 嵌套调用继承 env）。若执行态仍直接 exit 0，
    helper 会产出【0 字节 prompt + exit 0】，调用方读成「成功但无 findings」——
    正是本 change 要消灭的静默失效，出现在治这个病的 change 自己身上。
    """
    ctx = _write(tmp_path, "ctx.md", b"some context\n")
    e = os.environ.copy()
    e["_OV_TEST_LIB_ONLY"] = "1"
    e.pop("SDFLOW_VOICE_RUNNER", None)
    r = subprocess.run(
        ["bash", str(HELPER), "render-prompt", "--context-file", str(ctx)],
        capture_output=True, env=e, timeout=30,
    )
    assert r.returncode == 2, (r.returncode, r.stdout[:200], r.stderr[:400])
    assert b"_OV_TEST_LIB_ONLY" in r.stderr, r.stderr
    assert r.stdout == b"", r.stdout[:200]


def test_lib_only_seam_still_works_when_sourced(tmp_path):
    """接缝在【被 source】时仍只加载函数、不派发命令（正向：函数可驱动、无命令输出）。"""
    script = textwrap.dedent(f"""\
        set -u
        _OV_TEST_LIB_ONLY=1 . {HELPER!s} version
        utf8_head_trim /dev/null 0
        """)
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    # `version` 参数被忽略（未派发）⇒ stdout 只有函数自己的输出
    assert "outside-voice.sh" not in r.stdout, r.stdout
    assert r.stdout.strip() == "0", r.stdout


# ── 端到端：render-prompt 的可观测性 ────────────────────────────────────────

def _run_render(ctx: Path, max_bytes: int):
    e = os.environ.copy()
    e.pop("SDFLOW_VOICE_RUNNER", None)
    e.pop("SDFLOW_VOICE_MODEL", None)
    e["OV_MAX_CONTEXT_BYTES"] = str(max_bytes)
    return subprocess.run(["bash", str(HELPER), "render-prompt", "--context-file", str(ctx)],
                          capture_output=True, env=e, timeout=30)


@pytest.mark.parametrize("max_bytes", list(range(60, 90)))
def test_render_prompt_emits_valid_utf8_when_truncating(tmp_path, max_bytes):
    """端到端：扫一段 OV_MAX_CONTEXT_BYTES 取值（⇒ 一段 half 切点），stdout 恒为合法 UTF-8。"""
    corpus = _write(tmp_path, "mixed.md", MIXED)
    r = _run_render(corpus, max_bytes)
    assert r.returncode == 0, r.stderr
    r.stdout.decode("utf-8", errors="strict")   # 非法即抛 → 红
    assert b"OV_TRUNCATED=true" in r.stderr


def test_stderr_reports_dropped_byte_counts(tmp_path):
    """截断时 stderr 可见【实际丢弃字节数】，且新增输出只有计数、不含 context 正文。"""
    corpus = _write(tmp_path, "mixed.md", MIXED)
    r = _run_render(corpus, 100)
    err = r.stderr.decode("utf-8")
    dropped = [ln for ln in err.splitlines() if ln.startswith("OV_TRUNCATED_DROPPED_BYTES=")]
    backscan = [ln for ln in err.splitlines() if ln.startswith("OV_UTF8_BACKSCAN_DROPPED=")]
    assert len(dropped) == 1 and len(backscan) == 1, err
    total = int(dropped[0].split("=")[1])
    assert total == len(MIXED) - 100 + int(backscan[0].split("=")[1])
    # 正文不得出现在 stderr（该内容未经出境扫描）
    for probe in ("hello ASCII", "更多中文", "😀"):
        assert probe not in err, f"stderr 泄漏 context 正文: {probe}"


def test_ascii_truncation_reports_zero_backscan_loss(tmp_path):
    corpus = _write(tmp_path, "ascii.md", ASCII_ONLY)
    r = _run_render(corpus, 100)
    err = r.stderr.decode("utf-8")
    assert "OV_UTF8_BACKSCAN_DROPPED=0" in err, err
    assert f"OV_TRUNCATED_DROPPED_BYTES={len(ASCII_ONLY) - 100}" in err, err


def test_secret_scan_still_covers_whole_file_before_truncation(tmp_path):
    """密钥扫描覆盖面未缩小：密钥落在【被截断丢弃的中段】仍拒发 exit 3。"""
    filler = b"x" * 400
    data = filler + b"\nkey=AKIA" + b"A" * 16 + b"\n" + filler
    corpus = _write(tmp_path, "leak.md", data)
    r = _run_render(corpus, 100)
    assert r.returncode == 3, (r.returncode, r.stderr)
    assert b"secret-hit" in r.stderr


# ── 接缝：stderr 契约通道不被污染 + 降级路径不静默〔S1/S2/S3〕 ──────────────
#
# stderr 是被两层 SKILL.md 解析的【契约通道】（truncated 取 helper stderr 的 OV_TRUNCATED）。
# 任何裸重定向失败信息混进去 = 破坏契约。这三条锁的是 re-review 实跑抓出的三个接缝洞。


def _source_and_run(snippet: str, cwd: Path):
    """在 source 态驱动脚本内部函数（不走命令派发）。"""
    script = f"_OV_TEST_LIB_ONLY=1 . {HELPER!s}\n{snippet}\n"
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                          cwd=str(cwd), timeout=30)


def test_tail_skip_unreadable_file_does_not_pollute_stderr_contract(tmp_path):
    """〔S1〕`2>/dev/null` MUST 排在 `< "$file"` 【之前】。

    bash 从左到右处理重定向：写成 `wc -c < "$f" 2>/dev/null` 时 `< "$f"` 先失败，报错由
    shell 自身打到【尚未被重定向】的 stderr ⇒ `bash: ...: Permission denied` 原样进契约通道。
    变异验证：把源里的顺序换回去，本用例即红。

    〔F-新1〕stdout 断言从 "0" 改为 ""：`wc -c` 失败（这里由 chmod 000 触发）与「合法结论
    不用跳过」此前同形（旧实现均落 echo 0）——那正是 F-新1 的病灶之一。修复后取字节失败
    统一输出空串，见 test_tail_skip_reports_failure_not_zero_when_wc_fails 的专项覆盖。
    """
    f = tmp_path / "noperm.txt"
    f.write_bytes(b"hello world")
    f.chmod(0o000)
    try:
        r = _source_and_run(f'utf8_tail_skip "{f}" 4', tmp_path)
    finally:
        f.chmod(0o644)
    assert r.stderr == "", f"契约通道被污染: {r.stderr!r}"
    assert r.stdout.strip() == "", (
        f"wc 失败时不得输出'0'（与合法结论同形，F-新1 复发）: {r.stdout!r}"
    )


def test_render_prompt_size_read_failure_is_fail_loud_not_silent_full_dump(tmp_path):
    """〔S2〕size 取不到 ⇒ exit 2，MUST NOT 兜底成 0。

    size 是【截断判据本身】：兜底成 0 会让 `[ 0 -gt N ]` 为假、静默走 else 分支把超限
    context 全量 cat 出去（正是本 change 要消灭的静默失效）。且报错必须是我们的固定字面，
    不是 shell 的 `integer expression expected`（那说明空 size 漏进了算术比较）。
    """
    ctx = tmp_path / "ctx.md"
    ctx.write_bytes(MIXED)
    # 让 wc 失败 = 模拟 -r 检查后的 TOCTOU 权限变化（真实竞态已实跑复现，此处取确定性驱动）
    r = _source_and_run(f'wc() {{ return 1; }}\nrender_prompt "{ctx}"', tmp_path)
    assert r.returncode == 2, (r.returncode, r.stdout[:200], r.stderr)
    assert r.stdout == "", f"fail-loud 路径不得产出半截 prompt: {r.stdout[:200]!r}"
    assert "size 读取失败" in r.stderr, r.stderr
    assert "integer expression expected" not in r.stderr, r.stderr


def test_backscan_fallback_emits_visible_marker(tmp_path):
    """〔S3 · 契约在 code-review-fix1 M1 已变〕回扫值取不到 MUST 对外可见【且不再兜底继续
    产出 prompt】。

    旧契约（1.4.2 及以前）：回扫取不到时兜底成 0（= 退回按字节切）、打一行哨兵、仍
    exit 0 继续产出 prompt。code-review-fix1 M1 判定这仍是"做不到却假装做成了"（design.md
    F2 明确 od 不可用须 fail-loud、非零退出）——现在改为：回扫不可用 ⇒ 不产出 prompt、
    不启动 runner、非零退出（此处用 exit 1），哨兵行 OV_UTF8_BACKSCAN_UNAVAILABLE=1 仍打印
    （只是伴随失败，不再伴随"降级后继续"）。
    """
    ctx = tmp_path / "ctx.md"
    ctx.write_bytes(MIXED)
    env_prefix = f'export OV_MAX_CONTEXT_BYTES=100\n'

    # 正常路径：标记 MUST NOT 出现，exit 0，正常产出 prompt
    ok = _source_and_run(env_prefix + f'render_prompt "{ctx}" >/dev/null', tmp_path)
    assert ok.returncode == 0, ok.stderr
    assert "OV_UTF8_BACKSCAN_DROPPED=" in ok.stderr, ok.stderr
    assert "OV_UTF8_BACKSCAN_UNAVAILABLE" not in ok.stderr, ok.stderr

    # 降级路径：两个回扫函数返回空 ⇒ fail-loud（M1）：非零退出、不产出 prompt、标记 MUST 出现，
    # OV_UTF8_BACKSCAN_DROPPED/OV_TRUNCATED 等"继续截断"分支的输出 MUST NOT 出现
    # （render_prompt 在写出任何内容前就已 exit）。
    broken = _source_and_run(
        env_prefix
        + "utf8_head_trim() { echo ''; }\nutf8_tail_skip() { echo ''; }\n"
        + f'render_prompt "{ctx}" >/dev/null',
        tmp_path,
    )
    assert broken.returncode != 0, broken.stderr
    assert "OV_UTF8_BACKSCAN_UNAVAILABLE=1" in broken.stderr, broken.stderr
    assert "OV_UTF8_BACKSCAN_DROPPED=" not in broken.stderr, (
        f"M1 复发：回扫不可用却仍打印了'继续截断'分支的输出: {broken.stderr!r}"
    )
    assert "OV_TRUNCATED=" not in broken.stderr, (
        f"M1 复发：回扫不可用却仍走到了正常结束路径: {broken.stderr!r}"
    )
    for probe in ("hello ASCII", "更多中文", "😀"):
        assert probe not in broken.stderr, f"stderr 泄漏 context 正文: {probe}"


# ── F-新1：取字节失败 MUST NOT 与「合法结论 0」同形 ─────────────────────────
#
# 病灶：`_ov_bytes_at`（依赖 `od`）失败时无输出、不报错；`utf8_head_trim`/`utf8_tail_skip`
# 旧实现在"一个字节都没拿到"时落回 `echo 0`——与「回扫算出来的合法结论就是 0」同形，
# 上面 test_backscan_fallback_emits_visible_marker 的 case 守卫因此是【死分支】：它靠
# mock 掉两个函数本身（直接 `echo ''`）来验证守卫逻辑，从没验证过这两个函数在【真实
# 取字节失败】时到底会不会真的输出空串。这里补上——不 mock 函数本身，只让它们的
# 依赖（`_ov_bytes_at` / `wc`）失败，走真实代码路径。


def test_head_trim_reports_failure_not_zero_when_byte_read_fails(tmp_path):
    """〔F-新1〕`_ov_bytes_at` 失败（模拟 od 不可用）时 `utf8_head_trim` MUST 输出空串，
    MUST NOT 输出 "0"（那与"末 4 字节全是 continuation ⇒ 不动"的合法结论不可区分）。

    只覆盖 `_ov_bytes_at`（真实故障点），不碰 `utf8_head_trim` 自身 —— 走的是它内部
    「bytes 数组为空」那条真实分支，不是靠 mock 顶层函数蒙混过关。
    """
    corpus = _write(tmp_path, "mixed.md", MIXED)
    r = _source_and_run(
        '_ov_bytes_at() { return 1; }\n'  # 模拟 od 失败：无输出、非零退出
        f'utf8_head_trim "{corpus}" 4',
        tmp_path,
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "", (
        f"取字节失败时不得输出'{r.stdout.strip()}'（与合法结论 0 同形，F-新1 复发）"
    )


def test_tail_skip_reports_failure_not_zero_when_byte_read_fails(tmp_path):
    """〔F-新1〕同上，覆盖 `utf8_tail_skip` 的对称分支：`wc` 正常（拿到 size）但
    `_ov_bytes_at` 失败 ⇒ MUST 输出空串，MUST NOT 输出 "0"。
    """
    corpus = _write(tmp_path, "mixed.md", MIXED)
    r = _source_and_run(
        '_ov_bytes_at() { return 1; }\n'
        f'utf8_tail_skip "{corpus}" 4',
        tmp_path,
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "", (
        f"取字节失败时不得输出'{r.stdout.strip()}'（与合法结论 0 同形，F-新1 复发）"
    )


def test_render_prompt_real_od_failure_reports_backscan_unavailable(tmp_path):
    """⭐〔F-新1 · 契约在 code-review-fix1 M1 已变〕端到端、不 mock 任何 outside-voice.sh
    函数：PATH 里塞一个真会失败的 `od` 可执行文件（模拟"未安装/权限突变/资源耗尽/沙箱
    瞬时故障"），走完整 render_prompt 截断路径，MUST 打印 OV_UTF8_BACKSCAN_UNAVAILABLE=1
    【且非零退出、不产出任何 prompt】——design.md F2：od 不可用须 fail-loud，MUST NOT
    兜底继续产出可能含非法字节的 prompt（旧版在此仍 exit 0 继续截断，被 code-review-fix1
    M1 判定为「做不到却假装做成了」的同类失效，与本 change 主题同形）。

    这是比 test_backscan_fallback_emits_visible_marker（mock 函数）更强的证据：证明
    「od 真的挂了」这条路径能被 render_prompt 的守卫正确接住，而不只是"守卫逻辑本身
    没问题、但从没被真故障触发过"。

    变异验证：把 utf8_head_trim/utf8_tail_skip 的"bytes 为空/got=0 ⇒ echo ''"分支
    还原成旧版"echo 0"（即撤销 F-新1 修复）后，本用例转红——已实跑验证，见 impl-report。
    再变异：把 M1 的 fail-loud（`exit 1`）还原成旧版"兜底 htrim=0/tskip=0 继续产出"，
    本用例的 returncode/stdout 断言同样转红——见 code-review-fix1 报告里的变异验证记录。
    """
    ctx = _write(tmp_path, "mixed.md", MIXED)
    shim = tmp_path / "shim"
    shim.mkdir()
    (shim / "od").write_text("#!/bin/sh\nexit 1\n")
    (shim / "od").chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{shim}{os.pathsep}{env['PATH']}"
    env["OV_MAX_CONTEXT_BYTES"] = "100"
    env.pop("SDFLOW_VOICE_RUNNER", None)
    env.pop("SDFLOW_VOICE_MODEL", None)
    r = subprocess.run(
        ["bash", str(HELPER), "render-prompt", "--context-file", str(ctx)],
        capture_output=True, env=env, timeout=30,
    )
    assert r.returncode != 0, (
        f"M1 复发：od 真实失败却仍 exit 0（design.md F2 要求 fail-loud 非零退出）: {r.stderr!r}"
    )
    assert r.stdout == b"", (
        f"M1 复发：回扫不可用却仍产出了 prompt 内容: {r.stdout[:200]!r}"
    )
    err = r.stderr.decode("utf-8")
    assert "OV_UTF8_BACKSCAN_UNAVAILABLE=1" in err, (
        f"真实 od 失败没有被识别为失败（F-新1 复发）: {err!r}"
    )
    for probe in ("hello ASCII", "更多中文", "😀"):
        assert probe not in err, f"stderr 泄漏 context 正文: {probe}"


def _have_timeout_bin() -> bool:
    import shutil

    return bool(shutil.which("timeout") or shutil.which("gtimeout"))


@pytest.mark.skipif(not _have_timeout_bin(), reason="需要 timeout/gtimeout（do_exec 前置退出）")
def test_exec_render_failure_still_reaches_stderr(tmp_path):
    """〔N1〕exec 路径下 render_prompt 的 fail-loud 报错 MUST 到达真实 stderr。

    do_exec 把 render_prompt 的 stderr 重定向进 $workdir/render.meta，事后才回灌。
    若 render_prompt 内的 `exit 2` 直接终止【整个脚本】，回灌永不执行，且 EXIT trap 的
    `rm -rf $workdir` 抹掉 render.meta ⇒ 操作者只看到 rc=2 + 空 stdout + 空 stderr，
    零诊断信息——正是本 change 要消灭的那个病，在自己新开的路径上复活。
    ∴ 断言 rc 保真(2) 的【同时】stderr 必须含固定字面诊断。

    变异验证：把 do_exec 里的子壳 + rc 回灌还原成裸调用 ⇒ 本测试转红（stderr 为空）。
    """
    ctx = tmp_path / "ctx.md"
    ctx.write_bytes(MIXED)
    # wc 失败 = 模拟第 301 行预检之后才发生的 TOCTOU（预检按定义盖不住"检查之后"）
    shim = tmp_path / "shim"
    shim.mkdir()
    (shim / "wc").write_text("#!/bin/sh\nexit 1\n")
    (shim / "wc").chmod(0o755)

    env = dict(os.environ)
    env["PATH"] = f"{shim}{os.pathsep}{env['PATH']}"
    env["SDFLOW_VOICE_RUNNER"] = "codex"
    r = subprocess.run(
        ["bash", str(HELPER), "exec", "--context-file", str(ctx)],
        capture_output=True, text=True, cwd=str(tmp_path), env=env,
    )
    assert r.returncode == 2, (r.returncode, r.stdout[:200], r.stderr[:400])
    assert r.stdout == "", f"fail-loud 路径不得产出半截 prompt: {r.stdout[:200]!r}"
    assert r.stderr.strip() != "", "N1 复发：exit 非零但 stderr 全空（报错被 workdir 吞掉）"
    assert "size 读取失败" in r.stderr, r.stderr
    # 回灌的是 render.meta，MUST NOT 夹带 context 正文（未经出境扫描）
    for probe in ("hello ASCII", "更多中文", "😀"):
        assert probe not in r.stderr, f"stderr 泄漏 context 正文: {probe}"


# ── code-review-fix1 M2：_ov_bytes_at / _ov_read_bytes_strict 核验真实 od 返回码 + 数量 ──
#
# 病灶：`od ... | tr -s ' ' '\n' | grep -v '^$'` 的 `$?` 只反映管道【末端】grep 的返回码；
# od 半途失败（吐了一半再报错）时，grep 对"已吐出的部分"仍能正常匹配、返回 0 ⇒ 调用方
# 把【部分结果】误当【完整结果】。修法：先用命令替换单独捕获 od 自身的返回码，再对捕获
# 到的文本做格式化；并新增 `_ov_read_bytes_strict` 核验收到的字节数严格等于请求数、且
# 每项在 0..255。


def test_ov_bytes_at_propagates_real_od_exit_code_not_pipeline_tail(tmp_path):
    """〔M2〕`_ov_bytes_at` 的返回码 MUST 是 od 自身的返回码，不是管道末端 tr/grep 的返回码。

    塞一个真会"先吐点数据、再非零退出"的 `od` 影子二进制，直接验证返回码。
    """
    shim = tmp_path / "shim"
    shim.mkdir()
    (shim / "od").write_text("#!/bin/sh\necho ' 65 66'\nexit 1\n")
    (shim / "od").chmod(0o755)
    ctx = tmp_path / "ctx.md"
    ctx.write_bytes(b"hello world")
    env = os.environ.copy()
    env["PATH"] = f"{shim}{os.pathsep}{env['PATH']}"
    script = f'_OV_TEST_LIB_ONLY=1 . {HELPER!s}\n_ov_bytes_at "{ctx}" 0 3\necho "RC=$?"\n'
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, env=env, timeout=30)
    assert r.returncode == 0, r.stderr
    assert "RC=1" in r.stdout, (
        f"M2 复发：od 已非零退出，_ov_bytes_at 却报告成功(RC != 1): {r.stdout!r}"
    )

    # 变异对照：还原成旧版"直接把 od 接进管道、返回码来自管道尾端"的实现（用功能等价的
    # 替身函数在 source 之后覆盖，不依赖对正文做脆弱的精确字符串匹配），同样输入下应变回
    # RC=0 —— 证明这条断言真的由"单独捕获 od 返回码"这个修复点承重。
    mutant_script = (
        f'_OV_TEST_LIB_ONLY=1 . {HELPER!s}\n'
        "_ov_bytes_at() { od -An -tu1 -j \"$2\" -N \"$3\" \"$1\" 2>/dev/null | tr -s ' ' '\\n' | grep -v '^$'; }\n"
        f'_ov_bytes_at "{ctx}" 0 3\necho "RC=$?"\n'
    )
    r2 = subprocess.run(["bash", "-c", mutant_script], capture_output=True, text=True, env=env, timeout=30)
    assert r2.returncode == 0, r2.stderr
    assert "RC=0" in r2.stdout, (
        "变异体（旧管道实现）竟然也报告失败——说明本用例未真正锁定"
        f"「返回码来自管道尾端」这条修复点: {r2.stdout!r}"
    )


def test_ov_read_bytes_strict_rejects_partial_output_even_when_producer_reports_success(tmp_path):
    """〔M2〕即便 `_ov_bytes_at`（od）本身以 rc=0 退出，只要实际吐出的字节数与请求的
    count 不符，`_ov_read_bytes_strict` MUST 判定失败——不能只凭"完全为空"才算失败
    （旧版 utf8_head_trim/utf8_tail_skip 正是这么判的：只查 `${#bytes[@]} -eq 0`），那样
    "od 吐了一半又提前收尾但自己 rc=0"这种半成品会被当成完整合法结果使用。
    """
    ctx = tmp_path / "ctx.md"
    ctx.write_bytes(b"hello world")
    script = f"""
    _OV_TEST_LIB_ONLY=1 . {HELPER!s}
    _ov_bytes_at() {{ printf '104\\n101\\n'; return 0; }}  # 请求 3 个，只给 2 个，且自称成功
    _ov_read_bytes_strict "{ctx}" 0 3
    echo "RC=$?"
    """
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    assert "RC=1" in r.stdout, f"M2 复发：字节数与请求不符仍被判定成功: {r.stdout!r}"

    # 变异对照：重现旧判据（只查"完全为空"，不核对数量）——同样输入下应报告成功，
    # 证明上面的断言确实由「数量核验」这个新增修复点承重，不是巧合绿。
    mutant_script = f"""
    _OV_TEST_LIB_ONLY=1 . {HELPER!s}
    _ov_bytes_at() {{ printf '104\\n101\\n'; return 0; }}
    _ov_read_bytes_strict_old() {{
      local file="$1" offset="$2" count="$3" raw b
      raw=$(_ov_bytes_at "$file" "$offset" "$count") || return 1
      local -a bytes=()
      while IFS= read -r b; do [ -n "$b" ] && bytes+=("$b"); done <<< "$raw"
      if [ "${{#bytes[@]}}" -eq 0 ]; then return 1; fi
      printf '%s\\n' "${{bytes[@]}}"
      return 0
    }}
    _ov_read_bytes_strict_old "{ctx}" 0 3
    echo "RC=$?"
    """
    r2 = subprocess.run(["bash", "-c", mutant_script], capture_output=True, text=True, timeout=30)
    assert r2.returncode == 0, r2.stderr
    assert "RC=0" in r2.stdout, (
        "旧判据（只查完全为空）对本用例的部分输出竟然也报告失败——"
        f"说明本用例没有真正锁定「数量核验」这条修复点: {r2.stdout!r}"
    )


def test_ov_read_bytes_strict_rejects_out_of_range_values(tmp_path):
    """〔M2〕收到的字节值须严格落在 0..255；出现非法值（非数字/越界）MUST 判定失败。"""
    ctx = tmp_path / "ctx.md"
    ctx.write_bytes(b"abc")
    script = f"""
    _OV_TEST_LIB_ONLY=1 . {HELPER!s}
    _ov_bytes_at() {{ printf '65\\n999\\n67\\n'; return 0; }}  # 999 越界
    _ov_read_bytes_strict "{ctx}" 0 3
    echo "RC=$?"
    """
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    assert "RC=1" in r.stdout, f"越界字节值未被拒绝: {r.stdout!r}"


# ── code-review-fix1 M3：do_exec 侧「render.meta 因磁盘写满而为空」的不依赖磁盘兜底诊断 ──
#
# 对抗镜 B 的原始复现手法：把 workdir 所在的 TMPDIR 指向一个填满的小容量卷，render_prompt
# 子壳内的全部写入（含它自己的 stderr 重定向目标 render.meta）静默失败 ⇒ do_exec 事后
# `cat render.meta >&2` 读到空文件、转发等于没转发，操作者只看到 rc≠0 + 全空 stdout/stderr。
# 这里用 macOS `hdiutil` 建一个几 MB 的 ramdisk、精确填到只剩几 KB 可用空间来真实复现该
# 场景（而不是 mock），验证 do_exec 新增的"不经过 workdir 磁盘路径、直写真实 stderr"的
# 兜底诊断行确实出现。非 Darwin / 无 hdiutil 权限的环境显式 skip（同 bash_bin 矩阵的
# "缺失即可见 skip"原则），不静默变成"这条用例形同虚设"。


def _make_tiny_full_ramdisk(tmp_path):
    """建一个 ~2MB 的 HFS ramdisk，返回 (dev, mount_point)。精确填到"仅剩几 KB"这件事
    改由 `_calibrate_min_free_blocks`（块粒度自适应探测）负责——见该函数注释。
    任何一步失败（无 hdiutil 权限、非 Darwin 等）⇒ pytest.skip，不让基础设施问题
    伪装成"修复失效"。

    [impl-review-fix] 分配块大小显式定为 512（`newfs_hfs -b 512`），不用默认 4096：
    默认 4096 的块粒度和本场景要卡的目标写入量（render_prompt 完整 prompt ~5KB）
    是同一数量级——`workdir` 一次性触发的 catalog b-tree 扩容开销（约一整个分配块）
    与"留出的余量"挤在同一个块里，1 块之差就能把"mkdir 刚好够、写不下 prompt"
    翻成"mkdir 都不够"或"prompt 也写得下"，本机压测证实两种翻车都真实发生
    （29673453574 是前者；本地重跑 30 次曾 1 次撞见 do_exec 重定向 open() 本身因
    0 剩余块而失败于"No space left on device"，比 render 阶段更早——那是后者的
    变体）。缩到 512（HFS+ 允许的最小值，仅有"非最优"警告，无功能损失，catalog/
    extent b-tree 节点大小仍是 4096，一次性开销不变但用 8 倍精细的单位计量）后，
    同一开销相对目标写入量的粒度误差从 ~80%（4096/5146）降到 ~10%（512/5146），
    本地压测 30/30 稳定复现"mkdir 成功、render.meta 与 prompt.md 都能 open()、
    完整 prompt 写不下"。
    """
    if platform.system() != "Darwin" or shutil.which("hdiutil") is None:
        pytest.skip("M3 磁盘写满复现依赖 macOS hdiutil ramdisk，本平台不适用")
    mount_point = tmp_path / "ov_ramdisk"
    mount_point.mkdir()
    try:
        dev = subprocess.run(
            ["hdiutil", "attach", "-nomount", "ram://4096"],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout.split()[0]
        subprocess.run(["newfs_hfs", "-b", "512", dev],
                        capture_output=True, text=True, timeout=30, check=True)
        subprocess.run(["mount", "-t", "hfs", dev, str(mount_point)],
                        capture_output=True, text=True, timeout=30, check=True)
    except Exception as e:  # noqa: BLE001 — 基础设施探测失败一律 skip，不当测试失败
        pytest.skip(f"M3 ramdisk 建立失败（环境不支持，非本次修复问题）: {e}")

    return dev, mount_point


def _fill_leaving_blocks(mount_point, n_blocks):
    """把 mount_point 精确填到只剩 n_blocks 个【分配块】（`st.f_frsize`）可用——按块
    对齐，不用任意字节数。

    [impl-review-fix] 根因〔CI run 29673453574，macos-latest〕：旧版用固定字节数
    （如 8000）当目标可用空间。`os.statvfs` 报告的可用空间在实际发生分配块级别的
    quantization——本机实测同一个字节目标在填盘后实际落地的可用空间是 4096 或 8192
    这类整块数，具体落在哪个块边界取决于该 macOS 版本 / newfs_hfs 参数下 catalog
    元数据的初始开销（"Used" 基线），这个基线在不同 runner 上不同 ⇒ 同一个字节数在
    开发机上恰好落在"够 mkdir、不够写 5KB prompt"的那个块，在 CI runner 上却落在
    "连 mkdir 都不够"的块。与其继续赌一个字节数，不如直接以块为单位表达目标——
    彻底消除这类字节/块边界不对齐的漂移。
    """
    st = os.statvfs(str(mount_point))
    block = st.f_frsize
    avail = st.f_bavail * block
    target = n_blocks * block
    filler = mount_point / "filler.bin"
    if filler.exists():
        filler.unlink()
    fill = avail - target
    if fill > 0:
        with open(filler, "wb") as f:
            f.write(b"0" * fill)


def _calibrate_min_free_blocks(mount_point, max_blocks=8):
    """[impl-review-fix] 自适应探测：在【这一块全新 ramdisk】上，建一个目录最少要留几个
    分配块可用空间——不猜一个字节数，让文件系统自己回答（基准 5：无界底层开销不手搓）。

    从 1 块开始尝试建目录，失败就把可用空间加大到 2 块、3 块……直到成功或触到
    max_blocks 上限。成功后把探测用的目录删掉（把这部分空间还给可用池）——此时
    mount_point 上剩余的可用空间恰好等于"让一次 mkdir 成功所需的最小块数"，且
    catalog b-tree 该做的一次性扩容已经在探测过程中做过（扩容是粘性的，不会随
    rmdir 缩回去），所以随后真实脚本自己的 `mktemp -d` 只会比探测更宽松，不会更紧。

    返回找到的块数；探测到 max_blocks 仍不够 ⇒ 返回 None，由调用方判定"本环境这次
    建不起前提"并 skip（而不是让 mkdir 本身失败混进被测流程、假冒成"复现了 M3"）。
    """
    for n in range(1, max_blocks + 1):
        _fill_leaving_blocks(mount_point, n)
        probe = mount_point / "probe_dir"
        try:
            probe.mkdir()
        except OSError:
            continue
        probe.rmdir()
        return n
    return None


def _detach_ramdisk(dev, mount_point=None):
    """卸载 + 弹出 ramdisk——自行清理，不残留挂载点/设备节点污染开发机。

    实测〔macOS〕：新挂载的卷会被 Spotlight（mds/fseventsd）短暂持有，此时
    `hdiutil detach`（含 `-force`）与 `diskutil unmountDisk force` 都可能【回报成功
    却实际仍挂载】——只有对【挂载点路径】用 `umount -f` 才能可靠摘下文件系统，之后
    `hdiutil detach -force` 才能真正弹出设备节点。三级递进兜底，最大化清理成功率，
    任何一步失败都不让异常向上抛（清理函数本身不该成为测试失败的新来源）。
    """
    if mount_point is not None:
        subprocess.run(["umount", "-f", str(mount_point)], capture_output=True, text=True, timeout=30)
    r = subprocess.run(["hdiutil", "detach", dev], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        subprocess.run(["hdiutil", "detach", dev, "-force"], capture_output=True, text=True, timeout=30)


def _build_m3_mutant(tmp_path):
    """把 do_exec 里"render.meta 为空时的兜底诊断"那段摘掉，还原成旧版"只转发
    render.meta"三行。返回变异体脚本路径。"""
    src = HELPER.read_text(encoding="utf-8")
    mutant_marker = 'if [ ! -s "$workdir/render.meta" ]; then'
    assert mutant_marker in src, "源码结构已变，本变异验证需要同步更新"
    import re as _re
    mutated = _re.sub(
        r'  if \[ "\$rc" -ne 0 \]; then\n(?:.*\n)*?    exit "\$rc"\n  fi\n',
        '  if [ "$rc" -ne 0 ]; then exit "$rc"; fi\n',
        src,
        count=1,
    )
    assert mutated != src, "变异未生效——do_exec 结构已变，须同步更新本用例"
    mutant = tmp_path / "outside-voice-mutant-m3.sh"
    mutant.write_text(mutated, encoding="utf-8")
    mutant.chmod(0o755)
    return mutant


def _run_disk_full_scenario(script_path, tmp_path, subdir_name):
    """在一块全新的、精确填到只剩几个分配块可用空间的 ramdisk 上跑一次
    `script_path exec --context-file ...`，返回 subprocess.CompletedProcess。
    每次调用都用【全新】ramdisk（不复用/不二次填充同一块），规避"建目录 + 删目录"
    反复churn 在小容量 HFS 卷上造成的可用空间碎片化漂移（实测：同一块 2MB ramdisk
    连续两次填到同一目标字节数，第二次 `mktemp -d` 会因元数据开销提前失败）。

    [impl-review-fix] 可用空间目标由 `_calibrate_min_free_blocks` 自适应探测（块粒度），
    不再赌一个写死的字节数——探测不出（本环境元数据开销超出探测上限）⇒ 直接
    `pytest.skip`，不让"建前提本身失败"混进被测流程假冒成"复现了 M3"。
    """
    sub = tmp_path / subdir_name
    sub.mkdir()
    dev, mount_point = _make_tiny_full_ramdisk(sub)
    try:
        n_blocks = _calibrate_min_free_blocks(mount_point)
        if n_blocks is None:
            pytest.skip(
                "M3 磁盘写满场景：探测了 8 个分配块仍无法在本环境的 ramdisk 上建出一个"
                "目录（文件系统元数据开销超出探测上限）——本次未能建立『磁盘在 render "
                "阶段耗尽』的前提，未验证 M3；这不代表 M3 已失效，MUST NOT 因为本用例"
                "常 skip 就删掉它"
            )
        ctx = tmp_path / "ctx.md"
        if not ctx.exists():
            ctx.write_text("diff content for M3 disk-full test\n")
        bin_dir = tmp_path / "bin"
        if not bin_dir.exists():
            bin_dir.mkdir()
            fake_codex = bin_dir / "codex"
            fake_codex.write_text("#!/usr/bin/env bash\ncat >/dev/null\nexit 0\n")
            fake_codex.chmod(0o755)

        env = os.environ.copy()
        env["TMPDIR"] = str(mount_point)
        env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
        env["SDFLOW_VOICE_RUNNER"] = "codex"
        env.pop("SDFLOW_VOICE_MODEL", None)

        return subprocess.run(
            ["bash", str(script_path), "exec", "--context-file", str(ctx)],
            capture_output=True, env=env, timeout=30,
        )
    finally:
        _detach_ramdisk(dev, mount_point)


@pytest.mark.skipif(not _have_timeout_bin(), reason="需要 timeout/gtimeout（do_exec 前置退出）")
def test_exec_disk_full_render_meta_gets_unconditional_stderr_diagnostic(tmp_path):
    """⭐〔M3〕workdir 所在磁盘写满 ⇒ render.meta 本身写入失败为空 ⇒ do_exec MUST 仍在真实
    stderr 上留一条不依赖该磁盘的诊断行（"非零退出 ⇒ stderr 必有可辨识原因"）。

    变异验证：把 do_exec 里"render.meta 为空时的兜底诊断"那段去掉（还原成旧版"读到啥转发
    啥"），在【另一块独立的、同样精确填满的】ramdisk 上跑同一场景，stderr 应变回全空。
    """
    r = _run_disk_full_scenario(HELPER, tmp_path, "ramdisk-real")
    # [impl-review-fix] 块级自适应校准（见 _calibrate_min_free_blocks）已经把"mkdtemp 建
    # workdir、do_exec 打开 prompt.md/render.meta 两个重定向目标"都校准到几乎必然成立；
    # 这里仍留一道兜底探测——万一在某个环境里，这些【由 shell 自己在差异化代码之前就完成
    # 的步骤】（workdir 创建 / 打开重定向目标 / 子壳内某条命令的 write()）仍先于 M3 那段
    # 差异化代码而失败，产出的是 shell/coreutils 自己的原生诊断（"mktemp 失败:"、
    # "No space left on device" 等），这类噪声在【真实版与变异版之间完全相同】
    # （变异只摘掉了 do_exec 里"render.meta 为空时"那段兜底 echo，不动这些更早的代码）——
    # 意味着本次跑法根本没有走到能区分"有兜底/无兜底"的那段代码，继续断言毫无意义，
    # 应该响亮 skip 而不是把"建前提失败"误判成"验证通过"（本地压测 40 次曾撞见 2 次：
    # 一次是 do_exec 重定向本身 open() 失败于 0 剩余空间，一次是子壳内 printf 的 write()
    # 失败、错误直接漏到真实 stderr）。
    def _shell_level_enospc_noise(stderr):
        for marker in (b"mktemp \xe5\xa4\xb1\xe8\xb4\xa5:", b"No space left on device"):
            if marker in stderr:
                return marker
        return None

    _noise = _shell_level_enospc_noise(r.stderr)
    if _noise is not None:
        pytest.skip(
            "M3 磁盘写满场景：本环境即便经过块级自适应校准，仍在真正走到 M3 差异化代码之前"
            f"就撞见 shell/coreutils 自己的满盘原生诊断（含 {_noise!r}）——本次未能建立"
            "『磁盘在 render 阶段耗尽、且仅由 render_prompt 自身诊断』的前提，未验证 M3；"
            f"这不代表 M3 已失效，MUST NOT 因为本用例常 skip 就删掉它。stderr={r.stderr!r}"
        )
    assert r.returncode != 0, "磁盘写满场景下 exec 竟然报告成功"
    assert r.stdout == b"", r.stdout[:200]
    assert r.stderr.strip() != b"", (
        "M3 复发：磁盘写满导致 render.meta 为空，stderr 又变回全空——"
        "不依赖磁盘的兜底诊断没有生效"
    )
    # 🔴 **不断言失败发生在哪一步**〔macOS CI 实证，2026-07-19 run 29673347533〕：
    # 本用例的不变量是「磁盘写满 ⇒ 非零退出 ∧ stdout 空 ∧ **stderr 有可辨识原因**」——
    # 上面三条断言已完整锁死它。曾经这里还多一条 `b"render_prompt" in stderr and b"rc=" in stderr`，
    # 那是把「失败要有声」写成了「必须**在这个特定位置**失败」：
    #   · 开发机（brew ramdisk 建得起来、填满后才崩）⇒ 挂在 render_prompt，断言过；
    #   · macOS runner（ramdisk 从一开始就不可写）⇒ `mktemp` 建 workdir 就先挂，
    #     stderr = `mktemp: mkdtemp failed on …/ov_ramdisk 不可写` ⇒ 断言红，**而产品行为完全正确**。
    # 磁盘在哪一步耗尽取决于环境，不是被测契约的一部分。∴ 只核「有声」，不核「在哪出声」。
    # （反向保证仍在：下方变异体断言 stderr **必须全空**——若哪天连这条也松了，本用例才真失去承重。）
    assert len(r.stderr.strip()) >= 10, (
        f"stderr 有内容但短得不像可辨识诊断（可能只是个换行/单字符）: {r.stderr!r}"
    )

    mutant = _build_m3_mutant(tmp_path)
    r2 = _run_disk_full_scenario(mutant, tmp_path, "ramdisk-mutant")
    _noise2 = _shell_level_enospc_noise(r2.stderr)
    if _noise2 is not None:
        # 变异体与真实版共享 workdir 创建 / 重定向打开 / 子壳内命令这些【更早】的代码
        # （变异只摘掉了 do_exec 里"render.meta 为空时"那段兜底 echo）——若两者在这些
        # 更早的位置都撞见同一条 shell/coreutils 原生诊断，本次的差异化验证无效：两个
        # 变体产出同一条与 M3 无关的噪声，根本没有走到能区分「有兜底/无兜底」的那段代码。
        pytest.skip(
            "M3 磁盘写满场景：变异体这一次独立的 ramdisk 上，在走到 M3 差异化代码之前就"
            f"撞见 shell/coreutils 自己的满盘原生诊断（含 {_noise2!r}）——本次未能建立可"
            "区分 M3 修复点的前提，未验证 M3；这不代表 M3 已失效，MUST NOT 因为本用例常"
            f" skip 就删掉它。stderr={r2.stderr!r}"
        )
    assert r2.returncode != 0
    assert r2.stderr.strip() == b"", (
        "变异体（旧版无条件兜底诊断）在同一类满盘场景下 stderr 竟然不是空的——"
        f"说明本用例没有真正锁定 M3 这条修复点: {r2.stderr!r}"
    )
