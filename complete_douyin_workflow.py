#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整流程自动化脚本
从关闭抖音开始，到成功导入通讯录的完整流程

流程步骤：
1. 关闭抖音应用
2. 启动抖音应用
3. 等待启动完成
4. 导航到个人资料页面（"我"）
5. 点击"添加朋友"
6. 点击"通讯录"
7. 成功进入通讯录页面
8. 可选：导入通讯录联系人

每个步骤都会输出详细的XML日志和关键信息
"""

import sys
import os
import time
import logging

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入所有需要的模块
from modules.adb_interface import ADBInterface
from modules.douyin_app_manager import DouyinAppManager
from modules.douyin_splash_detector import DouyinSplashDetector
from modules.douyin_navigation_detector import DouyinNavigationDetector
from modules.douyin_add_friend_detector import DouyinAddFriendDetector
from modules.ui_context_analyzer import UIContextAnalyzer


def setup_logging():
    """设置日志格式"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )


def print_step_header(step_num: int, title: str, description: str):
    """打印步骤标题"""
    print(f"\n{'='*80}")
    print(f"🚀 步骤{step_num}：{title}")
    print(f"📋 {description}")
    print(f"{'='*80}")


def analyze_current_ui_context(adb: ADBInterface,
                               context_analyzer: UIContextAnalyzer,
                               step_name: str) -> bool:
    """分析当前UI上下文并输出详细信息"""
    print(f"\n📊 {step_name} - UI上下文分析")
    print("=" * 60)
    
    try:
        # 尝试获取XML内容
        xml_content = adb.get_ui_xml()
        
        if xml_content:
            print(f"✅ 成功获取UI XML (长度: {len(xml_content)} 字符)")
            
            # 显示XML预览（前500字符，更详细）
            if len(xml_content) > 500:
                xml_preview = xml_content[:500] + "..."
            else:
                xml_preview = xml_content
            
            print(f"\n🔬 XML内容预览:")
            print("-" * 60)
            print(xml_preview)
            print("-" * 60)
            
            # 提取关键信息显示
            import re
            
            # 提取应用包名
            package_matches = re.findall(r'package="([^"]+)"', xml_content)
            if package_matches:
                unique_packages = list(set(package_matches))
                print(f"\n� 检测到的应用包: {', '.join(unique_packages[:5])}")
            
            # 提取文本内容
            text_matches = re.findall(r'text="([^"]+)"', xml_content)
            if text_matches:
                non_empty_texts = [t for t in text_matches if t.strip()]
                print(f"\n📝 界面文本内容: {', '.join(non_empty_texts[:10])}")
            
            # 分析UI上下文
            context = context_analyzer.analyze_current_context(xml_content)
            context_analyzer.print_context_info(context, f"{step_name}")
            
            # 检查是否需要重启应用
            if context_analyzer.should_restart_app(context):
                print("⚠️ UI分析建议重启应用")
                return False
            
            return context['is_valid_page']
        else:
            print("❌ 无法获取UI XML内容")
            print("💡 可能的原因:")
            print("  - 设备未连接或授权")
            print("  - UI服务繁忙（could not get idle state）")
            print("  - 应用界面正在加载")
            print("  - ADB权限问题")
            return False
            
    except Exception as e:
        print(f"❌ UI分析过程出错: {str(e)}")
        return False


def step_1_close_douyin(app_manager: DouyinAppManager,
                        context_analyzer: UIContextAnalyzer,
                        adb: ADBInterface) -> bool:
    """步骤1：关闭抖音应用"""
    print_step_header(1, "关闭抖音应用", "确保干净的起始状态")
    
    try:
        # 检查当前应用状态
        app_status = app_manager.get_app_status_info()
        print(f"📱 当前应用状态: {app_status}")
        
        if app_status.get('is_running', False):
            print("🔄 检测到抖音正在运行，准备关闭...")
            
            # 分析关闭前的UI状态
            print("\n📊 关闭前UI状态分析:")
            analyze_current_ui_context(adb, context_analyzer, "关闭前状态")
            
            # 关闭应用
            if app_manager.stop_douyin():
                print("✅ 抖音应用已成功关闭")
                time.sleep(2)  # 等待完全关闭
                
                # 验证关闭状态
                final_status = app_manager.get_app_status_info()
                print(f"📱 关闭后状态: {final_status}")
                
                if not final_status.get('is_running', True):
                    return True
                else:
                    print("⚠️ 应用可能未完全关闭")
                    return False
            else:
                print("❌ 关闭抖音失败")
                return False
        else:
            print("✅ 抖音应用未运行，无需关闭")
            return True
            
    except Exception as e:
        print(f"❌ 关闭抖音时发生错误: {e}")
        return False


