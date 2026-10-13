# -*- coding: utf-8 -*-
"""剧集台账 · SQLite 存储层（2026-10-10 用户要求引入数据库机制）
══════════════════════════════════════════════════════════════════

用户 2026-10-10 要求（原话）：
  「这个网站系统要更新 使用sqllite做为数据库引入数据库机制
    这个网站可以操作整个过程」

⛔⛔⛔ 2026-10-09 用户定的架构（原话，JSON 版迁来，语义不变）：
  「首先，你把剧本写成了每 10 秒一个的分镜脚本……这一个 10 秒一个的分镜脚本
    就是一个片。然后，每一片的脚本应该都是经过评审的……你应该有一个片的一个文件。
    这个文件里面记录了所有的片的提示词。然后每 3 个片在一个链上……
    然后你 GPU 就从前往后去取一个片，然后来运行。」

设计（⛔ 铁律）：
  ① **对外接口不变**：`load()` / `save()` / `S()` / `next_pending()` /
     `set_chain()` / `table()` 与旧 JSON 版同名同语义。
     scheduler.py / web_server.py 不用改调用方式。
  ② **SQLite 主存，JSON 只当备份**：每次 save 先写库（事务），再顺手
     dump 一份 show_ledger.json（人工可看 + 兜底）。
  ③ **操作流水表 ops**：谁在什么时候对哪片做了什么 —— 「网站可以操作
     整个过程」的账本基础，网页有 API 可查。
  ④ **WAL 模式**：调度器写 + 网页读同时进行，互不锁死。
"""

import io
import json
import os
import sqlite3
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SEGS = os.path.join(HERE, "xs001_segs")
DB_PATH = os.path.join(HERE, "show_ledger.db")
LEDGER = os.path.join(HERE, "show_ledger.json")   # 兼容旧引用（备份用）

CHAIN_SIZE = 3

ASPECT_W_H = {"4:3 (Standard)": (4, 3), "9:16 (Portrait)": (9, 16),
              "1:1 (Square)": (1, 1), "16:9 (Landscape)": (16, 9)}

