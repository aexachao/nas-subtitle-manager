#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 样式定义
集中管理所有 CSS 样式
"""

HERO_CSS = """
<style>
    .stApp {
        background-color: #09090b;
        color: #e4e4e7;
    }
    
    h1 { font-size: 32px !important; font-weight: 700 !important; padding-bottom: 0.5rem; }
    h2, h3 { font-size: 16px !important; font-weight: 600 !important; }
    
    section[data-testid="stSidebar"] {
        background-color: #111114;
        border-right: 1px solid #27272a;
    }

    .hero-card {
        background-color: #18181b;
        border: 1px solid #27272a;
        border-radius: 6px;
        padding: 12px 16px;
        transition: border-color 0.2s;
        margin-bottom: 16px;
    }
    .hero-card:hover {
        border-color: #3f3f46;
    }
    
    .status-chip {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 500;
        margin-right: 6px;
    }
    .chip-gray { background: #27272a; color: #a1a1aa; border: 1px solid #3f3f46; }
    .chip-blue { background: #172554; color: #60a5fa; border: 1px solid #1e3a8a; }
    .chip-green { background: #064e3b; color: #34d399; border: 1px solid #065f46; }
    .chip-red { background: #450a0a; color: #f87171; border: 1px solid #7f1d1d; }

    .stButton button {
        background-color: transparent !important;
        border: 1px solid #3f3f46 !important;
        color: #d4d4d8 !important;
        border-radius: 6px !important;
        font-size: 13px !important;
        height: 32px !important;
        padding: 0 12px !important;
    }
    .stButton button:hover {
        border-color: #71717a !important;
        background-color: #27272a !important;
        color: #fff !important;
    }
    
    div[data-testid="stVerticalBlock"] button[kind="primary"] {
        background-color: #2563eb !important;
        border: 1px solid #2563eb !important;
        color: white !important;
    }
    div[data-testid="stVerticalBlock"] button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
    }

    .stProgress > div > div > div > div { background-color: #2563eb; }
    
    div[data-testid="stCheckbox"] label {
        min-height: 0px !important;
        margin-bottom: 0px !important;
    }
    
    .task-card-wrapper {
        position: relative;
        margin-bottom: 24px;
    }
    
    .task-card-wrapper + div[data-testid="column"] {
        margin-top: -48px !important;
        margin-bottom: 12px !important;
        padding-right: 16px !important;
    }
</style>
"""