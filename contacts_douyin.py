#!/usr/bin/env python3
"""抖音通讯录批量关注工具。"""

import argparse
import logging
import sys
import time
from datetime import datetime
from douyin_automator import DouyinAutomator


def setup_logging(log_level: str = "INFO") -> None:
    """设置日志配置"""
    level = getattr(logging, log_level.upper())
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 创建日志文件
    main_log = f"logs/contacts_douyin_main_{date_str}.log"
    debug_log = f"logs/contacts_douyin_debug_{date_str}.log"
    error_log = f"logs/contacts_douyin_error_{date_str}.log"

    # 确保日志目录存在
    import os

    os.makedirs("logs", exist_ok=True)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 清除现有处理器
    root_logger.handlers = []

    # 详细格式
    detailed_formatter = logging.Formatter(
        "%(asctime)s | %(name)-15s | %(levelname)-8s | "
        "%(filename)s:%(lineno)d | %(funcName)s() | %(message)s"
    )

    # 简洁格式
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S"
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 主日志文件
    main_handler = logging.FileHandler(main_log, encoding="utf-8")
    main_handler.setLevel(logging.INFO)
    main_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(main_handler)

    # 调试日志文件
    debug_handler = logging.FileHandler(debug_log, encoding="utf-8")
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(debug_handler)

    # 错误日志文件
    error_handler = logging.FileHandler(error_log, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)

    # 记录启动信息
    logging.info("=" * 60)
    logging.info("抖音通讯录批量关注工具启动")
    logging.info("日志级别: %s", log_level)
    logging.info("主日志: %s", main_log)
    logging.info("调试日志: %s", debug_log)
    logging.info("错误日志: %s", error_log)
    logging.info("=" * 60)


def _find_contacts_text_element(elements) -> object:
    """查找通讯录文本元素"""
    for element in elements:
        if (
            element.is_clickable_element()
            and element.text == "通讯录"
            and element.class_name == "android.widget.TextView"
        ):
            return element
    return None


def _find_clickable_parent(text_element, elements) -> object:
    """查找文本元素的可点击父元素"""
    for parent in elements:
        if (
            parent.is_clickable_element()
            and parent.class_name == "android.widget.LinearLayout"
            and text_element.bounds_contains_in(parent.bounds)
        ):
            return parent
    return None


def click_contacts_button(automator: DouyinAutomator) -> bool:
    """点击通讯录按钮"""
    logger = logging.getLogger(__name__)

    if not automator.get_current_ui():
        logger.error("获取当前UI失败")
        return False

    # 查找通讯录文本元素
    text_element = _find_contacts_text_element(automator.ui_analyzer.elements)
    if not text_element:
        logger.error("未找到通讯录文本")
        return False

    # 查找可点击的父元素
    contacts_button = _find_clickable_parent(
        text_element, automator.ui_analyzer.elements
    )
    if not contacts_button:
        logger.error("未找到通讯录按钮")
        return False

    center = contacts_button.get_center()
    if not center:
        logger.error("通讯录按钮坐标获取失败")
        return False

    logger.info("点击通讯录按钮: %s", center)
    success = automator.adb.tap(center[0], center[1])

    if success:
        logger.info("成功点击通讯录按钮")
        time.sleep(3)  # 等待页面加载
        return True
    else:
        logger.error("点击通讯录按钮失败")
        return False


