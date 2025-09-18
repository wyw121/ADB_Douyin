#!/usr/bin/env python3

import sys
import os

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.adb_interface import ADBInterface
from modules.douyin_add_friend_detector import DouyinAddFriendDetector


def check_current_status():
    """检查当前状态"""
    print("🔍 检查当前抖音状态...")
    
    try:
        adb = ADBInterface()
        if not adb.check_connection():
            print("❌ 设备未连接")
            return
        
        # 获取当前Activity
        current_activity = adb.get_current_activity()
        print(f"📱 当前Activity: {current_activity}")
        
        # 检查是否在通讯录页面
        friend_detector = DouyinAddFriendDetector(adb)
        
        if friend_detector.is_on_contacts_page():
            print("✅ 当前在通讯录页面！")
        elif friend_detector.is_on_add_friends_page():
            print("✅ 当前在添加朋友页面！")
        else:
            print("ℹ️ 当前不在添加朋友相关页面")
        
        # 获取检测状态
        status = friend_detector.get_detection_status()
        print(f"\n📊 检测状态:")
        for key, value in status.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")


if __name__ == "__main__":
    check_current_status()