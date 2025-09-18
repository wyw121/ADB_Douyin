#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试'我'按钮的点击能力"""

import sys
import os
import re
import xml.etree.ElementTree as ET

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.adb_interface import ADBInterface


def find_clickable_profile_element():
    """找到可点击的'我'相关元素"""
    print("🔍 查找可点击的'我'按钮元素")
    
    adb = ADBInterface()
    ui_analyzer = UIAnalyzer()
    
    # 获取UI内容
    xml_content = adb.get_ui_xml()
    if not xml_content:
        print("❌ 无法获取UI内容")
        return None
    
    try:
        root = ET.fromstring(xml_content)
    except Exception as e:
        print(f"❌ 解析XML失败: {e}")
        return None
    
    print("✅ 成功获取UI内容")
    
    # 查找所有包含"我"的元素
    profile_elements = []
    for element in root.iter():
        text = element.get('text', '').strip()
        desc = element.get('content-desc', '').strip()
        
        if '我' in text or '我' in desc:
            bounds_str = element.get('bounds', '')
            if bounds_str:
                # 解析坐标
                import re
                coords = re.findall(r'\d+', bounds_str)
                if len(coords) >= 4:
                    x1, y1, x2, y2 = map(int, coords[:4])
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    clickable = element.get('clickable', 'false') == 'true'
                    
                    profile_elements.append({
                        'text': text,
                        'desc': desc,
                        'center': (center_x, center_y),
                        'bounds': (x1, y1, x2, y2),
                        'clickable': clickable,
                        'class': element.get('class', ''),
                        'element': element
                    })
    
    print(f"找到 {len(profile_elements)} 个包含'我'的元素:")
    for i, elem in enumerate(profile_elements):
        print(f"  {i+1}. 文本:'{elem['text']}' 描述:'{elem['desc']}' "
              f"位置:{elem['center']} 可点击:{elem['clickable']} 类:{elem['class']}")
    
    # 查找可点击的父元素或相关元素
    print("\n🔍 查找相关的可点击元素:")
    
    for elem_info in profile_elements:
        element = elem_info['element']
        center_x, center_y = elem_info['center']
        
        # 检查父元素
        parent = element.getparent() if hasattr(element, 'getparent') else None
        if parent is not None:
            parent_clickable = parent.get('clickable', 'false') == 'true'
            if parent_clickable:
                print(f"  ✅ 找到可点击父元素: 类:{parent.get('class', '')} "
                      f"位置:{elem_info['center']}")
                return elem_info['center']
        
        # 查找附近的可点击元素（在导航栏区域）
        for other_elem in root.iter():
            other_clickable = other_elem.get('clickable', 'false') == 'true'
            if not other_clickable:
                continue
                
            other_bounds_str = other_elem.get('bounds', '')
            if other_bounds_str:
                import re
                other_coords = re.findall(r'\d+', other_bounds_str)
                if len(other_coords) >= 4:
                    ox1, oy1, ox2, oy2 = map(int, other_coords[:4])
                    other_center_x = (ox1 + ox2) // 2
                    other_center_y = (oy1 + oy2) // 2
                    
                    # 检查是否在附近（50像素以内）且在底部区域
                    if (abs(other_center_x - center_x) < 50 and 
                        abs(other_center_y - center_y) < 50 and
                        other_center_y > 1400):
                        print(f"  ✅ 找到附近可点击元素: 类:{other_elem.get('class', '')} "
                              f"位置:({other_center_x}, {other_center_y})")
                        return (other_center_x, other_center_y)
    
    print("❌ 未找到可点击的'我'按钮元素")
    return None

def test_click_profile():
    """测试点击'我'按钮"""
    clickable_position = find_clickable_profile_element()
    
    if clickable_position:
        print(f"\n🎯 尝试点击位置: {clickable_position}")
        adb = ADBInterface()
        result = adb.tap_element(clickable_position)
        if result:
            print("✅ 点击成功")
        else:
            print("❌ 点击失败")
    else:
        print("❌ 无法找到可点击的'我'按钮位置")

if __name__ == "__main__":
    test_click_profile()