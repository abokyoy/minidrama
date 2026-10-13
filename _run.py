# -*- coding: utf-8 -*-
"""
中性路径启动器：把中文目录从命令行里拿掉，避免 cmd 代码页把路径 mangle 掉。
同时把 stdout/stderr 重定向到日志文件（计划任务没有控制台）。

用法（供 Windows 计划任务调用）：
    python E:\\LLM\\try\\minidrama\\_run.py ep001
"""
import os
import sys
import runpy
import datetime

BASE = "E:\\LLM\\try\\minidrama\\保洁"
TARGET = os.path.join(BASE, "autopilot.py")


class _Tee:
    """同时写到原 stdout（如果有）和日志文件。"""

    def __init__(self, fh, orig):
        self.fh = fh
        self.orig = orig

    def write(self, s):
        try:
            if self.orig is not None:
                self.orig.write(s)
        except Exception:
            pass
        try:
            self.fh.write(s)
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
    ep = sys.argv[1] if len(sys.argv) > 1 else "ep001"
    logdir = os.path.join(BASE, ep, "logs")
    os.makedirs(logdir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = open(os.path.join(logdir, "runner_%s.log" % stamp), "a", encoding="utf-8", errors="replace")
    sys.stdout = _Tee(fh, sys.stdout)
    sys.stderr = _Tee(fh, sys.stderr)

    os.chdir(BASE)
    if BASE not in sys.path:
        sys.path.insert(0, BASE)
    sys.argv = [TARGET, ep]
    print("=" * 60)
    print("[runner] start %s at %s" % (ep, datetime.datetime.now()))
    try:
        runpy.run_path(TARGET, run_name="__main__")
    except SystemExit:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        print("[runner] exit at %s" % datetime.datetime.now())
        fh.flush()
