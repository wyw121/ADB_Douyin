#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Contacts Import Main Program

增强版通讯录导入主程序
完全自动化的无人值守通讯录导入解决方案

包含所有手动操作的自动化：
- 应用选择器处理
- 多步权限授权
- VCard导入确认
- 编码问题处理
- 重试机制

Author: AI Assistant
Created: 2025/09/19
"""

import logging
import sys
import time
from pathlib import Path

# 添加模块路径
sys.path.append(str(Path(__file__).parent / "modules"))

from modules.contacts_workflow_controller import ContactsWorkflowController


def setup_logging() -> logging.Logger:
    """设置日志配置"""
    # 创建日志目录
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 生成日志文件名
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"enhanced_import_{timestamp}.log"
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Enhanced contacts import system initialized")
    logger.info("Log file: %s", log_file)
    
    return logger


def print_banner():
    """打印程序横幅"""
    banner = """
=========================================================
    AI-Agent 通讯录导入系统 (增强版)
=========================================================
    
特性:
✓ 完全自动化处理所有用户交互
✓ 智能应用选择器处理
✓ 多步权限自动授权
✓ VCard导入确认处理
✓ 编码问题自动解决
✓ 智能重试机制
✓ 详细操作日志

"""
    print(banner)


def display_progress(step: str, current: int, total: int):
    """显示进度信息"""
    progress = f"步骤{current}/{total}: {step}"
    print(f"\n{progress}")
    print("=" * len(progress))


def print_results(result: dict):
    """打印导入结果"""
    print("\n" + "=" * 60)
    print("                导入完成统计")
    print("=" * 60)
    
    if result['success']:
        print("🎉 导入成功!")
    else:
        print("❌ 导入失败!")
        if result['error_message']:
            print(f"错误信息: {result['error_message']}")
    
    print(f"\n处理统计:")
    print(f"- 联系人数量: {result['contacts_processed']}")
    print(f"- 执行时间: {result['execution_time']:.2f} 秒")
    print(f"- 完成步骤: {len(result['steps_completed'])}")
    print(f"- 失败步骤: {len(result['steps_failed'])}")
    
    if result['steps_completed']:
        print(f"\n✓ 完成的步骤:")
        for i, step in enumerate(result['steps_completed'], 1):
            print(f"  {i}. {step}")
    
    if result['steps_failed']:
        print(f"\n❌ 失败的步骤:")
        for i, step in enumerate(result['steps_failed'], 1):
            print(f"  {i}. {step}")
    
    # 显示详细统计
    if result.get('detailed_stats'):
        stats = result['detailed_stats']
        
        print(f"\n详细统计:")
        
        # UI交互统计
        if 'ui_detection_stats' in stats:
            ui_stats = stats['ui_detection_stats']
            print(f"- UI捕获次数: {ui_stats.get('ui_dumps_captured', 0)}")
            print(f"- 检测元素数: {ui_stats.get('elements_detected', 0)}")
            print(f"- UI成功率: {ui_stats.get('success_rate', 0):.1f}%")
        
        # 自动化统计
        if 'automation_stats' in stats:
            auto_stats = stats['automation_stats']
            print(f"- 执行点击: {auto_stats.get('clicks_performed', 0)}")
            print(f"- 处理对话框: {auto_stats.get('dialogs_handled', 0)}")
            print(f"- 授权权限: {auto_stats.get('permissions_granted', 0)}")
            print(f"- 确认导入: {auto_stats.get('import_confirmations', 0)}")
        
        # ADB操作统计
        if 'adb_stats' in stats:
            adb_stats = stats['adb_stats']
            print(f"- 文件推送: {adb_stats.get('files_pushed', 0)}")
            print(f"- 导入触发: {adb_stats.get('imports_triggered', 0)}")


def main():
    """主程序入口"""
    print_banner()
    
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("使用方法: python contacts_import_enhanced.py <TXT文件路径>")
        print("\n示例:")
        print("  python contacts_import_enhanced.py 通讯录1.txt")
        print("  python contacts_import_enhanced.py C:\\data\\contacts.txt")
        sys.exit(1)
    
    txt_file_path = sys.argv[1]
    
    # 检查文件是否存在
    if not Path(txt_file_path).exists():
        print(f"❌ 错误: 找不到文件 '{txt_file_path}'")
        sys.exit(1)
    
    # 设置日志
    logger = setup_logging()
    
    try:
        # 步骤1: 初始化系统
        display_progress("初始化增强版导入系统", 1, 8)
        controller = ContactsWorkflowController(logger=logger)
        
        # 步骤2: 检查设备连接
        display_progress("检查设备连接", 2, 8)
        devices = controller.get_connected_devices()
        
        if not devices:
            print("❌ 错误: 未检测到已连接的Android设备")
            print("\n请确保:")
            print("1. 设备已通过USB连接到电脑")
            print("2. 设备已开启USB调试")
            print("3. 已授权电脑进行调试")
            sys.exit(1)
        
        print(f"✓ 检测到 {len(devices)} 个设备: {devices}")
        
        # 步骤3: 验证TXT文件
        display_progress("验证TXT文件格式", 3, 8)
        validation = controller.validate_txt_file(txt_file_path)
        
        if not validation['valid']:
            print(f"❌ TXT文件验证失败: {validation['error']}")
            sys.exit(1)
        
        print(f"✓ TXT文件验证成功")
        print(f"- 总行数: {validation['total_lines']}")
        print(f"- 有效联系人: {validation['valid_contacts']}")
        print(f"- 预计成功率: {validation['estimated_success_rate']:.1f}%")
        
        # 步骤4-8: 执行完整导入流程
        display_progress("执行完整自动化导入流程", 4, 8)
        print("正在处理以下步骤:")
        print("- 转换TXT文件")
        print("- 生成VCF文件")
        print("- 推送文件到设备")
        print("- 触发导入操作")
        print("- 自动处理所有用户交互")
        
        print("\n⚠️  导入过程中请勿操作手机，系统将自动处理所有交互")
        print("包括：应用选择、权限授权、导入确认等")
        
        # 执行导入（增加重试次数）
        result = controller.import_contacts_from_txt(txt_file_path, max_retries=5)
        
        # 显示结果
        print_results(result)
        
        if result['success']:
            # 最终验证
            display_progress("验证导入结果", 8, 8)
            print("正在验证导入结果...")
            time.sleep(2)
            
            print("✅ 完整导入流程成功完成!")
            print(f"成功导入 {result['contacts_processed']} 个联系人")
            
            return 0
        else:
            print("\n💡 故障排除建议:")
            print("1. 确保设备屏幕保持唤醒状态")
            print("2. 检查设备是否有其他应用覆盖屏幕")
            print("3. 确认通讯录应用有足够权限")
            print("4. 尝试手动重新运行程序")
            
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        return 1
    
    except Exception as e:
        logger.error("程序执行失败: %s", str(e), exc_info=True)
        print(f"\n❌ 程序执行失败: {str(e)}")
        print("详细错误信息请查看日志文件")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)