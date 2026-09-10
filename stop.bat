@echo off
chcp 936 >nul
REM ============================================================
REM  无人饮料售货机 - 一键关闭脚本（Windows）
REM  通过端口 8000 定位并停止后端服务进程（不影响其他 python 程序）
REM ============================================================
setlocal

echo 正在查找售货机服务进程(端口 8000)...
set "FOUND=0"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    set "FOUND=1"
    echo 停止进程 PID=%%a
    taskkill /F /PID %%a >nul 2>&1
)

if "%FOUND%"=="0" goto not_found
echo 服务已停止。
goto done

:not_found
echo 未发现运行中的服务。

:done
pause
endlocal
