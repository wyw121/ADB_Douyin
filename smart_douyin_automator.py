#!/usr/bin/env python3
"""
智能抖音自动化程序
整合了所有功能的最终版本，支持：
1. 自动检测和启动抖音
2. 多分辨率智能适配
3. 简体/繁体/乱码文字智能识别
4. 智能导航到通讯录
5. 自动批量关注
"""

import logging
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class SmartADBConnection:
    """智能ADB连接管理"""

    def __init__(self, device_id: Optional[str] = None):
        self.device_id = device_id
        self.logger = self._setup_logger()
        self.adb_path = self._get_adb_path()
        self.screen_size = None

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("SmartADB")
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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        local_adb = os.path.join(current_dir, "platform-tools", "adb.exe")

        if os.path.exists(local_adb):
            return local_adb
        return "adb"

    def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """执行ADB命令"""
        try:
            if self.device_id:
                full_command = f'"{self.adb_path}" -s {self.device_id} ' f"{command}"
            else:
                full_command = f'"{self.adb_path}" {command}'

            self.logger.debug(f"执行命令: {full_command}")

            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="ignore",
            )

            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip(), "error": None}
            else:
                return {
                    "success": False,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip(),
                }

        except Exception as e:
            self.logger.error(f"命令执行异常: {str(e)}")
            return {"success": False, "output": None, "error": str(e)}

    def check_connection(self) -> bool:
        """检查设备连接"""
        result = self.execute_command("devices")
        if result["success"]:
            lines = result["output"].split("\n")[1:]
            devices = []
            for line in lines:
                line = line.strip()
                if line and "\tdevice" in line:
                    device_id = line.split("\t")[0]
                    devices.append(device_id)

            if not devices:
                self.logger.error("没有检测到连接的设备")
                return False

            if not self.device_id:
                self.device_id = devices[0]
                self.logger.info(f"使用设备: {self.device_id}")

            return True
        return False

    def get_current_activity(self) -> Optional[str]:
        """获取当前Activity"""
        result = self.execute_command("shell dumpsys activity")
        if result["success"]:
            output = result["output"]
            for line in output.split("\n"):
                focus_check = "mCurrentFocus" in line
                app_check = "com.ss.android.ugc.aweme" in line
                if focus_check and app_check:
                    # 提取Activity名称
                    parts = line.split("/")
                    if len(parts) > 1:
                        activity = parts[1].split("}")[0]
                        return activity
        return None

    def get_screen_size(self) -> Optional[Tuple[int, int]]:
        """获取屏幕尺寸"""
        if self.screen_size:
            return self.screen_size

        result = self.execute_command("shell wm size")
        if result["success"]:
            output = result["output"]
            if "Physical size:" in output:
                size_str = output.split("Physical size:")[1].strip()
                width, height = map(int, size_str.split("x"))
                self.screen_size = (width, height)
                self.logger.info(f"屏幕尺寸: {width}x{height}")
                return self.screen_size
        return None

    def tap(self, x: int, y: int) -> bool:
        """点击屏幕"""
        result = self.execute_command(f"shell input tap {x} {y}")
        return result["success"]

    def get_ui_xml(self) -> Optional[str]:
        """获取UI XML"""
        # 导出UI结构
        result = self.execute_command("shell uiautomator dump")
        if not result["success"]:
            return None

        # 读取UI文件
        result = self.execute_command("shell cat /sdcard/window_dump.xml")
        if result["success"]:
            return result["output"]
        return None

    def start_app(self, package_name: str) -> bool:
        """启动应用"""
        # 优先使用具体的Activity启动（针对抖音）
        if package_name == "com.ss.android.ugc.aweme":
            cmd = "shell am start -n " "com.ss.android.ugc.aweme/.splash.SplashActivity"
        else:
            cmd = (
                f"shell monkey -p {package_name} "
                f"-c android.intent.category.LAUNCHER 1"
            )

        result = self.execute_command(cmd)
        return result["success"]

    def is_app_running(self, package_name: str) -> bool:
        """检查应用是否运行"""
        import platform

        # 根据操作系统选择合适的命令
        filter_cmd = "findstr" if platform.system() == "Windows" else "grep"

        # 方法1：检查进程
        cmd1 = f"shell ps | {filter_cmd} {package_name}"
        result1 = self.execute_command(cmd1)
        if result1["success"] and package_name in result1["output"]:
            return True

        # 方法2：检查当前焦点窗口
        cmd2 = f"shell dumpsys activity | {filter_cmd} mCurrentFocus"
        result2 = self.execute_command(cmd2)
        if result2["success"] and package_name in result2["output"]:
            return True

        # 方法3：检查最近任务
        cmd3 = f"shell dumpsys activity recents | {filter_cmd} {package_name}"
        result3 = self.execute_command(cmd3)
        if result3["success"] and package_name in result3["output"]:
            return True

        return False


