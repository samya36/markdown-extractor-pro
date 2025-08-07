# Universal Subtitle Downloader 🎬📝

一个完整的多平台视频字幕下载器，支持AI字幕生成和多种格式转换。

A comprehensive multi-platform video subtitle downloader with AI generation and format conversion capabilities.

## ✨ 功能特性 | Features

### 🌍 多平台支持 | Multi-Platform Support
- **YouTube** - 支持手动字幕和自动生成字幕
- **哔哩哔哩 (Bilibili)** - 支持中文字幕下载
- **通用平台** - 基于 yt-dlp，支持 1000+ 网站
- **更多平台** - Twitter, Facebook, Instagram, TikTok, Vimeo等

### 🤖 AI 字幕生成 | AI Subtitle Generation
- **OpenAI Whisper** - 高质量多语言语音转文字
- **Google Speech Recognition** - 在线语音识别
- **自动回退** - 无字幕时自动使用AI生成
- **多种模型** - tiny, base, small, medium, large等

### 🔄 格式转换 | Format Conversion
- **10+ 格式支持** - SRT, VTT, ASS, SSA, TTML, JSON, CSV, XML等
- **双向转换** - 任意格式间相互转换
- **智能解析** - 自动识别和解析各种字幕格式
- **格式验证** - 确保输出质量

### 🌐 多语言支持 | Multi-Language Support
- **60+ 语言** - 支持世界主要语言
- **语言检测** - 自动检测字幕语言
- **翻译功能** - 集成Google翻译等服务
- **语言匹配** - 智能匹配语言变体

### ⚡ 高性能 | High Performance
- **异步处理** - 基于asyncio的高效并发
- **批量下载** - 支持多个视频同时处理
- **进度跟踪** - 实时处理进度显示
- **错误恢复** - 自动重试和错误处理

## 🚀 快速开始 | Quick Start

### 安装依赖 | Installation

```bash
# 克隆项目
git clone <repository-url>
cd video-subtitle-downloader

# 安装依赖
pip install -r requirements_universal.txt

# 安装 FFmpeg (如果需要AI功能)
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 下载 FFmpeg 并添加到 PATH
```

### 基本使用 | Basic Usage

#### 命令行使用 | Command Line Usage

```bash
# 基础下载
python -m universal_subtitle_downloader.cli https://www.youtube.com/watch?v=VIDEO_ID

# 指定语言和格式
python -m universal_subtitle_downloader.cli \
    https://www.youtube.com/watch?v=VIDEO_ID \
    --languages zh-CN en \
    --formats srt vtt

# 启用AI字幕生成
python -m universal_subtitle_downloader.cli \
    https://example.com/video.mp4 \
    --ai-fallback \
    --ai-model base

# 批量下载
python -m universal_subtitle_downloader.cli \
    --batch urls.txt \
    --output-dir ./downloads

# 查看视频信息
python -m universal_subtitle_downloader.cli \
    https://www.youtube.com/watch?v=VIDEO_ID \
    --info-only

# 列出可用字幕
python -m universal_subtitle_downloader.cli \
    https://www.youtube.com/watch?v=VIDEO_ID \
    --list-subtitles
```

#### Python API 使用 | Python API Usage

```python
import asyncio
from universal_subtitle_downloader import (
    UniversalSubtitleDownloader,
    DownloadRequest
)

async def download_subtitles():
    async with UniversalSubtitleDownloader() as downloader:
        # 创建下载请求
        request = DownloadRequest(
            url="https://www.youtube.com/watch?v=VIDEO_ID",
            languages=['zh-CN', 'en'],
            formats=['srt', 'vtt'],
            enable_ai_fallback=True,
            ai_model="base"
        )
        
        # 执行下载
        result = await downloader.download_subtitles(request)
        
        if result.success:
            print(f"成功下载: {result.video_info.title}")
            print(f"文件: {result.downloaded_files}")
        else:
            print(f"下载失败: {result.errors}")

# 运行下载
asyncio.run(download_subtitles())
```

## 📋 详细功能 | Detailed Features

### 支持的平台 | Supported Platforms

