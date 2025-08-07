# 🎬 增强版视频字幕下载器

一个功能强大的视频字幕下载工具，**专门解决YouTube访问限制问题**，支持AI智能字幕生成和数百个视频平台。

## ✨ 核心特性

### 🚫 YouTube访问限制解决方案
- **智能代理切换** - 自动轮换代理服务器绕过地理限制
- **多重绕过策略** - User-Agent轮换、请求头优化、重试机制
- **地理位置伪装** - 支持多国IP地址模拟
- **稳定性保障** - 智能降级和故障转移

### 🤖 AI字幕生成
- **Whisper集成** - 基于OpenAI Whisper的高质量AI转录
- **多语言支持** - 自动识别语言并生成准确字幕
- **音频预处理** - 自动优化音频质量提升识别准确率
- **格式丰富** - SRT、VTT、TXT、JSON等多种输出格式

### 📋 任务管理系统
- **异步处理** - 支持多任务并发下载
- **进度追踪** - 实时显示下载进度和状态
- **任务队列** - 智能调度和资源管理
- **历史记录** - 完整的操作日志和结果保存

### 🌐 平台支持
- **YouTube** - 完美支持，绕过各种限制
- **Bilibili** - 国内主流视频平台
- **Twitter/X** - 社交媒体视频
- **Facebook/Instagram** - 社交平台内容
- **数百个平台** - 基于yt-dlp的广泛支持

## 🛠️ 技术架构

### 后端核心
- **FastAPI** - 异步高性能API框架
- **增强版yt-dlp** - 优化配置的视频提取引擎
- **OpenAI Whisper** - 最先进的AI语音识别
- **PyTorch** - AI模型推理引擎
- **异步任务队列** - 高并发任务处理
- **智能代理管理** - 自动代理轮换系统

### 前端界面
- **React 19** - 最新版本的现代化框架
- **TypeScript** - 完整的类型安全保障
- **Tailwind CSS** - 现代化UI设计系统
- **组件化架构** - 可维护的模块化设计
- **实时状态同步** - 任务进度实时更新

## 🚀 快速开始

### 一键启动（推荐）

```bash
# 克隆项目
git clone <项目地址>
cd video-subtitle-downloader

# 一键启动（自动安装依赖）
python start.py
```

### 手动安装

#### 环境要求
- **Python 3.8+** （推荐3.10+）
- **Node.js 16+** （推荐18+）
- **FFmpeg** （必需，用于音频处理）

#### 后端安装
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt

# 启动增强版服务
cd backend
python enhanced_main.py
```

#### 前端安装
```bash
cd frontend
npm install
npm start
```

### Docker 部署（即将支持）
```bash
docker-compose up -d
```

## 🎯 使用指南

### 基础使用
1. **访问界面**: http://localhost:3000
2. **输入链接**: 粘贴任意支持的视频URL
3. **获取信息**: 点击"获取信息"查看视频详情
4. **配置选项**: 选择语言、格式、AI生成等选项
5. **开始下载**: 点击"开始下载"，任务进入队列

### YouTube访问限制解决
1. **添加代理**: 进入"代理设置"标签页
2. **输入代理地址**: 支持HTTP/HTTPS/SOCKS5代理
3. **测试连接**: 点击"测试连接"验证代理可用性
4. **自动切换**: 系统会自动轮换使用代理服务器

#### 推荐代理服务
- **免费代理**: ProxyList、FreeProxy等（不稳定）
- **付费代理**: Bright Data、Oxylabs、Proxy-Seller等
- **VPN服务**: 配合HTTP代理使用

### AI字幕生成
- **自动触发**: 当视频无现有字幕时自动启用
- **模型选择**: 首次使用会自动下载Whisper模型
- **语言识别**: 自动检测音频语言
- **多格式输出**: SRT、TXT、JSON格式同时生成

### 任务管理
- **实时监控**: 任务管理页面查看所有下载进度
- **并发控制**: 最多支持3个并发下载任务
- **历史记录**: 保存所有下载历史和结果
- **错误重试**: 自动重试失败的任务

## 📁 项目架构

```
video-subtitle-downloader/
├── backend/                    # 🐍 Python后端服务
│   ├── enhanced_main.py       # 🚀 增强版FastAPI主应用
│   ├── enhanced_downloader.py # 💪 强化版下载引擎
│   ├── task_manager.py        # 📋 异步任务管理器
│   ├── requirements.txt       # 📦 Python依赖清单
│   └── downloads/             # 📁 下载文件存储目录
├── frontend/                  # ⚛️ React前端界面
│   ├── src/
│   │   ├── EnhancedApp.tsx   # 🎨 增强版主应用
│   │   ├── components/       # 🧩 组件库
│   │   │   ├── ProxyManager.tsx    # 🔒 代理管理组件
│   │   │   ├── TaskList.tsx        # 📋 任务列表组件
│   │   │   └── SystemStats.tsx     # 📊 系统状态组件
│   │   ├── types/           # 📝 TypeScript类型定义
│   │   ├── config.ts        # ⚙️ 配置文件
│   │   └── ErrorBoundary.tsx # 🛡️ 错误边界
│   └── package.json         # 📦 前端依赖清单
├── start.py                   # 🚀 一键启动脚本
└── README.md                  # 📖 项目文档
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
- `POST /api/download/start` - 开始下载任务
- `GET /api/task/{task_id}` - 查询任务状态
- `DELETE /api/task/{task_id}` - 取消任务
- `POST /api/proxy/add` - 添加代理服务器
- `GET /api/stats` - 系统统计信息

