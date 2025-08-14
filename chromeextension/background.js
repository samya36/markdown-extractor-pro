// Background script for handling multi-page extraction

class MultiPageExtractor {
    constructor() {
        this.extractionQueue = [];
        this.extractedContent = [];
        this.currentExtraction = null;
        this.totalPages = 0;
        this.processedPages = 0;
    }
    
    // 开始多页面提取
    async startExtraction(urls, options) {
        this.extractionQueue = urls;
        this.extractedContent = [];
        this.totalPages = urls.length;
        this.processedPages = 0;
        this.currentExtraction = {
            startTime: Date.now(),
            options: options
        };
        
        console.log(`开始批量提取 ${urls.length} 个页面`);
        
        // 逐个处理URL，即使某些失败也继续
        for (const urlInfo of urls) {
            try {
                await this.extractFromUrl(urlInfo);
            } catch (error) {
                console.error(`提取页面失败: ${urlInfo.url}`, error);
                // 即使失败也要更新进度
                this.processedPages++;
                this.sendProgressUpdate();
            }
        }
        
        console.log(`批量提取完成，成功提取 ${this.extractedContent.length}/${urls.length} 个页面`);
        return this.mergeContent();
    }
    
    // 从单个URL提取内容
    async extractFromUrl(urlInfo) {
        return new Promise((resolve, reject) => {
            const timeoutId = setTimeout(() => {
                reject(new Error(`页面 ${urlInfo.url} 提取超时`));
            }, 30000); // 30秒超时
            
            chrome.tabs.create({ 
                url: urlInfo.url, 
                active: false 
            }, (tab) => {
                if (!tab) {
                    clearTimeout(timeoutId);
                    reject(new Error(`无法创建标签页: ${urlInfo.url}`));
                    return;
                }
                
                // 等待页面加载完成
                const listener = (tabId, info) => {
                    if (tabId === tab.id && info.status === 'complete') {
                        chrome.tabs.onUpdated.removeListener(listener);
                        clearTimeout(timeoutId);
                        
                        // 给页面一点时间完全渲染
                        setTimeout(() => {
                            // 注入content script并提取内容
                            chrome.tabs.sendMessage(tab.id, {
                                action: 'extract',
                                options: this.currentExtraction.options
                            }, (response) => {
                                // 检查运行时错误
                                if (chrome.runtime.lastError) {
                                    console.error('消息发送失败:', chrome.runtime.lastError);
                                    chrome.tabs.remove(tab.id);
                                    reject(new Error(`消息发送失败: ${chrome.runtime.lastError.message}`));
                                    return;
                                }
                                
                                if (response && response.success) {
                                    this.extractedContent.push({
                                        title: urlInfo.title,
                                        url: urlInfo.url,
                                        content: response.data
                                    });
                                } else {
                                    console.warn(`页面 ${urlInfo.url} 提取失败:`, response?.error);
                                }
                                
                                this.processedPages++;
                                
                                // 关闭标签页
                                chrome.tabs.remove(tab.id);
                                
                                // 发送进度更新
                                this.sendProgressUpdate();
                                
                                resolve();
                            });
                        }, 1000); // 等待1秒让页面完全加载
                    }
                };
                
                chrome.tabs.onUpdated.addListener(listener);
            });
        });
    }
    
    // 合并提取的内容
    mergeContent() {
        let mergedMarkdown = `# 多页面内容提取报告\n\n`;
        mergedMarkdown += `> 提取时间: ${new Date().toLocaleString()}\n`;
        mergedMarkdown += `> 总计提取: ${this.extractedContent.length}个页面\n\n`;
        
        let totalImages = [];
        let totalStats = {
            wordCount: 0,
            imageCount: 0
        };
        
        for (const page of this.extractedContent) {
            // 添加页面标题
            mergedMarkdown += `## ${page.title}\n\n`;
            mergedMarkdown += `> 来源: [${page.url}](${page.url})\n\n`;
            
            // 添加内容
            mergedMarkdown += page.content.markdown + '\n\n---\n\n';
            
            // 合并图片
            if (page.content.images) {
                totalImages = totalImages.concat(page.content.images);
            }
            
            // 更新统计
            totalStats.wordCount += page.content.stats.wordCount;
            totalStats.imageCount += page.content.stats.imageCount;
        }
        
        // 添加统计信息
        mergedMarkdown += `## 提取统计\n\n`;
        mergedMarkdown += `- 成功提取: ${this.extractedContent.length}个页面\n`;
        mergedMarkdown += `- 总字数: ${totalStats.wordCount.toLocaleString()}字\n`;
        mergedMarkdown += `- 总图片数: ${totalStats.imageCount}张\n`;
        
        return {
            markdown: mergedMarkdown.trim(),
            images: totalImages,
            stats: totalStats
        };
    }
    
