"""
基础字幕提取器
为所有平台提供统一的字幕提取接口
"""

import re
import json
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import aiohttp
import yt_dlp
from ..config import subtitle_config, app_config, USER_AGENTS
import random
import time

logger = logging.getLogger(__name__)

@dataclass
class SubtitleSegment:
    """字幕片段数据结构"""
    start_time: float  # 开始时间（秒）
    end_time: float    # 结束时间（秒）
    text: str         # 字幕文本
    confidence: float = 1.0  # 置信度（0-1）
    language: str = ""       # 语言代码
    
    def duration(self) -> float:
        """获取字幕片段持续时间"""
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

@dataclass
class SubtitleTrack:
    """字幕轨道数据结构"""
    language: str              # 语言代码
    language_name: str         # 语言名称
    is_auto_generated: bool    # 是否自动生成
    format: str               # 原始格式
    url: str                  # 下载URL
    segments: List[SubtitleSegment] = None  # 字幕片段
    quality: str = "unknown"   # 质量等级
    source: str = "unknown"    # 来源
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        if self.segments:
            data['segments'] = [seg.to_dict() for seg in self.segments]
        return data

@dataclass
class VideoInfo:
    """视频信息数据结构"""
    id: str
    title: str
    duration: float
    uploader: str
    upload_date: str
    view_count: int
    description: str
    thumbnail: str
    webpage_url: str
    platform: str
    available_subtitles: List[str]
    automatic_captions: List[str]
    formats_info: Dict
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

