import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import config from './config';
import { VideoInfo, TaskStatus, ApiResponse, DownloadRequest } from './types';
import ErrorBoundary from './ErrorBoundary';
import ProxyManager from './components/ProxyManager';
import TaskList from './components/TaskList';
import SystemStats from './components/SystemStats';

const API_BASE = config.API_BASE_URL;

function EnhancedApp() {
  const [url, setUrl] = useState('');
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [currentTask, setCurrentTask] = useState<TaskStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'main' | 'tasks' | 'proxy' | 'stats'>('main');
  
  // 配置选项
  const [languages, setLanguages] = useState(['zh-CN', 'en']);
  const [formats, setFormats] = useState(['srt', 'txt']);
  const [useAI, setUseAI] = useState(true);
  const [downloadVideo, setDownloadVideo] = useState(false);

  const getVideoInfo = async () => {
    if (!url.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post<ApiResponse<VideoInfo>>(`${API_BASE}/video/info`, { url });
      if (response.data.success && response.data.data) {
        setVideoInfo(response.data.data);
      } else {
        throw new Error(response.data.error || '获取视频信息失败');
      }
    } catch (error: any) {
      console.error('Error fetching video info:', error);
      alert(error.response?.data?.detail || error.message || '获取视频信息失败');
    }
    setLoading(false);
  };

  const startDownload = async () => {
    setLoading(true);
    try {
      const downloadRequest: DownloadRequest = {
        url,
        languages,
        formats,
        use_ai: useAI,
        download_video: downloadVideo
      };

      const response = await axios.post<{success: boolean; task_id: string}>(`${API_BASE}/download/start`, downloadRequest);
      
      if (response.data.success) {
        const taskId = response.data.task_id;
        setCurrentTask({ 
          task_id: taskId, 
          task_type: 'subtitle_download',
          status: 'pending', 
          progress: 0, 
          message: '开始处理...',
          created_at: new Date().toISOString()
        });
        
        // 轮询任务状态
        pollTaskStatus(taskId);
        
        // 切换到任务管理标签页
        setActiveTab('tasks');
      }
      
    } catch (error: any) {
      console.error('Error starting download:', error);
      alert(error.response?.data?.detail || error.message || '启动下载失败');
    }
    setLoading(false);
  };

  const pollTaskStatus = async (taskId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get<ApiResponse<TaskStatus>>(`${API_BASE}/task/${taskId}`);
        const taskData = response.data.data;
        
        if (taskData) {
          setCurrentTask(taskData);
          
          if (taskData.status === 'completed' || taskData.status === 'failed' || taskData.status === 'cancelled') {
            clearInterval(pollInterval);
          }
        }
      } catch (error: any) {
        console.error('Error polling task status:', error);
        clearInterval(pollInterval);
      }
    }, 2000);
  };

  const downloadFile = (filename: string) => {
    window.open(`${API_BASE}/download/file/${filename}`, '_blank');
  };

  const formatDuration = (duration: number): string => {
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    const seconds = duration % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const formatViewCount = (count: number): string => {
    if (count >= 1000000) {
      return `${(count / 1000000).toFixed(1)}M`;
    }
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`;
    }
    return count.toString();
  };

  const renderMainTab = () => (
    <div className="space-y-6">
      {/* URL 输入区域 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          视频链接
        </label>
        <div className="flex gap-4">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="输入 YouTube、B站、Twitter 等视频链接..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={getVideoInfo}
            disabled={loading || !url.trim()}
            className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
          >
            获取信息
          </button>
        </div>
      </div>

      {/* 视频信息显示 */}
      {videoInfo && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">📹 视频信息</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div><strong>标题:</strong> {videoInfo.title}</div>
              <div><strong>作者:</strong> {videoInfo.uploader}</div>
              <div><strong>时长:</strong> {formatDuration(videoInfo.duration)}</div>
            </div>
            <div className="space-y-2">
              <div><strong>观看次数:</strong> {formatViewCount(videoInfo.view_count || 0)}</div>
              <div><strong>现有字幕:</strong> {videoInfo.has_subtitles ? '有' : '无'}</div>
              <div><strong>上传日期:</strong> {videoInfo.upload_date || 'N/A'}</div>
            </div>
          </div>
          
          {videoInfo.available_subtitles.length > 0 && (
            <div className="mt-4">
              <strong>可用字幕语言:</strong>
              <div className="flex flex-wrap gap-1 mt-1">
                {videoInfo.available_subtitles.map(lang => (
                  <span key={lang} className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                    {lang}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {videoInfo.automatic_captions.length > 0 && (
            <div className="mt-2">
              <strong>自动字幕语言:</strong>
              <div className="flex flex-wrap gap-1 mt-1">
                {videoInfo.automatic_captions.map(lang => (
                  <span key={lang} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                    {lang}
                  </span>
                ))}
              </div>
            </div>
          )}

          {videoInfo.description && (
            <div className="mt-4">
              <strong>描述:</strong>
              <p className="text-sm text-gray-600 mt-1">{videoInfo.description}</p>
            </div>
          )}
        </div>
      )}

      {/* 下载配置 */}
      {videoInfo && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">⚙️ 下载配置</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                字幕语言
              </label>
              <div className="space-y-2">
                {['zh-CN', 'zh', 'en', 'ja', 'ko', 'es', 'fr'].map(lang => (
                  <label key={lang} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={languages.includes(lang)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setLanguages([...languages, lang]);
                        } else {
                          setLanguages(languages.filter(l => l !== lang));
                        }
                      }}
                      className="mr-2"
                    />
                    <span className="text-sm">{lang}</span>
                  </label>
                ))}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                输出格式
              </label>
              <div className="space-y-2">
                {['srt', 'vtt', 'txt', 'raw'].map(format => (
                  <label key={format} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formats.includes(format)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFormats([...formats, format]);
                        } else {
                          setFormats(formats.filter(f => f !== format));
                        }
                      }}
                      className="mr-2"
                    />
                    <span className="text-sm">{format.toUpperCase()}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
          
          <div className="mt-4 space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={useAI}
                onChange={(e) => setUseAI(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">启用 AI 字幕生成（无现有字幕时使用 Whisper）</span>
            </label>
            
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={downloadVideo}
                onChange={(e) => setDownloadVideo(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">下载完整视频文件</span>
            </label>
          </div>
          
          <button
            onClick={startDownload}
            disabled={loading || languages.length === 0 || formats.length === 0}
            className="mt-6 w-full py-3 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50 font-semibold"
          >
            🚀 开始下载
          </button>
        </div>
      )}

      {/* 任务进度显示 */}
      {currentTask && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">⏳ 当前任务</h2>
          
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>{currentTask.message}</span>
                <span>{currentTask.progress.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-500 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${currentTask.progress}%` }}
                ></div>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className={`font-semibold px-3 py-1 rounded-full text-sm ${
                currentTask.status === 'completed' ? 'bg-green-100 text-green-800' :
                currentTask.status === 'failed' ? 'bg-red-100 text-red-800' : 
                currentTask.status === 'running' ? 'bg-blue-100 text-blue-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {currentTask.status === 'completed' ? '✅ 已完成' :
                 currentTask.status === 'failed' ? '❌ 失败' :
                 currentTask.status === 'running' ? '🔄 运行中' :
                 currentTask.status === 'cancelled' ? '🚫 已取消' : '⏳ 等待中'}
              </span>
              
              <span className="text-xs text-gray-500">
                #{currentTask.task_id.slice(-8)}
              </span>
            </div>

            {/* 下载结果 */}
            {currentTask.status === 'completed' && currentTask.result && (
              <div className="mt-6">
                <h3 className="font-semibold mb-3">📂 下载结果</h3>
                
                {currentTask.result.existing_subtitles && Object.keys(currentTask.result.existing_subtitles).length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-medium mb-2">现有字幕:</h4>
                    <div className="grid grid-cols-1 gap-2">
                      {Object.entries(currentTask.result.existing_subtitles).map(([lang, file]: [string, any]) => (
                        <button
                          key={lang}
                          onClick={() => downloadFile(file.split('/').pop())}
                          className="flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded border text-left"
                        >
                          <span>📄 {lang} 字幕</span>
                          <span className="text-xs text-gray-500">点击下载</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                
                {currentTask.result.ai_subtitles && (
                  <div className="mb-4">
                    <h4 className="font-medium mb-2">
                      🤖 AI 生成字幕 ({currentTask.result.ai_subtitles.language}):
                    </h4>
                    <div className="grid grid-cols-1 gap-2">
                      {Object.entries(currentTask.result.ai_subtitles.formats).map(([format, file]: [string, any]) => (
                        <button
                          key={format}
                          onClick={() => downloadFile(file.split('/').pop())}
                          className="flex items-center justify-between p-3 bg-blue-50 hover:bg-blue-100 rounded border text-left"
                        >
                          <span>🤖 {format.toUpperCase()} 格式</span>
                          <span className="text-xs text-gray-500">点击下载</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {currentTask.error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                <h4 className="font-medium text-red-800 mb-2">错误信息:</h4>
                <p className="text-red-700 text-sm">{currentTask.error}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-100 py-8">
        <div className="max-w-6xl mx-auto px-4">
          <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">
            🎬 增强版视频字幕下载器
          </h1>
          
          {/* 标签页导航 */}
          <div className="flex justify-center mb-8">
            <div className="bg-white rounded-lg shadow-md p-1 inline-flex">
              <button
                onClick={() => setActiveTab('main')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'main'
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-700 hover:text-blue-500'
                }`}
              >
                🎯 主要功能
              </button>
              <button
                onClick={() => setActiveTab('tasks')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'tasks'
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-700 hover:text-blue-500'
                }`}
              >
                📋 任务管理
              </button>
              <button
                onClick={() => setActiveTab('proxy')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'proxy'
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-700 hover:text-blue-500'
                }`}
              >
                🔒 代理设置
              </button>
              <button
                onClick={() => setActiveTab('stats')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'stats'
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-700 hover:text-blue-500'
                }`}
              >
                📊 系统状态
              </button>
            </div>
          </div>

          {/* 内容区域 */}
          {activeTab === 'main' && renderMainTab()}
          {activeTab === 'tasks' && (
            <TaskList 
              currentTask={currentTask} 
              onTaskSelect={setCurrentTask}
            />
          )}
          {activeTab === 'proxy' && <ProxyManager />}
          {activeTab === 'stats' && <SystemStats />}
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default EnhancedApp;