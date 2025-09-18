#!/usr/bin/env python3
"""抖音自动化脚本 - 纯命令行自动运行版本，完全自动化执行。"""

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
    main_log = f"logs/auto_douyin_main_{date_str}.log"
    debug_log = f"logs/auto_douyin_debug_{date_str}.log"
    error_log = f"logs/auto_douyin_error_{date_str}.log"

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
    logging.info("抖音自动化工具启动 - 纯自动化模式")
    logging.info("日志级别: %s", log_level)
    logging.info("主日志: %s", main_log)
    logging.info("调试日志: %s", debug_log)
    logging.info("错误日志: %s", error_log)
    logging.info("=" * 60)


def test_adb_connection(automator: DouyinAutomator) -> bool:
    """测试 ADB 连接"""
    logger = logging.getLogger(__name__)

    print("🔧 测试 ADB 连接...")
    logger.info("开始测试 ADB 连接")

    try:
        if not automator.check_connection():
            logger.error("ADB 连接失败")
            print("❌ ADB 连接失败！请检查：")
            print("   1. 手机已通过 USB 连接")
            print("   2. 已开启 USB 调试")
            print("   3. 已授权 ADB 调试")
            return False

        logger.info("ADB 连接成功: %s", automator.adb.device_id)
        print(f"✅ ADB 连接成功: {automator.adb.device_id}")
        return True

    except Exception as e:
        logger.error("ADB 连接测试异常: %s", str(e))
        print(f"❌ ADB 连接测试失败: {str(e)}")
        return False


def test_ui_capture(automator: DouyinAutomator) -> bool:
    """测试 UI 获取功能"""
    logger = logging.getLogger(__name__)

    print("📱 测试 UI 界面获取...")
    logger.info("开始测试 UI 获取功能")

    try:
        ui_xml = automator.adb.get_ui_xml()
        if ui_xml and len(ui_xml) > 100:
            logger.info("UI XML 获取成功，长度: %d", len(ui_xml))
            print(f"✅ UI 获取成功: XML 长度 {len(ui_xml)}")
            return True
        else:
            logger.error("UI XML 获取失败或内容为空")
            print("❌ UI 获取失败")
            return False

    except Exception as e:
        logger.error("UI 获取测试异常: %s", str(e))
        print(f"❌ UI 获取测试失败: {str(e)}")
        return False


def start_douyin_app(automator: DouyinAutomator) -> bool:
    """启动抖音应用"""
    logger = logging.getLogger(__name__)

    print("🚀 启动抖音应用...")
    logger.info("开始启动抖音应用")

    try:
        if automator.start_douyin():
            logger.info("抖音应用启动成功")
            print("✅ 抖音启动成功")

            # 等待应用加载
            print("⏳ 等待应用加载（5秒）...")
            time.sleep(5)
            return True
        else:
            logger.error("抖音应用启动失败")
            print("❌ 抖音启动失败")
            return False

    except Exception as e:
        logger.error("启动抖音应用异常: %s", str(e))
        print(f"❌ 启动抖音失败: {str(e)}")
        return False


def analyze_current_screen(automator: DouyinAutomator) -> bool:
    """分析当前屏幕"""
    logger = logging.getLogger(__name__)

    print("🔍 分析当前屏幕...")
    logger.info("开始分析当前屏幕")

    try:
        success = automator.analyze_current_screen()
        if success:
            logger.info("屏幕分析完成")
            print("✅ 屏幕分析完成")

            # 输出基本统计信息
            if hasattr(automator, "ui_analyzer") and automator.ui_analyzer:
                elements = automator.ui_analyzer.elements
                clickable_count = sum(1 for e in elements if e.is_clickable_element())
                logger.info(
                    "分析结果: 总元素=%d, 可点击元素=%d", len(elements), clickable_count
                )
                print(
                    f"📊 分析结果: {len(elements)} 个元素，"
                    f"{clickable_count} 个可点击"
                )
            return True
        else:
            logger.error("屏幕分析失败")
            print("❌ 屏幕分析失败")
            return False

    except Exception as e:
        logger.error("屏幕分析异常: %s", str(e))
        print(f"❌ 屏幕分析失败: {str(e)}")
        return False


