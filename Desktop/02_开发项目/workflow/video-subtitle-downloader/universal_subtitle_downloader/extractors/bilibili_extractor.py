"""
哔哩哔哩字幕提取器
专门处理哔哩哔哩视频的字幕提取
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

class BilibiliSubtitleExtractor(BaseSubtitleExtractor):
    """哔哩哔哩专用字幕提取器"""
    
    def __init__(self, proxy_manager=None, session: aiohttp.ClientSession = None):
        super().__init__(proxy_manager, session)
        self.platform_name = "哔哩哔哩"
        
        # 哔哩哔哩特定配置
        self.ydl_opts.update({
            'writesubtitles': True,
            'writeautomaticsub': True,
            'allsubtitles': False,
            'subtitlesformat': 'srt/ass/best',
        })
        
        # API URLs
        self.api_base = "https://api.bilibili.com"
        self.subtitle_api = "https://i0.hdslb.com/bfs/subtitle"
    
    def can_handle(self, url: str) -> bool:
        """检查是否为B站URL"""
        parsed = urlparse(url.lower())
        return any(domain in parsed.netloc for domain in [
            'bilibili.com', 'b23.tv', 'bilibili.tv'
        ])
    
    async def extract_video_info(self, url: str) -> VideoInfo:
        """提取B站视频信息"""
        try:
            self.logger.info(f"Extracting Bilibili video info from: {url}")
            
            # 使用yt-dlp获取基本信息
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
            
            # 提取BVID或AV号
            bvid, aid = self._extract_video_ids(url, info)
            
            # 获取详细的视频信息（包括字幕信息）
            detailed_info = await self._get_detailed_video_info(bvid, aid)
            
            # 合并信息
            video_info = VideoInfo(
                id=bvid or str(aid),
                title=info.get('title', 'Unknown'),
                duration=info.get('duration', 0),
                uploader=info.get('uploader', 'Unknown'),
                upload_date=info.get('upload_date', ''),
                view_count=detailed_info.get('view', info.get('view_count', 0)),
                description=(detailed_info.get('desc', info.get('description', '')) or '')[:500],
                thumbnail=detailed_info.get('pic', info.get('thumbnail', '')),
                webpage_url=info.get('webpage_url', url),
                platform='bilibili',
                available_subtitles=self._extract_available_subtitles(detailed_info),
                automatic_captions=[],  # B站主要是手动字幕
                formats_info=self._extract_formats_info(info)
            )
            
            self.logger.info(f"Extracted Bilibili info for: {video_info.title}")
            return video_info
            
        except Exception as e:
            self.logger.error(f"Failed to extract Bilibili video info: {str(e)}")
            raise Exception(f"哔哩哔哩视频信息提取失败: {str(e)}")
    
    async def extract_subtitles(self, url: str, languages: List[str] = None) -> List[SubtitleTrack]:
        """提取B站字幕"""
        try:
            if languages is None:
                languages = ['zh-CN', 'zh', 'en']
            
            self.logger.info(f"Extracting Bilibili subtitles for languages: {languages}")
            
            # 获取视频信息
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
            
            bvid, aid = self._extract_video_ids(url, info)
            cid = info.get('id') or await self._get_cid(bvid, aid)
            
            if not cid:
                raise Exception("无法获取视频CID")
            
            # 获取字幕列表
            subtitle_list = await self._get_subtitle_list(aid, cid)
            
            subtitle_tracks = []
            
            # 处理每个字幕
            for subtitle_info in subtitle_list:
                lang = subtitle_info.get('lan', 'zh-CN')
                lang_doc = subtitle_info.get('lan_doc', '中文')
                subtitle_url = subtitle_info.get('subtitle_url', '')
                
                # 检查是否匹配请求的语言
                if languages and not any(self._language_matches(lang, req_lang) for req_lang in languages):
                    continue
                
                if not subtitle_url:
                    continue
                
                # 确保URL是完整的
                if subtitle_url.startswith('//'):
                    subtitle_url = 'https:' + subtitle_url
                elif subtitle_url.startswith('/'):
                    subtitle_url = 'https://i0.hdslb.com' + subtitle_url
                
                try:
                    # 下载字幕内容
                    content = await self.download_subtitle_content(subtitle_url, 'json')
                    if not content:
                        continue
                    
                    # 解析B站字幕JSON格式
                    segments = self._parse_bilibili_subtitle(content)
                    if not segments:
                        continue
                    
                    # 创建字幕轨道
                    track = SubtitleTrack(
                        language=lang,
                        language_name=lang_doc,
                        is_auto_generated=subtitle_info.get('type', 0) == 1,  # 1表示AI生成
                        format='srt',  # B站字幕转换为SRT格式
                        url=subtitle_url,
                        segments=segments,
                        quality="high",
                        source="bilibili"
                    )
                    
                    subtitle_tracks.append(track)
                    self.logger.info(f"Extracted Bilibili subtitle: {lang} ({lang_doc})")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to extract subtitle {lang}: {str(e)}")
                    continue
            
            self.logger.info(f"Found {len(subtitle_tracks)} Bilibili subtitle tracks")
            return subtitle_tracks
            
        except Exception as e:
            self.logger.error(f"Failed to extract Bilibili subtitles: {str(e)}")
            raise Exception(f"哔哩哔哩字幕提取失败: {str(e)}")
    
    def _extract_video_ids(self, url: str, info: Dict) -> Tuple[Optional[str], Optional[int]]:
        """提取BVID和AV号"""
        bvid = None
        aid = None
        
        # 从yt-dlp信息中获取
        if 'id' in info:
            video_id = info['id']
            if video_id.startswith('BV'):
                bvid = video_id
            else:
                try:
                    aid = int(video_id)
                except:
                    pass
        
        # 从URL中提取
        if 'BV' in url:
            bv_match = re.search(r'BV[a-zA-Z0-9]+', url)
            if bv_match:
                bvid = bv_match.group()
        
        if 'av' in url.lower():
            av_match = re.search(r'av(\d+)', url.lower())
            if av_match:
                aid = int(av_match.group(1))
        
        return bvid, aid
    
    async def _get_detailed_video_info(self, bvid: Optional[str], aid: Optional[int]) -> Dict:
        """获取详细视频信息"""
        try:
            params = {}
            if bvid:
                params['bvid'] = bvid
            elif aid:
                params['aid'] = aid
            else:
                return {}
            
            url = f"{self.api_base}/x/web-interface/view"
            
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Referer': 'https://www.bilibili.com/',
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            return data.get('data', {})
            
            return {}
            
        except Exception as e:
            self.logger.warning(f"Failed to get detailed video info: {str(e)}")
            return {}
    
    async def _get_cid(self, bvid: Optional[str], aid: Optional[int]) -> Optional[str]:
        """获取视频CID"""
        try:
            detailed_info = await self._get_detailed_video_info(bvid, aid)
            pages = detailed_info.get('pages', [])
            if pages:
                return str(pages[0].get('cid'))
            return None
        except Exception as e:
            self.logger.warning(f"Failed to get CID: {str(e)}")
            return None
    
    async def _get_subtitle_list(self, aid: Optional[int], cid: str) -> List[Dict]:
        """获取字幕列表"""
        try:
            if not aid or not cid:
                return []
            
            url = f"{self.api_base}/x/player/v2"
            params = {
                'aid': aid,
                'cid': cid,
            }
            
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Referer': 'https://www.bilibili.com/',
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            player_info = data.get('data', {})
                            subtitle_info = player_info.get('subtitle', {})
                            return subtitle_info.get('subtitles', [])
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get subtitle list: {str(e)}")
            return []
    
    def _parse_bilibili_subtitle(self, content: str) -> List[SubtitleSegment]:
        """解析B站字幕JSON格式"""
        try:
            data = json.loads(content)
            segments = []
            
            body = data.get('body', [])
            for item in body:
                start_time = item.get('from', 0)
                end_time = item.get('to', 0)
                text = item.get('content', '').strip()
                
                if text and end_time > start_time:
                    segments.append(SubtitleSegment(
                        start_time=start_time,
                        end_time=end_time,
                        text=text
                    ))
            
            return segments
            
        except Exception as e:
            self.logger.error(f"Failed to parse Bilibili subtitle: {str(e)}")
            return []
    
    def _extract_available_subtitles(self, detailed_info: Dict) -> List[str]:
        """从详细信息中提取可用字幕语言"""
        # 这里需要实际的API调用来获取字幕列表
        # 暂时返回常见的语言
        return ['zh-CN', 'zh']
    
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
        # 简单的语言匹配逻辑
        if subtitle_lang == request_lang:
            return True
        
        # 处理中文变体
        chinese_variants = ['zh', 'zh-CN', 'zh-TW', 'zh-Hans', 'zh-Hant']
        if subtitle_lang in chinese_variants and request_lang in chinese_variants:
            return True
        
        # 处理基础语言代码
        subtitle_base = subtitle_lang.split('-')[0]
        request_base = request_lang.split('-')[0]
        if subtitle_base == request_base:
            return True
        
        return False
    
    def get_supported_languages(self) -> Dict[str, str]:
        """获取B站支持的字幕语言"""
        # B站主要支持中文，也有一些英文内容
        return {
            'zh-CN': '简体中文',
            'zh-TW': '繁体中文',
            'zh': '中文',
            'en': '英语',
            'ja': '日语',
            'ko': '韩语'
        }
    
    async def search_videos_with_subtitles(self, keyword: str, max_results: int = 20) -> List[Dict]:
        """搜索带字幕的B站视频"""
        try:
            search_url = f"{self.api_base}/x/web-interface/search/type"
            params = {
                'search_type': 'video',
                'keyword': keyword,
                'page': 1,
                'page_size': max_results,
                'order': 'totalrank'
            }
            
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Referer': 'https://www.bilibili.com/',
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            results = []
                            videos = data.get('data', {}).get('result', [])
                            
                            for video in videos:
                                # 检查是否有字幕（这需要额外的API调用）
                                bvid = video.get('bvid')
                                if bvid:
                                    video_url = f"https://www.bilibili.com/video/{bvid}"
                                    
                                    results.append({
                                        'title': video.get('title', ''),
                                        'url': video_url,
                                        'bvid': bvid,
                                        'duration': video.get('duration', ''),
                                        'play': video.get('play', 0),
                                        'author': video.get('author', ''),
                                        'description': video.get('description', ''),
                                        'pic': video.get('pic', ''),
                                    })
                            
                            return results
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to search Bilibili videos: {str(e)}")
            return []