class SmartUIElement:
    """智能UI元素类"""

    def __init__(self, node: ET.Element):
        self.node = node
        self.attributes = node.attrib
        self.text = self.attributes.get("text", "")
        self.content_desc = self.attributes.get("content-desc", "")
        self.resource_id = self.attributes.get("resource-id", "")
        self.class_name = self.attributes.get("class", "")
        self.bounds = self._parse_bounds()
        clickable_attr = self.attributes.get("clickable", "false")
        self.clickable = clickable_attr.lower() == "true"
        self.enabled = self.attributes.get("enabled", "true").lower() == "true"

    def _parse_bounds(self) -> Optional[Tuple[int, int, int, int]]:
        """解析边界坐标"""
        bounds_str = self.attributes.get("bounds", "")
        if bounds_str:
            pattern = r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]"
            match = re.match(pattern, bounds_str)
            if match:
                return tuple(map(int, match.groups()))
        return None

    def get_center(self) -> Optional[Tuple[int, int]]:
        """获取中心坐标"""
        if self.bounds:
            x1, y1, x2, y2 = self.bounds
            return ((x1 + x2) // 2, (y1 + y2) // 2)
        return None

    def is_clickable(self) -> bool:
        """判断是否可点击"""
        return self.clickable and self.enabled and self.bounds is not None


class SmartTextMatcher:
    """智能文本匹配器 - 支持简体/繁体/乱码识别"""

    def __init__(self):
        # 定义关键词映射表
        self.keyword_variants = {
            "我": ["我", "鎴?", "Me"],
            "添加朋友": [
                "添加朋友",
                "添加好友",
                "加朋友",
                "娣诲姞鏈嬪弸",
                "Add Friends",
            ],
            "通讯录": [
                "通讯录",
                "联系人",
                "通信录",
                "閫氳褰?",
                "鎵嬫満閫氳褰?",
                "Contacts",
            ],
            "关注": ["关注", "+关注", "鍏虫敞", "Follow"],
            "返回": ["返回", "后退", "杩斿洖", "Back", "←", "<"],
            "搜索": ["搜索", "鎼滅储", "Search"],
        }

        # 编译正则表达式模式
        self.patterns = {}
        for key, variants in self.keyword_variants.items():
            pattern = "|".join(re.escape(v) for v in variants)
            self.patterns[key] = re.compile(pattern, re.IGNORECASE)

    def match_keyword(self, text: str, keyword: str) -> bool:
        """匹配关键词"""
        if keyword in self.patterns:
            return bool(self.patterns[keyword].search(text))
        return keyword.lower() in text.lower()

    def find_best_match(self, text: str) -> Optional[str]:
        """找到最佳匹配的关键词"""
        for keyword, pattern in self.patterns.items():
            if pattern.search(text):
                return keyword
        return None


class SmartUIAnalyzer:
    """智能UI分析器"""

    def __init__(self):
        self.logger = logging.getLogger("SmartUI")
        self.elements = []
        self.text_matcher = SmartTextMatcher()
        self.screen_size = None

    def parse_xml(self, xml_content: str, screen_size: Tuple[int, int] = None) -> bool:
        """解析XML内容"""
        try:
            self.screen_size = screen_size
            root = ET.fromstring(xml_content)
            self.elements = []
            self._parse_node(root)
            self.logger.info(f"解析UI成功，共 {len(self.elements)} 个元素")
            return True
        except Exception as e:
            self.logger.error(f"解析XML失败: {str(e)}")
            return False

    def _parse_node(self, node: ET.Element):
        """递归解析节点"""
        element = SmartUIElement(node)
        self.elements.append(element)
        for child in node:
            self._parse_node(child)

    def find_elements_by_keyword(
        self, keyword: str, clickable_only: bool = True
    ) -> List[SmartUIElement]:
        """根据关键词查找元素"""
        matches = []
        for element in self.elements:
            combined_text = element.text + " " + element.content_desc
            if self.text_matcher.match_keyword(combined_text, keyword):
                if not clickable_only or element.is_clickable():
                    matches.append(element)

        self.logger.info(f"关键词 '{keyword}' 找到 {len(matches)} 个匹配元素")
        return matches

    def find_bottom_navigation_element(self, keyword: str) -> Optional[SmartUIElement]:
        """查找底部导航元素"""
        candidates = self.find_elements_by_keyword(keyword)
        if not candidates:
            return None

        if not self.screen_size:
            return candidates[0]  # 没有屏幕尺寸信息时返回第一个

        # 找到最靠近屏幕底部的元素
        screen_height = self.screen_size[1]
        bottom_candidates = []

        for element in candidates:
            center = element.get_center()
            if center and center[1] > screen_height * 0.8:  # 在屏幕下方20%区域
                bottom_candidates.append(element)

        if bottom_candidates:
            # 返回最靠下的元素
            return max(bottom_candidates, key=lambda e: e.get_center()[1])

        return candidates[0]  # 如果没有在底部区域的，返回第一个匹配的

    def find_add_friend_button(self) -> Optional[SmartUIElement]:
        """查找添加朋友按钮"""
        return self.find_best_element_by_keyword("添加朋友")

    def find_contacts_button(self) -> Optional[SmartUIElement]:
        """查找通讯录按钮"""
        return self.find_best_element_by_keyword("通讯录")

    def is_on_profile_page(self) -> bool:
        """检查是否在个人资料页面"""
        # 检查是否有"添加朋友"按钮
        add_friend_button = self.find_add_friend_button()
        if add_friend_button:
            return True

        # 检查底部导航的"我"按钮是否选中
        me_buttons = self.find_elements_by_keyword("我", clickable_only=False)
        for button in me_buttons:
            center = button.get_center()
            if button.selected and center and center[1] > 1400:
                return True

        return False

    def is_on_add_friends_page(self) -> bool:
        """检查是否在添加朋友页面"""
        # 检查页面标题
        title_elements = self.find_elements_by_keyword("添加朋友", clickable_only=False)
        for element in title_elements:
            if element.text == "添加朋友" and element.get_center():
                return True

        # 检查是否有"通讯录"按钮
        contacts_button = self.find_contacts_button()
        return contacts_button is not None

    def find_best_element_by_keyword(self, keyword: str) -> Optional[SmartUIElement]:
        """找到最佳匹配的元素"""
        candidates = self.find_elements_by_keyword(keyword)
        if not candidates:
            return None

        # 优先选择文本完全匹配的元素
        for element in candidates:
            if self.text_matcher.match_keyword(element.text, keyword):
                return element

        # 否则选择描述匹配的元素
        for element in candidates:
            if self.text_matcher.match_keyword(element.content_desc, keyword):
                return element

        return candidates[0]

    def find_follow_buttons(self) -> List[SmartUIElement]:
        """查找所有关注按钮"""
        return self.find_elements_by_keyword("关注")


class SmartDouyinAutomator:
    """智能抖音自动化程序"""

    DOUYIN_PACKAGE = "com.ss.android.ugc.aweme"

    def __init__(self, device_id: Optional[str] = None):
        self.adb = SmartADBConnection(device_id)
        self.ui_analyzer = SmartUIAnalyzer()
        self.logger = self._setup_logger()

        # 创建日志目录
        os.makedirs("logs", exist_ok=True)

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("SmartDouyin")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S"
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

            # 文件处理器
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"logs/smart_douyin_{date_str}.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_formatter = logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        return logger

    def check_connection(self) -> bool:
        """检查ADB连接"""
        return self.adb.check_connection()

    def is_douyin_running(self) -> bool:
        """检查抖音是否运行"""
        return self.adb.is_app_running(self.DOUYIN_PACKAGE)

    def start_douyin(self) -> bool:
        """启动抖音"""
        if self.is_douyin_running():
            self.logger.info("抖音已经在运行")
            return True

        self.logger.info("启动抖音...")
        success = self.adb.start_app(self.DOUYIN_PACKAGE)
        if success:
            time.sleep(5)  # 等待启动
            return self.is_douyin_running()
        return False

    def get_current_ui(self) -> bool:
        """获取当前UI"""
        xml_content = self.adb.get_ui_xml()
        if xml_content:
            screen_size = self.adb.get_screen_size()
            return self.ui_analyzer.parse_xml(xml_content, screen_size)
        return False

    def navigate_to_profile(self) -> bool:
        """导航到个人资料页面"""
        self.logger.info("导航到个人资料页面...")

        # 检查当前Activity
        current_activity = self.adb.get_current_activity()
        if current_activity:
            self.logger.info(f"当前Activity: {current_activity}")

            # 如果已经在个人资料相关页面，直接返回成功
            if "MainActivity" in current_activity:
                if not self.get_current_ui():
                    self.logger.error("获取UI失败")
                    return False

                # 检查是否已经在个人资料页面
                if self.ui_analyzer.is_on_profile_page():
                    self.logger.info("已经在个人资料页面")
                    return True

        if not self.get_current_ui():
            self.logger.error("获取UI失败")
            return False

        # 查找底部的"我"按钮
        profile_button = self.ui_analyzer.find_bottom_navigation_element("我")
        if not profile_button:
            self.logger.error("未找到'我'按钮")
            return False

        center = profile_button.get_center()
        if not center:
            self.logger.error("'我'按钮坐标获取失败")
            return False

        self.logger.info(f"点击'我'按钮: {center}")
        success = self.adb.tap(center[0], center[1])

        if success:
            time.sleep(3)  # 等待页面加载
            return True

        return False

    def navigate_to_add_friends(self) -> bool:
        """导航到添加朋友页面"""
        self.logger.info("导航到添加朋友页面...")

        # 检查当前Activity
        current_activity = self.adb.get_current_activity()
        if current_activity:
            self.logger.info(f"当前Activity: {current_activity}")

            # 如果已经在添加朋友页面，直接返回成功
            if "RawAddFriendsActivity" in current_activity:
                self.logger.info("已经在添加朋友页面")
                return True

        if not self.get_current_ui():
            return False

        # 检查UI是否已经在添加朋友页面
        if self.ui_analyzer.is_on_add_friends_page():
            self.logger.info("UI检测：已经在添加朋友页面")
            return True

        add_friend_button = self.ui_analyzer.find_add_friend_button()
        if not add_friend_button:
            self.logger.error("未找到'添加朋友'按钮")
            return False

        center = add_friend_button.get_center()
        if not center:
            return False

        self.logger.info(f"点击'添加朋友'按钮: {center}")
        success = self.adb.tap(center[0], center[1])

        if success:
            time.sleep(3)
            return True

        return False

    def navigate_to_contacts(self) -> bool:
        """导航到通讯录页面"""
        self.logger.info("导航到通讯录页面...")

        if not self.get_current_ui():
            return False

        contacts_button = self.ui_analyzer.find_contacts_button()
        if not contacts_button:
            self.logger.error("未找到'通讯录'按钮")
            return False

        center = contacts_button.get_center()
        if not center:
            return False

        self.logger.info(f"点击'通讯录'按钮: {center}")
        success = self.adb.tap(center[0], center[1])

        if success:
            time.sleep(3)
            return True

        return False

    def follow_contacts(self, max_count: int = 5) -> int:
        """关注通讯录朋友"""
        self.logger.info(f"开始关注通讯录朋友，最多 {max_count} 个")

        if not self.get_current_ui():
            return 0

        follow_buttons = self.ui_analyzer.find_follow_buttons()
        self.logger.info(f"找到 {len(follow_buttons)} 个关注按钮")

        if not follow_buttons:
            self.logger.warning("未找到可关注的朋友")
            return 0

        followed_count = 0
        max_follow = min(max_count, len(follow_buttons))

        for i in range(max_follow):
            button = follow_buttons[i]
            center = button.get_center()

            if center:
                self.logger.info(f"点击关注按钮 {i+1}/{max_follow}: {center}")
                success = self.adb.tap(center[0], center[1])

                if success:
                    followed_count += 1
                    self.logger.info(f"成功关注朋友 {i+1}")
                    time.sleep(2)  # 等待界面更新
                else:
                    self.logger.warning(f"关注朋友 {i+1} 失败")
            else:
                self.logger.warning(f"关注按钮 {i+1} 坐标获取失败")

        self.logger.info(f"关注操作完成，成功关注 {followed_count} 个朋友")
        return followed_count

    def auto_follow_contacts(self, max_count: int = 5) -> bool:
        """自动执行完整的通讯录关注流程"""
        try:
            print("🎯 智能抖音自动化程序启动")
            print("=" * 50)

            # 1. 检查连接
            print("🔧 检查ADB连接...")
            if not self.check_connection():
                print("❌ ADB连接失败")
                return False
            print(f"✅ ADB连接成功: {self.adb.device_id}")

            # 2. 启动抖音
            print("🚀 启动抖音...")
            if not self.start_douyin():
                print("❌ 抖音启动失败")
                return False
            print("✅ 抖音启动成功")

            # 3. 导航到个人资料
            print("👤 导航到个人资料页面...")
            if not self.navigate_to_profile():
                print("❌ 导航到个人资料失败")
                return False
            print("✅ 进入个人资料页面")

            # 4. 导航到添加朋友
            print("👥 导航到添加朋友页面...")
            if not self.navigate_to_add_friends():
                print("❌ 导航到添加朋友失败")
                return False
            print("✅ 进入添加朋友页面")

            # 5. 导航到通讯录
            print("📞 导航到通讯录页面...")
            if not self.navigate_to_contacts():
                print("❌ 导航到通讯录失败")
                return False
            print("✅ 进入通讯录页面")

            # 6. 关注朋友
            print(f"🎯 开始关注通讯录朋友（最多 {max_count} 个）...")
            followed_count = self.follow_contacts(max_count)

            if followed_count > 0:
                print(f"🎉 任务完成！成功关注了 {followed_count} 个朋友")
                return True
            else:
                print("😔 没有找到可关注的朋友")
                return False

        except Exception as e:
            self.logger.exception("自动化流程异常")
            print(f"❌ 程序异常: {str(e)}")
            return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="智能抖音自动化程序")
    parser.add_argument("--device", "-d", help="指定ADB设备ID")
    parser.add_argument("--count", "-c", type=int, default=5, help="最大关注数量")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")

    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # 创建自动化程序
        automator = SmartDouyinAutomator(args.device)

        # 执行自动化流程
        success = automator.auto_follow_contacts(args.count)

        if success:
            print("\n✅ 程序执行成功！")
            return 0
        else:
            print("\n❌ 程序执行失败！")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        return 2
    except Exception as e:
        print(f"\n💥 程序异常: {str(e)}")
        return 3


if __name__ == "__main__":
    exit(main())
