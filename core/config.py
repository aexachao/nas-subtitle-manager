#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责应用配置的加载、保存和验证
"""

import json
import copy  # ✅ 新增：用于深拷贝配置字典
from typing import Dict, Optional
from dataclasses import dataclass, field, asdict

from core.models import (
    ContentType,
    ProviderConfig,
    WhisperConfig,
    TranslationConfig,
    ExportConfig,
    VADParameters
)


# ============================================================================
# VAD 参数预设
# ============================================================================

VAD_PRESETS = {
    ContentType.MOVIE: VADParameters(
        threshold=0.5,
        min_speech_duration_ms=250,
        min_silence_duration_ms=2000,
        speech_pad_ms=400
    ),
    ContentType.DOCUMENTARY: VADParameters(
        threshold=0.45,
        min_speech_duration_ms=300,
        min_silence_duration_ms=1800,
        speech_pad_ms=500
    ),
    ContentType.VARIETY: VADParameters(
        threshold=0.6,
        min_speech_duration_ms=200,
        min_silence_duration_ms=2500,
        speech_pad_ms=300
    ),
    ContentType.ANIMATION: VADParameters(
        threshold=0.4,
        min_speech_duration_ms=150,
        min_silence_duration_ms=1500,
        speech_pad_ms=350
    ),
    ContentType.LECTURE: VADParameters(
        threshold=0.5,
        min_speech_duration_ms=400,
        min_silence_duration_ms=2500,
        speech_pad_ms=600
    ),
    ContentType.MUSIC: VADParameters(
        threshold=0.7,
        min_speech_duration_ms=500,
        min_silence_duration_ms=3000,
        speech_pad_ms=200
    ),
    ContentType.CUSTOM: VADParameters(
        threshold=0.5,
        min_speech_duration_ms=250,
        min_silence_duration_ms=2000,
        speech_pad_ms=400
    )
}

# 内容类型描述
CONTENT_TYPE_DESCRIPTIONS = {
    ContentType.MOVIE: '标准配置，适合电影、电视剧等有明确对话的影视内容。时间轴精准度高。',
    ContentType.DOCUMENTARY: '优化旁白识别，减少背景音乐干扰。适合纪录片、新闻、访谈节目。',
    ContentType.VARIETY: '高阈值过滤笑声、掌声、背景音。适合综艺节目、脱口秀、多人访谈。',
    ContentType.ANIMATION: '适配较快语速，减少卡顿。适合日本动漫、卡通片等快节奏内容。',
    ContentType.LECTURE: '注重完整语句识别，增加停顿缓冲。适合教学视频、演讲、培训课程。',
    ContentType.MUSIC: '极高阈值仅提取人声，忽略背景音乐。适合 MV、音乐会、歌唱节目。',
    ContentType.CUSTOM: '默认配置，也可以手动调整 VAD 参数以满足特殊需求。'
}


# ============================================================================
# LLM 提供商配置
# ============================================================================

LLM_PROVIDERS = {
    "Ollama (本地模型)": {
        "base_url": "http://ollama:11434/v1",
        "model": "qwen2.5:7b",
        "help": "无需联网，使用本地算力"
    },
    "DeepSeek (深度求索)": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "help": "国内推荐"
    },
    "Google Gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-1.5-flash",
        "help": "速度极快"
    },
    "Moonshot (Kimi)": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
        "help": "长文本优化"
    },
    "Aliyun (通义千问)": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-turbo",
        "help": "阿里官方"
    },
    "ZhipuAI (智谱GLM)": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
        "help": "智谱清言"
    },
    "OpenAI (官方)": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "help": "需科学上网"
    },
    "自定义 (Custom)": {
        "base_url": "",
        "model": "",
        "help": "手动填写"
    }
}


# ============================================================================
# 应用配置类
# ============================================================================

@dataclass
class AppConfig:
    """应用配置（主配置类）"""
    
    # Whisper 配置
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    
    # 翻译配置
    translation: TranslationConfig = field(default_factory=TranslationConfig)
    
    # 导出配置
    export: ExportConfig = field(default_factory=ExportConfig)
    
    # 内容类型
    content_type: ContentType = ContentType.MOVIE
    
    # 当前使用的 LLM 提供商
    current_provider: str = 'Ollama (本地模型)'
    
    # 各提供商的配置
    provider_configs: Dict[str, ProviderConfig] = field(default_factory=dict)
    
    def get_vad_parameters(self) -> VADParameters:
        """获取当前内容类型的 VAD 参数"""
        return VAD_PRESETS.get(self.content_type, VAD_PRESETS[ContentType.MOVIE])
    
    def get_current_provider_config(self) -> ProviderConfig:
        """获取当前提供商的配置"""
        if self.current_provider not in self.provider_configs:
            default = LLM_PROVIDERS.get(self.current_provider, {})
            return ProviderConfig(
                api_key='',
                base_url=default.get('base_url', ''),
                model_name=default.get('model', '')
            )
        return self.provider_configs[self.current_provider]
    
    def update_provider_config(
        self, 
        provider: str, 
        api_key: str, 
        base_url: str, 
        model_name: str
    ):
        """更新指定提供商的配置"""
        self.provider_configs[provider] = ProviderConfig(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name
        )
        self.current_provider = provider
    
    def to_dict(self) -> Dict:
        """转换为字典（用于序列化）"""
        return {
            'whisper': self.whisper.to_dict(),
            'translation': self.translation.to_dict(),
            'export': self.export.to_dict(),
            'content_type': self.content_type.value if isinstance(self.content_type, ContentType) else self.content_type,
            'current_provider': self.current_provider,
            'provider_configs': {
                k: v.to_dict() for k, v in self.provider_configs.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AppConfig':
        """从字典创建配置对象"""
        # 解析 Whisper 配置
        whisper_data = data.get('whisper', {})
        whisper = WhisperConfig(**whisper_data)
        
        # 解析翻译配置
        translation_data = data.get('translation', {})
        translation = TranslationConfig(**translation_data)
        
        # 解析导出配置
        export_data = data.get('export', {'formats': ['srt']})
        export = ExportConfig.from_dict(export_data)
        
        # 解析内容类型
        content_type_str = data.get('content_type', 'movie')
        try:
            content_type = ContentType(content_type_str)
        except ValueError:
            content_type = ContentType.MOVIE
        
        # 解析提供商配置
        provider_configs_data = data.get('provider_configs', {})
        provider_configs = {
            k: ProviderConfig.from_dict(v) 
            for k, v in provider_configs_data.items()
        }
        
        return cls(
            whisper=whisper,
            translation=translation,
            export=export,
            content_type=content_type,
            current_provider=data.get('current_provider', 'Ollama (本地模型)'),
            provider_configs=provider_configs
        )


# ============================================================================
# 配置持久化（与数据库交互）
# ============================================================================

class ConfigManager:
    """配置管理器（负责配置的加载和保存）"""
    
    def __init__(self, db_connection):
        """
        初始化配置管理器
        
        Args:
            db_connection: 数据库连接工厂函数
        """
        self.get_db = db_connection
        self._last_saved_config_dict = {}  # ✅ 新增：缓存上一次保存或加载的配置
    
    def load(self) -> AppConfig:
        """从数据库加载配置"""
        conn = self.get_db()
        try:
            cursor = conn.execute("SELECT key, value FROM config")
            config_dict = {row[0]: row[1] for row in cursor.fetchall()}
            
            if not config_dict:
                # ✅ 修改：初始化默认配置时也记录缓存
                default_config = AppConfig()
                self._last_saved_config_dict = default_config.to_dict()
                return default_config
            
            # 构建嵌套配置字典
            data = {
                'whisper': {
                    'model_size': config_dict.get('whisper_model', 'base'),
                    'compute_type': config_dict.get('compute_type', 'int8'),
                    'device': config_dict.get('device', 'cpu'),
                    'source_language': config_dict.get('source_language', 'auto')
                },
                'translation': {
                    'enabled': config_dict.get('enable_translation', 'false') == 'true',
                    'target_language': config_dict.get('target_language', 'zh'),
                    'max_lines_per_batch': int(config_dict.get('max_lines_per_batch', 500))
                },
                'export': json.loads(config_dict.get('export_formats', '{"formats": ["srt"]}')),
                'content_type': config_dict.get('content_type', 'movie'),
                'current_provider': config_dict.get('current_provider', 'Ollama (本地模型)'),
                'provider_configs': json.loads(config_dict.get('provider_configs', '{}'))
            }
            
            # ✅ 修改：加载完成后更新缓存
            loaded_config = AppConfig.from_dict(data)
            self._last_saved_config_dict = loaded_config.to_dict()
            return loaded_config
            
        finally:
            conn.close()
    
    def save(self, config: AppConfig) -> bool:
        """
        保存配置到数据库
        
        Returns:
            bool: True 表示实际执行了保存，False 表示未变更无需保存
        """
        # ✅ 新增：获取新配置的字典形式并比对
        new_config_dict = config.to_dict()
        
        if new_config_dict == self._last_saved_config_dict:
            # 如果配置内容完全一致，跳过数据库操作
            return False

        conn = self.get_db()
        try:
            # 扁平化配置
            flat_config = {
                'whisper_model': config.whisper.model_size,
                'compute_type': config.whisper.compute_type,
                'device': config.whisper.device,
                'source_language': config.whisper.source_language,
                'enable_translation': 'true' if config.translation.enabled else 'false',
                'target_language': config.translation.target_language,
                'max_lines_per_batch': str(config.translation.max_lines_per_batch),
                'export_formats': json.dumps(config.export.to_dict(), ensure_ascii=False),
                'content_type': config.content_type.value if isinstance(config.content_type, ContentType) else config.content_type,
                'current_provider': config.current_provider,
                'provider_configs': json.dumps(
                    {k: v.to_dict() for k, v in config.provider_configs.items()},
                    ensure_ascii=False
                )
            }
            
            for key, value in flat_config.items():
                conn.execute(
                    "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                    (key, str(value))
                )
            
            conn.commit()
            
            # ✅ 新增：保存成功后更新缓存
            self._last_saved_config_dict = copy.deepcopy(new_config_dict)
            return True
            
        except Exception as e:
            print(f"Failed to save config: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()


# ============================================================================
# 辅助函数
# ============================================================================

def get_content_type_display_name(content_type: ContentType) -> str:
    """获取内容类型的显示名称"""
    display_names = {
        ContentType.MOVIE: '🎬 电影/剧集（标准）',
        ContentType.DOCUMENTARY: '📺 纪录片/新闻',
        ContentType.VARIETY: '🎤 综艺/访谈',
        ContentType.ANIMATION: '🎨 动画/动漫',
        ContentType.LECTURE: '🎓 讲座/课程',
        ContentType.MUSIC: '🎵 音乐视频/MV',
        ContentType.CUSTOM: '⚙️ 自定义'
    }
    return display_names.get(content_type, content_type.value)


def get_content_type_description(content_type: ContentType) -> str:
    """获取内容类型的详细描述"""
    return CONTENT_TYPE_DESCRIPTIONS.get(
        content_type, 
        '默认配置'
    )