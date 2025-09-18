#!/usr/bin/env python3
"""
调试导航栏检测问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.adb_interface import ADBInterface
from modules.ui_intelligence import UIAnalyzer

def main():
    print("🔍 调试导航栏检测")
    
    # 初始化
    adb = ADBInterface()
    analyzer = UIAnalyzer()
    
    # 获取UI
    print("获取UI内容...")
    xml_content = adb.get_ui_xml()
    if not xml_content:
        print("❌ 无法获取UI")
        return
    
    # 解析UI
    if not analyzer.parse_xml(xml_content):
        print("❌ UI解析失败")
        return
    
    print(f"✅ 解析成功，共{len(analyzer.elements)}个元素")
    
    # 分析导航栏
    print("\n分析导航栏结构...")
    nav_structure = analyzer.analyze_bottom_navigation_structure()
    
    if nav_structure:
        print(f"检测结果:")
        print(f"  - 总按钮数: {nav_structure['total_buttons']}")
        print(f"  - 有效导航栏: {nav_structure['is_valid_navigation']}")
        print(f"  - 容器边界: {nav_structure['container_bounds']}")
        
        print(f"\n按钮详情:")
        for i, btn in enumerate(nav_structure['buttons']):
            profile_mark = " [我按钮]" if btn['is_profile_button'] else ""
            print(f"  {i+1}. 文本:'{btn['text']}' 描述:'{btn['content_desc']}' "
                  f"位置:{btn['center']} 类:{btn['class_name']}{profile_mark}")
    else:
        print("❌ 未检测到导航栏结构")
    
    # 查找所有包含"我"的元素
    print(f"\n查找所有包含'我'的元素:")
    me_elements = []
    for element in analyzer.elements:
        if (element.text and '我' in element.text) or \
           (element.content_desc and '我' in element.content_desc):
            me_elements.append(element)
    
    if me_elements:
        for i, elem in enumerate(me_elements):
            print(f"  {i+1}. 文本:'{elem.text}' 描述:'{elem.content_desc}' "
                  f"位置:{elem.bounds} 可点击:{elem.clickable}")
    else:
        print("  未找到包含'我'的元素")
    
    # 查找底部区域的所有可点击元素
    print(f"\n查找底部区域(y>1800)的可点击元素:")
    bottom_elements = []
    for element in analyzer.elements:
        if element.bounds and len(element.bounds) >= 4:
            if element.bounds[1] > 1800 and element.is_clickable_element():
                bottom_elements.append(element)
    
    print(f"找到{len(bottom_elements)}个底部可点击元素:")
    for i, elem in enumerate(bottom_elements[:10]):  # 只显示前10个
        text = elem.text or elem.content_desc or "无文本"
        print(f"  {i+1}. '{text}' @ {elem.bounds} 类:{elem.class_name}")

if __name__ == "__main__":
    main()