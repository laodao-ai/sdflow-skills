"""resolve-models.sh（add-codex-host-support Task 6）：宿主判定 + 机队档位解析器（纯 shell，ADR-1）。

契约：`eval "$(resolve-models.sh [--root <repo_root>])"` 导出六变量
SDFLOW_HOST / SDFLOW_TIER_{STRONG,MID,LIGHT} / SDFLOW_VOICE_RUNNER / SDFLOW_VOICE_MODEL。

宿主判定用正信号（CLAUDECODE=1 / CODEX_THREAD_ID 非空），MUST NOT「缺失即另一方」推断。
档位从 workflow bundle 的 model-tiers.md 机读块读，覆盖按机队分键（ADR-8），eval 注入面
（GC-6/D5）用模型 ID 字符集校验 + printf %q 纵深防御加固。

Run: python3 -m pytest sdflow-init/tests/test_resolve_models.py -v
"""
import importlib.util
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "fixtures"))
from model_tiers_cases import CASES as MODEL_TIERS_CASES  # noqa: E402 共享畸形输入语料

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "sdflow-init" / "assets" / "hack" / "resolve-models.sh"
OUTSIDE_VOICE = REPO / "sdflow-init" / "assets" / "hack" / "outside-voice.sh"
JOB_PY = REPO / "sdflow-init" / "assets" / "hack" / "outside-voice-job.py"

# 宿主判据的**第二份实现**（Python 侧）——parity 门要拿它跟本 shell 脚本对跑。
_JOB_SPEC = importlib.util.spec_from_file_location("sdflow_outside_voice_job", JOB_PY)
JOB = importlib.util.module_from_spec(_JOB_SPEC)
_JOB_SPEC.loader.exec_module(JOB)


def make_bundle_repo(tmp_path, claude=("opus", "sonnet", "haiku"),
                      codex=("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")):
    """一个自包含的本地 pin bundle（resolve-workflow.sh 的 local-pin 分支会命中它），
    含 model-tiers.md 机读块——resolve-models.sh 靠它定位档位缺省。"""
    root = tmp_path / "repo"
    wf = root / "openspec" / "workflow"
    wf.mkdir(parents=True)
    (wf / "workflow.md").write_text("# wf\n", encoding="utf-8")
    (wf / "spec-checklists").mkdir()
    (wf / "spec-checklists" / "d.md").write_text("x\n", encoding="utf-8")
    (wf / "code-checklists").mkdir()
    (wf / "code-checklists" / "d.md").write_text("x\n", encoding="utf-8")
    (wf / "model-tiers.md").write_text(
        "# model-tiers\n\n```model-tier-defaults\n"
        f"claude.strong: {claude[0]}\nclaude.mid: {claude[1]}\nclaude.light: {claude[2]}\n"
        f"codex.strong: {codex[0]}\ncodex.mid: {codex[1]}\ncodex.light: {codex[2]}\n"
        "```\n",
        encoding="utf-8",
    )
    return root


def write_config_yaml(root, content):
    osdir = root / "openspec"
    osdir.mkdir(parents=True, exist_ok=True)
    (osdir / "config.yaml").write_text(content, encoding="utf-8")


def run_resolve(root, env_overrides=None, no_sdflow_home=True, extra_args=()):
    env = dict(os.environ)
    if no_sdflow_home:
        # 隔离真实 ~/.sdflow：不让本机已装的全局 canonical 干扰测试（每条用例应只吃本地 pin bundle）
        env["SDFLOW_HOME"] = str(root.parent / "no-such-sdflow-home")
    env.pop("CLAUDECODE", None)
    env.pop("CODEX_THREAD_ID", None)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", str(SCRIPT), "--root", str(root), *extra_args],
        capture_output=True, text=True, env=env, timeout=15,
    )


