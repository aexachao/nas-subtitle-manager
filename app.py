#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NAS 字幕管家 V7.0 - 重构版
主程序：仅负责 Streamlit UI 入口和页面路由
"""

import os
import streamlit as st
import logging

# 抑制 Tornado WebSocket 警告
logging.getLogger('tornado.application').setLevel(logging.ERROR)
logging.getLogger('tornado.access').setLevel(logging.ERROR)

# 导入核心模块
# 导入核心模块
from database.connection import init_database
from core.worker import start_worker
# OLD: from ui.sidebar import render_sidebar
from ui.settings_modal import render_settings_dialog
from ui.pages.media_library import render_media_library_page
from ui.pages.task_queue import render_task_queue_page
from ui.styles import HERO_CSS


# ============================================================================
# 主程序
# ============================================================================

def main():
    """主函数"""
    # 页面配置
    st.set_page_config(
        page_title="NAS 字幕管家",
        layout="wide"
    )
    
    # 应用样式
    st.markdown(HERO_CSS, unsafe_allow_html=True)
    
    # Header 布局 (Logo + 标题 + 设置按钮) - 与媒体库工具栏对齐
    col_h1, col_h2, col_h3, col_h4, col_settings = st.columns([2.2, 1.3, 3, 0.8, 0.8])
    
    with col_h1:
        # 使用 base64 编码图片并用 flexbox 实现垂直居中
        import base64
        with open("assets/logo.png", "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()
        
        st.markdown(
            f"""
            <div style='display: flex; align-items: center; gap: 16px;'>
                <img src='data:image/png;base64,{logo_base64}' style='height: 48px; width: 48px; object-fit: contain;' />
                <h1 style='margin: 0; font-size: 32px; font-weight: 700; line-height: 48px;'>NAS 字幕管家</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # 空列用于对齐
    with col_h2:
        pass
    with col_h3:
        pass
    with col_h4:
        pass
        
    with col_settings:
        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True) # Spacer
        if st.button("⚙️ 系统配置", help="打开系统设置", use_container_width=True):
            render_settings_dialog()
    
    # 获取调试模式状态 (从 session)
    debug_mode = st.session_state.get('debug_mode', False)
    
    # 渲染主页面（Tab 切换）
    tab1, tab2 = st.tabs(["媒体库", "任务队列"])
    
    with tab1:
        render_media_library_page(debug_mode)
    
    with tab2:
        render_task_queue_page()


# ============================================================================
# 入口点
# ============================================================================

if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs("./data/models", exist_ok=True)
    
    # 初始化数据库
    init_database()
    
    # 启动后台工作器（仅启动一次）
    if 'worker_started' not in st.session_state:
        print("[Main] Starting worker thread...")
        start_worker()
        st.session_state.worker_started = True
        print("[Main] Worker thread started")
    
    # 运行主程序
    main()