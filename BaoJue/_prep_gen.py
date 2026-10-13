# -*- coding: utf-8 -*-
"""生成前后的资源体检 + 清场。

用户 2026-10-07 要求：
  1. 每次生成前都结束 ComfyUI，释放内存，再开始，保证速度
  2. 关掉占内存的应用（保留 WorkBuddy / v2rayN / mstsc 远程桌面 / 网易UU远程）

为什么重要（2026-10-07 实测）：
  第1 步采样 195s/it，正常 70-90s/it，最差 268s/it
  → 第 1 步最慢 = 模型正在加载 = 内存不够
  → 8 步预计从 10 分钟涨到 22 分钟
  → 原因就是后台 305 个进程占 9.2GB，ComfyUI 抢不到内存

用法：
  python _prep_gen.py           只体检（不杀任何东西）
  python _prep_gen.py --clean   体检 + 关 ComfyUI + 关第三方应用
"""
import ctypes
import ctypes.wintypes as wt
import subprocess
import sys
import time

# ══════════════════════════════════════════════════════════════
#  白名单：绝不能杀
# ══════════════════════════════════════════════════════════════
KEEP = {
    # 远程控制 —— 断了就联系不上（用户明确要求保留）
    "mstsc.exe", "gameviewerserver.exe", "gamviewer.exe",
    "uu.exe", "neteaseuu.exe", "uuclient.exe", "uuremote.exe",
    "remotedesktop.exe", "anydesk.exe", "sunloginclient.exe",
    "todesk.exe", "parsec.exe",
    # 代理 —— 断了下载不了
    "v2rayn.exe", "v2rayn-service.exe", "xray.exe", "sing-box.exe",
    "clash.exe", "clash-verge.exe", "verge-mihomo.exe",
    # 我们自己 + 它的子进程
    "workbuddy.exe", "codebuddy.exe", "code.exe", "node.exe",
    "python.exe", "pythonw.exe", "bash.exe", "sh.exe", "git.exe",
    "grep.exe", "sed.exe", "awk.exe", "tail.exe", "head.exe",
    # 系统骨架
    "system", "system idle process", "[system process]",
    "registry", "memory compression", "secure system",
    "smss.exe", "csrss.exe", "wininit.exe", "winlogon.exe",
    "services.exe", "lsass.exe", "lsm.exe", "svchost.exe",
    "fontdrvhost.exe", "dwm.exe", "sihost.exe", "ctfmon.exe",
    "conhost.exe", "powershell.exe", "pwsh.exe", "cmd.exe", "wscript.exe",
    "wmiprvse.exe", "wmic.exe", "taskhostw.exe", "runtimebroker.exe",
    "searchindexer.exe", "searchprotocolhost.exe", "searchfilterhost.exe",
    # 显卡 / 外设驱动（杀了会黑屏或外设失灵）
    "nvcontainer.exe", "nvdisplay.container.exe", "nvidia app.exe",
    "nvbackend.exe",
    "armourycrate.service.exe", "armourycrate.usersessionhelper.exe",
    "asussystemcontrol.exe", "asus_framework.exe", "asusservice.exe",
    "asusrotation.exe", "rogthrustv2service.exe", "rogliveservice.exe",
    "aura.service.exe", "lighting.service.exe",
    "logibolt.exe", "logioptionsmgr.exe", "logioptionsmanager.exe",
    "logioptionsservice.exe", "logioverlay.exe", "logiagent.exe",
    "lghub_system_tray.exe", "lghub_agent.exe", "lghub_manager.exe",
    "audioaccessoryservice.exe", "nahimicservice.exe",
    "btpaneld.exe", "rtsservice.exe",
    # 输入法 / 安全软件（杀了我这边没法打字、也拦不了误操作）
    "ime_service.exe", "imeservice.exe", "hipstrust.exe", "hipsdaemon.exe",
    "hipsmain.exe", "hipsclient.exe", "hipslog.exe", "kemonmain.exe",
    "kemon.exe", "usblink.exe", "usbkey.exe", "wetype_server.exe",
    "wetype_renderer.exe", "wetype_update.exe", "qqpcmgr.exe",
    "msmpeng.exe", "nissrv.exe", "windowsdefender.exe",
    # 其它常驻小工具（杀了收益小、风险高）
    "explorer.exe", "widgets.exe", "taskhost.exe", "sihost.exe",
    "microsoftedgewebview2.exe", "geekdesk.exe", "msmpci.dll",
}

