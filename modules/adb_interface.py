"""ADB接口模块 - 统一管理ADB连接和设备操作"""

import logging
import subprocess
import time
from typing import Optional, Tuple


class ADBInterface:
    """ADB接口类，提供统一的ADB操作接口"""
    
    # 常量定义
    DOUYIN_PACKAGE = "com.ss.android.ugc.aweme"
    DEFAULT_DELAY = 1.0
    DEFAULT_TIMEOUT = 10
    
    def __init__(self, device_id: Optional[str] = None, 
                 adb_path: str = "platform-tools/adb.exe"):
        """初始化ADB接口
        
        Args:
            device_id: 设备ID，如果为None则自动选择第一个设备
            adb_path: ADB可执行文件路径
        """
        self.device_id = device_id
        self.adb_path = adb_path
        self.logger = logging.getLogger(__name__)
        
        # 如果没有指定设备ID，自动检测
        if not self.device_id:
            self._auto_detect_device()

    def _auto_detect_device(self) -> None:
        """自动检测可用设备"""
        devices = self.get_connected_devices()
        if devices:
            self.device_id = devices[0]
            self.logger.info("自动选择设备: %s", self.device_id)
        else:
            self.logger.error("未找到可用设备")

    def get_connected_devices(self) -> list:
        """获取已连接的设备列表"""
        try:
            result = subprocess.run(
                [self.adb_path, "devices"],
                capture_output=True,
                text=True,
                check=True
            )
            
            devices = []
            for line in result.stdout.strip().split('\n')[1:]:
                if line.strip() and 'device' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)
                    
            self.logger.info("找到 %d 个设备: %s", len(devices), devices)
            return devices
            
        except subprocess.CalledProcessError as e:
            self.logger.error("获取设备列表失败: %s", str(e))
            return []

    def check_connection(self) -> bool:
        """检查设备连接状态"""
        if not self.device_id:
            return False
            
        devices = self.get_connected_devices()
        is_connected = self.device_id in devices
        
        if is_connected:
            self.logger.info("设备 %s 连接正常", self.device_id)
        else:
            self.logger.error("设备 %s 未连接", self.device_id)
            
        return is_connected

    def execute_command(self, command: list) -> Optional[str]:
        """执行ADB命令
        
        Args:
            command: 命令参数列表
            
        Returns:
            命令输出结果或None
        """
        if not self.device_id:
            self.logger.error("未指定设备ID")
            return None
            
        full_command = [self.adb_path, "-s", self.device_id] + command
        
        try:
            self.logger.debug("执行命令: %s", " ".join(full_command))
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=True
            )
            
            self.logger.debug("命令执行成功")
            if result.stdout:
                return result.stdout.strip()
            else:
                return ""
            
        except subprocess.CalledProcessError as e:
            self.logger.error("命令执行失败: %s", str(e))
            return None
        except Exception as e:
            self.logger.error("命令执行异常: %s", str(e))
            return None

    def get_screen_size(self) -> Optional[Tuple[int, int]]:
        """获取屏幕尺寸"""
        result = self.execute_command([
            "shell", "wm", "size"
        ])
        
        if result:
            try:
                # 解析输出如: "Physical size: 1080x1920"
                size_str = result.split(": ")[1]
                width, height = map(int, size_str.split("x"))
                self.logger.debug("屏幕尺寸: %dx%d", width, height)
                return (width, height)
            except (IndexError, ValueError) as e:
                self.logger.error("解析屏幕尺寸失败: %s", str(e))
                
        return None

    def get_ui_xml(self) -> Optional[str]:
        """获取当前UI的XML结构，使用多种方法重试"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            self.logger.debug("获取UI XML - 第%d次尝试", attempt + 1)
            
            # 尝试方法1: 标准dump到文件
            xml_content = self._try_standard_dump()
            if xml_content:
                return xml_content
            
            # 尝试方法2: 强制等待后重试
            if attempt == 0:
                self.logger.debug("标准dump失败，等待设备稳定后重试")
                time.sleep(2)
                xml_content = self._try_standard_dump()
                if xml_content:
                    return xml_content
            
            # 尝试方法3: 使用压缩dump (Android 7+)
            if attempt == 1:
                xml_content = self._try_compressed_dump()
                if xml_content:
                    return xml_content
            
            # 最后尝试：直接输出到stdout（容错性最高）
            if attempt == max_attempts - 1:
                xml_content = self._try_stdout_dump()
                if xml_content:
                    return xml_content
        
        self.logger.error("所有UI获取方法都失败了")
        return None

    def _try_standard_dump(self) -> Optional[str]:
        """尝试标准的dump到文件方法"""
        try:
            # 先清除旧文件
            self.execute_command([
                "shell", "rm", "-f", "/sdcard/window_dump.xml"
            ])
            
            # dump UI结构
            dump_result = self.execute_command([
                "shell", "uiautomator", "dump", "/sdcard/window_dump.xml"
            ])
            
            if dump_result is not None and "ERROR:" not in str(dump_result):
                # 等待文件写入完成
                time.sleep(1)
                
                # 读取文件内容
                xml_result = self.execute_command([
                    "shell", "cat", "/sdcard/window_dump.xml"
                ])
                
                if xml_result and len(xml_result) > 100 and "<?xml" in xml_result:
                    # 验证XML格式
                    if xml_result.count("<?xml") == 1:
                        self.logger.debug("标准dump成功，XML长度: %d", len(xml_result))
                        return xml_result
                    else:
                        self.logger.warning("XML内容包含重复头部，尝试清理")
                        # 只保留第一个XML文档
                        first_end = xml_result.find("</hierarchy>")
                        if first_end > 0:
                            clean_xml = xml_result[:first_end + len("</hierarchy>")]
                            self.logger.debug("清理后XML长度: %d", len(clean_xml))
                            return clean_xml
                
                self.logger.error("读取的XML内容无效")
                return None
                
            self.logger.error("UI dump执行失败")
            return None
            
        except Exception as e:
            self.logger.error("获取UI XML异常: %s", str(e))
            return None

    def tap(self, x: int, y: int) -> bool:
        """点击屏幕指定位置
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            是否执行成功
        """
        result = self.execute_command([
            "shell", "input", "tap", str(x), str(y)
        ])
        
        success = result is not None
        if success:
            self.logger.info("点击坐标 (%d, %d) 成功", x, y)
            time.sleep(self.DEFAULT_DELAY)
        else:
            self.logger.error("点击坐标 (%d, %d) 失败", x, y)
            
        return success

    def swipe(self, x1: int, y1: int, x2: int, y2: int, 
              duration: int = 300) -> bool:
        """滑动屏幕
        
        Args:
            x1, y1: 起始坐标
            x2, y2: 结束坐标  
            duration: 滑动时长(毫秒)
            
        Returns:
            是否执行成功
        """
        result = self.execute_command([
            "shell", "input", "swipe", 
            str(x1), str(y1), str(x2), str(y2), str(duration)
        ])
        
        success = result is not None
        if success:
            self.logger.info("滑动 (%d,%d) -> (%d,%d) 成功", x1, y1, x2, y2)
            time.sleep(self.DEFAULT_DELAY)
        else:
            self.logger.error("滑动失败")
            
        return success

    def start_app(self, package_name: str = None) -> bool:
        """启动应用
        
        Args:
            package_name: 应用包名，默认为抖音
            
        Returns:
            是否启动成功
        """
        if not package_name:
            package_name = self.DOUYIN_PACKAGE
            
        result = self.execute_command([
            "shell", "monkey", "-p", package_name,
            "-c", "android.intent.category.LAUNCHER", "1"
        ])
        
        success = result is not None
        if success:
            self.logger.info("启动应用 %s 成功", package_name)
            time.sleep(3)  # 等待应用启动
        else:
            self.logger.error("启动应用 %s 失败", package_name)
            
        return success

    def stop_app(self, package_name: str = None) -> bool:
        """停止应用
        
        Args:
            package_name: 应用包名，默认为抖音
            
        Returns:
            是否停止成功
        """
        if not package_name:
            package_name = self.DOUYIN_PACKAGE
            
        result = self.execute_command([
            "shell", "am", "force-stop", package_name
        ])
        
        success = result is not None
        if success:
            self.logger.info("停止应用 %s 成功", package_name)
        else:
            self.logger.error("停止应用 %s 失败", package_name)
            
        return success

    def is_app_running(self, package_name: str = None) -> bool:
        """检查应用是否在运行
        
        Args:
            package_name: 应用包名，默认为抖音
            
        Returns:
            应用是否在运行
        """
        if not package_name:
            package_name = self.DOUYIN_PACKAGE
            
        result = self.execute_command([
            "shell", "dumpsys", "activity", "|", "grep", f"mCurrentFocus.*{package_name}"
        ])
        
        is_running = result is not None and package_name in result
        self.logger.debug("应用 %s 运行状态: %s", package_name, is_running)
        
        return is_running

    def get_current_activity(self) -> Optional[str]:
        """获取当前活动的Activity"""
        result = self.execute_command([
            "shell", "dumpsys", "activity", "activities", "|", 
            "grep", "mCurrentFocus"
        ])
        
        if result:
            try:
                # 解析输出获取Activity名称
                activity = result.split("/")[-1].split("}")[0]
                self.logger.debug("当前Activity: %s", activity)
                return activity
            except (IndexError, AttributeError):
                pass
                
        return None

    def wait_for_element_text(self, text: str, timeout: int = None) -> bool:
        """等待包含指定文本的元素出现
        
        Args:
            text: 要等待的文本
            timeout: 超时时间，默认使用DEFAULT_TIMEOUT
            
        Returns:
            是否找到元素
        """
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT
            
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            xml_content = self.get_ui_xml()
            if xml_content and text in xml_content:
                self.logger.info("找到包含文本 '%s' 的元素", text)
                return True
            time.sleep(1)
            
        self.logger.warning("等待文本 '%s' 超时", text)
        return False

    def is_douyin_in_splash(self) -> bool:
        """检查抖音是否在启动画面"""
        try:
            result = self.execute_command([
                "shell", "dumpsys", "activity", "|", "grep", 
                "mCurrentFocus.*com.ss.android.ugc.aweme"
            ])
            
            if not result:
                return False
            
            # 抖音启动画面Activity名称模式
            splash_patterns = [
                "SplashActivity",
                "LaunchActivity", 
                "WelcomeActivity",
                "InitActivity",
                "StartActivity"
            ]
            
            is_splash = any(pattern in result for pattern in splash_patterns)
            
            if is_splash:
                self.logger.info("检测到抖音在启动画面: %s", result.strip())
            else:
                self.logger.debug("抖音当前状态: %s", result.strip())
            
            return is_splash
            
        except Exception as e:
            self.logger.error("检查启动画面状态失败: %s", str(e))
            return False

    def wait_for_douyin_main_interface(self, timeout: int = 30) -> bool:
        """等待抖音主界面加载完成"""
        self.logger.info("等待抖音主界面加载完成...")
        
        start_time = time.time()
        check_interval = 2  # 每2秒检查一次
        splash_detected = False
        
        while time.time() - start_time < timeout:
            elapsed_time = int(time.time() - start_time)
            
            # 检查是否还在启动画面
            if self.is_douyin_in_splash():
                splash_detected = True
                self.logger.info("启动画面检测中... (%ds/%ds)", 
                               elapsed_time, timeout)
                time.sleep(check_interval)
                continue
            
            # 如果之前检测到启动画面，现在不在了，说明正在加载
            if splash_detected:
                self.logger.info("启动画面结束，等待主界面就绪...")
                time.sleep(3)  # 给主界面一些加载时间
            
            # 检查UI是否可获取且包含主界面元素
            xml_content = self.get_ui_xml()
            if xml_content and self._is_main_interface_ready(xml_content):
                self.logger.info("✅ 抖音主界面加载完成")
                return True
            
            self.logger.debug("主界面尚未就绪，继续等待... (%ds/%ds)", 
                            elapsed_time, timeout)
            time.sleep(check_interval)
        
        self.logger.warning("等待抖音主界面超时")
        return False

    def _is_main_interface_ready(self, xml_content: str) -> bool:
        """检查是否为主界面就绪状态"""
        if not xml_content:
            return False
        
        # 检查主界面特征元素
        main_indicators = [
            "我",  # 底部导航栏
            "推荐",  # 顶部标签
            "关注",  # 顶部标签
            "直播",  # 顶部标签
        ]
        
        # 至少要有2个主界面指示元素
        found_indicators = sum(1 for indicator in main_indicators 
                              if indicator in xml_content)
        
        is_ready = found_indicators >= 2
        self.logger.debug("主界面指示元素: %d/4, 就绪状态: %s", 
                         found_indicators, is_ready)
        
        return is_ready

    def _try_compressed_dump(self) -> Optional[str]:
        """尝试压缩dump方法 (Android 7+)"""
        try:
            self.logger.debug("尝试压缩dump方法")
            
            # 清除旧文件
            self.execute_command(["shell", "rm", "-f", self.UI_DUMP_PATH])
            
            # 使用压缩dump
            dump_result = self.execute_command([
                "shell", "uiautomator", "dump", "--compressed", self.UI_DUMP_PATH
            ])
            
            if dump_result is not None and "ERROR:" not in str(dump_result):
                time.sleep(1)
                
                # 读取压缩文件
                xml_result = self.execute_command([
                    "shell", "cat", self.UI_DUMP_PATH
                ])
                
                if (xml_result and len(xml_result) > self.MIN_XML_LENGTH and 
                        "<?xml" in xml_result):
                    self.logger.debug("压缩dump成功，XML长度: %d", len(xml_result))
                    return xml_result
            
            return None
            
        except Exception as e:
            self.logger.debug("压缩dump失败: %s", str(e))
            return None

    def _try_stdout_dump(self) -> Optional[str]:
        """尝试直接输出到stdout的dump方法"""
        try:
            self.logger.debug("尝试stdout dump方法")
            
            # 直接dump到stdout
            result = self.execute_command([
                "exec-out", "uiautomator", "dump", "/dev/tty"
            ])
            
            if result and len(result) > self.MIN_XML_LENGTH:
                # 清理可能的错误信息
                if "ERROR:" in result:
                    # 尝试提取XML部分
                    xml_start = result.find("<?xml")
                    if xml_start > 0:
                        result = result[xml_start:]
                
                if "<?xml" in result and "</hierarchy>" in result:
                    self.logger.debug("stdout dump成功，XML长度: %d", len(result))
                    return result
            
            return None
            
        except Exception as e:
            self.logger.debug("stdout dump失败: %s", str(e))
            return None