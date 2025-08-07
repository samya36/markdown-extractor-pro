"""
通用视频字幕下载器 - 配置文件
支持所有主要视频平台，多语言，多格式字幕下载
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class SubtitleConfig:
    """字幕配置类"""
    
    # 支持的输出格式
    SUPPORTED_FORMATS = [
        'srt',      # SubRip字幕
        'vtt',      # WebVTT字幕
        'ass',      # Advanced SubStation Alpha
        'ssa',      # SubStation Alpha
        'txt',      # 纯文本
        'json',     # JSON格式（包含时间戳）
        'csv',      # CSV格式
        'xml',      # XML格式
        'ttml',     # Timed Text Markup Language
        'dfxp',     # Distribution Format Exchange Profile
    ]
    
    # 支持的语言代码（ISO 639-1/639-2）
    SUPPORTED_LANGUAGES = {
        # 主要语言
        'zh-CN': '简体中文',
        'zh-TW': '繁体中文', 
        'zh': '中文',
        'en': '英语',
        'ja': '日语',
        'ko': '韩语',
        'es': '西班牙语',
        'fr': '法语',
        'de': '德语',
        'ru': '俄语',
        'pt': '葡萄牙语',
        'it': '意大利语',
        'ar': '阿拉伯语',
        'hi': '印地语',
        'th': '泰语',
        'vi': '越南语',
        'id': '印尼语',
        'ms': '马来语',
        'tr': '土耳其语',
        'pl': '波兰语',
        'nl': '荷兰语',
        'sv': '瑞典语',
        'no': '挪威语',
        'da': '丹麦语',
        'fi': '芬兰语',
        'he': '希伯来语',
        'cs': '捷克语',
        'hu': '匈牙利语',
        'ro': '罗马尼亚语',
        'bg': '保加利亚语',
        'hr': '克罗地亚语',
        'sr': '塞尔维亚语',
        'sl': '斯洛文尼亚语',
        'sk': '斯洛伐克语',
        'lt': '立陶宛语',
        'lv': '拉脱维亚语',
        'et': '爱沙尼亚语',
        'uk': '乌克兰语',
        'be': '白俄罗斯语',
        'mk': '马其顿语',
        'sq': '阿尔巴尼亚语',
        'mt': '马耳他语',
        'ga': '爱尔兰语',
        'is': '冰岛语',
        'ca': '加泰罗尼亚语',
        'eu': '巴斯克语',
        'gl': '加利西亚语',
        'cy': '威尔士语',
        'fa': '波斯语',
        'ur': '乌尔都语',
        'bn': '孟加拉语',
        'ta': '泰米尔语',
        'te': '泰卢固语',
        'ml': '马拉雅拉姆语',
        'kn': '卡纳达语',
        'gu': '古吉拉特语',
        'pa': '旁遮普语',
        'or': '奥里雅语',
        'as': '阿萨姆语',
        'ne': '尼泊尔语',
        'si': '僧伽罗语',
        'my': '缅甸语',
        'km': '高棉语',
        'lo': '老挝语',
        'ka': '格鲁吉亚语',
        'am': '阿姆哈拉语',
        'sw': '斯瓦希里语',
        'zu': '祖鲁语',
        'af': '南非荷兰语',
        'xh': '科萨语',
    }
    
    # AI模型配置
    WHISPER_MODELS = {
        'tiny': {'size': '39MB', 'speed': '32x', 'accuracy': '低'},
        'base': {'size': '74MB', 'speed': '16x', 'accuracy': '中'},
        'small': {'size': '244MB', 'speed': '6x', 'accuracy': '中高'},
        'medium': {'size': '769MB', 'speed': '2x', 'accuracy': '高'},
        'large': {'size': '1550MB', 'speed': '1x', 'accuracy': '最高'},
        'large-v2': {'size': '1550MB', 'speed': '1x', 'accuracy': '最高+'},
        'large-v3': {'size': '1550MB', 'speed': '1x', 'accuracy': '最高++'},
    }
    
    # 平台配置
    PLATFORM_CONFIGS = {
        'youtube': {
            'name': 'YouTube',
            'domains': ['youtube.com', 'youtu.be', 'm.youtube.com'],
            'subtitle_formats': ['vtt', 'srv3', 'srv2', 'srv1', 'ttml'],
            'auto_captions': True,
            'manual_captions': True,
            'live_captions': True,
        },
        'bilibili': {
            'name': '哔哩哔哩',
            'domains': ['bilibili.com', 'b23.tv'],
            'subtitle_formats': ['srt', 'ass'],
            'auto_captions': True,
            'manual_captions': True,
            'live_captions': False,
        },
        'twitter': {
            'name': 'Twitter/X',
            'domains': ['twitter.com', 'x.com', 't.co'],
            'subtitle_formats': ['vtt'],
            'auto_captions': False,
            'manual_captions': False,
            'live_captions': False,
        },
        'facebook': {
            'name': 'Facebook',
            'domains': ['facebook.com', 'fb.watch'],
            'subtitle_formats': ['vtt'],
            'auto_captions': True,
            'manual_captions': False,
            'live_captions': False,
        },
        'instagram': {
            'name': 'Instagram',
            'domains': ['instagram.com'],
            'subtitle_formats': ['vtt'],
            'auto_captions': False,
            'manual_captions': False,
            'live_captions': False,
        },
        'tiktok': {
            'name': 'TikTok',
            'domains': ['tiktok.com'],
            'subtitle_formats': ['vtt'],
            'auto_captions': True,
            'manual_captions': False,
            'live_captions': False,
        },
        'vimeo': {
            'name': 'Vimeo',
            'domains': ['vimeo.com'],
            'subtitle_formats': ['vtt', 'srt'],
            'auto_captions': False,
            'manual_captions': True,
            'live_captions': False,
        },
        'dailymotion': {
            'name': 'Dailymotion',
            'domains': ['dailymotion.com'],
            'subtitle_formats': ['vtt', 'srt'],
            'auto_captions': False,
            'manual_captions': True,
            'live_captions': False,
        },
        'twitch': {
            'name': 'Twitch',
            'domains': ['twitch.tv'],
            'subtitle_formats': ['vtt'],
            'auto_captions': False,
            'manual_captions': False,
            'live_captions': True,
        },
        'generic': {
            'name': '通用平台',
            'domains': ['*'],
            'subtitle_formats': ['vtt', 'srt', 'ass'],
            'auto_captions': False,
            'manual_captions': False,
            'live_captions': False,
        }
    }

@dataclass
class AppConfig:
    """应用配置类"""
    
    # 应用信息
    APP_NAME = "Universal Subtitle Downloader"
    VERSION = "3.0.0"
    DESCRIPTION = "完整的多平台视频字幕下载器"
    
    # 目录配置
    BASE_DIR = Path(__file__).parent.parent
    DOWNLOAD_DIR = BASE_DIR / "downloads"
    CACHE_DIR = BASE_DIR / "cache"
    LOGS_DIR = BASE_DIR / "logs"
    MODELS_DIR = BASE_DIR / "models"
    
    # 网络配置
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    CHUNK_SIZE = 8192
    
    # 并发配置
    MAX_CONCURRENT_DOWNLOADS = 5
    MAX_CONCURRENT_AI_TASKS = 2
    
    # 代理配置
    PROXY_TIMEOUT = 10
    PROXY_CHECK_URL = "https://httpbin.org/ip"
    
    # AI配置
    DEFAULT_WHISPER_MODEL = "base"
    WHISPER_DEVICE = "auto"  # "cpu", "cuda", "auto"
    
    # 字幕配置
    SUBTITLE_QUALITY_THRESHOLD = 0.8  # 字幕质量阈值
    MAX_SUBTITLE_LENGTH = 100  # 每行最大字符数
    MIN_SUBTITLE_DURATION = 0.5  # 最小字幕显示时间(秒)
    
    # 翻译配置
    ENABLE_TRANSLATION = True
    TRANSLATION_SERVICES = ["google", "bing", "yandex"]
    
    def __post_init__(self):
        """初始化后创建必要目录"""
        for directory in [self.DOWNLOAD_DIR, self.CACHE_DIR, self.LOGS_DIR, self.MODELS_DIR]:
            directory.mkdir(exist_ok=True, parents=True)

# 全局配置实例
subtitle_config = SubtitleConfig()
app_config = AppConfig()

# 环境变量配置
class EnvConfig:
    """环境变量配置"""
    
    # API密钥
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY")
    BING_TRANSLATE_API_KEY = os.getenv("BING_TRANSLATE_API_KEY")
    
    # 代理设置
    HTTP_PROXY = os.getenv("HTTP_PROXY")
    HTTPS_PROXY = os.getenv("HTTPS_PROXY")
    SOCKS_PROXY = os.getenv("SOCKS_PROXY")
    
    # 数据库配置（可选）
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///subtitles.db")
    
    # 调试模式
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # 日志级别
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

env_config = EnvConfig()

# User-Agent池
USER_AGENTS = [
    # Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    
    # Opera
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
]

# 常用的视频质量标识符
VIDEO_QUALITIES = {
    'best': '最佳质量',
    'worst': '最低质量', 
    'bestvideo': '最佳视频',
    'worstvideo': '最低视频',
    'bestaudio': '最佳音频',
    'worstaudio': '最低音频',
    '2160p': '4K (2160p)',
    '1440p': '2K (1440p)',
    '1080p': 'Full HD (1080p)',
    '720p': 'HD (720p)',
    '480p': 'SD (480p)',
    '360p': '360p',
    '240p': '240p',
    '144p': '144p',
}

# MIME类型映射
MIME_TYPES = {
    'srt': 'text/plain',
    'vtt': 'text/vtt',
    'ass': 'text/plain',
    'ssa': 'text/plain',
    'txt': 'text/plain',
    'json': 'application/json',
    'csv': 'text/csv',
    'xml': 'application/xml',
    'ttml': 'application/ttml+xml',
    'dfxp': 'application/ttaf+xml',
}