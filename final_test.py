#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""完整流程测试 - 最终验证版本"""

import sys
import os

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入模块
from modules.adb_interface import ADBInterface
from modules.douyin_add_friend_detector import DouyinAddFriendDetector


def final_complete_test():
    """最终完整测试"""
    print("🎯 完整流程最终验证测试")
    print("=" * 60)
    
    try:
        # 初始化组件
        adb = ADBInterface()
        detector = DouyinAddFriendDetector(adb)
        
        # 检查设备连接
        devices = adb.get_connected_devices()
        if not devices:
            print("❌ 没有连接的设备")
            return False
        print(f"✅ 设备连接: {devices}")
        
        # 测试通讯录按钮检测
        print("\n🔍 测试通讯录按钮检测...")
        contacts_button = detector.detect_contacts_button()
        
        if contacts_button:
            print("✅ 找到通讯录按钮:")
            print(f"   位置: {contacts_button['center']}")
            print(f"   文本: '{contacts_button['text']}'")
            print(f"   检测方法: {contacts_button['detection_method']}")
            if 'match_score' in contacts_button:
                print(f"   匹配分数: {contacts_button['match_score']:.2f}")
        else:
            print("❌ 未找到通讯录按钮")
            
        # 测试页面状态检测
        print("\n📋 测试页面状态检测...")
        print(f"在添加朋友页面: {detector.is_on_add_friends_page()}")
        print(f"在通讯录页面: {detector.is_on_contacts_page()}")
        
        # 显示检测状态
        print("\n📊 检测状态总结:")
        status = detector.get_detection_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        print("\n🎉 测试完成！流程验证成功!")
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    final_complete_test()