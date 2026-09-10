"""全部顶层 `*/SKILL.md` 的 YAML frontmatter 必须可解析且含非空 name/description（T296）。

输入面复用 setup.sh 的安装判据（顶层目录含 SKILL.md）——setup.sh 只认文件存在、不校验
能否解析，写坏会被静默装上；最早能拦住的机械点是编辑后的首次 pytest/CI，即本文件。

手段（CLAUDE.md 基准 5）：YAML 本体是无界语法面，MUST NOT import yaml（零依赖不变量，
CI 泳道只装 pinned yq、不装 PyYAML）也 MUST NOT 手搓解析——交给 yq 原生
`--front-matter=extract`（与 `ship_gate._yq` 同一 idiom；这里刻意**不**命名为 `_yq`、
不进 `test_yq_wrapper_consistency` 的拷贝名册——它是测试内的一次性薄调用，非新消费点）。
yq 缺失 / 装错（kislyuk 版不识 `--front-matter`）都走 fail-loud，先例
`test_frontmatter_parse.py` 同样如此。上游动机：matt 套件 fix/907（frontmatter 值里的
冒号击穿手搓解析）——yq 真解析下该类写坏会以非零退出或非字符串值形态被下面两条断言拦住。
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILL_FILES = sorted(REPO.glob("*/SKILL.md"))


def test_scan_face_nonempty():
    """本门自身的 L3：本仓定义上就是 skills 集合，扫出 0 个 = 扫描面坏了，
    MUST NOT 让下方 parametrize 静默变空集恒真。不写死数量——skill 会增删。"""
    assert SKILL_FILES, "顶层 */SKILL.md 一个都没找到——glob 或仓根解析坏了"


@pytest.mark.parametrize("skill_md", SKILL_FILES, ids=lambda p: p.parent.name)
def test_frontmatter_parses_and_has_name_description(skill_md):
    yq = shutil.which("yq")
    assert yq is not None, (
        "yq(mikefarah) 未安装——本门依赖它解析 YAML（macOS: brew install yq）")

    text = skill_md.read_text(encoding="utf-8")
    assert text.lstrip("\ufeff").startswith("---\n"), (
        f"{skill_md.parent.name}/SKILL.md 首行不是 `---`——缺 frontmatter，"
        "setup.sh 会照装不误但运行时无法识别该 skill")

    result = subprocess.run(
        [yq, "--front-matter=extract", "-o", "json", ".", str(skill_md)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    # 只信 returncode，不检查 stderr 内容——yq 在 Windows 上每次 --front-matter 调用
    # 都会往 stderr 打一行临时文件清理噪音（ship_gate._yq F11 已核实的已知行为）。
    assert result.returncode == 0, (
        f"{skill_md.parent.name}/SKILL.md frontmatter 不是合法 YAML：\n{result.stderr}")

    data = json.loads(result.stdout)
    assert isinstance(data, dict), (
        f"{skill_md.parent.name}/SKILL.md frontmatter 顶层应为映射，"
        f"实为 {type(data).__name__}")
    for key in ("name", "description"):
        value = data.get(key)
        assert isinstance(value, str) and value.strip(), (
            f"{skill_md.parent.name}/SKILL.md frontmatter 缺 {key} 或其值非非空字符串"
            f"（实为 {value!r}）")
