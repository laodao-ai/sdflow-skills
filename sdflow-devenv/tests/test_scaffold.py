"""devenv_scaffold 的测试 —— B 层（手）。

重点在 verify-lane：它是 skill 唯一「产生新事实」的地方（真 fork 执行，拿真 exit code）。
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import devenv_scaffold as F  # noqa: E402
import devenv_schema as S  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "openspec").mkdir()
    return tmp_path


def run(*argv):
    return F.main([str(a) for a in argv])


# ---------- init：退出码驱动的模式分流 ----------

def test_init_without_openspec_is_fail_closed(tmp_path):
    assert run("init", "--root", tmp_path) == 3


def test_init_creates_blank_framework(repo, capsys):
    assert run("init", "--root", repo) == 0
    d = S.load(repo)
    assert set(d["layers"]) == set(S.LAYERS)
    assert all(d["layers"][n]["how"] == S.PENDING for n in S.LAYERS)
    assert "十五格全待定" in capsys.readouterr().out


def test_init_warns_loudly_on_missing_sad_but_does_not_block(repo, capsys):
    """MUST NOT 佯装有 SAD。但也 MUST NOT fail-closed —— 显式降级。"""
    assert run("init", "--root", repo) == 0
    err = capsys.readouterr().err
    assert "sad.md 缺失" in err and "泳道覆盖对账【失效】" in err


def test_init_on_existing_needs_on_exists(repo):
    run("init", "--root", repo)
    assert run("init", "--root", repo) == 4
    assert run("init", "--root", repo, "--on-exists", "continue") == 0


def test_continue_on_corrupt_file_fails_with_three_part_message(repo, capsys):
    run("init", "--root", repo)
    (repo / S.DEVENV_REL).write_text("{坏了", encoding="utf-8")
    capsys.readouterr()
    assert run("init", "--root", repo, "--on-exists", "continue") == 2
    err = capsys.readouterr().err
    assert "问题：" in err and "原因：" in err and "修复：" in err and "replan" in err


def test_replan_on_corrupt_file_starts_over(repo, capsys):
    run("init", "--root", repo)
    (repo / S.DEVENV_REL).write_text("{坏了", encoding="utf-8")
    assert run("init", "--root", repo, "--on-exists", "replan") == 0
    d = S.load(repo)                                  # 旧文件被替换成合法的新文件
    assert set(d["layers"]) == set(S.LAYERS) and "round" in d
    assert "按新建处理" in capsys.readouterr().err


# ---------- --root 必须是 git 仓顶层（T426 / T436）----------

def test_root_in_git_subdirectory_is_rejected(repo, capsys):
    _git(repo, "init", "-q")
    sub = repo / "sub"
    sub.mkdir()
    capsys.readouterr()
    assert run("init", "--root", sub) == 2
    err = capsys.readouterr().err
    assert "问题：" in err and "原因：" in err
    assert f"把 --root 改为仓顶层 {repo.resolve()}" in err


def test_root_at_git_toplevel_is_accepted(repo):
    _git(repo, "init", "-q")
    assert run("init", "--root", repo) == 0


# ---------- set-layer ----------

def test_set_layer_writes_slots(repo):
    run("init", "--root", repo)
    assert run("set-layer", "--root", repo, "--layer", "unit",
               "--how", "go test", "--blind-spots", "不证明消息真穿过 TCP") == 0
    L = S.load(repo)["layers"]["unit"]
    assert L["how"] == "go test"
    assert L["blind_spots"] == "不证明消息真穿过 TCP"
    assert L["convention"] == S.PENDING          # 没给的槽保持待定 —— MUST NOT 替人填


def test_not_applicable_requires_consequence(repo, capsys):
    """不写后果，`不适用` 就是一个不需要负责的逃生舱。"""
    run("init", "--root", repo)
    assert run("set-layer", "--root", repo, "--layer", "e2e",
               "--not-applicable", "--reason", "没时间") == 1
    assert "逃生舱" in capsys.readouterr().err


def test_not_applicable_with_consequence(repo):
    run("init", "--root", repo)
    assert run("set-layer", "--root", repo, "--layer", "e2e", "--not-applicable",
               "--reason", "库无部署形态", "--consequence", "使用者用错 API 我们看不见") == 0
    assert S.load(repo)["layers"]["e2e"]["status"] == S.NOT_APPLICABLE


def test_set_layer_never_writes_layer_status(repo):
    """A25：层状态是投影，MUST NOT 手写 —— 连 CLI 都没有这个入口。"""
    run("init", "--root", repo)
    run("set-layer", "--root", repo, "--layer", "unit", "--how", "x")
    assert "status" not in S.load(repo)["layers"]["unit"]


# ---------- set-lane ----------

def test_set_lane_planned(repo):
    run("init", "--root", repo)
    assert run("set-lane", "--root", repo, "--id", "hermetic", "--layer", "unit",
               "--status", "planned", "--method", "go test ./...",
               "--source", "直接 go test") == 0
    d = S.load(repo)
    assert d["lanes"][0]["id"] == "hermetic"
    assert d["layers"]["unit"]["lane_ids"] == ["hermetic"]


def test_set_lane_rejects_verified(repo, capsys):
    """🔴 verified MUST 由 verify-lane（脚本跑）或 confirm-lane（人跑+人门）产出。"""
    run("init", "--root", repo)
    assert run("set-lane", "--root", repo, "--id", "x", "--layer", "unit",
               "--status", "verified", "--method", "true") == 5
    assert "verify-lane" in capsys.readouterr().err


def test_scaffolded_requires_blocked_by(repo, capsys):
    """「跑不绿」是合法状态，「跑不绿却不说为什么」不是。"""
    run("init", "--root", repo)
    assert run("set-lane", "--root", repo, "--id", "x", "--layer", "unit",
               "--status", "scaffolded", "--method", "go test") == 1
    assert "blocked-by" in capsys.readouterr().err


def test_set_lane_rejects_path_escape(repo, capsys):
    run("init", "--root", repo)
    assert run("set-lane", "--root", repo, "--id", "x", "--layer", "unit",
               "--status", "planned", "--method", "go test",
               "--smoke", "../../../etc/passwd") == 2
    assert "越界" in capsys.readouterr().err


# ---------- ⭐ verify-lane：真 fork 执行 ----------

def test_verify_lane_green(repo, capsys):
    run("init", "--root", repo)
    run("set-lane", "--root", repo, "--id", "ok", "--layer", "unit",
        "--status", "planned", "--method", "true", "--source", "裸命令")
    assert run("verify-lane", "--root", repo, "--id", "ok") == 0

    lane = S.load(repo)["lanes"][0]
    assert lane["status"] == "verified"
    ev = lane["verification"]["evidence"]
    assert ev["exit"] == 0
    assert ev["attested_by"] == "script"        # 脚本验的，不是人说的
    assert "at_commit" in ev and "at_time" in ev
    assert "digest" not in json.dumps(ev)       # A23：无时效锚

    out = capsys.readouterr().out
    assert "不是「当前状态的绿灯」" in out       # 诚实呈现，MUST NOT 佯装无条件的绿


def test_verify_lane_red_becomes_scaffolded_not_failure(repo, capsys):
    """🔴 跑红【不是 skill 的失败】—— 跑不绿是合法状态。退出码仍是 0。"""
    run("init", "--root", repo)
    run("set-lane", "--root", repo, "--id", "bad", "--layer", "unit",
        "--status", "planned", "--method", "echo 'boom' >&2; exit 7", "--source", "x")
    assert run("verify-lane", "--root", repo, "--id", "bad") == 0   # ← 0，不是 7

    lane = S.load(repo)["lanes"][0]
    assert lane["status"] == "scaffolded"
    assert "boom" in lane["blocked_by"] and "exit 7" in lane["blocked_by"]
    assert "evidence" not in lane["verification"]     # 没跑绿 ⇒ 没有证据

    err = capsys.readouterr().err
    assert "不是「调通」" in err                        # 失败不 debug


def test_verify_lane_nonexistent_command_lets_the_tool_judge(repo):
    """A21：「命令能不能跑」由工具自己判 —— 零解析器。

    命令不存在 ⇒ shell 自己报错 ⇒ exit≠0 ⇒ 进不了 verified。
    我们不需要（也不能）事先解析 Makefile 去猜 target 存不存在。
    """
    run("init", "--root", repo)
    run("set-lane", "--root", repo, "--id", "ghost", "--layer", "unit",
        "--status", "planned", "--method", "make no-such-target-anywhere",
        "--source", "x")
    run("verify-lane", "--root", repo, "--id", "ghost")
    assert S.load(repo)["lanes"][0]["status"] == "scaffolded"


def test_verify_lane_timeout(repo):
    run("init", "--root", repo)
    run("set-lane", "--root", repo, "--id", "slow", "--layer", "unit",
        "--status", "planned", "--method", "sleep 5", "--source", "x")
    assert run("verify-lane", "--root", repo, "--id", "slow", "--timeout", "1") == 0
    lane = S.load(repo)["lanes"][0]
    assert lane["status"] == "scaffolded"
    assert "超时" in lane["blocked_by"]
    assert "未确认是环境问题还是 smoke 本身挂了" in lane["blocked_by"]


def test_verify_lane_surfaces_make_overriding_warning(repo, capsys):
    """⭐ A24：target 重名 —— 【让 make 自己回答】。

    GNU make 遇到同名 target 会打 `overriding recipe for target` 到 stderr。
    我们只是【读它已经打出来的那行】—— 零额外执行、零解析器。

    （反面：我一度提议复制 Makefile → `make -n` 探测 —— 那会执行任意代码：
      `$(shell …)` 在解析期就求值，`include` 的 remake 规则会真往仓库写文件。）
    """
    (repo / "Makefile").write_text(
        'integration:\n\t@echo "用户原来的"\n\nintegration:\n\t@echo "skill 追加的"\n',
        encoding="utf-8")
    run("init", "--root", repo)
    run("set-lane", "--root", repo, "--id", "dup", "--layer", "integration",
        "--status", "planned", "--method", "make integration", "--source", "Makefile")
    run("verify-lane", "--root", repo, "--id", "dup")
    err = capsys.readouterr().err
    assert "target 重名" in err
    assert "后定义的赢" in err


def test_verify_lane_refuses_human_executor(repo, capsys):
    run("init", "--root", repo)
    run("set-lane", "--root", repo, "--id", "board", "--layer", "e2e",
        "--status", "planned", "--method", "烧板", "--executor", "human", "--source", "x")
    assert run("verify-lane", "--root", repo, "--id", "board") == 1
    assert "confirm-lane" in capsys.readouterr().err


# ---------- confirm-lane：人说的，如实标 ----------

def test_confirm_lane_marks_human_attested(repo, capsys):
    run("init", "--root", repo)
    run("set-lane", "--root", repo, "--id", "board", "--layer", "e2e",
        "--status", "planned", "--method", "按 SOP 烧板并跑冒烟",
        "--executor", "human", "--source", "board-bringup-sop.md")
    assert run("confirm-lane", "--root", repo, "--id", "board",
               "--confirmed-what", "烧了 3 块板，冒烟全过") == 0

    ev = S.load(repo)["lanes"][0]["verification"]["evidence"]
    assert ev["attested_by"] == "human"       # 🔴 人说的，不是脚本验的
    assert ev["confirmed_what"] == "烧了 3 块板，冒烟全过"
    assert "**人工确认**" in capsys.readouterr().out


def test_confirm_lane_refuses_script_executor(repo, capsys):
    """把「条件不具备」标成「方法没法用程序跑」，是在撒谎。"""
    run("init", "--root", repo)
    run("set-lane", "--root", repo, "--id", "x", "--layer", "unit",
        "--status", "planned", "--method", "go test", "--source", "x")
    assert run("confirm-lane", "--root", repo, "--id", "x", "--confirmed-what", "我跑过了") == 1
    assert "撒谎" in capsys.readouterr().err


# ---------- render ----------

def test_render_shows_banner_and_projection(repo):
    run("init", "--root", repo)
    run("set-lane", "--root", repo, "--id", "ok", "--layer", "unit",
        "--status", "planned", "--method", "true", "--source", "裸命令")
    run("verify-lane", "--root", repo, "--id", "ok")
    run("render", "--root", repo)

    md = (repo / F.STRATEGY_MD).read_text(encoding="utf-8")
    assert "DO NOT EDIT" in md
    assert "格待定" in md                       # 代价横幅
    assert "✅ 已验证" in md                     # unit 层状态 = 从泳道投影
    assert "○ 计划中" in md or "planned" in md
    assert "verified-at" in md                 # MUST 带 commit 锚
    assert "不是「当前状态的绿灯」" in md


def test_render_scaffolded_layer_is_not_called_implemented(repo):
    """A25 回归：从未跑绿的层，MUST NOT 呈现为「已实现」。"""
    run("init", "--root", repo)
    run("set-lane", "--root", repo, "--id", "x", "--layer", "integration",
        "--status", "scaffolded", "--method", "go test -tags=integration ./...",
        "--source", "裸命令", "--blocked-by", "本机无 mosquitto —— brew install mosquitto")
    run("render", "--root", repo)
    md = (repo / F.STRATEGY_MD).read_text(encoding="utf-8")
    assert "已搭好，未验证" in md
    assert "已实现" not in md


def test_render_not_applicable_shows_consequence(repo):
    run("init", "--root", repo)
    run("set-layer", "--root", repo, "--layer", "e2e", "--not-applicable",
        "--reason", "库无部署形态", "--consequence", "使用者用错 API 我们看不见")
    run("render", "--root", repo)
    md = (repo / F.STRATEGY_MD).read_text(encoding="utf-8")
    assert "不适用" in md
    assert "使用者用错 API 我们看不见" in md


# ---------- inject：幂等 ----------

def test_inject_is_idempotent(repo):
    (repo / "CLAUDE.md").write_text("# 项目\n\n原有内容\n", encoding="utf-8")
    run("init", "--root", repo)
    run("inject", "--root", repo)
    once = (repo / "CLAUDE.md").read_text(encoding="utf-8")
    run("inject", "--root", repo)
    twice = (repo / "CLAUDE.md").read_text(encoding="utf-8")
    assert once == twice
    assert twice.count(F.MARK_START) == 1
    assert "原有内容" in twice                  # MUST NOT 覆盖人的东西


def test_inject_replaces_block_in_place():
    text = f"# X\n\n{F.MARK_START}\n旧\n{F.MARK_END}\n\n尾部\n"
    got = F.inject_block(text, "新")
    assert "旧" not in got and "新" in got
    assert "尾部" in got


# ---------- 🔴 红线：skill 没有删除能力（adr/0022）----------

def test_scaffold_has_no_delete_capability():
    """🔴 adr/0022：skill MUST NOT 删除用户的任何文件。

    爆炸半径不受控 —— 指向它的引用可能在【仓外】（书签 / 别的仓 / 代码注释里的路径）。
    连接口都不该有。
    """
    import ast
    src = Path(__file__).resolve().parents[1] / "scripts" / "devenv_scaffold.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))

    # 唯一例外：_prune_lane_logs 只删自己生成、同泳道、文件名严格匹配的失败日志（T435），
    # 且只允许 unlink；其余函数里出现任何删除调用都报红。
    allowed = {"_prune_lane_logs": {"unlink"}}

    def called_names(node):
        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Attribute):
                    yield f.attr
                elif isinstance(f, ast.Name):
                    yield f.id

    banned = {"unlink", "rmtree", "remove", "rmdir"}
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef):
            ok = allowed.get(fn.name, set())
            hits = (set(called_names(fn)) & banned) - ok
            assert not hits, (
                f"scaffold 的 {fn.name}() 里出现了 {sorted(hits)} —— "
                "skill MUST NOT 删除用户文件（adr/0022）"
            )
    module_level = [n for n in tree.body if not isinstance(n, ast.FunctionDef)]
    for node in module_level:
        assert not (set(called_names(node)) & banned), "scaffold 模块级出现了删除调用（adr/0022）"


def test_scaffold_does_not_parse_build_files():
    """🔴 A21：无界语法面禁手搓。MUST NOT import re 去解析 Makefile/shell。"""
    import ast
    src = Path(__file__).resolve().parents[1] / "scripts" / "devenv_scaffold.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    imports = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.add(n.module.split(".")[0])
    assert "re" not in imports, "scaffold MUST NOT import re —— 那是通往手搓解析器的路（A21）"


# ---------- environments.md：模版骨架（人写区，零机械渲染）----------

def test_init_seeds_environments_skeleton(repo, capsys):
    """environments.md 不是「skill 给个初稿」—— skill 铺【十槽骨架】，然后逐槽问出来。"""
    run("init", "--root", repo)
    md = (repo / F.ENV_MD).read_text(encoding="utf-8")
    assert md.count(S.PENDING) == 10          # 十槽全待定
    for _, title in F.ENV_SLOTS:
        assert title in md
    assert "10 槽全待定" in capsys.readouterr().out


def test_environments_test_section_is_a_pointer_only(repo):
    """切线 = 测试 vs 非测试。MUST NOT 在 environments.md 里复述测试命令（双写必漂移）。"""
    run("init", "--root", repo)
    md = (repo / F.ENV_MD).read_text(encoding="utf-8")
    body = md.split("## 2. 测试")[1].split("## 3.")[0]
    assert "testing-strategy.md" in body
    assert S.PENDING not in body               # test 节没有槽 —— 它只是一行指针


def test_init_never_overwrites_existing_environments(repo):
    """铺完就归人 own —— skill MUST NOT 覆盖它（它是纯人写，零机械渲染）。"""
    (repo / "openspec" / "architecture").mkdir(parents=True)
    (repo / F.ENV_MD).write_text("# 我自己写的\n\n别动我\n", encoding="utf-8")
    run("init", "--root", repo)
    assert "别动我" in (repo / F.ENV_MD).read_text(encoding="utf-8")


def test_render_never_touches_environments(repo):
    """render 只管 testing-strategy.md。environments.md 零机械渲染。"""
    run("init", "--root", repo)
    (repo / F.ENV_MD).write_text("# 人填过的\n\n常见坑：AirPlay 占 5000 端口\n",
                                 encoding="utf-8")
    run("render", "--root", repo)
    assert "AirPlay" in (repo / F.ENV_MD).read_text(encoding="utf-8")


# ---------- verify-lane 失败日志落盘（tasks 5.1）----------

RUNS = "openspec/architecture/.devenv-runs"


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
         "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=True).stdout


def _git_commit_all(repo, msg="c"):
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--allow-empty", "-m", msg)


def _lane(repo, lid, method, **kw):
    argv = ["set-lane", "--root", repo, "--id", lid, "--layer", "unit",
            "--status", "planned", "--method", method, "--source", "x"]
    for k, v in kw.items():
        argv += [f"--{k.replace('_', '-')}", v]
    assert run(*argv) == 0


def _blocked_by(repo, lid):
    return next(l for l in S.load(repo)["lanes"] if l["id"] == lid)["blocked_by"]


def _log_path_of(repo, blocked_by):
    rel = blocked_by.partition("日志：")[2]
    assert rel, blocked_by
    return rel, repo / rel


def test_failed_lane_without_output_writes_log_and_no_duplicate_exit(repo):
    run("init", "--root", repo)
    _lane(repo, "quiet", "exit 1")
    assert run("verify-lane", "--root", repo, "--id", "quiet") == 0
    bb = _blocked_by(repo, "quiet")
    rel, path = _log_path_of(repo, bb)
    assert bb == f"无输出（exit 1）· 日志：{rel}"
    assert bb.count("exit 1") == 1
    assert rel.startswith(f"{RUNS}/quiet-") and rel.endswith(".log")
    assert path.is_file()


def test_failed_lane_with_output_keeps_last_80_lines(repo):
    run("init", "--root", repo)
    _lane(repo, "noisy", "seq 1 200; echo oops >&2; exit 2")
    run("verify-lane", "--root", repo, "--id", "noisy")
    bb = _blocked_by(repo, "noisy")
    rel, path = _log_path_of(repo, bb)
    assert bb.startswith("oops（exit 2）· 日志：")
    text = path.read_text(encoding="utf-8")
    out_lines = text.split("## stdout")[1].split("## stderr")[0].split()
    assert out_lines[-80:] == [str(i) for i in range(121, 201)]
    assert "120" not in out_lines
    assert "oops" in text.split("## stderr")[1]


def test_stderr_whitespace_only_falls_back_to_stdout_in_summary(repo):
    run("init", "--root", repo)
    _lane(repo, "ws", "echo real-out; printf '  \\n' >&2; exit 3")
    run("verify-lane", "--root", repo, "--id", "ws")
    assert _blocked_by(repo, "ws").startswith("real-out（exit 3）")


def test_log_keeps_only_latest_five_per_lane(repo):
    run("init", "--root", repo)
    runs = repo / RUNS
    for _ in range(7):
        F._write_failure_log(repo, "a", 1, False, "o", "e")
    F._write_failure_log(repo, "ab", 1, False, "o", "e")        # 前缀相近的另一泳道
    (runs / "a-notes.log").write_text("手写\n", encoding="utf-8")   # 文件名形状不符：不是本脚本生成的
    F._write_failure_log(repo, "a", 1, False, "o", "e")
    assert len(F._lane_logs(runs, "a")) == 5
    assert len(F._lane_logs(runs, "ab")) == 1
    assert (runs / "a-notes.log").is_file()
    assert (runs / ".gitignore").is_file()


def test_log_line_over_2000_chars_is_truncated(repo):
    run("init", "--root", repo)
    _lane(repo, "wide", "head -c 5000 /dev/zero | tr '\\0' x; echo; exit 1")
    run("verify-lane", "--root", repo, "--id", "wide")
    _, path = _log_path_of(repo, _blocked_by(repo, "wide"))
    text = path.read_text(encoding="utf-8")
    assert "x" * 2000 + "…（已截断）" in text
    assert "x" * 2001 not in text


def test_log_names_carry_microseconds_and_never_overwrite(repo, monkeypatch):
    real = datetime(2026, 10, 23, 1, 2, 3, 456789, tzinfo=timezone.utc)

    class FixedNow(datetime):
        @classmethod
        def now(cls, tz=None):
            return real

    monkeypatch.setattr(F, "datetime", FixedNow)
    rel1 = F._write_failure_log(repo, "x", 1, False, "first", "")
    rel2 = F._write_failure_log(repo, "x", 1, False, "second", "")
    assert "20261023T010203456789Z" in rel1
    assert rel1 != rel2 and rel2.endswith("-2.log")
    assert "first" in (repo / rel1).read_text(encoding="utf-8")
    assert "second" in (repo / rel2).read_text(encoding="utf-8")


def test_timeout_keeps_partial_output_in_log(repo):
    run("init", "--root", repo)
    _lane(repo, "slow2", "echo before-timeout; sleep 5")
    run("verify-lane", "--root", repo, "--id", "slow2", "--timeout", "1")
    bb = _blocked_by(repo, "slow2")
    _, path = _log_path_of(repo, bb)
    assert bb.startswith("超时（1s）")
    assert "before-timeout" in path.read_text(encoding="utf-8")


def test_lane_id_with_path_chars_stays_inside_runs_dir(repo):
    run("init", "--root", repo)
    _lane(repo, "../x", "exit 3")
    run("verify-lane", "--root", repo, "--id", "../x")
    _, path = _log_path_of(repo, _blocked_by(repo, "../x"))
    assert path.parent == (repo / RUNS).resolve()
    assert "/" not in path.name


def test_unwritable_runs_dir_warns_and_still_records_lane(repo, capsys):
    run("init", "--root", repo)
    (repo / RUNS).parent.mkdir(parents=True, exist_ok=True)
    (repo / RUNS).write_text("占位文件，使目录创建失败", encoding="utf-8")
    _lane(repo, "bad", "echo boom >&2; exit 7")
    assert run("verify-lane", "--root", repo, "--id", "bad") == 0
    lane = S.load(repo)["lanes"][0]
    assert lane["status"] == "scaffolded"
    assert lane["blocked_by"] == "boom（exit 7）"
    assert "日志写入失败" in capsys.readouterr().err


def test_failure_log_is_not_tracked_by_git(repo):
    _git(repo, "init", "-q")
    run("init", "--root", repo)
    _lane(repo, "g", "echo x; exit 1")
    run("verify-lane", "--root", repo, "--id", "g")
    status = _git(repo, "status", "--porcelain", "--untracked-files=all")
    assert ".log" not in status
    assert f"{RUNS}/.gitignore" in status          # .gitignore 自身可被跟踪
    ig = (repo / RUNS / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "*" in ig and "!.gitignore" in ig


def test_runs_gitignore_only_appends_missing_lines(repo):
    run("init", "--root", repo)
    (repo / RUNS).mkdir(parents=True)
    (repo / RUNS / ".gitignore").write_text("keep-me\n*", encoding="utf-8")
    _lane(repo, "g", "exit 1")
    run("verify-lane", "--root", repo, "--id", "g")
    ig = (repo / RUNS / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ig == ["keep-me", "*", "!.gitignore"]


def test_non_utf8_runs_gitignore_warns_and_still_records_lane(repo, capsys):
    run("init", "--root", repo)
    (repo / RUNS).mkdir(parents=True)
    (repo / RUNS / ".gitignore").write_bytes(b"keep-\xff\xfe\n")   # [impl-review-fix] P1: 非 UTF-8 字节
    _lane(repo, "bad", "echo boom >&2; exit 7")
    assert run("verify-lane", "--root", repo, "--id", "bad") == 0
    lane = S.load(repo)["lanes"][0]
    assert lane["status"] == "scaffolded"
    assert lane["blocked_by"] == "boom（exit 7）"
    assert "日志写入失败" in capsys.readouterr().err


# ---------- 证据记录工作区是否干净（tasks 5.2）----------

def _committed_repo(repo):
    """仓已提交 devenv 产物 —— 之后的改动才算「未提交」。"""
    _git(repo, "init", "-q")
    run("init", "--root", repo)
    _git_commit_all(repo)


def _evidence_of(repo, lid):
    lane = next(l for l in S.load(repo)["lanes"] if l["id"] == lid)
    return lane["verification"]["evidence"]


def test_dirty_true_when_uncommitted_change_and_prompts(repo, capsys):
    _committed_repo(repo)
    _lane(repo, "ok", "true")
    (repo / "smoke.sh").write_text("echo hi\n", encoding="utf-8")    # 未提交的非 devenv 文件
    assert run("verify-lane", "--root", repo, "--id", "ok") == 0
    assert S.load(repo)["lanes"][0]["status"] == "verified"           # 不阻止执行与写入
    assert _evidence_of(repo, "ok")["dirty"] is True
    assert "工作区有未提交改动，提交后重跑才有可复现的锚" in capsys.readouterr().err


def test_dirty_false_when_clean(repo):
    _committed_repo(repo)
    _lane(repo, "ok", "true")
    _git_commit_all(repo)
    assert run("verify-lane", "--root", repo, "--id", "ok") == 0
    assert _evidence_of(repo, "ok")["dirty"] is False


def test_dirty_false_when_only_devenv_owned_files_uncommitted(repo):
    _committed_repo(repo)
    arch = repo / "openspec" / "architecture"
    (arch / "testing-strategy.md").write_text("x\n", encoding="utf-8")
    (arch / "devenv-review.md").write_text("x\n", encoding="utf-8")
    (arch / "review").mkdir()
    (arch / "review" / "devenv-review.html").write_text("x\n", encoding="utf-8")
    (arch / ".outside-voice" / "r1").mkdir(parents=True)
    (arch / ".outside-voice" / "r1" / "lens-a.md").write_text("x\n", encoding="utf-8")
    (arch / ".devenv-runs").mkdir()
    (arch / ".devenv-runs" / "a.log").write_text("x\n", encoding="utf-8")
    _lane(repo, "ok", "true")                    # 改了 .devenv.json 与 devenv-log.md
    assert run("verify-lane", "--root", repo, "--id", "ok") == 0
    assert _evidence_of(repo, "ok")["dirty"] is False


def test_dirty_key_absent_without_repo(repo):
    run("init", "--root", repo)
    _lane(repo, "ok", "true")
    run("verify-lane", "--root", repo, "--id", "ok")
    assert "dirty" not in _evidence_of(repo, "ok")


def test_confirm_lane_records_dirty(repo):
    _committed_repo(repo)
    _lane(repo, "board", "按 SOP 烧板", executor="human")
    (repo / "notes.txt").write_text("x\n", encoding="utf-8")
    assert run("confirm-lane", "--root", repo, "--id", "board",
               "--confirmed-what", "烧了") == 0
    assert _evidence_of(repo, "board")["dirty"] is True


def test_review_summary_marks_dirty_evidence_in_section_4(repo):
    _committed_repo(repo)
    _lane(repo, "ok", "true")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    run("verify-lane", "--root", repo, "--id", "ok")
    assert "未提交改动" in _section(_review(repo), 4)


def test_render_marks_dirty_evidence(repo):
    _committed_repo(repo)
    _lane(repo, "ok", "true")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    run("verify-lane", "--root", repo, "--id", "ok")
    run("render", "--root", repo)
    assert "未提交改动" in (repo / F.STRATEGY_MD).read_text(encoding="utf-8")


# ---------- 本轮起点 round（tasks 5.3）----------

def test_init_new_writes_round(repo):
    _git(repo, "init", "-q")
    _git_commit_all(repo)
    head = _git(repo, "rev-parse", "HEAD").strip()
    run("init", "--root", repo)
    rnd = S.load(repo)["round"]
    assert rnd["base_commit"] == head
    assert rnd["started_at"].endswith("Z")


def test_init_new_without_repo_records_no_git(repo):
    run("init", "--root", repo)
    assert S.load(repo)["round"]["base_commit"] == "(no-git)"


def test_continue_keeps_existing_round(repo):
    _git(repo, "init", "-q")
    _git_commit_all(repo)
    run("init", "--root", repo)
    before = S.load(repo)["round"]
    _git_commit_all(repo, "more")
    assert run("init", "--root", repo, "--on-exists", "continue") == 0
    assert S.load(repo)["round"] == before


def test_replan_resets_round(repo):
    _git(repo, "init", "-q")
    _git_commit_all(repo)
    run("init", "--root", repo)
    _git_commit_all(repo, "more")
    head = _git(repo, "rev-parse", "HEAD").strip()
    assert run("init", "--root", repo, "--on-exists", "replan") == 0
    assert S.load(repo)["round"]["base_commit"] == head


def test_continue_backfills_missing_round(repo):
    _git(repo, "init", "-q")
    _git_commit_all(repo)
    run("init", "--root", repo)
    data = S.load(repo)
    del data["round"]
    S.save(repo, data)
    head = _git(repo, "rev-parse", "HEAD").strip()
    assert run("init", "--root", repo, "--on-exists", "continue") == 0
    assert S.load(repo)["round"]["base_commit"] == head


# ---------- set-review-docs（tasks 5.4）----------

def test_set_review_docs_success_overwrites(repo):
    run("init", "--root", repo)
    (repo / "docs").mkdir()
    (repo / "docs" / "command-testing.md").write_text("# x\n", encoding="utf-8")
    (repo / "docs" / "other.md").write_text("# y\n", encoding="utf-8")
    assert run("set-review-docs", "--root", repo, "--path", "docs/command-testing.md") == 0
    assert S.load(repo)["review"]["extra_docs"] == ["docs/command-testing.md"]
    assert run("set-review-docs", "--root", repo, "--path", "docs/other.md") == 0
    assert S.load(repo)["review"]["extra_docs"] == ["docs/other.md"]       # 覆盖写


def test_set_review_docs_rejects_escape_and_keeps_file(repo, capsys):
    run("init", "--root", repo)
    (repo / "docs").mkdir()
    (repo / "docs" / "ok.md").write_text("# y\n", encoding="utf-8")
    before = (repo / S.DEVENV_REL).read_text(encoding="utf-8")
    assert run("set-review-docs", "--root", repo,
               "--path", "docs/ok.md", "--path", "../outside.md") == 2    # 任一失败整条拒绝
    assert (repo / S.DEVENV_REL).read_text(encoding="utf-8") == before
    assert "../outside.md" in capsys.readouterr().err


def test_set_review_docs_rejects_non_markdown(repo):
    run("init", "--root", repo)
    (repo / ".env").write_text("SECRET=1\n", encoding="utf-8")
    before = (repo / S.DEVENV_REL).read_text(encoding="utf-8")
    assert run("set-review-docs", "--root", repo, "--path", ".env") == 2
    assert (repo / S.DEVENV_REL).read_text(encoding="utf-8") == before


def test_set_review_docs_rejects_missing_file_and_dot_git_dir(repo):
    run("init", "--root", repo)
    (repo / ".git").mkdir()
    (repo / ".git" / "x.md").write_text("x\n", encoding="utf-8")
    assert run("set-review-docs", "--root", repo, "--path", "nope.md") == 2
    assert run("set-review-docs", "--root", repo, "--path", ".git/x.md") == 2


def test_set_review_docs_recovers_from_null_review_section(repo):
    run("init", "--root", repo)
    (repo / "docs").mkdir()
    (repo / "docs" / "a.md").write_text("# a\n", encoding="utf-8")
    data = S.load(repo)
    data["review"] = None                                  # [impl-review-fix] C1: review 为 null 不得 TypeError
    S.save(repo, data)
    assert run("set-review-docs", "--root", repo, "--path", "docs/a.md") == 0
    assert S.load(repo)["review"]["extra_docs"] == ["docs/a.md"]


# ---------- 汇总 devenv-review.md（tasks 6.1）----------

REVIEW_SECTIONS = ["结论", "需要人拍板的事项", "三层框架", "泳道与证据",
                   "环境文档", "落地物清单", "冷审处置", "本轮新增 issues"]


def _review(repo):
    assert run("render", "--root", repo) == 0
    return (repo / "openspec" / "architecture" / "devenv-review.md").read_text(encoding="utf-8")


def _section(text, n):
    """第 n 节（1 起）的正文：到下一个 `## ` 标题为止。"""
    parts = text.split("\n## ")
    return parts[n]


def _round_repo(repo):
    """有基线提交的仓：round.base_commit 是真提交号（_committed_repo 在无提交的仓里 init，起点是 (no-git)）。"""
    _git(repo, "init", "-q")
    _git_commit_all(repo, "base")
    run("init", "--root", repo)
    _git_commit_all(repo, "devenv")


def test_review_has_eight_sections_in_order(repo):
    _committed_repo(repo)
    text = _review(repo)
    assert "DO NOT EDIT" in text
    heads = [ln for ln in text.splitlines() if ln.startswith("## ")]
    assert heads == [f"## {i}. {name}" for i, name in enumerate(REVIEW_SECTIONS, 1)]


def test_review_conclusion_has_cost_banner_same_as_strategy(repo):
    _committed_repo(repo)
    text = _review(repo)
    banner = "> ⚠️ 本框架 15/15 格待定，尚不构成一份可用的测试策略。"
    assert banner in _section(text, 1)
    assert banner in (repo / F.STRATEGY_MD).read_text(encoding="utf-8")


def test_review_failed_lane_links_log_but_never_embeds_it(repo):
    _committed_repo(repo)
    _lane(repo, "bad", "printf 'SECRET-%s\\n' OUT-9; echo boom >&2; exit 3")
    run("verify-lane", "--root", repo, "--id", "bad")
    rel, log_file = _log_path_of(repo, _blocked_by(repo, "bad"))
    assert "SECRET-OUT-9" in log_file.read_text(encoding="utf-8")     # 前提：日志里确有这段输出
    text = _review(repo)
    lanes = _section(text, 4)
    assert "`bad`" in lanes
    assert _blocked_by(repo, "bad").split("· 日志：")[0] in lanes
    assert rel.replace("openspec/architecture/", "") in lanes          # 相对路径链接
    assert "SECRET-OUT-9" not in text                  # 日志里的 stdout 不进汇总


def test_review_lists_invalidated_files_with_git_rm(repo):
    _committed_repo(repo)
    (repo / "docs").mkdir()
    (repo / "docs" / "old.md").write_text("\n> ⚠️ 已失效\n\n旧文档\n", encoding="utf-8")
    (repo / "docs" / "mention.md").write_text(
        "# 说明\n\n正文里引用：\n> ⚠️ 已失效\n这行文字\n", encoding="utf-8")
    _git_commit_all(repo)
    (repo / "docs" / "fresh.md").write_text("> ⚠️ 已失效\n未提交的新文件\n", encoding="utf-8")
    text = _section(_review(repo), 2)
    assert "git rm docs/old.md" in text
    assert "docs/fresh.md" in text                      # 未跟踪未忽略的候选也列入
    assert "mention.md" not in text                     # 正文引用不算：只看首个非空行


def test_review_lists_pending_environment_lines_and_unverified_lanes(repo):
    _committed_repo(repo)
    _lane(repo, "p", "true")
    run("init", "--root", repo, "--on-exists", "continue")
    run("set-layer", "--root", repo, "--layer", "e2e", "--not-applicable",
        "--reason", "库无部署形态", "--consequence", "看不见端到端")
    text = _section(_review(repo), 2)
    assert "environments.md" in text and S.PENDING in text    # 行号 + 原文行
    assert "`p`" in text                                      # planned 泳道
    assert "库无部署形态" in text and "看不见端到端" in text   # 不适用的层


def test_review_twice_is_byte_identical_and_lists_uncommitted_without_derived(repo):
    _round_repo(repo)
    (repo / "new.txt").write_text("x\n", encoding="utf-8")
    arch = repo / "openspec" / "architecture"
    (arch / "review").mkdir(exist_ok=True)
    (arch / "review" / "devenv-review.html").write_text("<html>", encoding="utf-8")
    first = _review(repo)
    second = _review(repo)
    assert first == second
    landed = _section(first, 6)
    assert "new.txt" in landed
    for derived in ("devenv-review.md", "review/", ".devenv-runs/"):
        assert derived not in landed


def test_review_landing_and_issues_come_from_git_relative_to_round_start(repo):
    _round_repo(repo)
    (repo / "src.py").write_text("print(1)\n", encoding="utf-8")
    (repo / "openspec" / "issues" / "open").mkdir(parents=True)
    (repo / "openspec" / "issues" / "open" / "T9.md").write_text("# T9\n", encoding="utf-8")
    _git_commit_all(repo, "work")
    (repo / "openspec" / "issues" / "open" / "T10.md").write_text("# T10\n", encoding="utf-8")
    text = _review(repo)
    assert "src.py" in _section(text, 6)
    issues = _section(text, 8)
    assert "T9.md" in issues and "T10.md" in issues       # 已提交的新增 + 未跟踪的新增


def test_review_issues_include_added_but_uncommitted(repo):
    _round_repo(repo)
    d = repo / "openspec" / "issues" / "open"
    d.mkdir(parents=True)
    (d / "T11.md").write_text("# T11\n", encoding="utf-8")
    _git(repo, "add", "openspec/issues/open/T11.md")      # [impl-review-fix] V2: 已 add 未提交
    assert "T11.md" in _section(_review(repo), 8)


def test_review_ignores_outside_voice_symlinked_outside_repo(repo, tmp_path_factory):
    _round_repo(repo)
    outside = tmp_path_factory.mktemp("ov-outside")
    run_d = outside / "99990101T000000Z-aaaaaa"
    run_d.mkdir()
    (run_d / "disposition.md").write_text("LEAKED-DISPOSITION\n", encoding="utf-8")
    (run_d / "lens-leak.md").write_text("# leak\n", encoding="utf-8")
    link = repo / "openspec" / "architecture" / ".outside-voice"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("无法创建软链：Windows 开启开发者模式或以管理员运行后重跑")
    text = _review(repo)
    assert "LEAKED-DISPOSITION" not in text
    assert F._pick_run_dir(repo.resolve(), S.load(repo)) is None   # [impl-review-fix] H2


def test_review_unreachable_base_says_cannot_compute_and_exit_zero(repo):
    _round_repo(repo)
    data = S.load(repo)
    data["round"]["base_commit"] = "f" * 40               # rebase 之后起点不可达
    S.save(repo, data)
    text = _review(repo)
    for n in (6, 8):
        sec = _section(text, n)
        assert "无法计算" in sec and "replan" in sec


def test_review_without_round_or_git_says_cannot_compute(repo):
    run("init", "--root", repo)                            # 无 git ⇒ (no-git)
    text = _review(repo)
    assert "无法计算" in _section(text, 6) and "无法计算" in _section(text, 8)
    data = S.load(repo)
    del data["round"]
    S.save(repo, data)
    text = _review(repo)
    assert "continue" in _section(text, 6)                 # 提示补记


def _outside_voice_run(repo, name, disposition=None, lens=()):
    d = repo / "openspec" / "architecture" / ".outside-voice" / name
    d.mkdir(parents=True)
    if disposition is not None:
        (d / "disposition.md").write_text(disposition, encoding="utf-8")
    for l in lens:
        (d / l).write_text(f"# {l}\n", encoding="utf-8")
    return d


def test_review_picks_latest_run_with_disposition_not_older_than_round(repo):
    _round_repo(repo)
    started = S.load(repo)["round"]["started_at"]          # 2026-..T..Z
    compact = started.replace("-", "").replace(":", "")
    _outside_voice_run(repo, "20000101T000000Z-aaaaaa", disposition="OLD-DISPOSITION\n")
    _outside_voice_run(repo, compact + "-bbbbbb", disposition="MID-DISPOSITION\n")
    _outside_voice_run(repo, "99990101T000000Z-cccccc")    # 更新，但没有 disposition.md
    sec = _section(_review(repo), 7)
    assert "MID-DISPOSITION" in sec
    assert "OLD-DISPOSITION" not in sec


def test_review_without_disposition_says_none(repo):
    _committed_repo(repo)
    assert "本轮无冷审处置记录" in _section(_review(repo), 7)


# ---------- review-page 子命令（tasks 6.2）----------

import shutil  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
GEN_SRC = REPO_ROOT / "sdflow-init" / "assets" / "hack"


@pytest.fixture
def sdflow_home(tmp_path, monkeypatch):
    """含仓内生成器与评审页资产的临时 SDFLOW_HOME（不碰真实 ~/.sdflow）。"""
    home = tmp_path / "sdhome"
    (home / "hack").mkdir(parents=True)
    shutil.copy(GEN_SRC / "render-review-page.py", home / "hack" / "render-review-page.py")
    shutil.copytree(GEN_SRC / "review-page", home / "hack" / "review-page")
    monkeypatch.setenv("SDFLOW_HOME", str(home))
    return home


def _page_repo(tmp_path):
    repo = tmp_path / "proj"
    (repo / "openspec").mkdir(parents=True)
    _round_repo(repo)
    return repo


def _page_docs(repo):
    log = json.loads((repo / "openspec/architecture/review/devenv-review.revisions.json")
                     .read_text(encoding="utf-8"))
    return log["revisions"][-1]["docs"]


def test_review_page_generates_page_with_required_and_optional_docs(tmp_path, sdflow_home, capsys):
    repo = _page_repo(tmp_path)
    _outside_voice_run(repo, "99990101T000000Z-aaaaaa", disposition="处置\n",
                       lens=("lens-vacuous.md", "lens-blind.md"))
    assert run("render", "--root", repo) == 0
    capsys.readouterr()
    assert run("review-page", "--root", repo, "--no-open", "--event", "冷审处置完成") == 0
    out = capsys.readouterr().out
    html = repo / "openspec" / "architecture" / "review" / "devenv-review.html"
    assert html.is_file() and f"评审页：{html}" in out
    docs = _page_docs(repo)
    assert {"devenv-review", "testing-strategy", "environments",
            "lens-vacuous", "lens-blind"} <= set(docs)
    log = json.loads((html.parent / "devenv-review.revisions.json").read_text(encoding="utf-8"))
    assert log["revisions"][-1]["event"] == "冷审处置完成"


def test_review_page_generator_missing_prints_hint_and_exits_zero(tmp_path, monkeypatch, capsys):
    empty_home = tmp_path / "empty-home"
    empty_home.mkdir()
    monkeypatch.setenv("SDFLOW_HOME", str(empty_home))
    repo = _page_repo(tmp_path)
    run("render", "--root", repo)
    capsys.readouterr()
    assert run("review-page", "--root", repo, "--no-open") == 0
    out = capsys.readouterr()
    text = out.out + out.err
    assert "评审页未生成" in text and "在运行 checkout 跑 bash setup.sh" in text
    assert not (repo / "openspec/architecture/review/devenv-review.html").exists()


def test_review_page_generator_failure_does_not_block(tmp_path, sdflow_home, capsys):
    repo = _page_repo(tmp_path)               # 没跑 render ⇒ 必有文档 devenv-review.md 缺失
    assert run("review-page", "--root", repo, "--no-open") == 0
    assert "评审页未生成" in capsys.readouterr().out


def test_review_page_same_named_readmes_get_distinct_labels(tmp_path, sdflow_home):
    repo = _page_repo(tmp_path)
    for d in ("docs", "guide"):
        (repo / d).mkdir()
        (repo / d / "README.md").write_text(f"# {d}\n", encoding="utf-8")
    assert run("set-review-docs", "--root", repo,
               "--path", "docs/README.md", "--path", "guide/README.md") == 0
    run("render", "--root", repo)
    assert run("review-page", "--root", repo, "--no-open") == 0
    docs = _page_docs(repo)
    assert docs["README"]["path"] == "docs/README.md"
    assert docs["guide-README"]["path"] == "guide/README.md"


def test_review_page_skips_extra_doc_that_no_longer_qualifies(tmp_path, sdflow_home, capsys):
    repo = _page_repo(tmp_path)
    (repo / "docs").mkdir()
    (repo / "docs" / "gone.md").write_text("# x\n", encoding="utf-8")
    run("set-review-docs", "--root", repo, "--path", "docs/gone.md")
    (repo / "docs" / "gone.md").unlink()                       # 配置之后文件消失
    run("render", "--root", repo)
    capsys.readouterr()
    assert run("review-page", "--root", repo, "--no-open") == 0
    cap = capsys.readouterr()
    assert "docs/gone.md" in cap.err                           # 告警并跳过
    assert "gone" not in _page_docs(repo)