# ══════════════════════════════════════════════════════════════
#  黑名单：优先关（按占内存排序）
# ══════════════════════════════════════════════════════════════
KILL_FIRST = [
    # ── 本机实测的大头（2026-10-07 体检得出）──
    "gh.exe",              # GitHub Desktop，实测占 3.7 GB ← 单个最大
    "githubdesktop.exe",
    "doubao.exe",          # 豆包（用户 2026-10-10 同意加入清场，实测 0.4GB）
    "geekdesk.exe",          # 桌面记录，常驻 444 MB
    "nvidia overlay.exe",    # N卡覆盖层，255 MB
    "promecefpluginhost.exe",  # 剪映/CEF 插件宿主
    "msedge.exe", "chrome.exe", "firefox.exe", "brave.exe",
    "msedgewebview2.exe",
    "wps.exe", "wpscloud.exe", "wpscloudsvr.exe", "et.exe", "wpp.exe",
    "qq.exe", "wechat.exe", "wxwork.exe", "weixin.exe",
    "neteasemusic.exe", "qqmusic.exe", "kugou.exe", "kuwo.exe",
    "steam.exe", "steamwebhelper.exe", "epicgameslauncher.exe",
    "battle.net.exe", "bnet.exe", "origin.exe", "ubisoftconnect.exe",
    "nvidia app.exe", "nvidia share.exe",
    "armourycrate.usersessionhelper.exe", "rogliveservice.exe",
    "obs64.exe", "obsidian.exe", "notion.exe", "typora.exe",
    "postman.exe", "docker desktop.exe", "com.docker.backend.exe",
    "idea64.exe", "pycharm64.exe", "rider64.exe", "webstorm.exe",
    "datagrip64.exe", "cursor.exe",
    "figma.exe", "skype.exe", "discord.exe", "telegram.exe",
    "spotify.exe", "foobar2000.exe", "aimp.exe",
    "vlc.exe", "potplayermini64.exe", "mpc-hc.exe",
    "excel.exe", "powerpnt.exe", "winword.exe", "outlook.exe",
    "onedrive.exe", "dropbox.exe", "baidunetdisk.exe", "nutstore.exe",
    "capcut.exe", "jianying.exe", "xvideoclient.exe",
    "adb.exe", "scrcpy.exe", "mumu.exe", "nox.exe", "ldplayer.exe",
]

# ComfyUI 相关的进程名（生成前必须全关）
COMFY_PROCS = [
    "main.py",             # ComfyUI 主进程
    "comfyui.exe",
    "python.exe",          # 只会杀带 comfy 参数的，见 kill_comfy
]


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
        ("th32ProcessID", wt.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
        ("th32ParentProcessID", wt.DWORD), ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wt.DWORD), ("szExeFile", ctypes.c_char * 260),
    ]


