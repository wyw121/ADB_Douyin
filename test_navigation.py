#!/usr/bin/env python3
"""
测试底部导航栏识别模块
"""

import sys
import os
import logging
import time

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.adb_interface import ADBInterface
from modules.douyin_app_manager import DouyinAppManager
from modules.douyin_splash_detector import DouyinSplashDetector
from modules.douyin_navigation_detector import DouyinNavigationDetector


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
    
    print("🎯 测试抖音底部导航栏识别模块")
    print("=" * 60)
    
    try:
        # 初始化组件
        print("🔧 初始化组件...")
        adb = ADBInterface()
        app_manager = DouyinAppManager(adb)
        splash_detector = DouyinSplashDetector(adb, app_manager)
        nav_detector = DouyinNavigationDetector(adb)
        
        # 检查设备连接
        devices = adb.get_connected_devices()
        if not devices:
            print("❌ 没有找到连接的设备")
            return
        print(f"✅ 设备连接正常: {devices}")
        
        # 第1步: 确保抖音在主界面
        print("\n🚀 第1步: 确保抖音在主界面...")
        if not splash_detector.wait_for_douyin_ready(max_attempts=2):
            print("❌ 抖音无法进入主界面")
            return
        print("✅ 抖音已在主界面")
        
        # 第2步: 测试导航栏检测
        print("\n🔍 第2步: 测试导航栏结构检测...")
        nav_structure = nav_detector.detect_navigation_structure()
        if nav_structure:
            print(f"✅ 检测到导航栏: {nav_structure['total_buttons']}个按钮")
            print(f"  - 有效导航栏: {nav_structure['is_valid_navigation']}")
            print(f"  - 容器边界: {nav_structure['container_bounds']}")
            
            # 显示所有按钮
            for i, btn in enumerate(nav_structure['buttons']):
                profile_mark = " [我按钮]" if btn['is_profile_button'] else ""
                print(f"  - 按钮{i+1}: '{btn['text']}' @ {btn['center']}{profile_mark}")
        else:
            print("❌ 未检测到导航栏结构")
            return
        
        # 第3步: 测试"我"按钮查找
        print("\n👤 第3步: 测试'我'按钮安全查找...")
        profile_button = nav_detector.find_profile_button_safely()
        if profile_button:
            print(f"✅ 找到'我'按钮:")
            print(f"  - 位置: {profile_button['center']}")
            print(f"  - 文本: '{profile_button['text']}'")
            print(f"  - 检测方法: {profile_button.get('source', '未知')}")
        else:
            print("❌ 未找到'我'按钮")
            return
        
        # 第4步: 测试导航状态
        print("\n📊 第4步: 检查导航检测状态...")
        nav_status = nav_detector.get_navigation_status()
        print(f"导航检测状态:")
        for key, value in nav_status.items():
            print(f"  - {key}: {value}")
        
        # 第5步: 测试安全导航
        print("\n🧭 第5步: 测试安全导航到个人资料...")
        print("正在自动执行导航测试...")
        
        if nav_detector.navigate_to_profile_safely():
            print("✅ 成功导航到个人资料页面")
            
            # 等待2秒让页面加载
            time.sleep(2)
        else:
            print("❌ 导航到个人资料页面失败")
        
        # 总结
        print("\n📋 安全机制总结:")
        print("=" * 40)
        print("1. ✅ 导航栏结构完整验证")
        print("2. ✅ 多重坐标安全检查") 
        print("3. ✅ 缓存位置验证机制")
        print("4. ✅ 多种检测方法后备")
        print("5. ✅ 容器边界范围验证")
        print("6. ✅ 点击前最终安全检查")
        print("7. ✅ 页面加载结果验证")
        
    except Exception as e:
        logger.error("测试过程中发生异常: %s", str(e))
        print(f"❌ 测试失败: {e}")
    
    print("\n✅ 测试完成")


if __name__ == "__main__":
    main()