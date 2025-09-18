"""模块化抖音自动化主程序"""

import argparse
import logging
import sys
import time
from datetime import datetime
from typing import Dict

from modules.automation_engine import AutomationEngine


class DouyinAutomationController:
    """抖音自动化控制器 - 协调各个模块的工作"""
    
    def __init__(self, device_id: str = None):
        """初始化控制器
        
        Args:
            device_id: 设备ID
        """
        self.automation_engine = AutomationEngine(device_id)
        self.logger = logging.getLogger(__name__)
        
    def setup_logging(self, log_level: str = "INFO") -> None:
        """设置日志配置"""
        level = getattr(logging, log_level.upper())
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 创建日志目录
        import os
        os.makedirs("logs", exist_ok=True)

        # 配置日志格式
        detailed_formatter = logging.Formatter(
            "%(asctime)s | %(name)-15s | %(levelname)-8s | "
            "%(filename)s:%(lineno)d | %(message)s"
        )

        console_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s", 
            datefmt="%H:%M:%S"
        )

        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.handlers = []

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # 文件处理器
        main_log = f"logs/modular_douyin_{date_str}.log"
        file_handler = logging.FileHandler(main_log, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)

        self.logger.info("=" * 60)
        self.logger.info("模块化抖音自动化工具启动")
        self.logger.info("日志级别: %s", log_level)
        self.logger.info("日志文件: %s", main_log)
        self.logger.info("=" * 60)

    def run_system_check(self) -> bool:
        """运行系统检查"""
        print("\n🧪 系统检查阶段")
        print("-" * 30)
        
        # 1. 检查ADB连接
        print("🔧 检查ADB连接...")
        if not self.automation_engine.check_connection():
            print("❌ ADB连接失败")
            return False
        print("✅ ADB连接成功")
        
        # 2. 测试UI获取
        print("📱 测试UI获取...")
        if not self.automation_engine.get_current_ui():
            print("⚠️ UI获取失败，但继续执行")
            # 不返回False，允许继续执行
        else:
            print("✅ UI获取成功")
        
        print("\n✅ 系统检查通过!")
        return True

    def run_app_workflow(self) -> bool:
        """运行应用启动和导航流程"""
        print("\n🚀 应用启动阶段")
        print("-" * 30)
        
        # 1. 强制关闭并重启抖音（含主界面检测）
        print("🔄 强制重启抖音并等待主界面加载...")
        if not self.automation_engine.force_restart_douyin():
            print("❌ 抖音重启失败")
            return False
        print("✅ 抖音重启成功，主界面已加载")
        
        # 2. 分析当前屏幕
        print("🔍 分析当前屏幕...")
        if not self.automation_engine.analyze_current_screen():
            print("⚠️ 屏幕分析失败，但继续执行")
            # 不返回False，允许继续执行
        else:
            print("✅ 屏幕分析完成")
        
        return True

    def run_navigation_workflow(self) -> bool:
        """运行导航流程"""
        print("\n🧭 导航流程阶段")
        print("-" * 30)
        
        # 1. 导航到个人资料
        print("👤 导航到个人资料...")
        if not self.automation_engine.navigate_to_profile():
            print("❌ 导航到个人资料失败")
            return False
        print("✅ 成功到达个人资料页面")
        
        # 2. 导航到添加朋友
        print("➕ 导航到添加朋友...")
        if not self.automation_engine.navigate_to_add_friends():
            print("❌ 导航到添加朋友失败")
            return False
        print("✅ 成功到达添加朋友页面")
        
        # 3. 导航到通讯录
        print("📞 导航到通讯录...")
        if not self.automation_engine.navigate_to_contacts():
            print("❌ 导航到通讯录失败")
            return False
        print("✅ 成功到达通讯录页面")
        
        return True

    def run_contact_workflow(self, max_count: int = 10) -> Dict:
        """运行联系人关注流程"""
        print(f"\n👥 联系人关注阶段 (最多 {max_count} 个)")
        print("-" * 30)
        
        results = {
            "total_processed": 0,
            "successful_follows": 0,
            "failed_follows": 0,
            "skipped": 0,
            "contact_details": [],
        }
        
        processed_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 5
        
        while (processed_count < max_count and 
               scroll_attempts < max_scroll_attempts):
            
            # 获取当前页面的联系人
            contacts = self.automation_engine.get_contact_list()
            
            if not contacts:
                print("⚠️ 未找到联系人，尝试滚动...")
                if self.automation_engine.scroll_down():
                    scroll_attempts += 1
                    time.sleep(2)
                    continue
                else:
                    break
            
            # 处理当前页面的联系人
            page_processed = 0
            for contact in contacts:
                if processed_count >= max_count:
                    break
                    
                contact_name = contact["name"]
                print(f"📋 处理联系人 {processed_count + 1}/{max_count}: {contact_name}")
                
                if contact["can_follow"]:
                    if self.automation_engine.follow_contact(contact):
                        results["successful_follows"] += 1
                        print(f"✅ 成功关注: {contact_name}")
                        status = "success"
                    else:
                        results["failed_follows"] += 1
                        print(f"❌ 关注失败: {contact_name}")
                        status = "failed"
                else:
                    results["skipped"] += 1
                    print(f"⏭️ 跳过: {contact_name} (可能已关注)")
                    status = "skipped"
                
                results["contact_details"].append({
                    "name": contact_name, 
                    "status": status
                })
                
                processed_count += 1
                page_processed += 1
                results["total_processed"] += 1
                
                # 操作间隔
                time.sleep(1)
            
            # 如果处理了联系人但还没达到目标，滚动到下一页
            if page_processed > 0 and processed_count < max_count:
                print("📄 滚动到下一页...")
                if self.automation_engine.scroll_down():
                    time.sleep(2)
                else:
                    break
            else:
                scroll_attempts += 1
        
        # 显示结果统计
        print(f"\n📊 关注结果统计：")
        print(f"   总处理: {results['total_processed']}")
        print(f"   成功关注: {results['successful_follows']}")
        print(f"   关注失败: {results['failed_follows']}")
        print(f"   跳过: {results['skipped']}")
        
        return results

    def run_complete_workflow(self, max_follow_count: int = 10) -> Dict:
        """运行完整的自动化工作流程"""
        self.logger.info("开始执行完整的抖音自动化流程...")
        
        workflow_result = {
            "success": False,
            "step_results": {},
            "follow_results": None,
            "error_message": None,
        }
        
        try:
            # 阶段1: 系统检查
            if not self.run_system_check():
                workflow_result["error_message"] = "系统检查失败"
                return workflow_result
            workflow_result["step_results"]["system_check"] = True
            
            # 阶段2: 应用启动和初始分析
            if not self.run_app_workflow():
                workflow_result["error_message"] = "应用启动流程失败"
                return workflow_result
            workflow_result["step_results"]["app_workflow"] = True
            
            # 阶段3: 导航流程
            if not self.run_navigation_workflow():
                workflow_result["error_message"] = "导航流程失败"
                return workflow_result
            workflow_result["step_results"]["navigation_workflow"] = True
            
            # 阶段4: 联系人关注流程
            follow_results = self.run_contact_workflow(max_follow_count)
            workflow_result["follow_results"] = follow_results
            workflow_result["step_results"]["contact_workflow"] = True
            
            workflow_result["success"] = True
            self.logger.info("完整工作流程执行成功！")
            
        except Exception as e:
            self.logger.error("工作流程执行异常: %s", str(e), exc_info=True)
            workflow_result["error_message"] = str(e)
        
        return workflow_result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="模块化抖音通讯录自动关注工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python modular_douyin.py                    # 默认关注10个联系人
  python modular_douyin.py --count 5          # 关注5个联系人  
  python modular_douyin.py --device 192.168.1.100 --count 20  # 指定设备
  python modular_douyin.py --test-only        # 仅测试连接
        """
    )
    
    parser.add_argument("--device", "-d", 
                       help="指定 ADB 设备 ID")
    parser.add_argument("--count", "-c", type=int, default=10,
                       help="最大关注数量（默认 10）")
    parser.add_argument("--test-only", action="store_true",
                       help="仅运行测试，不执行实际关注操作")
    parser.add_argument("--log-level", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       default="INFO", help="日志级别（默认 INFO）")
    
    args = parser.parse_args()
    
    # 初始化控制器
    controller = DouyinAutomationController(args.device)
    controller.setup_logging(args.log_level)
    
    print("🎯 模块化抖音通讯录自动关注工具")
    print("=" * 50)
    
    try:
        if args.test_only:
            # 仅运行系统检查和应用启动测试
            if controller.run_system_check():
                if controller.run_app_workflow():
                    print("\n🎉 测试模式完成，所有功能正常！")
                    controller.logger.info("测试模式完成，功能正常")
                else:
                    print("\n❌ 应用流程测试失败！")
                    sys.exit(1)
            else:
                print("\n❌ 系统检查失败！")
                sys.exit(1)
        else:
            # 运行完整流程
            result = controller.run_complete_workflow(args.count)
            
            if result["success"]:
                print("\n🎉 自动化流程完成！")
                controller.logger.info("自动化流程成功完成")
            else:
                print(f"\n❌ 自动化流程失败: {result['error_message']}")
                controller.logger.error("自动化流程失败: %s", 
                                      result['error_message'])
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
        controller.logger.warning("用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序异常: {str(e)}")
        controller.logger.exception("程序执行异常")
        sys.exit(1)
    
    print("\n👋 程序结束")
    controller.logger.info("程序正常结束")


if __name__ == "__main__":
    main()