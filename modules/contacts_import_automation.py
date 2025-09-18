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
        
        # 常见按钮文本模式（升级版，支持更复杂的权限对话框）
        self.button_patterns = {
            'confirm': [
                r'^确定$', r'^确认$', r'^导入$', r'^OK$', 
                r'^Accept$', r'^Import$', r'^Confirm$'
            ],
            'allow': [
                r'^允许$', r'^同意$', r'^Allow$', r'^Grant$', 
                r'^Accept$', r'^Permit$', r'.*允许.*', r'.*Allow.*'
            ],
            'allow_always': [
                r'^始终.*允许$', r'^Always.*Allow$', r'^Allow.*Always$',
                r'始终允许', r'仅在使用应用时允许', r'Allow all the time'
            ],
            'cancel': [
                r'^取消$', r'^Cancel$', r'^Deny$', r'^Refuse$', r'^禁止$'
            ]
        }
        
        self.logger.info("ContactsImportAutomation initialized")
    
    def parse_permission_dialog_xml(self, ui_xml: str) -> Dict[str, Any]:
        """
        专门解析权限对话框的XML，精确定位按钮
        
        Args:
            ui_xml: UI XML字符串
            
        Returns:
            Dict: 解析结果，包含按钮位置和类型
        """
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(ui_xml)
            
            result = {
                'permission_type': '',
                'step_info': '',
                'buttons': [],
                'recommended_button': None
            }
            
            # 递归查找所有元素
            def find_elements(node):
                # 查找权限信息
                text = node.get('text', '')
                if '允许' in text and ('访问' in text or '权限' in text):
                    result['permission_type'] = text
                
                # 查找步骤信息
                if re.search(r'\d+/\d+', text):
                    result['step_info'] = text
                
                # 查找按钮
                if (node.get('clickable') == 'true' and 
                    node.get('class') == 'android.widget.Button'):
                    
                    button_info = {
                        'text': text,
                        'bounds': node.get('bounds', ''),
                        'resource_id': node.get('resource-id', ''),
                        'button_type': self._classify_button(text)
                    }
                    result['buttons'].append(button_info)
                
                # 递归处理子节点
                for child in node:
                    find_elements(child)
            
            find_elements(root)
            
            # 确定推荐点击的按钮
            result['recommended_button'] = self._get_recommended_button(
                result['buttons']
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Permission dialog XML parsing failed: %s", str(e))
            return {}
    
    def _classify_button(self, button_text: str) -> str:
        """
        分类按钮类型
        
        Args:
            button_text: 按钮文本
            
        Returns:
            str: 按钮类型
        """
        text = button_text.lower()
        
        if '始终' in text and '允许' in text:
            return 'always_allow'
        elif '允许' in text:
            return 'allow'
        elif '禁止' in text or '拒绝' in text:
            return 'deny'
        elif '取消' in text:
            return 'cancel'
        elif '确定' in text:
            return 'confirm'
        else:
            return 'unknown'
    
    def _get_recommended_button(self, buttons: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        获取推荐点击的按钮
        
        Args:
            buttons: 按钮列表
            
        Returns:
            Optional[Dict]: 推荐的按钮，如果没有返回None
        """
        # 按优先级排序
        priority_order = ['always_allow', 'allow', 'confirm']
        
        for button_type in priority_order:
            for button in buttons:
                if button['button_type'] == button_type:
                    return button
        
        return None
    
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
        处理权限请求对话框（智能版本，支持多步骤权限）
        
        Args:
            ui_elements: UI元素列表
            
        Returns:
            bool: 处理是否成功
        """
        try:
            # 检查是否是多步骤权限对话框
            is_multi_step = self._is_multi_step_permission_dialog(ui_elements)
            
            # 优先查找"始终允许"按钮
            allow_button = self._find_button_by_patterns(
                ui_elements, self.button_patterns['allow_always']
            )
            
            # 如果没找到"始终允许"，查找普通"允许"按钮
            if not allow_button:
                allow_button = self._find_button_by_patterns(
                    ui_elements, self.button_patterns['allow']
                )
            
            if allow_button:
                button_text = allow_button.get('text', '未知按钮')
                self.logger.info(f"Found permission button: '{button_text}', clicking...")
                
                if self.click_element_by_bounds(allow_button['bounds']):
                    self.automation_stats['permissions_granted'] += 1
                    self.automation_stats['dialogs_handled'] += 1
                    
                    # 如果是多步骤权限，等待更长时间
                    wait_time = 2 if is_multi_step else 1
                    time.sleep(wait_time)
                    
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
    
    def _is_multi_step_permission_dialog(self, ui_elements: List[Dict[str, Any]]) -> bool:
        """
        检查是否是多步骤权限对话框
        
        Args:
            ui_elements: UI元素列表
            
        Returns:
            bool: 是否是多步骤权限对话框
        """
        for element in ui_elements:
            text = element.get('text', '')
            # 查找类似"1/2"、"2/2"的文本
            if re.search(r'\d+/\d+', text):
                return True
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
    
    def smart_handle_permission_dialog(self) -> bool:
        """
        智能处理权限对话框（基于实际XML解析）
        
        Returns:
            bool: 处理是否成功
        """
        try:
            # 获取当前UI XML
            ui_xml = self._capture_ui_xml()
            if not ui_xml:
                self.logger.error("Failed to capture UI XML")
                return False
            
            # 解析权限对话框
            dialog_info = self.parse_permission_dialog_xml(ui_xml)
            
            if not dialog_info or not dialog_info.get('buttons'):
                self.logger.warning("No permission dialog or buttons found")
                return False
            
            # 记录发现的信息
            if dialog_info.get('permission_type'):
                self.logger.info(f"Permission type: {dialog_info['permission_type']}")
            
            if dialog_info.get('step_info'):
                self.logger.info(f"Step info: {dialog_info['step_info']}")
            
            # 获取推荐按钮
            recommended_button = dialog_info.get('recommended_button')
            
            if not recommended_button:
                self.logger.error("No recommended button found")
                return False
            
            # 点击推荐按钮
            button_text = recommended_button.get('text', '未知')
            bounds = recommended_button.get('bounds', '')
            
            self.logger.info(f"Clicking recommended button: '{button_text}'")
            
            if self.click_element_by_bounds(bounds):
                self.automation_stats['permissions_granted'] += 1
                self.automation_stats['dialogs_handled'] += 1
                
                # 等待对话框处理
                time.sleep(2)
                
                self.logger.info("Smart permission dialog handled successfully")
                return True
            else:
                self.logger.error("Failed to click recommended button")
                return False
                
        except Exception as e:
            self.logger.error("Smart permission handling failed: %s", str(e))
            self.automation_stats['automation_errors'] += 1
            return False
    
    def _capture_ui_xml(self) -> Optional[str]:
        """
        捕获当前UI XML
        
        Returns:
            Optional[str]: UI XML字符串
        """
        try:
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            
            cmd.extend(["exec-out", "uiautomator", "dump", "/dev/tty"])
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=15, check=False)
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                return None
                
        except Exception as e:
            self.logger.error("UI XML capture failed: %s", str(e))
            return None

    def perform_automated_import(self, analysis_result: Dict[str, Any]) -> bool:
        """
        执行自动化导入流程
        
        Args:
            analysis_result: UI分析结果
            
        Returns:
            bool: 自动化是否成功
        """
        try:
            success = False
            
            # 处理权限对话框
            if analysis_result.get('permission_dialog', {}).get('found'):
                self.logger.info("Handling permission dialog...")
                success = self.handle_permission_dialog(
                    analysis_result.get('clickable_elements', [])
                )
                
                if success:
                    # 等待权限对话框处理完成后再继续
                    time.sleep(1)
            
            # 处理导入对话框
            if analysis_result.get('import_dialog', {}).get('found'):
                self.logger.info("Handling import dialog...")
                import_success = self.handle_import_dialog(
                    analysis_result.get('clickable_elements', [])
                )
                success = success or import_success
            
            # 如果没有检测到相关对话框，尝试打开通讯录应用
            if (not analysis_result.get('permission_dialog', {}).get('found') and
                not analysis_result.get('import_dialog', {}).get('found') and
                not analysis_result.get('contacts_app', {}).get('found')):
                
                self.logger.info("No dialogs detected, opening contacts app...")
                success = self.open_contacts_app()
            
            if success:
                self.automation_stats['successful_automations'] += 1
                
            return success
            
        except Exception as e:
            self.logger.error("Automated import failed: %s", str(e))
            self.automation_stats['automation_errors'] += 1
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