class BaseSubtitleExtractor(ABC):
    """基础字幕提取器抽象类"""
    
    def __init__(self, proxy_manager=None, session: aiohttp.ClientSession = None):
        self.proxy_manager = proxy_manager
        self.session = session
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # yt-dlp配置
        self.ydl_opts = self._get_base_ydl_opts()
        
    def _get_base_ydl_opts(self) -> Dict:
        """获取基础yt-dlp配置"""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'writesubtitles': False,  # 我们手动处理字幕
            'writeautomaticsub': False,
            'skip_download': True,
            'format': 'best',
            
            # 网络配置
            'socket_timeout': app_config.REQUEST_TIMEOUT,
            'retries': app_config.MAX_RETRIES,
            'fragment_retries': app_config.MAX_RETRIES,
            
            # 请求头配置
            'http_headers': {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            
            # 绕过地理限制
            'geo_bypass': True,
            'geo_bypass_country': ['US', 'UK', 'JP', 'SG', 'DE', 'FR'],
            
            # YouTube特定优化
            'youtube_include_dash_manifest': False,
            'ignoreerrors': False,
        }
        
        # 添加代理配置
        if self.proxy_manager and self.proxy_manager.get_current_proxy():
            proxy = self.proxy_manager.get_current_proxy()
            opts['proxy'] = proxy
            self.logger.info(f"Using proxy: {proxy}")
        
        return opts
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """检查是否能处理该URL"""
        pass
    
    @abstractmethod
    async def extract_video_info(self, url: str) -> VideoInfo:
        """提取视频信息"""
        pass
    
    @abstractmethod
    async def extract_subtitles(self, url: str, languages: List[str] = None) -> List[SubtitleTrack]:
        """提取字幕"""
        pass
    
    async def download_subtitle_content(self, subtitle_url: str, format_type: str = "vtt") -> str:
        """下载字幕内容"""
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Referer': subtitle_url,
            }
            
            # 使用代理
            proxy = None
            if self.proxy_manager:
                proxy = self.proxy_manager.get_current_proxy()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(
                    subtitle_url, 
                    headers=headers,
                    proxy=proxy
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        self.logger.info(f"Downloaded subtitle content: {len(content)} characters")
                        return content
                    else:
                        raise Exception(f"HTTP {response.status}: Failed to download subtitle")
                        
        except Exception as e:
            self.logger.error(f"Error downloading subtitle: {str(e)}")
            raise
    
    def parse_subtitle_content(self, content: str, format_type: str) -> List[SubtitleSegment]:
        """解析字幕内容"""
        try:
            if format_type.lower() == 'vtt':
                return self._parse_vtt(content)
            elif format_type.lower() == 'srt':
                return self._parse_srt(content)
            elif format_type.lower() in ['srv3', 'srv2', 'srv1']:
                return self._parse_youtube_srv(content)
            elif format_type.lower() == 'ttml':
                return self._parse_ttml(content)
            elif format_type.lower() in ['ass', 'ssa']:
                return self._parse_ass(content)
            else:
                self.logger.warning(f"Unsupported subtitle format: {format_type}")
                return []
        except Exception as e:
            self.logger.error(f"Error parsing subtitle content: {str(e)}")
            return []
    
    def _parse_vtt(self, content: str) -> List[SubtitleSegment]:
        """解析VTT格式字幕"""
        segments = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 查找时间戳行
            if '-->' in line:
                time_match = re.match(r'(\d+:[\d:.]+)\s+-->\s+(\d+:[\d:.]+)', line)
                if time_match:
                    start_time = self._parse_time(time_match.group(1))
                    end_time = self._parse_time(time_match.group(2))
                    
                    # 获取字幕文本
                    i += 1
                    text_lines = []
                    while i < len(lines) and lines[i].strip():
                        text_line = lines[i].strip()
                        # 移除VTT标签
                        text_line = re.sub(r'<[^>]+>', '', text_line)
                        if text_line:
                            text_lines.append(text_line)
                        i += 1
                    
                    if text_lines:
                        text = '\n'.join(text_lines)
                        segments.append(SubtitleSegment(
                            start_time=start_time,
                            end_time=end_time,
                            text=text
                        ))
            i += 1
        
        return segments
    
    def _parse_srt(self, content: str) -> List[SubtitleSegment]:
        """解析SRT格式字幕"""
        segments = []
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # 跳过序号行
                time_line = lines[1]
                text_lines = lines[2:]
                
                time_match = re.match(r'(\d+:[\d:,]+)\s+-->\s+(\d+:[\d:,]+)', time_line)
                if time_match:
                    start_time = self._parse_time(time_match.group(1).replace(',', '.'))
                    end_time = self._parse_time(time_match.group(2).replace(',', '.'))
                    text = '\n'.join(text_lines)
                    
                    segments.append(SubtitleSegment(
                        start_time=start_time,
                        end_time=end_time,
                        text=text
                    ))
        
        return segments
    
    def _parse_youtube_srv(self, content: str) -> List[SubtitleSegment]:
        """解析YouTube SRV格式字幕"""
        try:
            import xml.etree.ElementTree as ET
            
            segments = []
            root = ET.fromstring(content)
            
            for text_elem in root.findall('.//text'):
                start = float(text_elem.get('start', 0))
                duration = float(text_elem.get('dur', 0))
                end_time = start + duration
                text = text_elem.text or ''
                
                # 清理文本
                text = re.sub(r'<[^>]+>', '', text)
                text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                
                if text.strip():
                    segments.append(SubtitleSegment(
                        start_time=start,
                        end_time=end_time,
                        text=text.strip()
                    ))
            
            return segments
        except Exception as e:
            self.logger.error(f"Error parsing SRV format: {str(e)}")
            return []
    
    def _parse_ttml(self, content: str) -> List[SubtitleSegment]:
        """解析TTML格式字幕"""
        try:
            import xml.etree.ElementTree as ET
            
            segments = []
            root = ET.fromstring(content)
            
            # 查找所有p标签（段落）
            for p in root.findall('.//{http://www.w3.org/ns/ttml}p'):
                begin = p.get('begin', '0s')
                end = p.get('end', '0s')
                
                start_time = self._parse_ttml_time(begin)
                end_time = self._parse_ttml_time(end)
                
                # 获取文本内容
                text = ''.join(p.itertext()).strip()
                
                if text:
                    segments.append(SubtitleSegment(
                        start_time=start_time,
                        end_time=end_time,
                        text=text
                    ))
            
            return segments
        except Exception as e:
            self.logger.error(f"Error parsing TTML format: {str(e)}")
            return []
    
    def _parse_ass(self, content: str) -> List[SubtitleSegment]:
        """解析ASS/SSA格式字幕"""
        segments = []
        lines = content.split('\n')
        
        # 查找事件部分
        in_events = False
        for line in lines:
            line = line.strip()
            
            if line.startswith('[Events]'):
                in_events = True
                continue
            elif line.startswith('[') and in_events:
                break
            
            if in_events and line.startswith('Dialogue:'):
                parts = line.split(',', 9)
                if len(parts) >= 10:
                    start_time = self._parse_ass_time(parts[1])
                    end_time = self._parse_ass_time(parts[2])
                    text = parts[9]
                    
                    # 清理ASS标签
                    text = re.sub(r'\{[^}]*\}', '', text)
                    text = text.replace('\\N', '\n')
                    
                    if text.strip():
                        segments.append(SubtitleSegment(
                            start_time=start_time,
                            end_time=end_time,
                            text=text.strip()
                        ))
        
        return segments
    
    def _parse_time(self, time_str: str) -> float:
        """解析时间字符串为秒数"""
        try:
            # 处理不同的时间格式
            time_str = time_str.strip()
            
            # HH:MM:SS.mmm 或 HH:MM:SS,mmm
            if ':' in time_str:
                parts = time_str.replace(',', '.').split(':')
                if len(parts) == 3:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = float(parts[2])
                    return hours * 3600 + minutes * 60 + seconds
                elif len(parts) == 2:
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
            
            # 纯秒数
            return float(time_str)
        except:
            return 0.0
    
    def _parse_ttml_time(self, time_str: str) -> float:
        """解析TTML时间格式"""
        try:
            if time_str.endswith('s'):
                return float(time_str[:-1])
            elif time_str.endswith('ms'):
                return float(time_str[:-2]) / 1000
            elif 'h' in time_str or 'm' in time_str or 's' in time_str:
                # 复杂时间格式 如 1h2m3.5s
                hours = 0
                minutes = 0
                seconds = 0
                
                h_match = re.search(r'(\d+(?:\.\d+)?)h', time_str)
                if h_match:
                    hours = float(h_match.group(1))
                
                m_match = re.search(r'(\d+(?:\.\d+)?)m', time_str)
                if m_match:
                    minutes = float(m_match.group(1))
                
                s_match = re.search(r'(\d+(?:\.\d+)?)s', time_str)
                if s_match:
                    seconds = float(s_match.group(1))
                
                return hours * 3600 + minutes * 60 + seconds
            else:
                return self._parse_time(time_str)
        except:
            return 0.0
    
    def _parse_ass_time(self, time_str: str) -> float:
        """解析ASS时间格式 H:MM:SS.cc"""
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                sec_parts = parts[2].split('.')
                seconds = int(sec_parts[0])
                centiseconds = int(sec_parts[1]) if len(sec_parts) > 1 else 0
                return hours * 3600 + minutes * 60 + seconds + centiseconds / 100
        except:
            return 0.0
    
    def clean_subtitle_text(self, text: str) -> str:
        """清理字幕文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 解码HTML实体
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' ',
        }
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        return text.strip()
    
    async def retry_with_backoff(self, func, *args, max_retries=None, **kwargs):
        """带退避的重试机制"""
        if max_retries is None:
            max_retries = app_config.MAX_RETRIES
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    # 指数退避
                    delay = app_config.RETRY_DELAY * (2 ** attempt)
                    self.logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
        
        raise last_error