#!/usr/bin/env python3

import sys
import os
import logging
import time
import subprocess
from datetime import datetime

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入所有必要的模块
from modules.adb_interface import ADBInterface
from modules.douyin_app_manager import DouyinAppManager
from modules.douyin_splash_detector import DouyinSplashDetector
from modules.douyin_navigation_detector import DouyinNavigationDetector
from modules.douyin_add_friend_detector import DouyinAddFriendDetector

# 步骤名称常量
STEP_INIT_ADB = "初始化ADB接口"
STEP_START_APP = "启动抖音应用"
STEP_HANDLE_SPLASH = "处理启动画面和弹窗"
STEP_NAVIGATE_PROFILE = "导航到'我'页面"
STEP_ENTER_ADD_FRIENDS = "进入添加朋友页面"
STEP_ENTER_CONTACTS = "进入通讯录页面"
STEP_VERIFY_STATE = "验证最终状态"


def setup_logging():
    """设置日志系统"""
    # 创建logs目录
    os.makedirs("logs", exist_ok=True)
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 生成日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f'logs/full_workflow_{timestamp}.log'
    
    # 配置根日志器
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def print_step(step_num, title, status="进行中"):
    """打印步骤信息"""
    status_icons = {
        "进行中": "🔍",
        "成功": "✅",
        "失败": "❌",
        "警告": "⚠️"
    }
    icon = status_icons.get(status, "🔍")
    print(f"\n{icon} 步骤 {step_num}: {title}")
    print("-" * 50)


def check_prerequisites():
    """检查运行前提条件"""
    print_step(0, "检查运行前提条件")
    
    # 检查ADB是否可用
    try:
        result = subprocess.run(['adb', 'version'],
                                capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print("❌ ADB不可用，请检查ADB安装")
            return False
        print("✅ ADB工具可用")
    except FileNotFoundError:
        # 尝试使用本地platform-tools
        try:
            adb_path = os.path.join("platform-tools", "adb.exe")
            result = subprocess.run([adb_path, 'version'],
                                    capture_output=True, text=True,
                                    check=False)
            if result.returncode != 0:
                print("❌ 本地ADB不可用")
                return False
            print("✅ 本地ADB工具可用")
        except Exception:
            print("❌ 找不到ADB工具")
            return False
    
        # 检查设备连接
        try:
            adb = ADBInterface()
            if not adb.check_connection():
                print("❌ 没有检测到Android设备连接")
                print("请确保:")
                print("  1. 设备已通过USB连接到计算机")
                print("  2. 设备已开启USB调试")
                print("  3. 已在设备上信任此计算机")
                return False
            print("✅ Android设备连接正常")
        except Exception as e:
            print(f"❌ 设备连接检查失败: {e}")
            return False
    
    return True


def run_full_workflow():
    """运行完整的自动化流程"""
    logger = logging.getLogger(__name__)
    
    print("🚀 抖音自动化全流程开始运行...")
    print("=" * 60)
    
    try:
        # 步骤1: 初始化ADB接口
        print_step(1, STEP_INIT_ADB)
        adb = ADBInterface()
        if not adb.check_connection():
            print_step(1, STEP_INIT_ADB, "失败")
            return False
        print_step(1, STEP_INIT_ADB, "成功")
        
        # 步骤2: 启动抖音应用
        print_step(2, STEP_START_APP)
        app_manager = DouyinAppManager(adb)
        # 检查是否已经运行，如果没有则启动
        if not app_manager.is_douyin_running():
            if not app_manager.start_douyin():
                print_step(2, STEP_START_APP, "失败")
                return False
        print_step(2, STEP_START_APP, "成功")
        
        # 等待应用完全启动
        print("⏳ 等待应用完全启动...")
        time.sleep(5)
        
        # 步骤3: 处理启动画面
        print_step(3, STEP_HANDLE_SPLASH)
        splash_detector = DouyinSplashDetector(adb, app_manager)
        splash_result = splash_detector.wait_for_douyin_ready()
        if splash_result:
            print_step(3, STEP_HANDLE_SPLASH, "成功")
        else:
            print_step(3, STEP_HANDLE_SPLASH, "警告")
            print("⚠️ 启动画面处理完成，但可能有未处理的弹窗")
        
        # 步骤4: 导航到"我"页面
        print_step(4, STEP_NAVIGATE_PROFILE)
        nav_detector = DouyinNavigationDetector(adb)
        if not nav_detector.navigate_to_profile_safely():
            print_step(4, STEP_NAVIGATE_PROFILE, "失败")
            return False
        print_step(4, STEP_NAVIGATE_PROFILE, "成功")
        
        # 步骤5: 进入添加朋友页面
        print_step(5, STEP_ENTER_ADD_FRIENDS)
        friend_detector = DouyinAddFriendDetector(adb)
        if not friend_detector.navigate_to_add_friends_safely():
            print_step(5, STEP_ENTER_ADD_FRIENDS, "失败")
            return False
        print_step(5, STEP_ENTER_ADD_FRIENDS, "成功")
        
        # 步骤6: 进入通讯录页面
        print_step(6, STEP_ENTER_CONTACTS)
        if not friend_detector.navigate_to_contacts_safely():
            print_step(6, STEP_ENTER_CONTACTS, "失败")
            return False
        print_step(6, STEP_ENTER_CONTACTS, "成功")
        
        # 步骤7: 验证最终状态
        print_step(7, STEP_VERIFY_STATE)
        if friend_detector.is_on_contacts_page():
            print_step(7, STEP_VERIFY_STATE, "成功")
            print("🎉 已成功到达通讯录页面！")
        else:
            print_step(7, STEP_VERIFY_STATE, "警告")
            print("⚠️ 流程完成，但最终状态验证有问题")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断操作")
        return False
    except Exception as e:
        logger.error(f"全流程运行异常: {e}", exc_info=True)
        print(f"❌ 运行过程中发生异常: {e}")
        return False


def print_summary(success):
    """打印运行总结"""
    print("\n" + "=" * 60)
    if success:
        print("🎉 全流程运行完成！")
        print("✅ 所有步骤都已成功执行")
        print("📱 抖音应用现在应该在通讯录页面")
        print("\n📋 接下来您可以:")
        print("  • 查看通讯录联系人")
        print("  • 手动添加好友")
        print("  • 或者继续其他自动化操作")
    else:
        print("❌ 全流程运行未完全成功")
        print("📋 请检查:")
        print("  • 设备连接状态")
        print("  • 抖音应用是否正常")
        print("  • 网络连接是否稳定")
        print("  • 查看日志文件获取详细信息")
    
    print("\n📝 日志文件位置: logs/")
    print("🔧 如有问题，请查看全流程操作指南.md")
    print("=" * 60)


def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    print("🤖 抖音自动化全流程运行器")
    print("版本: 1.0.0")
    print("作者: AI Assistant")
    print("=" * 60)
    
    # 检查前提条件
    if not check_prerequisites():
        print("\n❌ 前提条件检查失败，程序退出")
        print("请解决上述问题后重新运行")
        sys.exit(1)
    
    print("\n✅ 前提条件检查通过，开始运行全流程...")
    time.sleep(2)
    
    # 运行全流程
    success = run_full_workflow()
    
    # 打印总结
    print_summary(success)
    
    # 等待用户确认
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()