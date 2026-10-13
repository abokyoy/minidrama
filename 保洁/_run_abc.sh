#!/bin/bash
# A/B/C 三个变体串行：vC -> vA -> vB -> 自动对比
# 同一段 seg05、同 prev(seg04认可版)、同提示词，唯一差别是工作流。
#
# ⛔ 必须串行：一张 16GB 显存跑不了两个 H3 实例。
# ⛔ 建议 setsid 脱离父 shell：WorkBuddy 的 turn 被中断时，
#    同一进程组的后台任务会被一起杀掉（10-09 09:32 vC 就是这么没的）。
cd "E:/LLM/try/minidrama/保洁" || exit 1
export MINIDRAMA_PORT=8189
PY="C:/Users/86134/.workbuddy/binaries/python/versions/3.13.12/python.exe"
PYCV="C:/Users/86134/.workbuddy/binaries/python/envs/default/Scripts/python.exe"

echo "########## ABC 串行开始 $(date '+%m-%d %H:%M:%S') ##########"
for V in vC vA vB; do
  echo ""
  echo "======= $V 开始 $(date '+%H:%M:%S') ======="
  "$PY" -u _chain.py 5 --kind=chain --wf=$V --force 2>&1
  RC=$?
  echo "======= $V 结束 rc=$RC $(date '+%H:%M:%S') ======="
  if [ $RC -ne 0 ]; then
    echo "!! $V 失败(rc=$RC)，继续下一个变体"
  fi
  # 每段之间重启 ComfyUI，避免越接越黑
  "$PY" _kill_old.py 2>&1 | tail -1
  sleep 10
done

echo ""
echo "########## 三个变体跑完，开始对比 $(date '+%H:%M:%S') ##########"
"$PYCV" _abc_compare.py 2>&1
echo "########## ABC 全程结束 $(date '+%H:%M:%S') ##########"