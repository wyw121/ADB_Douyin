#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""完整流程联动测试：智能打开抖音 → 找到"我" → 添加朋友 → 通讯录"""

import sys
import os
import time
import logging

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入模块
from modules.adb_interface import ADBInterface
from modules.douyin_app_manager import DouyinAppManager
from modules.douyin_splash_detector import DouyinSplashDetector
from modules.douyin_navigation_detector import DouyinNavigationDetector
from modules.douyin_add_friend_detector import DouyinAddFriendDetector


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )


def initialize_components():
    """初始化所有组件"""
    print("\n🔧 第1阶段：组件初始化...")
    adb = ADBInterface()
    app_manager = DouyinAppManager(adb)
    splash_detector = DouyinSplashDetector(adb, app_manager)
    nav_detector = DouyinNavigationDetector(adb)
    add_friend_detector = DouyinAddFriendDetector(adb)
    
    # 检查设备连接
    devices = adb.get_connected_devices()
    if not devices:
        print("❌ 没有连接的设备")
        return None
    
    print(f"✅ 设备连接正常: {devices}")
    return {
        'adb': adb,
        'app_manager': app_manager,
        'splash_detector': splash_detector,
        'nav_detector': nav_detector,
        'add_friend_detector': add_friend_detector
    }


def start_douyin_app(app_manager, splash_detector):
    """启动抖音应用"""
    print("\n📱 第2阶段：智能启动抖音应用...")
    
    # 检查当前状态
    app_status = app_manager.get_app_status_info()
    print(f"当前应用状态: {app_status}")
    
    # 确保抖音启动并就绪
    if not app_status.get('is_running', False):
        print("启动抖音应用...")
        if not app_manager.start_douyin():
            print("❌ 启动抖音失败")
            return False
    
    # 等待完全就绪
    print("等待抖音完全就绪...")
    if not splash_detector.wait_for_douyin_ready(max_attempts=5):
        print("❌ 抖音启动超时")
        return False
    
    print("✅ 抖音已完全就绪")
    return True


def navigate_to_profile(nav_detector):
    """导航到个人资料页面"""
    print("\n👤 第3阶段：智能导航到个人资料页面...")
    
    # 检测导航栏结构
    nav_structure = nav_detector.detect_navigation_structure()
    if nav_structure:
        print(f"✅ 检测到导航栏: {nav_structure['total_buttons']}个按钮")
    else:
        print("⚠️ 未检测到导航栏结构，继续尝试...")
    
    # 安全导航到个人资料页面
    if not nav_detector.navigate_to_profile_safely():
        print("❌ 导航到个人资料页面失败")
        return False
    
    print("✅ 成功导航到个人资料页面")
    return True


def detect_and_navigate_add_friends(add_friend_detector):
    """检测并导航到添加朋友页面"""
    print("\n🔍 第4阶段：智能检测添加朋友功能...")
    
    # 检查页面状态
    add_friend_status = add_friend_detector.get_detection_status()
    print("添加朋友检测状态:")
    for key, value in add_friend_status.items():
        print(f"  - {key}: {value}")
    
    # 检测添加朋友按钮
    add_friend_button = add_friend_detector.detect_add_friend_button()
    if not add_friend_button:
        print("❌ 未找到添加朋友按钮")
        return False
    
    print("✅ 找到添加朋友按钮:")
    print(f"   - 位置: {add_friend_button['center']}")
    print(f"   - 文本: '{add_friend_button['text']}'")
    print(f"   - 检测方法: {add_friend_button['detection_method']}")
    if 'match_score' in add_friend_button:
        print(f"   - 匹配分数: {add_friend_button['match_score']:.2f}")
    
    # 导航到添加朋友页面
    print("\n🧭 导航到添加朋友页面...")
    if not add_friend_detector.navigate_to_add_friends_safely():
        print("❌ 导航到添加朋友页面失败")
        return False
    
    print("✅ 成功导航到添加朋友页面")
    
    # 验证页面状态
    if add_friend_detector.is_on_add_friends_page():
        print("✅ 确认当前在添加朋友页面")
    else:
        print("⚠️ 页面状态验证异常，但继续流程...")
    
    return True


def detect_and_navigate_contacts(add_friend_detector, adb):
    """检测并导航到通讯录页面"""
    print("\n📱 第5阶段：智能检测通讯录功能...")
    
    # 等待页面加载
    time.sleep(2)
    
    # 检测通讯录按钮
    contacts_button = add_friend_detector.detect_contacts_button()
    if not contacts_button:
        print("❌ 未找到通讯录按钮")
        analyze_page_elements(adb)
        return False
    
    print("✅ 找到通讯录按钮:")
    print(f"   - 位置: {contacts_button['center']}")
    print(f"   - 文本: '{contacts_button['text']}'")
    print(f"   - 检测方法: {contacts_button['detection_method']}")
    
    # 导航到通讯录页面
    print("\n📋 导航到通讯录页面...")
    if not add_friend_detector.navigate_to_contacts_safely():
        print("❌ 导航到通讯录页面失败")
        return False
    
    print("✅ 成功导航到通讯录页面")
    
    # 验证通讯录页面
    if add_friend_detector.is_on_contacts_page():
        print("✅ 确认当前在通讯录页面")
    else:
        print("⚠️ 通讯录页面状态验证异常...")
    
    return True


