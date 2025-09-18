#!/usr/bin/env python3
"""
抖音启动画面检测模块
负责检测和处理抖音启动画面状态
"""

import logging
import time
from typing import Optional, Tuple
from .adb_interface import ADBInterface
from .douyin_app_manager import DouyinAppManager


class DouyinSplashDetector:
    """抖音启动画面检测器"""
    
    # 启动画面Activity模式
    SPLASH_PATTERNS = [
        "SplashActivity",
        "LaunchActivity", 
        "WelcomeActivity",
        "InitActivity",
        "StartActivity",
        "LoadingActivity"
    ]
    
    # 主界面指示元素
    MAIN_INTERFACE_INDICATORS = [
        "我",      # 底部导航栏
        "推荐",    # 顶部标签
        "关注",    # 顶部标签
        "直播",    # 顶部标签
        "同城",    # 顶部标签
    ]
    
    def __init__(self, adb_interface: ADBInterface, 
                 app_manager: DouyinAppManager):
        """初始化启动画面检测器
        
        Args:
            adb_interface: ADB接口实例
            app_manager: 应用管理器实例
        """
        self.logger = logging.getLogger(__name__)
        self.adb = adb_interface
        self.app_manager = app_manager
        
        # 配置参数
        self.splash_timeout = 30  # 启动画面最大等待时间(秒)
        self.detection_interval = 2  # 检测间隔(秒)
        self.restart_threshold = 25  # 重启阈值(秒)

    def is_in_splash_screen(self) -> bool:
        """检查是否在启动画面"""
        try:
            current_activity = self.app_manager.get_douyin_current_activity()
            
            if not current_activity:
                return False
            
            # 检查是否匹配启动画面模式
            is_splash = any(pattern in current_activity 
                           for pattern in self.SPLASH_PATTERNS)
            
            if is_splash:
                self.logger.debug("检测到启动画面: %s", current_activity)
            else:
                self.logger.debug("当前Activity: %s", current_activity)
            
            return is_splash
            
        except Exception as e:
            self.logger.error("检查启动画面状态失败: %s", str(e))
            return False

    def is_main_interface_ready(self) -> bool:
        """检查主界面是否就绪"""
        try:
            # 先检查不在启动画面
            if self.is_in_splash_screen():
                return False
            
            # 尝试获取UI内容
            xml_content = self.adb.get_ui_xml()
            if not xml_content:
                self.logger.debug("无法获取UI内容")
                return False
            
            # 检查主界面指示元素
            found_indicators = []
            for indicator in self.MAIN_INTERFACE_INDICATORS:
                if indicator in xml_content:
                    found_indicators.append(indicator)
            
            # 至少需要2个主界面指示元素
            is_ready = len(found_indicators) >= 2
            
            if is_ready:
                self.logger.info("主界面就绪，找到指示元素: %s", found_indicators)
            else:
                self.logger.debug("主界面未就绪，找到指示元素: %s", 
                                found_indicators)
            
            return is_ready
            
        except Exception as e:
            self.logger.error("检查主界面就绪状态失败: %s", str(e))
            return False

    def wait_through_splash_screen(self) -> Tuple[bool, str]:
        """等待通过启动画面
        
        Returns:
            (成功标志, 状态描述)
        """
        self.logger.info("开始等待通过启动画面...")
        
        start_time = time.time()
        splash_detected = False
        last_restart_time = 0
        
        while time.time() - start_time < self.splash_timeout:
            elapsed_time = int(time.time() - start_time)
            
            # 检查应用是否还在运行
            if not self.app_manager.is_douyin_running():
                return False, "抖音应用已停止运行"
            
            # 检查是否在启动画面
            if self.is_in_splash_screen():
                splash_detected = True
                self.logger.info("启动画面检测中... (%ds/%ds)", 
                               elapsed_time, self.splash_timeout)
                
                # 如果卡在启动画面太久，尝试重启
                if (elapsed_time > self.restart_threshold and 
                        elapsed_time - last_restart_time > 15):
                    self.logger.warning("启动画面超时，尝试重启抖音...")
                    if self.app_manager.restart_douyin():
                        last_restart_time = elapsed_time
                        self.logger.info("重启完成，继续监控...")
                    else:
                        return False, "重启失败"
                
                time.sleep(self.detection_interval)
                continue
            
            # 不在启动画面了，检查主界面是否就绪
            if splash_detected:
                self.logger.info("已离开启动画面，检查主界面...")
                time.sleep(3)  # 给主界面一些加载时间
            
            if self.is_main_interface_ready():
                total_time = int(time.time() - start_time)
                self.logger.info("✅ 主界面加载完成 (耗时: %ds)", total_time)
                return True, f"主界面就绪，耗时{total_time}秒"
            
            self.logger.debug("主界面尚未就绪，继续等待... (%ds/%ds)", 
                            elapsed_time, self.splash_timeout)
            time.sleep(self.detection_interval)
        
        # 超时
        total_time = int(time.time() - start_time)
        if splash_detected:
            return False, f"启动画面超时，耗时{total_time}秒"
        else:
            return False, f"未检测到启动画面，但主界面未就绪，耗时{total_time}秒"

    def handle_splash_timeout(self) -> bool:
        """处理启动画面超时情况"""
        self.logger.warning("处理启动画面超时...")
        
        # 尝试点击屏幕中央（可能有遮罩或需要用户交互）
        screen_size = self.adb.get_screen_size()
        if screen_size:
            center_x = screen_size[0] // 2
            center_y = screen_size[1] // 2
            self.logger.info("尝试点击屏幕中央: (%d, %d)", center_x, center_y)
            self.adb.tap(center_x, center_y)
            time.sleep(2)
            
            # 检查是否有效果
            if not self.is_in_splash_screen():
                self.logger.info("点击屏幕有效，已离开启动画面")
                return True
        
        # 尝试按返回键
        self.logger.info("尝试按返回键...")
        self.adb.execute_command(["shell", "input", "keyevent", "4"])
        time.sleep(1)
        
        # 尝试重启应用
        self.logger.info("尝试重启应用...")
        return self.app_manager.restart_douyin()

    def wait_for_douyin_ready(self, max_attempts: int = 3) -> bool:
        """等待抖音完全就绪
        
        Args:
            max_attempts: 最大尝试次数
            
        Returns:
            是否成功就绪
        """
        self.logger.info("等待抖音完全就绪...")
        
        for attempt in range(max_attempts):
            self.logger.info("第%d次尝试等待抖音就绪", attempt + 1)
            
            # 确保抖音正在运行
            if not self.app_manager.is_douyin_running():
                self.logger.info("抖音未运行，启动中...")
                if not self.app_manager.start_douyin():
                    self.logger.error("启动抖音失败")
                    continue
            
            # 等待通过启动画面
            success, message = self.wait_through_splash_screen()
            
            if success:
                self.logger.info("✅ 抖音已完全就绪: %s", message)
                return True
            else:
                self.logger.warning("❌ 第%d次尝试失败: %s", attempt + 1, message)
                
                # 如果不是最后一次尝试，处理超时情况
                if attempt < max_attempts - 1:
                    if self.handle_splash_timeout():
                        continue
                    else:
                        self.logger.error("处理启动画面超时失败")
        
        self.logger.error("所有尝试都失败，抖音无法就绪")
        return False

    def get_splash_status_info(self) -> dict:
        """获取启动画面状态信息"""
        status = {
            'is_in_splash': False,
            'current_activity': None,
            'is_main_ready': False,
            'app_running': False,
            'ui_available': False
        }
        
        try:
            # 应用运行状态
            status['app_running'] = self.app_manager.is_douyin_running()
            
            if status['app_running']:
                # 当前Activity
                status['current_activity'] = (
                    self.app_manager.get_douyin_current_activity())
                
                # 启动画面状态
                status['is_in_splash'] = self.is_in_splash_screen()
                
                # UI可用性
                xml_content = self.adb.get_ui_xml()
                status['ui_available'] = xml_content is not None
                
                # 主界面就绪状态
                if not status['is_in_splash']:
                    status['is_main_ready'] = self.is_main_interface_ready()
            
        except Exception as e:
            self.logger.error("获取启动画面状态信息失败: %s", str(e))
        
        return status