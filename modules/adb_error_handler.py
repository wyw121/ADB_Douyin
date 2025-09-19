#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ADB命令错误处理和重试模块
提供统一的错误处理、重试机制和故障恢复功能
"""

import logging
import time
import subprocess
from typing import Optional, Dict, Any, List, Callable, Tuple
from enum import Enum


class ErrorType(Enum):
    """错误类型枚举"""
    ADB_CONNECTION_LOST = "adb_connection_lost"
    ADB_COMMAND_FAILED = "adb_command_failed"
    UI_DUMP_FAILED = "ui_dump_failed"
    DEVICE_UNAUTHORIZED = "device_unauthorized"
    DEVICE_OFFLINE = "device_offline"
    APP_CRASH = "app_crash"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class RecoveryAction(Enum):
    """恢复动作枚举"""
    RETRY_COMMAND = "retry_command"
    RESTART_ADB_SERVER = "restart_adb_server"
    RECONNECT_DEVICE = "reconnect_device"
    RESTART_APP = "restart_app"
    RESTART_DEVICE = "restart_device"
    WAIT_AND_RETRY = "wait_and_retry"
    SKIP_AND_CONTINUE = "skip_and_continue"
    ABORT_OPERATION = "abort_operation"


class ADBErrorHandler:
    """ADB错误处理器"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """初始化错误处理器
        
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
        """
        self.logger = logging.getLogger(__name__)
        self.max_retries = max_retries
        self.base_delay = base_delay
        
        # 错误统计
        self.error_count = {}
        self.last_error_time = {}
        self.consecutive_failures = 0
        
        # 错误处理策略配置
        self.error_strategies = self._init_error_strategies()
        
        # ADB相关配置
        self.adb_path = "platform-tools/adb.exe"
        self.device_id = None
    
    def set_device_id(self, device_id: str):
        """设置当前设备ID"""
        self.device_id = device_id
    
    def _init_error_strategies(self) -> Dict[ErrorType, List[RecoveryAction]]:
        """初始化错误处理策略"""
        return {
            ErrorType.ADB_CONNECTION_LOST: [
                RecoveryAction.RESTART_ADB_SERVER,
                RecoveryAction.RECONNECT_DEVICE,
                RecoveryAction.WAIT_AND_RETRY
            ],
            ErrorType.ADB_COMMAND_FAILED: [
                RecoveryAction.WAIT_AND_RETRY,
                RecoveryAction.RETRY_COMMAND,
                RecoveryAction.RESTART_ADB_SERVER
            ],
            ErrorType.UI_DUMP_FAILED: [
                RecoveryAction.WAIT_AND_RETRY,
                RecoveryAction.RETRY_COMMAND,
                RecoveryAction.RESTART_APP
            ],
            ErrorType.DEVICE_UNAUTHORIZED: [
                RecoveryAction.RECONNECT_DEVICE,
                RecoveryAction.RESTART_ADB_SERVER
            ],
            ErrorType.DEVICE_OFFLINE: [
                RecoveryAction.RECONNECT_DEVICE,
                RecoveryAction.RESTART_ADB_SERVER,
                RecoveryAction.WAIT_AND_RETRY
            ],
            ErrorType.APP_CRASH: [
                RecoveryAction.RESTART_APP,
                RecoveryAction.WAIT_AND_RETRY
            ],
            ErrorType.TIMEOUT: [
                RecoveryAction.WAIT_AND_RETRY,
                RecoveryAction.RETRY_COMMAND
            ],
            ErrorType.UNKNOWN: [
                RecoveryAction.WAIT_AND_RETRY,
                RecoveryAction.RETRY_COMMAND,
                RecoveryAction.RESTART_ADB_SERVER
            ]
        }
    
    def analyze_error(self, error: Exception, command: List[str], 
                     stderr: str = "") -> ErrorType:
        """分析错误类型
        
        Args:
            error: 异常对象
            command: 失败的命令
            stderr: 标准错误输出
            
        Returns:
            ErrorType: 错误类型
        """
        error_str = str(error).lower()
        stderr_lower = stderr.lower()
        command_str = " ".join(command).lower()
        
        # 根据错误信息判断错误类型
        if "device unauthorized" in error_str or "unauthorized" in stderr_lower:
            return ErrorType.DEVICE_UNAUTHORIZED
        
        if "device offline" in error_str or "offline" in stderr_lower:
            return ErrorType.DEVICE_OFFLINE
        
        if "no devices" in error_str or "device not found" in error_str:
            return ErrorType.ADB_CONNECTION_LOST
        
        if "uiautomator" in command_str and ("non-zero exit status" in error_str):
            return ErrorType.UI_DUMP_FAILED
        
        if "timeout" in error_str or "timed out" in error_str:
            return ErrorType.TIMEOUT
        
        if "dumpsys activity" in command_str and "non-zero exit status" in error_str:
            # dumpsys activity命令失败通常是因为没有找到对应的activity
            return ErrorType.ADB_COMMAND_FAILED
        
        if isinstance(error, subprocess.CalledProcessError):
            return ErrorType.ADB_COMMAND_FAILED
        
        return ErrorType.UNKNOWN
    
    def execute_with_retry(self, command_func: Callable, command_args: tuple,
                          operation_name: str) -> Tuple[bool, Any]:
        """执行命令并自动重试
        
        Args:
            command_func: 要执行的命令函数
            command_args: 命令参数
            operation_name: 操作名称（用于日志）
            
        Returns:
            Tuple[bool, Any]: (是否成功, 结果)
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info("🔄 %s - 第%d次重试", operation_name, attempt)
                
                # 执行命令
                result = command_func(*command_args)
                
                # 重置连续失败计数
                self.consecutive_failures = 0
                
                if attempt > 0:
                    self.logger.info("✅ %s - 重试成功", operation_name)
                
                return True, result
                
            except Exception as e:
                last_error = e
                self.consecutive_failures += 1
                
                # 记录错误统计
                error_type = self.analyze_error(e, [], "")
                self._record_error(error_type)
                
                self.logger.warning("⚠️ %s - 第%d次尝试失败: %s", 
                                  operation_name, attempt + 1, str(e))
                
                # 如果是最后一次尝试，不再重试
                if attempt >= self.max_retries:
                    break
                
                # 执行恢复策略
                recovery_success = self._execute_recovery_strategy(error_type, e)
                
                if not recovery_success:
                    self.logger.error("❌ %s - 恢复策略失败，停止重试", operation_name)
                    break
        
        self.logger.error("❌ %s - 所有重试都失败了，最后错误: %s", 
                         operation_name, str(last_error))
        return False, last_error
    
    def _execute_recovery_strategy(self, error_type: ErrorType, 
                                 error: Exception) -> bool:
        """执行恢复策略
        
        Args:
            error_type: 错误类型
            error: 异常对象
            
        Returns:
            bool: 恢复是否成功
        """
        strategies = self.error_strategies.get(error_type, 
                                             [RecoveryAction.WAIT_AND_RETRY])
        
        for strategy in strategies:
            self.logger.info("🔧 执行恢复策略: %s", strategy.value)
            
            try:
                if strategy == RecoveryAction.WAIT_AND_RETRY:
                    self._wait_with_backoff()
                    return True
                
                elif strategy == RecoveryAction.RESTART_ADB_SERVER:
                    return self._restart_adb_server()
                
                elif strategy == RecoveryAction.RECONNECT_DEVICE:
                    return self._reconnect_device()
                
                elif strategy == RecoveryAction.RESTART_APP:
                    return self._restart_target_app()
                
                elif strategy == RecoveryAction.RESTART_DEVICE:
                    return self._restart_device()
                
                elif strategy == RecoveryAction.RETRY_COMMAND:
                    # 这个策略由上层重试逻辑处理
                    return True
                
                elif strategy == RecoveryAction.SKIP_AND_CONTINUE:
                    self.logger.warning("⏭️ 跳过当前操作，继续执行")
                    return False  # 表示不再重试，但不是致命错误
                
                elif strategy == RecoveryAction.ABORT_OPERATION:
                    self.logger.error("🛑 中止操作")
                    return False
                    
            except Exception as recovery_error:
                self.logger.error("❌ 恢复策略执行失败: %s", str(recovery_error))
                continue
        
        return False
    
    def _wait_with_backoff(self):
        """指数退避等待（限制最大等待时间）"""
        # 限制最大等待时间为10秒
        delay = min(self.base_delay * (2 ** min(self.consecutive_failures, 3)), 10)
        self.logger.info("⏳ 等待 %.1f 秒后重试...", delay)
        time.sleep(delay)
    
    def _restart_adb_server(self) -> bool:
        """重启ADB服务器"""
        try:
            self.logger.info("🔄 正在重启ADB服务器...")
            
            # 停止ADB服务器
            subprocess.run([self.adb_path, "kill-server"], 
                         capture_output=True, timeout=10)
            time.sleep(2)
            
            # 启动ADB服务器
            result = subprocess.run([self.adb_path, "start-server"], 
                                  capture_output=True, timeout=10)
            
            if result.returncode == 0:
                self.logger.info("✅ ADB服务器重启成功")
                time.sleep(3)  # 等待服务器完全启动
                return True
            else:
                self.logger.error("❌ ADB服务器重启失败")
                return False
                
        except Exception as e:
            self.logger.error("❌ 重启ADB服务器时出错: %s", str(e))
            return False
    
    def _reconnect_device(self) -> bool:
        """重新连接设备"""
        if not self.device_id:
            self.logger.warning("⚠️ 没有设备ID，无法重新连接")
            return False
        
        try:
            self.logger.info("🔄 正在重新连接设备: %s", self.device_id)
            
            # 检查设备状态
            result = subprocess.run([self.adb_path, "devices"], 
                                  capture_output=True, text=True, timeout=10)
            
            if self.device_id in result.stdout:
                if "unauthorized" in result.stdout:
                    self.logger.warning("⚠️ 设备未授权，请在设备上确认USB调试授权")
                    time.sleep(5)  # 给用户时间授权
                    return False
                elif "offline" in result.stdout:
                    self.logger.info("🔄 设备离线，尝试重新连接...")
                    # 可以尝试一些重连操作
                    time.sleep(3)
                    return True
                else:
                    self.logger.info("✅ 设备连接正常")
                    return True
            else:
                self.logger.error("❌ 设备未找到: %s", self.device_id)
                return False
                
        except Exception as e:
            self.logger.error("❌ 重新连接设备时出错: %s", str(e))
            return False
    
    def _restart_target_app(self) -> bool:
        """重启目标应用（抖音）"""
        if not self.device_id:
            return False
        
        try:
            self.logger.info("🔄 正在重启抖音应用...")
            
            # 强制停止应用
            subprocess.run([self.adb_path, "-s", self.device_id, 
                           "shell", "am", "force-stop", 
                           "com.ss.android.ugc.aweme"], 
                          capture_output=True, timeout=10)
            
            time.sleep(2)
            
            # 启动应用
            result = subprocess.run([self.adb_path, "-s", self.device_id, 
                                   "shell", "am", "start", "-n",
                                   "com.ss.android.ugc.aweme/.main.MainActivity"],
                                  capture_output=True, timeout=15)
            
            if result.returncode == 0:
                self.logger.info("✅ 抖音应用重启成功")
                time.sleep(5)  # 等待应用启动
                return True
            else:
                self.logger.error("❌ 抖音应用重启失败")
                return False
                
        except Exception as e:
            self.logger.error("❌ 重启应用时出错: %s", str(e))
            return False
    
    def _restart_device(self) -> bool:
        """重启设备（手机）"""
        if not self.device_id:
            return False
        
        try:
            self.logger.warning("🔄 准备重启设备: %s", self.device_id)
            self.logger.warning("⚠️ 设备将重启，请确保设备处于安全状态")
            
            # 给用户3秒时间取消
            self.logger.info("⏰ 3秒后开始重启设备，按Ctrl+C取消...")
            try:
                time.sleep(3)
            except KeyboardInterrupt:
                self.logger.info("⏹️ 用户取消设备重启")
                return False
            
            # 执行重启命令
            self.logger.info("🔄 正在重启设备...")
            result = subprocess.run([self.adb_path, "-s", self.device_id,
                                    "shell", "reboot"],
                                   capture_output=True, timeout=10)
            
            if result.returncode == 0:
                self.logger.info("✅ 重启命令发送成功")
                return self._wait_for_device_restart()
            else:
                self.logger.error("❌ 重启命令发送失败")
                return False
                
        except KeyboardInterrupt:
            self.logger.info("⏹️ 用户取消设备重启")
            return False
        except Exception as e:
            self.logger.error("❌ 重启设备时出错: %s", str(e))
            return False
    
    def _wait_for_device_restart(self) -> bool:
        """等待设备重启完成"""
        # 等待设备关机
        self.logger.info("⏳ 等待设备关机...")
        time.sleep(10)
        
        # 等待设备重启并重新连接
        self.logger.info("⏳ 等待设备重新启动...")
        max_wait_time = 120  # 最多等待2分钟
        wait_time = 0
        
        while wait_time < max_wait_time:
            time.sleep(10)
            wait_time += 10
            
            # 检查设备是否重新上线
            try:
                devices_result = subprocess.run(
                    [self.adb_path, "devices"],
                    capture_output=True, text=True, timeout=10)
                    
                if (self.device_id in devices_result.stdout and 
                    "device" in devices_result.stdout):
                    self.logger.info("✅ 设备重启完成，重新连接成功")
                    
                    # 等待系统完全启动
                    self.logger.info("⏳ 等待系统完全启动...")
                    time.sleep(20)
                    return True
                    
            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue
            
            self.logger.info("⏳ 设备重启中... (%d/%d秒)", 
                           wait_time, max_wait_time)
        
        self.logger.error("❌ 设备重启超时，可能需要手动检查")
        return False
    
    def _record_error(self, error_type: ErrorType):
        """记录错误统计"""
        current_time = time.time()
        
        if error_type not in self.error_count:
            self.error_count[error_type] = 0
        
        self.error_count[error_type] += 1
        self.last_error_time[error_type] = current_time
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return {
            "error_count": {et.value: count for et, count in self.error_count.items()},
            "consecutive_failures": self.consecutive_failures,
            "last_errors": {et.value: time.ctime(ts) 
                           for et, ts in self.last_error_time.items()}
        }
    
    def reset_statistics(self):
        """重置错误统计"""
        self.error_count.clear()
        self.last_error_time.clear()
        self.consecutive_failures = 0
        self.logger.info("🔄 错误统计已重置")
    
    def is_system_healthy(self) -> bool:
        """检查系统健康状态"""
        # 如果连续失败次数过多，认为系统不健康
        if self.consecutive_failures > 5:
            return False
        
        # 如果总错误数过多，认为系统不健康
        total_errors = sum(self.error_count.values())
        if total_errors > 20:
            return False
        
        return True


