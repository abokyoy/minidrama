# -*- coding: utf-8 -*-
"""连续跑 xs001 的多段，每段前自动清场（复用 _run_one 的主流程太绕，直接串）。

用法：
  python _run_many.py 2 3 4 5            # 官方版，跑 2/3/4/5
  python _run_many.py 2 3 4 5 --old      # 老实例8188

每段跑完立刻抽帧拼图（不自动验收，人工看），然后下一段。
**每满 2 段强制重启 ComfyUI** —— 跑久了会越接越暗（实测过）。
"""
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
RUN1 = os.path.join(BASE, "_run_one.py")


def sh(cmd, timeout=3600):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=timeout)


def frames(mp4, tag):
    cp = sh('cp "%s" "D:/_abtmp/%s.mp4"' % (mp4, tag))
    if cp.returncode != 0:
        print("  拷不进D:/_abtmp")
        return
    sh('"%s" "%s" "D:/_abtmp/%s.mp4" 12' % (PY,
                                    os.path.join(BASE, "_dup_check.py"), tag))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    old = "--old" in sys.argv
    segs = [int(a) for a in args]
    suffix = "" if old else " official"
    print("=" * 66)
    print(" 连跑 %s" % ", ".join("seg%02d" % s for s in segs))
    print("=" * 66)

    results = []
    for i, s in enumerate(segs, 1):
        print("\n" + "#" * 66)
        print("# seg%02d  开始  (%d/%d)" % (s, i, len(segs)))
        print("#" * 66)
        t0 = time.time()
        r = sh('"%s" -u "%s" %d%s' % (PY, RUN1, s, suffix))
        out = (r.stdout or "") + (r.stderr or "")
        for line in out.splitlines():
            sline = line.strip()
            if (sline.startswith("成片") or sline.startswith("指标")
                    or "physical" in sline or "已关" in sline
                    or sline[:2] in ("p0", "p1", "p2", "p5", "p7", "p9")
                    or sline.startswith(("sat", "local", "contrast", "dyn"))
                    or "SAVED" in sline):
                print("   " + sline[:120])
        dt = time.time() - t0
        print("-- seg%02d 用时 %.1f 分" % (s, dt / 60))

        # 找最新成片
        out_dir = r"D:\output" if old else r"D:\output_h3off"
        d = out_dir.replace("\\", "/")
        ls = sh('ls -t "%s"/*_t%02d*_*-audio.mp4 2>/dev/null | head -1'
                % (d, s))
        mp4 = (ls.stdout or "").strip()
        if mp4:
            print("   成片: %s" % mp4)
            frames(mp4, "m_t%02d" % s)
            results.append((s, mp4))
        else:
            print("   没找到成片")

        # 每 2 段重启 ComfyUI
        if i % 2 == 0 and i < len(segs):
            print("\n>>> 跑满 2 段，重启 ComfyUI（防越接越暗）")
            sh('"%s" "%s" --port %d' % (
                PY, os.path.join(BASE, "_stop_all.py"), 8188 if old else 8189))
            time.sleep(6)

    print("\n" + "=" * 66)
    print(" 全部完成")
    for s, m in results:
        print("  seg%02d  %s" % (s, m))
    print("抽帧图: D:/_abtmp/m_t%02d*.jpg 和 E:\\LLM\\try\\minidrama\\_contact_m_t*.jpg")
    print("=" * 66)


if __name__ == "__main__":
    main()