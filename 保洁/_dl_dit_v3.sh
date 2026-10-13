#!/bin/bash
# ⭐⭐ 重下 DiT —— 这一版修掉了「重试重复追加」这个毁文件的bug。
#
#【上一版为什么坏】_dl_dit_fresh.sh 用的是：
#     curl --retry 30 ... -r $CUR-$((WANT-1)) "$URL" >> "$TMP"
# `--retry` 在连接中断后会**从 Range 起点重新请求**，而 `>>` 又把这次重下的
# 完整字节追加到文件末尾 → 同一段数据被写两遍 → 整份文件数据区错位。
# 症状：头声明 `comfy_quant` 是 U8[72] 的 JSON 文本，实际却是权重字节。
# 本版跑完 20GB 全程只搜不到一个 "int8_tensorwise" 标记。
#
# 【本版规则】
#   1. 单次 curl，**不带 --retry**（宁可失败重来，也不污染文件）。
#   2. 每次都从 0 开始、全量、写到**临时新文件**（`> file.part`，不是 `>>`）。
#      断了就整个重下，绝不续传拼接。
#   3. 下完先验尺寸，再验内容（_check_quant.py），全过才 mv 替换正式文件。
#   4. 磁盘要留够：part 20GB + 正式 20GB + 旧文件 20GB。
set -u
URL="https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors"
DIR="/d/h3models/diffusion_models"
T="$DIR/minimax_h3_fl2va_pruned_int8_convrot.safetensors"
WANT=20970379616
PART="$DIR/_dit_v3.part"
PX=(--proxy http://127.0.0.1:10808)

say() { echo "[$(date +%H:%M:%S)] $*"; }

# ── 代理探测 ──
say "探测代理 10808 ..."
if ! curl -s -o /dev/null --proxy "${PX[@]}" -r 0-1000 "$URL" --max-time 20; then
  say "✗ 代理不通。请在 cmd 里执行 set http_proxy=http://127.0.0.1:10808 后重跑"
  exit 2
fi
say "✓ 代理可用"

# ── 磁盘检查：part + 正式 + 旧文件，至少要 45GB 可用 ──
AVAIL=$(( $(df -m --output=avail "$DIR" | tail -1) ))
say "可用空间 ${AVAIL} MB"
if [ "$AVAIL" -lt 46000 ]; then
  say "✗ 空间不足 46GB（需要 part 20G + 正式 20G + 旧文件暂存）。先清 D 盘。"
  exit 3
fi

# ── 关键：先看看源站给的 Content-Length 对不对得上 ──
say "查询远端大小 ..."
CL=$(curl -sIL --proxy "${PX[@]}" "$URL" --max-time 30 | tr -d '\r' \
     | grep -i '^content-length:' | tail -1 | awk '{print $2}')
say "远端 Content-Length = ${CL:-未知}  本地目标 = $WANT"
if [ -n "${CL:-}" ] && [ "$CL" != "$WANT" ]; then
  say "✗ 远端大小与预期不符，中止（避免再下一份错的）"
  exit 4
fi

# ── 单次全量下载，无 --retry，失败就整个重来 ──
ATTEMPT=0
while true; do
  ATTEMPT=$((ATTEMPT+1))
  [ "$ATTEMPT" -gt 4 ] && { say "✗ 连试 $ATTEMPT 次都失败，放弃"; exit 1; }
  say "第 $ATTEMPT 次下载（全量，约需50-70 分钟，中断会自动重试但整份重下）..."
  rm -f "$PART"
  # ⭐ 用 >> 让 curl 的 stdout 进文件（-o 在本机写不出文件），
  #   但每次都是**新建** part、不追加到旧数据，所以重试不会重复拼接。
  curl -L --proxy "${PX[@]}" \
       --connect-timeout 30 \
       --speed-time 120 --speed-limit 1024 \
       -C - \
       "$URL" >> "$PART"
  RC=$?
  GOT=$(stat -c%s "$PART" 2>/dev/null || echo 0)
  say "  curl rc=$RC  本次拿到 $((GOT/1048576)) MB"
  if [ "$GOT" -eq "$WANT" ]; then
    say "✓ 尺寸精确匹配 $WANT"
    break
  fi
  if [ "$GOT" -gt "$WANT" ]; then
    say "  超了 $((GOT-WANT)) 字节，截断到精确值"
    M=$((WANT/1048576)); R=$((WANT%1048576))
    dd if="$PART" of="$PART.cut" bs=1048576 count=$M 2>/dev/null
    tail -c +$((M*1048576+1)) "$PART" | head -c $R >> "$PART.cut"
    mv -f "$PART.cut" "$PART"
    say "  截断后 = $(stat -c%s "$PART")"
    break
  fi
  say "  不足，重来（第 $ATTEMPT 次）"
  sleep 5
done

FS=$(stat -c%s "$PART")
[ "$FS" != "$WANT" ] && { say "✗ 尺寸 $FS != $WANT，放弃"; exit 1; }

# ── ⭐ 内容校验（尺寸对 ≠ 内容对，这是本项目最贵的一条教训）──
say "=== 尺寸对，验内容 ==="
PY="C:/Users/86134/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
if ! "$PY" /e/LLM/try/minidrama/保洁/_check_quant.py "$PART"; then
  say "✗ 内容坏，不替换正式文件。part 保留在 $PART 供细查。"
  exit 1
fi

say "=== 内容 OK，替换正式文件 ==="
mv -f "$T" "$DIR/_dit_old_bad.safetensors" 2>/dev/null
mv -f "$PART" "$T"
say "✓ 完成 $(stat -c%s "$T") bytes"
say "旧坏文件留在 $DIR/_dit_old_bad.safetensors，确认没问题后可删"