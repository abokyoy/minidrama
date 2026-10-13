# -*- coding: utf-8 -*-
"""按行号精确替换 index.html 里播放器那段（避免 Edit 工具对不上）。
把重复的内联「生成中」面板抽成 runPanelHTML() 函数。
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "index.html")
lines = io.open(P, encoding="utf-8").read().split("\n")

# ⛔ 不用硬行号（内容一改就漂）→ 按内容定位边界
#起点：含 "}else if(vsrc !== lastVsrc){" 的那一行
i0 = next(i for i, l in enumerate(lines) if "else if(vsrc !== lastVsrc)" in l)
# 终点：从i0 往下第一处 "    lastVsrc = vsrc;" 的下一行
i1 = next(i for i, l in enumerate(lines) if i > i0 and l.strip() == "lastVsrc = vsrc;")
print("定位：%d..%d" % (i0 + 1, i1 + 1))
print("--- 起点行 ---", lines[i0][:70])
print("--- 终点行 ---", lines[i1][:70])

new = """}else if(vsrc !== lastVsrc){
    if(vsrc){
      const warn = cur.video.stale
        ? `<div class="vwarn">\\u26A0 \\u8FD9\\u662F\\u4E0A\\u4E00\\u8F6E\\u8DD1\\u5269\\u7684\\u65E7\\u7247\\uFF08${cur.video.mtime}\\uFF09\\uFF0C\\u672C\\u7247\\u5C1A\\u672A\\u91CD\\u8DD1</div>` : '';
      $('#stage').innerHTML = warn +
        `<video id="vd" src="${vsrc}#t=0.1" controls preload="auto" playsinline></video>`;
    }else{
      $('#stage').innerHTML = `<div class="empty">${cur?('\\u7247'+cur.seg+' \\u8FD8\\u6CA1\\u6709\\u6210\\u7247<br><span style="font-size:12px">'+ST[cur.status].t+'</span>'):'\\u6CA1\\u6709\\u53EF\\u9884\\u89C8\\u7684\\u6210\\u7247'}</div>`;
    }
    lastVsrc = vsrc;
  }"""

# 中文直接写更清楚，改用 unicode 转义会难读 → 这里直接用可读中文
new = """}else if(vsrc !== lastVsrc){
    if(vsrc){
      const warn = cur.video.stale
        ? `<div class="vwarn">⚠ 这是上一轮跑剩的旧片（${cur.video.mtime}），本片尚未重跑</div>` : '';
      $('#stage').innerHTML = warn +
        `<video id="vd" src="${vsrc}#t=0.1" controls preload="auto" playsinline></video>`;
    }else{
      $('#stage').innerHTML = `<div class="empty">${cur?('片'+cur.seg+' 还没有成片<br><span style="font-size:12px">'+ST[cur.status].t+'</span>'):'没有可预览的成片'}</div>`;
    }
    lastVsrc = vsrc;
  }"""

out = lines[:i0] + new.split("\n") + lines[i1 + 1:]
txt = "\n".join(out)

# 追加 runPanelHTML 函数（放在 node(x) 之前）
panel = '''
function runPanelHTML(cur){
  const busy = S.queue && S.queue.gpu_busy;
  const q = S.queue || {};
  return `<div class="empty" style="padding:38px 20px">
   <div style="font-size:30px;margin-bottom:14px">🎬</div>
   <div style="font-size:19px;color:#378ADD;font-weight:600;margin-bottom:10px">
     片${cur.seg} 正在生成中
   </div>
   <div style="font-size:13px;line-height:1.9;color:#8a9aa8">
     链${cur.chain} · 第${cur.pos}片 · ${cur.kind==='chain'?'接上一段尾帧':'从参考图起'} ·
     提示词 ${cur.words} 词<br>
     一片约需 13–15 分钟，出片后这一页会自动出现播放条
     ${cur.started_at?'<br>开跑时间 '+cur.started_at:''}
   </div>
   <div style="margin-top:16px;font-size:12px;color:#5a6a78">
     ${busy?'GPU 正在满载计算':'⚠ GPU 当前空闲，请检查调度器'}
     ${q.alive?('｜ComfyUI 运行中 '+q.running+' 个 / 排队 '+q.pending+' 个'):''}
   </div>
 </div>`;
}
'''
anchor = "\nfunction node(x){"
assert anchor in txt, "找不到 node(x)"
txt = txt.replace(anchor, panel + anchor, 1)

io.open(P, "w", encoding="utf-8").write(txt)
print("✅ 替换完成，runPanelHTML 已加入")
# 自检：确认没有重复的内联面板
n = txt.count("正在生成中")
print("「正在生成中」出现次数 =", n, "（应为 1）")
n2 = txt.count("}else if(vsrc !== lastVsrc){")
print("播放器分支次数 =", n2, "（应为 1）")