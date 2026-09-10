"""devenv_scaffold 的测试 —— B 层（手）。

重点在 verify-lane：它是 skill 唯一「产生新事实」的地方（真 fork 执行，拿真 exit code）。
"""
import json
import sys
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
        "--executor", "human", "--source", "embedded-test-sop")
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

    calls = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute):
                calls.add(f.attr)
            elif isinstance(f, ast.Name):
                calls.add(f.id)

    for banned in ("unlink", "rmtree", "remove", "rmdir"):
        assert banned not in calls, (
            f"scaffold 里出现了 {banned}() —— skill MUST NOT 删除用户文件（adr/0022）"
        )


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
