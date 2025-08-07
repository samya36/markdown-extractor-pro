"""
YouTube字幕提取器
专门处理YouTube视频的字幕提取，支持所有类型的字幕
"""

import re
import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import aiohttp
import yt_dlp
from .base_extractor import BaseSubtitleExtractor, SubtitleTrack, SubtitleSegment, VideoInfo
from ..config import subtitle_config, app_config, USER_AGENTS
import random

logger = logging.getLogger(__name__)

class YouTubeSubtitleExtractor(BaseSubtitleExtractor):
    """YouTube专用字幕提取器"""
    
    def __init__(self, proxy_manager=None, session: aiohttp.ClientSession = None):
        super().__init__(proxy_manager, session)
        self.platform_name = "YouTube"
        
        # YouTube特定配置
        self.ydl_opts.update({
            'youtube_include_dash_manifest': False,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'allsubtitles': False,  # 我们手动选择语言
            'subtitlesformat': 'vtt/srv3/srv2/srv1/ttml/best',
        })
    
    def can_handle(self, url: str) -> bool:
        """检查是否为YouTube URL"""
        parsed = urlparse(url.lower())
        return any(domain in parsed.netloc for domain in [
            'youtube.com', 'youtu.be', 'm.youtube.com', 'music.youtube.com'
        ])
    
    async def extract_video_info(self, url: str) -> VideoInfo:
        """提取YouTube视频信息"""
        try:
            self.logger.info(f"Extracting video info from: {url}")
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
                
                video_info = VideoInfo(
                    id=info.get('id', ''),
                    title=info.get('title', 'Unknown'),
                    duration=info.get('duration', 0),
                    uploader=info.get('uploader', 'Unknown'),
                    upload_date=info.get('upload_date', ''),
                    view_count=info.get('view_count', 0),
                    description=(info.get('description', '') or '')[:500],
                    thumbnail=info.get('thumbnail', ''),
                    webpage_url=info.get('webpage_url', url),
                    platform='youtube',
                    available_subtitles=list(info.get('subtitles', {}).keys()),
                    automatic_captions=list(info.get('automatic_captions', {}).keys()),
                    formats_info=self._extract_formats_info(info)
                )
                
                self.logger.info(f"Extracted info for: {video_info.title}")
                return video_info
                
        except Exception as e:
            self.logger.error(f"Failed to extract video info: {str(e)}")
            raise Exception(f"YouTube视频信息提取失败: {str(e)}")
    
    async def extract_subtitles(self, url: str, languages: List[str] = None) -> List[SubtitleTrack]:
        """提取YouTube字幕"""
        try:
            if languages is None:
                languages = ['zh-CN', 'zh', 'en']
            
            self.logger.info(f"Extracting subtitles for languages: {languages}")
            
            # 获取字幕信息
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
            
            subtitle_tracks = []
            
            # 1. 提取手动字幕（优先级最高）
            manual_subtitles = info.get('subtitles', {})
            for lang in languages:
                if lang in manual_subtitles:
                    tracks = await self._extract_manual_subtitles(manual_subtitles[lang], lang)
                    subtitle_tracks.extend(tracks)
            
            # 2. 提取自动生成字幕
            auto_captions = info.get('automatic_captions', {})
            for lang in languages:
                # 优先使用精确匹配
                if lang in auto_captions:
                    tracks = await self._extract_auto_captions(auto_captions[lang], lang)
                    subtitle_tracks.extend(tracks)
                # 尝试语言变体
                elif lang.split('-')[0] in auto_captions:
                    base_lang = lang.split('-')[0]
                    tracks = await self._extract_auto_captions(auto_captions[base_lang], base_lang)
                    subtitle_tracks.extend(tracks)
            
            # 3. 如果没有找到字幕，尝试英语作为后备
            if not subtitle_tracks and 'en' not in languages:
                if 'en' in manual_subtitles:
                    tracks = await self._extract_manual_subtitles(manual_subtitles['en'], 'en')
                    subtitle_tracks.extend(tracks)
                elif 'en' in auto_captions:
                    tracks = await self._extract_auto_captions(auto_captions['en'], 'en')
                    subtitle_tracks.extend(tracks)
            
            self.logger.info(f"Found {len(subtitle_tracks)} subtitle tracks")
            return subtitle_tracks
            
        except Exception as e:
            self.logger.error(f"Failed to extract subtitles: {str(e)}")
            raise Exception(f"YouTube字幕提取失败: {str(e)}")
    
    async def _extract_manual_subtitles(self, subtitle_formats: List[Dict], language: str) -> List[SubtitleTrack]:
        """提取手动字幕"""
        tracks = []
        
        # 按格式优先级排序
        format_priority = ['vtt', 'srv3', 'srv2', 'srv1', 'ttml']
        sorted_formats = sorted(
            subtitle_formats, 
            key=lambda x: format_priority.index(x.get('ext', 'unknown')) 
            if x.get('ext', 'unknown') in format_priority else 999
        )
        
        for format_info in sorted_formats:
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
                    is_auto_generated=False,
                    format=ext,
                    url=url,
                    segments=segments,
                    quality="high",
                    source="manual"
                )
                
                tracks.append(track)
                self.logger.info(f"Extracted manual subtitle: {language} ({ext})")
                
                # 只取第一个成功的格式
                break
                
            except Exception as e:
                self.logger.warning(f"Failed to extract manual subtitle format {format_info.get('ext')}: {str(e)}")
                continue
        
        return tracks
    
    async def _extract_auto_captions(self, caption_formats: List[Dict], language: str) -> List[SubtitleTrack]:
        """提取自动生成字幕"""
        tracks = []
        
        # 按格式优先级排序
        format_priority = ['vtt', 'srv3', 'srv2', 'srv1', 'ttml']
        sorted_formats = sorted(
            caption_formats, 
            key=lambda x: format_priority.index(x.get('ext', 'unknown')) 
            if x.get('ext', 'unknown') in format_priority else 999
        )
        
        for format_info in sorted_formats:
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
                    is_auto_generated=True,
                    format=ext,
                    url=url,
                    segments=segments,
                    quality="medium",
                    source="auto_generated"
                )
                
                tracks.append(track)
                self.logger.info(f"Extracted auto caption: {language} ({ext})")
                
                # 只取第一个成功的格式
                break
                
            except Exception as e:
                self.logger.warning(f"Failed to extract auto caption format {format_info.get('ext')}: {str(e)}")
                continue
        
        return tracks
    
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
                'url': f.get('url', '').split('?')[0]  # 移除查询参数
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
    
    async def get_live_captions(self, url: str, language: str = 'en') -> List[SubtitleSegment]:
        """获取直播字幕（如果支持）"""
        try:
            # YouTube直播字幕需要特殊处理
            # 这里是一个基础实现，实际可能需要更复杂的逻辑
            
            video_id = self._extract_video_id(url)
            if not video_id:
                return []
            
            # 构建直播字幕API URL
            api_url = f"https://www.youtube.com/api/timedtext?v={video_id}&lang={language}&fmt=vtt&live=1"
            
            content = await self.download_subtitle_content(api_url, 'vtt')
            if content:
                return self.parse_subtitle_content(content, 'vtt')
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get live captions: {str(e)}")
            return []
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """从URL提取视频ID"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def search_subtitles_by_query(self, query: str, language: str = 'en', max_results: int = 10) -> List[Dict]:
        """根据查询搜索带字幕的视频"""
        try:
            # 使用yt-dlp搜索功能
            search_opts = self.ydl_opts.copy()
            search_opts.update({
                'quiet': True,
                'extract_flat': True,
            })
            
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                search_results = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, f"ytsearch{max_results}:{query}", False
                )
            
            results = []
            for entry in search_results.get('entries', []):
                # 检查是否有字幕
                video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                
                try:
                    video_info = await self.extract_video_info(video_url)
                    if video_info.available_subtitles or video_info.automatic_captions:
                        results.append({
                            'title': entry.get('title'),
                            'url': video_url,
                            'duration': entry.get('duration'),
                            'view_count': entry.get('view_count'),
                            'upload_date': entry.get('upload_date'),
                            'available_subtitles': video_info.available_subtitles,
                            'automatic_captions': video_info.automatic_captions,
                        })
                except:
                    continue
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search subtitles: {str(e)}")
            return []
    
    def get_supported_languages(self) -> Dict[str, str]:
        """获取YouTube支持的字幕语言"""
        # YouTube支持大多数常见语言
        return subtitle_config.SUPPORTED_LANGUAGES