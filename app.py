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
from database.connection import init_database
from core.worker import start_worker
from ui.sidebar import render_sidebar
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
        page_icon="🎬",
        layout="wide"
    )
    
    # 应用样式
    st.markdown(HERO_CSS, unsafe_allow_html=True)
    
    # 页面标题
    st.markdown(
        "<h1 style='margin-bottom: 24px;'>NAS 字幕管家</h1>",
        unsafe_allow_html=True
    )
    
    # 渲染侧边栏（获取调试模式）
    debug_mode = render_sidebar()
    
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
    os.makedirs("/data/models", exist_ok=True)
    
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