class RetryableADBCommand:
    """可重试的ADB命令封装"""
    
    def __init__(self, error_handler: ADBErrorHandler):
        """初始化可重试命令
        
        Args:
            error_handler: 错误处理器实例
        """
        self.error_handler = error_handler
        self.logger = logging.getLogger(__name__)
    
    def execute_command(self, command: List[str], timeout: int = 30) -> Optional[str]:
        """执行ADB命令（带重试）
        
        Args:
            command: ADB命令列表
            timeout: 超时时间（秒）
            
        Returns:
            Optional[str]: 命令执行结果
        """
        def _execute():
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, command, result.stdout, result.stderr)
            
            return result.stdout
        
        success, result = self.error_handler.execute_with_retry(
            _execute, (), f"ADB命令: {' '.join(command)}")
        
        return result if success else None
    
    def get_ui_xml(self) -> Optional[str]:
        """获取UI XML（带重试）"""
        def _get_ui_xml():
            # 方法1: 标准uiautomator dump
            try:
                dump_cmd = [self.error_handler.adb_path]
                if self.error_handler.device_id:
                    dump_cmd.extend(["-s", self.error_handler.device_id])
                dump_cmd.extend(["shell", "uiautomator", "dump", "/dev/tty"])
                
                result = subprocess.run(dump_cmd, capture_output=True, 
                                      text=True, timeout=15)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout
            except:
                pass
            
            # 方法2: dump到文件再读取
            try:
                # dump到文件
                dump_cmd = [self.error_handler.adb_path]
                if self.error_handler.device_id:
                    dump_cmd.extend(["-s", self.error_handler.device_id])
                dump_cmd.extend(["shell", "uiautomator", "dump"])
                
                subprocess.run(dump_cmd, capture_output=True, timeout=10)
                
                # 读取文件
                read_cmd = [self.error_handler.adb_path]
                if self.error_handler.device_id:
                    read_cmd.extend(["-s", self.error_handler.device_id])
                read_cmd.extend(["shell", "cat", "/sdcard/window_dump.xml"])
                
                result = subprocess.run(read_cmd, capture_output=True, 
                                      text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout
            except:
                pass
            
            raise RuntimeError("所有UI XML获取方法都失败")
        
        success, result = self.error_handler.execute_with_retry(
            _get_ui_xml, (), "获取UI XML")
        
        return result if success else None


# 单例错误处理器实例
_global_error_handler = None

def get_global_error_handler() -> ADBErrorHandler:
    """获取全局错误处理器实例"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ADBErrorHandler()
    return _global_error_handler

def set_global_device_id(device_id: str):
    """设置全局设备ID"""
    handler = get_global_error_handler()
    handler.set_device_id(device_id)