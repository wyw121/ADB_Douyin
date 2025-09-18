#!/usr/bin/env python3
"""
调试启动画面检测脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.adb_interface import ADBInterface
from modules.ui_intelligence import UIAnalyzer
import time

def main():
    print("🔍 调试启动画面检测")
    print("=" * 50)
    
    # 初始化ADB接口
    adb = ADBInterface()
    
    # 检查设备连接
    devices = adb.get_connected_devices()
    if not devices:
        print("❌ 没有找到连接的设备")
        return
    
    print(f"✅ 找到设备: {devices}")
    
    # 检查抖音状态
    print("\n📱 检查抖音当前状态...")
    
    is_running = adb.is_app_running("com.ss.android.ugc.aweme")
    print(f"抖音运行状态: {is_running}")
    
    if is_running:
        is_splash = adb.is_douyin_in_splash()
        print(f"是否在启动画面: {is_splash}")
        
        # 获取当前Activity
        current_activity = adb.get_current_activity("com.ss.android.ugc.aweme")
        print(f"当前Activity: {current_activity}")
    
    # 尝试不同的UI获取方法
    print("\n🔧 测试UI获取方法...")
    
    # 方法1: 标准dump
    print("方法1: 标准dump")
    xml1 = adb._try_standard_dump()
    print(f"结果: {'成功' if xml1 else '失败'}")
    if xml1:
        print(f"XML长度: {len(xml1)}")
    
    # 方法2: 压缩dump
    print("方法2: 压缩dump")
    xml2 = adb._try_compressed_dump()
    print(f"结果: {'成功' if xml2 else '失败'}")
    if xml2:
        print(f"XML长度: {len(xml2)}")
    
    # 方法3: stdout dump
    print("方法3: stdout dump")
    xml3 = adb._try_stdout_dump()
    print(f"结果: {'成功' if xml3 else '失败'}")
    if xml3:
        print(f"XML长度: {len(xml3)}")
    
    # 如果任何方法成功，分析UI
    xml_content = xml1 or xml2 or xml3
    if xml_content:
        print("\n📊 分析UI内容...")
        analyzer = UIAnalyzer()
        if analyzer.parse_xml(xml_content):
            print(f"解析成功，共 {len(analyzer.elements)} 个元素")
            
            # 检查主界面标识
            main_ready = adb._is_main_interface_ready(xml_content)
            print(f"主界面就绪: {main_ready}")
            
            # 查找导航栏
            nav_structure = analyzer.analyze_bottom_navigation_structure()
            if nav_structure:
                print(f"导航栏检测: {nav_structure['total_buttons']}个按钮, "
                      f"有效: {nav_structure['is_valid_navigation']}")
        else:
            print("❌ UI解析失败")
    else:
        print("❌ 所有UI获取方法都失败")
    
    print("\n🎯 手动点击屏幕中央试试...")
    screen_size = adb.get_screen_size()
    if screen_size:
        center_x = screen_size[0] // 2
        center_y = screen_size[1] // 2
        print(f"点击屏幕中央: ({center_x}, {center_y})")
        adb.tap(center_x, center_y)
        
        # 等待2秒后再次检查
        time.sleep(2)
        if adb.is_douyin_in_splash():
            print("仍在启动画面")
        else:
            print("已离开启动画面")

if __name__ == "__main__":
    main()