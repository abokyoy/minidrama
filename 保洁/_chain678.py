# -*- coding: utf-8 -*-
r"""
正片续写链：seg06 → seg07 → seg08（拿上一段尾帧接续）

规则（用户 2026-10-08 明确要求）：
  · 续写 = 拿上一段成片的尾帧当引导（chain 工作流），不是各段独立生成
  · 只跑 3 段就停，跑完等用户看（用户：「先跑 3 段停」）
  · 每段跑前清场（reclaim_before_gen），否则系统内存 99% 满 → 每步多耗 110 秒
  · 每满 3 段 kill + 重启 ComfyUI，避免越接越黑
  · ⛔ 零甩镜：所有 Camera: 机位都是稳定机位（用户实测 Whip Pan 会让人晕）

用法： python _chain678.py            # 跑 seg06→07→08
      python _chain678.py --wf chain # 用 chain 工作流接续（默认）
      python _chain678.py --wf fixed # 用 fixed 工作流（独立生成，只用来对照）
"""
import os, sys, io, json, time, subprocess, glob, importlib.util

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
           "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)
os.environ["no_proxy"] = "127.0.0.1,localhost"
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# ⚠️ h3_driver.py 自己**不会**起 ComfyUI（踩过：直接调它 → WinError 10061 拒连）。
#    必须借 _run_one.py 的 start_comfy / reclaim_before_gen。
_spec = importlib.util.spec_from_file_location("ro", os.path.join(HERE, "_run_one.py"))
RO = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RO)

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVER = os.path.join(HERE, "h3_driver.py")
OUT_DIR = r"D:\output_h3off"
INST_DIR = r"E:\ComfyUI\ComfyUI_h3official"
WF_DIR = r"E:\ComfyUI\ComfyUI_new\user\default\workflows"
WF = {
    "chain": os.path.join(WF_DIR, "04_ref2v_seg2_chain.json"),
    "fixed": os.path.join(WF_DIR, "04_ref2v_4step_sla_ganloss_fixed.json"),
}
SEGS = ["06", "07", "08"]
# ⛔⛔ 参考图数量必须跟 seg05（用户认可的那支）**完全一致：2 张**。
# 我第一次跑 seg06 用了 3 张（多给一张小唐）→ 模型照抄，多画一个人 = 两个苏小满。
# 铁律：一段给几张环境/人物图，模型就画几个人。人物多出来第一原因是**参考图给多了**。
# seg05 = [苏小满, 钱经理] 两张 → seg06/07/08 也必须是这两张。
# 小唐在提示词里用文字描述外形，不给她参考图。
REFS = ["r01_ref1__9caa7471.png", "r02_ref2__bcad60c8.png"]


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


def run(cmd, timeout=3600, env=None):
    log("RUN", os.path.basename(cmd[1] if len(cmd) > 1 else cmd[0]))
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout,
                       env=env, cwd=HERE)
    out = (p.stdout or "") + (p.stderr or "")
    for ln in out.splitlines():
        if any(k in ln for k in ("SUBMITTED", "DONE", "SAVED", "成片", "ERROR",
                                 "清场", "QUALITY", "MODEL", "LORA", "参考图")):
            log("  ", ln.strip())
    if p.returncode != 0:
        log("!! 退出码", p.returncode)
        log(out[-1500:])
        raise SystemExit(p.returncode)
    return out


def newest(prefix):
    """按修改时间取最新成片 —— ⛔ 绝不信日志里的路径（踩过：日志说 D:\\output，
       实际落在 D:\\output_h3off）"""
    fs = glob.glob(os.path.join(OUT_DIR, prefix + "*.mp4"))
    if not fs:
        return None
    return max(fs, key=os.path.getmtime)


def main():
    wf_kind = "chain"
    if "--wf" in sys.argv:
        wf_kind = sys.argv[sys.argv.index("--wf") + 1]
    assert wf_kind in WF, "工作流只能是 chain 或 fixed"
    # 断点续跑：已有成片就跳过（除非 --force）
    force = "--force" in sys.argv

    log("=" * 66)
    log(" 正片续写链 seg%s   工作流=%s" % ("/".join(SEGS), wf_kind))
    log(" 输出目录", OUT_DIR)
    log("=" * 66)

    # ⚠️ 每段跑前必须清场：系统内存到 99% 时走页文件，每步多耗 ~110 秒
    # ⚠️ ComfyUI 启动权只属于本脚本 —— 手动 start 会清空队列（driver 死等）
    RO.reclaim_before_gen()
    os.environ["MINIDRAMA_PORT"] = str(RO.OFFICIAL_PORT)
    RO.start_comfy(RO.OFFICIAL_PORT, RO.OFFICIAL_DIR, RO.OFFICIAL_OUT,
                   RO.OFFICIAL_TEMP, "official")
    env = dict(os.environ)
    env["MINIDRAMA_PORT"] = str(RO.OFFICIAL_PORT)

    prev = None
    for i, sid in enumerate(SEGS, 1):
        prefix = "off_xs01_t%02d" % (5 + i)      # seg06->t06, seg07->t07, seg08->t08
        existing = newest(prefix)
        if existing and not force:
            log("[%d/3] seg%s 已有成片，跳过 -> %s" % (i, sid, os.path.basename(existing)))
            prev = existing
            continue

        # ⛔ 第 1 段必须用 fixed 工作流（从参考图出画面）。
        #    chain 工作流的节点 910（VHS_LoadVideoPath）里**写死了别人的路径**
        #    Z:\wx\output\clip1_00001_.mp4（踩过：报 400
        #    "Invalid file path: Z:\wx\output\clip1_00001_.mp4"）。
        #    driver 只在 prev_video 非空时才改这个节点 → 第一段传 None 就用 chain
        #    会直接 400。所以从第 2 段起才切 chain。
        kind = wf_kind if prev else "fixed"

        job = {
            "workflow": WF[kind],
            "prompt_file": os.path.join(HERE, "xs001_segs", "seg%s_prompt.txt" % sid),
            "out_prefix": prefix,
            "ref_dir": os.path.join(INST_DIR, "input"),
            "refs": REFS,
            "prev_video": prev,          # None = 第一段从参考图出画面
        }
        jp = os.path.join(HERE, "xs001_segs", "job%s_%s.json" % (sid, kind))
        json.dump(job, io.open(jp, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        log("[%d/3] seg%s  工作流=%s  prev=%s"
            % (i, sid, kind, os.path.basename(prev) if prev else "(无，用参考图)"))

        run([sys.executable, "-u", DRIVER, jp], env=env)

        got = newest(prefix)
        if not got:
            log("!! seg%s 没找到成片" % sid)
            raise SystemExit(4)
        log("    -> %s  (%.2f MB)" % (got, os.path.getsize(got) / 1048576.0))
        prev = got

    log("=" * 66)
    log(" 三段跑完。产物：")
    for i, sid in enumerate(SEGS, 1):
        f = newest("off_xs01_t%02d" % (5 + i))
        if f:
            log("  seg%s  %7.2f MB  %s" % (sid, os.path.getsize(f) / 1048576.0, f))
    log("=" * 66)


if __name__ == "__main__":
    main()
