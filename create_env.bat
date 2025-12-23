@echo off
REM ========================================
REM  手动创建 HEAC 0.2 Conda 环境
REM ========================================

echo.
echo ========================================
echo   创建 HEAC 0.2 Conda 环境
echo ========================================
echo.

echo [步骤 1/5] 创建基础环境 (Python 3.11)...
call conda create -n heac-0.2 python=3.11 -y
if errorlevel 1 (
    echo.
    echo 错误: 创建基础环境失败
    pause
    exit /b 1
)

echo.
echo [步骤 2/5] 激活环境...
call conda activate heac-0.2
if errorlevel 1 (
    echo.
    echo 错误: 激活环境失败
    pause
    exit /b 1
)

echo.
echo [步骤 3/5] 安装 Conda 包 (科学计算和ML库)...
echo 这可能需要几分钟，请耐心等待...
call conda install -c conda-forge numpy pandas scipy matplotlib seaborn plotly scikit-learn xgboost lightgbm joblib -y
if errorlevel 1 (
    echo.
    echo 错误: 安装 Conda 包失败
    pause
    exit /b 1
)

echo.
echo [步骤 4/5] 安装 Pip 包 (材料科学和Web应用)...
echo 这可能需要几分钟，请耐心等待...
call pip install pymatgen mp-api emmet-core matminer streamlit catboost optuna shap python-dotenv
if errorlevel 1 (
    echo.
    echo 错误: 安装 Pip 包失败
    pause
    exit /b 1
)

echo.
echo [步骤 5/5] 验证安装...
python -c "import numpy, pandas, pymatgen, streamlit, sklearn; print('✓ 环境创建成功！')"
if errorlevel 1 (
    echo.
    echo 警告: 验证失败，可能有包未正确安装
    pause
    exit /b 1
)

echo.
echo ========================================
echo   环境创建完成！
echo ========================================
echo.
echo Streamlit 版本信息:
call streamlit --version
echo.
echo 现在可以使用 start.bat 启动应用了！
echo.
pause
