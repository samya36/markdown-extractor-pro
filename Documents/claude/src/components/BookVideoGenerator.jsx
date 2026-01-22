import React, { useState, useRef } from 'react';
import JSZip from 'jszip';
import { toPng } from 'html-to-image';
import RecordRTC from 'recordrtc';
import './BookVideoGenerator.css';

/**
 * 书籍视频生成器组件
 * 将 EPUB 书籍转换为视频
 */
const BookVideoGenerator = () => {
  const [bookContent, setBookContent] = useState([]);
  const [currentPage, setCurrentPage] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recorder, setRecorder] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [status, setStatus] = useState({ type: 'info', message: '准备就绪' });
  const [settings, setSettings] = useState({
    pageDuration: 5, // 每页显示时间（秒）
    fontSize: 18,
    fontFamily: 'Georgia',
    backgroundColor: '#ffffff',
    textColor: '#333333',
    width: 1920,
    height: 1080,
  });

  const pageRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

      // 加载 EPUB 文件
  const loadEpub = async () => {
    try {
      setIsLoading(true);
      setStatus({ type: 'info', message: '正在加载 EPUB 文件...' });

      const response = await fetch('/Your Future Self.epub');
      if (!response.ok) {
        throw new Error(`HTTP错误: ${response.status}`);
      }
      const arrayBuffer = await response.arrayBuffer();
      const zip = await JSZip.loadAsync(arrayBuffer);

      // 读取 OPF 文件获取书籍结构
      const containerFile = zip.file('META-INF/container.xml');
      if (!containerFile) {
        throw new Error('无法找到 container.xml 文件，EPUB 格式可能不正确');
      }
      const containerXml = await containerFile.async('string');
      const opfMatch = containerXml.match(/full-path="([^"]+)"/);
      if (!opfMatch) {
        throw new Error('无法解析 container.xml 文件');
      }
      const opfPath = opfMatch[1];
      const opfFile = zip.file(opfPath);
      if (!opfFile) {
        throw new Error(`无法找到 OPF 文件: ${opfPath}`);
      }
      const opfContent = await opfFile.async('string');

      // 解析章节
      const manifestMatch = opfContent.match(/<manifest[^>]*>([\s\S]*?)<\/manifest>/);
      const itemRefs = opfContent.match(/<itemref[^>]*idref="([^"]+)"/g) || [];
      
      const chapters = [];
      for (const itemRef of itemRefs) {
        const id = itemRef.match(/idref="([^"]+)"/)[1];
        const itemMatch = opfContent.match(new RegExp(`<item[^>]*id="${id}"[^>]*href="([^"]+)"`));
        if (itemMatch) {
          const href = itemMatch[1];
          const basePath = opfPath.substring(0, opfPath.lastIndexOf('/'));
          const fullPath = basePath ? `${basePath}/${href}` : href;
          
          try {
            const htmlContent = await zip.file(fullPath).async('string');
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlContent, 'text/html');
            
            // 提取文本内容
            const textContent = doc.body.innerText || doc.body.textContent || '';
            if (textContent.trim()) {
              chapters.push({
                id,
                title: doc.querySelector('h1, h2, .title')?.textContent || `章节 ${chapters.length + 1}`,
                content: textContent,
                html: htmlContent,
              });
            }
          } catch (e) {
            console.warn(`无法读取章节 ${id}:`, e);
          }
        }
      }

      if (chapters.length === 0) {
        // 如果无法解析，尝试直接读取所有 HTML 文件
        const htmlFiles = Object.keys(zip.files).filter(name => name.endsWith('.html') || name.endsWith('.xhtml'));
        for (const fileName of htmlFiles) {
          try {
            const htmlContent = await zip.file(fileName).async('string');
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlContent, 'text/html');
            const textContent = doc.body.innerText || doc.body.textContent || '';
            if (textContent.trim()) {
              chapters.push({
                id: fileName,
                title: doc.querySelector('h1, h2, .title')?.textContent || `章节 ${chapters.length + 1}`,
                content: textContent,
                html: htmlContent,
              });
            }
          } catch (e) {
            console.warn(`无法读取文件 ${fileName}:`, e);
          }
        }
      }

      // 将内容分页
      const pages = [];
      chapters.forEach((chapter, chapterIndex) => {
        const paragraphs = chapter.content.split(/\n\n+/).filter(p => p.trim());
        let currentPageText = '';
        let pageNumber = pages.length + 1;

        paragraphs.forEach((paragraph, paraIndex) => {
          if (currentPageText.length + paragraph.length > 1500) {
            // 当前页已满，创建新页
            if (currentPageText.trim()) {
              pages.push({
                pageNumber: pageNumber++,
                chapterTitle: chapter.title,
                content: currentPageText.trim(),
                chapterIndex,
              });
            }
            currentPageText = paragraph + '\n\n';
          } else {
            currentPageText += paragraph + '\n\n';
          }
        });

        // 添加最后一页
        if (currentPageText.trim()) {
          pages.push({
            pageNumber: pageNumber++,
            chapterTitle: chapter.title,
            content: currentPageText.trim(),
            chapterIndex,
          });
        }
      });

      setBookContent(pages);
      setCurrentPage(0);
      setStatus({ 
        type: 'success', 
        message: `成功加载书籍！共 ${pages.length} 页，${chapters.length} 个章节` 
      });
    } catch (error) {
      console.error('加载 EPUB 失败:', error);
      setStatus({ 
        type: 'error', 
        message: `加载失败: ${error.message}. 请确保 EPUB 文件在 public 目录下。` 
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 格式化页面内容
  const formatPageContent = (page) => {
    if (!page) return '';
    const paragraphs = page.content.split(/\n\n+/).filter(p => p.trim());
    return paragraphs.map((para, index) => (
      <p key={index} className="book-paragraph">{para}</p>
    ));
  };

  // 开始录制视频
  const startRecording = async () => {
    try {
      setStatus({ type: 'info', message: '正在准备录制...' });

      // 创建 canvas 用于录制
      const canvas = document.createElement('canvas');
      canvas.width = settings.width;
      canvas.height = settings.height;
      const ctx = canvas.getContext('2d');

      // 创建 MediaStream
      const stream = canvas.captureStream(30); // 30 FPS
      streamRef.current = stream;

      // 创建录制器
      const newRecorder = new RecordRTC(stream, {
        type: 'video',
        mimeType: 'video/webm;codecs=vp9',
        videoBitsPerSecond: 2500000,
      });

      setRecorder(newRecorder);
      setIsRecording(true);
      setStatus({ type: 'info', message: '开始录制...' });

      // 开始录制
      newRecorder.startRecording();

      // 逐页渲染并录制
      for (let i = 0; i < bookContent.length; i++) {
        setCurrentPage(i);
        await new Promise(resolve => setTimeout(resolve, 100)); // 等待页面更新

        // 渲染当前页到 canvas
        if (pageRef.current) {
          const dataUrl = await toPng(pageRef.current, {
            width: settings.width,
            height: settings.height,
            backgroundColor: settings.backgroundColor,
            style: {
              transform: 'scale(1)',
            },
          });

          const img = new Image();
          await new Promise((resolve) => {
            img.onload = () => {
              ctx.fillStyle = settings.backgroundColor;
              ctx.fillRect(0, 0, canvas.width, canvas.height);
              ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
              resolve();
            };
            img.src = dataUrl;
          });
        }

        // 等待指定时间
        await new Promise(resolve => setTimeout(resolve, settings.pageDuration * 1000));
      }

      // 停止录制
      newRecorder.stopRecording(() => {
        const blob = newRecorder.getBlob();
        const url = URL.createObjectURL(blob);
        setVideoUrl(url);
        setIsRecording(false);
        setStatus({ 
          type: 'success', 
          message: '录制完成！视频已生成。' 
        });
      });
    } catch (error) {
      console.error('录制失败:', error);
      setStatus({ type: 'error', message: `录制失败: ${error.message}` });
      setIsRecording(false);
    }
  };

  // 停止录制
  const stopRecording = () => {
    if (recorder) {
      recorder.stopRecording(() => {
        const blob = recorder.getBlob();
        const url = URL.createObjectURL(blob);
        setVideoUrl(url);
        setIsRecording(false);
        setStatus({ type: 'success', message: '录制已停止' });
      });
    }
  };

  // 下载视频
  const downloadVideo = () => {
    if (videoUrl) {
      const a = document.createElement('a');
      a.href = videoUrl;
      a.download = 'Your Future Self - Book Video.webm';
      a.click();
    }
  };

  // 上一页
  const previousPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
    }
  };

  // 下一页
  const nextPage = () => {
    if (currentPage < bookContent.length - 1) {
      setCurrentPage(currentPage + 1);
    }
  };

  const currentPageData = bookContent[currentPage];
  const progress = bookContent.length > 0 ? ((currentPage + 1) / bookContent.length) * 100 : 0;

  return (
    <div className="book-video-container">
      <h2>📚 书籍视频生成器</h2>

      {/* 状态消息 */}
      {status.message && (
        <div className={`status-message ${status.type}`}>
          {status.message}
        </div>
      )}

      {/* 视频设置 */}
      <div className="video-settings">
        <h3>视频设置</h3>
        <div className="settings-row">
          <label>每页时长（秒）:</label>
          <input
            type="number"
            value={settings.pageDuration}
            onChange={(e) => setSettings({ ...settings, pageDuration: parseFloat(e.target.value) })}
            min="1"
            max="30"
            step="0.5"
            disabled={isRecording}
          />
        </div>
        <div className="settings-row">
          <label>视频宽度:</label>
          <input
            type="number"
            value={settings.width}
            onChange={(e) => setSettings({ ...settings, width: parseInt(e.target.value) })}
            min="640"
            max="3840"
            disabled={isRecording}
          />
        </div>
        <div className="settings-row">
          <label>视频高度:</label>
          <input
            type="number"
            value={settings.height}
            onChange={(e) => setSettings({ ...settings, height: parseInt(e.target.value) })}
            min="480"
            max="2160"
            disabled={isRecording}
          />
        </div>
        <div className="settings-row">
          <label>字体大小:</label>
          <input
            type="number"
            value={settings.fontSize}
            onChange={(e) => setSettings({ ...settings, fontSize: parseInt(e.target.value) })}
            min="12"
            max="32"
            disabled={isRecording}
          />
        </div>
      </div>

      {/* 控制按钮 */}
      <div className="book-video-controls">
        <button onClick={loadEpub} disabled={isLoading || isRecording}>
          {isLoading ? <span className="loading-spinner"></span> : '📖'} 加载书籍
        </button>
        <button 
          onClick={startRecording} 
          disabled={bookContent.length === 0 || isRecording || isLoading}
          className={isRecording ? 'recording' : ''}
        >
          {isRecording ? '🔴' : '🎬'} {isRecording ? '录制中...' : '开始录制视频'}
        </button>
        {isRecording && (
          <button onClick={stopRecording}>
            ⏹ 停止录制
          </button>
        )}
        {videoUrl && (
          <button onClick={downloadVideo}>
            💾 下载视频
          </button>
        )}
        <button onClick={previousPage} disabled={currentPage === 0 || isRecording}>
          ⬅ 上一页
        </button>
        <button onClick={nextPage} disabled={currentPage >= bookContent.length - 1 || isRecording}>
          下一页 ➡
        </button>
      </div>

      {/* 进度条 */}
      {bookContent.length > 0 && (
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>
      )}

      {/* 书籍阅读器 */}
      <div className="book-reader">
        <div 
          ref={pageRef}
          className="book-page"
          style={{
            fontSize: `${settings.fontSize}px`,
            fontFamily: settings.fontFamily,
            color: settings.textColor,
            backgroundColor: settings.backgroundColor,
          }}
        >
          {currentPageData ? (
            <>
              {currentPage === 0 && (
                <div className="book-title">Your Future Self</div>
              )}
              {currentPageData.chapterTitle && (
                <div className="book-chapter">{currentPageData.chapterTitle}</div>
              )}
              <div className="book-content">
                {formatPageContent(currentPageData)}
              </div>
              <div className="book-page-number">
                第 {currentPageData.pageNumber} 页 / 共 {bookContent.length} 页
              </div>
            </>
          ) : (
            <div className="book-content" style={{ textAlign: 'center', paddingTop: '200px' }}>
              {bookContent.length === 0 
                ? '请点击"加载书籍"按钮开始' 
                : '加载中...'}
            </div>
          )}
        </div>
      </div>

      {/* 视频预览 */}
      {videoUrl && (
        <div className="video-preview">
          <h3>视频预览</h3>
          <video controls src={videoUrl} style={{ width: '100%', maxWidth: '800px' }}></video>
        </div>
      )}

      <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
    </div>
  );
};

export default BookVideoGenerator;
