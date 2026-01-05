#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格式化工具函数
提供各种数据格式化功能
"""

from core.models import ISO_LANG_MAP


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
    
    Returns:
        格式化后的字符串（如 "1.5 GB"）
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_timestamp(seconds: float) -> str:
    """
    格式化时间戳为 SRT 格式
    
    Args:
        seconds: 秒数
    
    Returns:
        SRT 时间格式（HH:MM:SS,mmm）
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def get_lang_name(code: str) -> str:
    """
    获取语言代码对应的中文名称
    
    Args:
        code: 语言代码（如 'zh', 'en'）
    
    Returns:
        中文名称
    """
    return ISO_LANG_MAP.get(code.lower(), code)


def format_duration(seconds: int) -> str:
    """
    格式化时长
    
    Args:
        seconds: 秒数
    
    Returns:
        格式化后的时长（如 "1h 23m"）
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀
    
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_percentage(current: int, total: int, decimals: int = 1) -> str:
    """
    格式化百分比
    
    Args:
        current: 当前值
        total: 总值
        decimals: 小数位数
    
    Returns:
        百分比字符串（如 "75.5%"）
    """
    if total == 0:
        return "0%"
    
    percentage = (current / total) * 100
    return f"{percentage:.{decimals}f}%"