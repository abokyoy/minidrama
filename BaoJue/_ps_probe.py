import subprocess, sys

# 用 tasklist 拿 pid，再用 ctypes/WMI 之外的方式看命令行：读 PEB 太重，
# 退而求其次——看哪个 pid 的可执行文件是 _run_ep.py 的启动器。
r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
                   capture_output=True, text=True, encoding="gbk", errors="replace")
print(r.stdout)