def step_2_start_douyin(app_manager: DouyinAppManager,
                        context_analyzer: UIContextAnalyzer,
                        adb: ADBInterface) -> bool:
    """步骤2：启动抖音应用"""
    print_step_header(2, "启动抖音应用", "启动抖音并等待加载完成")
    
    try:
        print("🚀 正在启动抖音应用...")
        if not app_manager.start_douyin():
            print("❌ 启动抖音失败")
            return False
        
        # 等待应用启动
        time.sleep(3)
        
        # 分析启动后的UI状态
        print("\n📊 启动后UI状态分析:")
        analyze_current_ui_context(adb, context_analyzer, "启动后状态")
        
        # 检查应用状态
        app_status = app_manager.get_app_status_info()
        print(f"📱 启动后应用状态: {app_status}")
        
        if app_status.get('is_running', False):
            print("✅ 抖音应用启动成功")
            return True
        else:
            print("❌ 抖音应用启动失败")
            return False
            
    except Exception as e:
        print(f"❌ 启动抖音时发生错误: {e}")
        return False


def step_3_wait_for_ready(splash_detector: DouyinSplashDetector) -> bool:
    """步骤3：等待抖音完全就绪"""
    print_step_header(3, "等待抖音就绪", "等待启动画面消失，主界面加载完成")
    
    try:
        print("⏳ 等待抖音完全就绪...")
        if splash_detector.wait_for_douyin_ready(max_attempts=3):
            print("✅ 抖音已完全就绪")
            return True
        else:
            print("❌ 抖音启动超时或未就绪")
            return False
            
    except Exception as e:
        print(f"❌ 等待抖音就绪时发生错误: {e}")
        return False


def step_4_navigate_to_profile(nav_detector: DouyinNavigationDetector) -> bool:
    """步骤4：导航到个人资料页面"""
    print_step_header(4, "导航到个人资料", "查找并点击底部导航栏的'我'按钮")
    
    try:
        print("🧭 开始导航到个人资料页面...")
        
        # 检测导航栏结构
        nav_structure = nav_detector.detect_navigation_structure()
        if nav_structure:
            print(f"✅ 检测到导航栏: {nav_structure['total_buttons']}个按钮")
        
        # 安全导航到个人资料页面
        if nav_detector.navigate_to_profile_safely():
            print("✅ 成功导航到个人资料页面")
            return True
        else:
            print("❌ 导航到个人资料页面失败")
            return False
            
    except Exception as e:
        print(f"❌ 导航到个人资料时发生错误: {e}")
        return False


def step_5_click_add_friends(add_friend_detector: DouyinAddFriendDetector) -> bool:
    """步骤5：点击添加朋友"""
    print_step_header(5, "点击添加朋友", "在个人资料页面找到并点击'添加朋友'按钮")
    
    try:
        print("🔍 正在检测'添加朋友'按钮...")
        
        # 检测添加朋友按钮
        add_friend_button = add_friend_detector.detect_add_friend_button()
        if not add_friend_button:
            print("❌ 未找到'添加朋友'按钮")
            return False
        
        print("✅ 找到'添加朋友'按钮:")
        print(f"   位置: {add_friend_button['center']}")
        print(f"   文本: '{add_friend_button['text']}'")
        
        # 导航到添加朋友页面
        print("🎯 正在点击'添加朋友'按钮...")
        if add_friend_detector.navigate_to_add_friends_safely():
            print("✅ 成功导航到添加朋友页面")
            return True
        else:
            print("❌ 导航到添加朋友页面失败")
            return False
            
    except Exception as e:
        print(f"❌ 点击添加朋友时发生错误: {e}")
        return False


