"""
通用视频字幕下载器
Universal Subtitle Downloader

支持多平台视频字幕下载和AI字幕生成的完整解决方案
"""

__version__ = "3.0.0"
__author__ = "Universal Subtitle Downloader Team"
__description__ = "Complete multi-platform video subtitle downloader with AI generation"

# 主要组件导入
from .universal_downloader import (
    UniversalSubtitleDownloader,
    DownloadRequest,
    DownloadResult
)

from .ai_generator import (
    AISubtitleGenerator,
    TranscriptionResult
)

from .format_converter import SubtitleFormatConverter

# 提取器导入
from .extractors.base_extractor import (
    BaseSubtitleExtractor,
    SubtitleSegment,
    SubtitleTrack,
    VideoInfo
)

from .extractors.youtube_extractor import YouTubeSubtitleExtractor
from .extractors.bilibili_extractor import BilibiliSubtitleExtractor
from .extractors.generic_extractor import GenericSubtitleExtractor

# 配置导入
from .config import (
    subtitle_config,
    app_config,
    env_config
)

__all__ = [
    # 主要类
    'UniversalSubtitleDownloader',
    'DownloadRequest',
    'DownloadResult',
    'AISubtitleGenerator',
    'TranscriptionResult',
    'SubtitleFormatConverter',
    
    # 提取器类
    'BaseSubtitleExtractor',
    'YouTubeSubtitleExtractor',
    'BilibiliSubtitleExtractor',
    'GenericSubtitleExtractor',
    
    # 数据结构
    'SubtitleSegment',
    'SubtitleTrack',
    'VideoInfo',
    
    # 配置
    'subtitle_config',
    'app_config',
    'env_config',
]

def get_version():
    """获取版本信息"""
    return __version__

def get_supported_platforms():
    """获取支持的平台列表"""
    return list(subtitle_config.PLATFORM_CONFIGS.keys())

def get_supported_formats():
    """获取支持的字幕格式列表"""
    return subtitle_config.SUPPORTED_FORMATS.copy()

def get_supported_languages():
    """获取支持的语言列表"""
    return subtitle_config.SUPPORTED_LANGUAGES.copy()