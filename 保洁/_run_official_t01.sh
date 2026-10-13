#!/bin/bash
# ⭐ H3 官方档一键验证：切档 + 用原版参考图 + 跑 t01 一段
#
# 用法（模型下完之后）：
#   bash _run_official_t01.sh              # 默认 official_turbo8
#   bash _run_official_t01.sh official20  # 跑 20 步档
set -u
cd /e/LLM/try/minidrama/保洁

PROF="${1:-official_turbo8}"

echo "=============================================================="
echo" 切档位：$PROF"
echo "=============================================================="
python _quality.py set "$PROF" || exit 1
python _quality.py show

echo ""
echo "=============================================================="
echo " 前置检查"
echo "=============================================================="
# ① 老 ComfyUI 必须关掉（抢显存会导致 10061 拒连/ 整个进程消失）
if tasklist /fo csv /nh 2>/dev/null | grep -qi "^python.*main.py"; then
  echo "⚠️检测到有 ComfyUI 在跑（python main.py）。"
  echo "   两个实例会抢显存，必须只留一个。"
  echo "   → 请先关掉旧窗口，再重跑本脚本。"
  exit 2
fi
# ② 三个模型文件都在？
for f in "/d/h3models/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors:20970379616" \
         "/d/h3models/vae/minimax_h3_video_vae_fp16.safetensors:5207808496" \
         "/d/h3models/loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors:1956193000"; do
  p="${f%%:*}"; want="${f##*:}"
  if [ ! -f "$p" ]; then echo "  ✗ 缺文件: $p"; exit 3; fi
  got=$(stat -c%s "$p")
  if [ "$got" != "$want" ]; then echo "  ✗ 尺寸不对: $(basename $p) $got != $want"; exit 3; fi
  echo "  ✓ $(basename "$p")  $got bytes"
done

echo ""
echo "=============================================================="
echo " 开跑（首次要加载19.5GB 模型，约 7-8 分钟）"
echo "=============================================================="
# 官方原版模型步数足，能自己做高光 roll-off → 必须用**原版**参考图
MINIDRAMA_REF=orig python _run_one.py 1 official
