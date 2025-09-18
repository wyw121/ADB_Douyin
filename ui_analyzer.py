"""UI元素分析模块。

用于解析Android界面的XML结构，智能识别按钮和控件位置。
"""
import xml.etree.ElementTree as ET
import re
import time
from typing import List, Dict, Optional, Tuple
import logging


class UIElement:
    """UI元素类"""
    
    def __init__(self, node: ET.Element):
        """
        初始化UI元素
        
        Args:
            node: XML节点
        """
        self.node = node
        self.tag = node.tag
        self.attributes = node.attrib
        self.text = self.attributes.get('text', '')
        self.content_desc = self.attributes.get('content-desc', '')
        self.resource_id = self.attributes.get('resource-id', '')
        self.class_name = self.attributes.get('class', '')
        self.bounds = self._parse_bounds()
        clickable_attr = self.attributes.get('clickable', 'false')
        self.clickable = clickable_attr.lower() == 'true'
        self.enabled = self.attributes.get('enabled', 'true').lower() == 'true'
        self.children = []
    
    def _parse_bounds(self) -> Optional[Tuple[int, int, int, int]]:
        """解析边界坐标"""
        bounds_str = self.attributes.get('bounds', '')
        if bounds_str:
            # 格式: [x1,y1][x2,y2]
            pattern = r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]'
            match = re.match(pattern, bounds_str)
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                return (x1, y1, x2, y2)
        return None
    
    def get_center(self) -> Optional[Tuple[int, int]]:
        """获取元素中心坐标"""
        if self.bounds:
            x1, y1, x2, y2 = self.bounds
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            return (center_x, center_y)
        return None
    
    def contains_text(self, keywords: List[str],
                      ignore_case: bool = True) -> bool:
        """检查元素是否包含指定关键词"""
        combined_text = self.text + ' ' + self.content_desc
        search_text = combined_text.lower() if ignore_case else combined_text
        for keyword in keywords:
            search_keyword = keyword.lower() if ignore_case else keyword
            if search_keyword in search_text:
                return True
        return False
    
    def is_clickable_element(self) -> bool:
        """判断是否为可点击元素"""
        return self.clickable and self.enabled and self.bounds is not None
    
    def __str__(self):
        center = self.get_center()
        return (f"UIElement(class={self.class_name}, text='{self.text}', "
                f"desc='{self.content_desc}', center={center}, "
                f"clickable={self.clickable})")


