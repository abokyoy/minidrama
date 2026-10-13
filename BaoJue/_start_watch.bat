@echo off
REM Background watcher: checks pipeline every 10 min, logs to logs\watch_gen.log
cd /d "E:\LLM\try\minidrama\BaoJue"
"C:\Users\86134\.workbuddy\binaries\python\versions\3.13.12\python.exe" -u _watch_gen.py --loop >> "logs\watch_gen.log" 2>&1
