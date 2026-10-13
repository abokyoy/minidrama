# -*- coding: utf-8 -*-
"""
中性路径启动器（生成器版）：把中文目录从命令行里拿掉，避免 cmd 代码页 mangle 路径。
计划任务没有控制台，所以 stdout/stderr 全量落日志。

用法（供 Windows 计划任务调用）：
    python E:\\LLM\\try\\minidrama\\_run_gen.py ep001 --watch
"""
import os
import sys
import runpy
import datetime

BASE = "E:\\LLM\\try\\minidrama\\保洁"
TARGET = os.path.join(BASE, "gen_worker.py")


class _Tee:
    def __init__(self, fh, orig):
        self.fh = fh
        self.orig = orig

    def write(self, s):
        for f in (self.orig, self.fh):
            try:
                if f is not None:
                    f.write(s)
            except Exception:
                pass
        try:
            self.fh.flush()
        except Exception:
            pass
        return len(s)

    def flush(self):
        for f in (self.orig, self.fh):
            try:
                if f is not None:
                    f.flush()
            except Exception:
                pass


if __name__ == "__main__":
    args = sys.argv[1:] or ["ep001", "--watch"]
    ep = args[0]
    logdir = os.path.join(BASE, ep, "logs")
    os.makedirs(logdir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = open(os.path.join(logdir, "gen_runner_%s.log" % stamp), "a",
              encoding="utf-8", errors="replace")
    sys.stdout = _Tee(fh, sys.stdout)
    sys.stderr = _Tee(fh, sys.stderr)

    os.chdir(BASE)
    if BASE not in sys.path:
        sys.path.insert(0, BASE)
    sys.argv = [TARGET] + args
    print("=" * 60)
    print("[gen-runner] start %s at %s" % (" ".join(args), datetime.datetime.now()))
    try:
        runpy.run_path(TARGET, run_name="__main__")
    except SystemExit:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        print("[gen-runner] exit at %s" % datetime.datetime.now())
        fh.flush()
