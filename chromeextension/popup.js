// Popup script for controlling the extension

document.addEventListener('DOMContentLoaded', async () => {
    // 获取当前标签页信息
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const currentUrl = document.getElementById('currentUrl');
    currentUrl.textContent = new URL(tab.url).hostname;
    
    // 从存储中加载设置
    const settings = await loadSettings();
    applySettings(settings);
    
    // 元素引用
    const extractBtn = document.getElementById('extractBtn');
    const previewSection = document.getElementById('previewSection');
    const markdownPreview = document.getElementById('markdownPreview');
    const actionButtons = document.getElementById('actionButtons');
    const copyBtn = document.getElementById('copyBtn');
    const saveBtn = document.getElementById('saveBtn');
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsPanel = document.getElementById('settingsPanel');
    const statusText = document.getElementById('statusText');
    const statusStats = document.getElementById('statusStats');
    const wordCount = document.getElementById('wordCount');
    const imageCount = document.getElementById('imageCount');
    
    let currentMarkdown = '';
    let currentStats = null;
    let currentImages = [];
    
    // 获取提取模式
    function getExtractionMode() {
        return document.querySelector('input[name="mode"]:checked').value;
    }
    
    // 检测是否为知识星球页面并显示批量模式
    if (tab.url.includes('zsxq.com')) {
        // 显示知识星球批量模式选项
        const zsxqModeHtml = `
            <label class="mode-option zsxq-mode" title="专门针对知识星球设计，批量提取目标栏目的所有文章">
                <input type="radio" name="mode" value="zsxq-batch">
                <div class="mode-content">
                    <div class="mode-title">🚀 知识星球批量提取</div>
                    <div class="mode-desc">自动提取目标栏目所有文章内容</div>
                    <div class="mode-targets">目标: 人工智能写作、佳作共赏、外语学习、好物分享</div>
                </div>
            </label>
        `;
        
        const modeSelection = document.querySelector('.mode-selection');
        if (modeSelection) {
            modeSelection.insertAdjacentHTML('beforeend', zsxqModeHtml);
        }
    }
    
    // 提取内容
    extractBtn.addEventListener('click', async () => {
        const mode = getExtractionMode();
        extractBtn.disabled = true;
        extractBtn.classList.add('loading');
        statusText.textContent = '正在提取内容...';
        
        try {
            const options = getOptions();
            
            if (mode === 'current') {
                // 仅提取当前页面
                await extractCurrentPage(options);
            } else if (mode === 'smart') {
                // 智能识别模式
                await extractSmartMode(options);
            } else if (mode === 'deep') {
                // 深度提取模式
                await extractDeepMode(options);
            } else if (mode === 'zsxq-batch') {
                // 知识星球批量提取模式
                await extractZsxqBatchMode(options);
            }
        } catch (error) {
            console.error('提取错误:', error);
            statusText.textContent = '❌ 提取失败，请刷新页面重试';
        } finally {
            extractBtn.disabled = false;
            extractBtn.classList.remove('loading');
        }
        
        // 更新按钮文本
        updateExtractButtonText();
    });
    
    // 更新提取按钮文本
    function updateExtractButtonText() {
        const mode = getExtractionMode();
        const buttonText = {
            'current': '提取当前页面',
            'smart': '智能识别',
            'deep': '深度提取',
            'zsxq-batch': '批量提取知识星球'
        };
        
        const extractBtn = document.getElementById('extractBtn');
        extractBtn.textContent = buttonText[mode] || '提取内容';
    }
    
    // 监听模式切换
    document.addEventListener('change', (e) => {
        if (e.target.name === 'mode') {
            updateExtractButtonText();
        }
    });
    
    // 提取当前页面
    async function extractCurrentPage(options) {
        const response = await chrome.tabs.sendMessage(tab.id, {
            action: 'extract',
            options: options
        });
        
        if (response.success) {
            currentMarkdown = response.data.markdown;
            currentStats = response.data.stats;
            currentImages = response.data.images || [];
            
            displayResults();
            statusText.textContent = '✅ 提取成功！';
        } else {
            statusText.textContent = '❌ 提取失败: ' + response.error;
        }
    }
    
    // 智能识别模式
    async function extractSmartMode(options) {
        try {
            // 先检测页面布局
            statusText.textContent = '正在检测页面结构...';
            const layoutResponse = await chrome.tabs.sendMessage(tab.id, {
                action: 'detect-layout'
            });
            
            if (!layoutResponse || !layoutResponse.success) {
                statusText.textContent = '❌ 页面结构检测失败: ' + (layoutResponse?.error || '未知错误');
                return;
            }
            
            const layout = layoutResponse.data;
            console.log('检测到的页面布局:', layout);
            
            // 显示检测到的结构
            displayDetectedLayout(layout);
            
            // 提取带链接的内容
            statusText.textContent = '正在提取页面内容和链接...';
            const response = await chrome.tabs.sendMessage(tab.id, {
                action: 'extract-with-links',
                options: options
            });
            
            if (!response || !response.success) {
                statusText.textContent = '❌ 内容提取失败: ' + (response?.error || '未知错误');
                return;
            }
            
            const { currentPage, deepLinks } = response.data;
            console.log(`当前页面提取成功，发现 ${deepLinks?.length || 0} 个深度链接`);
            
            // 如果有需要深度提取的链接
            if (deepLinks && deepLinks.length > 0) {
                statusText.textContent = `检测到 ${deepLinks.length} 个链接，准备深度提取...`;
                
                // 询问用户是否继续
                if (confirm(`检测到 ${deepLinks.length} 个需要深度提取的链接，是否继续？\n\n注意：这可能需要较长时间。`)) {
                    await performDeepExtraction(deepLinks, currentPage, options);
                } else {
                    // 仅显示当前页面内容
                    currentMarkdown = currentPage.markdown;
                    currentStats = currentPage.stats;
                    currentImages = currentPage.images || [];
                    displayResults();
                    statusText.textContent = '✅ 当前页面提取成功！';
                }
            } else {
                // 没有深度链接，显示当前页面
                currentMarkdown = currentPage.markdown;
                currentStats = currentPage.stats;
                currentImages = currentPage.images || [];
                displayResults();
                statusText.textContent = '✅ 提取成功！';
            }
        } catch (error) {
            console.error('智能识别模式错误:', error);
            statusText.textContent = '❌ 智能识别失败: ' + error.message;
        }
    }
    
    // 深度提取模式
    async function extractDeepMode(options) {
        try {
            statusText.textContent = '正在扫描页面中的所有链接...';
            const response = await chrome.tabs.sendMessage(tab.id, {
                action: 'extract-with-links',
                options: options
            });
            
            if (!response || !response.success) {
                statusText.textContent = '❌ 深度扫描失败: ' + (response?.error || '未知错误');
                return;
            }
            
            const { currentPage, deepLinks } = response.data;
            console.log(`深度模式: 当前页面提取成功，发现 ${deepLinks?.length || 0} 个链接`);
            
            if (deepLinks && deepLinks.length > 0) {
                statusText.textContent = `发现 ${deepLinks.length} 个链接，开始深度提取...`;
                await performDeepExtraction(deepLinks, currentPage, options);
            } else {
                currentMarkdown = currentPage.markdown;
                currentStats = currentPage.stats;
                currentImages = currentPage.images || [];
                displayResults();
                statusText.textContent = '✅ 当前页面提取成功（未发现可提取链接）！';
            }
        } catch (error) {
            console.error('深度提取模式错误:', error);
            statusText.textContent = '❌ 深度提取失败: ' + error.message;
        }
    }
    
    // 知识星球批量提取模式
    async function extractZsxqBatchMode(options) {
        try {
            // 检查是否为知识星球页面
            if (!tab.url.includes('zsxq.com')) {
                statusText.textContent = '❌ 请在知识星球页面使用此功能';
                return;
            }
            
            statusText.textContent = '正在检测知识星球栏目结构...';
            
            // 提取知识星球栏目信息
            const response = await chrome.tabs.sendMessage(tab.id, {
                action: 'extract-zsxq-columns',
                options: options
            });
            
            if (!response || !response.success) {
                statusText.textContent = '❌ 知识星球栏目检测失败: ' + (response?.error || '未知错误');
                return;
            }
            
            const { columns, totalColumns } = response.data;
            console.log(`检测到 ${totalColumns} 个目标栏目:`, columns.map(c => `${c.title}(${c.articleCount}篇)`).join(', '));
            
            if (totalColumns === 0) {
                statusText.textContent = '❌ 未检测到目标栏目（人工智能写作、佳作共赏、外语学习、好物分享）';
                return;
            }
            
            // 计算总文章数
            const totalArticles = columns.reduce((sum, col) => sum + col.articleCount, 0);
            
            // 显示检测结果并询问用户是否继续
            const confirmMessage = `检测到以下栏目:\n\n${columns.map(col => 
                `• ${col.title}: ${col.articleCount}篇文章`
            ).join('\n')}\n\n总计: ${totalArticles}篇文章\n\n这将花费较长时间（预计${Math.ceil(totalArticles * 3 / 60)}分钟），是否继续批量提取？`;
            
            if (!confirm(confirmMessage)) {
                statusText.textContent = 'ℹ️ 用户取消了批量提取操作';
                return;
            }
            
            // 开始批量提取
            await performZsxqBatchExtraction(columns, options, totalArticles);
            
        } catch (error) {
            console.error('知识星球批量提取错误:', error);
            statusText.textContent = '❌ 批量提取失败: ' + error.message;
        }
    }
    
    // 执行知识星球批量提取
    async function performZsxqBatchExtraction(columns, options, totalArticles) {
        const imageProgress = document.getElementById('imageProgress');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        // 显示进度
        imageProgress.style.display = 'block';
        document.querySelector('.progress-title').textContent = '批量提取进度';
        
        // 重置进度条
        progressFill.style.width = '0%';
        progressText.textContent = `0 / ${totalArticles}`;
        statusText.textContent = '正在准备批量提取...';
        
        // 定义进度监听器
        const progressListener = (message, sender, sendResponse) => {
            if (message.type === 'zsxq-extraction-progress') {
                const percentage = message.data.percentage;
                const processed = message.data.processed;
                const total = message.data.total;
                
                progressFill.style.width = `${percentage}%`;
                progressText.textContent = `${processed} / ${total}`;
                statusText.textContent = `正在提取文章: ${processed}/${total} (${percentage}%)`;
                
                if (processed === total) {
                    chrome.runtime.onMessage.removeListener(progressListener);
                }
            }
        };
        
        // 添加进度监听器
        chrome.runtime.onMessage.addListener(progressListener);
        
        try {
            // 使用background script进行批量提取
            chrome.runtime.sendMessage({
                action: 'start-zsxq-batch-extraction',
                columns: columns,
                options: options
            }, (response) => {
                // 移除监听器
                chrome.runtime.onMessage.removeListener(progressListener);
                
                if (chrome.runtime.lastError) {
                    console.error('批量提取消息发送失败:', chrome.runtime.lastError);
                    statusText.textContent = '❌ 批量提取启动失败';
                    imageProgress.style.display = 'none';
                    return;
                }
                
                if (response && response.success) {
                    currentMarkdown = response.data.markdown;
                    currentStats = response.data.stats;
                    currentImages = [];
                    
                    displayResults();
                    
                    // 显示成功信息
                    const stats = response.data.stats;
                    statusText.textContent = `✅ 批量提取完成！成功 ${stats.successCount}/${totalArticles} 篇 (成功率 ${stats.successRate}%)`;
                    
                    // 显示详细统计
                    displayZsxqExtractionStats(response.data);
                    
                    // 隐藏进度条
                    setTimeout(() => {
                        imageProgress.style.display = 'none';
                    }, 3000);
                } else {
                    statusText.textContent = '❌ 批量提取失败: ' + (response?.error || '未知错误');
                    imageProgress.style.display = 'none';
                }
            });
        } catch (error) {
            chrome.runtime.onMessage.removeListener(progressListener);
            console.error('批量提取异常:', error);
            statusText.textContent = '❌ 批量提取出现异常';
            imageProgress.style.display = 'none';
        }
    }
    
    // 显示知识星球提取统计
    function displayZsxqExtractionStats(data) {
        // 创建统计信息元素
        const statsDiv = document.createElement('div');
        statsDiv.className = 'zsxq-stats';
        statsDiv.innerHTML = `
            <div class="stats-title">提取统计报告</div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${data.stats.successCount}</div>
                    <div class="stat-label">成功</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.stats.failedCount}</div>
                    <div class="stat-label">失败</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.stats.successRate}%</div>
                    <div class="stat-label">成功率</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${(data.stats.wordCount / 1000).toFixed(1)}k</div>
                    <div class="stat-label">字数</div>
                </div>
            </div>
            <div class="columns-summary">
                ${data.columns.map(col => 
                    `<div class="column-stat">${col.title}: ${col.extractedArticles.length}/${col.totalArticles}篇</div>`
                ).join('')}
            </div>
        `;
        
        // 插入到预览区域上方
        const previewSection = document.getElementById('previewSection');
        const existingStats = document.querySelector('.zsxq-stats');
        if (existingStats) {
            existingStats.remove();
        }
        previewSection.insertBefore(statsDiv, previewSection.firstChild);
    }
    
    // 执行深度提取
    async function performDeepExtraction(links, currentPage, options) {
        const imageProgress = document.getElementById('imageProgress');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        // 显示进度
        imageProgress.style.display = 'block';
        document.querySelector('.progress-title').textContent = '页面提取进度';
        
        // 重置进度条
        progressFill.style.width = '0%';
        progressText.textContent = `0 / ${links.length}`;
        statusText.textContent = '正在准备批量提取...';
        
        // 定义进度监听器
        const progressListener = (message, sender, sendResponse) => {
            if (message.type === 'extraction-progress') {
                progressFill.style.width = `${message.data.percentage}%`;
                progressText.textContent = `${message.data.processed} / ${message.data.total}`;
                statusText.textContent = `正在提取页面: ${message.data.processed}/${message.data.total}`;
                
                if (message.data.processed === message.data.total) {
                    chrome.runtime.onMessage.removeListener(progressListener);
                }
            }
        };
        
        // 添加进度监听器
        chrome.runtime.onMessage.addListener(progressListener);
        
        try {
            // 使用background script进行多页面提取
            chrome.runtime.sendMessage({
                action: 'start-multi-extraction',
                urls: links,
                options: options
            }, (response) => {
                // 移除监听器
                chrome.runtime.onMessage.removeListener(progressListener);
                
                if (chrome.runtime.lastError) {
                    console.error('批量提取消息发送失败:', chrome.runtime.lastError);
                    statusText.textContent = '❌ 批量提取启动失败';
                    imageProgress.style.display = 'none';
                    return;
                }
                
                if (response && response.success) {
                    // 合并当前页面和提取的内容
                    const mergedContent = mergeAllContent(currentPage, response.data);
                    
                    currentMarkdown = mergedContent.markdown;
                    currentStats = mergedContent.stats;
                    currentImages = mergedContent.images;
                    
                    displayResults();
                    statusText.textContent = `✅ 成功提取 ${links.length + 1} 个页面！`;
                    
                    // 隐藏进度条
                    setTimeout(() => {
                        imageProgress.style.display = 'none';
                    }, 2000);
                } else {
                    statusText.textContent = '❌ 深度提取失败: ' + (response?.error || '未知错误');
                    imageProgress.style.display = 'none';
                }
            });
        } catch (error) {
            chrome.runtime.onMessage.removeListener(progressListener);
            console.error('批量提取异常:', error);
            statusText.textContent = '❌ 批量提取出现异常';
            imageProgress.style.display = 'none';
        }
    }
    
    // 显示检测到的布局
    function displayDetectedLayout(layout) {
        const detectedLayout = document.getElementById('detectedLayout');
        const layoutInfo = document.getElementById('layoutInfo');
        const linksPreview = document.getElementById('linksPreview');
        
        let infoText = '';
        let linksHtml = '';
        
        if (layout.hasColumns) {
            infoText += `检测到 ${layout.columns.length} 个专栏<br>`;
            layout.columns.forEach(column => {
                if (column.links.length > 0) {
                    column.links.slice(0, 5).forEach(link => {
                        linksHtml += `
                            <div class="link-item">
                                <span class="link-title">${link.title}</span>
                                <span class="link-badge">${link.needsDeepExtraction ? '需深度提取' : '已有内容'}</span>
                            </div>
                        `;
                    });
                }
            });
        }
        
        if (layout.hasArticleList) {
            infoText += `检测到 ${layout.articleLinks.length} 篇文章链接<br>`;
            layout.articleLinks.slice(0, 5).forEach(link => {
                linksHtml += `
                    <div class="link-item">
                        <span class="link-title">${link.title}</span>
                        <span class="link-badge">文章</span>
                    </div>
                `;
            });
        }
        
        if (infoText) {
            layoutInfo.innerHTML = infoText;
            linksPreview.innerHTML = linksHtml;
            detectedLayout.style.display = 'block';
        }
    }
    
    // 合并所有内容
    function mergeAllContent(currentPage, extractedData) {
        let markdown = `# ${document.title}\n\n`;
        markdown += `## 主页面内容\n\n`;
        markdown += currentPage.markdown + '\n\n';
        markdown += extractedData.markdown;
        
        return {
            markdown: markdown,
            stats: {
                wordCount: currentPage.stats.wordCount + extractedData.stats.wordCount,
                imageCount: currentPage.stats.imageCount + extractedData.stats.imageCount
            },
            images: (currentPage.images || []).concat(extractedData.images || [])
        };
    }
    
    // 显示结果
    function displayResults() {
        // 显示预览
        markdownPreview.textContent = currentMarkdown;
        previewSection.style.display = 'block';
        actionButtons.style.display = 'flex';
        
        // 更新统计
        wordCount.textContent = currentStats.wordCount?.toLocaleString() || 0;
        imageCount.textContent = currentStats.imageCount || 0;
        statusStats.style.display = 'flex';
        
        // 自动滚动到预览区域
        previewSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    // 复制到剪贴板
    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(currentMarkdown);
            
            // 显示复制成功动画
            copyBtn.classList.add('success');
            const originalText = copyBtn.querySelector('span:last-child').textContent;
            copyBtn.querySelector('span:last-child').textContent = '已复制!';
            statusText.textContent = '✅ 已复制到剪贴板';
            
            setTimeout(() => {
                copyBtn.classList.remove('success');
                copyBtn.querySelector('span:last-child').textContent = originalText;
            }, 2000);
        } catch (error) {
            console.error('复制失败:', error);
            statusText.textContent = '❌ 复制失败';
        }
    });
    
    // 保存为文件
    saveBtn.addEventListener('click', async () => {
        const saveWithImages = document.getElementById('saveImages')?.checked ?? false;
        
        if (saveWithImages && currentImages.length > 0) {
            // 保存带图片的版本
            await saveWithImagesHandler();
        } else {
            // 仅保存Markdown
            const filename = generateFilename();
            const blob = new Blob([currentMarkdown], { type: 'text/markdown;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            
            URL.revokeObjectURL(url);
            
            // 显示保存成功动画
            saveBtn.classList.add('success');
            const originalText = saveBtn.querySelector('span:last-child').textContent;
            saveBtn.querySelector('span:last-child').textContent = '已保存!';
            statusText.textContent = `✅ 已保存为 ${filename}`;
            
            setTimeout(() => {
                saveBtn.classList.remove('success');
                saveBtn.querySelector('span:last-child').textContent = originalText;
            }, 2000);
        }
    });
    
    // 保存带图片的处理函数
    async function saveWithImagesHandler() {
        const folderName = generateFolderName();
        let processedMarkdown = currentMarkdown;
        let downloadedCount = 0;
        
        // 显示进度条
        const imageProgress = document.getElementById('imageProgress');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        imageProgress.style.display = 'block';
        progressText.textContent = `0 / ${currentImages.length}`;
        statusText.textContent = `正在下载图片...`;
        
        // 创建图片文件夹名
        const imageFolder = `images`;
        
        // 下载所有图片
        for (let i = 0; i < currentImages.length; i++) {
            const image = currentImages[i];
            try {
                // 使用Chrome Downloads API下载图片
                const downloadId = await chrome.downloads.download({
                    url: image.url,
                    filename: `${folderName}/${imageFolder}/${image.filename}`,
                    saveAs: false,
                    conflictAction: 'uniquify'
                });
                
                // 替换Markdown中的图片路径
                processedMarkdown = processedMarkdown.replace(
                    image.url,
                    `./${imageFolder}/${image.filename}`
                );
                
                downloadedCount++;
                
                // 更新进度
                const progress = ((downloadedCount / currentImages.length) * 100).toFixed(0);
                progressFill.style.width = `${progress}%`;
                progressText.textContent = `${downloadedCount} / ${currentImages.length}`;
                statusText.textContent = `正在下载图片: ${downloadedCount}/${currentImages.length}`;
            } catch (error) {
                console.error('下载图片失败:', image.url, error);
            }
        }
        
        // 保存处理后的Markdown文件
        const mdFilename = `${folderName}/${folderName}.md`;
        const blob = new Blob([processedMarkdown], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        
        await chrome.downloads.download({
            url: url,
            filename: mdFilename,
            saveAs: false,
            conflictAction: 'uniquify'
        });
        
        URL.revokeObjectURL(url);
        
        // 隐藏进度条
        setTimeout(() => {
            imageProgress.style.display = 'none';
            progressFill.style.width = '0%';
        }, 2000);
        
        statusText.textContent = `✅ 已保存Markdown和${downloadedCount}张图片到 ${folderName} 文件夹`;
    }
    
    // 切换设置面板
    settingsBtn.addEventListener('click', () => {
        const isVisible = settingsPanel.style.display !== 'none';
        settingsPanel.style.display = isVisible ? 'none' : 'block';
        settingsBtn.classList.toggle('active', !isVisible);
        
        if (!isVisible) {
            settingsPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    });
    
    // 保存设置
    document.querySelectorAll('.option-item input').forEach(input => {
        input.addEventListener('change', async () => {
            const options = getOptions();
            await saveSettings(options);
            statusText.textContent = '⚙️ 设置已保存';
        });
    });
    
    // 获取当前选项
    function getOptions() {
        return {
            preserveStyle: document.getElementById('preserveStyle').checked,
            extractImages: document.getElementById('extractImages').checked,
            cleanAds: document.getElementById('cleanAds').checked,
            preserveTables: document.getElementById('preserveTables').checked,
            includeCodeHighlight: document.getElementById('includeCodeHighlight').checked
        };
    }
    
    // 应用设置
    function applySettings(settings) {
        document.getElementById('preserveStyle').checked = settings.preserveStyle ?? true;
        document.getElementById('extractImages').checked = settings.extractImages ?? true;
        document.getElementById('cleanAds').checked = settings.cleanAds ?? true;
        document.getElementById('preserveTables').checked = settings.preserveTables ?? true;
        document.getElementById('includeCodeHighlight').checked = settings.includeCodeHighlight ?? true;
    }
    
    // 保存设置到存储
    async function saveSettings(settings) {
        return chrome.storage.local.set({ markdownExtractorSettings: settings });
    }
    
    // 从存储加载设置
    async function loadSettings() {
        const result = await chrome.storage.local.get('markdownExtractorSettings');
        return result.markdownExtractorSettings || {};
    }
    
    // 生成文件名
    function generateFilename() {
        const date = new Date();
        const dateStr = date.toISOString().split('T')[0];
        const timeStr = date.toTimeString().split(' ')[0].replace(/:/g, '-');
        const hostname = document.getElementById('currentUrl').textContent;
        const cleanHostname = hostname.replace(/[^a-z0-9]/gi, '_');
        
        return `${cleanHostname}_${dateStr}_${timeStr}.md`;
    }
    
    // 生成文件夹名
    function generateFolderName() {
        const date = new Date();
        const dateStr = date.toISOString().split('T')[0];
        const timeStr = date.toTimeString().split(' ')[0].replace(/:/g, '-');
        const hostname = document.getElementById('currentUrl').textContent;
        const cleanHostname = hostname.replace(/[^a-z0-9]/gi, '_');
        
        return `${cleanHostname}_${dateStr}_${timeStr}`;
    }
    
    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter: 提取
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            extractBtn.click();
        }
        // Ctrl/Cmd + C: 复制（当有内容时）
        else if ((e.ctrlKey || e.metaKey) && e.key === 'c' && currentMarkdown) {
            copyBtn.click();
        }
        // Ctrl/Cmd + S: 保存（当有内容时）
        else if ((e.ctrlKey || e.metaKey) && e.key === 's' && currentMarkdown) {
            e.preventDefault();
            saveBtn.click();
        }
    });
});