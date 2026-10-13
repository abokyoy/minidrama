@echo off
chcp 65001 >nul
cd /d "E:\LLM\try\minidrama\BaoJue"
set PY=C:\Users\86134\.workbuddy\binaries\python\envs\default\Scripts\python.exe

echo ============================================================
echo  Scheduler Command Console
echo ============================================================
echo.
echo   Dashboard (see GPU status anytime):  %PY% scheduler.py status
echo.
echo   Start scheduler (runs until idle):   %PY% scheduler.py run
echo.
echo   Reject a segment (re-chain):         %PY% scheduler.py reject 5 your reason
echo   Re-run after prompt edit:            %PY% scheduler.py resume 2
echo.
echo   Auto behavior of reject:
echo     - same chain as running segment  -> abort current, jump to next chain
echo     - different chain                -> wait current done, then re-order
echo ============================================================
echo.

set /p CMD="Enter command (status / run / reject N / resume N, ENTER to quit): "
if "%CMD%"=="" exit /b
%PY% scheduler.py %CMD%
echo.
pause
