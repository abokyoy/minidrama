#!/bin/bash
# ⛔ 不间断产片：一条命令跑完一集的 N 个片，全程无人干预。
#
# 用法：
#   bash _run_all.sh 8          # 从seg01 跑到 seg08
#   bash _run_all.sh 3 2        # 从第2片跑到第3片
#
# 每片：fixed（每3片的第1片）或 chain（接上一片尾帧）
# 每片之间自动重启 ComfyUI（防越接越黑）
# 每片出片立刻落一份成片清单到 all_segs.txt
#
# ⛔ 必须一次跑很多片，不要一段段问我 —— 这正是之前效率低的原因。

cd "E:/LLM/try/minidrama/保洁" || exit 1
export MINIDRAMA_PORT=8189
PY="C:/Users/86134/.workbuddy/binaries/python/versions/3.13.12/python.exe"
PYCV="C:/Users/86134/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
OUT="D:/output_h3off"

FROM=${1:-1}
TO=${2:-8}
LIST="all_segs.txt"

echo "########## 不间断产片 seg$(printf %02d $FROM) → seg$(printf %02d $TO) ##########"
echo "开始时间: $(date '+%m-%d %H:%M:%S')"

for SID in $(seq $FROM $TO); do
  SS=$(printf "%02d" $SID)
  echo ""
  echo "════════════ seg$SS 开始 $(date '+%H:%M:%S') ════════════"

  # 只在「这一片还没成片」时才跑；要重跑加 --force
  "$PY" -u _chain.py $SID 2>&1 | tail -25
  RC=${PIPESTATUS[0]}

  # 核对真实落盘（日志里的路径长期不可信）
  FOUND=$(ls -t $OUT/off_xs01_t${SS}_*-audio.mp4 2>/dev/null | head -1)
  if [ -z "$FOUND" ]; then
    FOUND=$(ls -t $OUT/off_xs01_t${SS}_*.mp4 2>/dev/null | head -1)
  fi

  if [ -n "$FOUND" ]; then
    SZ=$(du -m "$FOUND" | cut -f1)
    DUR=$("$PYCV" -c "
import subprocess,sys
try:
    r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',r'$FOUND'],capture_output=True,text=True,timeout=30)
    print('%.1f' % float(r.stdout.strip()))
except Exception: print('?')
" 2>/dev/null)
    echo "$SS|$FOUND|$SZ MB|${DUR}s|$(date '+%H:%M:%S')" >> $LIST
    echo "  ★ seg$SS 出片: $FOUND (${SZ}MB, ${DUR}s)"
  else
    echo "  ✗ seg$SS 没出片 (rc=$RC)"
    echo "$SS|失败 rc=$RC|$(date '+%H:%M:%S')" >> $LIST
  fi

  # 重启 ComfyUI（防越接越黑，也清掉上一片的显存残留）
  "$PY" _kill_old.py 2>&1 | tail -1
  sleep 8
done

echo ""
echo "########## 全部跑完 $(date '+%m-%d %H:%M:%S') ##########"
echo ""
echo "==== 成片清单 ===="
cat $LIST
echo ""
echo "==== 质量体检 ===="
"$PYCV" _abc_compare.py 2>&1 | head -40