| 平台 | 手动字幕 | 自动字幕 | 直播字幕 | 状态 |
|------|----------|----------|----------|------|
| YouTube | ✅ | ✅ | ✅ | 完全支持 |
| 哔哩哔哩 | ✅ | ✅ | ❌ | 完全支持 |
| Twitter/X | ❌ | ❌ | ❌ | 基础支持 |
| Facebook | ❌ | ✅ | ❌ | 基础支持 |
| Instagram | ❌ | ❌ | ❌ | 基础支持 |
| TikTok | ❌ | ✅ | ❌ | 基础支持 |
| Vimeo | ✅ | ❌ | ❌ | 基础支持 |
| 其他1000+站点 | 视情况 | 视情况 | ❌ | 通过yt-dlp |

### 支持的格式 | Supported Formats

| 格式 | 描述 | 读取 | 写入 | 推荐使用场景 |
|------|------|------|------|--------------|
| SRT | SubRip字幕 | ✅ | ✅ | 通用，兼容性最好 |
| VTT | WebVTT字幕 | ✅ | ✅ | 网页播放器 |
| ASS | Advanced SubStation | ✅ | ✅ | 高级样式，动画 |
| SSA | SubStation Alpha | ✅ | ✅ | 基础样式 |
| TTML | Timed Text Markup | ✅ | ✅ | 标准化格式 |
| DFXP | Distribution Format | ✅ | ✅ | 广播标准 |
| JSON | JSON格式 | ✅ | ✅ | 程序处理 |
| CSV | 逗号分隔值 | ✅ | ✅ | 数据分析 |
| XML | XML格式 | ✅ | ✅ | 结构化数据 |
| TXT | 纯文本 | ❌ | ✅ | 简单文本 |

### AI 模型对比 | AI Models Comparison

| 模型 | 大小 | 速度 | 精度 | 内存占用 | 推荐场景 |
|------|------|------|------|----------|----------|
| tiny | 39MB | 32x | 低 | 低 | 快速测试 |
| base | 74MB | 16x | 中 | 低 | **推荐默认** |
| small | 244MB | 6x | 中高 | 中 | 平衡选择 |
| medium | 769MB | 2x | 高 | 中高 | 高质量需求 |
| large | 1550MB | 1x | 最高 | 高 | 专业使用 |
| large-v2 | 1550MB | 1x | 最高+ | 高 | 最新版本 |
| large-v3 | 1550MB | 1x | 最高++ | 高 | 最新最好 |

## 🛠️ 配置选项 | Configuration Options

### 环境变量 | Environment Variables

```bash
# API 密钥
export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_TRANSLATE_API_KEY="your-google-translate-key"

# 代理设置
export HTTP_PROXY="http://proxy:port"
export HTTPS_PROXY="https://proxy:port"
export SOCKS_PROXY="socks5://proxy:port"

# 调试模式
export DEBUG="true"
export LOG_LEVEL="DEBUG"
```

### 配置文件示例 | Configuration File Example

```python
# config_custom.py
from universal_subtitle_downloader.config import app_config, subtitle_config

# 自定义下载目录
app_config.DOWNLOAD_DIR = "./my_subtitles"

# 自定义AI模型
app_config.DEFAULT_WHISPER_MODEL = "small"

# 自定义并发数
app_config.MAX_CONCURRENT_DOWNLOADS = 3

# 自定义语言优先级
PREFERRED_LANGUAGES = ['zh-CN', 'zh-TW', 'en', 'ja']
```

## 📊 性能优化 | Performance Optimization

### 并发设置 | Concurrency Settings

```python
# 推荐的并发设置
async with UniversalSubtitleDownloader() as downloader:
    # 批量下载时的并发控制
    results = await downloader.batch_download(
        requests, 
        max_concurrent=3  # 根据网络和CPU调整
    )
```

### 内存优化 | Memory Optimization

```python
# AI模型选择建议
memory_recommendations = {
    "4GB RAM": "tiny",
    "8GB RAM": "base", 
    "16GB RAM": "small",
    "32GB+ RAM": "medium/large"
}
```

### 网络优化 | Network Optimization

