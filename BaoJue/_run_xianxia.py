# -*- coding: utf-8 -*-
"""跑修仙测试段（xs900_segs/），走官方原版实例。

用法： python _run_xianxia.py
"""
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "ro", os.path.join(os.path.dirname(os.path.abspath(__file__)), "_run_one.py"))
RO = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RO)

SEGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xs900_segs")


def main():
    RO.pop_proxy()
    RO.reclaim_before_gen()
    print("=" * 66)
    print(" 修仙特效测试段（脸部参考图 assets_face/）")
    print("=" * 66)
    rf, job = RO.build_job(1, True, segs_dir=SEGS)
    print("提示词: %s（%d 词）"
          % (os.path.basename(job["prompt_file"]),
             len(open(job["prompt_file"], encoding="utf-8").read().split())))
    print("输出前缀: %s" % job["out_prefix"])
    os.environ["MINIDRAMA_PORT"] = str(RO.OFFICIAL_PORT)
    RO.start_comfy(RO.OFFICIAL_PORT, RO.OFFICIAL_DIR, RO.OFFICIAL_OUT,
                   RO.OFFICIAL_TEMP, "official")
    import subprocess
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "h3_driver.py")
    env = dict(os.environ)
    env["MINIDRAMA_PORT"] = str(RO.OFFICIAL_PORT)
    r = subprocess.run([sys.executable, "-u", p, rf], env=env,
                       cwd=os.path.dirname(os.path.abspath(__file__)))
    print("driver 退出码", r.returncode)
    return r.returncode


if __name__ == "__main__":
    main()
