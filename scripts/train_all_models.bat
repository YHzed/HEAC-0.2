@echo off
REM 批量训练所有辅助模型
REM 依次执行，防止错误传播

echo ===============================================================================
echo                    辅助模型批量训练脚本
echo ===============================================================================
echo.
echo 此脚本将依次训练5个辅助模型，每个模型独立保存
echo.
echo 模型列表:
echo   1. 形成能预测器
echo   2. 晶格常数预测器
echo   3. 磁矩预测器
echo   4. 弹性模量预测器（模拟数据）
echo   5. 脆性指数预测器（模拟数据）
echo.
echo ===============================================================================
echo.

set PYTHON=python
set START_TIME=%TIME%

echo [%TIME%] 开始训练...
echo.

REM 训练模型A
echo -------------------------------------------------------------------------------
echo [模型 1/5] 训练形成能预测器...
echo -------------------------------------------------------------------------------
%PYTHON% scripts/train_model_a_formation.py
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 模型A训练失败，错误代码: %ERRORLEVEL%
    set MODEL_A_STATUS=失败
) else (
    echo [成功] 模型A训练完成
    set MODEL_A_STATUS=成功
)
echo.

REM 训练模型B
echo -------------------------------------------------------------------------------
echo [模型 2/5] 训练晶格常数预测器...
echo -------------------------------------------------------------------------------
%PYTHON% scripts/train_model_b_lattice.py
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 模型B训练失败，错误代码: %ERRORLEVEL%
    set MODEL_B_STATUS=失败
) else (
    echo [成功] 模型B训练完成
    set MODEL_B_STATUS=成功
)
echo.

REM 训练模型C
echo -------------------------------------------------------------------------------
echo [模型 3/5] 训练磁矩预测器...
echo -------------------------------------------------------------------------------
%PYTHON% scripts/train_model_c_magnetic.py
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 模型C训练失败，错误代码: %ERRORLEVEL%
    set MODEL_C_STATUS=失败
) else (
    echo [成功] 模型C训练完成
    set MODEL_C_STATUS=成功
)
echo.

REM 训练模型D
echo -------------------------------------------------------------------------------
echo [模型 4/5] 训练弹性模量预测器...
echo -------------------------------------------------------------------------------
%PYTHON% scripts/train_model_d_elastic.py
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 模型D训练失败，错误代码: %ERRORLEVEL%
    set MODEL_D_STATUS=失败
) else (
    echo [成功] 模型D训练完成
    set MODEL_D_STATUS=成功
)
echo.

REM 训练模型E
echo -------------------------------------------------------------------------------
echo [模型 5/5] 训练脆性指数预测器...
echo -------------------------------------------------------------------------------
%PYTHON% scripts/train_model_e_brittleness.py
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 模型E训练失败，错误代码: %ERRORLEVEL%
    set MODEL_E_STATUS=失败
) else (
    echo [成功] 模型E训练完成
    set MODEL_E_STATUS=成功
)
echo.

set END_TIME=%TIME%

REM 显示总结
echo ===============================================================================
echo                          训练总结
echo ===============================================================================
echo.
echo 模型A (形成能):        %MODEL_A_STATUS%
echo 模型B (晶格常数):      %MODEL_B_STATUS%
echo 模型C (磁矩):          %MODEL_C_STATUS%
echo 模型D (弹性模量):      %MODEL_D_STATUS%
echo 模型E (脆性指数):      %MODEL_E_STATUS%
echo.
echo 开始时间: %START_TIME%
echo 结束时间: %END_TIME%
echo.
echo 查看模型状态: python scripts/check_proxy_models.py
echo ===============================================================================
echo.

pause
