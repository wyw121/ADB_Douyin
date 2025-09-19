#!/usr/bin/env python3
"""
抖音应用管理模块
负责抖音应用的启动、关闭和状态管理
"""

import logging
import time
from typing import Optional
from .adb_interface import ADBInterface
from .ui_context_analyzer import UIContextAnalyzer


class DouyinAppManager:
    """抖音应用管理器"""
    
    DOUYIN_PACKAGE = "com.ss.android.ugc.aweme"
    MAIN_ACTIVITY = "com.ss.android.ugc.aweme.main.MainActivity"
    
    def __init__(self, adb_interface: ADBInterface):
        """初始化应用管理器
        
        Args:
            adb_interface: ADB接口实例
        """
        self.logger = logging.getLogger(__name__)
        self.adb = adb_interface
        self.ui_analyzer = UIContextAnalyzer()
        
        # 配置参数
        self.startup_timeout = 15  # 启动超时时间(秒)
        self.shutdown_timeout = 10  # 关闭超时时间(秒)
        self.restart_max_attempts = 3  # 重启最大尝试次数

    def is_douyin_running(self) -> bool:
        """检查抖音是否正在运行"""
        try:
            return self.adb.is_app_running(self.DOUYIN_PACKAGE)
        except Exception as e:
            self.logger.error("检查抖音运行状态失败: %s", str(e))
            return False

    def get_douyin_current_activity(self) -> Optional[str]:
        """获取抖音当前Activity"""
        try:
            result = self.adb.execute_command([
                "shell", "dumpsys", "activity", "|", "grep", 
                f"mCurrentFocus.*{self.DOUYIN_PACKAGE}"
            ])
            
            if result and "mCurrentFocus" in result:
                # 提取Activity名称
                import re
                match = re.search(r'mCurrentFocus=Window\{[^}]*\s+[^/]+/([^}]+)\}', 
                                result)
                if match:
                    activity = match.group(1)
                    self.logger.debug("抖音当前Activity: %s", activity)
                    return activity
            
            return None
            
        except Exception as e:
            self.logger.error("获取抖音Activity失败: %s", str(e))
            return None

    def analyze_and_log_ui_state(self, stage_name: str = "未知阶段") -> None:
        """分析并记录当前UI状态"""
        try:
            self.logger.info(f"📊 {stage_name}UI状态分析:")
            
            # 获取UI XML
            xml_content = self.adb.get_ui_xml()
            if xml_content:
                # 分析UI内容
                context = self.ui_analyzer.analyze_context(xml_content)
                
                # 显示分析结果
                self.ui_analyzer.display_context(context, stage_name)
                
                # 记录原始XML长度
                self.logger.info(f"📄 原始XML长度: {len(xml_content)} 字符")
                
                # 记录XML开头（用于调试）
                xml_preview = xml_content[:200] + "..." if len(xml_content) > 200 else xml_content
                self.logger.debug(f"🔬 XML预览: {xml_preview}")
                
            else:
                self.logger.warning("❌ 无法获取UI XML内容")
                
        except Exception as e:
            self.logger.error(f"❌ UI状态分析失败: {e}")

    def stop_douyin(self) -> bool:
        """关闭抖音应用"""
        self.logger.info("正在关闭抖音应用...")
        
        try:
            # 强制停止应用
            result = self.adb.execute_command([
                "shell", "am", "force-stop", self.DOUYIN_PACKAGE
            ])
            
            if result is not None:
                self.logger.info("发送关闭命令成功")
                
                # 等待应用关闭
                for i in range(self.shutdown_timeout):
                    if not self.is_douyin_running():
                        self.logger.info("✅ 抖音应用已成功关闭")
                        return True
                    
                    self.logger.debug("等待应用关闭... (%d/%d)", 
                                    i + 1, self.shutdown_timeout)
                    time.sleep(1)
                
                self.logger.warning("⚠️ 应用关闭超时，但可能已关闭")
                return True  # 即使超时也认为成功，因为force-stop通常有效
            else:
                self.logger.error("❌ 发送关闭命令失败")
                return False
                
        except Exception as e:
            self.logger.error("关闭抖音应用异常: %s", str(e))
            return False

    def start_douyin(self) -> bool:
        """启动抖音应用"""
        self.logger.info("正在启动抖音应用...")
        
        try:
            # 启动主Activity
            result = self.adb.execute_command([
                "shell", "am", "start", "-n", 
                f"{self.DOUYIN_PACKAGE}/{self.MAIN_ACTIVITY}"
            ])
            
            if result is not None:
                self.logger.info("发送启动命令成功")
                
                # 等待应用启动
                for i in range(self.startup_timeout):
                    if self.is_douyin_running():
                        activity = self.get_douyin_current_activity()
                        self.logger.info("✅ 抖音应用已启动，当前Activity: %s", 
                                       activity or "未知")
                        return True
                    
                    self.logger.debug("等待应用启动... (%d/%d)", 
                                    i + 1, self.startup_timeout)
                    time.sleep(1)
                
                self.logger.error("❌ 应用启动超时")
                return False
            else:
                self.logger.error("❌ 发送启动命令失败")
                return False
                
        except Exception as e:
            self.logger.error("启动抖音应用异常: %s", str(e))
            return False

    def restart_douyin(self) -> bool:
        """重启抖音应用"""
        self.logger.info("正在重启抖音应用...")
        
        for attempt in range(self.restart_max_attempts):
            self.logger.info("重启抖音 - 第%d次尝试", attempt + 1)
            
            # 先关闭
            if not self.stop_douyin():
                self.logger.warning("关闭失败，但继续尝试启动")
            
            # 等待一下确保完全关闭
            time.sleep(2)
            
            # 再启动
            if self.start_douyin():
                self.logger.info("✅ 抖音重启成功")
                return True
            
            self.logger.warning("第%d次重启失败", attempt + 1)
            
            if attempt < self.restart_max_attempts - 1:
                self.logger.info("等待3秒后重试...")
                time.sleep(3)
        
        self.logger.error("❌ 抖音重启失败，已尝试%d次", self.restart_max_attempts)
        return False

    def force_restart_douyin(self) -> bool:
        """强制重启抖音（包括清理进程）"""
        self.logger.info("正在强制重启抖音应用...")
        
        try:
            # 1. 强制停止
            self.adb.execute_command([
                "shell", "am", "force-stop", self.DOUYIN_PACKAGE
            ])
            
            # 2. 杀死相关进程
            self.adb.execute_command([
                "shell", "pkill", "-f", self.DOUYIN_PACKAGE
            ])
            
            # 3. 清理缓存（可选）
            self.adb.execute_command([
                "shell", "pm", "clear", self.DOUYIN_PACKAGE
            ])
            
            self.logger.info("强制清理完成，等待5秒...")
            time.sleep(5)
            
            # 4. 重新启动
            return self.start_douyin()
            
        except Exception as e:
            self.logger.error("强制重启异常: %s", str(e))
            return False

    def get_app_status_info(self) -> dict:
        """获取应用状态详细信息"""
        status = {
            'is_running': False,
            'current_activity': None,
            'pid': None,
            'package_info': None
        }
        
        try:
            # 检查运行状态
            status['is_running'] = self.is_douyin_running()
            
            if status['is_running']:
                # 获取当前Activity
                status['current_activity'] = self.get_douyin_current_activity()
                
                # 获取进程ID
                pid_result = self.adb.execute_command([
                    "shell", "pidof", self.DOUYIN_PACKAGE
                ])
                if pid_result:
                    status['pid'] = pid_result.strip()
                
                # 获取包信息
                pkg_result = self.adb.execute_command([
                    "shell", "dumpsys", "package", self.DOUYIN_PACKAGE, 
                    "|", "grep", "versionName"
                ])
                if pkg_result:
                    status['package_info'] = pkg_result.strip()
            
        except Exception as e:
            self.logger.error("获取应用状态信息失败: %s", str(e))
        
        return status

    def wait_for_stable_state(self, timeout: int = 10) -> bool:
        """等待应用状态稳定"""
        self.logger.debug("等待应用状态稳定...")
        
        last_activity = None
        stable_count = 0
        required_stable = 3  # 需要连续3次相同状态才认为稳定
        
        for i in range(timeout):
            current_activity = self.get_douyin_current_activity()
            
            if current_activity == last_activity:
                stable_count += 1
                if stable_count >= required_stable:
                    self.logger.debug("应用状态已稳定: %s", current_activity)
                    return True
            else:
                stable_count = 0
                last_activity = current_activity
            
            time.sleep(1)
        
        self.logger.warning("应用状态未能稳定")
        return False