def follow_contacts_friends(automator: DouyinAutomator, max_count: int) -> int:
    """关注通讯录中的朋友"""
    logger = logging.getLogger(__name__)

    print(f"🎯 开始关注通讯录朋友（最多 {max_count} 个）...")
    logger.info("开始关注通讯录朋友，最大数量: %d", max_count)

    if not automator.get_current_ui():
        logger.error("获取当前UI失败")
        return 0

    # 查找关注按钮
    follow_buttons = []
    for element in automator.ui_analyzer.elements:
        # 查找FrameLayout元素，content-desc为"关注"且可点击
        if (
            element.is_clickable_element()
            and element.content_desc == "关注"
            and element.class_name == "android.widget.FrameLayout"
        ):
            follow_buttons.append(element)

    logger.info("找到 %d 个关注按钮", len(follow_buttons))
    print(f"📍 找到 {len(follow_buttons)} 个可关注的朋友")

    if not follow_buttons:
        logger.warning("未找到可关注的朋友")
        print("❌ 未找到可关注的朋友")
        return 0

    followed_count = 0
    max_follow = min(max_count, len(follow_buttons))

    for i in range(max_follow):
        button = follow_buttons[i]
        center = button.get_center()

        if center:
            logger.info("点击关注按钮 %d/%d: %s", i + 1, max_follow, center)
            print(f"👆 点击关注按钮 {i+1}/{max_follow}")

            success = automator.adb.tap(center[0], center[1])
            if success:
                followed_count += 1
                logger.info("成功关注朋友 %d", i + 1)
                print(f"✅ 成功关注朋友 {i+1}")
            else:
                logger.error("关注朋友 %d 失败", i + 1)
                print(f"❌ 关注朋友 {i+1} 失败")

            # 等待界面更新
            time.sleep(2)
        else:
            logger.warning("关注按钮 %d 坐标获取失败", i + 1)

    logger.info("关注操作完成，成功关注 %d 个朋友", followed_count)
    print(f"🎉 关注操作完成！成功关注 {followed_count} 个朋友")

    return followed_count


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="抖音通讯录批量关注工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python contacts_douyin.py                    # 默认关注5个通讯录朋友
  python contacts_douyin.py --count 10         # 关注10个通讯录朋友
  python contacts_douyin.py --device 192.168.1.100 --count 8  # 指定设备
        """,
    )

    parser.add_argument(
        "--device", "-d", help="指定 ADB 设备 ID（如 IP 地址或设备序列号）"
    )
    parser.add_argument(
        "--count", "-c", type=int, default=5, help="最大关注数量（默认 5）"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别（默认 INFO）",
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    print("📱 抖音通讯录批量关注工具")
    print("=" * 50)

    try:
        # 初始化自动化器
        logger.info("初始化自动化器，设备ID: %s", args.device or "自动检测")
        automator = DouyinAutomator(args.device)

        # 检查连接
        print("🔧 检查 ADB 连接...")
        if not automator.check_connection():
            logger.error("ADB 连接失败")
            print("❌ ADB 连接失败！")
            sys.exit(1)

        print(f"✅ ADB 连接成功: {automator.adb.device_id}")
        logger.info("ADB 连接成功: %s", automator.adb.device_id)

        # 启动抖音
        print("🚀 启动抖音应用...")
        if not automator.start_douyin():
            logger.error("抖音启动失败")
            print("❌ 抖音启动失败！")
            sys.exit(1)

        print("✅ 抖音启动成功")

        # 等待加载
        print("⏳ 等待应用加载...")
        time.sleep(3)

        # 导航到个人资料页面
        print("👤 导航到个人资料页面...")
        if not automator.navigate_to_profile():
            logger.error("导航到个人资料页面失败")
            print("❌ 导航到个人资料页面失败！")
            sys.exit(1)

        print("✅ 成功进入个人资料页面")

        # 点击添加朋友（实际上现在应该已经在个人资料页了，直接找添加朋友按钮）
        print("👥 寻找并点击添加朋友按钮...")

        # 直接在个人资料页面寻找添加朋友相关按钮
        found_add_friends = False
        for _ in range(3):  # 最多尝试3次
            if automator.get_current_ui():
                # 查找可能的添加朋友按钮文本
                for element in automator.ui_analyzer.elements:
                    if (
                        element.is_clickable_element()
                        and element.text
                        and any(
                            keyword in element.text
                            for keyword in ["添加朋友", "添加好友", "加朋友", "好友"]
                        )
                    ):
                        center = element.get_center()
                        if center:
                            logger.info("找到添加朋友按钮: %s", element.text)
                            success = automator.adb.tap(center[0], center[1])
                            if success:
                                found_add_friends = True
                                time.sleep(3)  # 等待页面加载
                                break

                if found_add_friends:
                    break
            time.sleep(1)

        if not found_add_friends:
            logger.error("未找到添加朋友按钮")
            print("❌ 未找到添加朋友按钮！")
            sys.exit(1)

        print("✅ 成功进入添加朋友页面")

        # 等待页面加载
        time.sleep(2)

        # 点击通讯录按钮
        print("📞 点击通讯录...")
        if not click_contacts_button(automator):
            logger.error("点击通讯录按钮失败")
            print("❌ 点击通讯录按钮失败！")
            sys.exit(1)

        print("✅ 成功进入通讯录页面")

        # 关注通讯录朋友
        followed_count = follow_contacts_friends(automator, args.count)

        if followed_count > 0:
            print(f"\n🎉 任务完成！成功关注了 {followed_count} 个通讯录朋友")
            logger.info("任务完成，成功关注 %d 个通讯录朋友", followed_count)
        else:
            print("\n😔 没有成功关注任何通讯录朋友")
            logger.warning("任务完成，但没有成功关注任何通讯录朋友")

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
        logger.warning("用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序异常: {str(e)}")
        logger.exception("程序执行异常")
        sys.exit(1)

    print("\n👋 程序结束")
    logger.info("程序正常结束")


if __name__ == "__main__":
    main()
