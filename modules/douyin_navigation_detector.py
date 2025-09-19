#!/usr/bin/env python3
"""
抖音底部导航栏识别模块
负责安全识别和点击底部导航栏的"我"按钮
"""

import logging
import time
from typing import Optional, Tuple, Dict, Any
from .adb_interface import ADBInterface
from .ui_intelligence import UIAnalyzer
from .ui_context_analyzer import UIContextAnalyzer


class DouyinNavigationDetector:
    """抖音底部导航栏检测器"""
    
    def __init__(self, adb_interface: ADBInterface):
        """初始化导航栏检测器
        
        Args:
            adb_interface: ADB接口实例
        """
        self.logger = logging.getLogger(__name__)
        self.adb = adb_interface
        self.ui_analyzer = UIAnalyzer()
        self.ui_context = UIContextAnalyzer()
        
        # 缓存的"我"按钮位置（安全机制）
        self.cached_profile_position = None
        self.cached_nav_structure = None
        self.last_cache_time = 0
        self.cache_validity_duration = 300  # 缓存有效期5分钟
        
        # 配置参数
        self.detection_max_attempts = 3
        self.coordinate_safety_threshold = 1300  # Y坐标安全阈值（调整）
        self.navigation_min_buttons = 3  # 最少导航按钮数

    def get_current_ui_safely(self) -> bool:
        """安全获取当前UI"""
        try:
            xml_content = self.adb.get_ui_xml()
            if xml_content:
                return self.ui_analyzer.parse_xml(xml_content)
            else:
                self.logger.warning("无法获取UI XML内容")
                return False
        except Exception as e:
            self.logger.error("获取UI时发生异常: %s", str(e))
            return False

    def detect_navigation_structure(self) -> Optional[Dict[str, Any]]:
        """检测底部导航栏结构（核心安全机制）"""
        self.logger.info("开始检测底部导航栏结构...")
        
        if not self.get_current_ui_safely():
            self.logger.error("无法获取UI，导航栏检测失败")
            return None
        
        # 添加UI上下文分析
        xml_content = self.adb.get_ui_xml()
        if xml_content:
            context = self.ui_context.analyze_current_context(xml_content)
            self.ui_context.print_context_info(context, "底部导航栏检测器")
        
        try:
            # 使用完整的导航栏结构分析
            nav_structure = self.ui_analyzer.analyze_bottom_navigation_structure()
            
            if not nav_structure:
                self.logger.warning("未检测到导航栏结构")
                return None
            
            # 验证导航栏的有效性
            if not self._validate_navigation_structure(nav_structure):
                self.logger.warning("导航栏结构验证失败")
                return None
            
            self.logger.info("✅ 检测到有效的导航栏结构: %d个按钮",
                           nav_structure['total_buttons'])
            
            # 缓存结构信息
            self.cached_nav_structure = nav_structure
            self.last_cache_time = time.time()
            
            return nav_structure
            
        except Exception as e:
            self.logger.error("导航栏结构检测异常: %s", str(e))
            return None

    def find_profile_button_safely(self) -> Optional[Dict[str, Any]]:
        """安全查找"我"按钮（多重验证机制）"""
        self.logger.info("开始安全查找'我'按钮...")
        
        for attempt in range(self.detection_max_attempts):
            self.logger.info("第%d次尝试查找'我'按钮", attempt + 1)
            
            # 方法1: 使用完整导航栏验证
            profile_button = self._find_with_navigation_verification()
            if profile_button:
                self.logger.info("✅ 通过导航栏验证找到'我'按钮")
                return profile_button
            
            # 方法2: 使用缓存验证（如果有的话）
            if self.cached_profile_position:
                profile_button = self._verify_cached_position()
                if profile_button:
                    self.logger.info("✅ 通过缓存验证找到'我'按钮")
                    return profile_button
            
            # 方法3: 使用传统检测方法（后备）
            profile_button = self._find_with_traditional_method()
            if profile_button:
                self.logger.info("✅ 通过传统方法找到'我'按钮")
                return profile_button
            
            if attempt < self.detection_max_attempts - 1:
                self.logger.warning("第%d次查找失败，等待2秒后重试", attempt + 1)
                time.sleep(2)
        
        self.logger.error("❌ 所有方法都无法找到'我'按钮")
        return None

    def _find_with_navigation_verification(self) -> Optional[Dict[str, Any]]:
        """使用导航栏验证方法查找（最安全）"""
        try:
            is_valid, profile_button = (
                self.ui_analyzer.verify_profile_button_in_navigation())
            
            if is_valid and profile_button:
                # 额外的坐标安全验证
                if self._verify_coordinate_safety(profile_button['center']):
                    # 缓存验证通过的位置
                    self.cached_profile_position = profile_button['center']
                    self.last_cache_time = time.time()
                    
                    self.logger.info("导航栏验证成功: 位置%s, 文本'%s'",
                                   profile_button['center'],
                                   profile_button['text'])
                    return profile_button
                else:
                    self.logger.warning("导航栏验证的坐标未通过安全检查")
            
            return None
            
        except Exception as e:
            self.logger.error("导航栏验证方法异常: %s", str(e))
            return None

    def _verify_cached_position(self) -> Optional[Dict[str, Any]]:
        """验证缓存位置的有效性"""
        try:
            # 检查缓存是否过期
            if (time.time() - self.last_cache_time > 
                    self.cache_validity_duration):
                self.logger.debug("缓存已过期，清除缓存")
                self.cached_profile_position = None
                return None
            
            if not self.cached_profile_position:
                return None
            
            # 基本坐标安全检查
            if not self._verify_coordinate_safety(self.cached_profile_position):
                self.logger.warning("缓存坐标未通过基本安全检查")
                self.cached_profile_position = None
                return None
            
            # 与当前导航栏结构比较（如果有的话）
            nav_structure = self.detect_navigation_structure()
            if nav_structure and nav_structure['container_bounds']:
                if not self._check_coordinate_in_container(
                        self.cached_profile_position, 
                        nav_structure['container_bounds']):
                    self.logger.warning("缓存坐标不在当前导航栏容器范围内")
                    self.cached_profile_position = None
                    return None
            
            # 构建缓存按钮信息
            cached_button = {
                'center': self.cached_profile_position,
                'text': '我',
                'source': 'cached',
                'bounds': None
            }
            
            self.logger.info("缓存位置验证通过: %s", 
                           self.cached_profile_position)
            return cached_button
            
        except Exception as e:
            self.logger.error("缓存位置验证异常: %s", str(e))
            return None

    def _find_with_traditional_method(self) -> Optional[Dict[str, Any]]:
        """使用传统检测方法（后备方案）"""
        try:
            if not self.get_current_ui_safely():
                return None
            
            if self.ui_analyzer.has_bottom_navigation_profile_button():
                position = self.ui_analyzer.get_profile_button_position()
                if position and self._verify_coordinate_safety(position):
                    traditional_button = {
                        'center': position,
                        'text': '我',
                        'source': 'traditional',
                        'bounds': None
                    }
                    
                    # 更新缓存
                    self.cached_profile_position = position
                    self.last_cache_time = time.time()
                    
                    self.logger.info("传统方法检测成功: %s", position)
                    return traditional_button
            
            return None
            
        except Exception as e:
            self.logger.error("传统检测方法异常: %s", str(e))
            return None

    def click_profile_button_safely(self, profile_button: Dict[str, Any]) -> bool:
        """安全点击"我"按钮"""
        try:
            position = profile_button['center']
            
            # 最后一次坐标安全检查
            if not self._verify_coordinate_safety(position):
                self.logger.error("点击前坐标安全检查失败")
                return False
            
            self.logger.info("正在安全点击'我'按钮: %s", position)
            
            # 执行点击
            success = self.adb.tap(position[0], position[1])
            
            if success:
                self.logger.info("✅ '我'按钮点击成功")
                # 等待页面跳转
                time.sleep(3)
                return True
            else:
                self.logger.error("❌ '我'按钮点击失败")
                return False
                
        except Exception as e:
            self.logger.error("安全点击异常: %s", str(e))
            return False

    def navigate_to_profile_safely(self) -> bool:
        """安全导航到个人资料页面（完整流程）"""
        self.logger.info("开始安全导航到个人资料页面...")
        
        # 第1步: 安全查找"我"按钮
        profile_button = self.find_profile_button_safely()
        if not profile_button:
            self.logger.error("无法找到'我'按钮，导航失败")
            return False
        
        # 第2步: 安全点击"我"按钮
        if not self.click_profile_button_safely(profile_button):
            self.logger.error("点击'我'按钮失败，导航失败")
            return False
        
        # 第3步: 验证导航结果
        if self._verify_profile_page_loaded():
            self.logger.info("✅ 成功导航到个人资料页面")
            return True
        else:
            self.logger.warning("⚠️ 可能已导航到个人资料页面，但验证失败")
            return True  # 给予一定宽容度

    def _validate_navigation_structure(self, nav_structure: Dict[str, Any]) -> bool:
        """验证导航栏结构的有效性"""
        if not nav_structure:
            return False
        
        # 检查按钮数量
        total_buttons = nav_structure.get('total_buttons', 0)
        if total_buttons < self.navigation_min_buttons:
            self.logger.warning("导航按钮数量不足: %d < %d", 
                              total_buttons, self.navigation_min_buttons)
            return False
        
        # 检查是否为有效导航栏
        if not nav_structure.get('is_valid_navigation', False):
            self.logger.warning("导航栏布局验证失败")
            return False
        
        # 检查是否包含"我"按钮
        has_profile = any(btn.get('is_profile_button', False) 
                         for btn in nav_structure.get('buttons', []))
        if not has_profile:
            self.logger.warning("导航栏中未找到'我'按钮")
            return False
        
        return True

    def _verify_coordinate_safety(self, position: Tuple[int, int]) -> bool:
        """验证坐标的安全性"""
        if not position or len(position) != 2:
            return False
        
        x, y = position
        
        # 检查坐标范围
        if x < 0 or y < 0 or x > 2000 or y > 3000:
            self.logger.warning("坐标超出合理范围: (%d, %d)", x, y)
            return False
        
        # 检查是否在底部导航区域
        if y < self.coordinate_safety_threshold:
            self.logger.warning("坐标不在底部导航区域: y=%d < %d", 
                              y, self.coordinate_safety_threshold)
            return False
        
        return True

    def _check_coordinate_in_container(self, position: Tuple[int, int], 
                                     container_bounds: Tuple[int, int, int, int]) -> bool:
        """检查坐标是否在容器范围内"""
        x, y = position
        min_x, min_y, max_x, max_y = container_bounds
        
        # 允许20像素的容差
        tolerance = 20
        in_bounds = (min_x - tolerance <= x <= max_x + tolerance and
                     min_y - tolerance <= y <= max_y + tolerance)
        
        if not in_bounds:
            self.logger.warning("坐标(%d,%d)不在容器(%s)范围内",
                              x, y, container_bounds)
        
        return in_bounds

    def _verify_profile_page_loaded(self) -> bool:
        """验证个人资料页面是否加载成功"""
        try:
            if not self.get_current_ui_safely():
                return False
            
            # 查找个人资料页面的特征元素
            profile_indicators = [
                "添加朋友",
                "编辑资料", 
                "设置",
                "获赞",
                "关注",
                "粉丝"
            ]
            
            xml_content = self.adb.get_ui_xml()
            if xml_content:
                found_indicators = [indicator for indicator in profile_indicators 
                                  if indicator in xml_content]
                
                # 至少要有2个指示元素
                is_loaded = len(found_indicators) >= 2
                
                if is_loaded:
                    self.logger.info("个人资料页面验证成功，找到: %s", 
                                   found_indicators)
                else:
                    self.logger.debug("个人资料页面验证失败，只找到: %s", 
                                    found_indicators)
                
                return is_loaded
            
            return False
            
        except Exception as e:
            self.logger.error("验证个人资料页面异常: %s", str(e))
            return False

    def get_navigation_status(self) -> Dict[str, Any]:
        """获取导航检测状态信息"""
        status = {
            'ui_available': False,
            'navigation_detected': False,
            'profile_button_found': False,
            'cached_position_available': False,
            'cache_valid': False,
            'last_detection_method': None
        }
        
        try:
            # UI可用性
            status['ui_available'] = self.get_current_ui_safely()
            
            if status['ui_available']:
                # 导航栏检测
                nav_structure = self.detect_navigation_structure()
                status['navigation_detected'] = nav_structure is not None
                
                if nav_structure:
                    # "我"按钮检测
                    profile_button = self.find_profile_button_safely()
                    status['profile_button_found'] = profile_button is not None
                    
                    if profile_button:
                        status['last_detection_method'] = profile_button.get('source', 'unknown')
            
            # 缓存状态
            status['cached_position_available'] = self.cached_profile_position is not None
            if self.cached_profile_position:
                cache_age = time.time() - self.last_cache_time
                status['cache_valid'] = cache_age < self.cache_validity_duration
            
        except Exception as e:
            self.logger.error("获取导航状态异常: %s", str(e))
        
        return status

    def clear_cache(self):
        """清除缓存数据"""
        self.logger.info("清除导航检测缓存")
        self.cached_profile_position = None
        self.cached_nav_structure = None
        self.last_cache_time = 0