    // 发送进度更新
    sendProgressUpdate() {
        chrome.runtime.sendMessage({
            type: 'extraction-progress',
            data: {
                total: this.totalPages,
                processed: this.processedPages,
                percentage: Math.round((this.processedPages / this.totalPages) * 100)
            }
        });
    }
}

// 监听消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'start-multi-extraction') {
        const extractor = new MultiPageExtractor();
        extractor.startExtraction(request.urls, request.options)
            .then(result => {
                sendResponse({ success: true, data: result });
            })
            .catch(error => {
                sendResponse({ success: false, error: error.message });
            });
        
        return true; // 保持消息通道开放
    }
    
    // 知识星球专用批量提取
    if (request.action === 'start-zsxq-batch-extraction') {
        const extractor = new ZsxqBatchExtractor();
        extractor.startBatchExtraction(request.columns, request.options)
            .then(result => {
                sendResponse({ success: true, data: result });
            })
            .catch(error => {
                sendResponse({ success: false, error: error.message });
            });
        
        return true; // 保持消息通道开放
    }
});

// 知识星球批量提取器
class ZsxqBatchExtractor {
    constructor() {
        this.extractedColumns = [];
        this.currentExtraction = null;
        this.totalArticles = 0;
        this.processedArticles = 0;
    }
    
    // 开始批量提取
    async startBatchExtraction(columnData, options) {
        this.extractedColumns = [];
        this.totalArticles = columnData.reduce((total, col) => total + col.articleCount, 0);
        this.processedArticles = 0;
        this.currentExtraction = {
            startTime: Date.now(),
            options: options,
            targetColumns: ['\u4eba\u5de5\u667a\u80fd\u5199\u4f5c', '\u4f73\u4f5c\u5171\u8d4f', '\u5916\u8bed\u5b66\u4e60', '\u597d\u7269\u5206\u4eab']
        };
        
        console.log(`\u5f00\u59cb\u6279\u91cf\u63d0\u53d6\u77e5\u8bc6\u661f\u7403\u5185\u5bb9\uff1a${columnData.length}\u4e2a\u680f\u76ee\uff0c\u5171${this.totalArticles}\u7bc7\u6587\u7ae0`);
        
        // 逐个处理栏目
        for (const column of columnData) {
            try {
                const columnResult = await this.extractColumn(column);
                this.extractedColumns.push(columnResult);
            } catch (error) {
                console.error(`\u63d0\u53d6\u680f\u76ee\u5931\u8d25: ${column.title}`, error);
                // 即使失\u8d25也要更\u65b0进\u5ea6
                this.processedArticles += column.articleCount;
                this.sendProgressUpdate();
            }
        }
        
        console.log(`\u6279\u91cf\u63d0\u53d6\u5b8c\u6210\uff0c\u6210\u529f\u63d0\u53d6 ${this.extractedColumns.length}/${columnData.length} \u4e2a\u680f\u76ee`);
        return this.generateFinalReport();
    }
    
