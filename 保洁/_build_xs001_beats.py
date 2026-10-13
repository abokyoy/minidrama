# -*- coding: utf-8 -*-
"""X003 终版剧本 → 新集 xs001 的分镜 beats（只做前 5 段 = 5 个 10 秒样片）

依据
----
1. 剧本：E:\\LLM\\try\\minidrama\\终版剧本\\X003_终版.md 第1集《擦桌子的人》场次 1-1
   （万山大厦 物业办公室 中午：耳钉搜卡）
2. `_diff_x003.py` 已逐条比对：X003 场次 1-1 与旧 ep001 场次 1-2
   **前 65 条台词一字不差**，只有 3 处差异：
     - 「景宸大厦」→「万山大厦」（改名）
     - 「咱们公司」→「咱们锦城」
     - 结尾多 4 句（钱经理「那……陆家那边……」等）
   → 前 5 段落在「一字不差」区间内，可直接复用已通过独立 agent 审核的旧分镜，
     只需把场景名景宸→万山。
3. 台词一个字不动（用户硬规矩），只做最小改写。

本文件只产出 5 段（t01–t05），对应剧本前 5 个 10 秒：
  t01 撞门拍桌（三楼包厢。贵客丢了一只金耳钉。三万八。）
  t02 点名（收台的时候，就你一个人在。/ 不是我。）
  t03 小唐作证（钱经理。中午，我看见她往兜里塞东西。没看清。）
  t04 看清楚了再说（小唐。看清楚了，再说。/ 反正，我看见了。）
  t05 掏兜（掏兜。自己掏，还是我喊保安。/ 你们不能搜我。）
"""
import json, os, io, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "ep001_beats", "scene12a.json")
OUT = os.path.join(BASE, "xs001_beats")
EPS = "xs01"
N = 5  # 只取前 5 段

REN = [
    ("景宸大厦", "万山大厦"),
    ("the property office of 景宸大厦", "the property office of 万山大厦"),
    ("the 3rd-floor ballroom corridor of 景宸大厦", "the 3rd-floor ballroom corridor of 万山大厦"),
]


def rename(text):
    for a, b in REN:
        text = text.replace(a, b)
    return text


def main():
    src = json.load(open(SRC, encoding="utf-8"))
    out = []
    for i, s in enumerate(src[:N], 1):
        d = json.loads(json.dumps(s, ensure_ascii=False))  # 深拷贝
        d["id"] = "%s_t%02d" % (EPS, i)
        d["scene"] = "1-1"  # X003 的场次号；1-1 在 ANCHORS 里是走廊 → 必须在渲染器映射
        for k in ("summary", "shots", "soundscape", "music"):
            if d.get(k):
                d[k] = rename(d[k])
        d["retention"] = rename(json.dumps(d["retention"], ensure_ascii=False)) and d["retention"]
        d["refs"] = [rename(r) for r in d["refs"]]
        out.append(d)

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "scene11.json")
    io.open(p, "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")

    print("写入 %s：%d 段" % (p, len(out)))
    for s in out:
        cn = re.findall(r"\[Chinese\]\s*([^\[\n]*)", s["shots"])
        nchar = sum(len(re.findall(r"[\u4e00-\u9fff]", x)) for x in cn)
        assert nchar <= 30, "段 %s 台词 %d 字，超 10 秒预算" % (s["id"], nchar)
        print("  %s  %-12s scene=%s  台词%d字/%d句  refs=%s"
              % (s["id"], s["title"], s["scene"], nchar, len(cn), s["refs"]))

    # 确认旧剧本地名已彻底清除
    blob = json.dumps(out, ensure_ascii=False)
    assert "景宸" not in blob, "仍残留景宸"
    print("✓ 无「景宸」残留；「万山」出现 %d 次" % blob.count("万山"))


if __name__ == "__main__":
    main()