def eval_resolve(root, env_overrides=None, no_sdflow_home=True, cwd=None):
    """真正走 `eval "$(resolve-models.sh ...)"` 接口——用于恶意值回归（断言不执行）。"""
    env = dict(os.environ)
    if no_sdflow_home:
        env["SDFLOW_HOME"] = str(root.parent / "no-such-sdflow-home")
    env.pop("CLAUDECODE", None)
    env.pop("CODEX_THREAD_ID", None)
    if env_overrides:
        env.update(env_overrides)
    script = f'eval "$(bash {shlex.quote(str(SCRIPT))} --root {shlex.quote(str(root))})"; ' \
             f'echo "SDFLOW_HOST=$SDFLOW_HOST"; echo "SDFLOW_TIER_STRONG=$SDFLOW_TIER_STRONG"; ' \
             f'echo "SDFLOW_TIER_MID=$SDFLOW_TIER_MID"; echo "SDFLOW_TIER_LIGHT=$SDFLOW_TIER_LIGHT"; ' \
             f'echo "SDFLOW_VOICE_RUNNER=$SDFLOW_VOICE_RUNNER"; echo "SDFLOW_VOICE_MODEL=$SDFLOW_VOICE_MODEL"'
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                          env=env, cwd=str(cwd) if cwd else None, timeout=15)


def parse_exports(stdout):
    out = {}
    for line in stdout.splitlines():
        if line.startswith("export SDFLOW_"):
            body = line[len("export "):]
            k, _, v = body.partition("=")
            # 值经 bash printf %q 编码；剥一层最外层单引号做粗略反解析（够测试断言用）
            if v.startswith("'") and v.endswith("'") and len(v) >= 2:
                v = v[1:-1]
            out[k] = v
    return out


class TestScriptExecutable:
    def test_script_is_executable(self):
        assert SCRIPT.exists()
        assert os.access(SCRIPT, os.X_OK)


class TestHostDetection:
    """GC-7：正信号判宿主，MUST NOT「缺失即另一方」推断。"""

    def test_claudecode_signal_yields_claude(self, tmp_path):
        root = make_bundle_repo(tmp_path)
        r = run_resolve(root, {"CLAUDECODE": "1"})
        assert r.returncode == 0, r.stderr
        exports = parse_exports(r.stdout)
        assert exports["SDFLOW_HOST"] == "claude"
        assert exports["SDFLOW_VOICE_RUNNER"] == "codex"

    def test_codex_thread_id_signal_yields_codex(self, tmp_path):
        root = make_bundle_repo(tmp_path)
        r = run_resolve(root, {"CODEX_THREAD_ID": "11111111-2222-3333-4444-555555555555"})
        assert r.returncode == 0, r.stderr
        exports = parse_exports(r.stdout)
        assert exports["SDFLOW_HOST"] == "codex"
        assert exports["SDFLOW_VOICE_RUNNER"] == "claude"

    def test_neither_signal_yields_unknown_with_stderr(self, tmp_path):
        root = make_bundle_repo(tmp_path)
        r = run_resolve(root, {})
        assert r.returncode == 0, r.stderr
        exports = parse_exports(r.stdout)
        assert exports["SDFLOW_HOST"] == "unknown"
        assert exports["SDFLOW_VOICE_RUNNER"] == ""
        assert "判不出" in r.stderr

    def test_both_signals_yields_unknown_with_conflict_warning(self, tmp_path):
        """两个正信号同时出现（环境泄漏等异常态）——MUST NOT 静默取其一。"""
        root = make_bundle_repo(tmp_path)
        r = run_resolve(root, {"CLAUDECODE": "1",
                               "CODEX_THREAD_ID": "11111111-2222-3333-4444-555555555555"})
        assert r.returncode == 0, r.stderr
        exports = parse_exports(r.stdout)
        assert exports["SDFLOW_HOST"] == "unknown"
        assert "冲突" in r.stderr

    def test_claudecode_zero_does_not_count_as_signal(self, tmp_path):
        """CLAUDECODE=0（或其它非 '1' 值）不构成正信号——严格判 '1'，不做真值转换猜测。"""
        root = make_bundle_repo(tmp_path)
        r = run_resolve(root, {"CLAUDECODE": "0"})
        exports = parse_exports(r.stdout)
        assert exports["SDFLOW_HOST"] == "unknown"

    def test_unknown_host_tiers_fall_back_to_claude_canonical_defaults(self, tmp_path):
        """ADR-7：宿主判不出 ⇒ 档位回落 canonical 缺省（不套用任何覆盖）。"""
        root = make_bundle_repo(tmp_path)
        write_config_yaml(root, "schema: spec-driven\nmodel-tiers:\n  strong: should-not-apply\n")
        r = run_resolve(root, {})
        exports = parse_exports(r.stdout)
        assert exports["SDFLOW_HOST"] == "unknown"
        assert exports["SDFLOW_TIER_STRONG"] == "opus"


