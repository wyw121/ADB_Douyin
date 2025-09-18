"""UI分析器模块 - 用于解析和分析Android UI结构"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple


class UIElement:
    """UI元素类，表示一个Android UI元素"""

    def __init__(self, node):
        """初始化UI元素
        
        Args:
            node: XML节点
        """
        self.node = node
        self.tag = node.tag
        self.text = node.get('text', '').strip()
        self.content_desc = node.get('content-desc', '').strip()
        self.resource_id = node.get('resource-id', '')
        self.class_name = node.get('class', '')
        self.package = node.get('package', '')
        self.clickable = node.get('clickable', 'false').lower() == 'true'
        self.enabled = node.get('enabled', 'true').lower() == 'true'
        self.focusable = node.get('focusable', 'false').lower() == 'true'
        self.scrollable = node.get('scrollable', 'false').lower() == 'true'
        
        # 解析边界坐标
        self.bounds = self._parse_bounds(node.get('bounds', ''))
        
        # 子元素
        self.children = []

    def _parse_bounds(self, bounds_str: str) -> Optional[
            Tuple[int, int, int, int]]:
        """解析边界坐标字符串
        
        Args:
            bounds_str: 边界字符串，格式如 "[x1,y1][x2,y2]"
            
        Returns:
            (left, top, right, bottom) 或 None
        """
        try:
            if not bounds_str or bounds_str == '':
                return None
                
            # 解析格式如 "[0,0][1080,1920]"
            bounds_str = bounds_str.strip('[]')
            parts = bounds_str.split('][')
            
            if len(parts) != 2:
                return None
                
            left_top = parts[0].split(',')
            right_bottom = parts[1].split(',')
            
            if len(left_top) != 2 or len(right_bottom) != 2:
                return None
                
            left = int(left_top[0])
            top = int(left_top[1])
            right = int(right_bottom[0])
            bottom = int(right_bottom[1])
            
            return (left, top, right, bottom)
            
        except (ValueError, IndexError):
            return None

    def get_center(self) -> Optional[Tuple[int, int]]:
        """获取元素中心坐标
        
        Returns:
            (x, y) 坐标或 None
        """
        if not self.bounds:
            return None
            
        left, top, right, bottom = self.bounds
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        return (center_x, center_y)

    def is_clickable_element(self) -> bool:
        """判断元素是否可点击"""
        return self.clickable and self.enabled

    def contains_text(self, keywords: List[str]) -> bool:
        """检查元素是否包含指定关键词
        
        Args:
            keywords: 关键词列表
            
        Returns:
            是否包含任意关键词
        """
        full_text = (self.text + ' ' + self.content_desc).lower()
        return any(keyword.lower() in full_text for keyword in keywords)

    def get_full_text(self) -> str:
        """获取元素的完整文本内容"""
        parts = []
        if self.text:
            parts.append(self.text)
        if self.content_desc:
            parts.append(self.content_desc)
        return ' '.join(parts)

    def __str__(self) -> str:
        """字符串表示"""
        return (f"UIElement(tag={self.tag}, text='{self.text}', "
                f"desc='{self.content_desc}', clickable={self.clickable})")


class UIAnalyzer:
    """UI分析器类，用于解析和分析Android UI结构"""

    def __init__(self):
        """初始化UI分析器"""
        self.logger = logging.getLogger(__name__)
        self.elements: List[UIElement] = []
        self.root_element: Optional[UIElement] = None
        self.package_name: str = ""

    def parse_xml(self, xml_content: str) -> bool:
        """解析UI XML内容
        
        Args:
            xml_content: UI XML字符串
            
        Returns:
            是否解析成功
        """
        try:
            if not xml_content or xml_content.strip() == '':
                self.logger.error("UI XML内容为空")
                return False

            # 清理之前的解析结果
            self.elements.clear()
            self.root_element = None
            self.package_name = ""

            # 解析XML
            root = ET.fromstring(xml_content)
            
            # 递归解析所有元素
            self._parse_element_recursive(root)
            
            # 检测主要包名
            self._detect_package_name()
            
            self.logger.info("成功解析UI，共 %d 个元素", len(self.elements))
            return True
            
        except ET.ParseError as e:
            self.logger.error("XML解析失败: %s", str(e))
            return False
        except Exception as e:
            self.logger.error("UI解析异常: %s", str(e))
            return False

    def _parse_element_recursive(self, node, parent_element=None):
        """递归解析XML元素
        
        Args:
            node: XML节点
            parent_element: 父UI元素
        """
        # 创建UI元素
        element = UIElement(node)
        
        # 设置根元素
        if self.root_element is None:
            self.root_element = element
            
        # 添加到元素列表
        self.elements.append(element)
        
        # 如果有父元素，添加到父元素的子元素列表
        if parent_element:
            parent_element.children.append(element)
        
        # 递归处理子元素
        for child_node in node:
            self._parse_element_recursive(child_node, element)

    def _detect_package_name(self):
        """检测主要的包名"""
        package_counts = {}
        
        for element in self.elements:
            if element.package:
                count = package_counts.get(element.package, 0) + 1
                package_counts[element.package] = count
                
        if package_counts:
            # 选择出现次数最多的包名
            self.package_name = max(package_counts, key=package_counts.get)
            self.logger.debug("检测到主要包名: %s", self.package_name)

    def find_elements_by_text(self, keywords: List[str],
                              clickable_only: bool = False) -> List[UIElement]:
        """根据文本内容查找元素"""
        matching_elements = []
        
        for element in self.elements:
            if element.contains_text(keywords):
                if not clickable_only or element.is_clickable_element():
                    matching_elements.append(element)
                    
        self.logger.debug("根据文本 %s 找到 %d 个元素", keywords,
                          len(matching_elements))
        return matching_elements

    def find_elements_by_resource_id(self, resource_ids: List[str]) -> (
            List[UIElement]):
        """根据资源ID查找元素"""
        matching_elements = []
        
        for element in self.elements:
            if element.resource_id in resource_ids:
                matching_elements.append(element)
                
        self.logger.debug("根据资源ID %s 找到 %d 个元素", resource_ids,
                          len(matching_elements))
        return matching_elements

    def find_clickable_elements(self) -> List[UIElement]:
        """查找所有可点击元素"""
        clickable_elements = [
            e for e in self.elements if e.is_clickable_element()
        ]
        self.logger.debug("找到 %d 个可点击元素", len(clickable_elements))
        return clickable_elements

    def find_douyin_specific_elements(self) -> Dict[str, List[UIElement]]:
        """查找抖音特定的UI元素"""
        results = {
            'navigation_tabs': [],
            'profile_button': [],
            'add_friend_button': [],
            'contacts_button': [],
            'follow_buttons': [],
            'contact_items': [],
        }
        
        # 导航标签
        nav_keywords = ['首页', '朋友', '拍摄', '消息', '我', 'Home', 'Friends',
                        'Record', 'Message', 'Me', 'Profile']
        results['navigation_tabs'] = self.find_elements_by_text(
            nav_keywords, clickable_only=True)
        
        # 个人资料/我的按钮
        profile_keywords = ['我', 'Me', 'Profile']
        results['profile_button'] = self.find_elements_by_text(
            profile_keywords, clickable_only=True)
        
        # 添加朋友按钮
        add_friend_keywords = ['添加朋友', '添加好友', '加朋友', 'Add Friends']
        results['add_friend_button'] = self.find_elements_by_text(
            add_friend_keywords, clickable_only=True)
        
        # 通讯录按钮
        contacts_keywords = ['通讯录', '联系人', 'Contacts', '通信录']
        results['contacts_button'] = self.find_elements_by_text(
            contacts_keywords, clickable_only=True)
        
        # 关注按钮
        follow_keywords = ['关注', 'Follow', '+ 关注']
        results['follow_buttons'] = self.find_elements_by_text(
            follow_keywords, clickable_only=True)
        
        # 联系人项目（通常是包含人名的TextView或类似元素）
        for element in self.elements:
            if (element.class_name in ['android.widget.TextView',
                                       'android.view.View'] and
                    element.text and len(element.text) > 0 and
                    len(element.text) < 20):  # 假设联系人姓名不会太长
                results['contact_items'].append(element)
        
        self.logger.debug("抖音特定元素统计: %s",
                          {k: len(v) for k, v in results.items()})
        
        return results

    def has_bottom_navigation_profile_button(self) -> bool:
        """检查是否存在底部导航栏的'我'按钮"""
        if not self.elements:
            self.logger.warning("没有UI元素可供分析")
            return False
        
        # 获取屏幕尺寸
        screen_width, screen_height = self._get_screen_dimensions()
        if screen_height == 0:
            self.logger.warning("无法确定屏幕尺寸")
            return False
        
        # 使用更精确的检测逻辑
        return self._detect_profile_button_precisely(screen_width, 
                                                    screen_height)

    def _get_screen_dimensions(self):
        """获取屏幕尺寸"""
        max_width = 0
        max_height = 0
        for element in self.elements:
            if element.bounds and len(element.bounds) >= 4:
                max_width = max(max_width, element.bounds[2])
                max_height = max(max_height, element.bounds[3])
        return max_width, max_height

    def _detect_profile_button_precisely(self, screen_width, screen_height):
        """精确检测底部导航栏的'我'按钮"""
        # 底部区域定义（最底部100像素）
        bottom_threshold = screen_height - 100
        
        # 寻找符合条件的候选元素
        candidates = []
        
        for element in self.elements:
            if not (element.bounds and len(element.bounds) >= 4):
                continue
                
            # 检查是否在底部区域
            element_top = element.bounds[1]
            element_bottom = element.bounds[3]
            if element_top < bottom_threshold:
                continue
            
            # 检查是否包含"我"相关文本
            if not self._is_profile_text(element):
                continue
                
            # 检查元素特征
            score = self._calculate_profile_button_score(element, 
                                                        screen_width,
                                                        screen_height)
            if score > 0:
                candidates.append((element, score))
                self.logger.debug("候选'我'按钮: 文本='%s', 描述='%s', "
                                 "位置=%s, 评分=%.1f",
                                 element.text, element.content_desc,
                                 element.bounds, score)
        
        # 选择评分最高的候选元素
        if candidates:
            best_candidate = max(candidates, key=lambda x: x[1])
            element, score = best_candidate
            if score >= 3.0:  # 最低评分阈值
                self.logger.info("✅ 检测到底部导航栏'我'按钮: %s (评分:%.1f)",
                                element.get_full_text(), score)
                return True
        
        self.logger.info("未检测到符合条件的底部导航栏'我'按钮")
        return False

    def get_profile_button_position(self):
        """获取'我'按钮的中心位置坐标"""
        if not self.elements:
            return None
        
        screen_width, screen_height = self._get_screen_dimensions()
        if screen_height == 0:
            return None
        
        # 使用相同的检测逻辑找到"我"按钮
        bottom_threshold = screen_height - 100
        candidates = []
        
        for element in self.elements:
            if not (element.bounds and len(element.bounds) >= 4):
                continue
            
            element_top = element.bounds[1]
            if element_top < bottom_threshold:
                continue
            
            if not self._is_profile_text(element):
                continue
                
            score = self._calculate_profile_button_score(element, 
                                                        screen_width,
                                                        screen_height)
            if score > 0:
                candidates.append((element, score))
        
        if candidates:
            best_candidate = max(candidates, key=lambda x: x[1])
            element, score = best_candidate
            if score >= 3.0:
                # 计算中心位置
                center_x = (element.bounds[0] + element.bounds[2]) // 2
                center_y = (element.bounds[1] + element.bounds[3]) // 2
                return (center_x, center_y)
        
        return None

    def _is_profile_text(self, element):
        """检查是否是'我'按钮的文本特征"""
        text = element.text.strip() if element.text else ""
        desc = element.content_desc.strip() if element.content_desc else ""
        
        # 精确匹配"我"（避免误判包含"我"的长文本）
        profile_patterns = [
            "我",           # 纯"我"字
            "Me",          # 英文
            "Profile",     # 英文
            "我，按钮",     # 带按钮描述
            "我，",         # 带逗号
        ]
        
        # 检查文本是否精确匹配或者是短文本
        for pattern in profile_patterns:
            if (text == pattern or desc == pattern or
                pattern in desc or 
                (len(text) <= 3 and "我" in text)):
                return True
        
        return False

    def _calculate_profile_button_score(self, element, screen_width, 
                                       screen_height):
        """计算'我'按钮的匹配评分"""
        score = 0.0
        
        # 基础分：可点击
        if element.is_clickable_element():
            score += 1.0
        
        # 位置分：在屏幕右侧（导航栏最右边通常是"我"）
        if element.bounds:
            center_x = (element.bounds[0] + element.bounds[2]) / 2
            if center_x > screen_width * 0.7:  # 右侧30%区域
                score += 2.0
            elif center_x > screen_width * 0.5:  # 右半边
                score += 1.0
        
        # 尺寸分：合理的按钮尺寸
        if element.bounds:
            width = element.bounds[2] - element.bounds[0]
            height = element.bounds[3] - element.bounds[1]
            if 20 <= width <= 150 and 20 <= height <= 80:
                score += 1.0
        
        # 资源ID分：抖音特定的资源ID
        if element.resource_id:
            if any(pattern in element.resource_id.lower() for pattern in 
                   ['profile', 'me', 'tab', 'bottom', 'nav']):
                score += 1.5
        
        # 类名分：常见的按钮或视图类
        button_classes = [
            'TextView', 'Button', 'ImageView', 'View',
            'LinearLayout', 'RelativeLayout', 'FrameLayout'
        ]
        if any(cls in element.class_name for cls in button_classes):
            score += 0.5
        
        return score
        return False

    def print_analysis_summary(self):
        """打印分析摘要"""
        info = {
            'total_elements': len(self.elements),
            'clickable_elements': len(self.find_clickable_elements()),
            'package_name': self.package_name,
        }
        
        print("\n" + "="*50)
        print("UI 分析摘要")
        print("="*50)
        print(f"总元素数: {info['total_elements']}")
        print(f"可点击元素: {info['clickable_elements']}")
        print(f"主要包名: {info['package_name']}")
            
        # 抖音特定元素
        douyin_elements = self.find_douyin_specific_elements()
        print("\n抖音特定元素:")
        for category, elements in douyin_elements.items():
            if elements:
                print(f"  {category}: {len(elements)} 个")
                for element in elements[:3]:  # 只显示前3个
                    text = element.get_full_text()[:30]
                    print(f"    - {text}")
                if len(elements) > 3:
                    print(f"    ... 还有 {len(elements) - 3} 个")
        
        print("="*50)

    def save_analysis_report(self, filename: str):
        """保存详细分析报告到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Android UI 分析报告\n")
                f.write("="*60 + "\n\n")
                
                # 基本信息
                info = {
                    'total_elements': len(self.elements),
                    'clickable_elements': len(self.find_clickable_elements()),
                    'package_name': self.package_name,
                }
                
                f.write("基本信息:\n")
                f.write(f"  总元素数: {info['total_elements']}\n")
                f.write(f"  可点击元素: {info['clickable_elements']}\n")
                f.write(f"  主要包名: {info['package_name']}\n")
                
                # 详细元素列表
                f.write("\n详细元素列表:\n")
                f.write("-" * 40 + "\n")
                
                for i, element in enumerate(self.elements):
                    f.write(f"{i+1}. {element.class_name}\n")
                    if element.text:
                        f.write(f"   文本: {element.text}\n")
                    if element.content_desc:
                        f.write(f"   描述: {element.content_desc}\n")
                    if element.resource_id:
                        f.write(f"   资源ID: {element.resource_id}\n")
                    f.write(f"   可点击: {element.clickable}\n")
                    if element.bounds:
                        f.write(f"   位置: {element.bounds}\n")
                    f.write("\n")
                
            self.logger.info("分析报告已保存到: %s", filename)
            
        except Exception as e:
            self.logger.error("保存分析报告失败: %s", str(e))

    def analyze_bottom_navigation_structure(self):
        """分析底部导航栏的完整结构"""
        if not self.elements:
            self.logger.warning("没有UI元素可供分析")
            return None
        
        screen_width, screen_height = self._get_screen_dimensions()
        if screen_height == 0:
            return None
        
        # 收集底部导航元素
        nav_elements = self._collect_bottom_nav_elements(screen_height)
        if not nav_elements:
            return None
        
        # 构建导航结构
        nav_structure = self._build_nav_structure(nav_elements, screen_width)
        
        self.logger.info("底部导航栏分析结果: %d个按钮, 有效导航栏: %s",
                         nav_structure['total_buttons'],
                         nav_structure['is_valid_navigation'])
        
        self._log_nav_buttons(nav_structure['buttons'])
        return nav_structure

    def _collect_bottom_nav_elements(self, screen_height):
        """收集底部导航区域的元素"""
        nav_bottom_threshold = screen_height - 150
        nav_elements = []
        
        for element in self.elements:
            if not (element.bounds and len(element.bounds) >= 4):
                continue
            
            element_top = element.bounds[1]
            
            # 检查是否在底部导航区域且可能是导航按钮
            if (element_top >= nav_bottom_threshold and
                    self._is_potential_nav_button(element)):
                nav_elements.append(element)
        
        # 按X坐标排序，从左到右
        nav_elements.sort(key=lambda e: e.bounds[0])
        return nav_elements

    def _build_nav_structure(self, nav_elements, screen_width):
        """构建导航栏结构信息"""
        nav_structure = {
            'total_buttons': len(nav_elements),
            'buttons': [],
            'container_bounds': None,
            'is_valid_navigation': False
        }
        
        # 构建按钮信息
        for i, element in enumerate(nav_elements):
            button_info = self._create_button_info(i, element)
            nav_structure['buttons'].append(button_info)
        
        # 验证和设置容器边界
        if len(nav_elements) >= 3:
            nav_structure['is_valid_navigation'] = (
                self._validate_navigation_layout(nav_elements, screen_width))
            nav_structure['container_bounds'] = (
                self._calculate_container_bounds(nav_elements))
        
        return nav_structure

    def _create_button_info(self, index, element):
        """创建按钮信息字典"""
        return {
            'index': index,
            'text': element.text.strip() if element.text else "",
            'content_desc': (element.content_desc.strip()
                             if element.content_desc else ""),
            'bounds': element.bounds,
            'center': ((element.bounds[0] + element.bounds[2]) // 2,
                       (element.bounds[1] + element.bounds[3]) // 2),
            'resource_id': element.resource_id,
            'class_name': element.class_name,
            'is_profile_button': self._is_profile_text(element)
        }

    def _calculate_container_bounds(self, nav_elements):
        """计算导航栏容器边界"""
        if not nav_elements:
            return None
        
        min_x = min(e.bounds[0] for e in nav_elements)
        max_x = max(e.bounds[2] for e in nav_elements)
        min_y = min(e.bounds[1] for e in nav_elements)
        max_y = max(e.bounds[3] for e in nav_elements)
        return (min_x, min_y, max_x, max_y)

    def _log_nav_buttons(self, buttons):
        """记录导航按钮详细信息"""
        for i, button in enumerate(buttons):
            profile_marker = " [我按钮]" if button['is_profile_button'] else ""
            self.logger.debug("导航按钮%d: 文本='%s', 描述='%s', 中心=%s%s",
                              i + 1, button['text'], button['content_desc'],
                              button['center'], profile_marker)

    def _is_potential_nav_button(self, element):
        """判断元素是否可能是导航按钮"""
        # 检查尺寸（导航按钮通常有合理的尺寸）
        if element.bounds:
            width = element.bounds[2] - element.bounds[0]
            height = element.bounds[3] - element.bounds[1]
            if width < 20 or width > 200 or height < 20 or height > 100:
                return False
        
        # 检查类名（常见的按钮类）
        button_classes = ['TextView', 'Button', 'ImageView', 'View',
                          'LinearLayout', 'RelativeLayout', 'FrameLayout']
        has_button_class = any(cls in element.class_name
                               for cls in button_classes)
        
        if not has_button_class:
            return False
        
        # 检查是否可点击或有可点击的子元素
        if element.is_clickable_element():
            return True
        
        # 检查是否有可点击的子元素（导航按钮可能是容器）
        if self._has_clickable_children(element):
            return True
        
        # 检查是否有文本或描述
        has_text = (element.text and element.text.strip()) or \
                   (element.content_desc and element.content_desc.strip())
        
        return has_text

    def _has_clickable_children(self, parent_element):
        """检查元素是否有可点击的子元素"""
        if not parent_element.bounds:
            return False
        
        parent_bounds = parent_element.bounds
        
        # 查找在父元素范围内的可点击子元素
        for element in self.elements:
            if not element.bounds or element == parent_element:
                continue
            
            # 检查是否在父元素内部
            if (element.bounds[0] >= parent_bounds[0] and
                element.bounds[1] >= parent_bounds[1] and
                element.bounds[2] <= parent_bounds[2] and
                element.bounds[3] <= parent_bounds[3]):
                
                if element.is_clickable_element():
                    return True
        
        return False

    def _validate_navigation_layout(self, nav_elements, screen_width):
        """验证导航栏布局是否合理"""
        if len(nav_elements) < 3:
            return False
        
        # 获取有效的导航按钮（去重，按位置分组）
        unique_buttons = self._get_unique_nav_buttons(nav_elements)
        
        if len(unique_buttons) < 3:
            return False
        
        # 检查按钮分布是否相对均匀
        centers = [(e.bounds[0] + e.bounds[2]) // 2 for e in unique_buttons]
        centers.sort()  # 确保从左到右排序
        
        # 计算相邻按钮间距
        spacings = []
        for i in range(1, len(centers)):
            spacing = centers[i] - centers[i-1]
            if spacing > 50:  # 只考虑明显分离的按钮
                spacings.append(spacing)
        
        if len(spacings) < 2:  # 至少要有2个有意义的间距
            return False
        
        # 检查间距是否相对合理（不要求完全均匀）
        min_spacing = min(spacings)
        max_spacing = max(spacings)
        
        if min_spacing <= 0 or max_spacing > min_spacing * 5:  # 放宽到5倍
            return False
        
        # 检查覆盖屏幕宽度的比例
        total_width = centers[-1] - centers[0]
        coverage = total_width / screen_width
        
        return coverage > 0.3  # 降低到30%的屏幕宽度

    def _get_unique_nav_buttons(self, nav_elements):
        """获取唯一的导航按钮（按位置去重）"""
        unique_buttons = []
        seen_positions = set()
        
        for element in nav_elements:
            if not element.bounds:
                continue
            
            # 使用中心点作为唯一标识（允许5像素误差）
            center_x = (element.bounds[0] + element.bounds[2]) // 2
            center_y = (element.bounds[1] + element.bounds[3]) // 2
            
            # 检查是否已有相近位置的按钮
            is_duplicate = False
            for seen_x, seen_y in seen_positions:
                if abs(center_x - seen_x) <= 5 and abs(center_y - seen_y) <= 5:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_positions.add((center_x, center_y))
                unique_buttons.append(element)
        
        return unique_buttons

    def verify_profile_button_in_navigation(self):
        """验证'我'按钮是否确实在导航栏中"""
        nav_structure = self.analyze_bottom_navigation_structure()
        
        if not nav_structure or not nav_structure['is_valid_navigation']:
            self.logger.warning("未检测到有效的底部导航栏")
            return False, None
        
        # 查找"我"按钮
        profile_button = None
        for button in nav_structure['buttons']:
            if button['is_profile_button']:
                profile_button = button
                break
        
        if not profile_button:
            self.logger.warning("在导航栏中未找到'我'按钮")
            return False, None
        
        # 验证"我"按钮是否与其他导航按钮在同一结构中
        total_buttons = nav_structure['total_buttons']
        profile_index = profile_button['index']
        
        # 检查是否有足够的导航按钮
        if total_buttons < 3:
            self.logger.warning("导航按钮数量不足(%d < 3)", total_buttons)
            return False, None
        
        # 检查"我"按钮的位置是否合理（通常在右侧）
        if profile_index < total_buttons / 2:
            self.logger.warning("'我'按钮位置异常(索引:%d, 总数:%d)", 
                              profile_index, total_buttons)
        
        self.logger.info("验证通过: '我'按钮在有效导航栏中(位置:%d/%d)", 
                        profile_index + 1, total_buttons)
        
        return True, profile_button
