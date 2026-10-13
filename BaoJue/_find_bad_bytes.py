# -*- coding: utf-8 -*-
"""定位 safetensors 里到底哪一段是坏字节。

背景：DiT 主模型尺寸对、张量头自洽（_verify_models.py 通过），
      但 ComfyUI 读量化层配置时 json.loads 报 UnicodeDecodeError: 0xd5。
      → 说明**中段有坏字节**（续传拼接时错位/重复），头尾自洽查不出来。

方法：按 safetensors 头里的 data_offsets 逐张量读，单独 utf-8 解码
      非二进制张量（如 layer_conf 那种存JSON 的量化参数），
      第一个解不出来的就是坏位置。
"""
import io
import json
import os
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

path = sys.argv[1] if len(sys.argv) > 1 else \
    r"D:\h3models\diffusion_models\minimax_h3_fl2va_pruned_int8_convrot.safetensors"

size = os.path.getsize(path)
print("文件: %s\n大小: %d bytes" % (os.path.basename(path), size))

with open(path, "rb") as f:
    n = struct.unpack("<Q", f.read(8))[0]
    head = json.loads(f.read(n).decode("utf-8"))
    base = 8 + n
    print("头长度: %d  键数: %d  数据起点: %d" % (n, len(head), base))

    # 收集所有张量，按 offset 排序
    items = []
    for k, v in head.items():
        if k == "__metadata__":
            continue
        items.append((k, v["dtype"], tuple(v.get("shape") or ()), v["data_offsets"]))
    items.sort(key=lambda x: x[3][0])
    print("张量数: %d  声明总字节: %d  实际数据区: %d"
          % (len(items), items[-1][3][1], size - base))

    # 找覆盖空隙 / 越界
    prev_end = 0
    gaps = []
    for k, dt, sh, (s, e) in items:
        if s > prev_end:
            gaps.append((prev_end, s - prev_end))
        prev_end = max(prev_end, e)
    if gaps:
        print("\n⚠️ 头里声明有空隙 %d 处（前3）: %s" % (len(gaps), gaps[:3]))
    if prev_end != size - base:
        print("\n⚠️ 最后一个张量结束于 %d，数据区应到 %d，差 %d"
              % (prev_end, size - base, size - base - prev_end))

    # 逐张量读，只对看起来是文本的（长度 < 4096 且 dtype F32/单个元素）试解码
    bad = []
    checked = 0
    for k, dt, sh, (s, e) in items:
        ln = e - s
        if ln == 0 or ln > 65536:
            continue
        f.seek(base + s)
        b = f.read(ln)
        checked += 1
        # 只检查看起来像JSON 的：全部字节都在可打印 ASCII / 空白范围
        if all(c < 128 for c in b):
            try:
                json.loads(b.decode("utf-8"))
            except Exception as ex:
                bad.append((k, s, ln, str(ex)[:70], b[:24].hex()))
        if len(bad) >= 5:
            break
    print("\n检查了 %d 个小张量" % checked)
    if bad:
        print("✗ 发现 %d 个无法解码的：" % len(bad))
        for k, s, ln, err, hx in bad:
            print("  %s\n    offset=%d len=%d\n    %s\n    头24字节: %s"
                  % (k, s, ln, err, hx))
    else:
        print("✓ 小张量里没找到坏字节")
    print("\n→ 若上面无异常，问题多半在**大张量的中间**（续传拼接错位），")
    print("  需要抽样比对：把同一区间分别从官方源和本地各取 1KB 比对。")
