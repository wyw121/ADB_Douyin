#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contacts UI Detector Module

AI-Agent-Friendly 通讯录UI检测器
智能识别通讯录导入相关的UI元素和状态

Author: AI Assistant
Created: 2025/09/18
"""

import logging
import subprocess
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any
import re
import time


class ContactsUIDetector:
    """
    通讯录UI检测器
    
    专为AI Agent设计，能够智能识别和分析Android设备上
    与通讯录导入相关的UI元素和状态
    """
    
    def __init__(self, device_id: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        """
        初始化UI检测器
        
        Args:
            device_id: 可选的设备ID
            logger: 可选的日志记录器
        """
        self.device_id = device_id
        self.logger = logger or logging.getLogger(__name__)
        self.adb_path = self._find_adb_executable()
        
        # UI检测统计
        self.detection_stats = {
            'ui_dumps_captured': 0,
            'elements_detected': 0,
            'import_dialogs_found': 0,
            'permission_dialogs_found': 0,
            'contacts_app_detected': 0,
            'detection_errors': 0
        }
        
        # 常见的通讯录相关UI文本模式
        self.contacts_patterns = {
            'import_confirm': [
                r'导入.*联系人',
                r'从.*vcard.*导入',
                r'是否.*导入联系人',
                r'import.*contact',
                r'确认导入',
                r'confirm.*import',
                r'添加.*通讯录',
                r'add.*contact'
            ],
            'permission_request': [
                r'允许.*访问.*联系人',
                r'允许.*访问.*音乐',
                r'允许.*访问.*照片',
                r'允许.*访问.*视频',
                r'allow.*access.*contact',
                r'allow.*access.*audio',
                r'allow.*access.*photo',
                r'联系人权限',
                r'contact.*permission',
                r'授权.*通讯录',
                r'grant.*contact',
                r'是否允许.*联系人',
                r'permission.*dialog'
            ],
            'app_selector': [
                r'选择应用',
                r'打开方式',
                r'choose.*app',
                r'open.*with',
                r'resolver.*activity',
                r'应用选择器'
            ],
            'contacts_app': [
                r'联系人',
                r'通讯录',
                r'contact',
                r'phone.*book',
                r'address.*book',
                r'电话本'
            ],
            'action_buttons': [
                r'确定',
                r'确认',
                r'导入',
                r'允许',
                r'始终允许',
                r'同意',
                r'OK',
                r'Accept',
                r'Import',
                r'Allow',
                r'Always Allow',
                r'Confirm'
            ],
            'deny_buttons': [
                r'取消',
                r'禁止',
                r'拒绝',
                r'Cancel',
                r'Deny',
                r'Refuse'
            ]
        }
        
        self.logger.info("ContactsUIDetector initialized")
    
    def _find_adb_executable(self) -> str:
        """查找ADB可执行文件路径"""
        from pathlib import Path
        
        # 项目本地ADB
        local_adb = Path(__file__).parent.parent / "platform-tools" / "adb.exe"
        if local_adb.exists():
            return str(local_adb)
        
        return "adb"
    
    def capture_ui_dump(self, encoding_fallback: bool = True) -> Optional[str]:
        """
        捕获当前UI XML转储，处理编码问题
        
        Args:
            encoding_fallback: 是否使用编码回退机制
            
        Returns:
            Optional[str]: UI XML字符串，失败时返回None
        """
        try:
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            
            cmd.extend(["exec-out", "uiautomator", "dump", "/dev/tty"])
            
            # 首先尝试UTF-8编码
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=15, check=False, encoding='utf-8',
                                    errors='ignore')
            
            if result.returncode == 0 and result.stdout.strip():
                self.detection_stats['ui_dumps_captured'] += 1
                return result.stdout.strip()
            
            # 如果UTF-8失败且启用回退，尝试其他编码
            if encoding_fallback:
                for encoding in ['gbk', 'gb2312', 'latin-1']:
                    try:
                        result = subprocess.run(
                            cmd, capture_output=True, text=True,
                            timeout=15, check=False, encoding=encoding,
                            errors='ignore'
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            self.detection_stats['ui_dumps_captured'] += 1
                            return result.stdout.strip()
                    except Exception:
                        continue
            
            self.logger.warning("UI dump failed: %s", result.stderr)
            self.detection_stats['detection_errors'] += 1
            return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("UI dump timeout")
            self.detection_stats['detection_errors'] += 1
            return None
        except Exception as e:
            self.logger.error("UI dump failed: %s", str(e))
            self.detection_stats['detection_errors'] += 1
            return None
    
    def parse_ui_elements(self, ui_xml: str) -> List[Dict[str, Any]]:
        """
        解析UI XML并提取元素信息
        
        Args:
            ui_xml: UI XML字符串
            
        Returns:
            List[Dict]: UI元素信息列表
        """
        elements = []
        
        try:
            root = ET.fromstring(ui_xml)
            
            # 递归遍历所有节点
            def traverse_node(node, depth=0):
                # 提取节点属性
                element_info = {
                    'tag': node.tag,
                    'text': node.get('text', ''),
                    'content_desc': node.get('content-desc', ''),
                    'resource_id': node.get('resource-id', ''),
                    'class': node.get('class', ''),
                    'package': node.get('package', ''),
                    'clickable': node.get('clickable', 'false') == 'true',
                    'enabled': node.get('enabled', 'false') == 'true',
                    'bounds': node.get('bounds', ''),
                    'depth': depth
                }
                
                # 只保留有用信息的元素
                if (element_info['text'] or 
                    element_info['content_desc'] or 
                    element_info['resource_id']):
                    elements.append(element_info)
                
                # 递归处理子节点
                for child in node:
                    traverse_node(child, depth + 1)
            
            traverse_node(root)
            self.detection_stats['elements_detected'] += len(elements)
            
        except ET.ParseError as e:
            self.logger.error("XML parsing failed: %s", str(e))
            self.detection_stats['detection_errors'] += 1
        
        return elements
    
    def detect_import_dialog(self, elements: List[Dict[str, Any]]) -> Dict:
        """
        检测导入确认对话框
        
        Args:
            elements: UI元素列表
            
        Returns:
            Dict: 检测结果，包含是否找到对话框和相关元素
        """
        result = {
            'found': False,
            'dialog_elements': [],
            'action_buttons': [],
            'message_text': '',
            'confidence': 0.0
        }
        
        dialog_keywords = 0
        total_keywords = len(self.contacts_patterns['import_confirm'])
        
        for element in elements:
            text_content = (element['text'] + ' ' + 
                          element['content_desc']).lower()
            
            # 检查导入相关关键词
            for pattern in self.contacts_patterns['import_confirm']:
                if re.search(pattern, text_content, re.IGNORECASE):
                    dialog_keywords += 1
                    result['dialog_elements'].append(element)
                    result['message_text'] = element['text']
                    break
            
            # 检查动作按钮
            for pattern in self.contacts_patterns['action_buttons']:
                if (re.search(pattern, text_content, re.IGNORECASE) and 
                    element['clickable']):
                    result['action_buttons'].append(element)
        
        # 计算置信度
        if dialog_keywords > 0:
            result['found'] = True
            result['confidence'] = min(dialog_keywords / total_keywords, 1.0)
            self.detection_stats['import_dialogs_found'] += 1
            
        return result
    
    def detect_permission_dialog(self, elements: List[Dict[str, Any]]) -> Dict:
        """
        检测权限请求对话框
        
        Args:
            elements: UI元素列表
            
        Returns:
            Dict: 检测结果
        """
        result = {
            'found': False,
            'permission_type': '',
            'action_buttons': [],
            'message_text': '',
            'confidence': 0.0
        }
        
        permission_keywords = 0
        total_keywords = len(self.contacts_patterns['permission_request'])
        
        for element in elements:
            text_content = (element['text'] + ' ' + 
                          element['content_desc']).lower()
            
            # 检查权限相关关键词
            for pattern in self.contacts_patterns['permission_request']:
                if re.search(pattern, text_content, re.IGNORECASE):
                    permission_keywords += 1
                    result['permission_type'] = 'contacts'
                    result['message_text'] = element['text']
                    break
            
            # 检查权限对话框按钮
            if element['clickable'] and element['text']:
                button_text = element['text'].lower()
                if any(word in button_text for word in 
                      ['允许', 'allow', '同意', 'accept', '确定', 'ok']):
                    result['action_buttons'].append(element)
        
        # 计算置信度
        if permission_keywords > 0:
            result['found'] = True
            result['confidence'] = min(permission_keywords / total_keywords, 1.0)
            self.detection_stats['permission_dialogs_found'] += 1
            
        return result
    
    def _check_selector_patterns(self, text: str) -> int:
        """检查应用选择器模式"""
        count = 0
        for pattern in self.contacts_patterns['app_selector']:
            if re.search(pattern, text, re.IGNORECASE):
                count += 1
                break
        return count
    
    def _find_contacts_option(self, element: Dict, text: str) -> bool:
        """查找通讯录相关选项"""
        if not element['clickable']:
            return False
        for pattern in self.contacts_patterns['contacts_app']:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def detect_app_selector(self, elements: List[Dict[str, Any]]) -> Dict:
        """
        检测应用选择器对话框
        
        Args:
            elements: UI元素列表
            
        Returns:
            Dict: 检测结果
        """
        result = {
            'found': False,
            'selector_type': '',
            'app_options': [],
            'contacts_option': None,
            'confidence': 0.0
        }
        
        selector_keywords = 0
        
        for element in elements:
            text_content = (element['text'] + ' ' +
                            element['content_desc']).lower()
            package = element.get('package', '').lower()
            
            # 检查应用选择器模式
            selector_keywords += self._check_selector_patterns(text_content)
            if selector_keywords > 0:
                result['selector_type'] = 'app_chooser'
            
            # 检查系统Resolver活动
            if 'resolver' in package or 'internal.app' in package:
                selector_keywords += 1
                result['selector_type'] = 'system_resolver'
            
            # 查找通讯录选项
            if self._find_contacts_option(element, text_content):
                result['contacts_option'] = element
                result['app_options'].append(element)
        
        if selector_keywords > 0:
            result['found'] = True
            result['confidence'] = min(selector_keywords / 2.0, 1.0)
            
        return result
    
    def _detect_permission_type(self, text: str) -> str:
        """检测权限类型"""
        if '音乐' in text or 'audio' in text:
            return 'audio'
        elif '照片' in text or 'photo' in text:
            return 'photo'
        elif '联系人' in text or 'contact' in text:
            return 'contacts'
        return ''
    
    def _parse_step_info(self, text: str) -> tuple:
        """解析步骤信息"""
        if re.match(r'\d+/\d+', text):
            parts = text.split('/')
            return parts[0], parts[1]
        return '', ''
    
    def _find_permission_buttons(self, element: Dict) -> tuple:
        """查找权限按钮"""
        if not (element['clickable'] and element['text']):
            return None, None
        
        text = element['text'].lower()
        allow_button = None
        deny_button = None
        
        for pattern in self.contacts_patterns['action_buttons']:
            if re.search(pattern, text, re.IGNORECASE):
                allow_button = element
                break
        
        for pattern in self.contacts_patterns['deny_buttons']:
            if re.search(pattern, text, re.IGNORECASE):
                deny_button = element
                break
        
        return allow_button, deny_button
    
    def detect_permission_dialog_advanced(self, elements: List[Dict]) -> Dict:
        """
        检测权限请求对话框（增强版，支持多步权限）
        
        Args:
            elements: UI元素列表
            
        Returns:
            Dict: 检测结果
        """
        result = {
            'found': False,
            'permission_type': '',
            'current_step': '',
            'total_steps': '',
            'message_text': '',
            'allow_button': None,
            'deny_button': None,
            'confidence': 0.0
        }
        
        permission_keywords = 0
        
        for element in elements:
            text_content = (element['text'] + ' ' +
                            element['content_desc']).lower()
            package = element.get('package', '').lower()
            
            # 检查权限控制器包名
            if 'permission' in package:
                permission_keywords += 1
            
            # 检查权限相关文本
            for pattern in self.contacts_patterns['permission_request']:
                if re.search(pattern, text_content, re.IGNORECASE):
                    permission_keywords += 1
                    result['message_text'] = element['text']
                    result['permission_type'] = self._detect_permission_type(
                        text_content
                    )
                    break
            
            # 解析步骤信息
            current, total = self._parse_step_info(element['text'])
            if current:
                result['current_step'] = current
                result['total_steps'] = total
            
            # 查找按钮
            allow_btn, deny_btn = self._find_permission_buttons(element)
            if allow_btn:
                result['allow_button'] = allow_btn
            if deny_btn:
                result['deny_button'] = deny_btn
        
        if permission_keywords > 0:
            result['found'] = True
            result['confidence'] = min(permission_keywords / 2.0, 1.0)
            self.detection_stats['permission_dialogs_found'] += 1
            
        return result
    
    def detect_vcard_import_dialog(self, elements: List[Dict]) -> Dict:
        """
        检测VCard导入确认对话框
        
        Args:
            elements: UI元素列表
            
        Returns:
            Dict: 检测结果
        """
        result = {
            'found': False,
            'message_text': '',
            'confirm_button': None,
            'cancel_button': None,
            'confidence': 0.0
        }
        
        import_keywords = 0
        
        for element in elements:
            text_content = (element['text'] + ' ' + 
                          element['content_desc']).lower()
            package = element.get('package', '').lower()
            
            # 检查是否是通讯录包
            if 'contact' in package:
                import_keywords += 1
            
            # 检查VCard导入相关文本
            if ('vcard' in text_content or 
                ('导入' in text_content and '联系人' in text_content)):
                import_keywords += 1
                result['message_text'] = element['text']
            
            # 查找确认和取消按钮
            if element['clickable'] and element['text']:
                text = element['text'].lower()
                
                if text in ['确定', 'ok', '导入', 'import']:
                    result['confirm_button'] = element
                elif text in ['取消', 'cancel']:
                    result['cancel_button'] = element
        
        if import_keywords > 0:
            result['found'] = True
            result['confidence'] = min(import_keywords / 2.0, 1.0)
            
        return result
    
    def detect_contacts_app(self, elements: List[Dict[str, Any]]) -> Dict:
        """
        检测是否在通讯录应用中
        
        Args:
            elements: UI元素列表
            
        Returns:
            Dict: 检测结果
        """
        result = {
            'found': False,
            'app_package': '',
            'app_elements': [],
            'confidence': 0.0
        }
        
        contacts_keywords = 0
        total_keywords = len(self.contacts_patterns['contacts_app'])
        
        for element in elements:
            # 检查应用包名
            if element['package']:
                package = element['package'].lower()
                if any(word in package for word in 
                      ['contact', 'phone', 'dialer']):
                    result['app_package'] = element['package']
                    contacts_keywords += 1
            
            # 检查界面文本
            text_content = (element['text'] + ' ' + 
                          element['content_desc']).lower()
            
            for pattern in self.contacts_patterns['contacts_app']:
                if re.search(pattern, text_content, re.IGNORECASE):
                    contacts_keywords += 1
                    result['app_elements'].append(element)
                    break
        
        # 计算置信度
        if contacts_keywords > 0:
            result['found'] = True
            result['confidence'] = min(contacts_keywords / total_keywords, 1.0)
            self.detection_stats['contacts_app_detected'] += 1
            
        return result
    
    def get_clickable_elements(self, elements: List[Dict[str, Any]]) -> List:
        """
        获取所有可点击的元素
        
        Args:
            elements: UI元素列表
            
        Returns:
            List: 可点击元素列表
        """
        clickable_elements = []
        
        for element in elements:
            if (element['clickable'] and element['enabled'] and 
                (element['text'] or element['content_desc'])):
                clickable_elements.append(element)
        
        return clickable_elements
    
    def analyze_current_screen(self, retry_on_fail: bool = True) -> Dict:
        """
        分析当前屏幕状态
        
        Args:
            retry_on_fail: 失败时是否重试
            
        Returns:
            Dict: 完整的屏幕分析结果
        """
        analysis = {
            'timestamp': time.time(),
            'ui_captured': False,
            'app_selector': {'found': False},
            'permission_dialog': {'found': False},
            'vcard_import_dialog': {'found': False},
            'import_dialog': {'found': False},
            'contacts_app': {'found': False},
            'clickable_elements': [],
            'recommended_actions': []
        }
        
        max_attempts = 3 if retry_on_fail else 1
        
        for attempt in range(max_attempts):
            try:
                # 捕获UI（使用编码回退）
                ui_xml = self.capture_ui_dump(encoding_fallback=True)
                if not ui_xml:
                    if attempt < max_attempts - 1:
                        time.sleep(1)
                        continue
                    return analysis
                
                analysis['ui_captured'] = True
                
                # 解析元素
                elements = self.parse_ui_elements(ui_xml)
                if not elements:
                    if attempt < max_attempts - 1:
                        time.sleep(1)
                        continue
                    return analysis
                
                # 执行各种检测
                analysis['app_selector'] = self.detect_app_selector(elements)
                analysis['permission_dialog'] = (
                    self.detect_permission_dialog_advanced(elements)
                )
                analysis['vcard_import_dialog'] = (
                    self.detect_vcard_import_dialog(elements)
                )
                analysis['import_dialog'] = self.detect_import_dialog(elements)
                analysis['contacts_app'] = self.detect_contacts_app(elements)
                analysis['clickable_elements'] = self.get_clickable_elements(
                    elements
                )
                
                # 生成推荐动作
                analysis['recommended_actions'] = (
                    self._generate_recommendations(analysis)
                )
                
                self.logger.info("Screen analysis completed successfully")
                return analysis
                
            except Exception as e:
                self.logger.error("Screen analysis attempt %d failed: %s",
                                  attempt + 1, str(e))
                if attempt < max_attempts - 1:
                    time.sleep(1)
                else:
                    self.detection_stats['detection_errors'] += 1
        
        return analysis
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        基于分析结果生成推荐动作
        
        Args:
            analysis: 屏幕分析结果
            
        Returns:
            List[str]: 推荐动作列表
        """
        recommendations = []
        
        # 应用选择器处理
        if analysis['app_selector']['found']:
            if analysis['app_selector']['contacts_option']:
                recommendations.append("检测到应用选择器，建议选择通讯录应用")
            else:
                recommendations.append("检测到应用选择器，需要查找通讯录选项")
        
        # 权限对话框处理
        elif analysis['permission_dialog']['found']:
            perm = analysis['permission_dialog']
            if perm['current_step'] and perm['total_steps']:
                recommendations.append(
                    f"检测到权限对话框({perm['current_step']}/"
                    f"{perm['total_steps']})，建议点击允许按钮"
                )
            else:
                recommendations.append("检测到权限对话框，建议点击允许按钮")
        
        # VCard导入对话框处理
        elif analysis['vcard_import_dialog']['found']:
            recommendations.append("检测到VCard导入确认对话框，建议点击确定按钮")
        
        # 普通导入对话框处理
        elif analysis['import_dialog']['found']:
            recommendations.append("检测到导入对话框，建议点击确认按钮")
        
        # 通讯录应用中
        elif analysis['contacts_app']['found']:
            recommendations.append("已在通讯录应用中，可以执行导入操作")
        
        # 未检测到相关界面
        else:
            recommendations.append("未检测到通讯录相关界面，建议检查导入状态")
        
        return recommendations
    
    def get_detection_statistics(self) -> Dict[str, int]:
        """
        获取检测统计信息
        
        Returns:
            Dict: 统计数据
        """
        stats = self.detection_stats.copy()
        if stats['ui_dumps_captured'] > 0:
            stats['success_rate'] = (
                (stats['ui_dumps_captured'] - stats['detection_errors']) /
                stats['ui_dumps_captured'] * 100
            )
        else:
            stats['success_rate'] = 0.0
            
        return stats


def main():
    """测试函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    detector = ContactsUIDetector()
    
    print("开始分析当前屏幕...")
    analysis = detector.analyze_current_screen()
    
    if not analysis['ui_captured']:
        print("❌ 无法捕获UI信息，请检查设备连接")
        return
    
    print("\n✓ UI分析完成")
    print(f"- 导入对话框: {'是' if analysis['import_dialog']['found'] else '否'}")
    print(f"- 权限对话框: {'是' if analysis['permission_dialog']['found'] else '否'}")
    print(f"- 通讯录应用: {'是' if analysis['contacts_app']['found'] else '否'}")
    print(f"- 可点击元素: {len(analysis['clickable_elements'])} 个")
    
    if analysis['recommended_actions']:
        print("\n推荐动作:")
        for i, action in enumerate(analysis['recommended_actions'], 1):
            print(f"{i}. {action}")
    
    stats = detector.get_detection_statistics()
    print("\n检测统计:")
    print(f"- UI捕获次数: {stats['ui_dumps_captured']}")
    print(f"- 检测元素数: {stats['elements_detected']}")
    print(f"- 检测错误: {stats['detection_errors']}")
    print(f"- 成功率: {stats['success_rate']:.1f}%")


if __name__ == "__main__":
    main()