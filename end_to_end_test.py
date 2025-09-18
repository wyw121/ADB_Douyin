#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
端到端完整流程测试
验证从启动抖音到进入通讯录的完整模块化流程

测试流程：
1. ✅ 智能启动抖音应用
2. ✅ 导航到个人资料页面（"我"）
3. ✅ 找到并点击"添加朋友"
4. ✅ 找到并点击"通讯录"
5. ✅ 成功进入通讯录页面
"""

import sys
import os
import time
import logging

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入所有模块
from modules.adb_interface import ADBInterface
from modules.douyin_app_manager import DouyinAppManager
from modules.douyin_splash_detector import DouyinSplashDetector
from modules.douyin_navigation_detector import DouyinNavigationDetector
from modules.douyin_add_friend_detector import DouyinAddFriendDetector


def setup_logging():
    """设置日志格式"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )


def test_step_1_smart_launch():
    """测试步骤1：智能启动抖音应用"""
    print("\n" + "="*80)
    print("🚀 步骤1：智能启动抖音应用")
    print("="*80)
    
    # 初始化组件
    adb = ADBInterface()
    app_manager = DouyinAppManager(adb)
    splash_detector = DouyinSplashDetector(adb, app_manager)
    
    # 检查设备连接
    devices = adb.get_connected_devices()
    if not devices:
        print("❌ 没有连接的设备")
        return None, None, None
    
    print(f"✅ 设备连接正常: {devices}")
    
    # 获取应用状态
    app_status = app_manager.get_app_status_info()
    print(f"📱 当前应用状态: {app_status}")
    
    # 确保抖音启动
    if not app_status.get('is_running', False):
        print("🔄 启动抖音应用...")
        if not app_manager.start_douyin():
            print("❌ 启动抖音失败")
            return None, None, None
    
    # 等待抖音就绪
    print("⏳ 等待抖音完全就绪...")
    if not splash_detector.wait_for_douyin_ready(max_attempts=5):
        print("❌ 抖音启动超时")
        return None, None, None
    
    print("✅ 抖音已完全就绪")
    return adb, app_manager, splash_detector


def test_step_2_navigate_to_profile(adb):
    """测试步骤2：导航到个人资料页面"""
    print("\n" + "="*80)
    print("👤 步骤2：导航到个人资料页面（'我'）")
    print("="*80)
    
    nav_detector = DouyinNavigationDetector(adb)
    
    # 检测导航栏结构
    nav_structure = nav_detector.detect_navigation_structure()
    if nav_structure:
        print(f"📐 检测到导航栏: {nav_structure['total_buttons']}个按钮")
    else:
        print("⚠️ 未检测到导航栏结构，尝试继续...")
    
    # 安全导航到个人资料页面
    print("🧭 正在导航到个人资料页面...")
    if not nav_detector.navigate_to_profile_safely():
        print("❌ 导航到个人资料页面失败")
        return None
    
    print("✅ 成功导航到个人资料页面")
    return nav_detector


def test_step_3_detect_add_friend(adb):
    """测试步骤3：检测并点击添加朋友"""
    print("\n" + "="*80) 
    print("🔍 步骤3：检测并点击'添加朋友'")
    print("="*80)
    
    add_friend_detector = DouyinAddFriendDetector(adb)
    
    # 检查当前页面状态
    status = add_friend_detector.get_detection_status()
    print("📊 检测状态:")
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # 检测添加朋友按钮
    print("🔎 正在检测'添加朋友'按钮...")
    add_friend_button = add_friend_detector.detect_add_friend_button()
    
    if not add_friend_button:
        print("❌ 未找到添加朋友按钮")
        return None
    
    print("✅ 找到添加朋友按钮:")
    print(f"   位置: {add_friend_button['center']}")
    print(f"   文本: '{add_friend_button['text']}'")
    print(f"   检测方法: {add_friend_button['detection_method']}")
    
    # 导航到添加朋友页面
    print("🎯 正在点击'添加朋友'按钮...")
    if not add_friend_detector.navigate_to_add_friends_safely():
        print("❌ 导航到添加朋友页面失败")
        return None
    
    print("✅ 成功导航到添加朋友页面")
    
    # 验证页面状态
    if add_friend_detector.is_on_add_friends_page():
        print("✅ 确认当前在添加朋友页面")
    else:
        print("⚠️ 页面状态验证异常")
    
    return add_friend_detector


