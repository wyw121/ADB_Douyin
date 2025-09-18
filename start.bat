@echo off
chcp 65001 >nul
:: 快速启动脚本 (Windows)

echo ===================================
echo   抖音通讯录批量关注工具启动脚本
echo ===================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

:: 检查ADB是否安装
adb version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到ADB工具，请先安装Android Platform Tools
    echo 请将adb.exe添加到系统PATH或复制到当前目录
    pause
    exit /b 1
)

:: 检查设备连接
echo 🔍 检查ADB设备连接...
for /f "tokens=*" %%i in ('adb devices ^| find /c "device"') do set device_count=%%i
if %device_count% lss 2 (
    echo ❌ 错误：未检测到连接的Android设备
    echo 请确保：
    echo 1. 手机已通过USB连接
    echo 2. 已开启USB调试模式
    echo 3. 已授权ADB调试
    pause
    exit /b 1
) else (
    echo ✅ 检测到设备连接
)

:: 启动主程序
echo 🚀 启动抖音自动化工具...
echo.
python main.py

echo.
echo 👋 程序结束
pause