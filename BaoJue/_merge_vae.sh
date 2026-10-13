#!/bin/bash
#只合并 VAE（DiT 还在补，先处理能处理的）
set -u
ROOT="/d/h3models"
target="$ROOT/vae/minimax_h3_video_vae_fp16.safetensors"
total=5207808496
nth=8
chunk=$(( total / nth ))

if [ -f "$target" ] && [ "$(stat -c%s "$target")" = "$total" ]; then
  echo "[已完整] $(basename "$target")"; exit 0
fi

echo "=== 截断 VAE 分片 ==="
for i in $(seq 0 $((nth-1))); do
  s=$(( i * chunk ))
  if [ "$i" -eq $((nth-1)) ]; then want=$(( total - s )); else want=$chunk; fi
  pf="$target.part$(printf %02d $i)"
  got=$(stat -c%s "$pf" 2>/dev/null || echo 0)
  if [ "$got" -gt "$want" ]; then
    mb=$(( want / 1048576 )); rest=$(( want % 1048576 ))
    rm -f "$pf.trim"
    if [ "$mb" -gt 0 ]; then dd if="$pf" of="$pf.trim" bs=1048576 count="$mb" 2>/dev/null
    else : > "$pf.trim"; fi
    if [ "$rest" -gt 0 ]; then
      tail -c +$(( mb * 1048576 + 1 )) "$pf" | head -c "$rest" >> "$pf.trim"
    fi
    mv -f "$pf.trim" "$pf"
    got=$(stat -c%s "$pf")
    echo "  part$(printf %02d $i) 截断 → $got / 应为 $want"
  fi
  if [ "$got" != "$want" ]; then
    echo "  ✗ part$(printf %02d $i) $got != $want，无法合并"; exit 1
  fi
done

echo "=== 流式合并（写完一片删一片）==="
: > "$target"
for i in $(seq 0 $((nth-1))); do
  cat "$target.part$(printf %02d $i)" >> "$target"
  rm -f "$target.part$(printf %02d $i)"
  echo "  $(( $(stat -c%s "$target") * 100 / total ))%  ($(( $(stat -c%s "$target") / 1000000 )) MB)"
done
fs=$(stat -c%s "$target")
if [ "$fs" != "$total" ]; then echo "  ✗ 合并后 $fs != $total"; exit 1; fi
echo "  ✓ VAE 完成 $fs bytes"
df -h /d | tail -1
