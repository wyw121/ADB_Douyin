"""
ADB 长连接管理模块
用于建立和维护与Android设备的ADB连接，执行ADB命令
"""

import logging
import os
import subprocess
import time
from typing import Dict, List, Optional


class ADBConnection:
    """ADB连接管理类"""

    def __init__(self, device_id: Optional[str] = None):
        """
        初始化ADB连接

        Args:
            device_id: 设备ID，如果为None则使用第一个可用设备
        """
        self.device_id = device_id
        self.logger = self._setup_logger()
        # 设置本地ADB工具路径
        self.adb_path = self._get_adb_path()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("ADBConnection")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _get_adb_path(self) -> str:
        """获取ADB工具路径"""
        # 优先使用项目目录下的ADB工具
        current_dir = os.path.dirname(os.path.abspath(__file__))
        local_adb = os.path.join(current_dir, "platform-tools", "adb.exe")

        if os.path.exists(local_adb):
            return local_adb

        # 如果本地没有，尝试使用系统PATH中的adb
        return "adb"

    def execute_command(self, command: str, timeout: int = 30) -> Dict[str, any]:
        """
        执行ADB命令

        Args:
            command: ADB命令（不包含adb前缀）
            timeout: 命令超时时间（秒）

        Returns:
            包含执行结果的字典：{'success': bool, 'output': str, 'error': str}
        """
        try:
            # 构建完整的ADB命令
            if self.device_id:
                full_command = f'"{self.adb_path}" -s {self.device_id} ' f"{command}"
            else:
                full_command = f'"{self.adb_path}" {command}'

            self.logger.info(f"执行命令: {full_command}")

            # 执行命令
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="ignore",  # 忽略编码错误
            )

            if result.returncode == 0:
                self.logger.info("命令执行成功")
                return {"success": True, "output": result.stdout.strip(), "error": None}
            else:
                self.logger.error(f"命令执行失败: {result.stderr}")
                return {
                    "success": False,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip(),
                }

        except subprocess.TimeoutExpired:
            self.logger.error(f"命令执行超时: {command}")
            return {
                "success": False,
                "output": None,
                "error": f"命令执行超时 ({timeout}秒)",
            }
        except Exception as e:
            self.logger.error(f"命令执行异常: {str(e)}")
            return {"success": False, "output": None, "error": str(e)}

    def get_devices(self) -> List[str]:
        """获取连接的设备列表"""
        result = self.execute_command("devices")
        if result["success"]:
            lines = result["output"].split("\n")[1:]  # 跳过标题行
            devices = []
            for line in lines:
                line = line.strip()
                if line and "\tdevice" in line:
                    device_id = line.split("\t")[0]
                    devices.append(device_id)
            return devices
        return []

    def check_device_connection(self) -> bool:
        """检查设备连接状态"""
        devices = self.get_devices()
        if not devices:
            self.logger.error("没有检测到连接的设备")
            return False

        if self.device_id and self.device_id not in devices:
            self.logger.error(f"指定的设备 {self.device_id} 未连接")
            return False

        if not self.device_id:
            self.device_id = devices[0]
            self.logger.info(f"使用第一个可用设备: {self.device_id}")

        return True

    def tap(self, x: int, y: int) -> bool:
        """
        点击屏幕指定坐标

        Args:
            x: X坐标
            y: Y坐标

        Returns:
            是否执行成功
        """
        result = self.execute_command(f"shell input tap {x} {y}")
        if result["success"]:
            self.logger.info(f"点击坐标 ({x}, {y}) 成功")
            return True
        else:
            self.logger.error(f"点击坐标 ({x}, {y}) 失败: {result['error']}")
            return False

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        """
        滑动屏幕

        Args:
            x1, y1: 起始坐标
            x2, y2: 结束坐标
            duration: 滑动持续时间（毫秒）

        Returns:
            是否执行成功
        """
        command = f"shell input swipe {x1} {y1} {x2} {y2} {duration}"
        result = self.execute_command(command)
        if result["success"]:
            self.logger.info(f"滑动 ({x1},{y1}) -> ({x2},{y2}) 成功")
            return True
        else:
            self.logger.error(f"滑动失败: {result['error']}")
            return False

    def input_text(self, text: str) -> bool:
        """
        输入文本

        Args:
            text: 要输入的文本

        Returns:
            是否执行成功
        """
        # 转义特殊字符
        escaped_text = text.replace(" ", "%s").replace("&", r"\&")
        result = self.execute_command(f"shell input text '{escaped_text}'")
        if result["success"]:
            self.logger.info(f"输入文本 '{text}' 成功")
            return True
        else:
            self.logger.error(f"输入文本失败: {result['error']}")
            return False

    def press_key(self, keycode: str) -> bool:
        """
        按键

        Args:
            keycode: 按键代码（如 KEYCODE_BACK, KEYCODE_HOME等）

        Returns:
            是否执行成功
        """
        result = self.execute_command(f"shell input keyevent {keycode}")
        if result["success"]:
            self.logger.info(f"按键 {keycode} 成功")
            return True
        else:
            self.logger.error(f"按键失败: {result['error']}")
            return False

    def get_screen_size(self) -> Optional[tuple]:
        """
        获取屏幕尺寸

        Returns:
            (width, height) 或 None
        """
        result = self.execute_command("shell wm size")
        if result["success"]:
            output = result["output"]
            if "Physical size:" in output:
                size_str = output.split("Physical size:")[1].strip()
                width, height = map(int, size_str.split("x"))
                return (width, height)
        return None

    def get_ui_dump(self) -> Optional[str]:
        """
        获取当前界面的UI结构XML

        Returns:
            UI XML字符串或None
        """
        # 先导出UI结构到设备
        result = self.execute_command("shell uiautomator dump")
        if not result["success"]:
            self.logger.error("导出UI结构失败")
            return None

        # 读取UI结构文件
        result = self.execute_command("shell cat /sdcard/window_dump.xml")
        if result["success"]:
            return result["output"]
        else:
            self.logger.error("读取UI结构文件失败")
            return None

    def get_ui_xml(self) -> Optional[str]:
        """
        获取当前界面的UI结构XML（兼容方法）

        Returns:
            UI XML字符串或None
        """
        return self.get_ui_dump()

    def force_stop_app(self, package_name: str) -> bool:
        """
        强制停止应用

        Args:
            package_name: 包名

        Returns:
            是否停止成功
        """
        command = f"shell am force-stop {package_name}"
        result = self.execute_command(command)
        
        if result["success"]:
            self.logger.info("强制停止应用 %s 成功", package_name)
            return True
        else:
            self.logger.error("强制停止应用失败: %s", result["error"])
            return False

    def start_app(self, package_name: str, activity_name: str = None) -> bool:
        """
        启动应用

        Args:
            package_name: 包名
            activity_name: Activity名称（可选）

        Returns:
            是否启动成功
        """
        if activity_name:
            command = f"shell am start -n {package_name}/{activity_name}"
        else:
            command = (
                f"shell monkey -p {package_name} "
                f"-c android.intent.category.LAUNCHER 1"
            )

        result = self.execute_command(command)
        if result["success"]:
            self.logger.info("启动应用 %s 成功", package_name)
            return True
        else:
            self.logger.error("启动应用失败: %s", result["error"])
            return False

    def wait_and_retry(self, operation, max_retries: int = 3, delay: float = 1.0):
        """
        带重试的操作执行

        Args:
            operation: 要执行的操作函数
            max_retries: 最大重试次数
            delay: 重试间隔（秒）

        Returns:
            操作结果
        """
        for attempt in range(max_retries):
            try:
                result = operation()
                if result:
                    return result
            except Exception as e:
                self.logger.warning(
                    "操作失败 (尝试 %d/%d): %s", attempt + 1, max_retries, str(e)
                )

            if attempt < max_retries - 1:
                time.sleep(delay)

        self.logger.error("操作失败，已重试 %d 次", max_retries)
        return None
