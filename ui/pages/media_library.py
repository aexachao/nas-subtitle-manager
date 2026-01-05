#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
媒体库页面（优化版）
- 移除快速扫描按钮
- 优化多层目录显示
"""

import time
from typing import Optional
import streamlit as st

from database.media_dao import MediaDAO
from database.task_dao import TaskDAO
from services.media_scanner import (
    scan_media_directory,
    discover_media_subdirectories
)
from utils.format_utils import format_file_size


def render_media_library_page(debug_mode: bool = False):
    """渲染媒体库页面"""
    
    # 顶部工具栏 - 3 列布局
    col_filter, col_dir_select, col_actions = st.columns([1.5, 4, 2.5])
    
    # ========== 列 1: 筛选器 ==========
    with col_filter:
        filter_type = st.radio(
            "筛选",
            ["全部", "有字幕", "无字幕"],
            horizontal=True,
            label_visibility="collapsed"
        )
    
    # ========== 列 2: 目录选择器 ==========
    with col_dir_select:
        # 获取子目录列表（使用缓存）
        if 'subdirs' not in st.session_state or st.session_state.get('refresh_subdirs'):
            with st.spinner("🔍 扫描目录结构..."):
                st.session_state.subdirs = discover_media_subdirectories(max_depth=3)
                st.session_state.refresh_subdirs = False
        
        subdirs = st.session_state.subdirs
        
        # 构建分组选项
        dir_options = _build_directory_options(subdirs)
        
        # 目录选择下拉框（无标签，无说明）
        selected_index = st.selectbox(
            "目录",
            range(len(dir_options)),
            format_func=lambda x: dir_options[x]['display'],
            index=0,
            key="selected_directory",
            label_visibility="collapsed"  # 隐藏标签
        )
        
        # 获取实际选中的目录路径
        selected_dir = dir_options[selected_index]['path']
    
    # ========== 列 3: 操作按钮 ==========
    with col_actions:
        col_refresh, col_start = st.columns([1, 1])
        
        with col_refresh:
            # 刷新按钮（去掉 emoji）
            if selected_dir is None:
                refresh_text = "刷新全部"
            else:
                refresh_text = "扫描"
            
            if st.button(refresh_text, use_container_width=True):
                _perform_scan(selected_dir, debug_mode)
        
        # 加载媒体文件
        filter_map = {
            "全部": None,
            "有字幕": True,
            "无字幕": False
        }
        
        files = MediaDAO.get_media_files_filtered(filter_map[filter_type])
        
        # 如果选择了子目录，进一步过滤
        if selected_dir:
            files = [f for f in files if selected_dir in f.file_path]
        
        # 统计选中文件
        selected_count = sum(
            1 for f in files if st.session_state.get(f"s_{f.id}", False)
        )
        
        with col_start:
            # 开始处理按钮（去掉 emoji）
            if selected_count > 0:
                btn_text = f"处理 ({selected_count})"
                btn_disabled = False
            else:
                btn_text = "开始处理"
                btn_disabled = True
            
            if st.button(
                btn_text,
                type="primary",
                use_container_width=True,
                disabled=btn_disabled
            ):
                _add_tasks_for_selected_files(files)
    
    # ========== 显示统计信息 ==========
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    _render_statistics(len(files), selected_count, selected_dir, filter_type)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    
    # ========== 空状态 ==========
    if not files:
        if selected_dir:
            st.info(f"🔭 该目录下暂无{filter_type}文件")
        else:
            st.info("🔭 暂无文件，请先扫描媒体库")
        return
    
    # ========== 全选功能 ==========
    current_select_all = st.checkbox("全选", key="select_all_box")  # 去掉 emoji
    last_select_all = st.session_state.get("_last_select_all", False)
    
    if current_select_all != last_select_all:
        for f in files:
            st.session_state[f"s_{f.id}"] = current_select_all
        st.session_state["_last_select_all"] = current_select_all
        st.rerun()
    
    # ========== 渲染文件列表 ==========
    for f in files:
        _render_media_card(f)


def _build_directory_options(subdirs: list) -> list:
    """
    构建层级化的目录选项
    
    Args:
        subdirs: 子目录列表
    
    Returns:
        选项列表，每项包含 display 和 path
    """
    options = [{'display': '📁 全部目录', 'path': None}]
    
    if not subdirs:
        return options
    
    # 按层级和名称排序
    sorted_dirs = sorted(subdirs, key=lambda x: (x.count('/') + x.count('\\'), x.lower()))
    
    # 分组显示
    current_depth = -1
    
    for d in sorted_dirs:
        depth = d.count('/') + d.count('\\')
        
        # 如果深度变化，添加分隔提示
        if depth != current_depth and depth > 0:
            current_depth = depth
            if depth == 1:
                options.append({'display': '─────── 📂 二级目录 ───────', 'path': None, 'disabled': True})
            elif depth == 2:
                options.append({'display': '─────── 📁 三级目录 ───────', 'path': None, 'disabled': True})
        
        # 获取目录名
        dir_name = d.split('/')[-1] if '/' in d else d.split('\\')[-1] if '\\' in d else d
        
        # 根据深度设置缩进和图标
        if depth == 0:
            display = f"📂 {dir_name}"
        elif depth == 1:
            display = f"　├─ 📁 {dir_name}"
        elif depth == 2:
            display = f"　　├─ 📄 {dir_name}"
        else:
            display = f"{'　' * depth}└─ 📄 {dir_name}"
        
        # 添加完整路径提示（鼠标悬停时显示）
        if depth > 0:
            display += f"  ({d})"
        
        options.append({'display': display, 'path': d})
    
    return options


def _render_statistics(total: int, selected: int, current_dir: Optional[str], filter_type: str):
    """渲染统计信息栏"""
    info_parts = []
    
    if current_dir:
        # 显示当前目录（最多显示 40 字符）
        display_path = current_dir if len(current_dir) <= 40 else "..." + current_dir[-37:]
        info_parts.append(f"📂 `{display_path}`")
    
    info_parts.append(f"📊 {filter_type}: **{total}** 个文件")
    
    if selected > 0:
        info_parts.append(f"✅ 已选: **{selected}** 个")
    
    st.caption(" | ".join(info_parts))


def _add_tasks_for_selected_files(files: list):
    """为选中的文件添加任务"""
    success_count = 0
    failed_files = []
    
    for f in files:
        if st.session_state.get(f"s_{f.id}", False):
            ok, msg = TaskDAO.add_task(f.file_path)
            if ok:
                success_count += 1
            else:
                failed_files.append((f.file_name, msg))
    
    # 显示结果
    if failed_files:
        st.warning(f"✅ 已添加 {success_count} 个任务，❌ {len(failed_files)} 个失败")
        for fname, reason in failed_files[:3]:
            st.caption(f"❌ {fname}: {reason}")
    else:
        st.toast(f"✅ 已添加 {success_count} 个任务")
    
    time.sleep(1)
    st.rerun()


def _perform_scan(subdirectory: Optional[str], debug_mode: bool):
    """执行扫描操作"""
    with st.spinner("🔍 扫描中..."):
        cnt, logs = scan_media_directory(
            subdirectory=subdirectory,
            debug=debug_mode
        )
        
        if subdirectory:
            st.toast(f"✅ {subdirectory}: 更新 {cnt} 个文件")
        else:
            st.toast(f"✅ 更新 {cnt} 个文件")
        
        if debug_mode and logs:
            with st.expander("📋 调试日志", expanded=True):
                for log in logs[:20]:
                    st.text(log)
    
    # 刷新目录列表
    st.session_state.refresh_subdirs = True
    st.rerun()


def _render_media_card(media_file):
    """渲染单个媒体文件卡片"""
    # 构建字幕徽章
    if not media_file.subtitles:
        badges = "<span class='status-chip chip-red'>无字幕</span>"
    else:
        badges = ""
        for sub in media_file.subtitles:
            lang = sub.lang.lower()
            if lang in ['zh', 'chs', 'cht']:
                cls = "chip-green"
            elif lang in ['en', 'eng']:
                cls = "chip-blue"
            else:
                cls = "chip-gray"
            badges += f"<span class='status-chip {cls}'>{sub.tag}</span>"
    
    # 布局：复选框 + 卡片
    c_check, c_card = st.columns([0.5, 20], gap="medium", vertical_alignment="center")
    
    with c_check:
        key = f"s_{media_file.id}"
        if key not in st.session_state:
            st.session_state[key] = False
        st.checkbox("选", key=key, label_visibility="collapsed")
    
    with c_card:
        st.markdown(
            f"""
            <div class="hero-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <div style="font-weight:600; font-size:15px; color:#f4f4f5; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;">
                        {media_file.file_name}
                    </div>
                    <div style="font-size:12px; color:#71717a; min-width:60px; text-align:right;">
                        {format_file_size(media_file.file_size)}
                    </div>
                </div>
                <div style="font-size:12px; color:#52525b; margin-bottom:12px; font-family:monospace;">
                    {media_file.file_path}
                </div>
                <div>{badges}</div>
            </div>
            """,
            unsafe_allow_html=True
        )