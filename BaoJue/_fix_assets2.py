# -*- coding: utf-8 -*-
"""把第 4/5 集新生成的参考图规范化成 char_*.png / sc_*.png
（注意：ImageGen 并行调用时 output_dir 不可靠，文件名时间戳还会撞车 —— 这次就丢了一张。
  所以这里按"实际落盘位置"逐一登记，不按 output_dir 猜。）"""
import shutil, os
A = r"E:/LLM/try/minidrama/保洁/assets"
G = os.path.join(A, "_gen")
PAIRS = [
    (os.path.join(G, "hospital_station", "Character_design_reference_she_2026-10-03T14-49-12.png"), "char_hushizhang.png"),
    (os.path.join(G, "hospital_station", "Empty_location_reference_photo_2026-10-03T14-49-14.png"), "sc_hospital_station.png"),
    (os.path.join(G, "lu_storage",       "Empty_location_reference_photo_2026-10-03T14-49-59.png"), "sc_lu_storage.png"),
    (os.path.join(G, "rental_gate2",     "Empty_location_reference_photo_2026-10-03T14-50-35.png"), "sc_rental_gate.png"),
]
for src, dst in PAIRS:
    if not os.path.exists(src):
        print("MISS", src); continue
    shutil.copy2(src, os.path.join(A, dst))
    print("OK   %-26s <- %s" % (dst, os.path.relpath(src, G)))