class TestHostDetectionParityAcrossLanguages:
    """🔒 跨语言 parity 门：宿主判据有**两份实现**，同一组 env 必须给同一个答案。

    `resolve-models.sh` 第 1 段（shell，决定 voice 用哪个 runner / 哪档模型）与
    `outside-voice-job.py` 的 `detect_host()`（Python，决定 efficacy 证据里落哪个 `host`）
    是同一个判据的两处实现。两边漂了不会有任何人当场发现 —— 而 efficacy 门的**决胜量**
    正是那个 `host`：shell 说 codex、Python 说 unknown，会让一轮真 Codex 跑出来的证据
    被判红（假失败），反向则是假绿。

    **手写「等价性证明」是死路**（CLAUDE.md 基准 5）：那等于用一份解析器去猜另一个
    语言的语义。正解 = **让两边自己回答** —— 同一组 env 各跑一遍，比结果。
    真值表与 `test_outside_voice_job.py` 的 `detect_host` 用例同源（正/负/冲突/缺失各一）。
    """

    HOST_ENVS = [
        {"CLAUDECODE": "1"},                                             # 正信号 → claude
        {"CODEX_THREAD_ID": "11111111-2222-3333-4444-555555555555"},     # 正信号 → codex
        {"CLAUDECODE": "1", "CODEX_THREAD_ID": "abc"},                   # 冲突 → unknown
        {},                                                              # 缺失 → unknown
        {"CLAUDECODE": "0"},                                             # 非 "1" 不算信号
        {"CODEX_THREAD_ID": ""},                                         # 空串不算信号
    ]

    @pytest.mark.parametrize("host_env", HOST_ENVS, ids=lambda e: repr(sorted(e.items())))
    def test_shell_and_python_agree_on_the_same_env(self, tmp_path, host_env):
        root = make_bundle_repo(tmp_path)
        r = run_resolve(root, host_env)          # run_resolve 先清两个信号再注入本用例
        assert r.returncode == 0, r.stderr
        shell_host = parse_exports(r.stdout)["SDFLOW_HOST"]
        python_host = JOB.detect_host(dict(host_env))
        assert shell_host == python_host, (
            f"宿主判据跨语言漂移：env={host_env} → resolve-models.sh={shell_host!r} / "
            f"detect_host()={python_host!r}")


class TestTierDefaultsPerFleet:
    """档位从 model-tiers.md 机读块读，两机队分列（spec-workflow「模型档位映射」）。"""

    def test_claude_host_reads_claude_fleet_defaults(self, tmp_path):
        root = make_bundle_repo(tmp_path)
        r = run_resolve(root, {"CLAUDECODE": "1"})
        exports = parse_exports(r.stdout)
        assert exports["SDFLOW_TIER_STRONG"] == "opus"
        assert exports["SDFLOW_TIER_MID"] == "sonnet"
        assert exports["SDFLOW_TIER_LIGHT"] == "haiku"
        assert exports["SDFLOW_VOICE_MODEL"] == "gpt-5.6-sol"  # 另一机队（codex）的强档

    def test_codex_host_reads_codex_fleet_defaults(self, tmp_path):
        root = make_bundle_repo(tmp_path)
        r = run_resolve(root, {"CODEX_THREAD_ID": "abc"})
        exports = parse_exports(r.stdout)
        assert exports["SDFLOW_TIER_STRONG"] == "gpt-5.6-sol"
        assert exports["SDFLOW_TIER_MID"] == "gpt-5.6-terra"
        assert exports["SDFLOW_TIER_LIGHT"] == "gpt-5.6-luna"
        assert exports["SDFLOW_VOICE_MODEL"] == "opus"  # 另一机队（claude）的强档

    def test_gate_step_never_downgrades_strong_across_hosts(self, tmp_path):
        """同一门禁步（强档）在两宿主下都不得降到 mid/light。"""
        root = make_bundle_repo(tmp_path)
        c = parse_exports(run_resolve(root, {"CLAUDECODE": "1"}).stdout)
        x = parse_exports(run_resolve(root, {"CODEX_THREAD_ID": "abc"}).stdout)
        assert c["SDFLOW_TIER_STRONG"] not in (c["SDFLOW_TIER_MID"], c["SDFLOW_TIER_LIGHT"])
        assert x["SDFLOW_TIER_STRONG"] not in (x["SDFLOW_TIER_MID"], x["SDFLOW_TIER_LIGHT"])


