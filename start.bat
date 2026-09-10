@echo off
chcp 936 >nul
REM ============================================================
REM  无人饮料售货机 - 一键启动脚本（Windows）
REM  环境：conda 环境 py3.10 + Node.js
REM  启动后访问：http://127.0.0.1:8000
REM ============================================================
setlocal
cd /d %~dp0

echo [1/4] 激活 conda 环境 py3.10 ...
set "PY=python"
call conda activate py3.10 >nul 2>&1
if not errorlevel 1 goto env_ok
echo [提示] conda activate 失败，改用固定路径 D:\Anaconda_envs\envs\py3.10
set "PY=D:\Anaconda_envs\envs\py3.10\python.exe"
:env_ok

"%PY%" --version >nul 2>&1
if errorlevel 1 goto no_python

echo [2/4] 安装/校验后端依赖 ...
"%PY%" -m pip install -q -r backend\requirements.txt
if errorlevel 1 goto pip_fail

echo [3/4] 构建前端（已构建则跳过）...
if exist frontend\dist\index.html goto start_server
pushd frontend
call npm install --no-audit --no-fund
if errorlevel 1 goto npm_fail
call npm run build
if errorlevel 1 goto build_fail
popd

:start_server
echo [4/4] 初始化数据并启动服务 ...
"%PY%" backend\scripts\seed.py
cd backend
echo.
echo ============================================
echo  服务地址: http://127.0.0.1:8000
echo  管理员账号: admin / admin123
echo  按 Ctrl+C 停止服务
echo ============================================
"%PY%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
goto end

:no_python
echo [错误] 找不到 py3.10 环境的 python
echo        请先执行: conda create -n py3.10 python=3.10 -y
pause
exit /b 1

:pip_fail
echo [错误] 后端依赖安装失败，请检查网络后重试
pause
exit /b 1

:npm_fail
echo [错误] 前端依赖安装失败，请确认已安装 Node.js
popd
pause
exit /b 1

:build_fail
echo [错误] 前端构建失败
popd
pause
exit /b 1

:end
endlocal