def run_full_automation(automator: DouyinAutomator, max_follow: int) -> bool:
    """运行完整自动化流程"""
    logger = logging.getLogger(__name__)

    print(f"🤖 开始完整自动化流程 (最多关注 {max_follow} 个联系人)...")
    logger.info("开始完整自动化流程，最大关注数: %d", max_follow)

    try:
        result = automator.run_complete_workflow(max_follow)

        if result["success"]:
            logger.info("自动化流程执行成功")
            print("✅ 自动化流程执行成功！")

            # 显示结果统计
            follow_results = result.get("follow_results", {})
            if follow_results:
                total = follow_results.get("total_processed", 0)
                success = follow_results.get("successful_follows", 0)
                failed = follow_results.get("failed_follows", 0)
                skipped = follow_results.get("skipped", 0)

                print("📈 执行统计:")
                print(f"   总处理: {total}")
                print(f"   成功关注: {success}")
                print(f"   关注失败: {failed}")
                print(f"   跳过: {skipped}")

                logger.info(
                    "执行统计 - 总处理:%d, 成功:%d, 失败:%d, 跳过:%d",
                    total,
                    success,
                    failed,
                    skipped,
                )

            return True
        else:
            error_msg = result.get("error_message", "未知错误")
            logger.error("自动化流程失败: %s", error_msg)
            print(f"❌ 自动化流程失败: {error_msg}")
            return False

    except Exception as e:
        logger.error("自动化流程异常: %s", str(e))
        print(f"❌ 自动化流程异常: {str(e)}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="抖音通讯录自动关注工具 - 纯自动化版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python auto_douyin.py                    # 默认关注10个联系人
  python auto_douyin.py --count 5          # 关注5个联系人
  python auto_douyin.py --device 192.168.1.100 --count 20  # 指定设备和数量
  python auto_douyin.py --test-only        # 仅测试连接，不执行关注
        """,
    )

    parser.add_argument(
        "--device", "-d", help="指定 ADB 设备 ID（如 IP 地址或设备序列号）"
    )
    parser.add_argument(
        "--count", "-c", type=int, default=10, help="最大关注数量（默认 10）"
    )
    parser.add_argument(
        "--test-only", action="store_true", help="仅运行测试，不执行实际关注操作"
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

    print("🎯 抖音通讯录自动关注工具 - 纯自动化版本")
    print("=" * 50)

    try:
        # 初始化自动化器
        logger.info("初始化自动化器，设备ID: %s", args.device or "自动检测")
        automator = DouyinAutomator(args.device)

        # 测试阶段
        print("\n🧪 系统测试阶段")
        print("-" * 30)

        # 1. 测试 ADB 连接
        if not test_adb_connection(automator):
            logger.error("ADB 连接测试失败，退出程序")
            sys.exit(1)

        # 2. 测试 UI 获取
        if not test_ui_capture(automator):
            logger.error("UI 获取测试失败，退出程序")
            sys.exit(1)

        # 3. 启动抖音应用
        if not start_douyin_app(automator):
            logger.error("抖音应用启动失败，退出程序")
            sys.exit(1)

        # 4. 分析当前屏幕
        if not analyze_current_screen(automator):
            logger.error("屏幕分析失败，退出程序")
            sys.exit(1)

        print("\n✅ 所有测试通过！")
        logger.info("所有系统测试通过")

        # 如果只是测试模式，到此结束
        if args.test_only:
            print("\n🎉 测试模式完成，程序退出")
            logger.info("测试模式完成")
            return

        # 执行阶段
        print("\n🚀 自动化执行阶段")
        print("-" * 30)

        # 运行完整自动化流程
        if run_full_automation(automator, args.count):
            print("\n🎉 自动化流程完成！")
            logger.info("自动化流程成功完成")
        else:
            print("\n❌ 自动化流程失败！")
            logger.error("自动化流程执行失败")
            sys.exit(1)

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