class PMC(ctypes.Structure):
    _fields_ = [
        ("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


TH32CS_SNAPPROCESS = 2
INVALID = ctypes.c_void_p(-1).value
PSAPI = ctypes.windll.psapi
KERNEL = ctypes.windll.kernel32
PROCESS_QUERY_LIMITED = 0x1000
PROCESS_TERMINATE = 0x0001


def phys():
    class MS(ctypes.Structure):
        _fields_ = [
            ("dwLength", wt.DWORD), ("dwMemoryLoad", wt.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]
    m = MS()
    m.dwLength = ctypes.sizeof(MS)
    KERNEL.GlobalMemoryStatusEx(ctypes.byref(m))
    return m


def snapshot():
    snap = KERNEL.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == INVALID:
        return []
    e = PROCESSENTRY32()
    e.dwSize = ctypes.sizeof(PROCESSENTRY32)
    out = []
    ok = KERNEL.Process32First(snap, ctypes.byref(e))
    while ok:
        if e.th32ProcessID != 0:
            name = e.szExeFile.decode("utf-8", "replace")
            h = KERNEL.OpenProcess(PROCESS_QUERY_LIMITED, False,
                                   e.th32ProcessID)
            c = PMC()
            c.cb = ctypes.sizeof(PMC)
            rss = 0.0
            if h and PSAPI.GetProcessMemoryInfo(h, ctypes.byref(c), c.cb):
                rss = c.WorkingSetSize / 1024 / 1024
            if h:
                KERNEL.CloseHandle(h)
            out.append({"pid": e.th32ProcessID, "name": name, "rss": rss,
                        "cmdline": cmdline_of(e.th32ProcessID)})
        ok = KERNEL.Process32Next(snap, ctypes.byref(e))
    KERNEL.CloseHandle(snap)
    return out


def cmdline_of(pid):
    """读命令行，用来认出ComfyUI 的 python 进程。"""
    try:
        out = subprocess.run(
            ["wmic", "process", "where", "ProcessId=%d" % pid,
             "get", "CommandLine"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=15)
        t = out.stdout
        i = t.find("\n")
        return (t[i + 1:] if i > 0 else "").strip()[:400]
    except Exception:
        return ""


def gpu():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,memory.used",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20)
        t, u = [x.strip() for x in out.stdout.strip().split(",")]
        return int(t), int(u)
    except Exception:
        return 0, 0


def kill_pid(pid):
    try:
        KERNEL.OpenProcess(PROCESS_TERMINATE, False, pid)
        h = KERNEL.OpenProcess(PROCESS_TERMINATE, False, pid)
        if h:
            KERNEL.TerminateProcess(h, 0)
            KERNEL.CloseHandle(h)
            return True
    except Exception:
        pass
    return False


def report(procs=None):
    m = phys()
    tot = m.ullTotalPhys / 1024 ** 3
    av = m.ullAvailPhys / 1024 ** 3
    gt, gu = gpu()
    print("=" * 60)
    print("物理内存 %.1f GB  空闲 %.1f GB  已用 %.1f GB (%.0f%%)"
          % (tot, av, tot - av, (tot - av) / tot * 100))
    print("提交内存 可用 %.1f GB / 总 %.1f GB"
          % (m.ullAvailPageFile / 1024 ** 3, m.ullTotalPageFile / 1024 ** 3))
    print("显存%d MB / %d MB" % (gu, gt))
    ps = procs if procs is not None else snapshot()
    print("进程数 %d" % len(ps))

    # ⛔ 关键健康检查：内存爆掉 → 采样速度崩（2026-10-07 实测 68→180 s/it）
    used_pct = (tot - av) / tot
    if used_pct >= 0.92:
        print("")
        print("⛔⛔⛔ 内存已爆（%d%%）！" % round(used_pct * 100))
        print("     实测后果：采样从68 s/it 掉到 180+ s/it（第6 步之后开始崩）")
        print("     原因：模型 19995MB > 显存 16384MB → 每步在显存/内存间搬运")
        print("           内存满了就只能走页文件 → 每步多花 110 秒")
        print("     提交内存只剩 %.1f GB，必须清场"
              % (m.ullAvailPageFile / 1024 ** 3))
    elif used_pct >= 0.85:
        print("")
        print("⚠️ 内存偏高（%d%%），采样可能变慢，建议清场" % round(used_pct * 100))

    agg = {}
    for p in ps:
        agg.setdefault(p["name"].lower(), [0, 0.0])
        agg[p["name"].lower()][0] += 1
        agg[p["name"].lower()][1] += p["rss"]
    top = sorted(agg.items(), key=lambda r: -r[1][1])[:18]
    print("-" * 60)
    for n, (c, mb) in top:
        mark = ""
        if n in {k.lower() for k in KILL_FIRST}:
            mark = "  << 可关"
        print("  %-34s x%-3d %7.0f MB%s" % (n, c, mb, mark))

    # ComfyUI 在哪
    comfy = [p for p in ps
             if "comfy" in p["cmdline"].lower()
             or "comfyui" in p["name"].lower()]
    if comfy:
        print("-" * 60)
        print("ComfyUI 进程:")
        for p in comfy:
            print("  pid=%d %s %.0f MB" % (p["pid"], p["name"], p["rss"]))
            print("      %s" % p["cmdline"][:120])
    return ps


def kill_comfy(ps):
    """关掉所有 ComfyUI 进程（含用 python 起的）。"""
    killed = []
    for p in ps:
        cl = p["cmdline"].lower()
        is_comfy = ("comfyui" in cl
                    or "comfy" in p["name"].lower()
                    or ("main.py" in cl and "comfy" in cl))
        if not is_comfy:
            continue
        if p["name"].lower() in KEEP and "comfy" not in cl:
            continue
        if kill_pid(p["pid"]):
            killed.append((p["pid"], p["name"], p["rss"]))
    return killed


def kill_apps(ps):
    """关掉占内存的第三方应用。"""
    targets = {k.lower() for k in KILL_FIRST}
    byname = {}
    for p in ps:
        byname.setdefault(p["name"].lower(), []).append(p)
    killed = []
    for n, lst in byname.items():
        if n not in targets or n in KEEP:
            continue
        freed = 0.0
        for p in lst:
            if kill_pid(p["pid"]):
                freed += p["rss"]
        if freed > 0:
            killed.append((n, len(lst), freed))
    return killed


def main():
    clean = "--clean" in sys.argv

    print("【生成前体检】")
    ps = report()

    if not clean:
        print()
        print("加 --clean 才会真的关进程。")
        return

    print()
    print("【关ComfyUI 释放显存/内存】")
    time.sleep(1)
    ps2 = snapshot()
    kc = kill_comfy(ps2)
    if kc:
        for pid, n, mb in kc:
            print("  已关 pid=%d %s (%.0f MB)" % (pid, n, mb))
    else:
        print("  ComfyUI 本来就没在跑")
    time.sleep(4)

    print()
    print("【关占内存的第三方应用】")
    ps3 = snapshot()
    ka = kill_apps(ps3)
    if ka:
        for n, c, mb in sorted(ka, key=lambda r: -r[2]):
            print("  已关 %-24s x%-2d 释放 %.0f MB" % (n, c, mb))
    else:
        print("  没有可关的目标")
    time.sleep(5)

    print()
    print("【清场后】")
    report()


if __name__ == "__main__":
    main()