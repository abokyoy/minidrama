# -*- coding: utf-8 -*-
"""
参考图提亮：解决用户 2026-10-03 反馈的「视频有点偏黑，人物阴影过重，没有柔和的感觉」。

诊断（实测灰度直方图）：
  角色图是亮的 —— char_* 中位 200~240，均值 130~200，没问题。
  场景图是暗的 —— sc_office_* 均值只有 51~90（中位 39~80），sc_alley_gate 55、sc_car_interior 76。
  ep001 有 82/129 段发生在这个办公室里，H3 是**照参考图打光**的，
  场景图黑 → 成片就黑 → 人物阴影就重。提示词里再怎么写 "NOT dark" 都压不过参考图。

修法：对参考图做一次「提亮 + 提升黑位 + 压对比」的保形映射，
      只改亮度曲线，不动构图、不动人脸比例，输出与输入同名同尺寸。
      原图先整体备份到 assets/_orig/，随时可回滚。

参数：目标中位灰度 TARGET（默认 155），黑位抬升 LIFT（默认 25），
      gamma 用二分法逐图求解，所以明暗不同的图会被拉到接近的观感，
      不会出现「亮的更亮、暗的还暗」。

用法： python _brighten_assets.py            # 场景图 + 偏暗的角色图，按需处理
       python _brighten_assets.py --force    # 已处理过的也重算（用 _orig 里的原图）
       python _brighten_assets.py --restore  # 从 _orig 还原
"""
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")

# 用 ComfyUI 的 venv（里面一定有 Pillow），避免污染本机环境
PY_IMG = r"E:\ComfyUI\ComfyUI-master\ComfyUI-master\venv\Scripts\python.exe"

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")
ORIG = os.path.join(ASSETS, "_orig")

LIFT = 25                      # 黑位抬升：把最暗处从 0 抬到 25
TARGET_SCENE = 155             # 场景图目标中位灰度
TARGET_CHAR = 200              # 角色图目标中位灰度（只在偏暗时才拉）
CHAR_TRIGGER = 190             # 角色图中位低于这个值才处理
# 夜戏图不能拉到 155，否则巷口/车厢会变成白天。给它们单独一档：
# 仍然是「明确偏亮的夜」（比原图 48/72 亮一大截），但保住夜晚的观感。
TARGET_BY_FILE = {
    "sc_alley_gate.png": (130, 18),
    "sc_car_interior.png": (130, 18),
    # ep002 的陆宅夜戏（会客厅 / 桌面 / 陆崇书房）：生图出来是 87/98/37，太黑，
    # H3 会照参考图打光 → 成片必黑。夜戏不能拉到 155（会变白天），统一到「明确偏亮的夜」。
    "sc_lu_hall.png": (130, 18),
    "sc_lu_hall_desk.png": (130, 18),
    "sc_lu_study.png": (130, 18),
    # ep003 的出租屋夜戏：生图 med=121，已经够亮，别再按日戏 155 拉到像白天
    "sc_rental_room.png": (130, 18),
    # ep004 杂物间夜戏：生图整片深棕（货架、旧箱笼全是深色），不拉会直接带黑成片
    "sc_lu_storage.png": (130, 18),
    # ep005 楼门口路灯下：夜戏，但用户要求「亮着的夜」，拉到 130 保住暖光又不发灰
    "sc_rental_gate.png": (130, 18),
}


def _ensure_pillow():
    try:
        import PIL  # noqa
        return True
    except ImportError:
        pass
    os.execv(PY_IMG, [PY_IMG, os.path.abspath(__file__)] + sys.argv[1:])
    return False


def stats(im):
    h = im.convert("L").histogram()
    tot = sum(h)
    c = 0
    med = None
    p05 = None
    for i, v in enumerate(h):
        c += v
        if p05 is None and c >= tot * 0.05:
            p05 = i
        if med is None and c >= tot * 0.5:
            med = i
    mean = sum(i * v for i, v in enumerate(h)) / tot
    return mean, med, p05


def solve_gamma(med_in, target, lift):
    """求 gamma，使 med_in 映射到 target。"""
    lo, hi = 0.30, 1.60
    for _ in range(40):
        g = (lo + hi) / 2
        v = 255.0 * ((med_in / 255.0) ** g) * (255 - lift) / 255.0 + lift
        if v < target:
            hi = g          # gamma 越大越暗 → v 太小说明 g 偏大
        else:
            lo = g
    return (lo + hi) / 2


def build_lut(g, lift):
    lut = []
    for i in range(256):
        v = 255.0 * ((i / 255.0) ** g) * (255 - lift) / 255.0 + lift
        lut.append(max(0, min(255, int(round(v)))))
    return lut


def process(path, target, force, lift=None):
    from PIL import Image
    name = os.path.basename(path)
    if name in TARGET_BY_FILE:
        target, _l = TARGET_BY_FILE[name]
        lift = _l
    if lift is None:
        lift = LIFT
    orig_path = os.path.join(ORIG, name)
    if not os.path.exists(orig_path):
        shutil.copy2(path, orig_path)      # 首次：备份原图
    src = orig_path if (force or os.path.exists(orig_path)) else path

    im = Image.open(src)
    mean0, med0, p050 = stats(im)
    if not force and med0 >= target * 0.92:
        return name, (mean0, med0, p050), None, "已足够亮，跳过"

    g = solve_gamma(med0, target, lift)
    lut = build_lut(g, lift)

    # 逐通道套 LUT：PIL 的 point() 对多通道图要求 256*通道数 个条目，
    # 所以拆成单通道分别套（顺带把灰度图/带 alpha 的图一起兼容了）
    im2 = im if im.mode == "RGBA" else im.convert("RGB")
    bands = im2.split()
    out = Image.merge(im2.mode, [b.point(lut) for b in bands])
    out.save(path, "PNG")
    m1, d1, p1 = stats(Image.open(path))
    return name, (mean0, med0, p050), (m1, d1, p1), "gamma=%.3f lift=%d" % (g, lift)


def restore():
    from PIL import Image  # noqa
    n = 0
    for f in sorted(os.listdir(ORIG)):
        if f.endswith(".png"):
            shutil.copy2(os.path.join(ORIG, f), os.path.join(ASSETS, f))
            n += 1
    print("已从 _orig 还原 %d 个参考图" % n)


def main():
    args = sys.argv[1:]
    if not _ensure_pillow():
        return
    if "--restore" in args:
        restore()
        return
    force = "--force" in args
    os.makedirs(ORIG, exist_ok=True)

    print("%-28s %-22s %-22s %s" % ("file", "before(mean/med/p05)", "after(mean/med/p05)", "note"))
    scenes = sorted(f for f in os.listdir(ASSETS)
                    if f.startswith("sc_") and f.endswith(".png"))
    chars = sorted(f for f in os.listdir(ASSETS)
                   if f.startswith("char_") and f.endswith(".png"))

    for f in scenes:
        name, b, a, note = process(os.path.join(ASSETS, f), TARGET_SCENE, force)
        print("%-28s %-22s %-22s %s" % (
            name,
            "%5.1f/%5d/%5d" % b,
            ("%5.1f/%5d/%5d" % a) if a else "-",
            note))

    for f in chars:
        name, b, a, note = process(os.path.join(ASSETS, f), TARGET_CHAR, force)
        print("%-28s %-22s %-22s %s" % (
            name,
            "%5.1f/%5d/%5d" % b,
            ("%5.1f/%5d/%5d" % a) if a else "-",
            note))


if __name__ == "__main__":
    main()