    // 提取单个栏\u76ee
    async extractColumn(column) {
        const columnResult = {
            title: column.title,
            totalArticles: column.articleCount,
            extractedArticles: [],
            failedArticles: [],
            summary: ''
        };
        
        // 提取每篇文章
        for (const article of column.articles) {
            try {
                console.log(`\u5f00\u59cb\u63d0\u53d6\u6587\u7ae0: ${article.title}`);
                console.log(`- \u662f\u5426\u6709\u8be6\u60c5\u9875: ${article.hasDetailPage}`);
                console.log(`- \u94fe\u63a5\u5730\u5740: ${article.url}`);
                
                if (article.hasDetailPage && article.url && article.url !== '#') {
                    // \u6709\u94fe\u63a5\u7684\u6587\u7ae0\uff0c\u9700\u8981\u6253\u5f00\u65b0\u9875\u9762\u63d0\u53d6
                    console.log(`\u6b63\u5728\u6253\u5f00\u94fe\u63a5\u63d0\u53d6\u6587\u7ae0: ${article.url}`);
                    const articleContent = await this.extractArticle(article);
                    if (articleContent) {
                        columnResult.extractedArticles.push(articleContent);
                        console.log(`\u6587\u7ae0\u63d0\u53d6\u6210\u529f: ${article.title}, \u5b57\u6570: ${articleContent.wordCount}`);
                    } else {
                        console.warn(`\u6587\u7ae0\u63d0\u53d6\u4e3a\u7a7a: ${article.title}`);
                        columnResult.failedArticles.push({
                            title: article.title,
                            url: article.url,
                            reason: '\u9875\u9762\u5185\u5bb9\u63d0\u53d6\u4e3a\u7a7a'
                        });
                    }
                } else {
                    // \u65e0\u94fe\u63a5\u7684\u6587\u7ae0\uff0c\u5c1d\u8bd5\u4ece\u5f53\u524d\u9875\u9762\u63d0\u53d6\u5185\u5bb9
                    console.log(`\u5c1d\u8bd5\u4ece\u5f53\u524d\u9875\u9762\u63d0\u53d6\u6587\u7ae0\u5185\u5bb9: ${article.title}`);
                    
                    // \u4f7f\u7528\u65b0\u7684\u63d0\u53d6\u65b9\u6cd5
                    const content = await this.extractCurrentPageArticle(article);
                    
                    if (content && content.trim().length > 10) {
                        columnResult.extractedArticles.push({
                            title: article.title,
                            url: '#',
                            content: content,
                            wordCount: content.length,
                            extractedAt: new Date().toISOString()
                        });
                        console.log(`\u5f53\u524d\u9875\u9762\u6587\u7ae0\u63d0\u53d6\u6210\u529f: ${article.title}, \u5b57\u6570: ${content.length}`);
                    } else {
                        console.warn(`\u5f53\u524d\u9875\u9762\u6587\u7ae0\u63d0\u53d6\u5931\u8d25\u6216\u5185\u5bb9\u8fc7\u77ed: ${article.title}`);
                        columnResult.failedArticles.push({
                            title: article.title,
                            url: '#',
                            reason: '\u5f53\u524d\u9875\u9762\u5185\u5bb9\u63d0\u53d6\u5931\u8d25\u6216\u5185\u5bb9\u8fc7\u77ed'
                        });
                    }
                }
                
                this.processedArticles++;
                this.sendProgressUpdate();
                
                // 防止请求过于频繁
                await this.delay(500);
                
            } catch (error) {
                console.error(`\u63d0\u53d6\u6587\u7ae0\u5f02\u5e38: ${article.title}`, error);
                columnResult.failedArticles.push({
                    title: article.title,
                    url: article.url || '#',
                    reason: `\u63d0\u53d6\u5f02\u5e38: ${error.message}`
                });
                this.processedArticles++;
                this.sendProgressUpdate();
            }
        }
        
        // 生成\u680f\u76ee总结
        columnResult.summary = `\u6210\u529f提\u53d6 ${columnResult.extractedArticles.length}/${column.articleCount} \u7bc7\u6587\u7ae0`;
        
        return columnResult;
    }
    
    // 提取单篇文章
    async extractArticle(article) {
        return new Promise((resolve, reject) => {
            const timeoutId = setTimeout(() => {
                reject(new Error(`\u6587\u7ae0 ${article.url} \u63d0\u53d6\u8d85\u65f6`));
            }, 20000); // 20\u79d2\u8d85\u65f6
            
            chrome.tabs.create({ 
                url: article.url, 
                active: false 
            }, (tab) => {
                if (!tab) {
                    clearTimeout(timeoutId);
                    reject(new Error(`\u65e0\u6cd5\u521b\u5efa\u6807\u7b7e\u9875: ${article.url}`));
                    return;
                }
                
                // 等待页\u9762加载完成
                const listener = (tabId, info) => {
                    if (tabId === tab.id && info.status === 'complete') {
                        chrome.tabs.onUpdated.removeListener(listener);
                        clearTimeout(timeoutId);
                        
                        // 给页\u9762时间完全渲染
                        setTimeout(() => {
                            // 注入content script并提取内容
                            chrome.tabs.sendMessage(tab.id, {
                                action: 'extract',
                                options: this.currentExtraction.options
                            }, (response) => {
                                // 检查运行时错误
                                if (chrome.runtime.lastError) {
                                    console.error('消息发送失败:', chrome.runtime.lastError);
                                    chrome.tabs.remove(tab.id);
                                    reject(new Error(`消息发送失败: ${chrome.runtime.lastError.message}`));
                                    return;
                                }
                                
                                if (response && response.success) {
                                    const articleContent = {
                                        title: article.title,
                                        url: article.url,
                                        content: response.data.markdown,
                                        wordCount: response.data.stats.wordCount,
                                        imageCount: response.data.stats.imageCount,
                                        images: response.data.images || [],
                                        extractedAt: new Date().toISOString()
                                    };
                                    resolve(articleContent);
                                } else {
                                    console.warn(`文章 ${article.url} 提取失败:`, response?.error);
                                    resolve(null);
                                }
                                
                                // 关闭标签页
                                chrome.tabs.remove(tab.id);
                            });
                        }, 2000); // 等待2秒让页面完全加载
                    }
                };
                
                chrome.tabs.onUpdated.addListener(listener);
            });
        });
    }
    
