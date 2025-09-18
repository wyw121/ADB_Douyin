#!/usr/bin/env python3
"""抖音通讯录批量关注工具 - 主程序"""
import argparse
import logging
import sys
import json
from datetime import datetime
from douyin_automator import DouyinAutomator


def setup_logging(log_level: str = 'INFO'):
    """设置详细日志配置 - 按照GitHub Copilot官方测试最佳实践"""
    level = getattr(logging, log_level.upper())
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 创建多个日志文件用于不同级别的日志
    main_log = f'logs/douyin_main_{date_str}.log'
    debug_log = f'logs/douyin_debug_{date_str}.log'
    error_log = f'logs/douyin_error_{date_str}.log'
    
    # 确保日志目录存在
    import os
    os.makedirs('logs', exist_ok=True)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # 清除现有处理器
    root_logger.handlers = []
    
    # 详细格式用于调试
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)-15s | %(levelname)-8s | '
        '%(filename)s:%(lineno)d | %(funcName)s() | %(message)s'
    )
    
    # 简洁格式用于控制台
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 控制台处理器 - 根据日志级别决定显示内容
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 主日志文件 - 记录INFO及以上级别
    main_handler = logging.FileHandler(main_log, encoding='utf-8')
    main_handler.setLevel(logging.INFO)
    main_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(main_handler)
    
    # 调试日志文件 - 记录所有级别
    debug_handler = logging.FileHandler(debug_log, encoding='utf-8')
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(debug_handler)
    
    # 错误日志文件 - 仅记录ERROR及以上级别
    error_handler = logging.FileHandler(error_log, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # 记录日志系统启动
    logging.info("="*60)
    logging.info("抖音自动化工具启动 - 日志系统已初始化")
    logging.info(f"日志级别: {log_level}")
    logging.info(f"主日志: {main_log}")
    logging.info(f"调试日志: {debug_log}")
    logging.info(f"错误日志: {error_log}")
    logging.info("="*60)


def print_banner():
    """打印程序横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                  抖音通讯录批量关注工具                        ║
║                  Douyin Contacts Auto-Follow Tool             ║
║                                                              ║
║  功能：通过ADB自动化操作抖音，批量关注通讯录好友                ║
║  作者：AI Assistant                                          ║
║  版本：1.0.0                                                 ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def _handle_ui_analysis_choice(automator, choice: str) -> bool:
    """处理UI分析模式的选择"""
    logger = logging.getLogger(__name__)
    
    if choice == '1':
        print("\n正在分析当前屏幕...")
        logger.info("开始UI屏幕分析测试")
        
        # 详细日志记录分析过程
        try:
            automator.analyze_current_screen()
            logger.info("UI分析完成，结果记录在日志中")
            
            # 如果有分析结果，记录关键统计信息
            if hasattr(automator, 'ui_analyzer') and automator.ui_analyzer:
                element_count = len(automator.ui_analyzer.elements)
                clickable_count = sum(1 for e in automator.ui_analyzer.elements
                                      if e.is_clickable_element())
                logger.info(f"UI分析统计: 总元素={element_count}, " +
                            f"可点击元素={clickable_count}")
            
        except Exception as e:
            logger.error(f"UI分析失败: {str(e)}", exc_info=True)
            print(f"❌ UI分析出错: {str(e)}")
        
        return False
        
    elif choice == '2':
        _handle_save_ui_xml(automator)
        return False
        
    elif choice == '3':
        _handle_start_douyin(automator)
        return False
        
    elif choice == '4':
        _handle_detailed_test_mode(automator)
        return False
        
    elif choice == '5':
        logger.info("退出UI分析模式")
        return True
        
    else:
        logger.warning(f"无效的UI分析选择: {choice}")
        print("❌ 无效选择，请重新输入")
        return False


def _handle_save_ui_xml(automator):
    """处理保存UI XML的操作"""
    logger = logging.getLogger(__name__)
    
    filename = input("请输入保存文件名 (回车使用默认名称): ").strip()
    if not filename:
        filename = None
        
    logger.info(f"开始保存UI XML, 文件名: {filename or '默认'}")
    print("\n正在保存UI XML...")
    
    try:
        success = automator.save_current_ui_xml(filename)
        if success:
            logger.info(f"UI XML保存成功: {filename or '默认文件名'}")
            print("✅ UI XML保存成功")
        else:
            logger.warning("UI XML保存失败")
            print("❌ UI XML保存失败")
    except Exception as e:
        logger.error(f"保存UI XML时发生异常: {str(e)}", exc_info=True)
        print(f"❌ 保存出错: {str(e)}")


def _handle_start_douyin(automator):
    """处理启动抖音的操作"""
    logger = logging.getLogger(__name__)
    
    logger.info("开始启动抖音应用")
    print("\n正在启动抖音...")
    
    try:
        success = automator.start_douyin()
        if success:
            logger.info("抖音应用启动成功")
            print("✅ 抖音启动成功")
        else:
            logger.warning("抖音应用启动失败")
            print("❌ 抖音启动失败")
    except Exception as e:
        logger.error(f"启动抖音时发生异常: {str(e)}", exc_info=True)
        print(f"❌ 启动出错: {str(e)}")


def _run_connection_test(automator) -> bool:
    """运行ADB连接测试"""
    logger = logging.getLogger(__name__)
    
    print("\n📡 测试1: ADB连接状态")
    logger.info("开始ADB连接测试")
    
    try:
        connection_ok = automator.check_connection()
        if connection_ok:
            logger.info(f"ADB连接成功: 设备ID={automator.adb.device_id}")
            print(f"✅ 连接成功: {automator.adb.device_id}")
        else:
            logger.error("ADB连接失败")
            print("❌ 连接失败")
        return connection_ok
    except Exception as e:
        logger.error(f"ADB连接测试异常: {str(e)}", exc_info=True)
        print(f"❌ 连接测试出错: {str(e)}")
        return False


def _run_ui_dump_test(automator) -> bool:
    """运行UI界面获取测试"""
    logger = logging.getLogger(__name__)
    
    print("\n📱 测试2: UI界面信息获取")
    logger.info("开始UI界面获取测试")
    
    try:
        ui_xml = automator.adb.get_ui_xml()
        if ui_xml and len(ui_xml) > 100:
            logger.info(f"UI XML获取成功: 长度={len(ui_xml)}")
            print(f"✅ UI获取成功: XML长度={len(ui_xml)}")
            return True
        else:
            logger.warning("UI XML获取失败或内容为空")
            print("❌ UI获取失败")
            return False
    except Exception as e:
        logger.error(f"UI获取测试异常: {str(e)}", exc_info=True)
        print(f"❌ UI获取测试出错: {str(e)}")
        return False


def _run_element_analysis_test(automator) -> bool:
    """运行UI元素解析测试"""
    logger = logging.getLogger(__name__)
    
    print("\n🔍 测试3: UI元素解析能力")
    logger.info("开始UI元素解析测试")
    
    try:
        automator.analyze_current_screen()
        
        if hasattr(automator, 'ui_analyzer') and automator.ui_analyzer:
            elements = automator.ui_analyzer.elements
            clickable_elements = [e for e in elements
                                  if e.is_clickable_element()]
            
            logger.info(f"UI元素解析完成: 总元素={len(elements)}, " +
                        f"可点击元素={len(clickable_elements)}")
            print(f"✅ 解析成功: 发现{len(elements)}个元素，"
                  f"其中{len(clickable_elements)}个可点击")
            return len(elements) > 0
        else:
            logger.warning("UI元素解析失败，analyzer未初始化")
            print("❌ 解析失败")
            return False
    except Exception as e:
        logger.error(f"UI元素解析测试异常: {str(e)}", exc_info=True)
        print(f"❌ 解析测试出错: {str(e)}")
        return False


def _run_douyin_detection_test(automator) -> bool:
    """运行抖音特定元素检测测试"""
    logger = logging.getLogger(__name__)
    
    print("\n🎵 测试4: 抖音应用元素检测")
    logger.info("开始抖音特定元素检测测试")
    
    try:
        if hasattr(automator, 'ui_analyzer') and automator.ui_analyzer:
            analyzer = automator.ui_analyzer
            douyin_elements = analyzer.find_douyin_specific_elements()
            
            total_found = sum(len(elements)
                              for elements in douyin_elements.values())
            
            logger.info(f"抖音元素检测完成: 共发现{total_found}个相关元素")
            print(f"✅ 检测完成: 发现{total_found}个抖音相关元素")
            
            # 详细记录找到的元素类型
            for element_type, elements in douyin_elements.items():
                if elements:
                    logger.debug(f"发现{element_type}: {len(elements)}个")
            
            return total_found > 0
        else:
            logger.warning("无法进行抖音元素检测，UI分析器未初始化")
            print("❌ 检测失败: UI分析器未初始化")
            return False
    except Exception as e:
        logger.error(f"抖音元素检测测试异常: {str(e)}", exc_info=True)
        print(f"❌ 抖音检测出错: {str(e)}")
        return False


def _run_navigation_test(automator) -> bool:
    """运行导航元素识别测试"""
    logger = logging.getLogger(__name__)
    
    print("\n🧭 测试5: 导航元素识别能力")
    logger.info("开始导航元素识别测试")
    
    try:
        if hasattr(automator, 'ui_analyzer') and automator.ui_analyzer:
            analyzer = automator.ui_analyzer
            navigation_elements = analyzer.find_navigation_elements()
            
            total_nav_elements = sum(len(elements)
                                     for elements in
                                     navigation_elements.values())
            
            logger.info(f"导航元素识别完成: 共发现{total_nav_elements}个导航元素")
            print(f"✅ 识别完成: 发现{total_nav_elements}个导航元素")
            
            # 详细记录导航元素类型
            for nav_type, elements in navigation_elements.items():
                if elements:
                    logger.debug(f"发现{nav_type}: {len(elements)}个")
            
            return total_nav_elements > 0
        else:
            logger.warning("无法进行导航元素识别，UI分析器未初始化")
            print("❌ 识别失败: UI分析器未初始化")
            return False
    except Exception as e:
        logger.error(f"导航元素识别测试异常: {str(e)}", exc_info=True)
        print(f"❌ 导航识别出错: {str(e)}")
        return False


def _print_test_summary(test_results: dict):
    """打印测试结果汇总"""
    logger = logging.getLogger(__name__)
    
    print("\n📊 测试结果汇总")
    print("=" * 50)
    logger.info("详细测试模式完成，汇总结果:")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    test_names = {
        'connection_test': 'ADB连接测试',
        'ui_dump_test': 'UI获取测试',
        'element_analysis_test': 'UI解析测试',
        'douyin_detection_test': '抖音元素检测',
        'navigation_test': '导航元素识别'
    }
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        display_name = test_names[test_name]
        print(f"{display_name}: {status}")
        logger.info(f"{display_name}: {'通过' if result else '失败'}")
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"\n总体成功率: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    logger.info(f"测试汇总: {passed_tests}/{total_tests} 通过 ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        logger.info("系统测试整体通过，可以正常使用")
        print("🎉 系统状态良好，可以正常使用！")
    elif success_rate >= 60:
        logger.warning("系统部分功能异常，建议检查配置")
        print("⚠️ 系统部分功能异常，建议检查配置")
    else:
        logger.error("系统存在严重问题，需要排查修复")
        print("🚨 系统存在严重问题，需要排查修复")
    
    print("\n详细日志已记录到logs目录中")
    logger.info("详细测试模式结束")


def _handle_detailed_test_mode(automator):
    """详细测试模式 - 按照GitHub Copilot官方最佳实践进行全面测试"""
    logger = logging.getLogger(__name__)
    
    print("\n🧪 详细测试模式启动")
    print("=" * 50)
    logger.info("进入详细测试模式 - 全面验证系统功能")
    
    test_results = {
        'connection_test': False,
        'ui_dump_test': False,
        'element_analysis_test': False,
        'douyin_detection_test': False,
        'navigation_test': False
    }
    
    # 执行各项测试
    test_results['connection_test'] = _run_connection_test(automator)
    if not test_results['connection_test']:
        logger.error("ADB连接失败，跳过后续测试")
        return test_results
        
    test_results['ui_dump_test'] = _run_ui_dump_test(automator)
    test_results['element_analysis_test'] = (
        _run_element_analysis_test(automator))
    test_results['douyin_detection_test'] = (
        _run_douyin_detection_test(automator))
    test_results['navigation_test'] = _run_navigation_test(automator)
    
    # 打印测试结果汇总
    _print_test_summary(test_results)
    
    return test_results


def analyze_ui_mode(device_id: str = None):
    """UI分析模式"""
    print("\n🔍 UI分析模式")
    print("=" * 50)
    
    automator = DouyinAutomator(device_id)
    
    # 检查连接
    if not automator.check_connection():
        print("❌ 设备连接失败！请检查ADB连接。")
        return
    
    print(f"✅ 设备连接成功: {automator.adb.device_id}")
    
    while True:
        print("\n请选择操作：")
        print("1. 分析当前屏幕")
        print("2. 保存当前UI XML")
        print("3. 启动抖音")
        print("4. 🧪 运行详细测试模式")
        print("5. 返回主菜单")
        
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if _handle_ui_analysis_choice(automator, choice):
            break
            
        else:
            print("❌ 无效选择，请重试")


def _get_user_confirmation() -> bool:
    """获取用户确认"""
    confirm = input("\n⚠️  即将开始自动化操作，请确保：\n"
                    "1. 手机已解锁\n"
                    "2. 已安装抖音应用\n"
                    "3. 已授权通讯录权限\n"
                    "是否继续？(y/N): ").strip().lower()
    return confirm == 'y'


def _display_workflow_results(result):
    """显示工作流程执行结果"""
    if result['success']:
        print("✅ 工作流程执行成功！")
        _display_step_results(result['step_results'])
        if result['follow_results']:
            _display_follow_results(result['follow_results'])
    else:
        print("❌ 工作流程执行失败！")
        print(f"错误信息: {result['error_message']}")


def _display_step_results(step_results):
    """显示步骤执行结果"""
    print("\n步骤执行状态：")
    steps = {
        'connection': '设备连接',
        'app_start': '启动抖音',
        'navigate_profile': '导航到个人资料',
        'navigate_add_friends': '导航到添加朋友',
        'navigate_contacts': '导航到通讯录',
        'batch_follow': '批量关注'
    }
    
    for step, status in step_results.items():
        step_name = steps.get(step, step)
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {step_name}")


def _display_follow_results(follow_results):
    """显示关注结果详情"""
    print("\n关注统计：")
    print(f"  总处理数量: {follow_results['total_processed']}")
    print(f"  成功关注: {follow_results['successful_follows']}")
    print(f"  关注失败: {follow_results['failed_follows']}")
    print(f"  跳过数量: {follow_results['skipped']}")
    
    if follow_results['contact_details']:
        print("\n详细处理结果：")
        for i, contact in enumerate(follow_results['contact_details'], 1):
            status_map = {
                'success': '✅ 成功关注',
                'failed': '❌ 关注失败',
                'skipped': '⏭️ 跳过'
            }
            status_text = status_map.get(contact['status'],
                                         contact['status'])
            print(f"  {i:2d}. {contact['name']} - {status_text}")


def auto_follow_mode(device_id: str = None, max_count: int = 10):
    """自动关注模式"""
    print("\n🤖 自动关注模式")
    print("=" * 50)
    
    automator = DouyinAutomator(device_id)
    
    print(f"设备ID: {device_id or '自动检测'}")
    print(f"最大关注数量: {max_count}")
    
    # 确认执行
    if not _get_user_confirmation():
        print("操作已取消")
        return
    
    print("\n🚀 开始执行自动化流程...")
    print("-" * 50)
    
    # 执行完整工作流程
    result = automator.run_complete_workflow(max_count)
    
    # 显示结果
    print("\n📊 执行结果")
    print("=" * 50)
    
    _display_workflow_results(result)
    
    # 保存结果到文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = f"follow_result_{timestamp}.json"
    
    try:
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n📄 结果已保存到: {result_file}")
    except Exception as e:
        print(f"❌ 保存结果失败: {str(e)}")


def _handle_ui_analysis_input() -> str:
    """获取UI分析模式的设备ID输入"""
    return input("请输入设备ID (回车使用默认设备): ").strip() or None


def _handle_auto_follow_input() -> tuple:
    """获取自动关注模式的参数"""
    device_id = input("请输入设备ID (回车使用默认设备): ").strip() or None
    try:
        max_count = int(input("请输入最大关注数量 (默认10): ").strip() or "10")
    except ValueError:
        max_count = 10
    return device_id, max_count


def _handle_device_setup():
    """处理ADB设备设置"""
    print("\n⚙️  ADB设备设置")
    print("-" * 30)
    
    # 显示可用设备
    from adb_connection import ADBConnection
    adb = ADBConnection()
    devices = adb.get_devices()
    
    if devices:
        print("可用设备列表：")
        for i, device in enumerate(devices, 1):
            print(f"  {i}. {device}")
    else:
        print("❌ 未检测到连接的设备")
        print("\n请确保：")
        print("1. 手机已通过USB连接到电脑")
        print("2. 手机已开启USB调试模式")
        print("3. 已授权ADB调试")
        print("4. ADB服务正在运行")


def _handle_interactive_choice(choice: str) -> bool:
    """处理交互式模式的选择，返回是否退出"""
    if choice == '1':
        device_id = _handle_ui_analysis_input()
        analyze_ui_mode(device_id)
        return False
        
    elif choice == '2':
        device_id, max_count = _handle_auto_follow_input()
        auto_follow_mode(device_id, max_count)
        return False
        
    elif choice == '3':
        _handle_device_setup()
        return False
        
    elif choice == '4':
        print("\n👋 感谢使用，再见！")
        return True
        
    else:
        print("❌ 无效选择，请重试")
        return False


def interactive_mode():
    """交互式模式"""
    print_banner()
    
    while True:
        print("\n请选择操作模式：")
        print("1. 🔍 UI分析模式 - 分析当前屏幕元素")
        print("2. 🤖 自动关注模式 - 批量关注通讯录好友")
        print("3. ⚙️  设置ADB设备")
        print("4. 🚪 退出程序")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if _handle_interactive_choice(choice):
            break


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='抖音通讯录批量关注工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                          # 交互式模式
  python main.py --analyze                # UI分析模式
  python main.py --auto-follow --count 5  # 自动关注5个好友
  python main.py --device 192.168.1.100  # 指定设备IP
        """
    )
    
    parser.add_argument('--device', '-d',
                        help='指定ADB设备ID（如IP地址或设备序列号）')
    parser.add_argument('--analyze', action='store_true',
                        help='启动UI分析模式')
    parser.add_argument('--auto-follow', action='store_true',
                        help='启动自动关注模式')
    parser.add_argument('--count', '-c', type=int, default=10,
                        help='最大关注数量（默认10）')
    parser.add_argument('--log-level',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        default='INFO', help='日志级别（默认INFO）')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    try:
        if args.analyze:
            print_banner()
            analyze_ui_mode(args.device)
        elif args.auto_follow:
            print_banner()
            auto_follow_mode(args.device, args.count)
        else:
            # 默认交互式模式
            interactive_mode()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序异常: {str(e)}")
        logging.exception("程序执行异常")
        sys.exit(1)


if __name__ == '__main__':
    main()
