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
    """〔S3〕回扫值取不到而兜底成 0（= 退回按字节切）MUST 对外可见。

    OV_UTF8_BACKSCAN_DROPPED=0 与「纯 ASCII 本就无需回扫」不可区分 ⇒ 无额外标记就是零信号
    静默降级，方向与本 change 论点相反。标记只含固定字面，不含 context 正文。
    """
    ctx = tmp_path / "ctx.md"
    ctx.write_bytes(MIXED)
    env_prefix = f'export OV_MAX_CONTEXT_BYTES=100\n'

    # 正常路径：标记 MUST NOT 出现
    ok = _source_and_run(env_prefix + f'render_prompt "{ctx}" >/dev/null', tmp_path)
    assert "OV_UTF8_BACKSCAN_DROPPED=" in ok.stderr, ok.stderr
    assert "OV_UTF8_BACKSCAN_UNAVAILABLE" not in ok.stderr, ok.stderr

    # 降级路径：两个回扫函数返回空 ⇒ 标记 MUST 出现
    broken = _source_and_run(
        env_prefix
        + "utf8_head_trim() { echo ''; }\nutf8_tail_skip() { echo ''; }\n"
        + f'render_prompt "{ctx}" >/dev/null',
        tmp_path,
    )
    assert "OV_UTF8_BACKSCAN_UNAVAILABLE=1" in broken.stderr, broken.stderr
    assert "OV_UTF8_BACKSCAN_DROPPED=0" in broken.stderr, broken.stderr
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
    """⭐〔F-新1〕端到端、不 mock 任何 outside-voice.sh 函数：PATH 里塞一个真会失败的
    `od` 可执行文件（模拟"未安装/权限突变/资源耗尽/沙箱瞬时故障"），走完整
    render_prompt 截断路径，MUST 打印 OV_UTF8_BACKSCAN_UNAVAILABLE=1。

    这是比 test_backscan_fallback_emits_visible_marker（mock 函数）更强的证据：证明
    「od 真的挂了」这条路径能被 render_prompt 的守卫正确接住，而不只是"守卫逻辑本身
    没问题、但从没被真故障触发过"。

    变异验证：把 utf8_head_trim/utf8_tail_skip 的"bytes 为空/got=0 ⇒ echo ''"分支
    还原成旧版"echo 0"（即撤销本次修复）后，本用例转红——已实跑验证，见 impl-report。
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
    assert r.returncode == 0, r.stderr
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