def step_6_click_contacts(add_friend_detector: DouyinAddFriendDetector,
                          context_analyzer: UIContextAnalyzer,
                          adb: ADBInterface) -> bool:
    """步骤6：点击通讯录"""
    print_step_header(6, "点击通讯录", "在添加朋友页面找到并点击'通讯录'按钮")
    
    try:
        # 等待页面加载
        time.sleep(3)
        
        # 分析当前页面状态
        print("\n📊 添加朋友页面UI状态分析:")
        analyze_current_ui_context(adb, context_analyzer, "添加朋友页面")
        
        print("🔍 正在检测'通讯录'按钮...")
        
        # 检测通讯录按钮
        contacts_button = add_friend_detector.detect_contacts_button()
        if not contacts_button:
            print("❌ 未找到'通讯录'按钮")
            return False
        
        print("✅ 找到'通讯录'按钮:")
        print(f"   位置: {contacts_button['center']}")
        print(f"   文本: '{contacts_button['text']}'")
        
        # 导航到通讯录页面
        print("🎯 正在点击'通讯录'按钮...")
        if add_friend_detector.navigate_to_contacts_safely():
            print("✅ 成功导航到通讯录页面")
            return True
        else:
            print("❌ 导航到通讯录页面失败")
            return False
            
    except Exception as e:
        print(f"❌ 点击通讯录时发生错误: {e}")
        return False


def step_7_verify_contacts_page(add_friend_detector: DouyinAddFriendDetector,
                                context_analyzer: UIContextAnalyzer,
                                adb: ADBInterface) -> bool:
    """步骤7：验证通讯录页面"""
    print_step_header(7, "验证通讯录页面", "确认已成功进入通讯录页面")
    
    try:
        # 等待页面加载
        time.sleep(3)
        
        # 分析通讯录页面状态
        print("\n📊 通讯录页面UI状态分析:")
        analyze_current_ui_context(adb, context_analyzer, "通讯录页面")
        
        # 验证页面
        if add_friend_detector.is_on_contacts_page():
            print("✅ 确认当前在通讯录页面")
            return True
        else:
            print("❌ 通讯录页面验证失败")
            return False
            
    except Exception as e:
        print(f"❌ 验证通讯录页面时发生错误: {e}")
        return False


def run_complete_workflow():
    """运行完整流程"""
    print("🎯 抖音通讯录自动化 - 完整流程")
    print("从关闭抖音到成功进入通讯录的完整自动化流程")
    print(f"{'='*80}")
    
    setup_logging()
    
    try:
        # 初始化所有模块
        print("\n🔧 初始化模块...")
        adb = ADBInterface()
        app_manager = DouyinAppManager(adb)
        splash_detector = DouyinSplashDetector(adb, app_manager)
        nav_detector = DouyinNavigationDetector(adb)
        add_friend_detector = DouyinAddFriendDetector(adb)
        context_analyzer = UIContextAnalyzer()
        
        # 检查设备连接
        devices = adb.get_connected_devices()
        if not devices:
            print("❌ 没有连接的设备")
            return False
        print(f"✅ 设备连接正常: {devices}")
        
        # 执行完整流程
        success = True
        
        # 步骤1：关闭抖音
        if success:
            success = step_1_close_douyin(app_manager, context_analyzer, adb)
        
        # 步骤2：启动抖音
        if success:
            success = step_2_start_douyin(app_manager, context_analyzer, adb)
        
        # 步骤3：等待就绪
        if success:
            success = step_3_wait_for_ready(splash_detector)
        
        # 步骤4：导航到个人资料
        if success:
            success = step_4_navigate_to_profile(nav_detector)
        
        # 步骤5：点击添加朋友
        if success:
            success = step_5_click_add_friends(add_friend_detector)
        
        # 步骤6：点击通讯录
        if success:
            success = step_6_click_contacts(add_friend_detector, context_analyzer, adb)
        
        # 步骤7：验证通讯录页面
        if success:
            success = step_7_verify_contacts_page(add_friend_detector, context_analyzer, adb)
        
        # 输出最终结果
        print(f"\n{'='*80}")
        if success:
            print("🎉 完整流程执行成功！")
            print("✅ 已成功从关闭抖音到进入通讯录页面")
            print("📱 系统状态：已可进行通讯录相关操作")
        else:
            print("❌ 流程执行失败")
            print("🔧 请检查设备状态和应用权限")
        print(f"{'='*80}")
        
        return success
        
    except Exception as e:
        print(f"❌ 完整流程执行时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 启动抖音通讯录完整流程自动化...")
    success = run_complete_workflow()
    
    if success:
        print("\n✅ 程序执行完成，流程成功！")
    else:
        print("\n❌ 程序执行完成，流程失败。")