# 🎬 视频字幕下载器

一个功能完整的视频字幕下载工具，支持从YouTube、B站等主流视频平台提取和生成字幕。

## ✨ 功能特性

- 📹 支持多平台视频信息获取（YouTube、Bilibili等）
- 🈶 自动提取现有字幕（多语言）
- 🤖 AI智能生成字幕（基于Whisper）
- 📄 多种输出格式（SRT、TXT、RAW）
- 🎯 可选择字幕语言
- 💾 支持完整视频下载
- 🌐 现代化Web界面
- 📱 响应式设计

## 🛠️ 技术栈

### 后端
- **FastAPI** - 高性能Python Web框架
- **yt-dlp** - 视频下载工具
- **OpenAI Whisper** - AI语音转文字
- **PyTorch** - 深度学习框架

### 前端
- **React 19** - 现代化前端框架
- **TypeScript** - 类型安全的JavaScript
- **Tailwind CSS** - 实用的CSS框架
- **Axios** - HTTP客户端

## 📦 安装部署

### 环境要求

- Python 3.9+
- Node.js 16+
- FFmpeg（用于音频处理）

### 后端安装

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\\Scripts\\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

### 前端安装

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

## 🚀 使用说明

1. **启动服务**
   - 后端服务：`http://localhost:8000`
   - 前端界面：`http://localhost:3000`

2. **下载字幕**
   - 输入视频链接
   - 点击"获取信息"查看视频详情
   - 选择需要的语言和格式
   - 点击"开始下载"

3. **配置选项**
   - 选择字幕语言（中文、英文、日文等）
   - 选择输出格式（SRT、TXT、RAW）
   - 启用/关闭AI生成（无现有字幕时）
   - 选择是否下载完整视频

## 📁 项目结构

```
video-subtitle-downloader/
├── backend/                 # Python后端
│   ├── main.py             # FastAPI主应用
│   ├── downloader.py       # 下载核心逻辑
│   ├── requirements.txt    # Python依赖
│   └── downloads/          # 下载文件存储
├── frontend/               # React前端
│   ├── src/
│   │   ├── App.tsx        # 主应用组件
│   │   ├── ErrorBoundary.tsx  # 错误边界
│   │   ├── config.ts      # 配置文件
│   │   └── types/         # TypeScript类型定义
│   ├── package.json       # 前端依赖
│   └── .env.example       # 环境变量示例
└── test.html              # 简单测试页面
```

## 🔧 配置说明

### 环境变量

前端配置（`.env`）：
```bash
REACT_APP_API_BASE_URL=http://localhost:8000/api
```

### API接口

- `GET /` - 健康检查
- `POST /api/video/info` - 获取视频信息
- `POST /api/download/start` - 开始下载任务（待实现）
- `GET /api/task/{task_id}` - 查询任务状态（待实现）

## 🔒 安全特性

- ✅ CORS配置限制域名访问
- ✅ 结构化日志记录
- ✅ 错误边界处理
- ✅ 输入验证和类型检查
- ✅ 环境变量配置

## 🐛 故障排除

### 常见问题

1. **Python依赖安装失败**
   ```bash
   # 升级pip
   pip install --upgrade pip
   
   # 安装系统依赖（Ubuntu/Debian）
   sudo apt install python3-dev build-essential
   ```

2. **FFmpeg未找到**
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # Windows
   # 下载FFmpeg并添加到PATH
   ```

3. **前端启动失败**
   ```bash
   # 清除缓存
   npm cache clean --force
   
   # 删除node_modules重新安装
   rm -rf node_modules
   npm install
   ```

## 📋 待办事项

- [ ] 实现后端下载任务管理
- [ ] 添加用户认证系统
- [ ] 支持更多视频平台
- [ ] 添加字幕编辑功能
- [ ] 实现批量下载
- [ ] 添加下载历史记录
- [ ] 支持Docker部署

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 开源协议

本项目基于MIT协议开源。详见 [LICENSE](LICENSE) 文件。

## ⚠️ 免责声明

本工具仅供学习和研究使用。请确保遵守相关平台的服务条款和版权法律。下载内容时请尊重原创作者的版权。

---

如有问题或建议，请在GitHub Issues中提出。