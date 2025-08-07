"""
智能字幕格式转换器
支持所有主流字幕格式之间的相互转换
"""

import re
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import asdict
import logging
from .extractors.base_extractor import SubtitleSegment, SubtitleTrack
from .config import subtitle_config, MIME_TYPES

logger = logging.getLogger(__name__)

class SubtitleFormatConverter:
    """字幕格式转换器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 支持的转换器映射
        self.converters = {
            'srt': {
                'generator': self._generate_srt,
                'parser': self._parse_srt,
                'mime_type': MIME_TYPES['srt'],
                'description': 'SubRip字幕格式'
            },
            'vtt': {
                'generator': self._generate_vtt,
                'parser': self._parse_vtt,
                'mime_type': MIME_TYPES['vtt'],
                'description': 'WebVTT字幕格式'
            },
            'ass': {
                'generator': self._generate_ass,
                'parser': self._parse_ass,
                'mime_type': MIME_TYPES['ass'],
                'description': 'Advanced SubStation Alpha'
            },
            'ssa': {
                'generator': self._generate_ssa,
                'parser': self._parse_ssa,
                'mime_type': MIME_TYPES['ssa'],
                'description': 'SubStation Alpha'
            },
            'txt': {
                'generator': self._generate_txt,
                'parser': None,  # TXT通常不需要解析回字幕
                'mime_type': MIME_TYPES['txt'],
                'description': '纯文本格式'
            },
            'json': {
                'generator': self._generate_json,
                'parser': self._parse_json,
                'mime_type': MIME_TYPES['json'],
                'description': 'JSON格式（包含时间戳）'
            },
            'csv': {
                'generator': self._generate_csv,
                'parser': self._parse_csv,
                'mime_type': MIME_TYPES['csv'],
                'description': 'CSV表格格式'
            },
            'xml': {
                'generator': self._generate_xml,
                'parser': self._parse_xml,
                'mime_type': MIME_TYPES['xml'],
                'description': 'XML格式'
            },
            'ttml': {
                'generator': self._generate_ttml,
                'parser': self._parse_ttml,
                'mime_type': MIME_TYPES['ttml'],
                'description': 'Timed Text Markup Language'
            },
            'dfxp': {
                'generator': self._generate_dfxp,
                'parser': self._parse_dfxp,
                'mime_type': MIME_TYPES['dfxp'],
                'description': 'Distribution Format Exchange Profile'
            }
        }
    
    def convert_subtitle_track(self, track: SubtitleTrack, target_format: str) -> str:
        """转换字幕轨道到指定格式"""
        if target_format not in self.converters:
            raise ValueError(f"Unsupported target format: {target_format}")
        
        if not track.segments:
            raise ValueError("No subtitle segments to convert")
        
        converter = self.converters[target_format]
        generator = converter['generator']
        
        try:
            content = generator(track.segments, track)
            self.logger.info(f"Converted {len(track.segments)} segments to {target_format}")
            return content
        except Exception as e:
            self.logger.error(f"Failed to convert to {target_format}: {str(e)}")
            raise
    
    def convert_segments(self, segments: List[SubtitleSegment], target_format: str, **kwargs) -> str:
        """直接转换字幕片段列表"""
        if target_format not in self.converters:
            raise ValueError(f"Unsupported target format: {target_format}")
        
        converter = self.converters[target_format]
        generator = converter['generator']
        
        # 创建临时轨道对象
        temp_track = SubtitleTrack(
            language=kwargs.get('language', 'unknown'),
            language_name=kwargs.get('language_name', 'Unknown'),
            is_auto_generated=kwargs.get('is_auto_generated', False),
            format=target_format,
            url="",
            segments=segments,
            quality=kwargs.get('quality', 'unknown'),
            source=kwargs.get('source', 'converted')
        )
        
        try:
            content = generator(segments, temp_track)
            self.logger.info(f"Converted {len(segments)} segments to {target_format}")
            return content
        except Exception as e:
            self.logger.error(f"Failed to convert to {target_format}: {str(e)}")
            raise
    
    def parse_subtitle_file(self, content: str, source_format: str) -> List[SubtitleSegment]:
        """解析字幕文件内容"""
        if source_format not in self.converters:
            raise ValueError(f"Unsupported source format: {source_format}")
        
        converter = self.converters[source_format]
        parser = converter['parser']
        
        if not parser:
            raise ValueError(f"Parsing not supported for format: {source_format}")
        
        try:
            segments = parser(content)
            self.logger.info(f"Parsed {len(segments)} segments from {source_format}")
            return segments
        except Exception as e:
            self.logger.error(f"Failed to parse {source_format}: {str(e)}")
            raise
    
    # SRT格式处理
    def _generate_srt(self, segments: List[SubtitleSegment], track: SubtitleTrack) -> str:
        """生成SRT格式字幕"""
        srt_content = []
        
        for i, segment in enumerate(segments, 1):
            start_time = self._seconds_to_srt_time(segment.start_time)
            end_time = self._seconds_to_srt_time(segment.end_time)
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(segment.text)
            srt_content.append("")  # 空行分隔
        
        return '\n'.join(srt_content)
    
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
                    start_time = self._srt_time_to_seconds(time_match.group(1))
                    end_time = self._srt_time_to_seconds(time_match.group(2))
                    text = '\n'.join(text_lines)
                    
                    segments.append(SubtitleSegment(
                        start_time=start_time,
                        end_time=end_time,
                        text=text
                    ))
        
        return segments
    
    # VTT格式处理
    def _generate_vtt(self, segments: List[SubtitleSegment], track: SubtitleTrack) -> str:
        """生成VTT格式字幕"""
        vtt_content = ["WEBVTT"]
        
        # 添加元数据
        if track.language:
            vtt_content.append(f"Language: {track.language}")
        
        vtt_content.append("")  # 空行
        
        for segment in segments:
            start_time = self._seconds_to_vtt_time(segment.start_time)
            end_time = self._seconds_to_vtt_time(segment.end_time)
            
            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(segment.text)
            vtt_content.append("")  # 空行分隔
        
        return '\n'.join(vtt_content)
    
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
                    start_time = self._vtt_time_to_seconds(time_match.group(1))
                    end_time = self._vtt_time_to_seconds(time_match.group(2))
                    
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
    
    # ASS格式处理
    def _generate_ass(self, segments: List[SubtitleSegment], track: SubtitleTrack) -> str:
        """生成ASS格式字幕"""
        ass_content = [
            "[Script Info]",
            f"Title: {track.language_name} Subtitles",
            f"ScriptType: v4.00+",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Default,Arial,16,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]
        
        for segment in segments:
            start_time = self._seconds_to_ass_time(segment.start_time)
            end_time = self._seconds_to_ass_time(segment.end_time)
            text = segment.text.replace('\n', '\\N')  # ASS换行符
            
            ass_content.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")
        
        return '\n'.join(ass_content)
    
    def _parse_ass(self, content: str) -> List[SubtitleSegment]:
        """解析ASS格式字幕"""
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
                    start_time = self._ass_time_to_seconds(parts[1])
                    end_time = self._ass_time_to_seconds(parts[2])
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
    
    # SSA格式处理（与ASS类似但更简单）
    def _generate_ssa(self, segments: List[SubtitleSegment], track: SubtitleTrack) -> str:
        """生成SSA格式字幕"""
        ssa_content = [
            "[Script Info]",
            f"Title: {track.language_name} Subtitles",
            f"ScriptType: v4.00",
            "",
            "[V4 Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, TertiaryColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, AlphaLevel, Encoding",
            "Style: Default,Arial,16,16777215,255,0,0,0,0,1,2,0,2,10,10,10,0,1",
            "",
            "[Events]",
            "Format: Marked, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]
        
        for segment in segments:
            start_time = self._seconds_to_ass_time(segment.start_time)
            end_time = self._seconds_to_ass_time(segment.end_time)
            text = segment.text.replace('\n', '\\n')
            
            ssa_content.append(f"Dialogue: Marked=0,{start_time},{end_time},Default,,0,0,0,,{text}")
        
        return '\n'.join(ssa_content)
    
    def _parse_ssa(self, content: str) -> List[SubtitleSegment]:
        """解析SSA格式字幕（与ASS解析类似）"""
        return self._parse_ass(content)  # SSA和ASS解析逻辑相同
    
    # TXT格式处理
    def _generate_txt(self, segments: List[SubtitleSegment], track: SubtitleTrack) -> str:
        """生成纯文本格式"""
        txt_lines = []
        
        for segment in segments:
            # 格式：[时间] 文本
            timestamp = f"[{self._seconds_to_readable_time(segment.start_time)}]"
            txt_lines.append(f"{timestamp} {segment.text}")
        
        return '\n'.join(txt_lines)
    
    # JSON格式处理
    def _generate_json(self, segments: List[SubtitleSegment], track: SubtitleTrack) -> str:
        """生成JSON格式字幕"""
        subtitle_data = {
            "metadata": {
                "language": track.language,
                "language_name": track.language_name,
                "format": "json",
                "total_segments": len(segments),
                "is_auto_generated": track.is_auto_generated,
                "source": track.source,
                "generated_at": datetime.now().isoformat()
            },
            "subtitles": []
        }
        
        for i, segment in enumerate(segments):
            subtitle_data["subtitles"].append({
                "index": i + 1,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "duration": segment.end_time - segment.start_time,
                "text": segment.text,
                "confidence": segment.confidence,
                "language": segment.language or track.language
            })
        
        return json.dumps(subtitle_data, ensure_ascii=False, indent=2)
    
    def _parse_json(self, content: str) -> List[SubtitleSegment]:
        """解析JSON格式字幕"""
        data = json.loads(content)
        segments = []
        
        for item in data.get("subtitles", []):
            segments.append(SubtitleSegment(
                start_time=item["start_time"],
                end_time=item["end_time"],
                text=item["text"],
                confidence=item.get("confidence", 1.0),
                language=item.get("language", "")
            ))
        
        return segments
    
    # CSV格式处理
    def _generate_csv(self, segments: List[SubtitleSegment], track: SubtitleTrack) -> str:
        """生成CSV格式字幕"""
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            "Index", "Start Time", "End Time", "Duration", "Text", 
            "Confidence", "Language"
        ])
        
        # 写入数据
        for i, segment in enumerate(segments, 1):
            writer.writerow([
                i,
                segment.start_time,
                segment.end_time,
                segment.end_time - segment.start_time,
                segment.text.replace('\n', ' | '),  # 替换换行符
                segment.confidence,
                segment.language or track.language
            ])
        
        return output.getvalue()
    
    def _parse_csv(self, content: str) -> List[SubtitleSegment]:
        """解析CSV格式字幕"""
        import io
        
        input_stream = io.StringIO(content)
        reader = csv.reader(input_stream)
        
        segments = []
        header = next(reader, None)  # 跳过表头
        
        for row in reader:
            if len(row) >= 5:
                segments.append(SubtitleSegment(
                    start_time=float(row[1]),
                    end_time=float(row[2]),
                    text=row[4].replace(' | ', '\n'),  # 恢复换行符
                    confidence=float(row[5]) if len(row) > 5 else 1.0,
                    language=row[6] if len(row) > 6 else ""
                ))
        
        return segments
    
    # XML格式处理
    def _generate_xml(self, segments: List[SubtitleSegment], track: SubtitleTrack) -> str:
        """生成XML格式字幕"""
        root = ET.Element("subtitles")
        
        # 添加元数据
        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "language").text = track.language
        ET.SubElement(metadata, "language_name").text = track.language_name
        ET.SubElement(metadata, "total_segments").text = str(len(segments))
        ET.SubElement(metadata, "is_auto_generated").text = str(track.is_auto_generated)
        ET.SubElement(metadata, "source").text = track.source
        
        # 添加字幕段落
        for i, segment in enumerate(segments, 1):
            subtitle_elem = ET.SubElement(root, "subtitle")
            subtitle_elem.set("index", str(i))
            subtitle_elem.set("start", str(segment.start_time))
            subtitle_elem.set("end", str(segment.end_time))
            subtitle_elem.set("confidence", str(segment.confidence))
            
            if segment.language:
                subtitle_elem.set("language", segment.language)
            
            subtitle_elem.text = segment.text
        
        # 格式化输出
        self._indent_xml(root)
        return ET.tostring(root, encoding='unicode', xml_declaration=True)
    
    def _parse_xml(self, content: str) -> List[SubtitleSegment]:
        """解析XML格式字幕"""
        root = ET.fromstring(content)
        segments = []
        
        for subtitle_elem in root.findall('subtitle'):
            segments.append(SubtitleSegment(
                start_time=float(subtitle_elem.get('start')),
                end_time=float(subtitle_elem.get('end')),
                text=subtitle_elem.text or '',
                confidence=float(subtitle_elem.get('confidence', 1.0)),
                language=subtitle_elem.get('language', '')
            ))
        
        return segments
    
    # TTML格式处理
    def _generate_ttml(self, segments: List[SubtitleSegment], track: SubtitleTrack) -> str:
        """生成TTML格式字幕"""
        ttml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<tt xmlns="http://www.w3.org/ns/ttml"
    xmlns:tts="http://www.w3.org/ns/ttml#styling"
    xmlns:ttm="http://www.w3.org/ns/ttml#metadata"
    xml:lang="{language}">
  <head>
    <metadata>
      <ttm:title>{title}</ttm:title>
    </metadata>
    <styling>
      <style xml:id="defaultStyle"
             tts:fontFamily="Arial"
             tts:fontSize="16px"
             tts:textAlign="center"
             tts:color="white"/>
    </styling>
  </head>
  <body>
    <div>
{paragraphs}
    </div>
  </body>
</tt>'''
        
        paragraphs = []
        for segment in segments:
            begin_time = self._seconds_to_ttml_time(segment.start_time)
            end_time = self._seconds_to_ttml_time(segment.end_time)
            text = segment.text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            paragraphs.append(f'      <p begin="{begin_time}" end="{end_time}" style="defaultStyle">{text}</p>')
        
        return ttml_template.format(
            language=track.language or 'en',
            title=f"{track.language_name} Subtitles",
            paragraphs='\n'.join(paragraphs)
        )
    
    def _parse_ttml(self, content: str) -> List[SubtitleSegment]:
        """解析TTML格式字幕"""
        try:
            root = ET.fromstring(content)
            segments = []
            
            # 查找所有p标签（段落）
            namespaces = {'ttml': 'http://www.w3.org/ns/ttml'}
            
            for p in root.findall('.//ttml:p', namespaces) or root.findall('.//p'):
                begin = p.get('begin', '0s')
                end = p.get('end', '0s')
                
                start_time = self._ttml_time_to_seconds(begin)
                end_time = self._ttml_time_to_seconds(end)
                
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
            self.logger.error(f"Error parsing TTML: {str(e)}")
            return []
    
    # DFXP格式处理（与TTML类似）
    def _generate_dfxp(self, segments: List[SubtitleSegment], track: SubtitleTrack) -> str:
        """生成DFXP格式字幕"""
        return self._generate_ttml(segments, track)  # DFXP与TTML格式相同
    
    def _parse_dfxp(self, content: str) -> List[SubtitleSegment]:
        """解析DFXP格式字幕"""
        return self._parse_ttml(content)  # DFXP与TTML解析相同
    
    # 时间格式转换工具方法
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """秒数转SRT时间格式 HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _srt_time_to_seconds(self, time_str: str) -> float:
        """SRT时间格式转秒数"""
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        return 0.0
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """秒数转VTT时间格式 HH:MM:SS.mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def _vtt_time_to_seconds(self, time_str: str) -> float:
        """VTT时间格式转秒数"""
        parts = time_str.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        return 0.0
    
    def _seconds_to_ass_time(self, seconds: float) -> str:
        """秒数转ASS时间格式 H:MM:SS.cc"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds - int(seconds)) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    def _ass_time_to_seconds(self, time_str: str) -> float:
        """ASS时间格式转秒数"""
        parts = time_str.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            sec_parts = parts[2].split('.')
            seconds = int(sec_parts[0])
            centisecs = int(sec_parts[1]) if len(sec_parts) > 1 else 0
            return hours * 3600 + minutes * 60 + seconds + centisecs / 100
        return 0.0
    
    def _seconds_to_ttml_time(self, seconds: float) -> str:
        """秒数转TTML时间格式"""
        return f"{seconds:.3f}s"
    
    def _ttml_time_to_seconds(self, time_str: str) -> float:
        """TTML时间格式转秒数"""
        if time_str.endswith('s'):
            return float(time_str[:-1])
        elif time_str.endswith('ms'):
            return float(time_str[:-2]) / 1000
        # 处理HH:MM:SS格式
        elif ':' in time_str:
            return self._vtt_time_to_seconds(time_str)
        return 0.0
    
    def _seconds_to_readable_time(self, seconds: float) -> str:
        """秒数转可读时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _indent_xml(self, elem, level=0):
        """格式化XML缩进"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent_xml(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def get_supported_formats(self) -> Dict[str, Dict]:
        """获取支持的格式信息"""
        return {
            format_name: {
                'mime_type': info['mime_type'],
                'description': info['description'],
                'can_parse': info['parser'] is not None,
                'can_generate': True
            }
            for format_name, info in self.converters.items()
        }
    
    def validate_segments(self, segments: List[SubtitleSegment]) -> List[str]:
        """验证字幕段落的有效性"""
        issues = []
        
        for i, segment in enumerate(segments):
            # 检查时间顺序
            if segment.start_time >= segment.end_time:
                issues.append(f"Segment {i+1}: Start time >= End time")
            
            # 检查时间重叠
            if i > 0 and segment.start_time < segments[i-1].end_time:
                issues.append(f"Segment {i+1}: Overlaps with previous segment")
            
            # 检查空文本
            if not segment.text.strip():
                issues.append(f"Segment {i+1}: Empty text")
            
            # 检查置信度
            if segment.confidence < 0 or segment.confidence > 1:
                issues.append(f"Segment {i+1}: Invalid confidence value")
        
        return issues