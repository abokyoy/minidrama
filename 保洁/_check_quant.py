# -*- coding: utf-8 -*-
"""验证 H3 量化模型的内容是否真实（尺寸对 ≠ 内容对）。

关键教训（2026-10-06）：`_verify_models.py` 只验了「尺寸 + 张量头尾自洽」，
一份**字节流错位**的文件照样能通过 —— 因为头是完整下载的，
而错位发生在数据区。但 ComfyUI 加载时立刻炸：
    json.loads(comfy_quant) -> UnicodeDecodeError: 0xd5

`comfy_quant` 这批张量存的是 **UTF-8 JSON 文本**（量化配置），
所以是天然的「内容探针」：只要有一个解不出JSON，文件就是坏的。
"""
import json
import os
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

path = sys.argv[1] if len(sys.argv) > 1 else \
    r"D:\h3models\diffusion_models\minimax_h3_fl2va_pruned_int8_convrot.safetensors"

with open(path, "rb") as f:
    n = struct.unpack("<Q", f.read(8))[0]
    head = json.loads(f.read(n).decode("utf-8"))
    base = 8 + n
    cq = [(k, v) for k, v in head.items()
          if k != "__metadata__" and "comfy_quant" in k]
    if not cq:
        print("✗ 一个 comfy_quant 张量都没有 —— 这不是 H3 量化模型")
        sys.exit(1)
    bad = 0
    for k, v in cq:
        s, e = v["data_offsets"]
        f.seek(base + s)
        b = f.read(e - s)
        try:
            d = json.loads(b.decode("utf-8"))
            if "format" not in d:
                print("✗ %s 的 JSON 里没有 format 字段" % k)
                bad += 1
        except Exception as ex:
            bad += 1
            if bad <= 3:
                print("✗ %s  offset=%d  %s" % (k, s, str(ex)[:70]))
                print("   头32字节: %s" % b[:32].hex())
    print("检查 %d 个 comfy_quant 张量，坏 %d 个" % (len(cq), bad))
    if bad == 0:
        k, v = cq[0]
        s, _ = v["data_offsets"]
        f.seek(base + s)
        print("✓ 内容完好。样例: %s" % f.read(120).decode("utf-8", "replace"))
    sys.exit(1 if bad else 0)
