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
                r'import.*contact',
                r'确认导入',
                r'confirm.*import',
                r'添加.*通讯录',
                r'add.*contact'
            ],
            'permission_request': [
                r'允许.*访问.*联系人',
                r'allow.*access.*contact',
                r'联系人权限',
                r'contact.*permission',
                r'授权.*通讯录',
                r'grant.*contact'
            ],
            'contacts_app': [
                r'联系人',
                r'通讯录',
                r'contact',
                r'phone.*book',
                r'address.*book'
            ],
            'action_buttons': [
                r'确定',
                r'确认',
                r'导入',
                r'允许',
                r'同意',
                r'OK',
                r'Accept',
                r'Import',
                r'Allow',
                r'Confirm'
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
    
    def capture_ui_dump(self) -> Optional[str]:
        """
        捕获当前UI XML转储
        
        Returns:
            Optional[str]: UI XML字符串，失败时返回None
        """
        try:
            # 方法1: 直接输出
            xml_content = self._try_direct_dump()
            if xml_content:
                return xml_content
            
            # 方法2: 文件方式
            xml_content = self._try_file_dump()
            if xml_content:
                return xml_content
            
            self.logger.warning("All UI dump methods failed")
            self.detection_stats['detection_errors'] += 1
            return None
                
        except Exception as e:
            self.logger.error("UI dump failed: %s", str(e))
            self.detection_stats['detection_errors'] += 1
            return None
    
    def _try_direct_dump(self) -> Optional[str]:
        """尝试直接输出方式获取UI"""
        cmd = [self.adb_path]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(["exec-out", "uiautomator", "dump", "/dev/tty"])
        
        for encoding in ['utf-8', 'gbk', 'gb2312']:
            try:
                result = subprocess.run(
                    cmd, capture_output=True, encoding=encoding,
                    errors='ignore', timeout=15, check=False
                )
                
                if self._is_valid_xml(result.stdout):
                    self.detection_stats['ui_dumps_captured'] += 1
                    return result.stdout.strip()
            except (subprocess.TimeoutExpired, UnicodeDecodeError):
                continue
        return None
    
    def _try_file_dump(self) -> Optional[str]:
        """尝试文件方式获取UI"""
        try:
            base_cmd = [self.adb_path]
            if self.device_id:
                base_cmd.extend(["-s", self.device_id])
            
            # 保存到设备文件
            dump_cmd = base_cmd + ['shell', 'uiautomator', 'dump', 
                                   '/sdcard/ui_dump.xml']
            subprocess.run(dump_cmd, timeout=10, check=False)
            
            # 读取文件内容
            read_cmd = base_cmd + ['shell', 'cat', '/sdcard/ui_dump.xml']
            result = subprocess.run(
                read_cmd, capture_output=True, encoding='utf-8',
                errors='ignore', timeout=10, check=False
            )
            
            if self._is_valid_xml(result.stdout):
                self.detection_stats['ui_dumps_captured'] += 1
                return result.stdout.strip()
        except Exception as e:
            self.logger.warning("File method failed: %s", str(e))
        return None
    
    def _is_valid_xml(self, content: str) -> bool:
        """检查内容是否为有效XML"""
        return (content and content.strip() and 
                '<?xml' in content and 'hierarchy' in content)
    
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
    
    def analyze_current_screen(self) -> Dict[str, Any]:
        """
        分析当前屏幕状态
        
        Returns:
            Dict: 完整的屏幕分析结果
        """
        analysis = {
            'timestamp': time.time(),
            'ui_captured': False,
            'import_dialog': {'found': False},
            'permission_dialog': {'found': False},
            'contacts_app': {'found': False},
            'clickable_elements': [],
            'recommended_actions': []
        }
        
        try:
            # 捕获UI
            ui_xml = self.capture_ui_dump()
            if not ui_xml:
                return analysis
            
            analysis['ui_captured'] = True
            
            # 解析元素
            elements = self.parse_ui_elements(ui_xml)
            if not elements:
                return analysis
            
            # 执行各种检测
            analysis['import_dialog'] = self.detect_import_dialog(elements)
            analysis['permission_dialog'] = self.detect_permission_dialog(elements)
            analysis['contacts_app'] = self.detect_contacts_app(elements)
            analysis['clickable_elements'] = self.get_clickable_elements(elements)
            
            # 生成推荐动作
            analysis['recommended_actions'] = self._generate_recommendations(
                analysis
            )
            
            self.logger.info("Screen analysis completed successfully")
            
        except Exception as e:
            self.logger.error("Screen analysis failed: %s", str(e))
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
        
        if analysis['permission_dialog']['found']:
            recommendations.append("检测到权限对话框，建议点击允许按钮")
            
        if analysis['import_dialog']['found']:
            recommendations.append("检测到导入对话框，建议点击确认按钮")
            
        if analysis['contacts_app']['found']:
            recommendations.append("已在通讯录应用中，可以执行导入操作")
            
        if not any([analysis['permission_dialog']['found'],
                   analysis['import_dialog']['found'],
                   analysis['contacts_app']['found']]):
            recommendations.append("未检测到通讯录相关界面，建议打开通讯录应用")
        
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