class TestFleetKeyedOverride:
    """ADR-8：覆盖按机队分键；扁平旧格式兼容读作 Claude 机队，Codex 机队不生效。"""

    def test_nested_override_applies_to_matching_fleet_only(self, tmp_path):
        root = make_bundle_repo(tmp_path)
        write_config_yaml(root, "schema: spec-driven\nmodel-tiers:\n"
                                 "  claude:\n    strong: claude-override\n"
                                 "  codex:\n    strong: codex-override\n")
        claude = parse_exports(run_resolve(root, {"CLAUDECODE": "1"}).stdout)
        codex = parse_exports(run_resolve(root, {"CODEX_THREAD_ID": "abc"}).stdout)
        assert claude["SDFLOW_TIER_STRONG"] == "claude-override"
        assert codex["SDFLOW_TIER_STRONG"] == "codex-override"

    def test_flat_legacy_applies_on_claude_host(self, tmp_path):
        root = make_bundle_repo(tmp_path)
        write_config_yaml(root, "schema: spec-driven\nmodel-tiers:\n  strong: legacy-override\n")
        claude = parse_exports(run_resolve(root, {"CLAUDECODE": "1"}).stdout)
        assert claude["SDFLOW_TIER_STRONG"] == "legacy-override"

    def test_flat_legacy_does_not_apply_on_codex_host(self, tmp_path):
        """MUST NOT 把扁平覆盖里的 Claude 模型名塞给 Codex 机队——回落 Codex 缺省。"""
        root = make_bundle_repo(tmp_path)
        write_config_yaml(root, "schema: spec-driven\nmodel-tiers:\n  strong: legacy-override\n")
        codex = parse_exports(run_resolve(root, {"CODEX_THREAD_ID": "abc"}).stdout)
        assert codex["SDFLOW_TIER_STRONG"] == "gpt-5.6-sol"
        assert codex["SDFLOW_TIER_STRONG"] != "legacy-override"

    def test_missing_fleet_section_falls_back_to_fleet_default(self, tmp_path):
        root = make_bundle_repo(tmp_path)
        write_config_yaml(root, "schema: spec-driven\nmodel-tiers:\n  claude:\n    strong: c-only\n")
        codex = parse_exports(run_resolve(root, {"CODEX_THREAD_ID": "abc"}).stdout)
        assert codex["SDFLOW_TIER_STRONG"] == "gpt-5.6-sol"

    def test_voice_model_for_codex_host_honors_claude_flat_override(self, tmp_path):
        """codex 宿主向 claude 发起 voice 时，VOICE_MODEL = Claude 机队强档——该值本身仍可被
        Claude 机队覆盖（含扁平兼容）影响，因为解析的是「另一机队 claude 的 strong」，非
        「codex 自己的 strong」。"""
        root = make_bundle_repo(tmp_path)
        write_config_yaml(root, "schema: spec-driven\nmodel-tiers:\n  strong: legacy-override\n")
        codex = parse_exports(run_resolve(root, {"CODEX_THREAD_ID": "abc"}).stdout)
        assert codex["SDFLOW_VOICE_MODEL"] == "legacy-override"