    // 提取元素内容(用于无链接的文章)
    extractElementContent(element) {
        if (!element) return '';
        
        // 简单的文本提取
        const text = element.textContent || element.innerText || '';
        return text.trim();
    }
    
    // 从当前页面提取文章内容
    async extractCurrentPageArticle(article) {
        return new Promise((resolve) => {
            // 由于background script无法直接访问DOM，我们需要获取原始标签页
            chrome.tabs.query({active: true, currentWindow: true}, async (tabs) => {
                if (tabs.length === 0) {
                    console.warn('无法找到活动标签页');
                    resolve('');
                    return;
                }
                
                const currentTab = tabs[0];
                
                try {
                    // 向content script发送消息，提取特定文章元素的内容
                    chrome.tabs.sendMessage(currentTab.id, {
                        action: 'extract-article-element',
                        article: {
                            title: article.title,
                            index: article.index,
                            description: article.description || '',
                            // 由于DOM元素无法序列化，我们传递一些标识信息
                            titleText: article.title,
                            wordCount: article.wordCount || 0
                        }
                    }, (response) => {
                        if (chrome.runtime.lastError) {
                            console.error('消息发送失败:', chrome.runtime.lastError);
                            resolve('');
                            return;
                        }
                        
                        if (response && response.success) {
                            resolve(response.content || '');
                        } else {
                            console.warn('文章元素内容提取失败:', response?.error);
                            resolve('');
                        }
                    });
                } catch (error) {
                    console.error('提取当前页面文章内容失败:', error);
                    resolve('');
                }
            });
        });
    }
    
    // 延迟函数
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // 发送进度更新
    sendProgressUpdate() {
        chrome.runtime.sendMessage({
            type: 'zsxq-extraction-progress',
            data: {
                total: this.totalArticles,
                processed: this.processedArticles,
                percentage: Math.round((this.processedArticles / this.totalArticles) * 100)
            }
        });
    }
    
    // 生成最终报告
    generateFinalReport() {
        let finalMarkdown = `# 知识星球内容批量提取报告\n\n`;
        finalMarkdown += `> 提取时间: ${new Date().toLocaleString()}\n`;
        finalMarkdown += `> 总计提取: ${this.extractedColumns.length}个栏目, ${this.totalArticles}篇文章\n\n`;
        
        let totalWordCount = 0;
        let totalImageCount = 0;
        let totalSuccess = 0;
        let totalFailed = 0;
        
        // 按栏目组织内容
        this.extractedColumns.forEach((column, index) => {
            finalMarkdown += `## ${index + 1}. ${column.title} (${column.extractedArticles.length}/${column.totalArticles}篇)\n\n`;
            
            if (column.extractedArticles.length > 0) {
                column.extractedArticles.forEach((article, articleIndex) => {
                    finalMarkdown += `### ${articleIndex + 1}. ${article.title}\n\n`;
                    
                    if (article.url !== '#') {
                        finalMarkdown += `> 原文链接: [${article.url}](${article.url})\n`;
                    }
                    finalMarkdown += `> 字数: ${article.wordCount} | 提取时间: ${new Date(article.extractedAt).toLocaleString()}\n\n`;
                    
                    finalMarkdown += article.content + '\n\n';
                    finalMarkdown += '---\n\n';
                    
                    totalWordCount += article.wordCount;
                    totalImageCount += article.imageCount || 0;
                });
                
                totalSuccess += column.extractedArticles.length;
            }
            
            if (column.failedArticles.length > 0) {
                finalMarkdown += `#### 提取失败的文章 (${column.failedArticles.length}篇)\n\n`;
                column.failedArticles.forEach(failed => {
                    finalMarkdown += `- **${failed.title}**: ${failed.reason}\n`;
                });
                finalMarkdown += '\n';
                
                totalFailed += column.failedArticles.length;
            }
            
            finalMarkdown += '\n';
        });
        
        // 添加最终统计
        finalMarkdown += `## 提取统计\n\n`;
        finalMarkdown += `- 成功提取: ${totalSuccess}篇文章\n`;
        finalMarkdown += `- 失败: ${totalFailed}篇文章\n`;
        finalMarkdown += `- 成功率: ${((totalSuccess / this.totalArticles) * 100).toFixed(1)}%\n`;
        finalMarkdown += `- 总字数: ${totalWordCount.toLocaleString()}字\n`;
        finalMarkdown += `- 总图片数: ${totalImageCount}张\n`;
        
        return {
            markdown: finalMarkdown,
            stats: {
                wordCount: totalWordCount,
                imageCount: totalImageCount,
                successCount: totalSuccess,
                failedCount: totalFailed,
                successRate: ((totalSuccess / this.totalArticles) * 100).toFixed(1)
            },
            columns: this.extractedColumns
        };
    }
}