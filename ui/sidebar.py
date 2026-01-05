#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
侧边栏配置 UI
负责渲染所有配置选项
"""

from typing import Tuple, List, Optional
import streamlit as st
import requests

from core.config import (
    ConfigManager,
    LLM_PROVIDERS,
    get_content_type_display_name,
    get_content_type_description
)
from core.models import ContentType, ISO_LANG_MAP, TARGET_LANG_OPTIONS
from database.connection import get_db_connection


def test_api_connection(api_key: str, base_url: str, model: str) -> Tuple[bool, str]:
    """测试 API 连接"""
    try:
        from services.translator import TranslationConfig, SubtitleTranslator, SubtitleEntry
        
        config = TranslationConfig(
            api_key=api_key,
            base_url=base_url,
            model_name=model,
            target_language='zh'
        )
        translator = SubtitleTranslator(config)
        
        # 简单测试：翻译一条假字幕
        test_entry = SubtitleEntry("1", "00:00:00,000 --> 00:00:01,000", "Hello")
        translator._translate_batch([test_entry])
        
        return True, "连接成功"
    except Exception as e:
        return False, str(e)


def fetch_ollama_models(base_url: str) -> List[str]:
    """获取 Ollama 模型列表"""
    try:
        root_url = base_url.replace("/v1", "").rstrip("/")
        resp = requests.get(f"{root_url}/api/tags", timeout=2.0)
        if resp.status_code == 200:
            return [m['name'] for m in resp.json().get('models', [])]
    except Exception as e:
        print(f"[Sidebar] Failed to fetch Ollama models: {e}")
    return []


def render_whisper_settings(config_manager: ConfigManager) -> dict:
    """渲染 Whisper 设置"""
    config = config_manager.load()
    changes = {}
    
    with st.expander("Whisper 设置", expanded=False):
        # 内容类型选择
        content_type_options = {ct: get_content_type_display_name(ct) for ct in ContentType}
        content_type_keys = list(content_type_options.keys())
        
        current_index = content_type_keys.index(config.content_type) \
            if config.content_type in content_type_keys else 0
        
        content_type = st.selectbox(
            "内容类型",
            content_type_keys,
            format_func=lambda x: content_type_options[x],
            index=current_index,
            help="选择内容类型以自动优化 VAD 参数"
        )
        changes['content_type'] = content_type
        
        # 显示当前选择的说明
        if content_type:
            st.caption(f"💡 {get_content_type_description(content_type)}")
        
        # 显示当前 VAD 参数
        from core.config import AppConfig
        temp_config = AppConfig(content_type=content_type)
        vad = temp_config.get_vad_parameters()
        
        with st.expander("📊 当前 VAD 参数（自动）", expanded=False):
            st.caption(f"阈值: {vad.threshold}")
            st.caption(f"最小语音时长: {vad.min_speech_duration_ms}ms")
            st.caption(f"最小静音时长: {vad.min_silence_duration_ms}ms")
            st.caption(f"语音填充: {vad.speech_pad_ms}ms")
        
        st.divider()
        
        # Whisper 模型设置
        model_sizes = ["tiny", "base", "small", "medium", "large-v3"]
        model_size = st.selectbox(
            "模型大小",
            model_sizes,
            index=model_sizes.index(config.whisper.model_size)
        )
        changes['whisper_model'] = model_size
        
        compute_types = ["int8", "float16"]
        compute_type = st.selectbox(
            "计算类型",
            compute_types,
            index=compute_types.index(config.whisper.compute_type)
        )
        changes['compute_type'] = compute_type
        
        devices = ["cpu", "cuda"]
        device = st.selectbox(
            "设备",
            devices,
            index=devices.index(config.whisper.device)
        )
        changes['device'] = device
        
        # 源语言
        lang_keys = list(ISO_LANG_MAP.keys())
        source_language = st.selectbox(
            "视频原声",
            lang_keys,
            format_func=lambda x: ISO_LANG_MAP[x],
            index=lang_keys.index(config.whisper.source_language)
        )
        changes['source_language'] = source_language
        
        st.divider()
        
        # 导出格式选择
        st.caption("🎬 导出格式")
        format_options = ['srt', 'vtt', 'ass', 'ssa', 'sub']
        selected_formats = []
        
        col1, col2 = st.columns(2)
        with col1:
            if st.checkbox('SRT', value='srt' in config.export.formats, key='fmt_srt'):
                selected_formats.append('srt')
            if st.checkbox('VTT', value='vtt' in config.export.formats, key='fmt_vtt'):
                selected_formats.append('vtt')
            if st.checkbox('ASS', value='ass' in config.export.formats, key='fmt_ass'):
                selected_formats.append('ass')
        with col2:
            if st.checkbox('SSA', value='ssa' in config.export.formats, key='fmt_ssa'):
                selected_formats.append('ssa')
            if st.checkbox('SUB', value='sub' in config.export.formats, key='fmt_sub'):
                selected_formats.append('sub')
        
        if not selected_formats:
            st.warning("⚠️ 至少选择一种格式")
            selected_formats = ['srt']
        
        changes['export_formats'] = selected_formats
        
        with st.expander("ℹ️ 格式说明", expanded=False):
            st.caption("**SRT**: 最通用，几乎所有播放器支持")
            st.caption("**VTT**: Web/HTML5 播放器专用")
            st.caption("**ASS**: 支持丰富样式，动漫字幕常用")
            st.caption("**SSA**: ASS 的前身，兼容性更好")
            st.caption("**SUB**: 老式 DVD 播放器支持")
    
    return changes


def render_translation_settings(config_manager: ConfigManager) -> Tuple[dict, bool]:
    """
    渲染翻译设置
    Returns:
        tuple: (配置变更字典, 用户是否点击了保存按钮)
    """
    config = config_manager.load()
    changes = {}
    should_save = False
    
    with st.expander("翻译设置", expanded=True):
        enable_translation = st.checkbox(
            "启用翻译",
            value=config.translation.enabled
        )
        changes['enable_translation'] = enable_translation
        
        target_lang = st.selectbox(
            "目标语言",
            TARGET_LANG_OPTIONS,
            format_func=lambda x: ISO_LANG_MAP.get(x, x),
            index=TARGET_LANG_OPTIONS.index(config.translation.target_language)
        )
        changes['target_language'] = target_lang
        
        # 分批大小配置
        max_lines = st.number_input(
            "每批最多翻译行数",
            min_value=100,
            max_value=2000,
            value=config.translation.max_lines_per_batch,
            step=100,
            help="短视频会一次性翻译，长视频会按此数量分批"
        )
        changes['max_lines_per_batch'] = max_lines
        
        # 回调函数确保提供商切换立即生效
        def on_provider_change():
            st.session_state.provider_changed = True
        
        provider_keys = list(LLM_PROVIDERS.keys())
        default_index = provider_keys.index(config.current_provider) \
            if config.current_provider in LLM_PROVIDERS else 0
        
        provider = st.selectbox(
            "AI 提供商",
            provider_keys,
            index=default_index,
            key="provider_selector",
            on_change=on_provider_change
        )
        changes['provider'] = provider
        
        # 获取当前选择的提供商配置
        provider_cfg = config.provider_configs.get(provider)
        if not provider_cfg:
            default = LLM_PROVIDERS.get(provider, {})
            from core.models import ProviderConfig
            provider_cfg = ProviderConfig(
                api_key='',
                base_url=default.get('base_url', ''),
                model_name=default.get('model', '')
            )
        
        # 清除提供商变化标记
        if 'provider_changed' in st.session_state:
            del st.session_state.provider_changed
        
        # 提供商配置
        base_url = st.text_input(
            "Base URL",
            value=provider_cfg.base_url,
            help=f"当前提供商: {provider}",
            key=f"base_url_{provider}"
        )
        changes['base_url'] = base_url
        
        # Ollama 特殊处理
        if "Ollama" in provider:
            ollama_models = fetch_ollama_models(base_url)
            if ollama_models:
                try:
                    idx = ollama_models.index(provider_cfg.model_name)
                except ValueError:
                    idx = 0
                model_name = st.selectbox(
                    "选择模型", 
                    ollama_models, 
                    index=idx,
                    key=f"model_{provider}"
                )
                if st.button("刷新模型列表", use_container_width=True, key=f"refresh_{provider}"):
                    st.rerun()
            else:
                st.error("未检测到本地模型,请检查 Ollama 服务")
                model_name = st.text_input(
                    "手动输入模型", 
                    value=provider_cfg.model_name,
                    key=f"model_manual_{provider}"
                )
                if st.button("重试连接", use_container_width=True, key=f"retry_{provider}"):
                    st.rerun()
            api_key = ""
        else:
            api_key = st.text_input(
                "API Key",
                value=provider_cfg.api_key,
                type="password",
                help="该 Key 仅保存给当前提供商",
                key=f"api_key_{provider}"
            )
            model_name = st.text_input(
                "模型名称", 
                value=provider_cfg.model_name,
                key=f"model_{provider}"
            )
        
        changes['api_key'] = api_key
        changes['model_name'] = model_name
        
        # 测试和保存按钮
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            if st.button("测试", use_container_width=True):
                with st.spinner("连接中..."):
                    ok, msg = test_api_connection(api_key, base_url, model_name)
                    if ok:
                        st.toast("✅ 连接成功")
                    else:
                        st.error(f"❌ {msg}")
        
        with col_t2:
            # 修改：仅当用户点击时 should_save 置为 True
            if st.button("保存", type="primary", use_container_width=True):
                should_save = True
    
    return changes, should_save


def render_sidebar() -> bool:
    """渲染侧边栏（主函数）"""
    with st.sidebar:
        st.caption("参数配置")
        
        # 调试模式开关
        debug_mode = st.toggle("调试日志", value=False)
        
        # 配置管理器
        config_manager = ConfigManager(get_db_connection)
        
        # 渲染 Whisper 设置
        whisper_changes = render_whisper_settings(config_manager)
        
        # 渲染翻译设置
        # 修改：接收是否保存的标志位
        translation_changes, should_save = render_translation_settings(config_manager)
        
        # 修改：只有明确点击了保存按钮，且包含提供商信息时，才执行保存
        if should_save and 'provider' in translation_changes:
            _save_all_settings(config_manager, whisper_changes, translation_changes)
    
    return debug_mode


def _save_all_settings(
    config_manager: ConfigManager,
    whisper_changes: dict,
    translation_changes: dict
):
    """保存所有设置"""
    config = config_manager.load()
    
    # 更新 Whisper 配置
    config.whisper.model_size = whisper_changes['whisper_model']
    config.whisper.compute_type = whisper_changes['compute_type']
    config.whisper.device = whisper_changes['device']
    config.whisper.source_language = whisper_changes['source_language']
    config.content_type = whisper_changes['content_type']
    config.export.formats = whisper_changes['export_formats']
    
    # 更新翻译配置
    config.translation.enabled = translation_changes['enable_translation']
    config.translation.target_language = translation_changes['target_language']
    config.translation.max_lines_per_batch = translation_changes['max_lines_per_batch']
    
    # 更新提供商配置
    config.update_provider_config(
        translation_changes['provider'],
        translation_changes['api_key'],
        translation_changes['base_url'],
        translation_changes['model_name']
    )
    
    # 保存到数据库
    # 修改：检查 save 方法的返回值 (需要在 core/config.py 中同步修改 save 方法返回 bool)
    if config_manager.save(config):
        formats_str = ', '.join([f.upper() for f in whisper_changes['export_formats']])
        st.toast(f"✅ 已保存配置（导出: {formats_str}）")
    # 如果 save 返回 False (配置未变更)，则不弹窗