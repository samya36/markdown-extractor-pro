import yt_dlp
import whisper
import os
import json
import random
import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import requests
from urllib.parse import urlparse
import re

logger = logging.getLogger(__name__)

class EnhancedVideoSubtitleDownloader:
    def __init__(self):
        self.whisper_model = None
        self.download_dir = "downloads"
        Path(self.download_dir).mkdir(exist_ok=True)
        
        # 代理配置
        self.proxies = []
        self.current_proxy_index = 0
        
        # User-Agent池
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 2
        
        logger.info("EnhancedVideoSubtitleDownloader initialized")
    
    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.user_agents)
    
    def _get_next_proxy(self) -> Optional[str]:
        """获取下一个代理"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy
    
    def _get_optimized_ydl_opts(self, use_proxy: bool = True) -> Dict:
        """获取优化的yt-dlp配置"""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['zh-CN', 'zh', 'en', 'ja', 'ko', 'es', 'fr', 'de'],
            'skip_download': True,
            
            # 绕过地理限制
            'geo_bypass': True,
            'geo_bypass_country': ['US', 'UK', 'JP', 'SG'],
            
            # 用户代理和头部
            'http_headers': {
                'User-Agent': self._get_random_user_agent(),
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            
            # 网络配置
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            
            # YouTube特定优化
            'youtube_include_dash_manifest': False,
            'ignoreerrors': False,
        }
        
        # 添加代理配置
        if use_proxy:
            proxy = self._get_next_proxy()
            if proxy:
                opts['proxy'] = proxy
                logger.info(f"Using proxy: {proxy}")
        
        return opts
    
    def get_video_info(self, url: str) -> Dict:
        """获取视频基本信息（带重试机制）"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempting to get video info (attempt {attempt + 1}/{self.max_retries})")
                
                ydl_opts = self._get_optimized_ydl_opts(use_proxy=(attempt > 0))
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    result = {
                        'id': info.get('id', ''),
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', 'Unknown'),
                        'view_count': info.get('view_count', 0),
                        'upload_date': info.get('upload_date', ''),
                        'description': info.get('description', '')[:500] + '...' if info.get('description') else '',
                        'thumbnail': info.get('thumbnail', ''),
                        'has_subtitles': bool(info.get('subtitles', {})),
                        'available_subtitles': list(info.get('subtitles', {}).keys()),
                        'automatic_captions': list(info.get('automatic_captions', {}).keys()),
                        'formats_count': len(info.get('formats', [])),
                        'webpage_url': info.get('webpage_url', url)
                    }
                    
                    logger.info(f"Successfully retrieved info for: {result['title']}")
                    return result
                    
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                # 检查是否为地理限制错误
                if any(keyword in error_msg for keyword in ['geo', 'region', 'country', 'location', 'blocked']):
                    logger.info("Detected geo-blocking, will try with proxy on next attempt")
                
                # 检查是否为速率限制
                if any(keyword in error_msg for keyword in ['rate', 'limit', '429', 'too many']):
                    delay = self.retry_delay * (2 ** attempt)  # 指数退避
                    logger.info(f"Rate limited, waiting {delay} seconds")
                    time.sleep(delay)
                
                # 最后一次尝试前等待
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        raise Exception(f"获取视频信息失败，已尝试 {self.max_retries} 次。最后错误: {str(last_error)}")
    
    def add_proxy(self, proxy_url: str) -> bool:
        """添加代理服务器"""
        try:
            # 验证代理格式
            parsed = urlparse(proxy_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid proxy URL format")
            
            self.proxies.append(proxy_url)
            logger.info(f"Added proxy: {proxy_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to add proxy {proxy_url}: {str(e)}")
            return False
    
    def test_proxy(self, proxy_url: str, timeout: int = 10) -> bool:
        """测试代理连接"""
        try:
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False
    
    def load_whisper_model(self, model_name: str = "base") -> bool:
        """加载Whisper模型"""
        try:
            if self.whisper_model is None:
                logger.info(f"Loading Whisper model: {model_name}")
                self.whisper_model = whisper.load_model(model_name)
                logger.info("Whisper model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            return False
    
    def download_subtitles(self, url: str, languages: List[str] = None, formats: List[str] = None) -> Dict:
        """下载字幕文件"""
        if languages is None:
            languages = ['zh-CN', 'en']
        if formats is None:
            formats = ['srt', 'vtt', 'txt']
        
        logger.info(f"Starting subtitle download for: {url}")
        results = {
            'existing_subtitles': {},
            'ai_subtitles': None,
            'video_info': None,
            'download_paths': []
        }
        
        try:
            # 获取视频信息
            video_info = self.get_video_info(url)
            results['video_info'] = video_info
            
            # 安全的文件名
            safe_title = self._sanitize_filename(video_info['title'])
            video_id = video_info.get('id', 'unknown')
            
            # 下载现有字幕
            existing_subs = self._download_existing_subtitles(url, safe_title, video_id, languages, formats)
            results['existing_subtitles'] = existing_subs
            results['download_paths'].extend(existing_subs.values())
            
            # 如果没有现有字幕，使用AI生成
            if not existing_subs:
                logger.info("No existing subtitles found, attempting AI generation")
                ai_result = self._generate_ai_subtitles(url, safe_title, video_id, formats)
                if ai_result:
                    results['ai_subtitles'] = ai_result
                    results['download_paths'].extend(ai_result['formats'].values())
            
            logger.info(f"Subtitle download completed. Files: {len(results['download_paths'])}")
            return results
            
        except Exception as e:
            logger.error(f"Subtitle download failed: {str(e)}")
            raise Exception(f"字幕下载失败: {str(e)}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名"""
        # 移除或替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        return filename.strip()
    
    def _download_existing_subtitles(self, url: str, title: str, video_id: str, languages: List[str], formats: List[str]) -> Dict[str, str]:
        """下载现有字幕"""
        results = {}
        
        for lang in languages:
            try:
                ydl_opts = self._get_optimized_ydl_opts()
                ydl_opts.update({
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': [lang],
                    'subtitlesformat': 'srt/vtt/best',
                    'outtmpl': f'{self.download_dir}/{title}-{video_id}-{lang}.%(ext)s',
                    'skip_download': True
                })
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # 查找下载的字幕文件
                for ext in ['srt', 'vtt']:
                    subtitle_file = Path(f"{self.download_dir}/{title}-{video_id}-{lang}.{ext}")
                    if subtitle_file.exists():
                        results[lang] = str(subtitle_file)
                        logger.info(f"Downloaded subtitle: {lang} -> {subtitle_file}")
                        
                        # 转换格式
                        if 'txt' in formats:
                            txt_file = self._convert_subtitle_to_txt(subtitle_file)
                            if txt_file:
                                results[f"{lang}_txt"] = txt_file
                        break
                        
            except Exception as e:
                logger.warning(f"Failed to download {lang} subtitle: {str(e)}")
                continue
        
        return results
    
    def _generate_ai_subtitles(self, url: str, title: str, video_id: str, formats: List[str]) -> Optional[Dict]:
        """使用AI生成字幕"""
        try:
            if not self.load_whisper_model():
                return None
            
            # 下载音频
            audio_file = self._extract_audio(url, title, video_id)
            if not audio_file:
                return None
            
            logger.info("Generating AI subtitles with Whisper")
            result = self.whisper_model.transcribe(audio_file)
            
            # 保存不同格式的字幕
            subtitle_formats = {}
            base_path = f"{self.download_dir}/{title}-{video_id}-ai"
            
            if 'srt' in formats:
                srt_file = f"{base_path}.srt"
                self._save_srt(result, srt_file)
                subtitle_formats['srt'] = srt_file
            
            if 'txt' in formats:
                txt_file = f"{base_path}.txt"
                self._save_txt(result, txt_file)
                subtitle_formats['txt'] = txt_file
            
            if 'raw' in formats:
                raw_file = f"{base_path}.json"
                with open(raw_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                subtitle_formats['raw'] = raw_file
            
            # 清理音频文件
            try:
                os.remove(audio_file)
            except Exception:
                pass
            
            return {
                'language': result.get('language', 'unknown'),
                'formats': subtitle_formats
            }
            
        except Exception as e:
            logger.error(f"AI subtitle generation failed: {str(e)}")
            return None
    
    def _extract_audio(self, url: str, title: str, video_id: str) -> Optional[str]:
        """提取音频文件"""
        try:
            audio_file = f"{self.download_dir}/{title}-{video_id}-temp.mp3"
            
            ydl_opts = self._get_optimized_ydl_opts()
            ydl_opts.update({
                'format': 'bestaudio/best',
                'outtmpl': audio_file,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if os.path.exists(audio_file):
                logger.info(f"Audio extracted: {audio_file}")
                return audio_file
            
            return None
            
        except Exception as e:
            logger.error(f"Audio extraction failed: {str(e)}")
            return None
    
    def _convert_subtitle_to_txt(self, subtitle_file: Path) -> Optional[str]:
        """将字幕文件转换为纯文本"""
        try:
            txt_file = subtitle_file.with_suffix('.txt')
            
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的SRT解析
            if subtitle_file.suffix == '.srt':
                lines = content.split('\n')
                text_lines = []
                
                for line in lines:
                    line = line.strip()
                    # 跳过序号行和时间轴行
                    if line and not line.isdigit() and '-->' not in line:
                        text_lines.append(line)
                
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(text_lines))
                
                logger.info(f"Converted to TXT: {txt_file}")
                return str(txt_file)
            
            return None
            
        except Exception as e:
            logger.error(f"Subtitle conversion failed: {str(e)}")
            return None
    
    def _save_srt(self, whisper_result: Dict, output_file: str):
        """保存SRT格式字幕"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(whisper_result['segments'], 1):
                start_time = self._seconds_to_srt_time(segment['start'])
                end_time = self._seconds_to_srt_time(segment['end'])
                text = segment['text'].strip()
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
    
    def _save_txt(self, whisper_result: Dict, output_file: str):
        """保存TXT格式字幕"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for segment in whisper_result['segments']:
                f.write(segment['text'].strip() + '\n')
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """将秒数转换为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def get_supported_sites(self) -> List[str]:
        """获取支持的网站列表"""
        try:
            import yt_dlp.extractor
            extractors = yt_dlp.extractor.gen_extractors()
            sites = []
            
            for extractor in extractors:
                if hasattr(extractor, 'IE_NAME') and extractor.IE_NAME:
                    sites.append(extractor.IE_NAME)
            
            return sorted(list(set(sites)))[:50]  # 限制返回数量
        except Exception as e:
            logger.error(f"Failed to get supported sites: {str(e)}")
            return ['youtube', 'bilibili', 'twitter', 'facebook', 'instagram']