## 🔒 安全与隐私

### 网络安全
- **代理加密** - 支持HTTPS和SOCKS5加密代理
- **请求签名** - 防止API滥用和恶意请求
- **域名限制** - CORS配置仅允许授权域名访问
- **速率限制** - 自动限制请求频率防止封禁

### 数据隐私
- **本地处理** - 所有数据本地存储，不上传到第三方
- **临时文件** - 音频文件自动清理，不留痕迹
- **日志脱敏** - 敏感信息自动过滤
- **代理隔离** - 代理配置与下载任务完全分离

### 访问控制
- **错误边界** - 前端异常自动恢复
- **输入验证** - 严格的URL和参数校验
- **资源限制** - 防止系统资源滥用

## 🐛 故障排除

### YouTube访问问题

**问题**: 提示"地理限制"或"视频不可用"
```bash
# 解决方案
1. 添加高质量代理服务器
2. 尝试不同国家的代理IP
3. 检查代理服务器是否正常工作
4. 使用付费代理服务提高成功率
```

**问题**: 频繁出现"429 Too Many Requests"
```bash
# 解决方案
1. 系统会自动等待和重试
2. 添加更多代理服务器分散请求
3. 降低并发任务数量
4. 检查代理IP是否被YouTube封禁
```

### AI字幕生成问题

**问题**: Whisper模型下载缓慢
```bash
# 解决方案
1. 配置代理服务器加速下载
2. 手动下载模型文件到缓存目录
3. 使用较小的模型（如"base"而非"large"）
```

**问题**: 生成字幕不准确
```bash
# 解决方案
1. 使用更大的Whisper模型
2. 确保音频质量良好
3. 检查音频语言是否正确识别
```

### 系统环境问题

**问题**: FFmpeg未安装
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# 从 https://ffmpeg.org/ 下载并添加到PATH
```

**问题**: Python版本过低
```bash
# 升级Python到3.8+
# 推荐使用pyenv或conda管理Python版本
pyenv install 3.10.0
pyenv global 3.10.0
```

**问题**: 依赖安装失败
```bash
# 升级pip和setuptools
pip install --upgrade pip setuptools wheel

# 清理缓存重新安装
pip cache purge
pip install -r backend/requirements.txt
```

### 网络连接问题

**问题**: 无法访问视频平台
```bash
# 检查网络连接
curl -I https://www.youtube.com

# 测试代理连接
curl -I --proxy socks5://proxy:port https://www.youtube.com

# 检查DNS解析
nslookup youtube.com
```

## 🎯 路线图

### v2.0 - 当前版本 ✅
- ✅ YouTube访问限制完美解决
- ✅ AI字幕生成（Whisper集成）
- ✅ 任务队列和进度追踪
- ✅ 代理服务器管理
- ✅ 现代化界面重设计
- ✅ 系统状态监控

### v2.1 - 即将发布 🚧
- [ ] Docker一键部署
- [ ] 批量URL处理
- [ ] 字幕后处理（翻译、校对）
- [ ] 移动端适配优化
- [ ] 云存储集成（可选）

### v3.0 - 未来规划 🔮
- [ ] 用户系统和权限管理
- [ ] 字幕在线编辑器
- [ ] API接口开放平台
- [ ] 企业级部署方案
- [ ] 更多AI模型支持

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 开源协议

本项目基于MIT协议开源。详见 [LICENSE](LICENSE) 文件。

## ⚠️ 重要声明

### 使用条款
本工具专为**学习研究**和**个人使用**而设计，请用户：

1. **遵守法律法规** - 严格遵守当地法律和平台服务条款
2. **尊重版权** - 仅下载您拥有版权或已获得授权的内容
3. **个人使用** - 不得将本工具用于商业用途或大规模爬取
4. **责任自负** - 使用本工具产生的任何后果由用户自行承担

### 技术声明
- **绕过限制功能**仅用于解决技术访问问题，不用于违规用途
- **代理功能**帮助用户解决网络连接问题，请使用合法代理服务
- **AI功能**基于开源模型，生成结果仅供参考

### 免责条款
开发者不对以下情况承担责任：
- 用户违反平台服务条款造成的账号封禁
- 使用不当导致的法律风险
- 代理服务器的安全性和稳定性
- AI生成内容的准确性和完整性

---

## 🤝 社区支持

- **GitHub Issues**: 报告bug和功能请求
- **Discussions**: 使用交流和经验分享  
- **Wiki**: 详细使用教程和常见问题
- **Releases**: 获取最新版本和更新日志

### 贡献代码
欢迎提交Pull Request！请先阅读贡献指南。

### Star ⭐
如果这个项目对您有帮助，请给一个Star支持！

---

**🎬 让视频字幕下载变得简单高效！**