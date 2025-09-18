#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart UI Interactor Module

智能UI交互引擎 - 专为处理Android权限、对话框和应用选择器设计
支持多厂商适配和智能按钮识别

Author: AI Assistant
Created: 2025/09/18
"""

import logging
import subprocess
import xml.etree.ElementTree as ET
import re
import time
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class UIElement:
    """UI元素数据类"""
    text: str
    bounds: str
    resource_id: str
    class_name: str
    clickable: bool
    enabled: bool
    content_desc: str
    package: str


@dataclass
class ClickCoordinate:
    """点击坐标"""
    x: int
    y: int
    confidence: float


class SmartUIInteractor:
    """
    智能UI交互引擎
    
    专为自动化处理Android系统对话框、权限请求、应用选择器设计
    """
    
    def __init__(self, device_id: Optional[str] = None):
        self.device_id = device_id
        self.logger = logging.getLogger(__name__)
        self.adb_path = self._find_adb_executable()
        
        # 交互统计
        self.stats = {
            'ui_dumps': 0,
            'clicks_performed': 0,
            'permissions_granted': 0,
            'dialogs_handled': 0,
            'apps_selected': 0,
            'failures': 0
        }
        
        # 按钮文本模式库
        self.button_patterns = {
            'allow': [
                '允许', '始终允许', '仅在使用时允许', 'Allow', 'Always Allow',
                'Allow only while using app', '同意', 'Agree', '授权', 'Grant'
            ],
            'confirm': [
                '确定', '确认', 'OK', 'Confirm', '是', 'Yes', '继续', 'Continue',
                '导入', 'Import', '保存', 'Save'
            ],
            'deny': [
                '禁止', '拒绝', 'Deny', 'Refuse', '取消', 'Cancel', '否', 'No'
            ],
            'contacts_apps': [
                '联系人', '通讯录', 'Contacts', 'Phone', 'Dialer', 'People'
            ]
        }
        
        self.logger.info("SmartUIInteractor initialized")
    
    def _find_adb_executable(self) -> str:
        """查找ADB可执行文件"""
        from pathlib import Path
        local_adb = Path(__file__).parent.parent / "platform-tools" / "adb.exe"
        return str(local_adb) if local_adb.exists() else "adb"
    
    def get_ui_xml(self) -> Optional[str]:
        """获取当前界面XML"""
        try:
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            cmd.extend(["exec-out", "uiautomator", "dump", "/dev/tty"])
            
            for encoding in ['utf-8', 'gbk', 'gb2312']:
                try:
                    result = subprocess.run(
                        cmd, capture_output=True, encoding=encoding,
                        errors='ignore', timeout=10
                    )
                    
                    if (result.returncode == 0 and result.stdout and 
                        '<?xml' in result.stdout):
                        self.stats['ui_dumps'] += 1
                        return result.stdout.strip()
                except Exception:
                    continue
            
            self.logger.warning("Failed to get UI XML")
            return None
        except Exception as e:
            self.logger.error(f"UI XML error: {e}")
            return None
    
    def parse_elements(self, xml_content: str) -> List[UIElement]:
        """解析UI元素"""
        elements = []
        try:
            root = ET.fromstring(xml_content)
            
            def extract_element(node):
                element = UIElement(
                    text=node.get('text', ''),
                    bounds=node.get('bounds', ''),
                    resource_id=node.get('resource-id', ''),
                    class_name=node.get('class', ''),
                    clickable=node.get('clickable', 'false') == 'true',
                    enabled=node.get('enabled', 'false') == 'true',
                    content_desc=node.get('content-desc', ''),
                    package=node.get('package', '')
                )
                
                if (element.clickable and element.enabled and 
                    (element.text or element.content_desc)):
                    elements.append(element)
                
                for child in node:
                    extract_element(child)
            
            extract_element(root)
        except ET.ParseError as e:
            self.logger.error(f"XML parse error: {e}")
        
        return elements
    
    def calculate_click_coordinates(self, bounds: str) -> Optional[ClickCoordinate]:
        """从bounds字符串计算点击坐标"""
        try:
            # bounds格式: [left,top][right,bottom]
            match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
            if match:
                left, top, right, bottom = map(int, match.groups())
                x = (left + right) // 2
                y = (top + bottom) // 2
                
                # 计算置信度（基于按钮大小）
                width = right - left
                height = bottom - top
                area = width * height
                confidence = min(area / 10000, 1.0)  # 标准化到0-1
                
                return ClickCoordinate(x, y, confidence)
        except Exception as e:
            self.logger.warning(f"Coordinate calculation failed: {e}")
        return None
    
    def find_button_by_text(self, elements: List[UIElement], 
                           button_type: str) -> List[Tuple[UIElement, float]]:
        """根据文本模式查找按钮"""
        candidates = []
        patterns = self.button_patterns.get(button_type, [])
        
        for element in elements:
            if not (element.clickable and element.enabled):
                continue
            
            text_content = (element.text + ' ' + element.content_desc).lower()
            
            for pattern in patterns:
                if pattern.lower() in text_content:
                    # 计算匹配置信度
                    confidence = len(pattern) / len(text_content) if text_content else 0
                    confidence = min(confidence * 2, 1.0)  # 放大置信度
                    candidates.append((element, confidence))
                    break
        
        # 按置信度排序
        return sorted(candidates, key=lambda x: x[1], reverse=True)
    
    def click_element(self, element: UIElement) -> bool:
        """点击UI元素"""
        try:
            coords = self.calculate_click_coordinates(element.bounds)
            if not coords:
                return False
            
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            cmd.extend(['shell', 'input', 'tap', str(coords.x), str(coords.y)])
            
            result = subprocess.run(cmd, timeout=5)
            success = result.returncode == 0
            
            if success:
                self.stats['clicks_performed'] += 1
                self.logger.info(f"Clicked: {element.text} at ({coords.x}, {coords.y})")
            
            return success
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return False
    
    def handle_permission_dialog(self, max_attempts: int = 5) -> bool:
        """处理权限对话框 - 支持多步权限"""
        permission_granted = False
        
        for attempt in range(max_attempts):
            self.logger.info(f"Permission attempt {attempt + 1}/{max_attempts}")
            
            xml_content = self.get_ui_xml()
            if not xml_content:
                time.sleep(2)
                continue
            
            elements = self.parse_elements(xml_content)
            if not elements:
                break
            
            # 检查是否还有权限对话框
            permission_detected = self._detect_permission_dialog(elements)
            if not permission_detected:
                break
            
            # 查找允许按钮
            allow_buttons = self.find_button_by_text(elements, 'allow')
            if allow_buttons:
                best_button, confidence = allow_buttons[0]
                self.logger.info(f"Found allow button: '{best_button.text}' "
                               f"(confidence: {confidence:.2f})")
                
                if self.click_element(best_button):
                    permission_granted = True
                    self.stats['permissions_granted'] += 1
                    time.sleep(2)  # 等待界面变化
                    continue
            
            # 如果没找到允许按钮，尝试确认按钮
            confirm_buttons = self.find_button_by_text(elements, 'confirm')
            if confirm_buttons:
                best_button, confidence = confirm_buttons[0]
                self.logger.info(f"Found confirm button: '{best_button.text}' "
                               f"(confidence: {confidence:.2f})")
                
                if self.click_element(best_button):
                    permission_granted = True
                    time.sleep(2)
                    continue
            
            self.logger.warning(f"No suitable button found in attempt {attempt + 1}")
            time.sleep(1)
        
        return permission_granted
    
    def handle_app_selector(self) -> bool:
        """处理应用选择器"""
        try:
            xml_content = self.get_ui_xml()
            if not xml_content:
                return False
            
            elements = self.parse_elements(xml_content)
            
            # 查找通讯录相关应用
            contacts_apps = self.find_button_by_text(elements, 'contacts_apps')
            if contacts_apps:
                best_app, confidence = contacts_apps[0]
                self.logger.info(f"Found contacts app: '{best_app.text}' "
                               f"(confidence: {confidence:.2f})")
                
                if self.click_element(best_app):
                    self.stats['apps_selected'] += 1
                    return True
            
            # 如果没找到明确的通讯录应用，尝试点击中间位置
            self.logger.warning("No contacts app found, trying center click")
            return self._try_center_click()
            
        except Exception as e:
            self.logger.error(f"App selector error: {e}")
            return False
    
    def handle_import_confirmation(self) -> bool:
        """处理导入确认对话框"""
        try:
            xml_content = self.get_ui_xml()
            if not xml_content:
                return False
            
            elements = self.parse_elements(xml_content)
            
            # 查找确认按钮
            confirm_buttons = self.find_button_by_text(elements, 'confirm')
            if confirm_buttons:
                best_button, confidence = confirm_buttons[0]
                self.logger.info(f"Found confirm button: '{best_button.text}' "
                               f"(confidence: {confidence:.2f})")
                
                if self.click_element(best_button):
                    self.stats['dialogs_handled'] += 1
                    return True
            
            return False
        except Exception as e:
            self.logger.error(f"Import confirmation error: {e}")
            return False
    
    def _detect_permission_dialog(self, elements: List[UIElement]) -> bool:
        """检测是否为权限对话框"""
        permission_keywords = [
            '允许', '权限', 'allow', 'permission', '访问', 'access'
        ]
        
        for element in elements:
            text_content = (element.text + ' ' + element.content_desc).lower()
            if any(keyword in text_content for keyword in permission_keywords):
                return True
        return False
    
    def _try_center_click(self) -> bool:
        """尝试点击屏幕中心"""
        try:
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            cmd.extend(['shell', 'input', 'tap', '360', '800'])
            
            result = subprocess.run(cmd, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def auto_handle_ui_flow(self, timeout: int = 60) -> Dict[str, Any]:
        """自动处理完整的UI交互流程"""
        start_time = time.time()
        results = {
            'success': False,
            'steps_completed': [],
            'total_time': 0,
            'stats': {},
            'errors': []
        }
        
        try:
            # 步骤1: 处理应用选择器
            if self.handle_app_selector():
                results['steps_completed'].append('app_selector')
                time.sleep(3)
            
            # 步骤2: 处理权限对话框（可能多个）
            if self.handle_permission_dialog():
                results['steps_completed'].append('permissions')
                time.sleep(3)
            
            # 步骤3: 处理导入确认
            if self.handle_import_confirmation():
                results['steps_completed'].append('import_confirmation')
            
            results['success'] = len(results['steps_completed']) > 0
            
        except Exception as e:
            self.logger.error(f"Auto UI flow error: {e}")
            results['errors'].append(str(e))
            
        finally:
            results['total_time'] = time.time() - start_time
            results['stats'] = self.get_statistics()
        
        return results
    
    def get_statistics(self) -> Dict[str, int]:
        """获取交互统计信息"""
        return self.stats.copy()


def main():
    """测试函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    interactor = SmartUIInteractor()
    
    print("🤖 智能UI交互测试")
    print("正在分析当前界面...")
    
    # 自动处理UI流程
    results = interactor.auto_handle_ui_flow()
    
    print(f"\n✓ 处理完成 (耗时: {results['total_time']:.1f}s)")
    print(f"- 成功: {'是' if results['success'] else '否'}")
    print(f"- 完成步骤: {', '.join(results['steps_completed'])}")
    
    if results['errors']:
        print("❌ 错误:")
        for error in results['errors']:
            print(f"  - {error}")
    
    stats = results['stats']
    print(f"\n📊 统计信息:")
    print(f"- UI捕获: {stats['ui_dumps']}")
    print(f"- 点击操作: {stats['clicks_performed']}")
    print(f"- 权限授权: {stats['permissions_granted']}")
    print(f"- 对话框处理: {stats['dialogs_handled']}")


if __name__ == "__main__":
    main()