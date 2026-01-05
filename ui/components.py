#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 可复用组件
提供通用的 UI 元素
"""

import streamlit as st
from typing import List, Optional, Callable


def render_directory_quick_actions(
    subdirs: List[str],
    on_scan: Callable[[Optional[str]], None],
    max_buttons: int = 5
):
    """
    渲染目录快捷操作按钮
    
    Args:
        subdirs: 子目录列表
        on_scan: 扫描回调函数 (subdirectory: Optional[str])
        max_buttons: 最多显示几个快捷按钮
    """
    if not subdirs:
        return
    
    st.caption("🚀 快速扫描")
    
    # 智能选择最常用的目录（按深度排序）
    # 优先显示一级目录
    first_level_dirs = [d for d in subdirs if '/' not in d and '\\' not in d]
    
    # 如果一级目录太少，补充二级目录
    if len(first_level_dirs) < max_buttons:
        second_level_dirs = [
            d for d in subdirs 
            if d.count('/') == 1 or d.count('\\') == 1
        ]
        quick_dirs = first_level_dirs + second_level_dirs[:max_buttons - len(first_level_dirs)]
    else:
        quick_dirs = first_level_dirs[:max_buttons]
    
    # 渲染快捷按钮
    cols = st.columns(min(len(quick_dirs), max_buttons))
    
    for idx, dir_path in enumerate(quick_dirs):
        if idx >= max_buttons:
            break
        
        with cols[idx]:
            # 提取目录名（去掉路径）
            dir_name = dir_path.split('/')[-1].split('\\')[-1]
            if len(dir_name) > 12:
                dir_name = dir_name[:10] + '..'
            
            if st.button(
                f"📂 {dir_name}",
                key=f"quick_scan_{idx}",
                use_container_width=True,
                help=f"快速扫描: {dir_path}"
            ):
                on_scan(dir_path)


def render_scan_statistics(
    total_files: int,
    selected_count: int,
    current_dir: Optional[str] = None,
    filter_type: str = "全部"
):
    """
    渲染扫描统计信息
    
    Args:
        total_files: 总文件数
        selected_count: 选中文件数
        current_dir: 当前目录
        filter_type: 筛选类型
    """
    info_parts = []
    
    if current_dir:
        # 缩短路径显示
        if len(current_dir) > 40:
            display_path = "..." + current_dir[-37:]
        else:
            display_path = current_dir
        info_parts.append(f"📂 `{display_path}`")
    
    info_parts.append(f"📊 {filter_type}: {total_files} 个")
    
    if selected_count > 0:
        info_parts.append(f"✅ 已选: {selected_count} 个")
    
    st.caption(" | ".join(info_parts))


def render_progress_indicator(current: int, total: int, message: str = ""):
    """
    渲染进度指示器
    
    Args:
        current: 当前进度
        total: 总进度
        message: 进度消息
    """
    if total == 0:
        progress = 0
    else:
        progress = current / total
    
    st.progress(progress, text=message if message else f"{current}/{total}")


def render_empty_state(
    icon: str = "🔭",
    title: str = "暂无数据",
    description: Optional[str] = None,
    action_label: Optional[str] = None,
    action_callback: Optional[Callable] = None
):
    """
    渲染空状态
    
    Args:
        icon: 图标
        title: 标题
        description: 描述
        action_label: 操作按钮标签
        action_callback: 操作回调
    """
    st.markdown(f"<div style='text-align: center; padding: 60px 20px;'>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size: 64px; margin-bottom: 16px;'>{icon}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size: 18px; font-weight: 600; color: #a1a1aa; margin-bottom: 8px;'>{title}</div>", unsafe_allow_html=True)
    
    if description:
        st.markdown(f"<div style='font-size: 14px; color: #71717a;'>{description}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if action_label and action_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(action_label, use_container_width=True, type="primary"):
                action_callback()