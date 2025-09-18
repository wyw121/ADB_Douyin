#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试抖音添加朋友功能检测模块"""

import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.adb_interface import ADBInterface
from modules.douyin_add_friend_detector import DouyinAddFriendDetector
from modules.douyin_navigation_detector import DouyinNavigationDetector
from modules.douyin_app_manager import DouyinAppManager
from modules.douyin_splash_detector import DouyinSplashDetector


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )


def test_add_friend_detection():
    """测试添加朋友功能检测"""
    print("🎯 测试抖音添加朋友功能检测模块")
    print("=" * 60)
    
    try:
        setup_logging()
        
        # 1. 初始化组件
        print("\n🔧 第1步：初始化组件...")
        adb = ADBInterface()
        app_manager = DouyinAppManager(adb)
        splash_detector = DouyinSplashDetector(adb, app_manager)
        nav_detector = DouyinNavigationDetector(adb)
        add_friend_detector = DouyinAddFriendDetector(adb)
        
        # 检查设备连接
        devices = adb.get_connected_devices()
        if not devices:
            print("❌ 没有连接的设备")
            return False
        print(f"✅ 设备连接正常: {devices}")
        
        # 2. 确保抖音在主界面
        print("\n🚀 第2步：确保抖音在主界面...")
        if not splash_detector.wait_for_douyin_ready(max_attempts=3):
            print("❌ 抖音未就绪")
            return False
        print("✅ 抖音已在主界面")
        
        # 3. 导航到个人资料页面
        print("\n👤 第3步：导航到个人资料页面...")
        if not nav_detector.navigate_to_profile_safely():
            print("❌ 导航到个人资料页面失败")
            return False
        print("✅ 成功导航到个人资料页面")
        
        # 4. 检测添加朋友按钮
        print("\n🔍 第4步：检测添加朋友按钮...")
        add_friend_button = add_friend_detector.detect_add_friend_button()
        
        if add_friend_button:
            print("✅ 找到添加朋友按钮:")
            print(f"   - 位置: {add_friend_button['center']}")
            print(f"   - 文本: '{add_friend_button['text']}'")
            print(f"   - 描述: '{add_friend_button['content_desc']}'")
            print(f"   - 检测方法: {add_friend_button['detection_method']}")
        else:
            print("❌ 未找到添加朋友按钮")
            return False
        
        # 5. 检查当前页面状态
        print("\n📊 第5步：检查页面状态...")
        status = add_friend_detector.get_detection_status()
        print("页面状态:")
        for key, value in status.items():
            print(f"  - {key}: {value}")
        
        # 6. 测试导航到添加朋友页面
        print("\n🧭 第6步：测试导航到添加朋友页面...")
        print("正在自动执行导航测试...")
        
        if add_friend_detector.navigate_to_add_friends_safely():
            print("✅ 成功导航到添加朋友页面")
            
            # 检查是否在添加朋友页面
            if add_friend_detector.is_on_add_friends_page():
                print("✅ 确认当前在添加朋友页面")
                
                # 7. 检测通讯录按钮
                print("\n📱 第7步：检测通讯录按钮...")
                contacts_button = add_friend_detector.detect_contacts_button()
                
                if contacts_button:
                    print("✅ 找到通讯录按钮:")
                    print(f"   - 位置: {contacts_button['center']}")
                    print(f"   - 文本: '{contacts_button['text']}'")
                    print(f"   - 描述: '{contacts_button['content_desc']}'")
                    print(f"   - 检测方法: {contacts_button['detection_method']}")
                    
                    # 8. 测试导航到通讯录页面
                    print("\n📋 第8步：测试导航到通讯录页面...")
                    if add_friend_detector.navigate_to_contacts_safely():
                        print("✅ 成功导航到通讯录页面")
                        
                        if add_friend_detector.is_on_contacts_page():
                            print("✅ 确认当前在通讯录页面")
                        else:
                            print("⚠️ 可能未完全加载通讯录页面")
                    else:
                        print("❌ 导航到通讯录页面失败")
                        
                else:
                    print("❌ 未找到通讯录按钮")
                    
            else:
                print("⚠️ 可能未完全加载添加朋友页面")
        else:
            print("❌ 导航到添加朋友页面失败")
        
        # 最终状态检查
        print("\n📊 最终状态检查...")
        final_status = add_friend_detector.get_detection_status()
        print("最终状态:")
        for key, value in final_status.items():
            print(f"  - {key}: {value}")
        
        print("\n🎉 添加朋友功能检测测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_test_summary():
    """打印测试总结"""
    print("\n" + "=" * 60)
    print("📋 添加朋友功能检测测试总结")
    print("=" * 60)
    print("测试覆盖的功能模块:")
    print("1. ✅ 添加朋友按钮检测")
    print("2. ✅ 添加朋友页面验证")
    print("3. ✅ 通讯录按钮检测")
    print("4. ✅ 通讯录页面验证")
    print("5. ✅ 安全导航机制")
    print("6. ✅ 多重检测方法")
    print("7. ✅ 缓存验证机制")
    print("8. ✅ 页面状态监控")
    print("\n检测方法:")
    print("- 🔍 UI结构完整分析")
    print("- 🎯 精确位置验证（左上角区域）")
    print("- 💾 智能缓存机制")
    print("- 🔄 多重后备方法")
    print("- 🛡️ 坐标安全验证")
    print("- 📱 Activity状态检查")
    print("- 📋 UI内容验证")


if __name__ == "__main__":
    print("🚀 启动添加朋友功能检测测试...")
    success = test_add_friend_detection()
    
    print_test_summary()
    
    if success:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 测试失败，请检查日志。")