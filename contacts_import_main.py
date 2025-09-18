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
    
    # 步骤7: UI交互处理（智能版本）
    print(f"\n步骤7: 处理UI交互...")
    print("正在智能分析设备屏幕...")
    
    max_attempts = 10
    ui_interaction_successful = False
    
    for attempt in range(max_attempts):
        print(f"尝试 {attempt + 1}/{max_attempts}...")
        
        # 首先尝试智能权限处理
        if automation.smart_handle_permission_dialog():
            print("✓ 智能权限处理成功")
            ui_interaction_successful = True
            
            # 等待一下再继续检测
            import time
            time.sleep(2)
            continue
        
        # 如果智能权限处理没有成功，使用传统方法
        analysis = ui_detector.analyze_current_screen()
        
        if not analysis['ui_captured']:
            print("⚠️  UI捕获失败，重试中...")
            import time
            time.sleep(2)
            continue
        
        # 检查是否还有需要处理的对话框
        has_dialog = (analysis.get('import_dialog', {}).get('found', False) or
                     analysis.get('permission_dialog', {}).get('found', False))
        
        if not has_dialog:
            # 没有对话框了，可能导入已完成
            print("✓ 未检测到需要处理的对话框，导入可能已完成")
            ui_interaction_successful = True
            break
        
        print("UI分析结果:")
        print(f"- 导入对话框: {'是' if analysis['import_dialog']['found'] else '否'}")
        print(f"- 权限对话框: {'是' if analysis['permission_dialog']['found'] else '否'}")
        print(f"- 通讯录应用: {'是' if analysis['contacts_app']['found'] else '否'}")
        
        # 执行传统自动化操作
        if automation.perform_automated_import(analysis):
            print("✓ 传统自动化操作执行成功")
            ui_interaction_successful = True
        else:
            print("⚠️  自动化操作未执行")
        
        import time
        time.sleep(2)
    
    if not ui_interaction_successful:
        print("⚠️  UI交互处理可能未完全成功，请手动检查设备状态")
    
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
    ui_stats = ui_detector.get_detection_statistics()
    automation_stats = automation.get_automation_statistics()
    
    print(f"转换统计:")
    print(f"- 有效联系人: {converter_stats['valid_numbers']}")
    print(f"- 转换成功率: {converter_stats['success_rate']:.1f}%")
    
    print(f"\nADB操作统计:")
    print(f"- 文件推送: {adb_stats['files_pushed']}")
    print(f"- 导入尝试: {adb_stats['import_attempts']}")
    print(f"- 成功导入: {adb_stats['successful_imports']}")
    
    print(f"\nUI检测统计:")
    print(f"- UI捕获次数: {ui_stats['ui_dumps_captured']}")
    print(f"- 检测元素数: {ui_stats['elements_detected']}")
    
    print(f"\n自动化统计:")
    print(f"- 执行点击: {automation_stats['clicks_performed']}")
    print(f"- 处理对话框: {automation_stats['dialogs_handled']}")
    print(f"- 授权权限: {automation_stats['permissions_granted']}")
    
    print(f"\n🎉 通讯录导入流程完成!")
    print(f"总计处理了 {len(contacts)} 个联系人")


if __name__ == "__main__":
    main()