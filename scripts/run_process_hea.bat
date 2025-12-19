@echo off
REM HEA.xlsx 数据处理 - 快速执行脚本
REM 使用方法：双击此文件或在命令行运行

echo ========================================
echo HEA.xlsx 数据处理脚本
echo ========================================
echo.

cd /d "%~dp0"
cd ..

echo 当前目录: %CD%
echo.

echo 开始处理数据...
python scripts\process_hea_xlsx.py

echo.
echo 按任意键退出...
pause > nul
