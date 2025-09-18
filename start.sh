#!/bin/bash
# 快速启动脚本 (Linux/macOS)

echo "==================================="
echo "  抖音通讯录批量关注工具启动脚本"
echo "==================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到Python 3，请先安装Python 3.7+"
    exit 1
fi

# 检查ADB是否安装
if ! command -v adb &> /dev/null; then
    echo "❌ 错误：未找到ADB工具，请先安装Android Platform Tools"
    exit 1
fi

# 检查设备连接
echo "🔍 检查ADB设备连接..."
devices=$(adb devices | grep -c "device$")
if [ $devices -eq 0 ]; then
    echo "❌ 错误：未检测到连接的Android设备"
    echo "请确保："
    echo "1. 手机已通过USB连接"
    echo "2. 已开启USB调试模式"
    echo "3. 已授权ADB调试"
    exit 1
else
    echo "✅ 检测到 $devices 个设备"
fi

# 启动主程序
echo "🚀 启动智能抖音自动化工具..."
python3 smart_douyin_automator.py

echo "👋 程序结束"