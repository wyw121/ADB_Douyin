#!/usr/bin/env python3
"""抖音自动化脚本 - 简化版本，直接关注推荐用户。"""

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
    main_log = f"logs/simple_douyin_main_{date_str}.log"
    debug_log = f"logs/simple_douyin_debug_{date_str}.log"
    error_log = f"logs/simple_douyin_error_{date_str}.log"

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
    logging.info("抖音自动化工具启动 - 简化版本")
    logging.info("日志级别: %s", log_level)
    logging.info("主日志: %s", main_log)
    logging.info("调试日志: %s", debug_log)
    logging.info("错误日志: %s", error_log)
    logging.info("=" * 60)


def _find_follow_buttons(automator: DouyinAutomator) -> list:
    """查找所有关注按钮"""
    follow_buttons = []

    # 首先查找FrameLayout元素，content-desc为"关注"且可点击
    for element in automator.ui_analyzer.elements:
        if (
            element.is_clickable_element()
            and element.content_desc == "关注"
            and element.class_name == "android.widget.FrameLayout"
        ):
            follow_buttons.append(element)

    return follow_buttons


def _click_follow_button(
    automator: DouyinAutomator, button, index: int, total: int
) -> bool:
    """点击单个关注按钮"""
    logger = logging.getLogger(__name__)
    center = button.get_center()

    if not center:
        logger.warning("关注按钮 %d 坐标获取失败", index)
        return False

    logger.info("点击关注按钮 %d/%d: %s", index, total, center)
    print(f"👆 点击关注按钮 {index}/{total}")

    success = automator.adb.tap(center[0], center[1])
    if success:
        logger.info("成功关注用户 %d", index)
        print(f"✅ 成功关注用户 {index}")
        time.sleep(2)  # 等待界面更新
        return True
    else:
        logger.error("关注用户 %d 失败", index)
        print(f"❌ 关注用户 {index} 失败")
        return False


def follow_recommended_users(automator: DouyinAutomator, max_count: int) -> int:
    """关注推荐用户"""
    logger = logging.getLogger(__name__)

    print(f"🎯 开始关注推荐用户（最多 {max_count} 个）...")
    logger.info("开始关注推荐用户，最大数量: %d", max_count)

    if not automator.get_current_ui():
        logger.error("获取当前UI失败")
        return 0

    # 查找关注按钮
    follow_buttons = _find_follow_buttons(automator)

    logger.info("找到 %d 个关注按钮", len(follow_buttons))
    print(f"📍 找到 {len(follow_buttons)} 个可关注的用户")

    if not follow_buttons:
        logger.warning("未找到可关注的用户")
        print("❌ 未找到可关注的用户")
        return 0

    followed_count = 0
    max_follow = min(max_count, len(follow_buttons))

    for i in range(max_follow):
        if _click_follow_button(automator, follow_buttons[i], i + 1, max_follow):
            followed_count += 1

    logger.info("关注操作完成，成功关注 %d 个用户", followed_count)
    print(f"🎉 关注操作完成！成功关注 {followed_count} 个用户")

    return followed_count


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="抖音自动关注工具 - 简化版本（关注推荐用户）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python simple_douyin.py                 # 默认关注3个推荐用户
  python simple_douyin.py --count 5       # 关注5个推荐用户
  python simple_douyin.py --device 192.168.1.100 --count 10  # 指定设备
        """,
    )

    parser.add_argument(
        "--device", "-d", help="指定 ADB 设备 ID（如 IP 地址或设备序列号）"
    )
    parser.add_argument(
        "--count", "-c", type=int, default=3, help="最大关注数量（默认 3）"
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

    print("🎯 抖音自动关注工具 - 简化版本")
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

        # 点击添加朋友
        print("👥 点击添加朋友...")
        if not automator.navigate_to_add_friends():
            logger.error("导航到添加朋友页面失败")
            print("❌ 导航到添加朋友页面失败！")
            sys.exit(1)

        print("✅ 成功进入添加朋友页面")

        # 等待页面加载
        time.sleep(2)

        # 关注推荐用户
        followed_count = follow_recommended_users(automator, args.count)

        if followed_count > 0:
            print(f"\n🎉 任务完成！成功关注了 {followed_count} 个用户")
            logger.info("任务完成，成功关注 %d 个用户", followed_count)
        else:
            print("\n😔 没有成功关注任何用户")
            logger.warning("任务完成，但没有成功关注任何用户")

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
