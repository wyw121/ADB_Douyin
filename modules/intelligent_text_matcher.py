#!/usr/bin/env python3
"""
智能文本匹配器 - 应对UI文本变化的智能识别机制
"""

import logging
import re
from typing import List, Dict, Set, Optional, Tuple
from difflib import SequenceMatcher


class IntelligentTextMatcher:
    """智能文本匹配器 - 处理UI文本变化和语言差异"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 核心概念词典 - 多语言和变体支持
        self.concept_dictionaries = {
            "add_friend": {
                # 简体中文变体
                "simplified_chinese": [
                    "添加朋友", "添加好友", "加朋友", "加好友", "新增朋友",
                    "寻找朋友", "查找朋友", "发现朋友", "认识朋友", "结交朋友"
                ],
                # 繁体中文变体
                "traditional_chinese": [
                    "添加朋友", "添加好友", "加朋友", "加好友", "新增朋友",
                    "尋找朋友", "查找朋友", "發現朋友", "認識朋友", "結交朋友"
                ],
                # 英文变体
                "english": [
                    "Add Friends", "Add Friend", "Find Friends", "Discover Friends",
                    "New Friends", "Make Friends", "Connect", "Follow"
                ],
                # 关键字符组合
                "key_chars": ["加", "添", "友", "朋", "找", "寻", "發", "認"],
                # 语义相关词
                "semantic_related": ["推荐", "建议", "可能认识", "你可能", "推薦", "建議"]
            },
            
            "contacts": {
                # 简体中文变体
                "simplified_chinese": [
                    "通讯录", "联系人", "通信录", "手机通讯录", "电话簿",
                    "好友列表", "联系方式", "通讯簿"
                ],
                # 繁体中文变体
                "traditional_chinese": [
                    "通訊錄", "聯繫人", "通信錄", "手機通訊錄", "電話簿",
                    "好友列表", "聯繫方式", "通訊簿"
                ],
                # 英文变体
                "english": [
                    "Contacts", "Phone Book", "Address Book", "Contact List",
                    "Friends List", "Phonebook"
                ],
                # 关键字符组合
                "key_chars": ["通", "讯", "录", "联", "系", "人", "訊", "錄", "聯"],
                # 语义相关词
                "semantic_related": ["同步", "导入", "手机", "電話", "电话"]
            }
        }
        
        # 模糊匹配配置
        self.fuzzy_match_threshold = 0.7  # 相似度阈值
        self.partial_match_threshold = 0.8  # 部分匹配阈值
        
    def intelligent_match(self, text: str, concept: str) -> Tuple[bool, float, str]:
        """智能匹配文本与概念
        
        Args:
            text: 要匹配的文本
            concept: 概念类型 ("add_friend" 或 "contacts")
            
        Returns:
            (是否匹配, 匹配分数, 匹配方法)
        """
        if not text or not concept:
            return False, 0.0, "invalid_input"
        
        text = text.strip()
        if not text:
            return False, 0.0, "empty_text"
        
        if concept not in self.concept_dictionaries:
            return False, 0.0, "unknown_concept"
        
        concept_dict = self.concept_dictionaries[concept]
        
        # 方法1: 精确匹配
        exact_match, score = self._exact_match(text, concept_dict)
        if exact_match:
            return True, score, "exact_match"
        
        # 方法2: 模糊匹配
        fuzzy_match, score = self._fuzzy_match(text, concept_dict)
        if fuzzy_match:
            return True, score, "fuzzy_match"
        
        # 方法3: 关键字符匹配
        char_match, score = self._key_char_match(text, concept_dict)
        if char_match:
            return True, score, "key_char_match"
        
        # 方法4: 语义相关匹配
        semantic_match, score = self._semantic_match(text, concept_dict)
        if semantic_match:
            return True, score, "semantic_match"
        
        # 方法5: 正则表达式匹配
        regex_match, score = self._regex_match(text, concept)
        if regex_match:
            return True, score, "regex_match"
        
        return False, 0.0, "no_match"
    
    def _exact_match(self, text: str, concept_dict: Dict) -> Tuple[bool, float]:
        """精确匹配"""
        all_variants = []
        for lang_variants in ["simplified_chinese", "traditional_chinese", "english"]:
            if lang_variants in concept_dict:
                all_variants.extend(concept_dict[lang_variants])
        
        if text in all_variants:
            return True, 1.0
        
        # 检查文本是否包含完整的变体
        for variant in all_variants:
            if variant in text and len(variant) > 2:  # 避免太短的词误判
                return True, 0.95
        
        return False, 0.0
    
    def _fuzzy_match(self, text: str, concept_dict: Dict) -> Tuple[bool, float]:
        """模糊匹配 - 处理相似但不完全相同的文本"""
        all_variants = []
        for lang_variants in ["simplified_chinese", "traditional_chinese", "english"]:
            if lang_variants in concept_dict:
                all_variants.extend(concept_dict[lang_variants])
        
        max_ratio = 0.0
        for variant in all_variants:
            # 计算相似度
            ratio = SequenceMatcher(None, text, variant).ratio()
            max_ratio = max(max_ratio, ratio)
            
            # 检查部分匹配
            if len(variant) > 2:
                if variant in text:
                    partial_ratio = len(variant) / max(len(text), len(variant))
                    max_ratio = max(max_ratio, partial_ratio * 0.9)
        
        if max_ratio >= self.fuzzy_match_threshold:
            return True, max_ratio
        
        return False, max_ratio
    
    def _key_char_match(self, text: str, concept_dict: Dict) -> Tuple[bool, float]:
        """关键字符匹配 - 基于核心字符的匹配"""
        if "key_chars" not in concept_dict:
            return False, 0.0
        
        key_chars = concept_dict["key_chars"]
        matched_chars = 0
        
        for char in key_chars:
            if char in text:
                matched_chars += 1
        
        # 计算匹配比例
        match_ratio = matched_chars / len(key_chars)
        
        # 需要至少匹配一半的关键字符
        if match_ratio >= 0.5:
            return True, match_ratio * 0.8  # 降权，因为不如精确匹配可靠
        
        return False, match_ratio
    
    def _semantic_match(self, text: str, concept_dict: Dict) -> Tuple[bool, float]:
        """语义相关匹配 - 基于语义相关词的匹配"""
        if "semantic_related" not in concept_dict:
            return False, 0.0
        
        semantic_words = concept_dict["semantic_related"]
        
        for word in semantic_words:
            if word in text:
                return True, 0.6  # 语义匹配分数较低，因为可能有误判
        
        return False, 0.0
    
    def _regex_match(self, text: str, concept: str) -> Tuple[bool, float]:
        """正则表达式匹配 - 基于模式的匹配"""
        patterns = {
            "add_friend": [
                r".*[加添].*[朋友].*",  # 包含"加/添"和"朋友"
                r".*[寻找查發認尋].*[朋友].*",  # 包含"寻找/查/發/認/尋"和"朋友"
                r".*[Aa]dd.*[Ff]riend.*",  # 英文模式
                r".*[Ff]ind.*[Ff]riend.*",  # 英文查找模式
            ],
            "contacts": [
                r".*[通訊通信].*[录錄].*",  # 通讯录模式
                r".*[联聯].*[系人].*",  # 联系人模式
                r".*[Cc]ontact.*",  # 英文联系人
                r".*[Pp]hone.*[Bb]ook.*",  # 英文电话簿
            ]
        }
        
        if concept not in patterns:
            return False, 0.0
        
        for pattern in patterns[concept]:
            if re.match(pattern, text, re.IGNORECASE):
                return True, 0.7  # 正则匹配分数中等
        
        return False, 0.0
    
    def batch_match(self, texts: List[str], concept: str) -> List[Tuple[str, bool, float, str]]:
        """批量匹配文本"""
        results = []
        for text in texts:
            is_match, score, method = self.intelligent_match(text, concept)
            results.append((text, is_match, score, method))
        
        # 按匹配分数排序
        results.sort(key=lambda x: x[2], reverse=True)
        return results
    
    def get_best_matches(self, texts: List[str], concept: str, 
                        min_score: float = 0.5) -> List[Tuple[str, float, str]]:
        """获取最佳匹配结果"""
        matches = []
        for text in texts:
            is_match, score, method = self.intelligent_match(text, concept)
            if is_match and score >= min_score:
                matches.append((text, score, method))
        
        # 按分数排序
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def update_concept_dictionary(self, concept: str, new_variants: List[str], 
                                lang_type: str = "simplified_chinese"):
        """动态更新概念词典 - 支持学习新的变体"""
        if concept not in self.concept_dictionaries:
            self.concept_dictionaries[concept] = {}
        
        if lang_type not in self.concept_dictionaries[concept]:
            self.concept_dictionaries[concept][lang_type] = []
        
        for variant in new_variants:
            if variant not in self.concept_dictionaries[concept][lang_type]:
                self.concept_dictionaries[concept][lang_type].append(variant)
                self.logger.info(f"学习新变体: {concept} -> {variant}")
    
    def analyze_text_patterns(self, texts: List[str]) -> Dict[str, any]:
        """分析文本模式 - 用于发现新的UI模式"""
        analysis = {
            "total_texts": len(texts),
            "unique_texts": len(set(texts)),
            "char_frequency": {},
            "word_patterns": {},
            "length_distribution": {}
        }
        
        # 字符频率分析
        for text in texts:
            for char in text:
                analysis["char_frequency"][char] = analysis["char_frequency"].get(char, 0) + 1
        
        # 长度分布
        for text in texts:
            length = len(text)
            analysis["length_distribution"][length] = analysis["length_distribution"].get(length, 0) + 1
        
        return analysis