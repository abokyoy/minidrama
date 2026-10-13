#!/bin/bash
# ⭐ H3 官方原版模型 + turbo LoRA 分片下载
#
# 源选择（2026-10-06 实测）：
#   带代理 10808 → HF 官方源，8 线程聚合 4.9 MB/s
#   无代理       → hf-mirror 直连，8 线程聚合 3.2 MB/s
# 所以**有代理就用官方源**（更快，且拿到的是原版文件未经镜像二次处理）。
#
# 后台跑：bash _dl_h3_models.sh
# ⚠️ 必须整条命令作为后台任务的**主进程**跑（不要 nohup ... & 再退出），
#    否则父 shell 一死，子curl 全被带走，分片停在半路。
set -u

# ── 有代理就用官方源，没有就退回镜像 ────────────────────────────
if curl -s -o /dev/null --max-time 8 --proxy http://127.0.0.1:10808 \
        -r 0-100 "https://huggingface.co" 2>/dev/null; then
  export HTTP_PROXY=http://127.0.0.1:10808 HTTPS_PROXY=http://127.0.0.1:10808
  export http_proxy=http://127.0.0.1:10808 https_proxy=http://127.0.0.1:10808
  export ALL_PROXY=socks5://127.0.0.1:10808 all_proxy=socks5://127.0.0.1:10808
  BASE="https://huggingface.co"
  CURL_PROXY=(--proxy http://127.0.0.1:10808)
  echo "[源] HF 官方（走 10808 代理）"
else
  BASE="https://hf-mirror.com"
  CURL_PROXY=()
  echo "[源] hf-mirror（无代理直连）"
fi

ROOT="/d/h3models"
LOG_DIR="/e/LLM/try/minidrama/保洁/_dllogs"
mkdir -p "$LOG_DIR"

dl() {   # dl <url_path> <目标文件> <总大小> <线程数>
  local path="$1" target="$2" total="$3" nth="$4"
  local url="$BASE/$path"
  local dir;dir=$(dirname "$target")
  mkdir -p "$dir"
  # 已完成则跳过
  if [ -f "$target" ] && [ "$(stat -c%s "$target")" = "$total" ]; then
    echo "[跳过] $(basename "$target") 已完整"; return 0
  fi
  local chunk=$(( total / nth ))
  echo "=== 下载 $(basename "$target")  $(( total / 1000000 )) MB / $nth 线程 ==="
  # ⭐ 逐片续传：每片先看本地已有多少，再把 Range 起点往后挪。
  #   （不能用 curl -C - 配 -r：两个都改 Range 会互相打架下错偏移。）
  #   不删已有分片 → 换源/断网重来都不丢进度。
  for i in $(seq 0 $((nth-1))); do
    local s=$(( i * chunk ))
    local e
    if [ "$i" -eq $((nth-1)) ]; then e=$(( total - 1 )); else e=$(( s + chunk - 1 )); fi
    (
      local pf="$target.part$(printf %02d $i)"
      local need=$(( e - s + 1 ))
      while true; do
        local have=0
        [ -f "$pf" ] && have=$(stat -c%s "$pf")
        [ "$have" -ge "$need" ] && break
        # 续传：把 Range 起点挪到本地已有长度之后
        curl -s -L "${CURL_PROXY[@]}" --retry 10 --retry-all-errors --retry-delay 3 \
             -r $(( s + have ))-$e "$url" >> "$pf" \
             2>>"$LOG_DIR/curl_$(basename "$target").err"
        local now=0
        [ -f "$pf" ] && now=$(stat -c%s "$pf")
        [ "$now" -le "$have" ] && break      # 没有任何进展 → 放弃这片
      done
    ) &
  done
  wait
  # ⭐ 截断：HTTP 续传有时会多下一点（源端 Range 边界不完全严格）。
  #    多出来的字节是**下一段的开头**，留着会让整块文件错位 → 必须切掉。
  #    截断用 `head -c`，**只在超长时动**，正常片一个字节都不碰。
  for i in $(seq 0 $((nth-1))); do
    local s=$(( i * chunk ))
    local want; if [ "$i" -eq $((nth-1)) ]; then want=$(( total - s )); else want=$chunk; fi
    local pf="$target.part$(printf %02d $i)"
    local got; got=$(stat -c%s "$pf" 2>/dev/null || echo 0)
    if [ "$got" -gt "$want" ]; then
      head -c "$want" "$pf" > "$pf.trim" && mv -f "$pf.trim" "$pf"
      echo "  part$(printf %02d $i) 截断 $got → $want（续传多下的）"
    fi
  done
  # 校验每个分片
  local bad=0
  for i in $(seq 0 $((nth-1))); do
    local s=$(( i * chunk ))
    local want; if [ "$i" -eq $((nth-1)) ]; then want=$(( total - s )); else want=$chunk; fi
    local got; got=$(stat -c%s "$target.part$(printf %02d $i)" 2>/dev/null || echo 0)
    if [ "$got" != "$want" ]; then echo "  ✗ part$i $got != $want"; bad=1; fi
  done
  if [ "$bad" = "1" ]; then
    echo "  ✗ 分片不全，**不合并**（避免坏模型）。重跑本脚本会从头再来。"
    return 1
  fi
  cat $(for i in $(seq 0 $((nth-1))); do echo "$target.part$(printf %02d $i)"; done) > "$target"
  local fs; fs=$(stat -c%s "$target")
  if [ "$fs" != "$total" ]; then echo "  ✗ 合并后 $fs != $total"; return 1; fi
  rm -f "$target".part*
  echo "  ✓ 完成 $(basename "$target") $fs bytes"
  return 0
}

# ① 官方原版 DiT（关键：非 turbo，走 20 步档）
dl "Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors" \
   "$ROOT/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors" 20970379616 10
# ② fp16 视频 VAE（官方蓝图用的，本机 int8 版是量化重损的元凶之一）
dl "Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_fp16.safetensors" \
   "$ROOT/vae/minimax_h3_video_vae_fp16.safetensors" 5207808496 8
# ③ turbo LoRA（本地已有，校验完整性）
T="/d/h3models/loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"
if [ ! -f "$T" ] || [ "$(stat -c%s "$T")" != "1956193000" ]; then
  dl "lightx2v/Minimax-h3-Turbo/resolve/main/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors" \
     "$T" 1956193000 6
else
  echo "[跳过] turbo LoRA 已完整(1956193000)"
fi
echo "ALL DONE $(date +%H:%M:%S)"
