#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""调试当前页面内容，寻找通讯录入口"""

import sys
import os

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入模块
from modules.adb_interface import ADBInterface
from modules.ui_intelligence import UIAnalyzer


def debug_current_page():
    """调试当前页面内容"""
    print("🔍 调试当前页面内容...")
    
    adb = ADBInterface()
    
    # 获取UI内容
    ui_content = adb.get_ui_xml()
    if not ui_content:
        print("❌ 无法获取UI内容")
        return
    
    analyzer = UIAnalyzer()
    if not analyzer.parse_xml(ui_content):
        print("❌ 无法解析UI内容")
        return
    
    print(f"✅ 解析UI成功，共 {len(analyzer.elements)} 个元素")
    
    # 查找所有文本元素
    print("\n📝 所有文本元素:")
    text_elements = []
    for elem in analyzer.elements:
        if elem.text and elem.text.strip():
            text_elements.append(elem)
    
    for i, elem in enumerate(text_elements):
        clickable = "可点击" if elem.clickable else "不可点击"
        center = elem.get_center()
        print(f"  {i+1:2d}. '{elem.text}' @ {center} ({clickable})")
    
    # 查找所有可点击元素
    print(f"\n🎯 所有可点击元素 (共{len([e for e in analyzer.elements if e.clickable])}个):")
    clickable_elements = [elem for elem in analyzer.elements if elem.clickable]
    
    for i, elem in enumerate(clickable_elements):
        text = elem.text or elem.content_desc or f"资源ID:{elem.resource_id}" or "无文本"
        center = elem.get_center()
        bounds = elem.bounds
        print(f"  {i+1:2d}. '{text}' @ {center} bounds:{bounds}")
    
    # 查找可能与添加朋友、通讯录相关的元素
    print("\n🔍 可能相关的元素:")
    keywords = ['通讯录', '联系人', '好友', '推荐', '发现', '添加', 'contact', 'friend', 
                'recommend', 'discover', 'add', '手机', '电话', '联系', '同城', '可能认识']
    
    related_elements = []
    for elem in analyzer.elements:
        text = elem.text or elem.content_desc or ""
        if any(keyword in text.lower() for keyword in keywords):
            related_elements.append(elem)
    
    if related_elements:
        for i, elem in enumerate(related_elements):
            text = elem.text or elem.content_desc
            clickable = "可点击" if elem.clickable else "不可点击"
            center = elem.get_center()
            print(f"  {i+1}. '{text}' @ {center} ({clickable})")
    else:
        print("  未找到明显相关的元素")
    
    # 查找图标元素（可能是无文本的按钮）
    print("\n🎨 可能的图标按钮（无文本但可点击）:")
    icon_buttons = [elem for elem in analyzer.elements 
                   if elem.clickable and not (elem.text or elem.content_desc)]
    
    for i, elem in enumerate(icon_buttons):
        center = elem.get_center()
        bounds = elem.bounds
        resource_id = elem.resource_id or "无ID"
        print(f"  {i+1}. 图标按钮 @ {center} bounds:{bounds} ID:{resource_id}")
        if i >= 9:  # 只显示前10个
            break
    
    # 分析页面布局结构
    print("\n📐 页面布局分析:")
    print(f"  - 总元素数: {len(analyzer.elements)}")
    print(f"  - 文本元素: {len(text_elements)}")
    print(f"  - 可点击元素: {len(clickable_elements)}")
    print(f"  - 图标按钮: {len(icon_buttons)}")
    
    # 查找列表或滚动区域
    scrollable_elements = [elem for elem in analyzer.elements if elem.scrollable]
    if scrollable_elements:
        print(f"  - 可滚动区域: {len(scrollable_elements)}个")
        for elem in scrollable_elements:
            center = elem.get_center()
            bounds = elem.bounds
            print(f"    滚动区域 @ {center} bounds:{bounds}")


if __name__ == "__main__":
    debug_current_page()