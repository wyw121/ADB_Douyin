#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ContactsConverter Module

AI-Agent-Friendly通讯录数据转换器
处理各种格式的通讯录文件并转换为标准化的联系人数据结构

Author: AI Assistant
Created: 2025年9月18日
"""

import re
import logging
from typing import List, Dict, Optional
from pathlib import Path


class ContactsConverter:
    """
    智能通讯录数据转换器
    
    设计用于AI Agent操作，提供结构化数据处理和完整的错误处理
    支持多种输入格式的自动识别和转换
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化通讯录转换器
        
        Args:
            logger: 可选的日志记录器，用于AI Agent监控
        """
        self.logger = logger or logging.getLogger(__name__)
        self.supported_formats = ['txt', 'csv', 'tsv']
        self.phone_pattern = re.compile(r'^1[3-9]\d{9}$')  # 中国手机号格式
        
        # 统计数据，用于AI分析
        self.conversion_stats = {
            'total_input': 0,
            'valid_numbers': 0,
            'invalid_numbers': 0,
            'duplicates_removed': 0,
            'empty_lines': 0
        }
        
        self.logger.info(
            "ContactsConverter initialized for AI-Agent operation"
        )
    
    def convert_txt_to_contacts(self, file_path: str) -> List[Dict[str, str]]:
        """
        将TXT文件转换为标准化联系人数据
        
        Args:
            file_path: TXT文件路径
            
        Returns:
            List[Dict]: 标准化的联系人数据列表
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"Contact file not found: {file_path}")
            
            self.logger.info(f"Starting conversion of: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as file:
                raw_lines = file.readlines()
            
            self.conversion_stats['total_input'] = len(raw_lines)
            
            # 处理每一行数据
            contacts = []
            seen_numbers = set()
            
            for line_num, line in enumerate(raw_lines, 1):
                processed_contact = self._process_line(
                    line.strip(), line_num, seen_numbers
                )
                if processed_contact:
                    contacts.append(processed_contact)
            
            self.logger.info(
                f"Conversion completed: {len(contacts)} valid contacts "
                f"from {self.conversion_stats['total_input']} input lines"
            )
            
            return contacts
            
        except Exception as e:
            self.logger.error(
                f"Contacts conversion failed: {str(e)}", exc_info=True
            )
            raise
    
    def _process_line(self, line: str, line_num: int, 
                     seen_numbers: set) -> Optional[Dict[str, str]]:
        """
        处理单行数据
        
        Args:
            line: 输入行内容
            line_num: 行号
            seen_numbers: 已见过的号码集合（用于去重）
            
        Returns:
            Optional[Dict]: 处理后的联系人数据，无效时返回None
        """
        if not line or line == '0':  # 跳过空行和无效标记
            self.conversion_stats['empty_lines'] += 1
            return None
        
        # 尝试不同的解析方式
        contact_data = self._parse_contact_line(line)
        
        if not contact_data:
            self.logger.debug(f"Line {line_num}: Unable to parse '{line}'")
            self.conversion_stats['invalid_numbers'] += 1
            return None
        
        phone_number = contact_data['phone']
        
        # 验证手机号格式
        if not self._validate_phone_number(phone_number):
            self.logger.debug(
                f"Line {line_num}: Invalid phone format '{phone_number}'"
            )
            self.conversion_stats['invalid_numbers'] += 1
            return None
        
        # 检查重复
        if phone_number in seen_numbers:
            self.logger.debug(
                "Line %d: Duplicate number '%s'", line_num, phone_number
            )
            self.conversion_stats['duplicates_removed'] += 1
            return None
        
        seen_numbers.add(phone_number)
        self.conversion_stats['valid_numbers'] += 1
        
        # 生成标准化联系人数据
        standardized_contact = {
            'phone': phone_number,
            'name': contact_data.get('name', f"联系人{len(seen_numbers)}"),
            'email': contact_data.get('email', ''),
            'organization': contact_data.get('organization', ''),
            'source_line': line_num,
            'original_data': line
        }
        
        self.logger.debug(
            "Line %d: Processed contact '%s'", line_num, phone_number
        )
        return standardized_contact
    
    def _parse_contact_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        解析联系人数据行，支持多种格式
        
        Args:
            line: 输入行数据
            
        Returns:
            Optional[Dict]: 解析后的联系人数据
        """
        # 格式1: 纯手机号
        if self.phone_pattern.match(line):
            return {'phone': line}
        
        # 格式2和3: 分隔符格式处理
        contact_data = self._parse_delimited_format(line)
        if contact_data:
            return contact_data
        
        # 格式4: 从复杂文本中提取手机号
        return self._parse_text_with_phone(line)
    
    def _parse_delimited_format(self, line: str) -> Optional[Dict[str, str]]:
        """解析分隔符格式的联系人数据"""
        for delimiter in [',', '\t']:
            if delimiter in line:
                parts = [part.strip() for part in line.split(delimiter)]
                if len(parts) >= 2:
                    name, phone = parts[0], parts[1]
                    if self.phone_pattern.match(phone):
                        return {'phone': phone, 'name': name}
        return None
    
    def _parse_text_with_phone(self, line: str) -> Optional[Dict[str, str]]:
        """从复杂文本中提取手机号和姓名"""
        phone_match = self.phone_pattern.search(line)
        if phone_match:
            phone = phone_match.group()
            name_part = line[:phone_match.start()].strip()
            name = name_part if name_part and len(name_part) <= 50 else ''
            return {'phone': phone, 'name': name}
        return None
    
    def _validate_phone_number(self, phone: str) -> bool:
        """
        验证手机号码格式
        
        Args:
            phone: 手机号码字符串
            
        Returns:
            bool: 是否为有效手机号
        """
        return bool(self.phone_pattern.match(phone))
    
    def get_conversion_statistics(self) -> Dict[str, int]:
        """
        获取转换统计信息，用于AI Agent分析
        
        Returns:
            Dict: 包含各种统计数据的字典
        """
        stats = self.conversion_stats.copy()
        if stats['total_input'] > 0:
            stats['success_rate'] = (
                stats['valid_numbers'] / stats['total_input'] * 100
            )
        else:
            stats['success_rate'] = 0.0
            
        return stats
    
    def reset_statistics(self):
        """重置统计数据"""
        self.conversion_stats = {
            'total_input': 0,
            'valid_numbers': 0,
            'invalid_numbers': 0,
            'duplicates_removed': 0,
            'empty_lines': 0
        }
        self.logger.debug("Conversion statistics reset")
    
    def convert_csv_to_contacts(
            self,
            file_path: str,
            phone_column: str = 'phone',
            name_column: str = 'name'
    ) -> List[Dict[str, str]]:
        """
        将CSV文件转换为联系人数据
        
        Args:
            file_path: CSV文件路径
            phone_column: 手机号列名
            name_column: 姓名列名
            
        Returns:
            List[Dict]: 标准化的联系人数据列表
        """
        try:
            import csv
            contacts = []
            seen_numbers = set()
            
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, 1):
                    phone = row.get(phone_column, '').strip()
                    name = row.get(name_column, '').strip()
                    
                    if not phone:
                        continue
                    
                    if (self._validate_phone_number(phone) and
                            phone not in seen_numbers):
                        seen_numbers.add(phone)
                        contacts.append({
                            'phone': phone,
                            'name': name or f"联系人{len(seen_numbers)}",
                            'email': row.get('email', ''),
                            'organization': row.get('organization', ''),
                            'source_line': row_num,
                            'original_data': str(row)
                        })
            
            self.logger.info(
                "CSV conversion completed: %d contacts", len(contacts)
            )
            return contacts
            
        except Exception as e:
            self.logger.error(
                "CSV conversion failed: %s", str(e), exc_info=True
            )
            raise


def main():
    """测试函数"""
    import sys
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) != 2:
        print("Usage: python contacts_converter.py <contacts_file>")
        return
    
    file_path = sys.argv[1]
    converter = ContactsConverter()
    
    try:
        contacts = converter.convert_txt_to_contacts(file_path)
        stats = converter.get_conversion_statistics()
        
        print("\n转换完成:")
        print(f"- 输入行数: {stats['total_input']}")
        print(f"- 有效联系人: {stats['valid_numbers']}")
        print(f"- 无效数据: {stats['invalid_numbers']}")
        print(f"- 重复数据: {stats['duplicates_removed']}")
        print(f"- 空行: {stats['empty_lines']}")
        print(f"- 成功率: {stats['success_rate']:.1f}%")
        
        # 显示前几个联系人示例
        print("\n前5个联系人示例:")
        for i, contact in enumerate(contacts[:5], 1):
            print(f"{i}. {contact['name']}: {contact['phone']}")
            
    except (FileNotFoundError, ValueError, IOError) as e:
        print(f"转换失败: {str(e)}")


if __name__ == "__main__":
    main()