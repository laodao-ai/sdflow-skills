#!/usr/bin/env python3
"""生成 openspec/roadmaps/{name}/review.html —— roadmap 四件套产出后顺手落一份查看器 stub。

读取项目根 openspec/workflow/tools/review-stub.html 模板（由 opsx-project-init 铺设），替换
__PROJECT_NAME__（项目根目录名，对一次安装永不变，故不重蹈 __SCOPE__ 的过时症）后写为
openspec/roadmaps/{name}/review.html——目录 scope 不再靠模板占位符固化，而由 engine.js 在
加载时从 window.location.pathname 推导。

与 change-review-stub.py 那个 hook 的取舍不同：hook 是自动触发、缺前提静默跳过；这里是
opsx-roadmap-planner 流程里模型显式调用的一步，缺前提直接抛错更利于及时发现。
"""
import argparse
import os
import sys


def gen_review_stub(root, name):
    osroot = os.path.join(root, "openspec")
    stub_template_path = os.path.join(osroot, "workflow", "tools", "review-stub.html")
    root_review_path = os.path.join(osroot, "review.html")
    if not (os.path.isfile(stub_template_path) and os.path.isfile(root_review_path)):
        raise FileNotFoundError(
            "项目未铺设 review 工具（缺 openspec/workflow/tools/review-stub.html 或 openspec/review.html）。"
            "先跑 opsx-project-init init/update。"
        )
    roadmap_dir = os.path.join(osroot, "roadmaps", name)
    if not os.path.isdir(roadmap_dir):
        raise FileNotFoundError(f"目录不存在：{roadmap_dir}（应在四件套生成之后再跑本脚本）")

    dst = os.path.join(roadmap_dir, "review.html")
    project_name = os.path.basename(os.path.abspath(root))
    template_text = open(stub_template_path, encoding="utf-8").read()
    rendered = template_text.replace("__PROJECT_NAME__", project_name)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(rendered)
    return dst


def main():
    p = argparse.ArgumentParser(description="生成 roadmap 目录的 review.html stub")
    p.add_argument("name", help="roadmap 目录名（kebab-case，即 openspec/roadmaps/<name>/）")
    p.add_argument("--root", default=".", help="项目根（默认当前目录）")
    args = p.parse_args()
    try:
        dst = gen_review_stub(args.root, args.name)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"✓ 已生成 {dst}")


if __name__ == "__main__":
    main()
