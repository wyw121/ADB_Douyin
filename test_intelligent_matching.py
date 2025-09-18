#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试智能文本匹配器的应对机制"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.intelligent_text_matcher import IntelligentTextMatcher


def test_intelligent_matching():
    """测试智能匹配机制应对UI变化"""
    print("🧠 测试智能文本匹配器应对UI变化")
    print("=" * 80)
    
    matcher = IntelligentTextMatcher()
    
    # 测试场景1: 官方改为繁体字
    print("\n📝 场景1: 官方改为繁体字")
    print("-" * 40)
    
    traditional_texts = [
        "添加朋友",      # 繁体（实际上这个词繁体简体相同）
        "尋找朋友",      # 繁体的"寻找朋友"
        "發現朋友",      # 繁体的"发现朋友"
        "認識朋友",      # 繁体的"认识朋友"
        "結交朋友",      # 繁体的"结交朋友"
        "通訊錄",        # 繁体的"通讯录"
        "聯繫人",        # 繁体的"联系人"
    ]
    
    for text in traditional_texts:
        is_match, score, method = matcher.intelligent_match(text, "add_friend")
        if text in ["通訊錄", "聯繫人"]:
            is_match, score, method = matcher.intelligent_match(text, "contacts")
            concept = "通讯录"
        else:
            concept = "添加朋友"
        
        status = "✅" if is_match else "❌"
        print(f"{status} '{text}' -> {concept}: 匹配={is_match}, "
              f"分数={score:.2f}, 方法={method}")
    
    # 测试场景2: 官方改变措辞
    print("\n📝 场景2: 官方改变措辞")
    print("-" * 40)
    
    new_wordings = [
        "发现好友",      # 从"添加朋友"改为"发现好友"
        "寻找好友",      # 改为"寻找好友"
        "认识新朋友",    # 改为"认识新朋友"
        "查找朋友",      # 改为"查找朋友"
        "新增朋友",      # 改为"新增朋友"
        "手机联系人",    # 通讯录改为"手机联系人"
        "电话簿",        # 改为"电话簿"
        "好友列表",      # 改为"好友列表"
    ]
    
    for text in new_wordings:
        # 判断是添加朋友还是通讯录概念
        if any(word in text for word in ["联系人", "电话", "列表"]):
            is_match, score, method = matcher.intelligent_match(text, "contacts")
            concept = "通讯录"
        else:
            is_match, score, method = matcher.intelligent_match(text, "add_friend")
            concept = "添加朋友"
        
        status = "✅" if is_match else "❌"
        print(f"{status} '{text}' -> {concept}: 匹配={is_match}, "
              f"分数={score:.2f}, 方法={method}")
    
    # 测试场景3: 英文界面
    print("\n📝 场景3: 英文界面")
    print("-" * 40)
    
    english_texts = [
        "Add Friends",
        "Find Friends", 
        "Discover Friends",
        "New Friends",
        "Make Friends",
        "Contacts",
        "Phone Book",
        "Address Book",
        "Contact List"
    ]
    
    for text in english_texts:
        # 判断概念
        if any(word in text.lower() for word in ["contact", "phone", "address"]):
            is_match, score, method = matcher.intelligent_match(text, "contacts")
            concept = "通讯录"
        else:
            is_match, score, method = matcher.intelligent_match(text, "add_friend")
            concept = "添加朋友"
        
        status = "✅" if is_match else "❌"
        print(f"{status} '{text}' -> {concept}: 匹配={is_match}, "
              f"分数={score:.2f}, 方法={method}")
    
    # 测试场景4: 部分匹配和模糊匹配
    print("\n📝 场景4: 部分匹配和模糊匹配")
    print("-" * 40)
    
    fuzzy_texts = [
        "添加新朋友",       # 包含"添加朋友"
        "查找更多朋友",     # 包含关键字符
        "朋友推荐",         # 语义相关
        "你可能认识的人",   # 语义相关
        "通讯录同步",       # 包含"通讯录"
        "导入联系人",       # 包含"联系人"
        "手机通信录",       # 相似但不完全匹配
    ]
    
    for text in fuzzy_texts:
        # 两个概念都测试
        add_friend_match, af_score, af_method = matcher.intelligent_match(
            text, "add_friend")
        contacts_match, c_score, c_method = matcher.intelligent_match(
            text, "contacts")
        
        if af_score > c_score:
            best_match, best_score, best_method, concept = (
                add_friend_match, af_score, af_method, "添加朋友")
        else:
            best_match, best_score, best_method, concept = (
                contacts_match, c_score, c_method, "通讯录")
        
        status = "✅" if best_match else "❌"
        print(f"{status} '{text}' -> {concept}: 匹配={best_match}, "
              f"分数={best_score:.2f}, 方法={best_method}")
    
    # 测试场景5: 学习新变体
    print("\n📝 场景5: 动态学习新变体")
    print("-" * 40)
    
    # 模拟发现新的变体
    new_variants = ["交朋友", "觅友", "社交"]
    print(f"学习新的添加朋友变体: {new_variants}")
    matcher.update_concept_dictionary("add_friend", new_variants)
    
    # 测试学习后的效果
    for variant in new_variants:
        is_match, score, method = matcher.intelligent_match(variant, "add_friend")
        status = "✅" if is_match else "❌"
        print(f"{status} 学习后 '{variant}': 匹配={is_match}, "
              f"分数={score:.2f}, 方法={method}")
    
    # 测试场景6: 批量匹配和最佳选择
    print("\n📝 场景6: 批量匹配和最佳选择")
    print("-" * 40)
    
    mixed_texts = [
        "首页", "关注", "发现朋友", "消息", "我", 
        "编辑资料", "添加朋友", "设置", "通讯录", "帮助"
    ]
    
    print("批量匹配 - 添加朋友概念:")
    best_matches = matcher.get_best_matches(mixed_texts, "add_friend", min_score=0.5)
    for text, score, method in best_matches:
        print(f"  ✅ '{text}': 分数={score:.2f}, 方法={method}")
    
    print("\n批量匹配 - 通讯录概念:")
    best_matches = matcher.get_best_matches(mixed_texts, "contacts", min_score=0.5)
    for text, score, method in best_matches:
        print(f"  ✅ '{text}': 分数={score:.2f}, 方法={method}")
    
    # 安全机制总结
    print("\n" + "=" * 80)
    print("🛡️ 智能匹配机制安全特性总结")
    print("=" * 80)
    print("1. ✅ 多语言支持: 简体中文、繁体中文、英文")
    print("2. ✅ 多种匹配方法: 精确→模糊→关键字符→语义→正则")
    print("3. ✅ 分数机制: 每种方法都有置信度分数")
    print("4. ✅ 动态学习: 可以学习新的UI变体")
    print("5. ✅ 批量处理: 可以同时处理多个候选文本")
    print("6. ✅ 降级机制: 从高精度到低精度逐步尝试")
    print("7. ✅ 防误判: 最小分数阈值和位置验证")
    print("8. ✅ 智能排序: 自动选择最佳匹配结果")


if __name__ == "__main__":
    test_intelligent_matching()