```python
# 代理管理器使用
from universal_subtitle_downloader.proxy_manager import ProxyManager

proxy_manager = ProxyManager()
proxy_manager.add_proxy("http://proxy1:port")
proxy_manager.add_proxy("socks5://proxy2:port")

downloader = UniversalSubtitleDownloader(proxy_manager=proxy_manager)
```

## 🔧 高级用法 | Advanced Usage

### 自定义提取器 | Custom Extractor

```python
from universal_subtitle_downloader.extractors.base_extractor import BaseSubtitleExtractor

class CustomExtractor(BaseSubtitleExtractor):
    def can_handle(self, url: str) -> bool:
        return "custom-site.com" in url
    
    async def extract_subtitles(self, url: str, languages=None):
        # 实现自定义提取逻辑
        pass

# 注册自定义提取器
downloader.extractors['custom'] = CustomExtractor()
```

### 字幕后处理 | Subtitle Post-processing

```python
def post_process_subtitle(segments):
    """自定义字幕后处理"""
    processed = []
    for segment in segments:
        # 清理文本
        text = segment.text.strip()
        text = re.sub(r'\[.*?\]', '', text)  # 移除标记
        
        # 分割长句
        if len(text) > 50:
            # 自定义分割逻辑
            pass
        
        processed.append(SubtitleSegment(
            start_time=segment.start_time,
            end_time=segment.end_time,
            text=text
        ))
    
    return processed
```

### 格式自定义 | Format Customization

```python
# 自定义文件名模板
filename_templates = {
    'simple': '{title}.{format}',
    'detailed': '{title}_{language}_{quality}.{format}',
    'organized': '{platform}/{uploader}/{title}_{language}.{format}'
}

request = DownloadRequest(
    url="...",
    filename_template=filename_templates['organized']
)
```

## 🧪 测试 | Testing

```bash
# 运行单元测试
python -m pytest tests/

# 运行集成测试
python -m pytest tests/integration/

# 运行示例
python example_usage.py

# 测试特定平台
python -m pytest tests/test_youtube.py
python -m pytest tests/test_bilibili.py
```

## 📈 监控和统计 | Monitoring and Statistics

```python
async with UniversalSubtitleDownloader() as downloader:
    # 执行下载...
    
    # 获取统计信息
    stats = downloader.get_stats()
    print(f"成功率: {stats['success_rate']:.1%}")
    print(f"AI生成数量: {stats['ai_generated_count']}")
    print(f"平均处理时间: {stats['average_processing_time']:.2f}秒")
```

## ❗ 故障排除 | Troubleshooting

### 常见问题 | Common Issues

#### 1. 无法下载YouTube字幕
```bash
# 更新 yt-dlp
pip install --upgrade yt-dlp

# 检查网络连接
python -c "import yt_dlp; print(yt_dlp.version.__version__)"
```

#### 2. AI模型加载失败
```bash
# 检查依赖
pip install torch torchaudio
pip install openai-whisper

# 检查CUDA支持（可选）
python -c "import torch; print(torch.cuda.is_available())"
```

#### 3. 字符编码问题
```python
# 强制UTF-8编码
import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
```

#### 4. 代理连接问题
```bash
# 测试代理连接
curl --proxy http://proxy:port https://www.google.com

# 检查代理格式
export HTTP_PROXY="http://username:password@proxy:port"
```

### 日志调试 | Debug Logging

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 或者在运行时
python -m universal_subtitle_downloader.cli --debug <url>
```

## 🤝 贡献指南 | Contributing

欢迎提交Issue和Pull Request！

1. Fork 项目
2. 创建特性分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 提交Pull Request

## 📄 许可证 | License

MIT License - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢 | Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的视频下载库
- [OpenAI Whisper](https://github.com/openai/whisper) - 高质量语音识别
- [FFmpeg](https://ffmpeg.org/) - 多媒体处理框架
- 所有贡献者和用户的支持

## 📞 支持 | Support

- 📧 Email: support@example.com
- 💬 Discord: [Join our Discord](https://discord.gg/example)
- 🐛 Issues: [GitHub Issues](https://github.com/example/issues)
- 📖 文档: [完整文档](https://docs.example.com)

---

**Universal Subtitle Downloader** - 让字幕下载变得简单！ 🚀