class UIAnalyzer:
    """UI分析器"""
    
    def __init__(self):
        """初始化UI分析器"""
        self.logger = self._setup_logger()
        self.elements = []
        self.xml_content = None
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('UIAnalyzer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def parse_xml(self, xml_content: str) -> bool:
        """
        解析XML内容
        
        Args:
            xml_content: XML字符串
            
        Returns:
            是否解析成功
        """
        try:
            self.xml_content = xml_content
            root = ET.fromstring(xml_content)
            self.elements = []
            self._parse_node(root)
            self.logger.info(f"解析UI XML成功，共找到 {len(self.elements)} 个元素")
            return True
        except Exception as e:
            self.logger.error(f"解析XML失败: {str(e)}")
            return False
    
    def _parse_node(self, node: ET.Element):
        """递归解析XML节点"""
        element = UIElement(node)
        self.elements.append(element)
        
        # 递归解析子节点
        for child in node:
            self._parse_node(child)
    
    def find_elements_by_text(self, keywords: List[str],
                              clickable_only: bool = True) -> List[UIElement]:
        """
        根据文本关键词查找元素
        
        Args:
            keywords: 关键词列表
            clickable_only: 是否只返回可点击元素
            
        Returns:
            匹配的元素列表
        """
        matches = []
        for element in self.elements:
            if element.contains_text(keywords):
                if not clickable_only or element.is_clickable_element():
                    matches.append(element)
        
        self.logger.info(f"根据关键词 {keywords} 找到 {len(matches)} 个匹配元素")
        return matches
    
    def find_elements_by_class(self,
                               class_names: List[str]) -> List[UIElement]:
        """
        根据类名查找元素
        
        Args:
            class_names: 类名列表
            
        Returns:
            匹配的元素列表
        """
        matches = []
        for element in self.elements:
            for class_name in class_names:
                if class_name in element.class_name:
                    matches.append(element)
                    break
        
        self.logger.info(f"根据类名 {class_names} 找到 {len(matches)} 个匹配元素")
        return matches
    
    def find_elements_by_resource_id(self,
                                     resource_ids: List[str]
                                     ) -> List[UIElement]:
        """
        根据资源ID查找元素
        
        Args:
            resource_ids: 资源ID列表
            
        Returns:
            匹配的元素列表
        """
        matches = []
        for element in self.elements:
            for resource_id in resource_ids:
                if resource_id in element.resource_id:
                    matches.append(element)
                    break
        
        self.logger.info(f"根据资源ID {resource_ids} 找到 {len(matches)} 个匹配元素")
        return matches
    
    def find_navigation_elements(self) -> Dict[str, List[UIElement]]:
        """
        查找导航相关元素
        
        Returns:
            按类型分组的导航元素
        """
        navigation_elements = {
            'bottom_tabs': [],  # 底部标签
            'back_buttons': [],  # 返回按钮
            'menu_buttons': [],  # 菜单按钮
            'action_buttons': []  # 动作按钮
        }
        
        # 查找底部导航标签
        bottom_tab_keywords = ['首页', '推荐', '朋友', '我', '消息', '关注', '发现']
        potential_tabs = self.find_elements_by_text(bottom_tab_keywords)
        
        # 过滤出真正的底部标签（通常在屏幕下方）
        screen_height = self._estimate_screen_height()
        if screen_height:
            for element in potential_tabs:
                center = element.get_center()
                if center and center[1] > screen_height * 0.8:  # 在屏幕下方20%区域
                    navigation_elements['bottom_tabs'].append(element)
        
        # 查找返回按钮
        back_keywords = ['返回', '后退', '←', '<']
        back_buttons = self.find_elements_by_text(back_keywords)
        navigation_elements['back_buttons'].extend(back_buttons)
        
        # 查找菜单按钮
        menu_keywords = ['菜单', '更多', '⋮', '…']
        menu_buttons = self.find_elements_by_text(menu_keywords)
        navigation_elements['menu_buttons'].extend(menu_buttons)
        
        # 查找常见的动作按钮
        action_keywords = ['确定', '取消', '保存', '提交', '完成',
                           '下一步', '关注', '添加', '搜索']
        action_buttons = self.find_elements_by_text(action_keywords)
        navigation_elements['action_buttons'].extend(action_buttons)
        
        return navigation_elements
    
    def find_douyin_specific_elements(self) -> Dict[str, List[UIElement]]:
        """
        查找抖音特定的界面元素
        
        Returns:
            抖音相关元素字典
        """
        douyin_elements = {
            'profile_tab': [],      # "我"标签页
            'add_friend_button': [],  # "添加朋友"按钮
            'contacts_button': [],   # "通讯录"按钮
            'follow_buttons': [],    # "关注"按钮
            'contact_items': []      # 通讯录联系人项目
        }
        
        # 查找"我"标签页
        profile_keywords = ['我', 'Me', 'Profile']
        douyin_elements['profile_tab'] = self.find_elements_by_text(
            profile_keywords)
        
        # 查找"添加朋友"按钮
        add_friend_keywords = ['添加朋友', '添加好友', '加朋友', 'Add Friends']
        douyin_elements['add_friend_button'] = self.find_elements_by_text(
            add_friend_keywords)
        
        # 查找"通讯录"按钮
        contacts_keywords = ['通讯录', '联系人', 'Contacts', '通信录']
        douyin_elements['contacts_button'] = self.find_elements_by_text(
            contacts_keywords)
        
        # 查找"关注"按钮
        follow_keywords = ['关注', '+ 关注', 'Follow', '+关注']
        douyin_elements['follow_buttons'] = self.find_elements_by_text(
            follow_keywords)
        
        return douyin_elements

    def find_contact_items(self, text_hints: List[str] = None,
                           class_hints: List[str] = None,
                           resource_ids: List[str] = None
                           ) -> List[UIElement]:
        """查找联系人项目（通过多种策略）"""
        if text_hints is None:
            text_hints = []
        if class_hints is None:
            class_hints = ['android.widget.LinearLayout',
                           'android.widget.RelativeLayout',
                           'android.widget.FrameLayout']
        if resource_ids is None:
            resource_ids = []

        # 通过类名识别可能的联系人项目
        potential_contacts = self.find_elements_by_class(class_hints)
        
        # 过滤出可能的联系人项目（包含姓名相关的文本）
        contact_items = []
        for element in potential_contacts:
            if (element.is_clickable_element() and
                    element.text and len(element.text) > 0):
                # 检查是否像是人名（简单启发式判断）
                if self._looks_like_name(element.text):
                    contact_items.append(element)
        
        return contact_items
    
    def _looks_like_name(self, text: str) -> bool:
        """简单判断文本是否像人名"""
        if not text or len(text) > 10:  # 太长的文本不太可能是人名
            return False
        
        # 排除明显不是人名的文本
        exclude_keywords = [
            '关注', '粉丝', '获赞', '作品', '动态', '私信', '设置', '帮助',
            '点击', '查看', '更多', '推荐', '搜索', '发现', '消息'
        ]
        
        for keyword in exclude_keywords:
            if keyword in text:
                return False
        
        # 简单的中文姓名判断（1-4个汉字）
        chinese_char_count = len(re.findall(r'[\u4e00-\u9fff]', text))
        if 1 <= chinese_char_count <= 4 and chinese_char_count == len(text):
            return True
        
        # 英文姓名判断
        if re.match(r'^[A-Za-z\s]{2,20}$', text):
            return True
        
        return False
    
    def _estimate_screen_height(self) -> Optional[int]:
        """估算屏幕高度"""
        max_y = 0
        for element in self.elements:
            if element.bounds:
                _, _, _, y2 = element.bounds
                max_y = max(max_y, y2)
        return max_y if max_y > 0 else None
    
    def get_best_element_match(self, keywords: List[str],
                               preferred_classes: List[str] = None
                               ) -> Optional[UIElement]:
        """
        获取最佳匹配的元素
        
        Args:
            keywords: 关键词列表
            preferred_classes: 首选的类名列表
            
        Returns:
            最佳匹配的元素或None
        """
        matches = self.find_elements_by_text(keywords)
        
        if not matches:
            return None
        
        if len(matches) == 1:
            return matches[0]
        
        # 如果有多个匹配，尝试根据类名筛选
        if preferred_classes:
            class_matches = []
            for element in matches:
                for class_name in preferred_classes:
                    if class_name in element.class_name:
                        class_matches.append(element)
                        break
            if class_matches:
                matches = class_matches
        
        # 返回第一个匹配（可以根据需要添加更复杂的排序逻辑）
        return matches[0]
    
    def print_analysis_summary(self):
        """打印分析摘要"""
        print("\n=== UI分析摘要 ===")
        print(f"总元素数量: {len(self.elements)}")
        
        clickable_count = sum(1 for e in self.elements
                              if e.is_clickable_element())
        print(f"可点击元素: {clickable_count}")
        
        text_elements = [e for e in self.elements if e.text]
        print(f"包含文本的元素: {len(text_elements)}")
        
        # 显示一些关键元素
        navigation = self.find_navigation_elements()
        print("\n导航元素:")
        for nav_type, elements in navigation.items():
            if elements:
                print(f"  {nav_type}: {len(elements)} 个")
                for element in elements[:3]:  # 只显示前3个
                    center = element.get_center()
                    text = element.text or element.content_desc
                    print(f"    - {text} at {center}")
        
        douyin_elements = self.find_douyin_specific_elements()
        print("\n抖音相关元素:")
        for element_type, elements in douyin_elements.items():
            if elements:
                print(f"  {element_type}: {len(elements)} 个")
                for element in elements[:3]:  # 只显示前3个
                    center = element.get_center()
                    text = element.text or element.content_desc
                    print(f"    - {text} at {center}")
    
    def save_analysis_report(self, filename: str = "ui_analysis.txt"):
        """保存分析报告到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=== UI界面分析报告 ===\n\n")
                f.write(f"分析时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总元素数量: {len(self.elements)}\n\n")
                
                f.write("=== 可点击元素列表 ===\n")
                clickable_elements = [e for e in self.elements
                                      if e.is_clickable_element()]
                for i, element in enumerate(clickable_elements, 1):
                    center = element.get_center()
                    f.write(f"{i}. {element.class_name}\n")
                    f.write(f"   文本: {element.text}\n")
                    f.write(f"   描述: {element.content_desc}\n")
                    f.write(f"   中心坐标: {center}\n")
                    f.write(f"   资源ID: {element.resource_id}\n\n")
                
                f.write("=== 导航元素分析 ===\n")
                navigation = self.find_navigation_elements()
                for nav_type, elements in navigation.items():
                    f.write(f"\n{nav_type}:\n")
                    for element in elements:
                        center = element.get_center()
                        text = element.text or element.content_desc
                        f.write(f"  - {text} at {center}\n")
                
                f.write("\n=== 抖音专用元素分析 ===\n")
                douyin_elements = self.find_douyin_specific_elements()
                for element_type, elements in douyin_elements.items():
                    f.write(f"\n{element_type}:\n")
                    for element in elements:
                        center = element.get_center()
                        text = element.text or element.content_desc
                        f.write(f"  - {text} at {center}\n")
            
            self.logger.info(f"分析报告已保存到: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存分析报告失败: {str(e)}")
            return False


