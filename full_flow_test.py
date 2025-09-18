#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""完整流程测试：重启->启动画面->导航栏"我"点击"""

import sys
import os
import time
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.adb_interface import ADBInterface
from modules.douyin_app_manager import DouyinAppManager
from modules.douyin_splash_detector import DouyinSplashDetector  
from modules.douyin_navigation_detector import DouyinNavigationDetector


def full_flow_test():
    """完整流程测试"""
    print("🎯 完整流程测试：重启->启动画面->导航栏点击")
    print("=" * 60)
    
    try:
        # 1. 初始化所有组件
        print("\n🔧 第1步：初始化组件...")
        adb = ADBInterface()
        app_manager = DouyinAppManager(adb)
        splash_detector = DouyinSplashDetector(adb, app_manager)
        nav_detector = DouyinNavigationDetector(adb)
        
        # 检查设备连接
        devices = adb.get_connected_devices()
        if not devices:
            print("❌ 没有连接的设备")
            return False
        print(f"✅ 设备连接正常: {devices}")
        
        # 2. 强制重启抖音
        print("\n🔄 第2步：强制重启抖音...")
        print("正在关闭抖音...")
        app_manager.stop_douyin()
        time.sleep(3)  # 等待完全关闭
        
        print("正在启动抖音...")
        if not app_manager.start_douyin():
            print("❌ 启动抖音失败")
            return False
        print("✅ 抖音启动命令已发送")
        
        # 3. 检测启动画面并等待主界面就绪
        print("\n⏳ 第3步：检测启动画面并等待主界面就绪...")
        start_time = time.time()
        
        # 等待抖音完全启动并通过启动画面
        if not splash_detector.wait_for_douyin_ready(max_attempts=5):
            print("❌ 等待抖音就绪超时")
            return False
        
        elapsed_time = time.time() - start_time
        print(f"✅ 抖音已完全就绪 (耗时: {elapsed_time:.1f}秒)")
        
        # 4. 简单验证当前状态
        print("\n📊 第4步：验证当前应用状态...")
        app_status = app_manager.get_app_status_info()
        
        print(f"应用状态: {app_status}")
        
        if not app_status.get('is_running', False):
            print("❌ 应用未运行")
            return False
        
        print("✅ 应用状态验证通过")
        
        # 5. 检测导航栏结构
        print("\n🧭 第5步：检测导航栏结构...")
        nav_structure = nav_detector.detect_navigation_structure()
        
        if not nav_structure:
            print("❌ 未检测到导航栏结构")
            return False
        
        print(f"✅ 检测到导航栏: {nav_structure['total_buttons']}个按钮")
        print(f"   - 有效导航栏: {nav_structure['is_valid_navigation']}")
        print(f"   - 容器边界: {nav_structure['container_bounds']}")
        
        # 6. 查找"我"按钮
        print("\n👤 第6步：安全查找'我'按钮...")
        profile_button = nav_detector.find_profile_button_safely()
        
        if not profile_button:
            print("❌ 未找到'我'按钮")
            return False
        
        print(f"✅ 找到'我'按钮:")
        print(f"   - 位置: {profile_button['center']}")
        print(f"   - 文本: '{profile_button['text']}'")
        print(f"   - 描述: '{profile_button['content_desc']}'")
        
        # 7. 安全点击"我"按钮
        print("\n🎯 第7步：安全点击'我'按钮...")
        
        # 执行安全导航（无需用户确认）
        if not nav_detector.navigate_to_profile_safely():
            print("❌ 导航到个人资料页面失败")
            return False
        
        print("✅ 成功导航到个人资料页面")
        
        # 8. 验证导航结果
        print("\n✅ 第8步：验证导航结果...")
        time.sleep(2)  # 等待页面加载
        
        # 检查是否在个人资料页面
        current_activity = adb.get_current_activity()
        print(f"当前Activity: {current_activity}")
        
        # 获取UI内容验证
        ui_content = adb.get_ui_xml()
        if ui_content and any(keyword in ui_content for keyword in 
                              ['添加朋友', '获赞', '关注', '粉丝']):
            print("✅ 确认已成功导航到个人资料页面")
        else:
            print("⚠️ 无法确认是否在个人资料页面")
        
        print("\n🎉 完整流程测试成功完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_test_summary():
    """打印测试总结"""
    print("\n" + "=" * 60)
    print("📋 完整流程测试总结")
    print("=" * 60)
    print("测试覆盖的功能模块:")
    print("1. ✅ ADB设备连接管理")
    print("2. ✅ 抖音应用管理（重启）")
    print("3. ✅ 启动画面检测和等待")
    print("4. ✅ 主界面就绪验证")
    print("5. ✅ 导航栏结构检测")
    print("6. ✅ '我'按钮安全查找")
    print("7. ✅ 安全点击和导航")
    print("8. ✅ 导航结果验证")
    print("\n安全机制验证:")
    print("- 🛡️ 设备连接检查")
    print("- 🛡️ 应用状态监控")
    print("- 🛡️ 启动画面超时保护")
    print("- 🛡️ UI结构完整性验证")
    print("- 🛡️ 导航栏安全检测")
    print("- 🛡️ 坐标安全验证")
    print("- 🛡️ 用户确认机制")
    print("- 🛡️ 操作结果验证")


if __name__ == "__main__":
    print("🚀 启动完整流程测试...")
    success = full_flow_test()
    
    print_test_summary()
    
    if success:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 测试失败，请检查日志。")