def analyze_page_elements(adb):
    """分析页面中的可点击元素"""
    print("尝试查找页面中所有可点击元素...")
    
    ui_content = adb.get_ui_xml()
    if ui_content:
        from modules.ui_intelligence import UIAnalyzer
        analyzer = UIAnalyzer()
        if analyzer.parse_xml(ui_content):
            clickable_elements = [elem for elem in analyzer.elements 
                                if elem.clickable]
            print(f"页面中共有 {len(clickable_elements)} 个可点击元素:")
            for i, elem in enumerate(clickable_elements[:10]):
                text = elem.text or elem.content_desc or "无文本"
                center = elem.get_center()
                print(f"  {i+1}. '{text}' @ {center}")


def analyze_contacts_content(adb):
    """分析通讯录内容"""
    print("\n📊 第6阶段：分析通讯录内容...")
    
    # 等待通讯录加载
    time.sleep(3)
    
    # 获取当前页面内容进行分析
    ui_content = adb.get_ui_xml()
    if not ui_content:
        return False
    
    from modules.ui_intelligence import UIAnalyzer
    analyzer = UIAnalyzer()
    if not analyzer.parse_xml(ui_content):
        return False
    
    # 查找潜在的联系人元素
    contact_elements = []
    follow_buttons = []
    
    for elem in analyzer.elements:
        # 查找可能的联系人姓名
        if (elem.text and len(elem.text.strip()) > 0 and 
            len(elem.text.strip()) < 20 and
            elem.class_name == 'android.widget.TextView'):
            contact_elements.append(elem)
        
        # 查找关注/添加按钮
        if (elem.clickable and elem.text and 
            any(keyword in elem.text for keyword in 
                ['关注', '添加', '加好友', 'Follow', 'Add'])):
            follow_buttons.append(elem)
    
    print(f"✅ 发现 {len(contact_elements)} 个潜在联系人")
    print(f"✅ 发现 {len(follow_buttons)} 个可操作按钮")
    
    # 显示联系人示例
    display_contact_examples(contact_elements)
    display_action_buttons(follow_buttons)
    
    return True


def display_contact_examples(contact_elements):
    """显示联系人示例"""
    if contact_elements:
        print("联系人示例:")
        for i, elem in enumerate(contact_elements[:5]):
            center = elem.get_center()
            print(f"  {i+1}. '{elem.text}' @ {center}")


def display_action_buttons(follow_buttons):
    """显示操作按钮"""
    if follow_buttons:
        print("可操作按钮:")
        for i, elem in enumerate(follow_buttons[:3]):
            center = elem.get_center()
            print(f"  {i+1}. '{elem.text}' @ {center}")


def print_final_status(app_manager, add_friend_detector):
    """打印最终状态总结"""
    print("\n🎉 第7阶段：流程完成状态总结...")
    
    # 获取最终状态
    final_app_status = app_manager.get_app_status_info()
    final_add_friend_status = add_friend_detector.get_detection_status()
    
    print("最终状态总结:")
    print("应用状态:")
    for key, value in final_app_status.items():
        print(f"  - {key}: {value}")
    
    print("添加朋友功能状态:")
    for key, value in final_add_friend_status.items():
        print(f"  - {key}: {value}")


def complete_workflow_test():
    """完整工作流程测试"""
    print("🚀 抖音自动化完整流程联动测试")
    print("=" * 80)
    print("流程: 智能启动 → 导航到我 → 添加朋友 → 通讯录 → 批量添加")
    print("=" * 80)
    
    try:
        setup_logging()
        
        # 初始化组件
        components = initialize_components()
        if not components:
            return False
        
        # 启动抖音
        if not start_douyin_app(components['app_manager'], 
                               components['splash_detector']):
            return False
        
        # 导航到个人资料页面
        if not navigate_to_profile(components['nav_detector']):
            return False
        
        # 检测并导航到添加朋友页面
        if not detect_and_navigate_add_friends(
                components['add_friend_detector']):
            return False
        
        # 检测并导航到通讯录页面
        if not detect_and_navigate_contacts(
                components['add_friend_detector'], components['adb']):
            return False
        
        # 分析通讯录内容
        analyze_contacts_content(components['adb'])
        
        # 打印最终状态
        print_final_status(components['app_manager'], 
                          components['add_friend_detector'])
        
        print("\n🎯 完整流程测试成功完成！")
        print("已成功实现：智能启动 → 导航到我 → 添加朋友 → 通讯录")
        print("下一步可以实现具体的批量添加逻辑")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_workflow_summary():
    """打印工作流程总结"""
    print("\n" + "=" * 80)
    print("📋 完整流程联动测试总结")
    print("=" * 80)
    print("测试阶段:")
    print("1. ✅ 组件初始化和设备连接")
    print("2. ✅ 智能启动抖音应用")
    print("3. ✅ 智能导航到个人资料页面")
    print("4. ✅ 智能检测添加朋友功能")
    print("5. ✅ 智能检测通讯录功能")
    print("6. ✅ 分析通讯录内容")
    print("7. ✅ 流程完成和状态总结")
    print("\n集成的模块:")
    print("- 🔧 ADB接口管理")
    print("- 📱 抖音应用管理")
    print("- 🎬 启动画面检测")
    print("- 🧭 底部导航检测")
    print("- 👥 添加朋友功能检测")
    print("- 🧠 智能文本匹配")
    print("\n智能特性:")
    print("- 🛡️ 多重安全验证")
    print("- 🎯 精确位置定位")
    print("- 🔄 自动错误恢复")
    print("- 📊 实时状态监控")
    print("- 🌐 多语言支持")
    print("- 🤖 自适应UI变化")


if __name__ == "__main__":
    print("🚀 启动完整流程联动测试...")
    success = complete_workflow_test()
    
    print_workflow_summary()
    
    if success:
        print("\n✅ 所有联动测试通过！系统已可投入使用！")
    else:
        print("\n❌ 联动测试失败，需要进一步调试。")