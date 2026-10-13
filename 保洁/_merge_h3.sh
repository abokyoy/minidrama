#!/bin/bash
# ⭐ 边合并边删分片 —— D 盘只剩 21G，一次性 cat 需要 40G，会失败。
# 做法：写完第 i 片立刻删第 i 片，峰值 = 分片总量（约等于一个文件大小）。
set -u
ROOT="/d/h3models"

merge_stream() {   # merge_stream <目标文件> <总大小> <片数>
  local target="$1" total="$2" nth="$3"
  local chunk=$(( total / nth ))
  if [ -f "$target" ] && [ "$(stat -c%s "$target")" = "$total" ]; then
    echo "[已完整] $(basename "$target")"; return 0
  fi
  echo "=== 截断+ 合并 $(basename "$target") ==="
  # ① 先把所有超长的片截到目标长度
  for i in $(seq 0 $((nth-1))); do
    local s=$(( i * chunk ))
    local want; if [ "$i" -eq $((nth-1)) ]; then want=$(( total - s )); else want=$chunk; fi
    local pf="$target.part$(printf %02d $i)"
    local got; got=$(stat -c%s "$pf" 2>/dev/null || echo 0)
    if [ "$got" -gt "$want" ]; then
      # dd 整 MB 部分 + head 收尾余数。head -c 只用于 <1MB 的偏移，MSYS 下可靠。
      local mb=$(( want / 1048576 ))
      local rest=$(( want % 1048576 ))
      rm -f "$pf.trim"
      if [ "$mb" -gt 0 ]; then
        dd if="$pf" of="$pf.trim" bs=1048576 count="$mb" 2>/dev/null
      else
        : > "$pf.trim"
      fi
      if [ "$rest" -gt 0 ]; then
        tail -c +$(( mb * 1048576 + 1 )) "$pf" | head -c "$rest" >> "$pf.trim"
      fi
      mv -f "$pf.trim" "$pf"
      # ⚠️ 必须重新 stat：上面报的是截断**前**的尺寸，用它校验会误判
      got=$(stat -c%s "$pf")
      echo "  part$(printf %02d $i) 截断 → $got / 应为 $want"
    fi
    if [ "$got" != "$want" ]; then
      echo "  ✗ part$(printf %02d $i) 大小 $got != $want，无法合并"
      return 1
    fi
  done
  # ② 逐片追加，写完就删，峰值只多一片的大小
  : > "$target"
  for i in $(seq 0 $((nth-1))); do
    local pf="$target.part$(printf %02d $i)"
    cat "$pf" >> "$target"
    rm -f "$pf"
    local now; now=$(stat -c%s "$target")
    echo "  合并到 $(( now * 100 / total ))%  ($(( now / 1000000 )) MB)"
  done
  local fs; fs=$(stat -c%s "$target")
  if [ "$fs" != "$total" ]; then echo "  ✗ 合并后 $fs != $total"; return 1; fi
  echo "  ✓ 完成 $(basename "$target") $fs bytes"
  return 0
}

merge_stream "$ROOT/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors" 20970379616 10
merge_stream "$ROOT/vae/minimax_h3_video_vae_fp16.safetensors" 5207808496 8
echo "MERGE DONE $(date +%H:%M:%S)"
df -h /d | tail -1