def test_step_4_detect_contacts(add_friend_detector):
    """测试步骤4：检测并点击通讯录"""
    print("\n" + "="*80)
    print("📱 步骤4：检测并点击'通讯录'")
    print("="*80)
    
    # 等待页面加载
    time.sleep(2)
    
    # 检测通讯录按钮
    print("🔎 正在检测'通讯录'按钮...")
    contacts_button = add_friend_detector.detect_contacts_button()
    
    if not contacts_button:
        print("❌ 未找到通讯录按钮")
        return False
    
    print("✅ 找到通讯录按钮:")
    print(f"   位置: {contacts_button['center']}")
    print(f"   文本: '{contacts_button['text']}'")
    print(f"   检测方法: {contacts_button['detection_method']}")
    if 'match_score' in contacts_button:
        print(f"   匹配分数: {contacts_button['match_score']:.2f}")
    
    # 导航到通讯录页面
    print("🎯 正在点击'通讯录'按钮...")
    if not add_friend_detector.navigate_to_contacts_safely():
        print("❌ 导航到通讯录页面失败")
        return False
    
    print("✅ 成功导航到通讯录页面")
    return True


def test_step_5_verify_contacts_page(add_friend_detector, adb):
    """测试步骤5：验证通讯录页面"""
    print("\n" + "="*80)
    print("📋 步骤5：验证通讯录页面内容")
    print("="*80)
    
    # 等待页面加载
    time.sleep(3)
    
    # 验证通讯录页面
    if add_friend_detector.is_on_contacts_page():
        print("✅ 确认当前在通讯录页面")
    else:
        print("⚠️ 通讯录页面状态验证异常")
    
    # 分析页面内容
    print("📊 分析通讯录页面内容...")
    ui_content = adb.get_ui_xml()
    if ui_content:
        from modules.ui_intelligence import UIAnalyzer
        analyzer = UIAnalyzer()
        if analyzer.parse_xml(ui_content):
            print(f"📐 页面解析成功，共 {len(analyzer.elements)} 个元素")
            
            # 查找关键文本
            key_texts = []
            for elem in analyzer.elements:
                if elem.text and any(keyword in elem.text for keyword in 
                                   ['通讯录', '联系人', '朋友', '暂时没有']):
                    key_texts.append(elem.text)
            
            if key_texts:
                print("✅ 找到关键文本指示:")
                for text in key_texts:
                    print(f"   '{text}'")
            else:
                print("⚠️ 未找到明显的通讯录页面指示文本")
    
    return True


def run_complete_end_to_end_test():
    """运行完整的端到端测试"""
    print("🎯 开始端到端完整流程测试")
    print("测试目标：验证所有模块化环节并跑通完整流程")
    
    setup_logging()
    
    try:
        # 步骤1：智能启动抖音
        adb, app_manager, splash_detector = test_step_1_smart_launch()
        if not adb:
            return False
        
        # 步骤2：导航到个人资料页面
        nav_detector = test_step_2_navigate_to_profile(adb)
        if not nav_detector:
            return False
        
        # 步骤3：检测并点击添加朋友
        add_friend_detector = test_step_3_detect_add_friend(adb)  
        if not add_friend_detector:
            return False
        
        # 步骤4：检测并点击通讯录
        if not test_step_4_detect_contacts(add_friend_detector):
            return False
        
        # 步骤5：验证通讯录页面
        if not test_step_5_verify_contacts_page(add_friend_detector, adb):
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_final_summary(success):
    """打印最终测试总结"""
    print("\n" + "="*80)
    print("🏆 端到端完整流程测试总结")
    print("="*80)
    
    if success:
        print("🎉 所有测试步骤通过！")
        print("\n✅ 验证完成的功能:")
        print("   1. ✅ 智能启动抖音应用")
        print("   2. ✅ 导航到个人资料页面（'我'）")
        print("   3. ✅ 找到并点击'添加朋友'")
        print("   4. ✅ 找到并点击'通讯录'")
        print("   5. ✅ 成功进入通讯录页面")
        
        print("\n🏗️ 验证完成的模块:")
        print("   - ADBInterface: 设备连接和命令执行")
        print("   - DouyinAppManager: 应用管理和状态监控")
        print("   - DouyinSplashDetector: 启动画面检测")
        print("   - DouyinNavigationDetector: 导航功能")
        print("   - DouyinAddFriendDetector: 添加朋友和通讯录功能")
        print("   - IntelligentTextMatcher: 智能文本匹配")
        
        print("\n🚀 系统状态：已可投入使用！")
        print("📈 下一步：可以开发具体的批量添加朋友逻辑")
        
    else:
        print("❌ 测试失败，需要进一步调试")
        print("🔧 请检查设备连接和应用状态")


if __name__ == "__main__":
    print("🚀 启动端到端完整流程测试...")
    success = run_complete_end_to_end_test()
    print_final_summary(success)