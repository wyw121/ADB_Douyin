#!/usr/bin/env python3
"""
测试抖音应用管理和启动画面检测模块
"""

import sys
import os
import logging

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.adb_interface import ADBInterface
from modules.douyin_app_manager import DouyinAppManager
from modules.douyin_splash_detector import DouyinSplashDetector


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )


def main():
    """主测试函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🎯 测试抖音应用管理和启动画面检测模块")
    print("=" * 60)
    
    try:
        # 初始化组件
        print("\n🔧 初始化组件...")
        adb = ADBInterface()
        app_manager = DouyinAppManager(adb)
        splash_detector = DouyinSplashDetector(adb, app_manager)
        
        # 检查ADB连接
        devices = adb.get_connected_devices()
        if not devices:
            print("❌ 没有找到连接的设备")
            return
        print(f"✅ 设备连接正常: {devices}")
        
        # 测试应用管理功能
        print("\n📱 测试应用管理功能...")
        
        # 获取当前状态
        app_status = app_manager.get_app_status_info()
        print(f"应用运行状态: {app_status}")
        
        # 测试启动画面检测功能
        print("\n🚀 测试启动画面检测功能...")
        
        splash_status = splash_detector.get_splash_status_info()
        print(f"启动画面状态: {splash_status}")
        
        # 如果抖音正在运行，显示当前状态
        if app_status['is_running']:
            print(f"\n📊 抖音当前状态:")
            print(f"  - Activity: {app_status['current_activity']}")
            print(f"  - PID: {app_status['pid']}")
            print(f"  - 是否在启动画面: {splash_status['is_in_splash']}")
            print(f"  - 主界面就绪: {splash_status['is_main_ready']}")
            print(f"  - UI可用: {splash_status['ui_available']}")
        
        # 演示完整流程
        print("\n🔄 演示完整重启和等待流程...")
        print("正在重启抖音并等待就绪...")
        
        if splash_detector.wait_for_douyin_ready(max_attempts=2):
            print("✅ 抖音已完全就绪!")
            
            # 再次检查状态
            final_status = splash_detector.get_splash_status_info()
            print(f"\n📊 最终状态:")
            print(f"  - 应用运行: {final_status['app_running']}")
            print(f"  - 在启动画面: {final_status['is_in_splash']}")
            print(f"  - 主界面就绪: {final_status['is_main_ready']}")
            print(f"  - UI可用: {final_status['ui_available']}")
            print(f"  - 当前Activity: {final_status['current_activity']}")
        else:
            print("❌ 抖音未能完全就绪")
        
    except Exception as e:
        logger.error("测试过程中发生异常: %s", str(e))
        print(f"❌ 测试失败: {e}")
    
    print("\n✅ 测试完成")


if __name__ == "__main__":
    main()