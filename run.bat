@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ========================================
echo    VibeWatermark 正在启动 ...
echo ========================================
echo.

REM 检测 uv 是否可用
uv --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] 未检测到 uv，正在安装 ...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex" >nul 2>&1
    if errorlevel 1 (
        echo [INFO] 尝试通过 pip 安装 ...
        pip install uv >nul
    )
    echo [INFO] uv 安装完成
) else (
    echo [INFO] uv 已就绪
)

echo.
echo [INFO] 正在运行主程序 ...
echo.

uv run "%~dp0main.py"
set EXIT_CODE=!ERRORLEVEL!

echo.
if !EXIT_CODE! neq 0 (
    echo ========================================
    echo   启动失败 (错误码: !EXIT_CODE!)
    echo   请检查依赖或运行日志
    echo ========================================
) else (
    echo ========================================
    echo   程序已退出
    echo ========================================
)

echo.
pause
endlocal
