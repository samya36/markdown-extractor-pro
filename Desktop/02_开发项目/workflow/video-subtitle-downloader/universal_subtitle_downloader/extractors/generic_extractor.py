"""
通用字幕提取器
支持使用yt-dlp的任何平台
"""

import re
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, parse_qs
import aiohttp
import yt_dlp
from .base_extractor import BaseSubtitleExtractor, SubtitleTrack, SubtitleSegment, VideoInfo
from ..config import subtitle_config, app_config, USER_AGENTS
import random

logger = logging.getLogger(__name__)

class GenericSubtitleExtractor(BaseSubtitleExtractor):
    """通用字幕提取器，支持yt-dlp支持的所有平台"""
    
    def __init__(self, proxy_manager=None, session: aiohttp.ClientSession = None):
        super().__init__(proxy_manager, session)
        self.platform_name = "通用平台"
        
        # 通用配置，启用所有字幕相关选项
        self.ydl_opts.update({
            'writesubtitles': True,
            'writeautomaticsub': True,
            'allsubtitles': False,  # 我们手动选择语言
            'subtitlesformat': 'best',
            'ignoreerrors': True,  # 忽略错误继续处理
        })
    
    def can_handle(self, url: str) -> bool:
        """通用提取器可以处理任何URL，但优先级最低"""
        try:
            # 简单的URL验证
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False
    
    async def extract_video_info(self, url: str) -> VideoInfo:
        """提取视频信息"""
        try:
            self.logger.info(f"Extracting video info from: {url}")
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
            
            # 检测平台
            platform = self._detect_platform(url, info)
            
            video_info = VideoInfo(
                id=str(info.get('id', '')),
                title=info.get('title', 'Unknown'),
                duration=info.get('duration', 0),
                uploader=info.get('uploader', 'Unknown'),
                upload_date=info.get('upload_date', ''),
                view_count=info.get('view_count', 0),
                description=(info.get('description', '') or '')[:500],
                thumbnail=info.get('thumbnail', ''),
                webpage_url=info.get('webpage_url', url),
                platform=platform,
                available_subtitles=list(info.get('subtitles', {}).keys()),
                automatic_captions=list(info.get('automatic_captions', {}).keys()),
                formats_info=self._extract_formats_info(info)
            )
            
            self.logger.info(f"Extracted info for {platform}: {video_info.title}")
            return video_info
            
        except Exception as e:
            self.logger.error(f"Failed to extract video info: {str(e)}")
            raise Exception(f"视频信息提取失败: {str(e)}")
    
    async def extract_subtitles(self, url: str, languages: List[str] = None) -> List[SubtitleTrack]:
        """提取字幕"""
        try:
            if languages is None:
                languages = ['zh-CN', 'zh', 'en']
            
            self.logger.info(f"Extracting subtitles for languages: {languages}")
            
            # 获取字幕信息
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
            
            platform = self._detect_platform(url, info)
            subtitle_tracks = []
            
            # 1. 处理手动字幕（优先级更高）
            manual_subtitles = info.get('subtitles', {})
            for lang in languages:
                # 尝试精确匹配
                if lang in manual_subtitles:
                    tracks = await self._extract_subtitle_tracks(
                        manual_subtitles[lang], lang, False, platform
                    )
                    subtitle_tracks.extend(tracks)
                # 尝试语言变体匹配
                else:
                    for available_lang in manual_subtitles.keys():
                        if self._language_matches(available_lang, lang):
                            tracks = await self._extract_subtitle_tracks(
                                manual_subtitles[available_lang], available_lang, False, platform
                            )
                            subtitle_tracks.extend(tracks)
                            break
            
            # 2. 处理自动生成字幕
            auto_captions = info.get('automatic_captions', {})
            for lang in languages:
                # 只有在没有找到手动字幕时才使用自动字幕
                has_manual = any(track.language == lang and not track.is_auto_generated 
                               for track in subtitle_tracks)
                if has_manual:
                    continue
                
                # 尝试精确匹配
                if lang in auto_captions:
                    tracks = await self._extract_subtitle_tracks(
                        auto_captions[lang], lang, True, platform
                    )
                    subtitle_tracks.extend(tracks)
                # 尝试语言变体匹配
                else:
                    for available_lang in auto_captions.keys():
                        if self._language_matches(available_lang, lang):
                            tracks = await self._extract_subtitle_tracks(
                                auto_captions[available_lang], available_lang, True, platform
                            )
                            subtitle_tracks.extend(tracks)
                            break
            
            # 3. 如果没有找到任何字幕，尝试英语作为回退
            if not subtitle_tracks and 'en' not in languages:
                if 'en' in manual_subtitles:
                    tracks = await self._extract_subtitle_tracks(
                        manual_subtitles['en'], 'en', False, platform
                    )
                    subtitle_tracks.extend(tracks)
                elif 'en' in auto_captions:
                    tracks = await self._extract_subtitle_tracks(
                        auto_captions['en'], 'en', True, platform
                    )
                    subtitle_tracks.extend(tracks)
            
            self.logger.info(f"Found {len(subtitle_tracks)} subtitle tracks from {platform}")
            return subtitle_tracks
            
        except Exception as e:
            self.logger.error(f"Failed to extract subtitles: {str(e)}")
            raise Exception(f"字幕提取失败: {str(e)}")
    
    async def _extract_subtitle_tracks(
        self, 
        subtitle_formats: List[Dict], 
        language: str, 
        is_auto_generated: bool,
        platform: str
    ) -> List[SubtitleTrack]:
        """从字幕格式列表中提取字幕轨道"""
        tracks = []
        
        # 按格式优先级排序
        format_priority = ['vtt', 'srt', 'ttml', 'srv3', 'srv2', 'srv1', 'ass', 'ssa']
        sorted_formats = sorted(
            subtitle_formats,
            key=lambda x: format_priority.index(x.get('ext', 'unknown')) 
            if x.get('ext', 'unknown') in format_priority else 999
        )
        
        for format_info in sorted_formats[:3]:  # 最多尝试3个格式
            try:
                url = format_info.get('url')
                ext = format_info.get('ext', 'vtt')
                
                if not url:
                    continue
                
                # 下载字幕内容
                content = await self.download_subtitle_content(url, ext)
                if not content:
                    continue
                
                # 解析字幕
                segments = self.parse_subtitle_content(content, ext)
                if not segments:
                    continue
                
                # 创建字幕轨道
                track = SubtitleTrack(
                    language=language,
                    language_name=subtitle_config.SUPPORTED_LANGUAGES.get(language, language),
                    is_auto_generated=is_auto_generated,
                    format=ext,
                    url=url,
                    segments=segments,
                    quality="medium" if is_auto_generated else "high",
                    source=f"{platform}_{'auto' if is_auto_generated else 'manual'}"
                )
                
                tracks.append(track)
                self.logger.info(f"Extracted {platform} subtitle: {language} ({ext})")
                
                # 对于每种语言，只取第一个成功的格式
                break
                
            except Exception as e:
                self.logger.warning(f"Failed to extract subtitle format {format_info.get('ext')}: {str(e)}")
                continue
        
        return tracks
    
    def _detect_platform(self, url: str, info: Dict) -> str:
        """检测视频平台"""
        # 从URL检测
        parsed = urlparse(url.lower())
        domain = parsed.netloc.replace('www.', '').replace('m.', '')
        
        platform_mapping = {
            'youtube.com': 'youtube',
            'youtu.be': 'youtube',
            'bilibili.com': 'bilibili',
            'b23.tv': 'bilibili',
            'twitter.com': 'twitter',
            'x.com': 'twitter',
            'facebook.com': 'facebook',
            'fb.watch': 'facebook',
            'instagram.com': 'instagram',
            'tiktok.com': 'tiktok',
            'vimeo.com': 'vimeo',
            'dailymotion.com': 'dailymotion',
            'twitch.tv': 'twitch',
            'streamable.com': 'streamable',
            'reddit.com': 'reddit',
            'imgur.com': 'imgur',
        }
        
        for platform_domain, platform_name in platform_mapping.items():
            if platform_domain in domain:
                return platform_name
        
        # 从extractor info检测
        extractor = info.get('extractor', '').lower()
        if extractor:
            extractor_mapping = {
                'youtube': 'youtube',
                'bilibili': 'bilibili',
                'twitter': 'twitter',
                'facebook': 'facebook',
                'instagram': 'instagram',
                'tiktok': 'tiktok',
                'vimeo': 'vimeo',
                'dailymotion': 'dailymotion',
                'twitch': 'twitch',
            }
            
            for ext_name, platform_name in extractor_mapping.items():
                if ext_name in extractor:
                    return platform_name
        
        # 默认返回generic
        return 'generic'
    
    def _extract_formats_info(self, info: Dict) -> Dict:
        """提取格式信息"""
        formats_info = {
            'available_formats': [],
            'best_video': None,
            'best_audio': None,
        }
        
        formats = info.get('formats', [])
        
        for f in formats:
            format_info = {
                'format_id': f.get('format_id'),
                'ext': f.get('ext'),
                'resolution': f.get('resolution'),
                'fps': f.get('fps'),
                'vcodec': f.get('vcodec'),
                'acodec': f.get('acodec'),
                'filesize': f.get('filesize'),
                'quality': f.get('quality'),
                'url': f.get('url', '').split('?')[0] if f.get('url') else ''
            }
            formats_info['available_formats'].append(format_info)
        
        # 找出最佳视频和音频格式
        video_formats = [f for f in formats if f.get('vcodec') != 'none']
        audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
        
        if video_formats:
            best_video = max(video_formats, key=lambda x: (x.get('height', 0), x.get('fps', 0)))
            formats_info['best_video'] = best_video.get('format_id')
        
        if audio_formats:
            best_audio = max(audio_formats, key=lambda x: x.get('abr', 0))
            formats_info['best_audio'] = best_audio.get('format_id')
        
        return formats_info
    
    def _language_matches(self, subtitle_lang: str, request_lang: str) -> bool:
        """检查字幕语言是否匹配请求语言"""
        if subtitle_lang == request_lang:
            return True
        
        # 处理中文变体
        chinese_variants = ['zh', 'zh-CN', 'zh-TW', 'zh-Hans', 'zh-Hant']
        if subtitle_lang in chinese_variants and request_lang in chinese_variants:
            return True
        
        # 处理英语变体
        english_variants = ['en', 'en-US', 'en-GB']
        if subtitle_lang in english_variants and request_lang in english_variants:
            return True
        
        # 处理基础语言代码
        subtitle_base = subtitle_lang.split('-')[0]
        request_base = request_lang.split('-')[0]
        if subtitle_base == request_base:
            return True
        
        return False
    
    def get_supported_languages(self) -> Dict[str, str]:
        """获取支持的字幕语言"""
        return subtitle_config.SUPPORTED_LANGUAGES
    
    async def get_extractor_info(self, url: str) -> Dict[str, Any]:
        """获取yt-dlp提取器信息"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                # 获取提取器信息而不下载
                ie_result = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
                
                return {
                    'extractor': ie_result.get('extractor', ''),
                    'extractor_key': ie_result.get('extractor_key', ''),
                    'webpage_url': ie_result.get('webpage_url', ''),
                    'original_url': ie_result.get('original_url', ''),
                    'title': ie_result.get('title', ''),
                    'description': ie_result.get('description', ''),
                    'duration': ie_result.get('duration', 0),
                    'view_count': ie_result.get('view_count', 0),
                    'like_count': ie_result.get('like_count', 0),
                    'dislike_count': ie_result.get('dislike_count', 0),
                    'uploader': ie_result.get('uploader', ''),
                    'upload_date': ie_result.get('upload_date', ''),
                    'thumbnail': ie_result.get('thumbnail', ''),
                    'tags': ie_result.get('tags', []),
                    'categories': ie_result.get('categories', []),
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get extractor info: {str(e)}")
            return {}
    
    async def test_extraction(self, url: str) -> Dict[str, Any]:
        """测试是否可以从URL提取信息"""
        try:
            # 快速测试
            with yt_dlp.YoutubeDL({'quiet': True, 'simulate': True}) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
                
                return {
                    'extractable': True,
                    'platform': self._detect_platform(url, info),
                    'title': info.get('title', ''),
                    'has_subtitles': bool(info.get('subtitles') or info.get('automatic_captions')),
                    'subtitle_languages': list(info.get('subtitles', {}).keys()) + 
                                        list(info.get('automatic_captions', {}).keys()),
                    'duration': info.get('duration', 0),
                    'extractor': info.get('extractor', ''),
                }
                
        except Exception as e:
            return {
                'extractable': False,
                'error': str(e),
                'platform': 'unknown'
            }