#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADB Contacts Manager Module

AI-Agent-Friendly Android通讯录管理器
通过ADB处理VCF文件到Android设备的传输和导入操作

Author: AI Assistant
Created: 2025/09/18
"""

import logging
import subprocess
import time
from typing import Optional, List, Dict
from pathlib import Path


class ADBContactsManager:
    """
    ADB通讯录管理器
    
    专为AI Agent设计，提供自动化的Android设备通讯录导入功能
    包含完整的错误处理、重试机制和操作统计
    """
    
    def __init__(self, device_id: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        """
        初始化ADB通讯录管理器
        
        Args:
            device_id: 可选的设备ID，不指定时使用第一个连接的设备
            logger: 可选的日志记录器，用于AI Agent监控
        """
        self.device_id = device_id
        self.logger = logger or logging.getLogger(__name__)
        self.adb_path = self._find_adb_executable()
        
        # 设备通讯录存储路径
        self.device_contacts_path = "/sdcard/contacts_import/"
        self.temp_vcf_name = "import_contacts.vcf"
        
        # 操作统计，用于AI分析
        self.operation_stats = {
            'files_pushed': 0,
            'import_attempts': 0,
            'successful_imports': 0,
            'failed_operations': 0,
            'device_connection_errors': 0
        }
        
        self.logger.info("ADBContactsManager initialized for device: %s",
                         device_id or "default")
    
    def _find_adb_executable(self) -> str:
        """
        查找ADB可执行文件路径
        
        Returns:
            str: ADB可执行文件路径
        """
        # 首先检查项目本地的ADB
        local_adb = Path(__file__).parent.parent / "platform-tools" / "adb.exe"
        if local_adb.exists():
            return str(local_adb)
        
        # 检查系统PATH中的ADB
        try:
            result = subprocess.run(['where', 'adb'], 
                                  capture_output=True, text=True, 
                                  shell=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except Exception:
            pass
        
        # 默认返回adb命令
        return "adb"
    
    def check_device_connection(self) -> bool:
        """
        检查设备连接状态
        
        Returns:
            bool: 设备是否连接且可用
        """
        try:
            cmd = [self.adb_path, "devices"]
            if self.device_id:
                cmd = [self.adb_path, "-s", self.device_id, "get-state"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=10)
            
            if self.device_id:
                return result.returncode == 0 and "device" in result.stdout
            else:
                # 检查至少有一个设备连接
                lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                connected_devices = [line for line in lines 
                                   if '\tdevice' in line]
                return len(connected_devices) > 0
                
        except Exception as e:
            self.logger.error("Device connection check failed: %s", str(e))
            self.operation_stats['device_connection_errors'] += 1
            return False
    
    def push_vcf_to_device(self, vcf_file_path: str) -> bool:
        """
        将VCF文件推送到Android设备
        
        Args:
            vcf_file_path: 本地VCF文件路径
            
        Returns:
            bool: 推送是否成功
        """
        try:
            if not Path(vcf_file_path).exists():
                raise FileNotFoundError(f"VCF file not found: {vcf_file_path}")
            
            if not self.check_device_connection():
                raise ConnectionError("No Android device connected")
            
            # 在设备上创建目录
            self._create_device_directory()
            
            # 构建推送命令
            device_vcf_path = f"{self.device_contacts_path}{self.temp_vcf_name}"
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            
            cmd.extend(["push", vcf_file_path, device_vcf_path])
            
            self.logger.info("Pushing VCF file to device: %s -> %s", 
                           vcf_file_path, device_vcf_path)
            
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=30)
            
            if result.returncode == 0:
                self.operation_stats['files_pushed'] += 1
                self.logger.info("VCF file pushed successfully")
                return True
            else:
                self.logger.error("Failed to push VCF file: %s", 
                                result.stderr)
                self.operation_stats['failed_operations'] += 1
                return False
                
        except Exception as e:
            self.logger.error("VCF push operation failed: %s", str(e))
            self.operation_stats['failed_operations'] += 1
            return False
    
    def _create_device_directory(self):
        """在设备上创建导入目录"""
        try:
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            
            cmd.extend(["shell", "mkdir", "-p", self.device_contacts_path])
            
            subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
        except Exception as e:
            self.logger.debug("Directory creation failed (may already exist): %s",
                            str(e))
    
    def trigger_contacts_import(self) -> bool:
        """
        触发Android系统通讯录导入
        
        Returns:
            bool: 导入触发是否成功
        """
        try:
            if not self.check_device_connection():
                raise ConnectionError("No Android device connected")
            
            device_vcf_path = f"{self.device_contacts_path}{self.temp_vcf_name}"
            
            # 方法1: 使用Intent触发导入
            success = self._trigger_import_via_intent(device_vcf_path)
            
            if not success:
                # 方法2: 使用Content Provider导入
                success = self._trigger_import_via_content_provider()
            
            self.operation_stats['import_attempts'] += 1
            
            if success:
                self.operation_stats['successful_imports'] += 1
                self.logger.info("Contacts import triggered successfully")
            else:
                self.operation_stats['failed_operations'] += 1
                self.logger.error("Failed to trigger contacts import")
            
            return success
            
        except Exception as e:
            self.logger.error("Import trigger failed: %s", str(e))
            self.operation_stats['failed_operations'] += 1
            return False
    
    def _trigger_import_via_intent(self, device_vcf_path: str) -> bool:
        """通过Intent触发VCF导入"""
        try:
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            
            # 使用VIEW Intent打开VCF文件
            cmd.extend([
                "shell", "am", "start",
                "-a", "android.intent.action.VIEW",
                "-d", f"file://{device_vcf_path}",
                "-t", "text/vcard"
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=15)
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.debug("Intent-based import failed: %s", str(e))
            return False
    
    def _trigger_import_via_content_provider(self) -> bool:
        """通过Content Provider直接导入联系人"""
        try:
            # 注意：这种方法需要Root权限或特殊权限
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            
            # 尝试使用content命令导入
            cmd.extend([
                "shell", "content", "insert",
                "--uri", "content://com.android.contacts/raw_contacts",
                "--bind", "account_name:s:Phone --bind account_type:s:null"
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=15)
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.debug("Content provider import failed: %s", str(e))
            return False
    
    def import_contacts_from_vcf(self, vcf_file_path: str) -> bool:
        """
        完整的通讯录导入流程
        
        Args:
            vcf_file_path: VCF文件路径
            
        Returns:
            bool: 整个导入流程是否成功
        """
        try:
            self.logger.info("Starting complete contacts import process")
            
            # 步骤1: 推送VCF文件到设备
            if not self.push_vcf_to_device(vcf_file_path):
                return False
            
            # 等待文件稳定
            time.sleep(1)
            
            # 步骤2: 触发导入
            if not self.trigger_contacts_import():
                return False
            
            # 步骤3: 清理临时文件
            self._cleanup_device_files()
            
            self.logger.info("Complete contacts import process finished")
            return True
            
        except Exception as e:
            self.logger.error("Complete import process failed: %s", str(e))
            return False
    
    def _cleanup_device_files(self):
        """清理设备上的临时文件"""
        try:
            device_vcf_path = f"{self.device_contacts_path}{self.temp_vcf_name}"
            
            cmd = [self.adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            
            cmd.extend(["shell", "rm", "-f", device_vcf_path])
            
            subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            self.logger.debug("Device temporary files cleaned up")
            
        except Exception as e:
            self.logger.debug("Cleanup failed (non-critical): %s", str(e))
    
    def get_connected_devices(self) -> List[str]:
        """
        获取连接的Android设备列表
        
        Returns:
            List[str]: 设备ID列表
        """
        try:
            result = subprocess.run([self.adb_path, "devices"], 
                                  capture_output=True, text=True, 
                                  timeout=10)
            
            if result.returncode != 0:
                return []
            
            devices = []
            lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
            
            for line in lines:
                if '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)
            
            return devices
            
        except Exception as e:
            self.logger.error("Failed to get device list: %s", str(e))
            return []
    
    def get_operation_statistics(self) -> Dict[str, int]:
        """
        获取操作统计信息，用于AI Agent分析
        
        Returns:
            Dict: 包含统计数据的字典
        """
        stats = self.operation_stats.copy()
        if stats['import_attempts'] > 0:
            stats['success_rate'] = (
                stats['successful_imports'] / stats['import_attempts'] * 100
            )
        else:
            stats['success_rate'] = 0.0
            
        return stats
    
    def reset_statistics(self):
        """重置统计数据"""
        self.operation_stats = {
            'files_pushed': 0,
            'import_attempts': 0,
            'successful_imports': 0,
            'failed_operations': 0,
            'device_connection_errors': 0
        }
        self.logger.debug("ADB operation statistics reset")


def main():
    """测试函数"""
    import sys
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    manager = ADBContactsManager()
    
    # 检查设备连接
    if not manager.check_device_connection():
        print("❌ 没有检测到Android设备连接")
        print("请确保:")
        print("1. USB调试已启用")
        print("2. 设备已通过USB连接")
        print("3. 已授权此计算机的调试访问")
        return
    
    # 显示连接的设备
    devices = manager.get_connected_devices()
    print(f"✓ 检测到 {len(devices)} 个设备: {devices}")
    
    # 如果提供了VCF文件路径，执行导入
    if len(sys.argv) > 1:
        vcf_file = sys.argv[1]
        print(f"\n开始导入通讯录: {vcf_file}")
        
        success = manager.import_contacts_from_vcf(vcf_file)
        stats = manager.get_operation_statistics()
        
        print("\n导入统计:")
        print(f"- 文件推送: {stats['files_pushed']}")
        print(f"- 导入尝试: {stats['import_attempts']}")
        print(f"- 成功导入: {stats['successful_imports']}")
        print(f"- 失败操作: {stats['failed_operations']}")
        print(f"- 成功率: {stats['success_rate']:.1f}%")
        
        if success:
            print("\n✓ 通讯录导入完成")
        else:
            print("\n❌ 通讯录导入失败")
    else:
        print("\n使用方法: python adb_contacts_manager.py <vcf_file_path>")


if __name__ == "__main__":
    main()