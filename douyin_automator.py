"""抖音自动化操作模块，实现自动化导航和批量关注通讯录好友功能。"""
import time
import logging
from typing import List, Dict, Optional
from adb_connection import ADBConnection
from ui_analyzer import UIAnalyzer


class DouyinAutomator:
    """抖音自动化操作类"""

    def __init__(self, device_id: Optional[str] = None):
        """初始化抖音自动化操作。

        Args:
            device_id: 设备ID，如果为None则使用第一个可用设备
        """
        self.adb = ADBConnection(device_id)
        self.ui_analyzer = UIAnalyzer()
        self.logger = self._setup_logger()

        # 抖音相关配置
        self.douyin_package = "com.ss.android.ugc.aweme"
        self.operation_delay = 2.0  # 操作间隔（秒）
        self.max_retries = 3  # 最大重试次数

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('DouyinAutomator')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def check_connection(self) -> bool:
        """检查ADB连接状态"""
        if not self.adb.check_device_connection():
            self.logger.error("设备连接失败")
            return False

        self.logger.info("设备连接成功: %s", self.adb.device_id)
        return True

    def start_douyin(self) -> bool:
        """启动抖音应用"""
        self.logger.info("启动抖音应用...")
        success = self.adb.start_app(self.douyin_package)
        if success:
            time.sleep(3)  # 等待应用启动
            self.logger.info("抖音应用启动成功")
        else:
            self.logger.error("抖音应用启动失败")
        return success

    def get_current_ui(self) -> bool:
        """获取当前界面UI结构"""
        xml_content = self.adb.get_ui_dump()
        if xml_content:
            return self.ui_analyzer.parse_xml(xml_content)
        return False

    def wait_for_element(self, keywords: List[str], timeout: int = 10) -> bool:
        """等待指定元素出现。

        Args:
            keywords: 元素关键词
            timeout: 超时时间（秒）

        Returns:
            是否找到元素
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.get_current_ui():
                elements = self.ui_analyzer.find_elements_by_text(keywords)
                if elements:
                    return True
            time.sleep(1)

        self.logger.warning("等待元素超时: %s", keywords)
        return False

    def _filter_exact_matches(self, elements, keywords):
        """筛选精确匹配的元素"""
        exact_elements = []
        for element in elements:
            element_text = (element.text + ' ' +
                            element.content_desc).strip()
            for keyword in keywords:
                if keyword == element_text:
                    exact_elements.append(element)
                    break
        return exact_elements

    def _find_clickable_element(self, elements):
        """从元素列表中找到第一个可点击的元素"""
        for element in elements:
            if element.is_clickable_element():
                return element
        return None

    def click_element_by_text(self, keywords: List[str],
                              exact_match: bool = False) -> bool:
        """根据文本点击元素。

        Args:
            keywords: 关键词列表
            exact_match: 是否精确匹配

        Returns:
            是否点击成功
        """
        if not self.get_current_ui():
            self.logger.error("获取UI失败")
            return False

        elements = self.ui_analyzer.find_elements_by_text(keywords)

        # 如果需要精确匹配，进一步筛选
        if exact_match and elements:
            elements = self._filter_exact_matches(elements, keywords)

        if not elements:
            self.logger.warning("未找到包含关键词的元素: %s", keywords)
            return False

        # 选择最佳匹配元素（第一个可点击的）
        target_element = self._find_clickable_element(elements)

        if not target_element:
            self.logger.warning("找到元素但不可点击: %s", keywords)
            return False

        center = target_element.get_center()
        if center:
            element_desc = (target_element.text or
                            target_element.content_desc)
            self.logger.info("点击元素: %s at %s", element_desc, center)
            success = self.adb.tap(center[0], center[1])
            if success:
                time.sleep(self.operation_delay)
            return success

        return False

    def navigate_to_profile(self) -> bool:
        """导航到个人资料页面（"我"页面）"""
        self.logger.info("导航到个人资料页面...")

        # 获取当前UI
        if not self.get_current_ui():
            return False

        # 查找"我"按钮
        profile_keywords = ['我', 'Me', 'Profile']

        # 先尝试在底部导航栏查找
        navigation = self.ui_analyzer.find_navigation_elements()
        profile_tabs = navigation.get('bottom_tabs', [])

        # 从底部标签中找到"我"
        target_element = None
        for element in profile_tabs:
            if element.contains_text(profile_keywords):
                target_element = element
                break

        # 如果在底部标签中没找到，就在所有元素中查找
        if not target_element:
            profile_elements = self.ui_analyzer.find_elements_by_text(
                profile_keywords)
            if profile_elements:
                target_element = profile_elements[0]

        if target_element:
            center = target_element.get_center()
            if center:
                self.logger.info("点击个人资料标签: %s", center)
                success = self.adb.tap(center[0], center[1])
                if success:
                    time.sleep(self.operation_delay)
                    return True

        self.logger.error("未找到个人资料标签")
        return False

    def navigate_to_add_friends(self) -> bool:
        """导航到添加朋友页面"""
        self.logger.info("导航到添加朋友页面...")

        # 等待个人资料页面加载
        self.wait_for_element(['添加朋友', 'Add Friends'], timeout=5)

        # 查找添加朋友按钮
        add_friend_keywords = ['添加朋友', '添加好友', '加朋友', 'Add Friends']
        return self.click_element_by_text(add_friend_keywords)

    def navigate_to_contacts(self) -> bool:
        """导航到通讯录页面"""
        self.logger.info("导航到通讯录页面...")

        # 等待添加朋友页面加载
        self.wait_for_element(['通讯录', 'Contacts'], timeout=5)

        # 查找通讯录按钮
        contacts_keywords = ['通讯录', '联系人', 'Contacts', '通信录']
        return self.click_element_by_text(contacts_keywords)

    def get_contact_list(self) -> List[Dict]:
        """获取通讯录联系人列表。

        Returns:
            联系人信息列表
        """
        self.logger.info("获取通讯录联系人列表...")

        if not self.get_current_ui():
            return []

        douyin_elements = self.ui_analyzer.find_douyin_specific_elements()
        contact_items = douyin_elements.get('contact_items', [])
        follow_buttons = douyin_elements.get('follow_buttons', [])

        contacts = []

        # 分析联系人和对应的关注按钮
        for contact in contact_items:
            contact_center = contact.get_center()
            if not contact_center:
                continue

            # 查找距离该联系人最近的关注按钮
            nearest_follow_button = None
            min_distance = float('inf')

            for follow_btn in follow_buttons:
                btn_center = follow_btn.get_center()
                if btn_center:
                    # 计算距离（主要考虑垂直距离，因为通常在同一行）
                    distance = abs(contact_center[1] - btn_center[1])
                    # 假设在100像素范围内
                    if distance < min_distance and distance < 100:
                        min_distance = distance
                        nearest_follow_button = follow_btn

            contact_info = {
                'name': contact.text or contact.content_desc,
                'element': contact,
                'center': contact_center,
                'follow_button': nearest_follow_button,
                'can_follow': nearest_follow_button is not None
            }
            contacts.append(contact_info)

        self.logger.info("找到 %d 个通讯录联系人", len(contacts))
        return contacts

    def follow_contact(self, contact_info: Dict) -> bool:
        """关注指定联系人。

        Args:
            contact_info: 联系人信息字典

        Returns:
            是否关注成功
        """
        if not contact_info.get('can_follow'):
            self.logger.warning("联系人 %s 无法关注",
                                contact_info['name'])
            return False

        follow_button = contact_info['follow_button']
        center = follow_button.get_center()

        if center:
            self.logger.info("关注联系人: %s", contact_info['name'])
            success = self.adb.tap(center[0], center[1])
            if success:
                time.sleep(self.operation_delay)
                return True

        return False

    def _process_contact_page(self, contacts, start_index, max_count,
                              processed_count, results):
        """处理当前页面的联系人"""
        page_processed = 0
        for i, contact in enumerate(contacts):
            if i < start_index or processed_count >= max_count:
                continue

            contact_name = contact['name']
            self.logger.info("处理联系人 %d/%d: %s",
                             processed_count + 1, max_count, contact_name)

            if contact['can_follow']:
                success = self.follow_contact(contact)
                if success:
                    results['successful_follows'] += 1
                    self.logger.info("成功关注: %s", contact_name)
                    status = 'success'
                else:
                    results['failed_follows'] += 1
                    self.logger.warning("关注失败: %s", contact_name)
                    status = 'failed'
            else:
                results['skipped'] += 1
                self.logger.info("跳过联系人: %s (可能已关注)", contact_name)
                status = 'skipped'

            results['contact_details'].append({
                'name': contact_name,
                'status': status
            })

            processed_count += 1
            page_processed += 1
            results['total_processed'] += 1
            time.sleep(self.operation_delay)

        return page_processed, processed_count

    def batch_follow_contacts(self, max_count: int = 10,
                              start_index: int = 0) -> Dict:
        """批量关注通讯录联系人。

        Args:
            max_count: 最大关注数量
            start_index: 开始索引

        Returns:
            操作结果统计
        """
        self.logger.info("开始批量关注联系人，最多 %d 个...", max_count)

        results = {
            'total_processed': 0,
            'successful_follows': 0,
            'failed_follows': 0,
            'skipped': 0,
            'contact_details': []
        }

        processed_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 5

        while (processed_count < max_count and
               scroll_attempts < max_scroll_attempts):
            contacts = self.get_contact_list()

            if not contacts:
                self.logger.warning("没有找到联系人，尝试滚动页面")
                self._scroll_contacts_page()
                scroll_attempts += 1
                continue

            page_processed, processed_count = self._process_contact_page(
                contacts, start_index, max_count, processed_count, results)

            # 如果这一页处理了联系人，但还没达到目标数量，尝试滚动到下一页
            if page_processed > 0 and processed_count < max_count:
                self.logger.info("滚动到下一页联系人...")
                self._scroll_contacts_page()
                time.sleep(1)  # 等待页面加载
                start_index = 0  # 重置开始索引
            else:
                scroll_attempts += 1

        self.logger.info("批量关注完成！成功: %d, 失败: %d, 跳过: %d",
                         results['successful_follows'],
                         results['failed_follows'],
                         results['skipped'])

        return results

    def _scroll_contacts_page(self) -> bool:
        """滚动通讯录页面"""
        screen_size = self.adb.get_screen_size()
        if screen_size:
            width, height = screen_size
            # 从屏幕中下部向上滑动
            start_y = int(height * 0.7)
            end_y = int(height * 0.3)
            center_x = width // 2

            return self.adb.swipe(center_x, start_y, center_x, end_y, 500)
        return False

    def run_complete_workflow(self, max_follow_count: int = 10) -> Dict:
        """运行完整的自动化工作流程。

        Args:
            max_follow_count: 最大关注数量

        Returns:
            操作结果
        """
        self.logger.info("开始执行完整的抖音通讯录批量关注流程...")

        workflow_result = {
            'success': False,
            'step_results': {},
            'follow_results': None,
            'error_message': None
        }

        try:
            # 步骤1: 检查连接
            self.logger.info("步骤 1/6: 检查设备连接...")
            if not self.check_connection():
                workflow_result['error_message'] = "设备连接失败"
                return workflow_result
            workflow_result['step_results']['connection'] = True

            # 步骤2: 启动抖音
            self.logger.info("步骤 2/6: 启动抖音应用...")
            if not self.start_douyin():
                workflow_result['error_message'] = "抖音启动失败"
                return workflow_result
            workflow_result['step_results']['app_start'] = True

            # 步骤3: 导航到个人资料页面
            self.logger.info("步骤 3/6: 导航到个人资料页面...")
            if not self.navigate_to_profile():
                workflow_result['error_message'] = "导航到个人资料页面失败"
                return workflow_result
            workflow_result['step_results']['navigate_profile'] = True

            # 步骤4: 导航到添加朋友页面
            self.logger.info("步骤 4/6: 导航到添加朋友页面...")
            if not self.navigate_to_add_friends():
                workflow_result['error_message'] = "导航到添加朋友页面失败"
                return workflow_result
            workflow_result['step_results']['navigate_add_friends'] = True

            # 步骤5: 导航到通讯录页面
            self.logger.info("步骤 5/6: 导航到通讯录页面...")
            if not self.navigate_to_contacts():
                workflow_result['error_message'] = "导航到通讯录页面失败"
                return workflow_result
            workflow_result['step_results']['navigate_contacts'] = True

            # 步骤6: 批量关注联系人
            self.logger.info("步骤 6/6: 批量关注联系人...")
            follow_results = self.batch_follow_contacts(max_follow_count)
            workflow_result['follow_results'] = follow_results
            workflow_result['step_results']['batch_follow'] = True

            workflow_result['success'] = True
            self.logger.info("完整工作流程执行成功！")

        except Exception as e:
            self.logger.error("工作流程执行异常: %s", str(e))
            workflow_result['error_message'] = str(e)

        return workflow_result

    def analyze_current_screen(self) -> bool:
        """分析当前屏幕并生成报告"""
        self.logger.info("分析当前屏幕...")

        if not self.get_current_ui():
            self.logger.error("获取UI失败")
            return False

        # 生成分析报告
        self.ui_analyzer.print_analysis_summary()

        # 保存详细报告
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        report_filename = f"douyin_ui_analysis_{timestamp}.txt"
        self.ui_analyzer.save_analysis_report(report_filename)

        return True

    def save_current_ui_xml(self, filename: str = None) -> bool:
        """保存当前UI的XML到文件"""
        if not filename:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"douyin_ui_{timestamp}.xml"

        xml_content = self.adb.get_ui_dump()
        if xml_content:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
                self.logger.info("UI XML已保存到: %s", filename)
                return True
            except Exception as e:
                self.logger.error("保存XML失败: %s", str(e))

        return False
