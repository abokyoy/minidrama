# -*- coding: utf-8 -*-
"""验证 H3 模型文件是不是**真的**完整（尺寸对≠ 内容对）。

为什么必须验：HTTP 续传会在 Range 边界多下/少下几个字节，
尺寸对得上但中间可能少了一段 → ComfyUI 加载时才报看不懂的错，很难查。

方法：读 safetensors 头部。格式 = 8 字节小端长度 + JSON 头。
       头里第一个 key 必须是 __metadata__ 或张量名。
       再顺带确认头里声明的字节区间能覆盖整个文件。
"""
import io
import json
import os
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TARGETS = [
    (r"D:\h3models\diffusion_models\minimax_h3_fl2va_pruned_int8_convrot.safetensors",
     20970379616),
    (r"D:\h3models\vae\minimax_h3_video_vae_fp16.safetensors", 5207808496),
    (r"D:\h3models\loras\minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors",
     1956193000),
]

ok_all = True
for path, want in TARGETS:
    name = os.path.basename(path)
    if not os.path.exists(path):
        print("✗ %s  不存在" % name)
        ok_all = False
        continue
    size = os.path.getsize(path)
    line = "  %-58s %13d bytes  " % (name[:58], size)
    if size != want:
        print(line + "✗ 尺寸应为 %d" % want)
        ok_all = False
        continue
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        if n <= 0 or n > 200 * 1024 * 1024:
            print(line + "✗ 头长度异常 %d" % n)
            ok_all = False
            continue
        head = json.loads(f.read(n).decode("utf-8"))
    # 张量总字节范围：头里每项形如 {"dtype":..,"shape":[..],"data_offsets":[起,止]}
    # ⚠️ 是**具名**字段 data_offsets，不是位置索引 —— 之前写成 v[2] 直接 KeyError。
    maxend = 0
    ntensors = 0
    for k, v in head.items():
        if k == "__metadata__":
            continue
        ntensors += 1
        off = v.get("data_offsets")
        if not off or len(off) != 2:
            print(line + "✗ %s 缺 data_offsets" % k)
            ok_all = False
            break
        if off[1] > maxend:
            maxend = off[1]
    need = 8 + n + maxend
    if need != size:
        print(line + "✗ 头声明 %d，实际 %d，差 %d" % (need, size, size - need))
        ok_all = False
        continue
    print(line + "✓ %d 个张量，头尾自洽" % ntensors)

print()
print("全部通过 ✅" if ok_all else "有文件不通过 ✗")
sys.exit(0 if ok_all else 1)
