#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI上下文分析模块
负责分析和显示当前UI状态的关键信息，帮助判断模块是否在正确的界面工作
"""

import logging
import re
from typing import Dict, List, Optional, Any
from .ui_intelligence import UIAnalyzer


class UIContextAnalyzer:
    """UI上下文分析器"""
    
    # 抖音页面特征识别
    PAGE_SIGNATURES = {
        'main_feed': {
            'indicators': ['推荐', '关注', '直播', '同城'],
            'description': '抖音主页面(推荐页)'
        },
        'profile': {
            'indicators': ['个人资料', '编辑资料', '关注', '粉丝', '获赞'],
            'description': '个人资料页面'
        },
        'add_friends': {
            'indicators': ['添加朋友', '搜索用户名', '扫一扫', '通讯录'],
            'description': '添加朋友页面'
        },
        'contacts': {
            'indicators': ['手机通讯录', '通讯录朋友', '暂时没有找到'],
            'description': '手机通讯录页面'
        },
        'splash': {
            'indicators': ['启动', '加载', '欢迎', '初始化'],
            'description': '启动画面'
        },
        'navigation_bar': {
            'indicators': ['首页', '朋友', '消息', '我'],
            'description': '底部导航栏'
        },
        'unknown': {
            'indicators': [],
            'description': '未知页面'
        }
    }
    
    def __init__(self):
        """初始化UI上下文分析器"""
        self.logger = logging.getLogger(__name__)
        self.ui_analyzer = UIAnalyzer()
    
    def analyze_current_context(self, xml_content: str) -> Dict[str, Any]:
        """分析当前UI上下文
        
        Args:
            xml_content: UI XML内容
            
        Returns:
            包含页面信息的字典
        """
        if not xml_content:
            return self._create_empty_context("无法获取UI内容")
        
        # 解析XML
        if not self.ui_analyzer.parse_xml(xml_content):
            return self._create_empty_context("XML解析失败")
        
        # 分析页面类型
        page_type = self._detect_page_type(xml_content)
        
        # 提取关键信息
        key_elements = self._extract_key_elements()
        clickable_elements = self._extract_clickable_elements()
        text_elements = self._extract_text_elements()
        
        # 分析页面健康度
        health_score = self._calculate_page_health()
        
        return {
            'page_type': page_type,
            'page_description': self.PAGE_SIGNATURES[page_type]['description'],
            'total_elements': len(self.ui_analyzer.elements),
            'key_elements': key_elements,
            'clickable_elements': clickable_elements,
            'text_elements': text_elements,
            'health_score': health_score,
            'is_valid_page': health_score > 0.5,
            'xml_snippet': self._get_xml_snippet(xml_content),
            'recommendations': self._get_recommendations(page_type, health_score)
        }
    
    def _detect_page_type(self, xml_content: str) -> str:
        """检测页面类型"""
        page_scores = {}
        
        for page_type, signature in self.PAGE_SIGNATURES.items():
            if page_type == 'unknown':
                continue
                
            score = 0
            indicators = signature['indicators']
            
            for indicator in indicators:
                if indicator in xml_content:
                    score += 1
            
            # 计算匹配率
            if indicators:
                page_scores[page_type] = score / len(indicators)
            else:
                page_scores[page_type] = 0
        
        # 找到最高分的页面类型
        if page_scores:
            best_match = max(page_scores, key=page_scores.get)
            if page_scores[best_match] > 0.3:  # 至少30%匹配率
                return best_match
        
        return 'unknown'
    
    def _extract_key_elements(self) -> List[Dict[str, Any]]:
        """提取关键元素"""
        key_elements = []
        
        for element in self.ui_analyzer.elements:
            # 查找有文本的重要元素
            if element.text and len(element.text.strip()) > 0:
                # 过滤常见的重要元素
                if any(keyword in element.text for keyword in 
                       ['我', '首页', '推荐', '关注', '添加朋友', '通讯录', 
                        '返回', '确定', '取消', '搜索', '扫一扫']):
                    key_elements.append({
                        'text': element.text.strip(),
                        'class': element.class_name,
                        'clickable': element.clickable,
                        'bounds': element.bounds,
                        'center': element.get_center()
                    })
        
        return key_elements[:10]  # 限制数量
    
    def _extract_clickable_elements(self) -> List[Dict[str, Any]]:
        """提取可点击元素"""
        clickable_elements = []
        
        for element in self.ui_analyzer.elements:
            if element.clickable:
                text = element.text or element.content_desc or "无文本"
                clickable_elements.append({
                    'text': text.strip() if text else "无文本",
                    'class': element.class_name,
                    'bounds': element.bounds,
                    'center': element.get_center()
                })
        
        return clickable_elements[:15]  # 限制数量
    
    def _extract_text_elements(self) -> List[str]:
        """提取所有文本元素"""
        text_elements = []
        
        for element in self.ui_analyzer.elements:
            if element.text and len(element.text.strip()) > 0:
                text = element.text.strip()
                if len(text) < 50:  # 过滤过长的文本
                    text_elements.append(text)
        
        # 去重并排序
        return sorted(list(set(text_elements)))[:20]
    
    def _calculate_page_health(self) -> float:
        """计算页面健康度(0-1)"""
        if not self.ui_analyzer.elements:
            return 0.0
        
        score = 0.0
        total_elements = len(self.ui_analyzer.elements)
        
        # 基础分数：有元素就给基础分
        if total_elements > 0:
            score += 0.3
        
        # 可点击元素分数
        clickable_count = sum(1 for e in self.ui_analyzer.elements 
                            if e.clickable)
        if clickable_count > 0:
            score += 0.3
        
        # 文本元素分数
        text_count = sum(1 for e in self.ui_analyzer.elements 
                        if e.text and len(e.text.strip()) > 0)
        if text_count > 0:
            score += 0.2
        
        # 结构复杂度分数
        if total_elements > 10:
            score += 0.2
        
        return min(score, 1.0)
    
    def _get_xml_snippet(self, xml_content: str, max_length: int = 500) -> str:
        """获取XML片段用于显示"""
        if not xml_content:
            return "无XML内容"
        
        # 提取有意义的文本节点
        text_pattern = r'text="([^"]+)"'
        texts = re.findall(text_pattern, xml_content)
        
        # 提取resource-id
        id_pattern = r'resource-id="([^"]+)"'
        ids = re.findall(id_pattern, xml_content)
        
        snippet_parts = []
        
        if texts:
            snippet_parts.append(f"文本元素: {', '.join(texts[:8])}")
        
        if ids:
            relevant_ids = [id_val for id_val in ids 
                          if any(keyword in id_val.lower() 
                                for keyword in ['title', 'btn', 'text', 'tab'])]
            if relevant_ids:
                snippet_parts.append(f"关键ID: {', '.join(relevant_ids[:5])}")
        
        snippet = " | ".join(snippet_parts)
        
        if len(snippet) > max_length:
            snippet = snippet[:max_length] + "..."
        
        return snippet or "无关键信息"
    
    def _get_recommendations(self, page_type: str, health_score: float) -> List[str]:
        """获取建议"""
        recommendations = []
        
        if health_score < 0.3:
            recommendations.append("⚠️ 页面健康度低，建议重新获取UI或重启应用")
        
        if page_type == 'unknown':
            recommendations.append("❓ 未识别页面类型，可能需要导航到正确页面")
        
        if page_type == 'splash':
            recommendations.append("🔄 检测到启动画面，建议等待页面加载完成")
        
        if not recommendations:
            recommendations.append("✅ 页面状态正常")
        
        return recommendations
    
    def _create_empty_context(self, reason: str) -> Dict[str, Any]:
        """创建空的上下文信息"""
        return {
            'page_type': 'unknown',
            'page_description': f'无法分析: {reason}',
            'total_elements': 0,
            'key_elements': [],
            'clickable_elements': [],
            'text_elements': [],
            'health_score': 0.0,
            'is_valid_page': False,
            'xml_snippet': reason,
            'recommendations': [f"❌ {reason}"]
        }
    
    def print_context_info(self, context: Dict[str, Any], 
                          module_name: str = "UI分析") -> None:
        """打印上下文信息"""
        print(f"\n📊 {module_name} - UI上下文分析")
        print("=" * 60)
        
        print(f"📱 页面类型: {context['page_description']}")
        print(f"🏗️ 元素总数: {context['total_elements']}")
        print(f"💯 健康度: {context['health_score']:.2f}")
        print(f"✅ 页面有效: {'是' if context['is_valid_page'] else '否'}")
        
        if context['key_elements']:
            print(f"\n🔍 关键元素 ({len(context['key_elements'])}个):")
            for i, elem in enumerate(context['key_elements'][:5], 1):
                print(f"  {i}. '{elem['text']}' @ {elem['center']} "
                      f"({'可点击' if elem['clickable'] else '不可点击'})")
        
        if context['text_elements']:
            print(f"\n📝 页面文本: {', '.join(context['text_elements'][:10])}")
        
        print(f"\n🔬 XML片段: {context['xml_snippet']}")
        
        if context['recommendations']:
            print(f"\n💡 建议:")
            for rec in context['recommendations']:
                print(f"  {rec}")
        
        print("=" * 60)
    
    def should_restart_app(self, context: Dict[str, Any], 
                          expected_page: str = None) -> bool:
        """判断是否应该重启应用"""
        # 页面健康度太低
        if context['health_score'] < 0.2:
            self.logger.warning("页面健康度过低，建议重启应用")
            return True
        
        # 检测到启动画面卡住
        if context['page_type'] == 'splash' and context['total_elements'] < 5:
            self.logger.warning("启动画面卡住，建议重启应用")
            return True
        
        # 如果指定了期望页面，但当前页面不匹配且健康度低
        if (expected_page and 
            context['page_type'] != expected_page and 
            context['health_score'] < 0.5):
            self.logger.warning(f"期望页面'{expected_page}'但当前是'"
                              f"{context['page_type']}'，建议重启应用")
            return True
        
        return False