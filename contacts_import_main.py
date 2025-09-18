#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contacts Import Main Program

AI-Agent-Friendly 通讯录导入主程序
演示完整的从TXT到Android设备的通讯录导入流程

Author: AI Assistant
Created: 2025/09/18
"""

import logging
import sys
from pathlib import Path

# 添加modules路径
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from modules.contacts_converter import ContactsConverter
from modules.adb_contacts_manager import ADBContactsManager
from modules.smart_ui_interactor import SmartUIInteractor
from modules.contacts_ui_detector import ContactsUIDetector
from modules.contacts_import_automation import ContactsImportAutomation


def setup_logging():
    """设置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('contacts_import.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def create_vcf_file(contacts, output_path):
    """创建VCF文件"""
    try:
        with open(output_path, 'w', encoding='utf-8') as vcf_file:
            for contact in contacts:
                phone = contact.get('phone', '')
                name = contact.get('name', f"联系人_{phone[-4:]}")
                
                vcf_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{name}
N:{name};;;;
TEL;TYPE=CELL;TYPE=VOICE:{phone}
END:VCARD

"""
                vcf_file.write(vcf_content)
        return True
    except Exception as e:
        print(f"VCF文件创建失败: {e}")
        return False


def main():
    """主函数"""
    logger = setup_logging()
    
    if len(sys.argv) != 2:
        print("使用方法: python contacts_import_main.py <txt_file_path>")
        print("示例: python contacts_import_main.py modules/通讯录1.txt")
        return
    
    txt_file_path = sys.argv[1]
    
    if not Path(txt_file_path).exists():
        print(f"错误: 文件不存在 - {txt_file_path}")
        return
    
    print("=" * 60)
    print("    AI-Agent 通讯录导入系统")
    print("=" * 60)
    
    # 步骤1: 初始化模块
    print("\n步骤1: 初始化模块...")
    converter = ContactsConverter(logger=logger)
    adb_manager = ADBContactsManager(logger=logger)
    ui_detector = ContactsUIDetector(logger=logger)
    automation = ContactsImportAutomation(logger=logger)
    
    # 步骤2: 检查设备连接
    print("\n步骤2: 检查设备连接...")
    if not adb_manager.check_device_connection():
        print("❌ 没有检测到Android设备连接")
        print("请确保:")
        print("1. USB调试已启用")
        print("2. 设备已通过USB连接")
        print("3. 已授权此计算机的调试访问")
        return
    
    devices = adb_manager.get_connected_devices()
    print(f"✓ 检测到 {len(devices)} 个设备: {devices}")
    
    # 步骤3: 转换TXT文件
    print(f"\n步骤3: 转换TXT文件 - {txt_file_path}")
    try:
        contacts = converter.convert_txt_to_contacts(txt_file_path)
        stats = converter.get_conversion_statistics()
        
        print(f"转换结果:")
        print(f"- 输入行数: {stats['total_input']}")
        print(f"- 有效联系人: {stats['valid_numbers']}")
        print(f"- 无效数据: {stats['invalid_numbers']}")
        print(f"- 重复数据: {stats['duplicates_removed']}")
        print(f"- 成功率: {stats['success_rate']:.1f}%")
        
        if len(contacts) == 0:
            print("❌ 没有找到有效的联系人数据")
            return
            
    except Exception as e:
        print(f"❌ TXT文件转换失败: {e}")
        return
    
    # 步骤4: 生成VCF文件
    print(f"\n步骤4: 生成VCF文件...")
    vcf_path = str(Path(txt_file_path).with_suffix('.vcf'))
    
    if not create_vcf_file(contacts, vcf_path):
        print("❌ VCF文件生成失败")
        return
    
    print(f"✓ VCF文件已生成: {vcf_path}")
    
    # 步骤5: 推送VCF到设备
    print(f"\n步骤5: 推送VCF文件到设备...")
    if not adb_manager.push_vcf_to_device(vcf_path):
        print("❌ VCF文件推送到设备失败")
        return
    
    print("✓ VCF文件推送成功")
    
    # 步骤6: 触发导入
    print(f"\n步骤6: 触发通讯录导入...")
    if not adb_manager.trigger_contacts_import():
        print("❌ 触发导入失败")
        return
    
    print("✓ 导入已触发")
    
    # 步骤7: 智能UI交互处理
    print("\n步骤7: 智能UI交互处理...")
    print("正在启动智能交互引擎...")
    
    # 使用新的智能UI交互引擎
    ui_interactor = SmartUIInteractor(device_id=None)
    
    # 自动处理完整的UI交互流程
    interaction_result = ui_interactor.auto_handle_ui_flow()
    
    if interaction_result['success']:
        print("✓ UI交互处理成功!")
        completed_steps = interaction_result['steps_completed']
        if completed_steps:
            print(f"  完成步骤: {', '.join(completed_steps)}")
        print(f"  耗时: {interaction_result['total_time']:.1f}秒")
    else:
        print("⚠️  UI交互处理部分完成")
        if interaction_result['errors']:
            for error in interaction_result['errors']:
                print(f"  错误: {error}")
    
    ui_stats = interaction_result['stats']
    
    # 步骤8: 清理临时文件
    print(f"\n步骤8: 清理临时文件...")
    try:
        Path(vcf_path).unlink()
        print("✓ 临时文件已清理")
    except Exception as e:
        print(f"⚠️  清理失败: {e}")
    
    # 显示最终统计
    print(f"\n" + "=" * 60)
    print("    导入完成统计")
    print("=" * 60)
    
    converter_stats = converter.get_conversion_statistics()
    adb_stats = adb_manager.get_operation_statistics()
    # 获取旧版统计数据（如果需要的话）
    old_ui_stats = ui_detector.get_detection_statistics()
    
    print(f"转换统计:")
    print(f"- 有效联系人: {converter_stats['valid_numbers']}")
    print(f"- 转换成功率: {converter_stats['success_rate']:.1f}%")
    
    print(f"\nADB操作统计:")
    print(f"- 文件推送: {adb_stats['files_pushed']}")
    print(f"- 导入尝试: {adb_stats['import_attempts']}")
    print(f"- 成功导入: {adb_stats['successful_imports']}")
    
    print("\nUI交互统计:")
    print(f"- UI捕获次数: {ui_stats['ui_dumps']}")
    print(f"- 点击操作: {ui_stats['clicks_performed']}")
    
    print("\n自动化统计:")
    print(f"- 执行点击: {ui_stats['clicks_performed']}")
    print(f"- 处理对话框: {ui_stats['dialogs_handled']}")
    print(f"- 授权权限: {ui_stats['permissions_granted']}")
    
    print(f"\n🎉 通讯录导入流程完成!")
    print(f"总计处理了 {len(contacts)} 个联系人")


if __name__ == "__main__":
    main()