#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contacts Import Automation Module

AI-Agent-Friendly 通讯录导入自动化引擎
自动化处理导入确认、权限请求等交互流程

Author: AI Assistant
Created: 2025/09/18
"""

import logging
import subprocess
import time
from typing import Optional, Dict, Any, List, Tuple
import re


class ContactsImportAutomation:
    """
    通讯录导入自动化引擎
    
    专为AI Agent设计，能够自动处理Android设备上的
    通讯录导入相关的用户交互流程
    """
    
    def __init__(self, device_id: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        """
        初始化自动化引擎
        
        Args:
            device_id: 可选的设备ID
            logger: 可选的日志记录器
        """
        self.device_id = device_id
        self.logger = logger or logging.getLogger(__name__)
        self.adb_path = self._find_adb_executable()
        
        # 自动化统计
        self.automation_stats = {
            'clicks_performed': 0,
            'dialogs_handled': 0,
            'permissions_granted': 0,
            'import_confirmations': 0,
            'automation_errors': 0,
            'successful_automations': 0
        }
        
        # 常见按钮文本模式
        self.button_patterns = {
            'confirm': [
                r'^确定$', r'^确认$', r'^导入$', r'^OK$', 
                r'^Accept$', r'^Import$', r'^Confirm$'
            ],
            'allow': [
                r'^允许$', r'^始终允许$', r'^同意$', r'^Allow$',
                r'^Always Allow$', r'^Grant$', r'^Accept$', r'^Permit$'
            ],
            'deny': [
                r'^取消$', r'^禁止$', r'^拒绝$', r'^Cancel$',
                r'^Deny$', r'^Refuse$'
            ],
            'contacts_app': [
                r'联系人', r'通讯录', r'Contact', r'电话本'
            ]
        }
        
        self.logger.info("ContactsImportAutomation initialized")
    
    def _find_adb_executable(self) -> str:
        """查找ADB可执行文件路径"""
        from pathlib import Path
        
        local_adb = Path(__file__).parent.parent / "platform-tools" / "adb.exe"
        if local_adb.exists():
            return str(local_adb)
        
        return "adb"
    
    def click_element_by_bounds(self, bounds_str: str) -> bool:
        """
        通过边界坐标点击元素
        
        Args:
            bounds_str: 边界字符串，格式如 "[x1,y1][x2,y2]"
            
        Returns:
            bool: 点击是否成功
        """
        try:
            # 解析边界坐标
            coords = self._parse_bounds(bounds_str)
            if not coords:
                return False
            
            x1, y1, x2, y2 = coords
            # 计算中心点
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            return self.click_coordinate(center_x, center_y)
            
        except Exception as e:
            self.logger.error("Element click by bounds failed: %s", str(e))
            return False
    
    def click_coordinate(self, x: int, y: int) -> bool:
        """
        点击指定坐标
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            bool: 点击是否成功
        """
        try:
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            
            cmd.extend(["shell", "input", "tap", str(x), str(y)])
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=10, check=False)
            
            if result.returncode == 0:
                self.automation_stats['clicks_performed'] += 1
                self.logger.debug("Clicked coordinate (%d, %d)", x, y)
                return True
            else:
                self.logger.warning("Click failed at (%d, %d): %s", 
                                  x, y, result.stderr)
                return False
                
        except Exception as e:
            self.logger.error("Coordinate click failed: %s", str(e))
            self.automation_stats['automation_errors'] += 1
            return False
    
    def _parse_bounds(self, bounds_str: str) -> Optional[Tuple[int, int, int, int]]:
        """
        解析边界字符串
        
        Args:
            bounds_str: 边界字符串
            
        Returns:
            Optional[Tuple]: (x1, y1, x2, y2) 或 None
        """
        try:
            # 匹配格式: [x1,y1][x2,y2]
            pattern = r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]'
            match = re.match(pattern, bounds_str)
            
            if match:
                return tuple(map(int, match.groups()))
            
            return None
            
        except Exception:
            return None
    
    def handle_permission_dialog(self, ui_elements: List[Dict[str, Any]]) -> bool:
        """
        处理权限请求对话框
        
        Args:
            ui_elements: UI元素列表
            
        Returns:
            bool: 处理是否成功
        """
        try:
            # 查找允许按钮
            allow_button = self._find_button_by_patterns(
                ui_elements, self.button_patterns['allow']
            )
            
            if allow_button:
                self.logger.info("Found permission allow button, clicking...")
                
                if self.click_element_by_bounds(allow_button['bounds']):
                    self.automation_stats['permissions_granted'] += 1
                    self.automation_stats['dialogs_handled'] += 1
                    
                    # 等待对话框消失
                    time.sleep(1)
                    
                    self.logger.info("Permission dialog handled successfully")
                    return True
                else:
                    self.logger.error("Failed to click permission allow button")
                    return False
            else:
                self.logger.warning("No allow button found in permission dialog")
                return False
                
        except Exception as e:
            self.logger.error("Permission dialog handling failed: %s", str(e))
            self.automation_stats['automation_errors'] += 1
            return False
    
    def handle_import_dialog(self, ui_elements: List[Dict[str, Any]]) -> bool:
        """
        处理导入确认对话框
        
        Args:
            ui_elements: UI元素列表
            
        Returns:
            bool: 处理是否成功
        """
        try:
            # 查找确认按钮
            confirm_button = self._find_button_by_patterns(
                ui_elements, self.button_patterns['confirm']
            )
            
            if confirm_button:
                self.logger.info("Found import confirm button, clicking...")
                
                if self.click_element_by_bounds(confirm_button['bounds']):
                    self.automation_stats['import_confirmations'] += 1
                    self.automation_stats['dialogs_handled'] += 1
                    
                    # 等待导入开始
                    time.sleep(2)
                    
                    self.logger.info("Import dialog handled successfully")
                    return True
                else:
                    self.logger.error("Failed to click import confirm button")
                    return False
            else:
                self.logger.warning("No confirm button found in import dialog")
                return False
                
        except Exception as e:
            self.logger.error("Import dialog handling failed: %s", str(e))
            self.automation_stats['automation_errors'] += 1
            return False
    
    def _find_button_by_patterns(self, ui_elements: List[Dict[str, Any]], 
                                patterns: List[str]) -> Optional[Dict[str, Any]]:
        """
        根据文本模式查找按钮
        
        Args:
            ui_elements: UI元素列表
            patterns: 文本模式列表
            
        Returns:
            Optional[Dict]: 找到的按钮元素，没找到返回None
        """
        for element in ui_elements:
            if not element.get('clickable', False):
                continue
                
            button_text = element.get('text', '').strip()
            content_desc = element.get('content_desc', '').strip()
            
            # 检查按钮文本或内容描述
            for text in [button_text, content_desc]:
                if text:
                    for pattern in patterns:
                        if re.match(pattern, text, re.IGNORECASE):
                            return element
        
        return None
    
    def open_contacts_app(self) -> bool:
        """
        打开通讯录应用
        
        Returns:
            bool: 是否成功打开
        """
        try:
            # 尝试打开系统通讯录应用
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            
            # 使用Intent打开通讯录
            cmd.extend([
                "shell", "am", "start",
                "-a", "android.intent.action.MAIN",
                "-c", "android.intent.category.LAUNCHER",
                "-n", "com.android.contacts/.activities.PeopleActivity"
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=10, check=False)
            
            if result.returncode == 0:
                self.logger.info("Contacts app opened successfully")
                time.sleep(2)  # 等待应用启动
                return True
            else:
                # 尝试备用方法
                return self._open_contacts_alternative()
                
        except Exception as e:
            self.logger.error("Failed to open contacts app: %s", str(e))
            return False
    
    def _open_contacts_alternative(self) -> bool:
        """备用的打开通讯录方法"""
        try:
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            
            # 使用更通用的Intent
            cmd.extend([
                "shell", "am", "start",
                "-a", "android.intent.action.VIEW",
                "-d", "content://contacts/people"
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=10, check=False)
            
            if result.returncode == 0:
                self.logger.info("Contacts app opened via alternative method")
                time.sleep(2)
                return True
            
            return False
            
        except Exception:
            return False
    
    def handle_app_selector(self, analysis_result: Dict[str, Any]) -> bool:
        """
        处理应用选择器对话框
        
        Args:
            analysis_result: UI分析结果
            
        Returns:
            bool: 处理是否成功
        """
        try:
            app_selector = analysis_result.get('app_selector', {})
            
            if not app_selector.get('found'):
                return False
            
            contacts_option = app_selector.get('contacts_option')
            
            if contacts_option:
                self.logger.info("Found contacts option in app selector")
                if self.click_element_by_bounds(contacts_option['bounds']):
                    self.automation_stats['dialogs_handled'] += 1
                    time.sleep(2)  # 等待应用选择完成
                    self.logger.info("App selector handled successfully")
                    return True
            
            # 如果没有明确的通讯录选项，尝试点击屏幕中央
            self.logger.info("No specific contacts option found, trying center")
            if self.click_coordinate(360, 1000):  # 基于我们的测试经验
                self.automation_stats['dialogs_handled'] += 1
                time.sleep(2)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error("App selector handling failed: %s", str(e))
            self.automation_stats['automation_errors'] += 1
            return False
    
    def handle_permission_dialog_advanced(self, analysis_result: Dict) -> bool:
        """
        处理权限请求对话框（增强版，支持多步权限）
        
        Args:
            analysis_result: UI分析结果
            
        Returns:
            bool: 处理是否成功
        """
        try:
            perm_dialog = analysis_result.get('permission_dialog', {})
            
            if not perm_dialog.get('found'):
                return False
            
            allow_button = perm_dialog.get('allow_button')
            
            if allow_button:
                step_info = ""
                if perm_dialog.get('current_step'):
                    step_info = (f" (step {perm_dialog['current_step']}/"
                                 f"{perm_dialog['total_steps']})")
                
                self.logger.info("Found permission allow button%s", step_info)
                
                if self.click_element_by_bounds(allow_button['bounds']):
                    self.automation_stats['permissions_granted'] += 1
                    self.automation_stats['dialogs_handled'] += 1
                    time.sleep(2)  # 等待权限处理完成
                    
                    self.logger.info("Permission dialog handled successfully")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error("Advanced permission dialog handling failed: %s",
                              str(e))
            self.automation_stats['automation_errors'] += 1
            return False
    
    def handle_vcard_import_dialog(self, analysis_result: Dict[str, Any]) -> bool:
        """
        处理VCard导入确认对话框
        
        Args:
            analysis_result: UI分析结果
            
        Returns:
            bool: 处理是否成功
        """
        try:
            vcard_dialog = analysis_result.get('vcard_import_dialog', {})
            
            if not vcard_dialog.get('found'):
                return False
            
            confirm_button = vcard_dialog.get('confirm_button')
            
            if confirm_button:
                self.logger.info("Found VCard import confirm button")
                
                if self.click_element_by_bounds(confirm_button['bounds']):
                    self.automation_stats['import_confirmations'] += 1
                    self.automation_stats['dialogs_handled'] += 1
                    time.sleep(3)  # 等待导入开始
                    
                    self.logger.info("VCard import dialog handled successfully")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error("VCard import dialog handling failed: %s", str(e))
            self.automation_stats['automation_errors'] += 1
            return False
    
    def perform_automated_import(self, analysis_result: Dict[str, Any]) -> bool:
        """
        执行自动化导入流程（增强版）
        
        Args:
            analysis_result: UI分析结果
            
        Returns:
            bool: 自动化是否成功
        """
        try:
            success = False
            
            # 1. 处理应用选择器
            if analysis_result.get('app_selector', {}).get('found'):
                self.logger.info("Handling app selector...")
                success = self.handle_app_selector(analysis_result)
                if success:
                    return success
            
            # 2. 处理权限对话框（增强版）
            if analysis_result.get('permission_dialog', {}).get('found'):
                self.logger.info("Handling permission dialog...")
                success = self.handle_permission_dialog_advanced(
                    analysis_result
                )
                if success:
                    return success
            
            # 3. 处理VCard导入对话框
            if analysis_result.get('vcard_import_dialog', {}).get('found'):
                self.logger.info("Handling VCard import dialog...")
                success = self.handle_vcard_import_dialog(analysis_result)
                if success:
                    return success
            
            # 4. 处理普通导入对话框
            if analysis_result.get('import_dialog', {}).get('found'):
                self.logger.info("Handling import dialog...")
                success = self.handle_import_dialog(
                    analysis_result.get('clickable_elements', [])
                )
                if success:
                    return success
            
            # 5. 如果已在通讯录应用中，表示可能导入已完成
            if analysis_result.get('contacts_app', {}).get('found'):
                self.logger.info("Already in contacts app, import may be done")
                self.automation_stats['successful_automations'] += 1
                return True
            
            # 6. 如果没有检测到任何相关界面，可能需要等待或重试
            self.logger.warning("No actionable UI elements detected")
            return False
            
        except Exception as e:
            self.logger.error("Automated import failed: %s", str(e))
            self.automation_stats['automation_errors'] += 1
            return False
    
    def perform_complete_import_flow(self, max_attempts: int = 10) -> bool:
        """
        执行完整的导入流程，包含重试机制
        
        Args:
            max_attempts: 最大尝试次数
            
        Returns:
            bool: 完整流程是否成功
        """
        from .contacts_ui_detector import ContactsUIDetector
        
        detector = ContactsUIDetector(self.device_id, self.logger)
        
        for attempt in range(max_attempts):
            self.logger.info("Import flow attempt %d/%d", attempt + 1,
                             max_attempts)
            
            # 分析当前屏幕
            analysis = detector.analyze_current_screen()
            
            if not analysis['ui_captured']:
                self.logger.warning("UI capture failed, waiting...")
                time.sleep(2)
                continue
            
            # 执行自动化操作
            success = self.perform_automated_import(analysis)
            
            if success:
                # 等待一段时间后检查是否完成
                time.sleep(3)
                
                # 再次检查状态
                final_analysis = detector.analyze_current_screen()
                if (final_analysis['ui_captured'] and 
                    final_analysis['contacts_app']['found']):
                    self.logger.info("Complete import flow successful!")
                    return True
            
            # 等待后重试
            time.sleep(2)
        
        self.logger.error("Complete import flow failed after %d attempts",
                          max_attempts)
        return False
    
    def wait_for_import_completion(self, timeout: int = 30) -> bool:
        """
        等待导入完成
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            bool: 导入是否完成
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 检测导入完成状态
                
                # 简单等待，实际应用中应该有更精确的检测
                time.sleep(2)
                
                # 假设导入需要一定时间，这里简化处理
                if time.time() - start_time > 5:  # 假设5秒后导入完成
                    self.logger.info("Import appears to be completed")
                    return True
                    
            except Exception as e:
                self.logger.error("Error while waiting for import: %s", str(e))
                break
        
        self.logger.warning("Import completion wait timeout")
        return False
    
    def get_automation_statistics(self) -> Dict[str, int]:
        """
        获取自动化统计信息
        
        Returns:
            Dict: 统计数据
        """
        stats = self.automation_stats.copy()
        total_operations = (stats['dialogs_handled'] +
                            stats['clicks_performed'])
        
        if total_operations > 0:
            stats['success_rate'] = (
                stats['successful_automations'] / total_operations * 100
            )
        else:
            stats['success_rate'] = 0.0
            
        return stats
    
    def reset_statistics(self):
        """重置统计数据"""
        self.automation_stats = {
            'clicks_performed': 0,
            'dialogs_handled': 0,
            'permissions_granted': 0,
            'import_confirmations': 0,
            'automation_errors': 0,
            'successful_automations': 0
        }
        self.logger.debug("Automation statistics reset")


def main():
    """测试函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    automation = ContactsImportAutomation()
    
    print("开始测试通讯录导入自动化...")
    
    # 测试打开通讯录应用
    success = automation.open_contacts_app()
    
    if success:
        print("✓ 通讯录应用打开成功")
    else:
        print("❌ 通讯录应用打开失败")
    
    # 显示统计信息
    stats = automation.get_automation_statistics()
    print("\n自动化统计:")
    print(f"- 执行点击: {stats['clicks_performed']}")
    print(f"- 处理对话框: {stats['dialogs_handled']}")
    print(f"- 授权权限: {stats['permissions_granted']}")
    print(f"- 确认导入: {stats['import_confirmations']}")
    print(f"- 自动化错误: {stats['automation_errors']}")
    print(f"- 成功操作: {stats['successful_automations']}")


if __name__ == "__main__":
    main()