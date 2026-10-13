# -*- coding: utf-8 -*-
"""把 ImageGen 生成的原图规范化成 char_*.png / sc_*.png"""
import shutil
import os

A = r"E:\LLM\try\minidrama\保洁\assets"
G = os.path.join(A, "_gen")

PAIRS = [
    (os.path.join(A, "Character_design_sheet__16_9_h_2026-10-03T10-15-05.png"), "char_qiantai.png"),
    (os.path.join(A, "Character_design_sheet__16_9_h_2026-10-03T10-15-06.png"), "char_yisheng.png"),
    (os.path.join(G, "luman", "Character_design_sheet__16_9_h_2026-10-03T10-15-34.png"), "char_luman.png"),
    (os.path.join(G, "luman", "Character_design_sheet__16_9_h_2026-10-03T10-15-35.png"), "char_waipo.png"),
    (os.path.join(G, "zhangzong", "Character_design_sheet__16_9_h_2026-10-03T10-16-02.png"), "char_zhangzong.png"),
    (os.path.join(G, "hospital_ward", "Empty_location_reference_photo_2026-10-03T10-16-19.png"), "sc_hospital_ward.png"),
    (os.path.join(G, "hospital_corridor", "Empty_location_reference_photo_2026-10-03T10-16-36.png"), "sc_hospital_corridor.png"),
    (os.path.join(G, "hospital_bench", "Empty_location_reference_photo_2026-10-03T10-16-51.png"), "sc_hospital_bench.png"),
    (os.path.join(G, "lobby_1f", "Empty_location_reference_photo_2026-10-03T10-17-10.png"), "sc_lobby_1f.png"),
    (os.path.join(G, "building_exterior", "Location_reference_photograph__2026-10-03T10-17-26.png"), "sc_building_exterior.png"),
    (os.path.join(G, "car_interior", "Interior_location_reference_ph_2026-10-03T10-17-42.png"), "sc_car_interior.png"),
    (os.path.join(G, "alley_gate", "Exterior_location_reference_ph_2026-10-03T10-17-59.png"), "sc_alley_gate.png"),
]

for src, dst in PAIRS:
    d = os.path.join(A, dst)
    if not os.path.exists(src):
        print("MISS", src)
        continue
    shutil.copy2(src, d)
    print("OK  %-28s <- %s" % (dst, os.path.basename(src)))

print("--- 最终 assets ---")
for f in sorted(os.listdir(A)):
    if f.startswith(("char_", "sc_")):
        print("  %-28s %8.0f KB" % (f, os.path.getsize(os.path.join(A, f)) / 1024))
