@echo off
chcp 65001 >nul
echo 正在启动 VibeWatermark ...
call "%~dp0.venv\Scripts\activate.bat"
python "%~dp0main.py"
if errorlevel 1 (
    echo.
    echo 启动失败，请确保已安装依赖: .venv\Scripts\pip install -r requirements.txt
    pause
)
