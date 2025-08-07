"""
AI字幕生成系统
支持多种AI模型和语言，无字幕视频的智能转录
"""

import os
import re
import json
import logging
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import aiohttp
import numpy as np
from .extractors.base_extractor import SubtitleSegment, SubtitleTrack
from .config import subtitle_config, app_config, env_config

# 动态导入AI模型库
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available. Install with: pip install openai-whisper")

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logging.warning("SpeechRecognition not available. Install with: pip install SpeechRecognition")

try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    logging.warning("GoogleTrans not available. Install with: pip install googletrans==4.0.0rc1")

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionResult:
    """转录结果数据结构"""
    segments: List[SubtitleSegment]
    language: str
    confidence: float
    model_used: str
    processing_time: float
    word_count: int

class AISubtitleGenerator:
    """AI字幕生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 模型缓存
        self.whisper_models = {}
        self.sr_recognizer = None
        self.translator = None
        
        # 支持的模型
        self.available_models = self._check_available_models()
        
        # 初始化翻译器
        if GOOGLETRANS_AVAILABLE:
            try:
                self.translator = Translator()
            except Exception as e:
                self.logger.warning(f"Failed to initialize translator: {str(e)}")
    
    def _check_available_models(self) -> Dict[str, bool]:
        """检查可用的AI模型"""
        models = {
            'whisper': WHISPER_AVAILABLE,
            'speech_recognition': SPEECH_RECOGNITION_AVAILABLE,
            'google_translate': GOOGLETRANS_AVAILABLE,
        }
        
        self.logger.info(f"Available AI models: {[k for k, v in models.items() if v]}")
        return models
    
    async def generate_subtitles(
        self, 
        audio_file: str, 
        target_language: str = "auto",
        model_name: str = "base",
        model_type: str = "whisper"
    ) -> TranscriptionResult:
        """生成字幕"""
        
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            if model_type == "whisper" and self.available_models['whisper']:
                result = await self._generate_with_whisper(audio_file, model_name, target_language)
            elif model_type == "speech_recognition" and self.available_models['speech_recognition']:
                result = await self._generate_with_speech_recognition(audio_file, target_language)
            else:
                # 回退到默认模型
                if self.available_models['whisper']:
                    result = await self._generate_with_whisper(audio_file, "base", target_language)
                elif self.available_models['speech_recognition']:
                    result = await self._generate_with_speech_recognition(audio_file, target_language)
                else:
                    raise Exception("No AI models available for subtitle generation")
            
            processing_time = asyncio.get_event_loop().time() - start_time
            result.processing_time = processing_time
            
            # 计算字数
            word_count = sum(len(seg.text.split()) for seg in result.segments)
            result.word_count = word_count
            
            self.logger.info(f"Generated {len(result.segments)} subtitle segments in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate subtitles: {str(e)}")
            raise
    
    async def _generate_with_whisper(
        self, 
        audio_file: str, 
        model_name: str,
        target_language: str = "auto"
    ) -> TranscriptionResult:
        """使用Whisper生成字幕"""
        
        try:
            # 加载或获取缓存的模型
            if model_name not in self.whisper_models:
                self.logger.info(f"Loading Whisper model: {model_name}")
                
                # 在线程池中加载模型
                model = await asyncio.get_event_loop().run_in_executor(
                    None, whisper.load_model, model_name
                )
                self.whisper_models[model_name] = model
            
            model = self.whisper_models[model_name]
            
            # 设置转录选项
            options = {
                'fp16': False,  # 兼容性更好
                'language': None if target_language == "auto" else target_language.split('-')[0],
                'task': 'transcribe',
                'verbose': False,
            }
            
            # 在线程池中执行转录
            self.logger.info(f"Transcribing audio with Whisper ({model_name})...")
            result = await asyncio.get_event_loop().run_in_executor(
                None, model.transcribe, audio_file, options
            )
            
            # 转换为字幕段落
            segments = []
            for segment in result['segments']:
                subtitle_segment = SubtitleSegment(
                    start_time=segment['start'],
                    end_time=segment['end'],
                    text=self._clean_text(segment['text']),
                    confidence=segment.get('avg_logprob', 0.0),
                    language=result['language']
                )
                segments.append(subtitle_segment)
            
            # 后处理：合并短段落，分割长段落
            segments = self._post_process_segments(segments)
            
            return TranscriptionResult(
                segments=segments,
                language=result['language'],
                confidence=np.mean([seg.confidence for seg in segments]) if segments else 0.0,
                model_used=f"whisper-{model_name}",
                processing_time=0.0,  # 会在调用处设置
                word_count=0  # 会在调用处设置
            )
            
        except Exception as e:
            self.logger.error(f"Whisper transcription failed: {str(e)}")
            raise Exception(f"Whisper转录失败: {str(e)}")
    
    async def _generate_with_speech_recognition(
        self, 
        audio_file: str,
        target_language: str = "auto"
    ) -> TranscriptionResult:
        """使用SpeechRecognition生成字幕"""
        
        try:
            if not self.sr_recognizer:
                self.sr_recognizer = sr.Recognizer()
            
            # 分割音频为小段进行识别
            segments = await self._split_audio_for_sr(audio_file)
            
            subtitle_segments = []
            
            for i, (start_time, end_time, audio_data) in enumerate(segments):
                try:
                    # 使用Google Speech Recognition
                    text = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.sr_recognizer.recognize_google,
                        audio_data,
                        None,  # key
                        target_language.split('-')[0] if target_language != "auto" else "en"
                    )
                    
                    if text.strip():
                        subtitle_segment = SubtitleSegment(
                            start_time=start_time,
                            end_time=end_time,
                            text=self._clean_text(text),
                            confidence=0.8,  # Speech Recognition doesn't provide confidence
                            language=target_language if target_language != "auto" else "en"
                        )
                        subtitle_segments.append(subtitle_segment)
                        
                except sr.UnknownValueError:
                    self.logger.debug(f"Could not understand audio segment {i}")
                    continue
                except sr.RequestError as e:
                    self.logger.warning(f"Speech recognition request failed for segment {i}: {str(e)}")
                    continue
            
            # 检测语言
            detected_language = self._detect_language_from_segments(subtitle_segments)
            
            return TranscriptionResult(
                segments=subtitle_segments,
                language=detected_language,
                confidence=0.8,  # 固定值
                model_used="speech_recognition",
                processing_time=0.0,
                word_count=0
            )
            
        except Exception as e:
            self.logger.error(f"Speech recognition transcription failed: {str(e)}")
            raise Exception(f"语音识别转录失败: {str(e)}")
    
    async def _split_audio_for_sr(self, audio_file: str, chunk_duration: int = 30) -> List[Tuple[float, float, sr.AudioData]]:
        """为Speech Recognition分割音频"""
        
        try:
            import librosa
            
            # 加载音频
            y, sr_rate = librosa.load(audio_file, sr=16000)
            duration = len(y) / sr_rate
            
            chunks = []
            chunk_samples = chunk_duration * sr_rate
            
            for start_sample in range(0, len(y), chunk_samples):
                end_sample = min(start_sample + chunk_samples, len(y))
                
                start_time = start_sample / sr_rate
                end_time = end_sample / sr_rate
                
                chunk_audio = y[start_sample:end_sample]
                
                # 转换为AudioData格式
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    import soundfile as sf
                    sf.write(temp_file.name, chunk_audio, sr_rate)
                    
                    with sr.AudioFile(temp_file.name) as source:
                        audio_data = self.sr_recognizer.record(source)
                    
                    os.unlink(temp_file.name)
                
                chunks.append((start_time, end_time, audio_data))
            
            return chunks
            
        except ImportError:
            self.logger.error("librosa and soundfile are required for audio splitting")
            raise Exception("音频处理库缺失，请安装: pip install librosa soundfile")
        except Exception as e:
            self.logger.error(f"Failed to split audio: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """清理转录文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊标记
        text = re.sub(r'\[.*?\]', '', text)  # 移除[music], [applause]等
        text = re.sub(r'\(.*?\)', '', text)  # 移除括号内容
        
        # 首字母大写
        text = text.strip()
        if text:
            text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        return text
    
    def _post_process_segments(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        """后处理字幕段落"""
        if not segments:
            return segments
        
        processed = []
        
        for segment in segments:
            # 检查文本长度
            if len(segment.text) > app_config.MAX_SUBTITLE_LENGTH:
                # 分割长文本
                split_segments = self._split_long_segment(segment)
                processed.extend(split_segments)
            elif segment.duration() >= app_config.MIN_SUBTITLE_DURATION:
                # 保留正常长度的段落
                processed.append(segment)
            # 忽略过短的段落
        
        # 合并相邻的短段落
        merged = self._merge_short_segments(processed)
        
        return merged
    
    def _split_long_segment(self, segment: SubtitleSegment) -> List[SubtitleSegment]:
        """分割长字幕段落"""
        words = segment.text.split()
        if len(words) <= 10:  # 如果单词数不多，不分割
            return [segment]
        
        # 按句号、问号、感叹号分割
        sentences = re.split(r'[.!?]+', segment.text)
        if len(sentences) <= 1:
            # 按单词数量分割
            mid_word = len(words) // 2
            first_half = ' '.join(words[:mid_word])
            second_half = ' '.join(words[mid_word:])
            
            duration = segment.duration()
            mid_time = segment.start_time + duration / 2
            
            return [
                SubtitleSegment(
                    start_time=segment.start_time,
                    end_time=mid_time,
                    text=first_half,
                    confidence=segment.confidence,
                    language=segment.language
                ),
                SubtitleSegment(
                    start_time=mid_time,
                    end_time=segment.end_time,
                    text=second_half,
                    confidence=segment.confidence,
                    language=segment.language
                )
            ]
        
        # 按句子分割
        result = []
        sentence_start = segment.start_time
        sentence_duration = segment.duration() / len(sentences)
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if sentence:
                sentence_end = sentence_start + sentence_duration
                result.append(SubtitleSegment(
                    start_time=sentence_start,
                    end_time=sentence_end,
                    text=sentence,
                    confidence=segment.confidence,
                    language=segment.language
                ))
                sentence_start = sentence_end
        
        return result
    
    def _merge_short_segments(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        """合并短字幕段落"""
        if len(segments) <= 1:
            return segments
        
        merged = []
        current = segments[0]
        
        for next_segment in segments[1:]:
            # 如果当前段落很短且与下一个段落时间接近，则合并
            if (current.duration() < app_config.MIN_SUBTITLE_DURATION * 2 and
                next_segment.start_time - current.end_time < 1.0 and  # 间隔小于1秒
                len(current.text) + len(next_segment.text) < app_config.MAX_SUBTITLE_LENGTH):
                
                # 合并段落
                current = SubtitleSegment(
                    start_time=current.start_time,
                    end_time=next_segment.end_time,
                    text=f"{current.text} {next_segment.text}",
                    confidence=(current.confidence + next_segment.confidence) / 2,
                    language=current.language
                )
            else:
                merged.append(current)
                current = next_segment
        
        merged.append(current)
        return merged
    
    def _detect_language_from_segments(self, segments: List[SubtitleSegment]) -> str:
        """从字幕段落检测语言"""
        if not segments:
            return "unknown"
        
        # 简单的语言检测
        text_sample = ' '.join([seg.text for seg in segments[:5]])  # 前5个段落
        
        # 检测中文
        if re.search(r'[\u4e00-\u9fff]', text_sample):
            return "zh"
        # 检测日文
        elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text_sample):
            return "ja"
        # 检测韩文
        elif re.search(r'[\uac00-\ud7af]', text_sample):
            return "ko"
        # 检测阿拉伯文
        elif re.search(r'[\u0600-\u06ff]', text_sample):
            return "ar"
        # 检测泰文
        elif re.search(r'[\u0e00-\u0e7f]', text_sample):
            return "th"
        # 默认英语
        else:
            return "en"
    
    async def translate_subtitles(
        self, 
        segments: List[SubtitleSegment], 
        target_language: str
    ) -> List[SubtitleSegment]:
        """翻译字幕"""
        
        if not self.available_models['google_translate'] or not self.translator:
            self.logger.warning("Google Translate not available")
            return segments
        
        try:
            translated_segments = []
            
            # 批量翻译以提高效率
            batch_size = 10
            for i in range(0, len(segments), batch_size):
                batch = segments[i:i + batch_size]
                texts = [seg.text for seg in batch]
                
                # 执行翻译
                translations = await asyncio.get_event_loop().run_in_executor(
                    None, self._translate_batch, texts, target_language
                )
                
                # 创建翻译后的段落
                for j, translation in enumerate(translations):
                    if j < len(batch):
                        original_segment = batch[j]
                        translated_segment = SubtitleSegment(
                            start_time=original_segment.start_time,
                            end_time=original_segment.end_time,
                            text=translation,
                            confidence=original_segment.confidence * 0.9,  # 翻译会降低一些置信度
                            language=target_language
                        )
                        translated_segments.append(translated_segment)
            
            self.logger.info(f"Translated {len(translated_segments)} segments to {target_language}")
            return translated_segments
            
        except Exception as e:
            self.logger.error(f"Translation failed: {str(e)}")
            return segments  # 返回原文
    
    def _translate_batch(self, texts: List[str], target_language: str) -> List[str]:
        """批量翻译文本"""
        try:
            if not texts:
                return []
            
            # 合并文本进行翻译
            combined_text = '\n'.join(texts)
            result = self.translator.translate(combined_text, dest=target_language.split('-')[0])
            
            # 分割翻译结果
            translated_lines = result.text.split('\n')
            
            # 确保结果数量匹配
            if len(translated_lines) != len(texts):
                # 如果行数不匹配，逐个翻译
                return [self.translator.translate(text, dest=target_language.split('-')[0]).text for text in texts]
            
            return translated_lines
            
        except Exception as e:
            self.logger.error(f"Batch translation failed: {str(e)}")
            return texts  # 返回原文
    
    def create_subtitle_track_from_ai(
        self, 
        result: TranscriptionResult,
        source_url: str = "",
        quality: str = "ai_generated"
    ) -> SubtitleTrack:
        """从AI转录结果创建字幕轨道"""
        
        return SubtitleTrack(
            language=result.language,
            language_name=subtitle_config.SUPPORTED_LANGUAGES.get(result.language, result.language),
            is_auto_generated=True,
            format="srt",  # AI生成默认为SRT格式
            url="",  # AI生成的字幕没有URL
            segments=result.segments,
            quality=quality,
            source=f"ai_{result.model_used}"
        )
    
    def get_available_models(self) -> Dict[str, Any]:
        """获取可用的AI模型信息"""
        models_info = {}
        
        if self.available_models['whisper']:
            models_info['whisper'] = {
                'available': True,
                'models': list(subtitle_config.WHISPER_MODELS.keys()),
                'recommended': app_config.DEFAULT_WHISPER_MODEL,
                'description': 'OpenAI Whisper - 高质量多语言语音转文字'
            }
        
        if self.available_models['speech_recognition']:
            models_info['speech_recognition'] = {
                'available': True,
                'models': ['google'],
                'recommended': 'google',
                'description': 'Google Speech Recognition - 在线语音识别服务'
            }
        
        return models_info
    
    async def estimate_processing_time(self, audio_duration: float, model_type: str = "whisper") -> Dict[str, float]:
        """估算处理时间"""
        estimates = {}
        
        if model_type == "whisper":
            for model_name, info in subtitle_config.WHISPER_MODELS.items():
                # 根据模型速度估算
                speed_multiplier = float(info['speed'].replace('x', ''))
                estimated_time = audio_duration / speed_multiplier * 60  # 转换为秒
                estimates[model_name] = estimated_time
        
        elif model_type == "speech_recognition":
            # Speech Recognition通常较快但需要网络
            estimates['google'] = audio_duration * 0.5
        
        return estimates