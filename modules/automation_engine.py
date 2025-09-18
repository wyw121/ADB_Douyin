"""自动化引擎模块 - 核心自动化逻辑和导航控制"""

import logging
import time
from typing import Dict, List, Optional

from .adb_interface import ADBInterface
from .ui_intelligence import UIAnalyzer


class AutomationEngine:
    """自动化引擎类，负责执行具体的自动化操作"""
    
    def __init__(self, device_id: Optional[str] = None):
        """初始化自动化引擎
        
        Args:
            device_id: 设备ID
        """
        self.adb = ADBInterface(device_id)
        self.ui_analyzer = UIAnalyzer()
        self.logger = logging.getLogger(__name__)
        
        # 配置参数
        self.operation_delay = 2.0
        self.max_retries = 3
        self.scroll_duration = 500
        
        # 缓存已检测到的UI元素位置
        self.cached_profile_button_pos = None

    def check_connection(self) -> bool:
        """检查设备连接状态"""
        return self.adb.check_connection()

    def force_restart_douyin(self) -> bool:
        """强制关闭并重新启动抖音应用"""
        self.logger.info("强制关闭抖音应用...")
        
        # 先强制停止应用
        stop_success = self.adb.stop_app()
        if stop_success:
            self.logger.info("抖音应用已关闭")
            # 等待应用完全关闭
            time.sleep(3)
        else:
            self.logger.warning("关闭抖音失败，继续尝试启动")
        
        # 再启动应用
        return self.start_douyin()

    def start_douyin(self) -> bool:
        """启动抖音应用"""
        self.logger.info("启动抖音应用...")
        success = self.adb.start_app()
        if success:
            # 等待应用完全启动并检查主界面
            return self.wait_for_main_interface()
        
        return False
        
    def wait_for_main_interface(self) -> bool:
        """等待抖音主界面完全加载，包含启动画面检测"""
        self.logger.info("等待抖音主界面加载...")
        
        # 使用ADB接口的智能等待方法
        if self.adb.wait_for_douyin_main_interface(timeout=30):
            # 主界面加载完成后，尝试检测和缓存"我"按钮位置
            if self.get_current_ui():
                # 使用新的验证方法检测"我"按钮
                is_valid, profile_button = (
                    self.ui_analyzer.verify_profile_button_in_navigation())
                
                if is_valid and profile_button:
                    self.cached_profile_button_pos = profile_button['center']
                    self.logger.info("✅ 验证并缓存了导航栏'我'按钮位置: %s",
                                   self.cached_profile_button_pos)
                    return True
                else:
                    # 尝试旧方法作为后备
                    if self.ui_analyzer.has_bottom_navigation_profile_button():
                        self.cached_profile_button_pos = (
                            self.ui_analyzer.get_profile_button_position())
                        self.logger.info("✅ 使用后备方法缓存'我'按钮位置")
                        return True
            
            # 即使无法缓存按钮位置，主界面已加载完成
            self.logger.info("✅ 主界面已加载，但未能缓存'我'按钮位置")
            return True
        else:
            self.logger.warning("⚠️ 主界面加载超时，但继续执行流程")
            return True

    def stop_douyin(self) -> bool:
        """停止抖音应用"""
        self.logger.info("停止抖音应用...")
        return self.adb.stop_app()

    def get_current_ui(self) -> bool:
        """获取并解析当前UI"""
        xml_content = self.adb.get_ui_xml()
        if xml_content:
            return self.ui_analyzer.parse_xml(xml_content)
        return False

    def find_and_click_element(self, keywords: List[str], 
                              exact_match: bool = False) -> bool:
        """查找并点击元素
        
        Args:
            keywords: 搜索关键词
            exact_match: 是否精确匹配
            
        Returns:
            是否点击成功
        """
        if not self.get_current_ui():
            self.logger.error("无法获取UI信息")
            return False

        # 查找匹配的元素
        elements = self.ui_analyzer.find_elements_by_text(keywords)
        
        if exact_match and elements:
            elements = self._filter_exact_matches(elements, keywords)

        if not elements:
            self.logger.warning("未找到匹配元素: %s", keywords)
            return False

        # 查找可点击元素
        clickable_element = self._find_clickable_element(elements)
        
        if not clickable_element:
            # 尝试查找可点击的父元素
            clickable_element = self._find_clickable_parent(elements)

        if clickable_element:
            return self._click_element(clickable_element)
        else:
            self.logger.warning("找到元素但无法点击: %s", keywords)
            return False

    def _filter_exact_matches(self, elements, keywords):
        """筛选精确匹配的元素"""
        exact_elements = []
        for element in elements:
            element_text = (element.text + " " + element.content_desc).strip()
            for keyword in keywords:
                if keyword == element_text:
                    exact_elements.append(element)
                    break
        return exact_elements

    def _find_clickable_element(self, elements):
        """查找第一个可点击元素"""
        for element in elements:
            if element.is_clickable_element():
                return element
        return None

    def _find_clickable_parent(self, elements):
        """查找包含指定元素的可点击父元素"""
        for text_element in elements:
            text_bounds = text_element.bounds
            if not text_bounds:
                continue

            # 查找包含此文本元素的可点击元素
            for clickable_element in self.ui_analyzer.elements:
                if not clickable_element.is_clickable_element():
                    continue

                clickable_bounds = clickable_element.bounds
                if not clickable_bounds:
                    continue

                # 检查是否包含
                if self._bounds_contains(clickable_bounds, text_bounds):
                    self.logger.info("找到包含文本的可点击父元素")
                    return clickable_element

        return None

    def _bounds_contains(self, parent_bounds, child_bounds):
        """检查父边界是否包含子边界"""
        return (parent_bounds[0] <= child_bounds[0] and
                parent_bounds[1] <= child_bounds[1] and
                parent_bounds[2] >= child_bounds[2] and
                parent_bounds[3] >= child_bounds[3])

    def _click_element(self, element):
        """点击指定元素"""
        center = element.get_center()
        if center:
            element_desc = element.text or element.content_desc or "未知元素"
            self.logger.info("点击元素: %s at %s", element_desc, center)
            success = self.adb.tap(center[0], center[1])
            if success:
                time.sleep(self.operation_delay)
            return success
        return False

    def navigate_to_profile(self) -> bool:
        """导航到个人资料页面"""
        self.logger.info("导航到个人资料页面...")

        for attempt in range(self.max_retries):
            self.logger.info("第 %d 次尝试导航", attempt + 1)
            
            # 策略1: 验证导航栏结构并使用安全坐标
            if self._try_verified_navigation():
                if self._verify_profile_page():
                    return True
            
            # 策略2: 使用缓存的"我"按钮位置（需要验证安全性）
            if (self.cached_profile_button_pos and 
                    self._verify_cached_coordinate_safety()):
                self.logger.info("使用验证过的缓存坐标: %s",
                               self.cached_profile_button_pos)
                success = self.adb.tap(self.cached_profile_button_pos[0],
                                      self.cached_profile_button_pos[1])
                if success:
                    time.sleep(3)  # 等待页面加载
                    if self._verify_profile_page():
                        return True
            
            # 策略2: 查找"我"标签
            if self._try_find_profile_tab():
                if self._verify_profile_page():
                    return True
                    
            # 策略3: 尝试底部最右侧点击
            if attempt == self.max_retries - 1:
                if self._try_rightmost_bottom_click():
                    if self._verify_profile_page():
                        return True

            time.sleep(1)

        self.logger.error("导航到个人资料失败")
        return False

    def _try_find_profile_tab(self) -> bool:
        """尝试查找并点击个人资料标签"""
        profile_keywords = ["我", "Me", "Profile"]
        
        # 方法1: 直接查找
        if self.find_and_click_element(profile_keywords):
            time.sleep(2)
            return True
            
        # 方法2: 查找底部导航区域
        if not self.get_current_ui():
            return False
            
        screen_size = self.adb.get_screen_size()
        if not screen_size:
            return False
            
        width, height = screen_size
        bottom_threshold = height * 0.8
        
        # 查找底部区域的"我"元素
        elements = self.ui_analyzer.find_elements_by_text(
            profile_keywords, clickable_only=True)
            
        for element in elements:
            center = element.get_center()
            if center and center[1] > bottom_threshold:
                if self._click_element(element):
                    time.sleep(2)
                    return True
                    
        return False

    def _try_rightmost_bottom_click(self) -> bool:
        """尝试点击底部最右侧元素"""
        screen_size = self.adb.get_screen_size()
        if not screen_size:
            return False
            
        width, height = screen_size
        # 尝试经验位置：右下角导航区域
        x = int(width * 0.9)
        y = int(height * 0.95)
        
        self.logger.info("尝试点击经验位置: (%d, %d)", x, y)
        success = self.adb.tap(x, y)
        if success:
            time.sleep(2)
        return success

    def _verify_profile_page(self) -> bool:
        """验证是否在个人资料页面"""
        if not self.get_current_ui():
            return False
            
        # 个人资料页面的特征文本
        profile_indicators = [
            "添加朋友", "编辑资料", "关注", "粉丝",
            "Add Friends", "Edit Profile", "Following", "Followers"
        ]
        
        found_elements = self.ui_analyzer.find_elements_by_text(
            profile_indicators)
        
        if found_elements:
            self.logger.info("验证成功：在个人资料页面")
            return True
        else:
            self.logger.warning("验证失败：不在个人资料页面")
            return False

    def navigate_to_add_friends(self) -> bool:
        """导航到添加朋友页面"""
        self.logger.info("导航到添加朋友页面...")
        
        # 等待页面加载
        time.sleep(2)
        
        add_friend_keywords = ["添加朋友", "添加好友", "加朋友", "Add Friends"]
        return self.find_and_click_element(add_friend_keywords)

    def navigate_to_contacts(self) -> bool:
        """导航到通讯录页面"""
        self.logger.info("导航到通讯录页面...")
        
        # 等待页面加载
        time.sleep(2)
        
        contacts_keywords = ["通讯录", "联系人", "Contacts", "通信录"]
        return self.find_and_click_element(contacts_keywords)

    def get_contact_list(self) -> List[Dict]:
        """获取通讯录联系人列表"""
        self.logger.info("获取通讯录联系人列表...")
        
        if not self.get_current_ui():
            return []

        # 使用UI分析器查找抖音特定元素
        douyin_elements = self.ui_analyzer.find_douyin_specific_elements()
        contact_items = douyin_elements.get("contact_items", [])
        follow_buttons = douyin_elements.get("follow_buttons", [])

        contacts = []
        
        # 匹配联系人和关注按钮
        for contact in contact_items:
            contact_center = contact.get_center()
            if not contact_center:
                continue

            # 查找最近的关注按钮
            nearest_button = self._find_nearest_follow_button(
                contact_center, follow_buttons)

            contact_info = {
                "name": contact.text or contact.content_desc or "未知联系人",
                "element": contact,
                "center": contact_center,
                "follow_button": nearest_button,
                "can_follow": nearest_button is not None,
            }
            contacts.append(contact_info)

        self.logger.info("找到 %d 个联系人", len(contacts))
        return contacts

    def _find_nearest_follow_button(self, contact_center, follow_buttons):
        """查找最近的关注按钮"""
        nearest_button = None
        min_distance = float("inf")

        for button in follow_buttons:
            button_center = button.get_center()
            if button_center:
                # 计算距离（主要考虑垂直距离）
                distance = abs(contact_center[1] - button_center[1])
                if distance < min_distance and distance < 100:  # 100像素范围内
                    min_distance = distance
                    nearest_button = button

        return nearest_button

    def follow_contact(self, contact_info: Dict) -> bool:
        """关注指定联系人"""
        if not contact_info.get("can_follow"):
            self.logger.warning("联系人 %s 无法关注", 
                              contact_info.get("name", "未知"))
            return False

        follow_button = contact_info["follow_button"]
        return self._click_element(follow_button)

    def scroll_down(self) -> bool:
        """向下滚动页面"""
        screen_size = self.adb.get_screen_size()
        if not screen_size:
            return False
            
        width, height = screen_size
        start_y = int(height * 0.7)
        end_y = int(height * 0.3)
        center_x = width // 2

        self.logger.debug("向下滚动页面")
        return self.adb.swipe(center_x, start_y, center_x, end_y, 
                             self.scroll_duration)

    def wait_for_element(self, text: str, timeout: int = 10) -> bool:
        """等待指定元素出现"""
        return self.adb.wait_for_element_text(text, timeout)

    def analyze_current_screen(self) -> bool:
        """分析当前屏幕"""
        self.logger.info("分析当前屏幕...")
        
        if not self.get_current_ui():
            return False
            
        # 生成分析报告
        self.ui_analyzer.print_analysis_summary()
        
        # 保存详细报告
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_filename = f"screen_analysis_{timestamp}.txt"
        self.ui_analyzer.save_analysis_report(report_filename)
        
        return True

    def _try_verified_navigation(self) -> bool:
        """尝试使用验证的导航栏检测"""
        if not self.get_current_ui():
            return False
        
        # 验证'我'按钮是否在导航栏结构中
        is_valid, profile_button = (
            self.ui_analyzer.verify_profile_button_in_navigation())
        
        if not is_valid or not profile_button:
            self.logger.debug("未找到有效的导航栏'我'按钮")
            return False
        
        position = profile_button['center']
        
        # 验证坐标安全性
        if not self._verify_coordinate_safety(position):
            self.logger.warning("检测到的坐标未通过安全验证")
            return False
        
        # 缓存验证过的坐标
        self.cached_profile_button_pos = position
        self.logger.info("使用验证的导航栏'我'按钮: %s", position)
        
        return self.adb.tap(position[0], position[1])

    def _verify_coordinate_safety(self, position):
        """验证坐标的安全性"""
        if not position or len(position) != 2:
            return False
        
        x, y = position
        
        # 检查坐标是否在合理范围内
        if x < 0 or y < 0 or x > 2000 or y > 3000:
            self.logger.warning("坐标超出合理范围: (%d, %d)", x, y)
            return False
        
        # 检查是否在底部导航区域（动态计算）
        screen_size = self.adb.get_screen_size()
        if screen_size:
            _, screen_height = screen_size
            nav_threshold = screen_height - 200  # 底部200像素区域
            if y < nav_threshold:
                self.logger.warning("坐标不在底部导航区域: y=%d (阈值:%d)",
                                  y, nav_threshold)
                return False
        else:
            # 如果无法获取屏幕尺寸，使用固定阈值
            if y < 1400:
                self.logger.warning("坐标不在底部导航区域: y=%d", y)
                return False
        
        return True

    def _verify_cached_coordinate_safety(self):
        """验证缓存坐标的安全性"""
        if not self.cached_profile_button_pos:
            return False
        
        # 基本坐标验证
        if not self._verify_coordinate_safety(self.cached_profile_button_pos):
            self.logger.warning("缓存坐标未通过基本安全检查")
            return False
        
        # 尝试与当前导航栏结构比较
        try:
            if self.get_current_ui():
                nav_structure = (
                    self.ui_analyzer.analyze_bottom_navigation_structure())
                
                if nav_structure and nav_structure['is_valid_navigation']:
                    container_bounds = nav_structure['container_bounds']
                    if container_bounds:
                        return self._check_coordinate_in_container(
                            self.cached_profile_button_pos, container_bounds)
        except (AttributeError, TypeError, ValueError) as e:
            self.logger.warning("验证缓存坐标时出错: %s", str(e))
        
        # 如果无法验证结构，至少确保基本坐标合理
        return True

    def _check_coordinate_in_container(self, position, container_bounds):
        """检查坐标是否在容器范围内"""
        x, y = position
        min_x, min_y, max_x, max_y = container_bounds
        
        # 允许一定的容差（扩展边界20像素）
        tolerance = 20
        in_bounds = (min_x - tolerance <= x <= max_x + tolerance and
                     min_y - tolerance <= y <= max_y + tolerance)
        
        if in_bounds:
            self.logger.debug("缓存坐标在导航容器范围内")
        else:
            self.logger.warning("缓存坐标(%d,%d)不在导航容器(%s)范围内",
                               x, y, container_bounds)
        
        return in_bounds