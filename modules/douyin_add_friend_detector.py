#!/usr/bin/env python3
"""
抖音添加朋友功能检测模块
负责检测和操作添加朋友相关功能
"""

import logging
import time
from typing import Optional, Dict, Any, List
from .adb_interface import ADBInterface
from .ui_intelligence import UIAnalyzer
from .intelligent_text_matcher import IntelligentTextMatcher
from .ui_context_analyzer import UIContextAnalyzer


class DouyinAddFriendDetector:
    """抖音添加朋友功能检测器"""
    
    # 添加朋友相关Activity模式
    ADD_FRIENDS_ACTIVITIES = [
        "RawAddFriendsActivity",
        "AddFriendsActivity", 
        "FriendsActivity",
        "ContactsActivity"
    ]
    
    # 添加朋友按钮关键词
    ADD_FRIEND_KEYWORDS = [
        "添加朋友",
        "添加好友", 
        "加朋友",
        "Add Friends",
        "加好友"
    ]
    
    # 通讯录按钮关键词
    CONTACTS_KEYWORDS = [
        "通讯录",
        "联系人",
        "Contacts", 
        "通信录",
        "手机通讯录"
    ]
    
    # 页面验证关键词
    PAGE_INDICATORS = {
        "add_friends_page": ["添加朋友", "推荐好友", "你可能认识的人"],
        "contacts_page": ["通讯录", "联系人", "手机联系人", "同步通讯录"]
    }
    
    def __init__(self, adb_interface: ADBInterface):
        """初始化添加朋友检测器
        
        Args:
            adb_interface: ADB接口实例
        """
        self.logger = logging.getLogger(__name__)
        self.adb = adb_interface
        self.ui_analyzer = UIAnalyzer()
        self.text_matcher = IntelligentTextMatcher()
        self.ui_context = UIContextAnalyzer()
        
        # 配置参数
        self.click_timeout = 3  # 点击后等待时间(秒)
        self.detection_max_attempts = 3  # 最大检测尝试次数
        self.page_load_wait = 2  # 页面加载等待时间(秒)
        
        # 缓存机制
        self.cached_add_friend_position = None
        self.cached_contacts_position = None
        self.last_cache_time = 0
        self.cache_validity_duration = 30  # 缓存有效期(秒)

    def detect_add_friend_button(self) -> Optional[Dict[str, Any]]:
        """检测"添加朋友"按钮"""
        self.logger.info("开始检测'添加朋友'按钮...")
        
        # 添加UI上下文分析
        xml_content = self.adb.get_ui_xml()
        if xml_content:
            context = self.ui_context.analyze_current_context(xml_content)
            self.ui_context.print_context_info(context, "添加朋友检测器")
        
        for attempt in range(self.detection_max_attempts):
            self.logger.info("第%d次尝试检测'添加朋友'按钮", attempt + 1)
            
            # 方法1: 使用完整UI分析
            add_friend_button = self._find_add_friend_with_ui_analysis()
            if add_friend_button:
                self.logger.info("✅ 通过UI分析找到'添加朋友'按钮")
                return add_friend_button
            
            # 方法2: 使用缓存验证（如果有的话）
            if self.cached_add_friend_position:
                add_friend_button = self._verify_cached_add_friend_position()
                if add_friend_button:
                    self.logger.info("✅ 通过缓存验证找到'添加朋友'按钮")
                    return add_friend_button
            
            # 方法3: 使用传统文本匹配（后备）
            add_friend_button = self._find_add_friend_by_text()
            if add_friend_button:
                self.logger.info("✅ 通过文本匹配找到'添加朋友'按钮")
                return add_friend_button
            
            if attempt < self.detection_max_attempts - 1:
                self.logger.warning("第%d次检测失败，等待2秒后重试", attempt + 1)
                time.sleep(2)
        
        self.logger.error("❌ 所有方法都无法找到'添加朋友'按钮")
        return None

    def _find_add_friend_with_ui_analysis(self) -> Optional[Dict[str, Any]]:
        """使用UI分析方法查找添加朋友按钮"""
        try:
            ui_content = self.adb.get_ui_xml()
            if not ui_content:
                return None
            
            # 直接解析XML查找添加朋友按钮
            import xml.etree.ElementTree as ET
            root = ET.fromstring(ui_content)
            
            # 查找所有可点击元素，特别关注content-desc和text
            candidate_buttons = []
            
            for elem in root.iter():
                if elem.get('clickable') != 'true':
                    continue
                
                text = elem.get('text', '').strip()
                content_desc = elem.get('content-desc', '').strip()
                bounds = elem.get('bounds', '')
                
                # 检查是否包含"添加朋友"关键词
                is_add_friend = False
                matched_text = ""
                
                if '添加朋友' in text:
                    is_add_friend = True
                    matched_text = text
                elif '添加朋友' in content_desc:
                    is_add_friend = True
                    matched_text = content_desc
                elif any(keyword in text for keyword in self.ADD_FRIEND_KEYWORDS):
                    is_add_friend = True
                    matched_text = text
                elif any(keyword in content_desc for keyword in self.ADD_FRIEND_KEYWORDS):
                    is_add_friend = True
                    matched_text = content_desc
                
                if is_add_friend:
                    # 解析bounds获取中心点
                    center = self._parse_bounds_to_center(bounds)
                    if center:
                        candidate_buttons.append({
                            'center': center,
                            'text': text,
                            'content_desc': content_desc,
                            'bounds': bounds,
                            'matched_text': matched_text,
                            'element': elem
                        })
            
            if not candidate_buttons:
                return None
            
            # 选择最佳的添加朋友按钮（优先选择左上角区域的）
            best_button = self._select_best_add_friend_from_candidates(
                candidate_buttons)
            if not best_button:
                return None
            
            center = best_button['center']
            
            # 验证按钮位置合理性（左上角区域）
            if not self._verify_add_friend_position(center):
                return None
            
            # 缓存验证通过的位置
            self.cached_add_friend_position = center
            self.last_cache_time = time.time()
            
            self.logger.info("找到添加朋友按钮: 位置%s, 文本='%s', 描述='%s'", 
                           center, best_button['text'], best_button['content_desc'])
            
            return {
                'center': center,
                'text': best_button['text'],
                'content_desc': best_button['content_desc'],
                'bounds': best_button['bounds'],
                'detection_method': 'ui_analysis_improved'
            }
            
        except Exception as e:
            self.logger.error("UI分析方法异常: %s", str(e))
            return None

    def _parse_bounds_to_center(self, bounds_str: str) -> Optional[tuple]:
        """解析bounds字符串为中心点坐标"""
        try:
            if not bounds_str or not bounds_str.startswith('['):
                return None
            
            # 解析格式如: "[32,48][224,152]"
            parts = bounds_str.replace('[', '').replace(']', ',').split(',')
            if len(parts) < 4:
                return None
            
            x1, y1, x2, y2 = map(int, parts[:4])
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            return (center_x, center_y)
            
        except Exception as e:
            self.logger.debug("解析bounds失败: %s, 错误: %s", bounds_str, str(e))
            return None

    def _select_best_add_friend_from_candidates(self,
                                                candidates: List) -> Optional[Dict]:
        """从候选按钮中选择最佳的添加朋友按钮"""
        if not candidates:
            return None
        
        # 优先级评分：左上角区域优先，content-desc优先于text
        def get_priority_score(candidate):
            center = candidate['center']
            x, y = center
            
            # 基础分数：左上角优先（y坐标越小越好，x坐标适中）
            position_score = y * 1000 + abs(x - 128)  # 假设理想x坐标是128
            
            # 加分项：有content-desc的优先
            if candidate['content_desc']:
                position_score -= 10000  # 大幅减分表示优先
            
            # 加分项：text内容匹配度
            if candidate['text'] and '添加朋友' in candidate['text']:
                position_score -= 5000
            
            return position_score
        
        # 排序并选择最佳候选
        candidates.sort(key=get_priority_score)
        return candidates[0]

    def _select_best_add_friend_button(self, buttons: List) -> Optional[Any]:
        """选择最佳的添加朋友按钮（优先左上角）"""
        if not buttons:
            return None
        
        # 按位置排序，优先左上角（y坐标小，x坐标小）
        def get_priority_score(button):
            center = button.get_center()
            if not center:
                return float('inf')
            x, y = center
            # 左上角区域优先级更高（分数越小越好）
            return y * 1000 + x
        
        sorted_buttons = sorted(buttons, key=get_priority_score)
        return sorted_buttons[0] if sorted_buttons else None

    def _verify_add_friend_position(self, position: tuple) -> bool:
        """验证添加朋友按钮位置的合理性（应该在左上角区域）"""
        if not position or len(position) != 2:
            return False
        
        x, y = position
        
        # 检查坐标范围合理性
        if x < 0 or y < 0 or x > 2000 or y > 3000:
            self.logger.warning("添加朋友按钮坐标超出合理范围: (%d, %d)", x, y)
            return False
        
        # 检查是否在左上角区域（通常在屏幕上半部分，左侧或右侧）
        if y > 800:  # 不应该在屏幕下半部分
            self.logger.warning("添加朋友按钮位置过低: y=%d > 800", y)
            return False
        
        return True

    def _verify_cached_add_friend_position(self) -> Optional[Dict[str, Any]]:
        """验证缓存的添加朋友按钮位置"""
        try:
            # 检查缓存是否过期
            if time.time() - self.last_cache_time > self.cache_validity_duration:
                self.logger.debug("添加朋友按钮缓存已过期，清除缓存")
                self.cached_add_friend_position = None
                return None
            
            # 验证缓存位置是否仍然有效
            if not self._verify_add_friend_position(self.cached_add_friend_position):
                self.logger.debug("缓存的添加朋友按钮位置验证失败")
                self.cached_add_friend_position = None
                return None
            
            return {
                'center': self.cached_add_friend_position,
                'text': '添加朋友',
                'content_desc': '',
                'bounds': None,
                'detection_method': 'cached'
            }
            
        except Exception as e:
            self.logger.error("缓存验证异常: %s", str(e))
            return None

    def _find_add_friend_by_text(self) -> Optional[Dict[str, Any]]:
        """使用智能文本匹配查找添加朋友按钮（后备方法）"""
        try:
            ui_content = self.adb.get_ui_xml()
            if not ui_content:
                return None
            
            self.ui_analyzer.parse_xml(ui_content)
            
            # 收集所有可点击元素的文本
            all_clickable_texts = []
            for element in self.ui_analyzer.elements:
                if element.clickable:
                    # 检查文本和描述
                    texts_to_check = []
                    if element.text:
                        texts_to_check.append(element.text.strip())
                    if element.content_desc:
                        texts_to_check.append(element.content_desc.strip())
                    
                    for text in texts_to_check:
                        if text:
                            all_clickable_texts.append((text, element))
            
            # 使用智能匹配器批量匹配
            matches = []
            for text, element in all_clickable_texts:
                is_match, score, method = self.text_matcher.intelligent_match(
                    text, "add_friend")
                if is_match:
                    matches.append((element, score, method, text))
            
            # 选择最佳匹配
            if matches:
                # 按分数排序，选择最高分的
                matches.sort(key=lambda x: x[1], reverse=True)
                best_element, score, method, matched_text = matches[0]
                
                center = best_element.get_center()
                if center and self._verify_add_friend_position(center):
                    self.logger.info(
                        "智能匹配成功: 文本='%s', 分数=%.2f, 方法=%s", 
                        matched_text, score, method)
                    return {
                        'center': center,
                        'text': best_element.text or matched_text,
                        'content_desc': best_element.content_desc or '',
                        'bounds': best_element.bounds,
                        'detection_method': f'intelligent_{method}',
                        'match_score': score
                    }
            
            # 传统关键词匹配作为最后的后备
            for keyword in self.ADD_FRIEND_KEYWORDS:
                elements = self.ui_analyzer.find_elements_by_text(
                    [keyword], clickable_only=True)
                
                for element in elements:
                    center = element.get_center()
                    if center and self._verify_add_friend_position(center):
                        return {
                            'center': center,
                            'text': element.text or keyword,
                            'content_desc': element.content_desc or '',
                            'bounds': element.bounds,
                            'detection_method': 'traditional_text_match'
                        }
            
            return None
            
        except Exception as e:
            self.logger.error("智能文本匹配方法异常: %s", str(e))
            return None

    def navigate_to_add_friends_safely(self) -> bool:
        """安全导航到添加朋友页面"""
        self.logger.info("开始安全导航到添加朋友页面...")
        
        # 检查当前是否已经在添加朋友页面
        if self.is_on_add_friends_page():
            self.logger.info("✅ 已经在添加朋友页面")
            return True
        
        # 检测并点击添加朋友按钮
        add_friend_button = self.detect_add_friend_button()
        if not add_friend_button:
            self.logger.error("❌ 无法找到添加朋友按钮")
            return False
        
        # 执行点击
        center = add_friend_button['center']
        self.logger.info("正在安全点击'添加朋友'按钮: %s", center)
        
        if not self.adb.tap_element(center):
            self.logger.error("❌ 点击添加朋友按钮失败")
            return False
        
        self.logger.info("✅ '添加朋友'按钮点击成功")
        
        # 等待页面加载
        time.sleep(self.click_timeout)
        
        # 验证是否成功导航到添加朋友页面
        if self.is_on_add_friends_page():
            self.logger.info("✅ 成功导航到添加朋友页面")
            return True
        else:
            self.logger.warning("⚠️ 点击成功但可能未到达添加朋友页面")
            return False

    def is_on_add_friends_page(self) -> bool:
        """检查当前是否在添加朋友页面"""
        try:
            # 方法1: 检查Activity
            current_activity = self.adb.get_current_activity()
            if current_activity:
                for pattern in self.ADD_FRIENDS_ACTIVITIES:
                    if pattern in current_activity:
                        self.logger.debug("通过Activity确认在添加朋友页面: %s", 
                                        current_activity)
                        return True
            
            # 方法2: 检查UI内容
            ui_content = self.adb.get_ui_xml()
            if ui_content:
                page_indicators = self.PAGE_INDICATORS["add_friends_page"]
                found_indicators = [indicator for indicator in page_indicators 
                                  if indicator in ui_content]
                
                if found_indicators:
                    self.logger.debug("通过UI内容确认在添加朋友页面，找到指示: %s", 
                                    found_indicators)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error("检查添加朋友页面状态异常: %s", str(e))
            return False

    def detect_contacts_button(self) -> Optional[Dict[str, Any]]:
        """检测"通讯录"按钮"""
        self.logger.info("开始检测'通讯录'按钮...")
        
        try:
            ui_content = self.adb.get_ui_xml()
            if not ui_content:
                return None
            
            # 添加UI上下文分析
            context = self.ui_context.analyze_current_context(ui_content)
            self.ui_context.print_context_info(context, "通讯录检测器")
            
            # 直接解析XML查找通讯录按钮
            import xml.etree.ElementTree as ET
            root = ET.fromstring(ui_content)
            
            # 查找所有包含"通讯录"的元素（包括不可点击的）
            contacts_elements = []
            
            for elem in root.iter():
                text = elem.get('text', '').strip()
                content_desc = elem.get('content-desc', '').strip()
                bounds = elem.get('bounds', '')
                clickable = elem.get('clickable', 'false')
                
                # 检查是否包含"通讯录"关键词
                is_contacts = False
                matched_text = ""
                
                if '通讯录' in text:
                    is_contacts = True
                    matched_text = text
                elif '通讯录' in content_desc:
                    is_contacts = True
                    matched_text = content_desc
                elif any(keyword in text for keyword in self.CONTACTS_KEYWORDS):
                    is_contacts = True
                    matched_text = text
                elif any(keyword in content_desc for keyword in self.CONTACTS_KEYWORDS):
                    is_contacts = True
                    matched_text = content_desc
                
                if is_contacts:
                    center = self._parse_bounds_to_center(bounds)
                    if center:
                        contacts_elements.append({
                            'center': center,
                            'text': text,
                            'content_desc': content_desc,
                            'bounds': bounds,
                            'clickable': clickable == 'true',
                            'matched_text': matched_text,
                            'element': elem
                        })
            
            if not contacts_elements:
                self.logger.warning("未找到任何包含'通讯录'的元素")
                return None
            
            # 如果找到可点击的通讯录按钮，优先选择
            clickable_contacts = [elem for elem in contacts_elements if elem['clickable']]
            if clickable_contacts:
                best_button = clickable_contacts[0]  # 选择第一个可点击的
                self.logger.info("✅ 找到可点击的通讯录按钮")
            else:
                # 如果没有可点击的，寻找最大的区域（可能是容器）
                largest_area_button = None
                max_area = 0
                
                for elem in contacts_elements:
                    bounds = elem['bounds']
                    try:
                        # 计算区域面积
                        parts = bounds.replace('[', '').replace(']', ',').split(',')
                        if len(parts) >= 4:
                            x1, y1, x2, y2 = map(int, parts[:4])
                            area = (x2 - x1) * (y2 - y1)
                            if area > max_area:
                                max_area = area
                                largest_area_button = elem
                    except:
                        continue
                
                if largest_area_button:
                    best_button = largest_area_button
                    self.logger.info("✅ 找到最大区域的通讯录元素（将点击其中心）")
                else:
                    # 选择位置最合适的（在屏幕下半部分）
                    suitable_buttons = [elem for elem in contacts_elements 
                                      if elem['center'][1] > 500]  # y > 500
                    if suitable_buttons:
                        best_button = suitable_buttons[0]
                        self.logger.info("✅ 找到位置合适的通讯录元素")
                    else:
                        best_button = contacts_elements[0]  # 最后的后备选择
                        self.logger.info("✅ 使用第一个找到的通讯录元素")
            
            center = best_button['center']
            self.logger.info("通讯录按钮信息: 位置%s, 文本='%s', 描述='%s', 可点击=%s", 
                           center, best_button['text'], best_button['content_desc'], 
                           best_button['clickable'])
            
            return {
                'center': center,
                'text': best_button['text'] or best_button['matched_text'],
                'content_desc': best_button['content_desc'],
                'bounds': best_button['bounds'],
                'clickable': best_button['clickable'],
                'detection_method': 'improved_xml_parsing'
            }
            
        except Exception as e:
            self.logger.error("检测通讯录按钮异常: %s", str(e))
            return None

    def navigate_to_contacts_safely(self) -> bool:
        """安全导航到通讯录页面"""
        self.logger.info("开始安全导航到通讯录页面...")
        
        # 检查当前是否已经在通讯录页面
        if self.is_on_contacts_page():
            self.logger.info("✅ 已经在通讯录页面")
            return True
        
        # 检测并点击通讯录按钮
        contacts_button = self.detect_contacts_button()
        if not contacts_button:
            self.logger.error("❌ 无法找到通讯录按钮")
            return False
        
        # 执行点击
        center = contacts_button['center']
        self.logger.info("正在安全点击'通讯录'按钮: %s", center)
        
        if not self.adb.tap_element(center):
            self.logger.error("❌ 点击通讯录按钮失败")
            return False
        
        self.logger.info("✅ '通讯录'按钮点击成功")
        
        # 等待页面加载
        time.sleep(self.click_timeout)
        
        # 验证是否成功导航到通讯录页面
        if self.is_on_contacts_page():
            self.logger.info("✅ 成功导航到通讯录页面")
            return True
        else:
            self.logger.warning("⚠️ 点击成功但可能未到达通讯录页面")
            return False

    def is_on_contacts_page(self) -> bool:
        """检查当前是否在通讯录页面"""
        try:
            ui_content = self.adb.get_ui_xml()
            if ui_content:
                page_indicators = self.PAGE_INDICATORS["contacts_page"]
                found_indicators = [indicator for indicator in page_indicators 
                                  if indicator in ui_content]
                
                if found_indicators:
                    self.logger.debug("通过UI内容确认在通讯录页面，找到指示: %s", 
                                    found_indicators)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error("检查通讯录页面状态异常: %s", str(e))
            return False

    def get_detection_status(self) -> Dict[str, Any]:
        """获取检测状态信息"""
        try:
            ui_available = bool(self.adb.get_ui_xml())
            
            return {
                "ui_available": ui_available,
                "add_friend_button_cached": bool(self.cached_add_friend_position),
                "contacts_button_cached": bool(self.cached_contacts_position),
                "cache_valid": (time.time() - self.last_cache_time < 
                               self.cache_validity_duration),
                "on_add_friends_page": self.is_on_add_friends_page(),
                "on_contacts_page": self.is_on_contacts_page(),
                "detection_attempts_max": self.detection_max_attempts
            }
            
        except Exception as e:
            self.logger.error("获取检测状态异常: %s", str(e))
            return {"error": str(e)}