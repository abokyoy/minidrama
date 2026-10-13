#!/bin/bash
# ⛔⛔⛔ 已废弃，禁止使用！2026-10-06 20:45
#
# 【为什么废弃】这一版跑完了，20GB 全部错位，白下一遍。
# 病根在第26-27 行：
#     curl ... --retry 30 --retry-all-errors ... -r $CUR-$((WANT-1)) "$URL" >> "$TMP"
# `--retry` 在连接中断后，会**从本次 Range 的起点重新请求**，
# 而 `>>` 又把这次重下的**完整字节追加到文件末尾** → 同一段数据写了两遍。
# 结果：文件涨到 22.4GB（超出目标 1.43GB 就是重复的证据），
#截断回精确尺寸后，头部声明 comfy_quant 是 U8[72] 的 JSON 文本、
# 实际却是权重字节；整份文件搜不到一个 "int8_tensorwise" 标记。
#
# 【正确做法】见 `_dl_dit_v3.sh`（无 --retry、全量单发、每次新建 part 文件）。
# 【更省事的做法】直接浏览器 / 下载器下，见 `_下载清单_H3原版DiT.md`。
#
# 以下代码仅作事故记录，勿执行。
set -u
URL="https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors"
T="/d/h3models/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors"
WANT=20970379616
TMP="/d/h3models/diffusion_models/_dit_fresh.tmp"
PX=(--proxy http://127.0.0.1:10808)

# 代理不通就直接退出，别默默走直连（直连 hf.co 不通）
if ! curl -s -o /dev/null -w "" -r 0-1000 "${PX[@]}" "$URL" --max-time 15; then
  echo "✗ 代理 10808 不通，先开 V2RAYN 再跑本脚本"; exit 2
fi

echo "=== 全新单源下载 DiT（目标 $WANT bytes）==="
rm -f "$TMP"
while true; do
  CUR=0; [ -f "$TMP" ] && CUR=$(stat -c%s "$TMP")
  [ "$CUR" -ge "$WANT" ] && break
  curl -s -L "${PX[@]}" --retry 30 --retry-all-errors --retry-delay 3 \
       -r $CUR-$((WANT-1)) "$URL" >> "$TMP"
  NEW=$(stat -c%s "$TMP")
  PCT=$(( NEW * 100 / WANT ))
  echo "  $PCT%  ($(( NEW/1048576 )) / $(( WANT/1048576 )) MB)"
  [ "$NEW" -le "$CUR" ] && { echo "✗ 无进展，停止"; exit 1; }
  # 提前收：已经够了就截断
  if [ "$NEW" -gt "$WANT" ]; then
    echo "  续传多下了 $(( NEW-WANT ))，截断"
    dd if="$TMP" of="$TMP.t" bs=1048576 count=$((WANT/1048576)) 2>/dev/null
    R=$((WANT%1048576))
    tail -c +$(( (WANT/1048576)*1048576 + 1 )) "$TMP" | head -c $R >> "$TMP.t"
    mv -f "$TMP.t" "$TMP"
  fi
done

FS=$(stat -c%s "$TMP")
if [ "$FS" != "$WANT" ]; then echo "✗ 尺寸 $FS != $WANT"; exit 1; fi
echo "=== 尺寸对，验内容 ==="
python /e/LLM/try/minidrama/保洁/_check_quant.py "$TMP" || { echo "✗ 内容坏，不替换原文件"; exit 1; }
echo "=== 内容 OK，替换 ==="
mv -f "$TMP" "$T"
echo "✓ 完成 $(stat -c%s "$T") bytes"
