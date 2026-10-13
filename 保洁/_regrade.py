# -*- coding: utf-8 -*-
"""用新调色档（clean）重做已生成的成片。

为什么要重做而不是直接改文件：
`grade_one()` 是**原地替换**。已经用 legacy 曲线调过的成片，黑位已经被抬到 40，
再套新曲线只会更灰（叠两次抬黑位）。必须**从 _raw 的原片重新调**。

流程：
  1. 把 _raw 的原片复制回输出目录（覆盖当前已调色的成片）
  2. 调用 _grade.grade_one() 走新曲线
  3. 刷新 PNG 预览 + 复测分位，确认黑位/对比度回到目标区间

用法：
  python _regrade.py             # 处理 D:\output\new 下所有 xs01_* 成片
  python _regrade.py D:\output   # 指定目录
"""
import glob
import os
import shutil
import subprocess
import sys

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _grade  # noqa: E402


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else r"D:\output\new"
    raw_dir = os.path.join(d, "_raw")
    if not os.path.isdir(raw_dir):
        print("找不到原片目录:", raw_dir)
        return 1
    # 只处理有原片可回退的
    raws = sorted(glob.glob(os.path.join(raw_dir, "*.mp4")))
    if not raws:
        print("原片目录为空:", raw_dir)
        return 1
    print("调色档 :", _grade.GRADE.get("curve", "?"), "| sat", _grade.GRADE["sat"])
    print("原片数 :", len(raws))
    print()

    ok = bad = 0
    for r in raws:
        name = os.path.basename(r)
        dst = os.path.join(d, name)
        # ① 原片覆盖回输出目录（这一步就把 legacy 的影响彻底丢掉）
        shutil.copy2(r, dst)
        # ② 走新曲线
        res = _grade.grade_one(dst, backup=False)
        if name.endswith(_grade.AUDIO_SUFFIX):
            png = dst.replace(_grade.AUDIO_SUFFIX, ".png")
            _grade.refresh_png(dst)
        flag = "OK" if res == "OK" else "!!"
        ok += res == "OK"
        bad += res != "OK"
        print("%s %-40s %s" % (flag, name, res))

    print()
    print("完成 %d / 失败 %d" % (ok, bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