class TestEvalInjectionHardening:
    """GC-6/D5：eval 注入面加固——覆盖值须过模型 ID 字符集校验，恶意值不得在 eval 时执行。"""

    def test_dollar_paren_injection_rejected_and_not_executed(self, tmp_path):
        root = make_bundle_repo(tmp_path)
        marker = root / "INJECTED_DOLLAR"
        write_config_yaml(root, "schema: spec-driven\nmodel-tiers:\n"
                                 f"  claude:\n    strong: $(touch {marker})\n")
        r = eval_resolve(root, {"CLAUDECODE": "1"}, cwd=root)
        assert r.returncode == 0, r.stderr
        assert not marker.exists(), "eval 执行了注入的 $() 命令替换——安全回归"
        assert "SDFLOW_TIER_STRONG=opus" in r.stdout  # 回落缺省
        assert "非法字符" in r.stderr

    def test_backtick_injection_rejected_and_not_executed(self, tmp_path):
        root = make_bundle_repo(tmp_path)
        marker = root / "INJECTED_BACKTICK"
        write_config_yaml(root, "schema: spec-driven\nmodel-tiers:\n"
                                 f"  codex:\n    strong: `touch {marker}`\n")
        r = eval_resolve(root, {"CODEX_THREAD_ID": "abc"}, cwd=root)
        assert r.returncode == 0, r.stderr
        assert not marker.exists()
        assert "SDFLOW_TIER_STRONG=gpt-5.6-sol" in r.stdout

    def test_semicolon_command_injection_rejected_and_not_executed(self, tmp_path):
        root = make_bundle_repo(tmp_path)
        marker = root / "INJECTED_SEMI"
        write_config_yaml(root, "schema: spec-driven\nmodel-tiers:\n"
                                 f"  claude:\n    mid: sonnet; touch {marker}\n")
        r = eval_resolve(root, {"CLAUDECODE": "1"}, cwd=root)
        assert r.returncode == 0, r.stderr
        assert not marker.exists()
        assert "SDFLOW_TIER_MID=sonnet" in r.stdout

    def test_newline_embedded_via_second_line_ignored_not_executed(self, tmp_path):
        """恶意值试图借第二条物理行注入命令（YAML 行级读取天然只认第一行为 key: value）。"""
        root = make_bundle_repo(tmp_path)
        marker = root / "INJECTED_NEWLINE"
        write_config_yaml(root, "schema: spec-driven\nmodel-tiers:\n"
                                 "  claude:\n"
                                 "    strong: opus\n"
                                 f"touch {marker}\n")
        r = eval_resolve(root, {"CLAUDECODE": "1"}, cwd=root)
        assert r.returncode == 0, r.stderr
        assert not marker.exists()

    def test_output_is_printf_q_encoded(self, tmp_path):
        """即使值合法，输出仍经 printf %q 编码（纵深防御，非唯一防线）——正常值单纯字母数字时
        %q 输出不加引号包裹，断言 export 行格式正确、变量可被安全 eval。"""
        root = make_bundle_repo(tmp_path)
        r = run_resolve(root, {"CLAUDECODE": "1"})
        assert "export SDFLOW_HOST=claude" in r.stdout
        assert "export SDFLOW_TIER_STRONG=opus" in r.stdout

    # 🔴 D1：eval_resolve 的 f-string 插值 `{SCRIPT}`/`{root}` 未加引号 → root 含空格被 bash word-split
    # 拆成多参、脚本 arg 解析报 unknown arg 而静默错解。恰在 eval 注入测试套件里自身不加引号（讽刺面）。
    def test_root_with_space_not_word_split(self, tmp_path):
        spaced = tmp_path / "dir with space"
        spaced.mkdir()
        root = make_bundle_repo(spaced)
        r = eval_resolve(root, {"CLAUDECODE": "1"})
        assert "unknown arg" not in r.stderr, "root 含空格被 word-split（f-string 插值未加引号）"
        assert "SDFLOW_HOST=claude" in r.stdout          # eval 真跑成、导出生效
        assert "SDFLOW_TIER_STRONG=opus" in r.stdout


