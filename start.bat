@echo off
echo ========================================
echo    启动 HEAC 0.2 应用
echo ========================================
echo.

echo [1/3] 激活 conda 环境...
call conda activate heac-0.2
if errorlevel 1 (
    echo 错误: 无法激活 heac-0.2 环境
    echo 请确保已运行: conda env create -f environment.yml
    pause
    exit /b 1
)

echo [2/3] 切换到项目目录...
cd /d "d:\ML\HEAC 0.2"

echo [3/3] 启动 Streamlit 应用...
echo.
echo 应用将在浏览器中打开: http://localhost:8501
echo 按 Ctrl+C 停止应用
echo.
streamlit run app.py

pause