# ── 片的状态机（与旧版一致）─────────────────────────────────────
ST_PENDING = "pending"
ST_RUNNING = "running"
ST_DONE = "done"
ST_REJECTED = "rejected"
ST_HOLD = "hold"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
  key   TEXT PRIMARY KEY,
  value TEXT
);
CREATE TABLE IF NOT EXISTS segments (
  sid      INTEGER PRIMARY KEY,
  data     TEXT NOT NULL            -- 每片一个 JSON（字段会演进，不拆列）
);
CREATE TABLE IF NOT EXISTS ops (
  id    INTEGER PRIMARY KEY AUTOINCREMENT,
  t     TEXT NOT NULL,
  sid   INTEGER,                      -- NULL = 全局操作（如断链/导入）
  verb  TEXT NOT NULL,                -- preflight/promote/reject/approve/kill/stale/import...
  detail TEXT
);
CREATE INDEX IF NOT EXISTS idx_ops_sid ON ops(sid);
"""


def _conn():
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=10000")
    c.execute("PRAGMA synchronous=NORMAL")
    return c


def _init_db():
    with _conn() as c:
        c.executescript(_SCHEMA)
        row = c.execute("SELECT value FROM meta WHERE key='title'").fetchone()
        if row is None:
            c.execute("INSERT INTO meta VALUES('title',?)", ("X003 保洁",))
            c.execute("INSERT INTO meta VALUES('chain_size',?)", (str(CHAIN_SIZE),))


def log_op(sid, verb, detail=""):
    """记一条操作流水（网页「操作记录」数据源）。永不抛错。"""
    try:
        with _conn() as c:
            c.execute("INSERT INTO ops(t,sid,verb,detail) VALUES(?,?,?,?)",
                      (time.strftime("%Y-%m-%d %H:%M:%S"), sid, verb, detail))
    except Exception:
        pass


def ops_history(sid=None, limit=100):
    """查操作流水。sid=None 查全部。"""
    _init_db()
    with _conn() as c:
        if sid is None:
            rows = c.execute("SELECT t,sid,verb,detail FROM ops "
                             "ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        else:
            rows = c.execute("SELECT t,sid,verb,detail FROM ops "
                             "WHERE sid=? ORDER BY id DESC LIMIT ?",
                             (sid, limit)).fetchall()
    return [{"t": r[0], "sid": r[1], "verb": r[2], "detail": r[3]} for r in rows]


def _import_json_if_fresh():
    """库里没有任何片、而 JSON 台账有 → 导入（首次切换跑一次）。"""
    _init_db()
    with _conn() as c:
        n = c.execute("SELECT COUNT(*) FROM segments").fetchone()[0]
    if n > 0 or not os.path.exists(LEDGER):
        return
    try:
        led = json.load(io.open(LEDGER, encoding="utf-8"))
    except Exception:
        return
    with _conn() as c:
        for k, sg in (led.get("segments") or {}).items():
            c.execute("INSERT OR REPLACE INTO segments(sid,data) VALUES(?,?)",
                      (int(k), json.dumps(sg, ensure_ascii=False)))
        for k in ("title", "chain_size", "default_stage", "created"):
            if k in led:
                c.execute("INSERT OR REPLACE INTO meta VALUES(?,?)",
                          (k, str(led[k])))
    log_op(None, "import", "从 show_ledger.json 导入 %d 片"
           % len(led.get("segments") or {}))


_init_db()
_import_json_if_fresh()


# ── 对外接口（与旧 JSON 版同名同语义）───────────────────────────
def chain_of(sid):
    return (sid - 1) // CHAIN_SIZE + 1


def pos_in_chain(sid):
    return (sid - 1) % CHAIN_SIZE + 1


def chain_members(cid):
    start = (cid - 1) * CHAIN_SIZE + 1
    return list(range(start, start + CHAIN_SIZE))


def prompt_path(sid):
    return os.path.join(SEGS, "seg%02d_prompt.txt" % sid)


def kind_of(sid):
    return "fixed" if pos_in_chain(sid) == 1 else "chain"


def load(path=LEDGER):
    """读台账 dict。⛔ 返回结构与旧版一致：{title, chain_size, segments{...}}。"""
    _init_db()
    led = {"title": "X003 保洁", "chain_size": CHAIN_SIZE, "segments": {}}
    with _conn() as c:
        for k, v in c.execute("SELECT key,value FROM meta"):
            if k != "chain_size":
                led[k] = v
        row = c.execute("SELECT value FROM meta WHERE key='chain_size'").fetchone()
        if row:
            led["chain_size"] = int(row[0])
        for sid, data in c.execute("SELECT sid,data FROM segments ORDER BY sid"):
            led["segments"][str(sid)] = json.loads(data)
    if not led["segments"] and os.path.exists(path):
        return json.load(io.open(path, encoding="utf-8"))
    return led


def save(led, path=LEDGER):
    """写库（事务）+ dump 一份 JSON 备份。"""
    _init_db()
    with _conn() as c:
        c.execute("DELETE FROM segments")
        for k, sg in led["segments"].items():
            c.execute("INSERT INTO segments(sid,data) VALUES(?,?)",
                      (int(k), json.dumps(sg, ensure_ascii=False)))
        for k in ("title", "chain_size", "default_stage"):
            if k in led:
                c.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (k, str(led[k])))
    led["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    try:                                   # JSON 备份失败不影响主流程
        tmp = path + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as f:
            json.dump(led, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
    except Exception:
        pass
    return DB_PATH


def S(led, sid):
    return led["segments"][str(sid)]


def build(sids, title="", reviewed=True):
    """从磁盘上的提示词文件生成台账。**只收录已经有提示词文件的片。**"""
    segs = {}
    for sid in sids:
        pp = prompt_path(sid)
        if not os.path.exists(pp):
            continue
        n = len(io.open(pp, encoding="utf-8").read().split())
        segs[str(sid)] = {
            "chain": chain_of(sid),
            "pos": pos_in_chain(sid),
            "kind": kind_of(sid),
            "prompt": os.path.basename(pp),
            "words": n,
            "reviewed": bool(reviewed),
            "status": ST_PENDING,
            "stage": "preview",            # ⛔ 2026-10-10 用户铁律：默认低清
            "out": None,
            "history": [],
        }
    return {"title": title, "chain_size": CHAIN_SIZE,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"), "segments": segs}


def next_pending(led, only_chain=None):
    """取下一个该跑的片。规则与旧版一致。"""
    sids = sorted(int(k) for k in led["segments"])
    for sid in sids:
        sg = S(led, sid)
        if only_chain is not None and sg["chain"] != only_chain:
            continue
        if sg["status"] != ST_PENDING:
            continue
        # 同链前置片没完成 → 不能跳着跑（会拿到错的 prev_video）
        # ⛔ 2026-10-10 15:50 补：前置片「低清已出、hold 等用户确认」也算
        #   可续接（预出片与终版同参数同几何基准，拿低清当锚完全成立）。
        #   否则链1片1一 hold，片2/片3 永远卡死 —— 15:47 实际发生。
        if sg["pos"] > 1:
            prev = S(led, sid - 1)
            if prev["status"] not in (ST_DONE, ST_HOLD):
                continue
        return sid
    return None


def pending_chains(led):
    """还有活要干的链（按链号从小到大）。"""
    cs = []
    for k in sorted(led["segments"], key=lambda x: int(x)):
        sg = led["segments"][k]
        if sg["status"] in (ST_PENDING, ST_REJECTED):
            if sg["chain"] not in cs:
                cs.append(sg["chain"])
    return cs


def set_chain(led, cid, status, reason="", keep_approved=True):
    """把整条链打回某个状态。用户否定一片 = 整链重排（用户原话）。

    ⛔ keep_approved：用户**点头过**的片（approved_by_user）不因同链被打回而重做。
    """
    hit = []
    for sid in chain_members(cid):
        k = str(sid)
        if k not in led["segments"]:
            continue
        sg = led["segments"][k]
        if (keep_approved and sg.get("approved_by_user")
                and sg["status"] == ST_DONE and pos_in_chain(sid) > 1):
            hit.append(sid)          # 保留：已认可且不是链首
            continue
        if status == ST_PENDING and sg["status"] == ST_DONE:
            # 已完成但同链被否 → 也要重做（用户：「合理推断也会有问题」）
            if sg.get("out"):
                sg["history"].append({"t": time.strftime("%H:%M:%S"),
                                      "why": reason, "was": sg["out"]})
                sg["out"] = None
            sg["status"] = ST_PENDING
        else:
            sg["status"] = status
        hit.append(sid)
    log_op(None, "set_chain", "链%d → %s（%s）：片 %s"
           % (cid, status, reason, hit))
    return hit


def table(led):
    """给人看的板。"""
    lines = ["片   链.位 方式    状态     档     字数  产出"]
    for k in sorted(led["segments"], key=lambda x: int(x)):
        sg = led["segments"][k]
        mark = {"done": "OK", "running": ">>", "pending": "..",
                "hold": "!!", "rejected": "XX"}.get(sg["status"], "??")
        out = os.path.basename(sg.get("out") or sg.get("draft_out") or "-")
        if sg.get("draft_out") and not sg.get("out"):
            out = "(低清)" + out
        lines.append("%-4s %d.%d   %-7s %-11s %-6s %5d  %s"
                     % (k, sg["chain"], sg["pos"], sg["kind"],
                        sg["status"] + " " + mark,
                        sg.get("stage") or "preview",
                        sg.get("words", 0), out))
    return "\n".join(lines)
