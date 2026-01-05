#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言检测工具
基于字幕内容检测语言类型
"""

import re


def detect_language_from_subtitle(srt_path: str) -> str:
    """
    从字幕文件内容检测语言
    
    Args:
        srt_path: SRT 文件路径
    
    Returns:
        语言代码（zh/chs/cht/en/ja/ko/unknown）
    """
    try:
        with open(srt_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw_content = f.read(4096)  # 只读取前 4KB
        
        # 移除时间轴和序号
        content = re.sub(
            r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}',
            '',
            raw_content
        )
        content = re.sub(r'^\d+$', '', content, flags=re.MULTILINE)
        
        # 统计字符
        total_chars = len(re.sub(r'\s+', '', content))
        if total_chars < 50:
            return 'unknown'
        
        # 统计各语言特征字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', content))
        hiragana_chars = len(re.findall(r'[\u3040-\u309f]', content))
        katakana_chars = len(re.findall(r'[\u30a0-\u30ff]', content))
        hangul_chars = len(re.findall(r'[\uac00-\ud7af]', content))
        
        # 繁体中文特征字
        traditional_markers = [
            '臺', '灣', '繁', '體', '於', '與', 
            '個', '們', '裡', '這', '妳', '臉', 
            '廳', '學', '習'
        ]
        traditional_count = sum(1 for char in traditional_markers if char in content)
        
        # 统计英文单词
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', content)
        english_chars = sum(len(word) for word in english_words)
        
        # 判断语言
        if hiragana_chars >= 5 or katakana_chars >= 5:
            return 'ja'
        
        if hangul_chars >= 10:
            return 'ko'
        
        if chinese_chars >= 10:
            # 区分简繁体
            if traditional_count >= 3 and traditional_count / chinese_chars >= 0.2:
                return 'cht'
            return 'chs'
        
        if total_chars > 0 and english_chars / total_chars >= 0.5:
            return 'en'
        
        return 'unknown'
        
    except Exception as e:
        print(f"[LangDetection] Failed to detect language for {srt_path}: {e}")
        return 'unknown'


def detect_language_from_filename(filename: str) -> str:
    """
    从文件名检测语言
    
    Args:
        filename: 文件名
    
    Returns:
        语言代码（zh/chs/cht/en/ja/ko/unknown）
    """
    filename_lower = filename.lower()
    
    # 检查常见语言代码
    lang_codes = {
        'chs': 'chs',
        'cht': 'cht',
        'eng': 'en',
        'jpn': 'ja',
        'kor': 'ko',
        'zh': 'chs',
        'en': 'en',
        'ja': 'ja',
        'ko': 'ko',
    }
    
    for code, lang in lang_codes.items():
        # 检查 .code. 或 .code 结尾
        if f".{code}." in filename_lower or filename_lower.endswith(f".{code}"):
            return lang
    
    return 'unknown'


def detect_language_combined(
    srt_path: str,
    filename: str
) -> tuple[str, str]:
    """
    综合检测语言（文件名 + 内容）
    
    Args:
        srt_path: SRT 文件路径
        filename: 文件名
    
    Returns:
        (语言代码, 标签)
    """
    # 先尝试从文件名检测
    lang_from_filename = detect_language_from_filename(filename)
    
    if lang_from_filename != 'unknown':
        return lang_from_filename, get_language_tag(lang_from_filename)
    
    # 文件名检测失败，尝试内容检测
    lang_from_content = detect_language_from_subtitle(srt_path)
    return lang_from_content, get_language_tag(lang_from_content)


def get_language_tag(lang_code: str) -> str:
    """
    获取语言标签
    
    Args:
        lang_code: 语言代码
    
    Returns:
        语言标签（中文）
    """
    lang_map = {
        'chs': '简中',
        'cht': '繁中',
        'zh': '中文',
        'en': '英语',
        'eng': '英语',
        'ja': '日语',
        'jpn': '日语',
        'ko': '韩语',
        'kor': '韩语',
        'fr': '法语',
        'de': '德语',
        'ru': '俄语',
        'es': '西班牙语',
        'unknown': '未知'
    }
    return lang_map.get(lang_code.lower(), '未知')