class TestSharedMalformedFixtureConsistency:
    """design D10：resolver 与 config_lint 跨语言无法共享同一实现，改用共享畸形输入语料
    （fixtures/model_tiers_cases.py）断言两侧 accept/reject 判据一致。本文件断言 resolver 侧。"""

    def test_shared_cases_match_resolver_expectation(self, tmp_path):
        for case in MODEL_TIERS_CASES:
            root = make_bundle_repo(tmp_path / case["name"])
            write_config_yaml(root, "schema: spec-driven\n" + case["yaml_block"])
            for expect in case["resolver"]:
                env = {"CLAUDECODE": "1"} if expect["host"] == "claude" else {"CODEX_THREAD_ID": "abc"}
                r = run_resolve(root, env)
                assert r.returncode == 0, f"{case['name']}/{expect['host']}: {r.stderr}"
                exports = parse_exports(r.stdout)
                assert exports["SDFLOW_TIER_STRONG"] == expect["strong"], \
                    f"{case['name']}/{expect['host']}: strong"
                assert exports["SDFLOW_TIER_MID"] == expect["mid"], \
                    f"{case['name']}/{expect['host']}: mid"
                assert exports["SDFLOW_TIER_LIGHT"] == expect["light"], \
                    f"{case['name']}/{expect['host']}: light"
            marker_name = case.get("injection_marker")
            if marker_name:
                # 恶意值用例：真跑 eval，断言注入未执行（marker 文件未被创建）。
                marker = root / marker_name
                host_env = {"CLAUDECODE": "1"} if case["resolver"][0]["host"] == "claude" \
                    else {"CODEX_THREAD_ID": "abc"}
                r = eval_resolve(root, host_env, cwd=root)
                assert r.returncode == 0, r.stderr
                assert not marker.exists(), f"{case['name']}: 注入被执行"


class TestFleetHeaderTrailingContentCrosstalk:
    """Task 6 复评 Critical（reviewer 对抗复现）：fleet header 带行内注释击穿精确匹配，
    stale fleet 跨该行续命 ⇒ 后续叶子值被读进错误机队（opus 塞进 codex）。回归锁。"""

    CROSSTALK_CONFIG = ("schema: spec-driven\nmodel-tiers:\n"
                        "  codex:\n    strong: gpt-placeholder\n"
                        "  claude:  # override block for claude fleet\n    strong: opus\n")

    def test_opus_does_not_leak_into_codex_fleet(self, tmp_path):
        """codex 宿主下，claude 头后注释的 `strong: opus` MUST NOT 归 codex——codex.strong 仍取
        codex 段自己的 `gpt-placeholder` 覆盖（而非被 claude 块的 opus 串扰覆盖）。"""
        root = make_bundle_repo(tmp_path)
        write_config_yaml(root, self.CROSSTALK_CONFIG)
        codex = parse_exports(run_resolve(root, {"CODEX_THREAD_ID": "x"}).stdout)
        assert codex["SDFLOW_TIER_STRONG"] != "opus", "opus 泄进了 codex 机队（fleet 归属串扰）"
        assert codex["SDFLOW_TIER_STRONG"] == "gpt-placeholder"

    def test_opus_correctly_attributed_to_claude_fleet(self, tmp_path):
        """claude 宿主下，注释后的 `strong: opus` 正确归 claude。"""
        root = make_bundle_repo(tmp_path)
        write_config_yaml(root, self.CROSSTALK_CONFIG)
        claude = parse_exports(run_resolve(root, {"CLAUDECODE": "1"}).stdout)
        assert claude["SDFLOW_TIER_STRONG"] == "opus"


class TestOutsideVoiceDoesNotSelfResolve:
    """🔒 G6 同源锁（ADR-9）：outside-voice.sh MUST NOT 自行调 resolve-models.sh 重判宿主——
    只从环境读 $SDFLOW_VOICE_RUNNER，否则锚行 host 与 voice 实际 runner 可能不同源。"""

    def test_outside_voice_sh_does_not_reference_resolve_models(self):
        text = OUTSIDE_VOICE.read_text(encoding="utf-8")
        assert "resolve-models" not in text, (
            "outside-voice.sh 引用了 resolve-models（可能自行重判宿主，违反 ADR-9 同源约束）"
        )
