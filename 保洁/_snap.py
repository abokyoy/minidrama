# -*- coding: utf-8 -*-
"""分镜产物 sha 快照 —— 改渲染器前的零影响验证工具。

铁律（踩过 costly 的坑）：`storyboard_render.py` 任何改动之后，
必须拍快照 → 改 → 重渲染 → 比对，确认「变化段数 = 0」再往下走。
否则已生成的几十小时成片会因为 sha 变化被判定为 stale 而全部重跑。

manifest 真实结构：`epXXX_segs/manifest.json` 是一个 **list**，
每项形如 {"n":1, "id":"ep01_t01", "sha":"f8f822...", ...}，
sha 取前 16 位十六进制。第一版按 dict 写、路径写成 `ep001/manifest.json`，
扫到 0 集 —— manifest 其实是 list，且在 `epXXX_segs/` 下。别再假设结构。

用法：
  python _snap.py before.json           # 改渲染器之前
  python _snap.py after.json            # 改完重渲染之后
  python _snap.py diff before.json after.json
退出码：diff 有变化返回 1（方便脚本判断）
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
# ⚠️ 必须包含 xs 系列（X003 终版剧本）。第一版只写 ep001–ep005，
#    结果改完渲染器重渲染时 xs001–xs005 全在验证视野外，
#    「变化 0」是假的。2026-10-07 补。
EPS = ("ep001", "ep002", "ep003", "ep004", "ep005",
       "xs001", "xs002", "xs003", "xs004", "xs005")


def snap():
    out = {}
    for ep in EPS:
        m = os.path.join(BASE, ep + "_segs", "manifest.json")
        if not os.path.exists(m):
            continue
        try:
            d = json.load(io.open(m, encoding="utf-8"))
        except Exception as e:
            print("  跳过 %s：读不了 manifest（%s）" % (ep, e))
            continue
        items = d if isinstance(d, list) else d.get("segments", [])
        out[ep] = {it.get("id"): it.get("sha") for it in items if isinstance(it, dict)}
    return out


def save(path, s):
    io.open(path, "w", encoding="utf-8").write(
        json.dumps(s, ensure_ascii=False, sort_keys=True, indent=1))
    print("快照 %s：%d 集 / %d 段" % (os.path.basename(path), len(s),
                                       sum(len(v) for v in s.values())))


def diff(pa, pb):
    a = json.load(io.open(pa, encoding="utf-8"))
    b = json.load(io.open(pb, encoding="utf-8"))
    changed, same, gone = [], 0, []
    for ep in sorted(set(a) | set(b)):
        ka, kb = a.get(ep, {}), b.get(ep, {})
        for k in sorted(set(ka) | set(kb)):
            if k not in kb:
                gone.append(ep + "/" + k)
            elif k not in ka:
                changed.append(ep + "/" + k + " (新增)")
            elif ka[k] != kb[k]:
                changed.append(ep + "/" + k)
            else:
                same += 1
    print("=" * 60)
    print(" 未变 %d 段 ｜ 变化 %d 段 ｜ 消失 %d 段" % (same, len(changed), len(gone)))
    print("=" * 60)
    for c in changed[:40]:
        print("  变 %s" % c)
    for g in gone[:20]:
        print("  失 %s" % g)
    if len(changed) > 40:
        print("  … 还有 %d 段" % (len(changed) - 40))
    return len(changed)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1] == "diff":
        n = diff(sys.argv[2], sys.argv[3])
        sys.exit(1 if n else 0)
    else:
        save(sys.argv[1], snap())
