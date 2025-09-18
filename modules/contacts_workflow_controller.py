#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contacts Workflow Controller Module

AI-Agent-Friendly 通讯录导入工作流程控制器
整合所有模块，提供完整的通讯录导入解决方案

Author: AI Assistant
Created: 2025/09/18
"""

import logging
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

from .contacts_converter import ContactsConverter
from .adb_contacts_manager import ADBContactsManager
from .contacts_ui_detector import ContactsUIDetector
from .contacts_import_automation import ContactsImportAutomation


class ContactsWorkflowController:
    """
    通讯录导入工作流控制器
    
    专为AI Agent设计的完整通讯录导入解决方案
    协调各个模块完成从TXT文件到Android设备的完整导入流程
    """
    
    def __init__(self, device_id: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        """
        初始化工作流控制器
        
        Args:
            device_id: 可选的设备ID
            logger: 可选的日志记录器
        """
        self.device_id = device_id
        self.logger = logger or logging.getLogger(__name__)
        
        # 初始化各个模块
        self.converter = ContactsConverter(logger=self.logger)
        self.adb_manager = ADBContactsManager(device_id=device_id, 
                                            logger=self.logger)
        self.ui_detector = ContactsUIDetector(device_id=device_id, 
                                            logger=self.logger)
        self.automation = ContactsImportAutomation(device_id=device_id, 
                                                 logger=self.logger)
        
        # 工作流统计
        self.workflow_stats = {
            'total_workflows': 0,
            'successful_workflows': 0,
            'failed_workflows': 0,
            'contacts_converted': 0,
            'contacts_imported': 0,
            'ui_interactions': 0,
            'automation_actions': 0
        }
        
        self.logger.info("ContactsWorkflowController initialized")
    
    def import_contacts_from_txt(self, txt_file_path: str, 
                               max_retries: int = 3) -> Dict[str, Any]:
        """
        从TXT文件完整导入通讯录到Android设备
        
        Args:
            txt_file_path: TXT通讯录文件路径
            max_retries: 最大重试次数
            
        Returns:
            Dict: 完整的导入结果报告
        """
        workflow_result = {
            'success': False,
            'steps_completed': [],
            'steps_failed': [],
            'contacts_processed': 0,
            'error_message': '',
            'execution_time': 0,
            'detailed_stats': {}
        }
        
        start_time = time.time()
        self.workflow_stats['total_workflows'] += 1
        
        try:
            self.logger.info("Starting complete contacts import workflow")
            
            # 步骤1: 检查设备连接
            if not self._check_device_connection():
                raise ConnectionError("No Android device connected")
            workflow_result['steps_completed'].append('device_connection_check')
            
            # 步骤2: 转换TXT文件
            contacts = self._convert_txt_file(txt_file_path)
            if not contacts:
                raise ValueError("No valid contacts found in TXT file")
            
            workflow_result['contacts_processed'] = len(contacts)
            self.workflow_stats['contacts_converted'] += len(contacts)
            workflow_result['steps_completed'].append('txt_conversion')
            
            # 步骤3: 生成VCF文件
            vcf_path = self._generate_vcf_file(contacts, txt_file_path)
            if not vcf_path:
                raise RuntimeError("Failed to generate VCF file")
            workflow_result['steps_completed'].append('vcf_generation')
            
            # 步骤4: 执行导入流程（带重试）
            import_success = False
            for attempt in range(max_retries):
                try:
                    self.logger.info("Import attempt %d/%d", attempt + 1, max_retries)
                    
                    if self._execute_import_process(vcf_path):
                        import_success = True
                        break
                    else:
                        self.logger.warning("Import attempt %d failed", attempt + 1)
                        if attempt < max_retries - 1:
                            time.sleep(2)  # 等待后重试
                            
                except Exception as e:
                    self.logger.error("Import attempt %d error: %s", 
                                    attempt + 1, str(e))
                    if attempt < max_retries - 1:
                        time.sleep(2)
            
            if import_success:
                workflow_result['steps_completed'].append('contacts_import')
                self.workflow_stats['contacts_imported'] += len(contacts)
                workflow_result['success'] = True
                self.workflow_stats['successful_workflows'] += 1
            else:
                workflow_result['steps_failed'].append('contacts_import')
                raise RuntimeError("All import attempts failed")
            
            # 步骤5: 清理临时文件
            self._cleanup_temp_files(vcf_path)
            workflow_result['steps_completed'].append('cleanup')
            
        except Exception as e:
            self.logger.error("Workflow failed: %s", str(e))
            workflow_result['error_message'] = str(e)
            workflow_result['success'] = False
            self.workflow_stats['failed_workflows'] += 1
        
        # 计算执行时间和收集统计信息
        workflow_result['execution_time'] = time.time() - start_time
        workflow_result['detailed_stats'] = self._collect_detailed_stats()
        
        self.logger.info("Workflow completed in %.2f seconds", 
                        workflow_result['execution_time'])
        
        return workflow_result
    
    def _check_device_connection(self) -> bool:
        """检查设备连接"""
        try:
            return self.adb_manager.check_device_connection()
        except Exception as e:
            self.logger.error("Device connection check failed: %s", str(e))
            return False
    
    def _convert_txt_file(self, txt_file_path: str) -> List[Dict[str, str]]:
        """转换TXT文件"""
        try:
            contacts = self.converter.convert_txt_to_contacts(txt_file_path)
            self.logger.info("Converted %d contacts from TXT file", len(contacts))
            return contacts
        except Exception as e:
            self.logger.error("TXT conversion failed: %s", str(e))
            return []
    
    def _generate_vcf_file(self, contacts: List[Dict[str, str]], 
                          base_path: str) -> Optional[str]:
        """生成VCF文件"""
        try:
            # 创建VCF生成器（由于之前的模块问题，这里创建简化版本）
            vcf_path = str(Path(base_path).with_suffix('.vcf'))
            
            # 简化的VCF生成
            with open(vcf_path, 'w', encoding='utf-8') as vcf_file:
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
            
            self.logger.info("VCF file generated: %s", vcf_path)
            return vcf_path
            
        except Exception as e:
            self.logger.error("VCF generation failed: %s", str(e))
            return None
    
    def _execute_import_process(self, vcf_path: str) -> bool:
        """执行导入过程"""
        try:
            # 步骤1: 推送VCF文件到设备
            if not self.adb_manager.push_vcf_to_device(vcf_path):
                self.logger.error("Failed to push VCF file to device")
                return False
            
            # 步骤2: 触发导入
            if not self.adb_manager.trigger_contacts_import():
                self.logger.error("Failed to trigger contacts import")
                return False
            
            # 步骤3: 处理UI交互
            return self._handle_ui_interactions()
            
        except Exception as e:
            self.logger.error("Import process failed: %s", str(e))
            return False
    
    def _handle_ui_interactions(self, timeout: int = 30) -> bool:
        """处理UI交互"""
        start_time = time.time()
        interactions_handled = 0
        
        while time.time() - start_time < timeout:
            try:
                # 分析当前屏幕
                analysis = self.ui_detector.analyze_current_screen()
                self.workflow_stats['ui_interactions'] += 1
                
                if not analysis['ui_captured']:
                    self.logger.warning("Failed to capture UI, retrying...")
                    time.sleep(1)
                    continue
                
                # 执行自动化操作
                if self.automation.perform_automated_import(analysis):
                    interactions_handled += 1
                    self.workflow_stats['automation_actions'] += 1
                    
                    # 检查是否完成
                    if self._is_import_completed(analysis):
                        self.logger.info("Import completed successfully")
                        return True
                
                # 等待UI变化
                time.sleep(2)
                
            except Exception as e:
                self.logger.error("UI interaction error: %s", str(e))
                time.sleep(1)
        
        self.logger.warning("UI interaction timeout after %d interactions", 
                          interactions_handled)
        return interactions_handled > 0
    
    def _is_import_completed(self, analysis: Dict[str, Any]) -> bool:
        """检查导入是否完成"""
        # 检测导入完成状态
        return (not analysis.get('permission_dialog', {}).get('found', False) and
                not analysis.get('import_dialog', {}).get('found', False) and
                analysis.get('contacts_app', {}).get('found', False))
    
    def _cleanup_temp_files(self, vcf_path: str):
        """清理临时文件"""
        try:
            if Path(vcf_path).exists():
                Path(vcf_path).unlink()
                self.logger.debug("Cleaned up temporary VCF file: %s", vcf_path)
        except Exception as e:
            self.logger.warning("Cleanup failed: %s", str(e))
    
    def _collect_detailed_stats(self) -> Dict[str, Any]:
        """收集详细统计信息"""
        return {
            'workflow_stats': self.workflow_stats.copy(),
            'converter_stats': self.converter.get_conversion_statistics(),
            'adb_stats': self.adb_manager.get_operation_statistics(),
            'ui_detection_stats': self.ui_detector.get_detection_statistics(),
            'automation_stats': self.automation.get_automation_statistics()
        }
    
    def get_connected_devices(self) -> List[str]:
        """获取连接的设备列表"""
        return self.adb_manager.get_connected_devices()
    
    def validate_txt_file(self, txt_file_path: str) -> Dict[str, Any]:
        """
        验证TXT文件格式和内容
        
        Args:
            txt_file_path: TXT文件路径
            
        Returns:
            Dict: 验证结果
        """
        validation_result = {
            'valid': False,
            'total_lines': 0,
            'valid_contacts': 0,
            'invalid_lines': 0,
            'duplicate_numbers': 0,
            'issues': []
        }
        
        try:
            if not Path(txt_file_path).exists():
                validation_result['issues'].append("文件不存在")
                return validation_result
            
            # 使用转换器进行验证
            contacts = self.converter.convert_txt_to_contacts(txt_file_path)
            stats = self.converter.get_conversion_statistics()
            
            validation_result.update({
                'valid': len(contacts) > 0,
                'total_lines': stats['total_input'],
                'valid_contacts': stats['valid_numbers'],
                'invalid_lines': stats['invalid_numbers'],
                'duplicate_numbers': stats['duplicates_removed']
            })
            
            if stats['valid_numbers'] == 0:
                validation_result['issues'].append("没有找到有效的手机号码")
            
            if stats['invalid_numbers'] > stats['valid_numbers']:
                validation_result['issues'].append("无效数据过多，请检查文件格式")
            
        except Exception as e:
            validation_result['issues'].append(f"验证失败: {str(e)}")
        
        return validation_result
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """获取工作流统计信息"""
        stats = self.workflow_stats.copy()
        
        if stats['total_workflows'] > 0:
            stats['success_rate'] = (
                stats['successful_workflows'] / stats['total_workflows'] * 100
            )
        else:
            stats['success_rate'] = 0.0
            
        return stats


def main():
    """测试函数"""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    controller = ContactsWorkflowController()
    
    if len(sys.argv) != 2:
        print("使用方法: python contacts_workflow_controller.py <txt_file_path>")
        return
    
    txt_file = sys.argv[1]
    
    # 验证文件
    print("验证TXT文件...")
    validation = controller.validate_txt_file(txt_file)
    
    print("文件验证结果:")
    print(f"- 总行数: {validation['total_lines']}")
    print(f"- 有效联系人: {validation['valid_contacts']}")
    print(f"- 无效行数: {validation['invalid_lines']}")
    print(f"- 重复号码: {validation['duplicate_numbers']}")
    
    if validation['issues']:
        print("问题:")
        for issue in validation['issues']:
            print(f"  - {issue}")
    
    if not validation['valid']:
        print("❌ 文件验证失败，无法继续导入")
        return
    
    # 检查设备连接
    devices = controller.get_connected_devices()
    if not devices:
        print("❌ 没有检测到Android设备连接")
        return
    
    print(f"✓ 检测到设备: {devices}")
    
    # 执行完整导入流程
    print("\n开始导入流程...")
    result = controller.import_contacts_from_txt(txt_file)
    
    print("\n导入结果:")
    print(f"- 成功: {'是' if result['success'] else '否'}")
    print(f"- 处理联系人: {result['contacts_processed']}")
    print(f"- 执行时间: {result['execution_time']:.2f}秒")
    print(f"- 完成步骤: {', '.join(result['steps_completed'])}")
    
    if result['steps_failed']:
        print(f"- 失败步骤: {', '.join(result['steps_failed'])}")
    
    if result['error_message']:
        print(f"- 错误信息: {result['error_message']}")
    
    # 显示统计信息
    stats = controller.get_workflow_statistics()
    print("\n工作流统计:")
    print(f"- 总工作流: {stats['total_workflows']}")
    print(f"- 成功工作流: {stats['successful_workflows']}")
    print(f"- 成功率: {stats['success_rate']:.1f}%")


if __name__ == "__main__":
    main()