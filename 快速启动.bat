@echo off
chcp 65001 >nul
echo ===========================================
echo 冰川数据查询与预测系统 - 快速启动
echo ===========================================
echo.

cd /d E:\AIcode\ruanzhu

echo [1/2] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python或激活conda环境
    pause
    exit /b 1
)

echo.
echo [2/2] 启动Flask后端服务器...
echo.
echo 服务器启动后，您可以通过以下地址访问：
echo   - 本地访问: http://localhost:5000
echo   - 局域网访问: http://[本机IP]:5000
echo.
echo 按 Ctrl+C 停止服务器
echo.

conda activate ruanzhu
python app.py

pause

