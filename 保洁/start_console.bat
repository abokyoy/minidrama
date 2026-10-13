@echo off
chcp 65001 >nul
title BaoJue Scheduler Console - DO NOT CLOSE THIS WINDOW
cd /d "E:\LLM\try\minidrama\BaoJue"

echo ============================================================
echo   BaoJue Scheduler Console starting...
echo   Closing this window = scheduler stops. Do NOT close it.
echo ============================================================
echo.

rem -- Step 1: clean up stale processes (avoid GPU/port conflicts) --
echo [1/3] Cleaning stale processes...
"C:\Users\86134\.workbuddy\binaries\python\envs\default\Scripts\python.exe" _kill_stale.py
echo.

rem -- Step 2: start web dashboard (new window) --
echo [2/3] Starting web dashboard...
start "Dashboard Web - double-click to restart" cmd /k ""C:\Users\86134\.workbuddy\binaries\python\envs\default\Scripts\python.exe" -u web_server.py"
timeout /t 3 /nobreak >nul

rem -- Step 3: start scheduler (this window, logs shown here) --
echo [3/3] Starting scheduler (ComfyUI opens its own console window for progress)...
echo.
"C:\Users\86134\.workbuddy\binaries\python\envs\default\Scripts\python.exe" -u scheduler.py run

echo.
echo ============================================================
echo   Scheduler exited. If finished normally, press any key to close.
echo   To restart, double-click start_console.bat
echo ============================================================
pause
