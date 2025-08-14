// Content script for extracting page content with formatting preservation

class MarkdownExtractor {
    constructor() {
        this.options = {
            preserveStyle: true,
            extractImages: true,
            cleanAds: true,
            preserveTables: true,
            includeCodeHighlight: true,
            detectColumns: true,
            extractLinks: false
        };
    }
    
    // 判断一个元素是否主要是文本块（很多站用div承载正文）
    shouldTreatAsParagraph(element) {
        const tag = element.tagName?.toLowerCase();
        if (!['div', 'section', 'span', 'article'].includes(tag)) return false;
        
        // 过滤明显的非正文容器
        const nonContentRoles = ['navigation', 'banner', 'complementary', 'contentinfo', 'search', 'dialog', 'menu'];
        const role = element.getAttribute('role');
        if (role && nonContentRoles.includes(role)) return false;
        if (element.closest('nav, aside, header, footer')) return false;
        
        // 含有典型区块子元素则当容器跳过（但允许简单内联元素）
        const hasBlockChildren = element.querySelector('p, ul, ol, table, pre, blockquote, article, section, h1, h2, h3, h4, h5, h6');
        if (hasBlockChildren) return false;
        
        // 检查是否为纯文本或包含简单内联元素的容器
        const childElements = Array.from(element.children);
        const hasOnlyInlineChildren = childElements.every(child => {
            const childTag = child.tagName.toLowerCase();
            return ['span', 'a', 'strong', 'b', 'em', 'i', 'code', 'br', 'img'].includes(childTag);
        });
        
        // 文本长度阈值（使用innerText可更贴近用户可见文本）
        const textLen = (element.innerText || '').trim().replace(/\s+/g, ' ').length;
        
        // 降低长度阈值，并考虑包含重要内容的短文本
        if (textLen >= 5 && (hasOnlyInlineChildren || childElements.length === 0)) {
            // 检查是否包含有价值的内容模式
            const text = element.innerText.trim();
            const hasValuePattern = /[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}|\d+/.test(text);
            return hasValuePattern;
        }
        
        return textLen >= 20; // 较长文本直接通过
    }

    // 判断元素是否真实可见（避免克隆节点导致样式丢失）
    isActuallyVisible(element) {
        if (!element || element.nodeType !== Node.ELEMENT_NODE) return false;
        if (element.getAttribute('aria-hidden') === 'true') return false;
        if (element.hidden) return false;
        
        let el = element;
        while (el && el.nodeType === Node.ELEMENT_NODE) {
            const style = window.getComputedStyle(el);
            if (!style || style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity || '1') === 0) {
                return false;
            }
            el = el.parentElement;
        }
        const rect = element.getBoundingClientRect();
        if ((rect.width === 0 && rect.height === 0) || (element.offsetWidth === 0 && element.offsetHeight === 0)) {
            return false;
        }
        return true;
    }

    // 是否为垃圾/非正文节点 - 优化知识星球支持
    isJunkNode(element) {
        if (!this.options.cleanAds) return false;
        
        // 知识星球特殊处理：保留重要元素
        if (window.location.hostname.includes('zsxq.com')) {
            const importantZsxqSelectors = [
                'div.name', 'div.list-container', 'div.content', 
                'div.topic-detail-panel', 'a.link-of-topic'
            ];
            
            for (const sel of importantZsxqSelectors) {
                try {
                    if (element.matches(sel)) return false;
                } catch {}
            }
        }
        
        const junkSelectors = [
            '.ad', '.ads', '.advertisement', '.banner',
            '[id*="ad"]', '[class*="ad-"]', '[class*="popup"]',
            'iframe[src*="doubleclick"]', 'iframe[src*="googlesyndication"]',
            '.modal', '.overlay', '.newsletter-signup',
            'nav', 'aside', 'footer', 'header', 'noscript', 'script', 'style'
        ];
        try {
            for (const sel of junkSelectors) {
                if (element.matches(sel)) return true;
            }
        } catch {}
        return false;
    }

    // 寻找最可能的正文容器 - 增强知识星球支持
    findBestContentRoot(root = document.body) {
        const candidateSelectors = [
            'main', 'article', '[role="main"]', '.content', '.main', '#content',
            '.article', '.post', '.topic-detail', '.rich-text', '.markdown-body',
            // 知识星球特定选择器
            'div.topic-detail-panel'
        ];
        
        // 优先检查知识星球特定结构
        if (window.location.hostname.includes('zsxq.com')) {
            const zsxqContent = root.querySelector('div.topic-detail-panel');
            if (zsxqContent && this.isActuallyVisible(zsxqContent)) {
                return zsxqContent;
            }
        }
        
        for (const sel of candidateSelectors) {
            const el = root.querySelector(sel);
            if (el && this.isActuallyVisible(el)) return el;
        }
        // 回退：选择文本密度最高的块级元素
        let best = root;
        let bestScore = 0;
        const blocks = root.querySelectorAll('article, section, div');
        blocks.forEach(el => {
            if (!this.isActuallyVisible(el) || this.isJunkNode(el)) return;
            const text = (el.innerText || '').replace(/\s+/g, ' ').trim();
            const links = el.querySelectorAll('a').length + 1; // 链接越多噪声越大
            const score = text.length / links;
            if (score > bestScore) {
                bestScore = score;
                best = el;
            }
        });
        return best || root;
    }

    // 统计字数（兼容中英文）
    incrementStats(stats, text) {
        if (!text) return;
        const asciiWords = (text.match(/[A-Za-z0-9_]+/g) || []).length;
        const cjkChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
        stats.wordCount += asciiWords + cjkChars;
    }

    // 规范图片URL（优先原图/高分辨率）
    refineImageUrl(url) {
        try {
            const u = new URL(url, window.location.href);
            // 优先 srcset 里最大图已在调用处完成。此处做常见缩略参数裁剪
            if (u.hostname.includes('images.zsxq.com')) {
                // 去掉明显的缩略与模糊参数
                const cleaned = u.origin + u.pathname; // 去除 query
                return cleaned;
            }
            return u.href;
        } catch {
            return url;
        }
    }

    // 简单去重与噪声清理
    normalizeMarkdown(markdown) {
        const lines = markdown.split(/\n/);
        const result = [];
        let prev = '';
        for (let line of lines) {
            const trimmed = line.trim();
            // 移除常见站点导航类噪声，但保留知识星球重要内容
            const isNavigationNoise = /^(我的足迹|我的收藏|退出登录|默认排序|管理后台|榜单|共 \d+ 个专栏|展开全部)$/.test(trimmed);
            // 保留目标栏目标题，但过滤其他噪声
            const isTargetColumn = /^(人工智能写作|佳作共赏|外语学习|好物分享)(（\d+）)?$/.test(trimmed);
            const isOtherColumnNoise = /^(付费文章合集\d+|写作技巧分享|海外游记|打造个人品牌)(（\d+）)?$/.test(trimmed);
            const isNoise = isNavigationNoise || (!isTargetColumn && isOtherColumnNoise);
            if (isNoise) continue;
            if (trimmed && trimmed === prev) continue; // 连续重复行去重
            result.push(line);
            prev = trimmed;
        }
        return result.join('\n');
    }

    // 兜底：在抓取结果过少时宽松提取正文
    relaxedExtract(contentRoot) {
        let md = '';
        const add = (s) => { if (s) md += s + '\n\n'; };
        
        // 先标题
        const titleEl = document.querySelector('h1, .title, [class*="title"], [id*="title"]');
        if (titleEl && !this.isJunkNode(titleEl)) {
            add('# ' + (titleEl.innerText || '').trim());
        }
        
        // 更广泛的内容选择器，包括常见的内容容器
        const contentSelectors = [
            'h1, h2, h3, h4, h5, h6',
            'p',
            'div[class*="content"]',
            'div[class*="text"]', 
            'div[class*="article"]',
            'div[class*="post"]',
            'div[class*="body"]',
            'section',
            'article',
            'li',
            'blockquote',
            'pre',
            'span'
        ];
        
        const blocks = contentRoot.querySelectorAll(contentSelectors.join(','));
        const processedElements = new Set();
        
        blocks.forEach(el => {
            if (processedElements.has(el) || this.isJunkNode(el) || !this.isActuallyVisible(el)) return;
            
            // 避免处理已处理元素的父/子元素
            let isNested = false;
            for (const processed of processedElements) {
                if (processed.contains(el) || el.contains(processed)) {
                    isNested = true;
                    break;
                }
            }
            if (isNested) return;
            
            const text = (el.innerText || '').replace(/\s+/g, ' ').trim();
            if (!text || text.length < 3) return;
            
            const tag = el.tagName.toLowerCase();
            if (/^h[1-6]$/.test(tag)) {
                const level = parseInt(tag[1]);
                add('#'.repeat(level) + ' ' + text);
            } else if (tag === 'blockquote') {
                add('> ' + text.split('\n').join('\n> '));
            } else if (tag === 'pre' || tag === 'code') {
                add('```\n' + text + '\n```');
            } else {
                // 更宽松的文本长度要求
                if (text.length >= 3 && !/^(更多|阅读|点击|查看|分享|关注)$/.test(text)) {
                    add(text);
                }
            }
            
            processedElements.add(el);
        });
        
        return md;
    }
    
    // 检测页面布局类型
    detectPageLayout() {
        // 检测是否为知识星球页面
        const isZsxqPage = window.location.hostname.includes('zsxq.com') || 
                          document.querySelector('div.name, div.list-container, div.topic-detail-panel');
        
        const patterns = {
            // 专栏式布局检测 - 增加知识星球特定选择器
            columnLayout: [
                '.column', '.col', '.sidebar',
                '[class*="column"]', '[class*="sidebar"]',
                'aside', 'nav[class*="menu"]',
                // 知识星球特定选择器
                'div.name', 'div.list-container'
            ],
            // 文章列表检测 - 增加知识星球特定选择器
            articleList: [
                '.article-list', '.post-list', '.content-list',
                '[class*="list"]', '[class*="items"]',
                // 知识星球特定选择器
                'div.content', 'div.list-container'
            ],
            // 主内容区检测 - 增加知识星球特定选择器
            mainContent: [
                'main', 'article', '.content', '.main',
                '[role="main"]', '#content',
                // 知识星球特定选择器
                'div.topic-detail-panel'
            ]
        };
        
        let layout = {
            hasColumns: false,
            hasArticleList: false,
            columns: [],
            articleLinks: [],
            isZsxqPage: isZsxqPage,
            zsxqColumns: [],
            targetColumns: ['人工智能写作', '佳作共赏', '外语学习', '好物分享']
        };
        
        // 检测专栏 - 优化知识星球页面处理
        if (isZsxqPage) {
            // 知识星球专用检测逻辑
            const zsxqColumns = this.detectZsxqColumns();
            if (zsxqColumns.length > 0) {
                layout.hasColumns = true;
                layout.zsxqColumns = zsxqColumns;
                layout.columns = zsxqColumns;
            }
        } else {
            // 通用检测逻辑
            for (const selector of patterns.columnLayout) {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    layout.hasColumns = true;
                    layout.columns = Array.from(elements).map(el => ({
                        element: el,
                        title: this.extractColumnTitle(el),
                        links: this.extractColumnLinks(el)
                    }));
                    break;
                }
            }
        }
        
        // 检测文章列表
        for (const selector of patterns.articleList) {
            const elements = document.querySelectorAll(selector);
            if (elements.length > 0) {
                layout.hasArticleList = true;
                elements.forEach(el => {
                    const links = this.extractArticleLinks(el);
                    layout.articleLinks = layout.articleLinks.concat(links);
                });
            }
        }
        
        return layout;
    }
    
    // 提取专栏标题
    extractColumnTitle(element) {
        const headings = element.querySelectorAll('h1, h2, h3, h4');
        if (headings.length > 0) {
            return headings[0].textContent.trim();
        }
        return '未命名专栏';
    }
    
    // 提取专栏内的链接
    extractColumnLinks(element) {
        const links = element.querySelectorAll('a[href]');
        const linkData = [];
        
        links.forEach(link => {
            const href = link.href;
            const title = link.textContent.trim();
            
            // 过滤无效链接
            if (href && !href.startsWith('#') && !href.startsWith('javascript:')) {
                // 检查是否可能包含正文预览
                const preview = this.extractLinkPreview(link);
                
                linkData.push({
                    url: href,
                    title: title,
                    preview: preview,
                    needsDeepExtraction: preview.length < 100 // 预览内容少于100字符可能需要深度提取
                });
            }
        });
        
        return linkData;
    }
    
    // 提取链接预览内容
    extractLinkPreview(linkElement) {
        // 查找链接附近的预览文本
        const parent = linkElement.closest('li, div, article');
        if (parent) {
            // 查找描述、摘要等元素
            const previewSelectors = [
                '.description', '.summary', '.excerpt',
                '.preview', '.intro', 'p'
            ];
            
            for (const selector of previewSelectors) {
                const preview = parent.querySelector(selector);
                if (preview && preview !== linkElement) {
                    return preview.textContent.trim();
                }
            }
        }
        
        return '';
    }
    
    // 提取文章链接
    extractArticleLinks(element) {
        const links = [];
        const articles = element.querySelectorAll('article, .article, .post, [class*="item"]');
        
        articles.forEach(article => {
            const link = article.querySelector('a[href]');
            const title = article.querySelector('h1, h2, h3, h4, .title');
            const excerpt = article.querySelector('.excerpt, .summary, .description, p');
            
            if (link) {
                links.push({
                    url: link.href,
                    title: title ? title.textContent.trim() : link.textContent.trim(),
                    preview: excerpt ? excerpt.textContent.trim() : '',
                    needsDeepExtraction: true
                });
            }
        });
        
        return links;
    }
    
    // 检测知识星球专栏结构 - 增强版
    detectZsxqColumns() {
        const columns = [];
        const targetColumns = ['人工智能写作', '佳作共赏', '外语学习', '好物分享'];
        
        console.log('开始检测知识星球栏目...');
        
        // 查找各个目标栏目
        targetColumns.forEach(targetTitle => {
            console.log(`正在查找栏目: ${targetTitle}`);
            let columnContainer = null;
            let foundElement = null;
            
            // 方法1: 通过各种可能的选择器查找栏目名称
            const nameSelectors = [
                'div.name', '.name', '[class*="name"]',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                '.title', '[class*="title"]',
                '.column-title', '.section-title',
                'span', 'div', 'p'
            ];
            
            // 尝试各种选择器
            for (const selector of nameSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const el of elements) {
                    const text = (el.textContent || el.innerText || '').trim();
                    if (this.isTargetColumnMatch(text, targetTitle)) {
                        foundElement = el;
                        console.log(`通过选择器 "${selector}" 找到栏目: ${targetTitle}`);
                        break;
                    }
                }
                if (foundElement) break;
            }
            
            // 方法2: 如果还没找到，使用更广泛的文本搜索
            if (!foundElement) {
                console.log(`使用广泛搜索查找栏目: ${targetTitle}`);
                const allTextElements = document.querySelectorAll('*');
                for (const el of allTextElements) {
                    // 跳过script、style等元素
                    if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(el.tagName)) continue;
                    
                    const text = (el.textContent || el.innerText || '').trim();
                    if (this.isTargetColumnMatch(text, targetTitle) && this.isActuallyVisible(el)) {
                        foundElement = el;
                        console.log(`通过广泛搜索找到栏目: ${targetTitle}`);
                        break;
                    }
                }
            }
            
            // 方法3: 寻找栏目对应的内容容器
            if (foundElement) {
                columnContainer = this.findColumnContainer(foundElement);
                
                if (columnContainer) {
                    console.log(`找到栏目容器: ${targetTitle}`);
                    const columnData = {
                        title: targetTitle,
                        element: columnContainer,
                        foundElement: foundElement,
                        links: this.extractZsxqColumnLinks(columnContainer),
                        articles: this.extractZsxqArticles(columnContainer)
                    };
                    columns.push(columnData);
                } else {
                    console.warn(`找到栏目标题但未找到对应容器: ${targetTitle}`);
                }
            } else {
                console.warn(`未找到栏目: ${targetTitle}`);
            }
        });
        
        console.log(`检测完成，找到 ${columns.length} 个栏目`);
        return columns;
    }
    
    // 判断文本是否匹配目标栏目
    isTargetColumnMatch(text, targetTitle) {
        if (!text || text.length > 100) return false; // 避免匹配过长的文本
        
        // 精确匹配
        if (text === targetTitle) return true;
        
        // 包含匹配（去除数字和括号）
        const cleanText = text.replace(/[（）()0-9]/g, '').trim();
        if (cleanText === targetTitle) return true;
        
        // 部分匹配
        if (text.includes(targetTitle)) return true;
        
        // 容错匹配（处理可能的空格、标点符号差异）
        const normalizedText = text.replace(/[\s\u3000\-_·]/g, '');
        const normalizedTarget = targetTitle.replace(/[\s\u3000\-_·]/g, '');
        if (normalizedText.includes(normalizedTarget)) return true;
        
        return false;
    }
    
    // 查找栏目对应的内容容器
    findColumnContainer(titleElement) {
        // 尝试多种方式查找内容容器
        const containerSelectors = [
            'div.list-container',
            '.list-container', 
            '[class*="list"]',
            'div.content',
            '.content',
            '[class*="content"]',
            'ul', 'ol',
            '[class*="item"]',
            '[class*="article"]'
        ];
        
        // 1. 在父元素中查找
        let parent = titleElement.parentElement;
        let attempts = 0;
        while (parent && attempts < 5) { // 限制向上搜索层数
            for (const selector of containerSelectors) {
                const container = parent.querySelector(selector);
                if (container && this.isActuallyVisible(container)) {
                    const childCount = container.children.length;
                    if (childCount > 0) { // 确保容器有内容
                        return container;
                    }
                }
            }
            parent = parent.parentElement;
            attempts++;
        }
        
        // 2. 查找下一个兄弟元素
        let sibling = titleElement.nextElementSibling;
        let siblingAttempts = 0;
        while (sibling && siblingAttempts < 5) {
            if (this.isActuallyVisible(sibling)) {
                // 直接检查兄弟元素是否为容器
                for (const selector of containerSelectors) {
                    if (sibling.matches && sibling.matches(selector)) {
                        return sibling;
                    }
                }
                // 在兄弟元素内查找
                for (const selector of containerSelectors) {
                    const container = sibling.querySelector(selector);
                    if (container && this.isActuallyVisible(container)) {
                        return container;
                    }
                }
            }
            sibling = sibling.nextElementSibling;
            siblingAttempts++;
        }
        
        // 3. 如果还没找到，尝试在整个文档中查找
        for (const selector of containerSelectors.slice(0, 3)) { // 只用前几个最可能的选择器
            const containers = document.querySelectorAll(selector);
            for (const container of containers) {
                if (this.isActuallyVisible(container) && container.children.length > 0) {
                    // 简单的距离判断 - 如果容器在标题附近
                    const rect1 = titleElement.getBoundingClientRect();
                    const rect2 = container.getBoundingClientRect();
                    const distance = Math.abs(rect1.bottom - rect2.top);
                    if (distance < 200) { // 200px以内
                        return container;
                    }
                }
            }
        }
        
        return null;
    }
    
    // 提取知识星球栏目中的链接 - 增强版
    extractZsxqColumnLinks(container) {
        const links = [];
        console.log('开始提取栏目链接...');
        
        // 多种提取策略
        const strategies = [
            // 策略1: 查找 div.content 下的链接
            () => this.extractLinksFromContentDivs(container),
            // 策略2: 查找所有a标签
            () => this.extractLinksFromAnchors(container),
            // 策略3: 查找可点击的元素
            () => this.extractLinksFromClickableElements(container),
            // 策略4: 查找列表项
            () => this.extractLinksFromListItems(container)
        ];
        
        // 依次尝试各种策略
        for (const strategy of strategies) {
            const strategyLinks = strategy();
            if (strategyLinks.length > 0) {
                links.push(...strategyLinks);
                console.log(`通过策略提取到 ${strategyLinks.length} 个链接`);
            }
        }
        
        // 去重并过滤
        const uniqueLinks = this.deduplicateLinks(links);
        console.log(`去重后得到 ${uniqueLinks.length} 个链接`);
        
        return uniqueLinks;
    }
    
    // 从div.content中提取链接
    extractLinksFromContentDivs(container) {
        const links = [];
        const contentDivs = container.querySelectorAll('div.content, .content, [class*="content"]');
        
        contentDivs.forEach(contentDiv => {
            if (!this.isActuallyVisible(contentDiv)) return;
            
            const titleElement = contentDiv.querySelector('a[href], h1, h2, h3, h4, h5, h6, span, div, p');
            if (titleElement) {
                const link = titleElement.closest('a') || contentDiv.querySelector('a[href]');
                const title = this.extractCleanText(titleElement);
                
                if (this.isValidLinkTitle(title)) {
                    const descElement = contentDiv.querySelector('p, div:not(.content), span:not(:first-child)');
                    const description = descElement ? this.extractCleanText(descElement) : '';
                    
                    links.push({
                        url: link ? link.href : '#',
                        title: title,
                        description: description,
                        element: contentDiv,
                        needsDeepExtraction: true,
                        isClickable: !!link,
                        strategy: 'contentDivs'
                    });
                }
            }
        });
        
        return links;
    }
    
    // 从a标签中提取链接
    extractLinksFromAnchors(container) {
        const links = [];
        const anchors = container.querySelectorAll('a[href]');
        
        anchors.forEach(link => {
            if (!this.isActuallyVisible(link)) return;
            
            const title = this.extractCleanText(link);
            if (this.isValidLinkTitle(title) && !this.isNavigationLink(title)) {
                // 查找描述文本
                const description = this.findDescriptionForLink(link);
                
                links.push({
                    url: link.href,
                    title: title,
                    description: description,
                    element: link,
                    needsDeepExtraction: true,
                    isClickable: true,
                    strategy: 'anchors'
                });
            }
        });
        
        return links;
    }
    
    // 从可点击元素中提取链接
    extractLinksFromClickableElements(container) {
        const links = [];
        const clickableSelectors = [
            '[onclick]', '[role="button"]', '.clickable',
            '[style*="cursor:pointer"]', '[style*="cursor: pointer"]'
        ];
        
        clickableSelectors.forEach(selector => {
            const elements = container.querySelectorAll(selector);
            elements.forEach(element => {
                if (!this.isActuallyVisible(element)) return;
                
                const title = this.extractCleanText(element);
                if (this.isValidLinkTitle(title)) {
                    links.push({
                        url: '#',
                        title: title,
                        description: '',
                        element: element,
                        needsDeepExtraction: false, // 通常是当前页面内的内容
                        isClickable: true,
                        strategy: 'clickableElements'
                    });
                }
            });
        });
        
        return links;
    }
    
    // 从列表项中提取链接
    extractLinksFromListItems(container) {
        const links = [];
        const listItems = container.querySelectorAll('li, .item, [class*="item"]');
        
        listItems.forEach(item => {
            if (!this.isActuallyVisible(item)) return;
            
            const link = item.querySelector('a[href]');
            const titleElement = item.querySelector('a, h1, h2, h3, h4, h5, h6, span, div, p');
            
            if (titleElement) {
                const title = this.extractCleanText(titleElement);
                if (this.isValidLinkTitle(title)) {
                    const description = this.findDescriptionForLink(titleElement);
                    
                    links.push({
                        url: link ? link.href : '#',
                        title: title,
                        description: description,
                        element: item,
                        needsDeepExtraction: !!link,
                        isClickable: !!link,
                        strategy: 'listItems'
                    });
                }
            }
        });
        
        return links;
    }
    
    // 提取干净的文本
    extractCleanText(element) {
        if (!element) return '';
        const text = (element.textContent || element.innerText || '').trim();
        // 移除多余的空白字符
        return text.replace(/\s+/g, ' ');
    }
    
    // 验证链接标题是否有效
    isValidLinkTitle(title) {
        if (!title || title.length < 2 || title.length > 200) return false;
        
        // 过滤无意义的文本
        const invalidPatterns = [
            /^(更多|阅读|点击|查看|分享|关注|展开|收起)$/,
            /^(链接|网址|URL|地址)$/,
            /^\d+$/,
            /^[^\u4e00-\u9fa5a-zA-Z]*$/  // 只有符号或数字
        ];
        
        return !invalidPatterns.some(pattern => pattern.test(title));
    }
    
    // 判断是否为导航链接
    isNavigationLink(title) {
        const navigationPatterns = [
            /首页|主页|返回|上一页|下一页|更多|查看全部/,
            /登录|注册|退出|设置|帮助|关于/,
            /搜索|筛选|排序|过滤/
        ];
        
        return navigationPatterns.some(pattern => pattern.test(title));
    }
    
    // 为链接查找描述文本
    findDescriptionForLink(linkElement) {
        const parent = linkElement.closest('li, div, article, section');
        if (!parent) return '';
        
        const descriptionSelectors = [
            '.description', '.summary', '.excerpt', '.intro',
            'p', 'span:not(:first-child)', 'div:not(:first-child)'
        ];
        
        for (const selector of descriptionSelectors) {
            const desc = parent.querySelector(selector);
            if (desc && desc !== linkElement && desc.textContent) {
                const text = this.extractCleanText(desc);
                if (text && text.length > 10 && text.length < 300) {
                    return text;
                }
            }
        }
        
        return '';
    }
    
    // 去重链接
    deduplicateLinks(links) {
        const seen = new Set();
        const unique = [];
        
        links.forEach(link => {
            // 使用URL和标题的组合作为去重键
            const key = `${link.url}|${link.title}`;
            if (!seen.has(key)) {
                seen.add(key);
                unique.push(link);
            }
        });
        
        return unique;
    }
    
    // 提取知识星球文章列表 - 增强版
    extractZsxqArticles(container) {
        const articles = [];
        console.log('开始提取文章列表...');
        
        // 多种文章元素选择器
        const articleSelectors = [
            'div.content', '.content', '[class*="content"]',
            'li', '.item', '[class*="item"]',
            '.article', '[class*="article"]',
            '.post', '[class*="post"]',
            '.entry', '[class*="entry"]',
            'div', 'section', 'article'
        ];
        
        const foundArticles = new Set(); // 避免重复
        
        articleSelectors.forEach(selector => {
            const elements = container.querySelectorAll(selector);
            elements.forEach((element, index) => {
                if (foundArticles.has(element) || !this.isActuallyVisible(element)) return;
                
                const articleData = this.extractSingleArticle(element, articles.length + 1);
                if (articleData && this.isValidArticle(articleData)) {
                    articles.push(articleData);
                    foundArticles.add(element);
                }
            });
        });
        
        // 如果没有找到文章，尝试更宽泛的搜索
        if (articles.length === 0) {
            console.log('使用宽泛搜索提取文章...');
            const allElements = container.querySelectorAll('*');
            allElements.forEach((element, index) => {
                if (foundArticles.has(element) || !this.isActuallyVisible(element)) return;
                
                const text = this.extractCleanText(element);
                if (this.looksLikeArticleTitle(text)) {
                    const articleData = this.extractSingleArticle(element, articles.length + 1);
                    if (articleData && this.isValidArticle(articleData)) {
                        articles.push(articleData);
                        foundArticles.add(element);
                    }
                }
            });
        }
        
        console.log(`提取完成，找到 ${articles.length} 篇文章`);
        return articles;
    }
    
    // 提取单个文章信息
    extractSingleArticle(element, index) {
        // 查找标题元素
        const titleSelectors = [
            'a[href]', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            '.title', '[class*="title"]',
            'span', 'div', 'p'
        ];
        
        let titleElement = null;
        let title = '';
        
        // 尝试各种标题选择器
        for (const selector of titleSelectors) {
            const candidate = element.querySelector(selector);
            if (candidate && this.isActuallyVisible(candidate)) {
                const candidateText = this.extractCleanText(candidate);
                if (this.looksLikeArticleTitle(candidateText)) {
                    titleElement = candidate;
                    title = candidateText;
                    break;
                }
            }
        }
        
        // 如果没找到子元素，检查元素本身
        if (!titleElement) {
            const elementText = this.extractCleanText(element);
            if (this.looksLikeArticleTitle(elementText)) {
                titleElement = element;
                title = elementText;
            }
        }
        
        if (!titleElement || !title) return null;
        
        // 查找链接
        const link = titleElement.closest('a') || 
                     element.querySelector('a[href]') ||
                     (titleElement.tagName === 'A' ? titleElement : null);
        
        // 查找描述/摘要
        const description = this.extractArticleDescription(element, titleElement);
        
        // 查找发布时间
        const publishTime = this.extractPublishTime(element);
        
        return {
            index: index,
            title: title,
            url: link ? link.href : '#',
            description: description,
            publishTime: publishTime,
            element: element,
            titleElement: titleElement,
            hasDetailPage: !!link,
            wordCount: title.length + description.length
        };
    }
    
    // 判断文本是否像文章标题
    looksLikeArticleTitle(text) {
        if (!text || text.length < 3 || text.length > 200) return false;
        
        // 排除明显不是标题的文本
        const excludePatterns = [
            /^(更多|查看|点击|阅读|分享|关注|收藏|转发|评论|赞|踩)$/,
            /^(首页|主页|返回|刷新|加载|搜索|筛选)$/,
            /^(登录|注册|退出|设置|帮助|关于|联系)$/,
            /^\d{1,3}$/, // 纯数字
            /^[^\u4e00-\u9fa5a-zA-Z]*$/, // 只有符号
            /^(https?:\/\/|www\.)/i // URL
        ];
        
        if (excludePatterns.some(pattern => pattern.test(text))) {
            return false;
        }
        
        // 包含有意义内容的模式
        const meaningfulPatterns = [
            /[\u4e00-\u9fa5]{3,}/, // 至少3个中文字符
            /[a-zA-Z]{5,}/, // 至少5个英文字符
            /[\u4e00-\u9fa5a-zA-Z]{3,}.*[\u4e00-\u9fa5a-zA-Z]/ // 有意义的混合内容
        ];
        
        return meaningfulPatterns.some(pattern => pattern.test(text));
    }
    
    // 验证文章是否有效
    isValidArticle(article) {
        if (!article || !article.title) return false;
        
        // 标题长度检查
        if (article.title.length < 3 || article.title.length > 200) return false;
        
        // 检查是否为重复的导航元素
        const navigationTexts = [
            '导航', '菜单', '目录', '索引', '列表',
            '上一页', '下一页', '首页', '尾页',
            '返回', '回到顶部', '更多内容'
        ];
        
        if (navigationTexts.some(nav => article.title.includes(nav))) {
            return false;
        }
        
        return true;
    }
    
    // 提取文章描述
    extractArticleDescription(articleElement, titleElement) {
        const descriptionSelectors = [
            '.description', '.summary', '.excerpt', '.intro', '.abstract',
            '.content', '.text', 'p', 'div:not(:first-child)', 'span:not(:first-child)'
        ];
        
        for (const selector of descriptionSelectors) {
            const descElement = articleElement.querySelector(selector);
            if (descElement && descElement !== titleElement && this.isActuallyVisible(descElement)) {
                const text = this.extractCleanText(descElement);
                if (text && text.length > 10 && text.length < 500 && text !== titleElement.textContent.trim()) {
                    return text;
                }
            }
        }
        
        return '';
    }
    
    // 查找并提取文章内容
    findAndExtractArticleContent(article) {
        console.log(`开始查找文章内容: ${article.title}`);
        
        // 策略1: 通过标题文本查找元素
        const titleElements = document.querySelectorAll('*');
        let targetElement = null;
        
        for (const element of titleElements) {
            if (!this.isActuallyVisible(element)) continue;
            
            const text = this.extractCleanText(element);
            if (text === article.title || text.includes(article.title)) {
                // 找到标题元素，现在查找其关联的内容
                targetElement = this.findArticleContentFromTitle(element);
                if (targetElement) {
                    console.log(`通过标题匹配找到内容元素`);
                    break;
                }
            }
        }
        
        // 策略2: 如果没找到，尝试查找包含相似内容的元素
        if (!targetElement && article.description) {
            for (const element of titleElements) {
                if (!this.isActuallyVisible(element)) continue;
                
                const text = this.extractCleanText(element);
                if (text.includes(article.description.substring(0, 50))) {
                    targetElement = element;
                    console.log(`通过描述匹配找到内容元素`);
                    break;
                }
            }
        }
        
        // 策略3: 如果还没找到，尝试通过结构特征查找
        if (!targetElement) {
            const contentSelectors = [
                'div.content', '.content', '[class*="content"]',
                'article', '.article', '[class*="article"]',
                'p', 'div', 'section', 'span'
            ];
            
            for (const selector of contentSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (!this.isActuallyVisible(element)) continue;
                    
                    const text = this.extractCleanText(element);
                    // 如果元素包含文章标题的部分内容
                    if (text.length > 20 && this.containsArticleContent(text, article)) {
                        targetElement = element;
                        console.log(`通过内容特征匹配找到元素`);
                        break;
                    }
                }
                if (targetElement) break;
            }
        }
        
        if (targetElement) {
            // 提取完整的内容
            const content = this.extractElementCompleteContent(targetElement);
            console.log(`提取到内容: ${content.length} 字符`);
            return content;
        } else {
            console.warn(`未找到匹配的文章元素: ${article.title}`);
            return '';
        }
    }
    
    // 从标题元素查找文章内容
    findArticleContentFromTitle(titleElement) {
        // 查找标题的父容器
        let parent = titleElement.parentElement;
        let attempts = 0;
        
        while (parent && attempts < 5) {
            // 在父元素中查找内容区域
            const contentElement = parent.querySelector('.content, .text, .body, p, div:not(:first-child)');
            if (contentElement && contentElement !== titleElement && this.isActuallyVisible(contentElement)) {
                const text = this.extractCleanText(contentElement);
                if (text.length > 20) {
                    return contentElement;
                }
            }
            
            parent = parent.parentElement;
            attempts++;
        }
        
        // 查找下一个兄弟元素
        let sibling = titleElement.nextElementSibling;
        attempts = 0;
        while (sibling && attempts < 3) {
            if (this.isActuallyVisible(sibling)) {
                const text = this.extractCleanText(sibling);
                if (text.length > 20) {
                    return sibling;
                }
            }
            sibling = sibling.nextElementSibling;
            attempts++;
        }
        
        // 如果找不到兄弟元素，返回标题元素本身
        return titleElement;
    }
    
    // 检查文本是否包含文章相关内容
    containsArticleContent(text, article) {
        // 检查是否包含标题的关键词
        const titleWords = article.title.split(/\s+/).filter(word => word.length > 1);
        const matchedWords = titleWords.filter(word => text.includes(word));
        
        if (matchedWords.length >= Math.min(2, titleWords.length)) {
            return true;
        }
        
        // 检查是否包含描述中的内容
        if (article.description) {
            const descWords = article.description.split(/\s+/).filter(word => word.length > 2);
            const matchedDescWords = descWords.slice(0, 3).filter(word => text.includes(word));
            if (matchedDescWords.length >= 1) {
                return true;
            }
        }
        
        return false;
    }
    
    // 提取元素的完整内容
    extractElementCompleteContent(element) {
        // 如果元素本身内容较短，尝试提取其父元素的内容
        let targetElement = element;
        let text = this.extractCleanText(element);
        
        if (text.length < 50) {
            const parent = element.parentElement;
            if (parent) {
                const parentText = this.extractCleanText(parent);
                if (parentText.length > text.length * 2) {
                    targetElement = parent;
                    text = parentText;
                }
            }
        }
        
        // 使用提取器的标准方法提取内容
        try {
            return this.extractText(targetElement);
        } catch (error) {
            console.error('提取元素内容失败:', error);
            return text;
        }
    }
    
    // 提取发布时间
    extractPublishTime(element) {
        const timeSelectors = [
            'time', '.time', '.date', '.publish-time', '.create-time',
            '[datetime]', '[class*="time"]', '[class*="date"]'
        ];
        
        for (const selector of timeSelectors) {
            const timeElement = element.querySelector(selector);
            if (timeElement && this.isActuallyVisible(timeElement)) {
                const timeText = this.extractCleanText(timeElement);
                // 简单的时间格式检测
                if (/\d{4}[-\/]\d{1,2}[-\/]\d{1,2}|\d{1,2}:\d{2}/.test(timeText)) {
                    return timeText;
                }
            }
        }
        
        return '';
    }

    // 获取元素的计算样式
    getComputedStyles(element) {
        const styles = window.getComputedStyle(element);
        return {
            fontSize: styles.fontSize,
            fontWeight: styles.fontWeight,
            lineHeight: styles.lineHeight,
            letterSpacing: styles.letterSpacing,
            marginTop: styles.marginTop,
            marginBottom: styles.marginBottom,
            paddingTop: styles.paddingTop,
            paddingBottom: styles.paddingBottom,
            color: styles.color,
            backgroundColor: styles.backgroundColor,
            fontFamily: styles.fontFamily
        };
    }

    // 判断标题级别
    getHeadingLevel(element) {
        const tagName = element.tagName.toLowerCase();
        const headingMap = {
            'h1': 1,
            'h2': 2,
            'h3': 3,
            'h4': 4,
            'h5': 5,
            'h6': 6
        };
        
        if (headingMap[tagName]) {
            return headingMap[tagName];
        }
        
        // 通过样式判断标题级别
        const styles = this.getComputedStyles(element);
        const fontSize = parseFloat(styles.fontSize);
        const fontWeight = styles.fontWeight;
        
        if (fontWeight === 'bold' || fontWeight >= 600) {
            if (fontSize >= 32) return 1;
            if (fontSize >= 24) return 2;
            if (fontSize >= 18) return 3;
            if (fontSize >= 16) return 4;
        }
        
        return 0;
    }

    // 清理广告和无用元素
    cleanupElements(root) {
        if (!this.options.cleanAds) return;
        
        const selectors = [
            '.ad', '.ads', '.advertisement', '.banner',
            '[id*="ad"]', '[class*="ad-"]', '[class*="popup"]',
            'iframe[src*="doubleclick"]', 'iframe[src*="googlesyndication"]',
            '.modal', '.overlay', '.newsletter-signup',
            'script', 'style', 'noscript'
        ];
        
        selectors.forEach(selector => {
            root.querySelectorAll(selector).forEach(el => el.remove());
        });
    }

    // 提取表格为Markdown
    extractTable(table) {
        let markdown = '\n';
        const rows = table.querySelectorAll('tr');
        
        rows.forEach((row, rowIndex) => {
            const cells = row.querySelectorAll('th, td');
            let rowContent = '|';
            
            cells.forEach(cell => {
                const content = this.extractText(cell).trim().replace(/\|/g, '\\|');
                rowContent += ` ${content} |`;
            });
            
            markdown += rowContent + '\n';
            
            // 添加表头分隔线
            if (rowIndex === 0 && row.querySelector('th')) {
                let separator = '|';
                cells.forEach(() => {
                    separator += ' --- |';
                });
                markdown += separator + '\n';
            }
        });
        
        return markdown + '\n';
    }

    // 提取代码块
    extractCodeBlock(element) {
        const language = element.className.match(/language-(\w+)/)?.[1] || '';
        const code = element.textContent;
        return `\n\`\`\`${language}\n${code}\n\`\`\`\n`;
    }

    // 提取列表
    extractList(list) {
        let markdown = '\n';
        const items = list.querySelectorAll('li');
        const isOrdered = list.tagName.toLowerCase() === 'ol';
        
        items.forEach((item, index) => {
            const prefix = isOrdered ? `${index + 1}.` : '-';
            const content = this.extractText(item);
            markdown += `${prefix} ${content}\n`;
        });
        
        return markdown + '\n';
    }

    // 提取图片
    extractImage(img) {
        if (!this.options.extractImages) return '';
        
        // 优先选择 srcset 中分辨率最高的图
        let src = '';
        const srcset = img.getAttribute('srcset');
        if (srcset) {
            const candidates = srcset.split(',').map(s => s.trim());
            const last = candidates[candidates.length - 1]?.split(' ')[0];
            if (last) src = last;
        }
        if (!src) {
            src = img.src || img.getAttribute('data-src') || img.getAttribute('data-original');
        }
        const alt = img.alt || img.title || '图片';
        
        if (src) {
            // 处理相对路径
            const absoluteSrc = this.refineImageUrl(src);
            return {
                markdown: `![${alt}](${absoluteSrc})`,
                imageInfo: {
                    url: absoluteSrc,
                    alt: alt,
                    filename: this.generateImageFilename(absoluteSrc, alt)
                }
            };
        }
        return null;
    }
    
    // 生成图片文件名
    generateImageFilename(url, alt) {
        try {
            const urlObj = new URL(url);
            const pathname = urlObj.pathname;
            const ext = pathname.match(/\.(jpg|jpeg|png|gif|webp|svg|ico)$/i)?.[0] || '.jpg';
            
            // 清理alt文本作为文件名
            const cleanAlt = alt.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_').substring(0, 50);
            const timestamp = Date.now();
            
            return `image_${cleanAlt}_${timestamp}${ext}`;
        } catch {
            return `image_${Date.now()}.jpg`;
        }
    }

    // 提取文本内容
    extractText(element) {
        let text = '';
        
        for (const node of element.childNodes) {
            if (node.nodeType === Node.TEXT_NODE) {
                text += node.textContent;
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                const tagName = node.tagName.toLowerCase();
                
                // 处理内联样式
                if (tagName === 'strong' || tagName === 'b') {
                    text += `**${this.extractText(node)}**`;
                } else if (tagName === 'em' || tagName === 'i') {
                    text += `*${this.extractText(node)}*`;
                } else if (tagName === 'code') {
                    text += `\`${node.textContent}\``;
                } else if (tagName === 'a') {
                    const href = node.href;
                    const linkText = this.extractText(node);
                    
                    // 检查是否为知识星球的主题链接
                    const isZsxqTopicLink = node.classList.contains('link-of-topic') || 
                                          node.closest('.topic-detail-panel') ||
                                          href.includes('zsxq.com');
                    
                    if (this.options.extractLinks || isZsxqTopicLink) {
                        if (linkText && href) {
                            text += `[${linkText}](${href})`;
                        } else if (linkText) {
                            text += linkText;
                        } else if (href) {
                            text += href;
                        }
                    } else {
                        // 不提取链接时只显示文本
                        if (linkText) {
                            text += linkText;
                        }
                    }
                } else if (tagName === 'br') {
                    text += '\n';
                } else if (tagName === 'img') {
                    const imgResult = this.extractImage(node);
                    if (imgResult) {
                        text += imgResult.markdown;
                    }
                } else {
                    text += this.extractText(node);
                }
            }
        }
        
        return text.trim();
    }

    // 提取引用块
    extractBlockquote(element) {
        const content = this.extractText(element);
        return '\n> ' + content.split('\n').join('\n> ') + '\n\n';
    }

    // 主要提取函数
    extractContent(rootElement = document.body) {
        // 锁定主内容区域并在原始文档上遍历，避免克隆导致的可见性判断失效
        const contentRoot = this.findBestContentRoot(rootElement);

        let markdown = '';
        let stats = {
            wordCount: 0,
            imageCount: 0
        };
        let images = [];
        
        // 获取页面标题
        const pageTitle = document.title;
        if (pageTitle) {
            markdown += `# ${pageTitle}\n\n`;
        }
        
        // 遍历所有元素（在原文档，可见性可靠）
        const walker = document.createTreeWalker(
            contentRoot,
            NodeFilter.SHOW_ELEMENT,
            {
                acceptNode: (node) => {
                    // 跳过隐藏与噪声
                    if (!this.isActuallyVisible(node) || this.isJunkNode(node)) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );
        
        let node;
        const processedNodes = new Set();
        
        while (node = walker.nextNode()) {
            if (processedNodes.has(node)) continue;
            
            const tagName = node.tagName.toLowerCase();
            
            // 处理标题
            if (/^h[1-6]$/.test(tagName)) {
                const level = parseInt(tagName[1]);
                const text = this.extractText(node);
                markdown += '\n' + '#'.repeat(level) + ' ' + text + '\n\n';
                processedNodes.add(node);
            }
            // 处理段落
            else if (tagName === 'p') {
                const text = this.extractText(node);
                if (text) {
                    markdown += text + '\n\n';
                    this.incrementStats(stats, text);
                }
                processedNodes.add(node);
            }
            // 处理以 div/section 承载的富文本段落
            else if (tagName === 'div' || tagName === 'section') {
                if (this.shouldTreatAsParagraph(node)) {
                    const text = this.extractText(node);
                    if (text) {
                        markdown += text + '\n\n';
                        this.incrementStats(stats, text);
                    }
                    processedNodes.add(node);
                }
            }
            // 处理列表
            else if (tagName === 'ul' || tagName === 'ol') {
                markdown += this.extractList(node);
                processedNodes.add(node);
            }
            // 处理表格
            else if (tagName === 'table' && this.options.preserveTables) {
                markdown += this.extractTable(node);
                processedNodes.add(node);
            }
            // 处理代码块
            else if (tagName === 'pre' || (tagName === 'code' && node.parentElement.tagName !== 'PRE')) {
                markdown += this.extractCodeBlock(node);
                processedNodes.add(node);
            }
            // 处理引用
            else if (tagName === 'blockquote') {
                markdown += this.extractBlockquote(node);
                processedNodes.add(node);
            }
            // 处理图片
            else if (tagName === 'img') {
                const imgResult = this.extractImage(node);
                if (imgResult) {
                    markdown += imgResult.markdown + '\n\n';
                    images.push(imgResult.imageInfo);
                    stats.imageCount++;
                }
                processedNodes.add(node);
            }
            // 处理文章容器
            else if (tagName === 'article' || tagName === 'section' || tagName === 'main') {
                // 递归处理容器内容
                const heading = this.getHeadingLevel(node);
                if (heading > 0) {
                    const text = this.extractText(node);
                    markdown += '\n' + '#'.repeat(heading) + ' ' + text + '\n\n';
                }
            }
        }
        
        // 添加样式元数据（如果启用）
        if (this.options.preserveStyle) {
            const bodyStyles = this.getComputedStyles(document.body);
            const metadata = `\n---\n` +
                `原始样式信息:\n` +
                `字体: ${bodyStyles.fontFamily}\n` +
                `字号: ${bodyStyles.fontSize}\n` +
                `行高: ${bodyStyles.lineHeight}\n` +
                `字间距: ${bodyStyles.letterSpacing}\n` +
                `---\n`;
            markdown = metadata + markdown;
        }
        
        // 如果字数明显过少，启用宽松兜底提取
        if (stats.wordCount < 100) {
            const relaxed = this.relaxedExtract(contentRoot);
            if (relaxed && relaxed.length > markdown.length * 0.5) {
                // 只有当兜底提取的内容明显更丰富时才使用
                markdown = relaxed;
                // 重新统计
                stats.wordCount = 0;
                this.incrementStats(stats, relaxed);
            }
        }

        // 去重与清理
        const finalMarkdown = this.normalizeMarkdown(markdown).trim();
        
        return {
            markdown: finalMarkdown,
            stats: stats,
            images: images
        };
    }
}

// 监听来自popup的消息
chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
    const extractor = new MarkdownExtractor();
    
    if (request.action === 'extract') {
        extractor.options = request.options || extractor.options;
        
        try {
            const result = extractor.extractContent();
            sendResponse({
                success: true,
                data: result
            });
        } catch (error) {
            sendResponse({
                success: false,
                error: error.message
            });
        }
    }
    else if (request.action === 'detect-layout') {
        try {
            const layout = extractor.detectPageLayout();
            sendResponse({
                success: true,
                data: layout
            });
        } catch (error) {
            sendResponse({
                success: false,
                error: error.message
            });
        }
    }
    else if (request.action === 'extract-with-links') {
        extractor.options = request.options || extractor.options;
        
        try {
            // 先提取当前页面内容
            const currentPageContent = extractor.extractContent();
            
            // 检测页面布局和链接
            const layout = extractor.detectPageLayout();
            
            // 收集所有需要深度提取的链接
            let allLinks = [];
            
            if (layout.isZsxqPage && layout.zsxqColumns.length > 0) {
                // 知识星球专用处理
                layout.zsxqColumns.forEach(column => {
                    const deepLinks = column.links.filter(link => link.needsDeepExtraction);
                    allLinks = allLinks.concat(deepLinks.map(link => ({
                        ...link,
                        column: column.title,
                        columnIndex: layout.zsxqColumns.indexOf(column)
                    })));
                });
            } else {
                // 通用处理
                if (layout.hasColumns) {
                    layout.columns.forEach(column => {
                        const deepLinks = column.links.filter(link => link.needsDeepExtraction);
                        allLinks = allLinks.concat(deepLinks);
                    });
                }
                
                if (layout.hasArticleList) {
                    allLinks = allLinks.concat(layout.articleLinks);
                }
            }
            
            // 检测页面内的 a.link-of-topic 链接
            const topicLinks = document.querySelectorAll('a.link-of-topic');
            topicLinks.forEach(link => {
                allLinks.push({
                    url: link.href,
                    title: link.textContent.trim() || '主题链接',
                    description: '',
                    element: link,
                    needsDeepExtraction: true,
                    isTopicLink: true
                });
            });
            
            sendResponse({
                success: true,
                data: {
                    currentPage: currentPageContent,
                    layout: layout,
                    deepLinks: allLinks,
                    zsxqColumns: layout.zsxqColumns || [],
                    targetColumns: layout.targetColumns || []
                }
            });
        } catch (error) {
            sendResponse({
                success: false,
                error: error.message
            });
        }
    }
    else if (request.action === 'extract-zsxq-columns') {
        // 专门用于提取知识星球目标栏目内容
        extractor.options = request.options || extractor.options;
        extractor.options.extractLinks = true; // 强制开启链接提取
        
        try {
            console.log('=== 知识星球栏目提取开始 ===');
            console.log('当前URL:', window.location.href);
            console.log('页面标题:', document.title);
            
            const layout = extractor.detectPageLayout();
            console.log('页面布局检测结果:', layout);
            
            if (!layout.isZsxqPage) {
                console.warn('页面检测结果: 非知识星球页面');
                sendResponse({
                    success: false,
                    error: '当前页面不是知识星球页面',
                    debugInfo: {
                        url: window.location.href,
                        hostname: window.location.hostname,
                        title: document.title
                    }
                });
                return;
            }
            
            console.log(`检测到 ${layout.zsxqColumns.length} 个目标栏目`);
            
            // 提取所有目标栏目的详细内容
            const columnsData = [];
            
            layout.zsxqColumns.forEach((column, index) => {
                console.log(`处理栏目 ${index + 1}: ${column.title}`);
                console.log(`- 文章数量: ${column.articles.length}`);
                console.log(`- 链接数量: ${column.links.length}`);
                
                const columnResult = {
                    title: column.title,
                    index: index + 1,
                    articleCount: column.articles.length,
                    articles: column.articles,
                    links: column.links,
                    summary: `共有 ${column.articles.length} 篇文章`
                };
                
                // 为每篇文章生成预览
                columnResult.articles.forEach((article, articleIndex) => {
                    if (article.element) {
                        const preview = extractor.extractText(article.element).substring(0, 200);
                        article.preview = preview || '无预览内容';
                        console.log(`  文章 ${articleIndex + 1}: ${article.title}`);
                    }
                });
                
                columnsData.push(columnResult);
            });
            
            const result = {
                pageType: 'zsxq-columns',
                totalColumns: columnsData.length,
                columns: columnsData,
                extractedAt: new Date().toISOString(),
                pageUrl: window.location.href,
                debugInfo: {
                    detectedElements: layout.zsxqColumns.length,
                    totalArticles: columnsData.reduce((sum, col) => sum + col.articleCount, 0),
                    pageStructure: {
                        hasNameDivs: document.querySelectorAll('div.name').length,
                        hasListContainers: document.querySelectorAll('div.list-container').length,
                        hasContentDivs: document.querySelectorAll('div.content').length
                    }
                }
            };
            
            console.log('=== 提取完成 ===');
            console.log('提取结果:', result);
            
            sendResponse({
                success: true,
                data: result
            });
            
        } catch (error) {
            console.error('知识星球栏目提取失败:', error);
            sendResponse({
                success: false,
                error: error.message,
                debugInfo: {
                    url: window.location.href,
                    error: error.stack,
                    pageElements: {
                        totalElements: document.querySelectorAll('*').length,
                        visibleElements: Array.from(document.querySelectorAll('*')).filter(el => 
                            extractor.isActuallyVisible(el)).length
                    }
                }
            });
        }
    }
    else if (request.action === 'extract-article-element') {
        // 提取特定文章元素的内容
        try {
            const article = request.article;
            console.log(`收到提取文章元素请求: ${article.title}`);
            
            // 尝试通过标题查找对应的文章元素
            const content = extractor.findAndExtractArticleContent(article);
            
            if (content && content.trim().length > 0) {
                console.log(`文章元素内容提取成功: ${content.length} 字符`);
                sendResponse({
                    success: true,
                    content: content
                });
            } else {
                console.warn(`文章元素内容提取为空: ${article.title}`);
                sendResponse({
                    success: false,
                    error: '文章内容为空或未找到对应元素'
                });
            }
        } catch (error) {
            console.error('文章元素提取异常:', error);
            sendResponse({
                success: false,
                error: error.message
            });
        }
    }
    
    return true; // 保持消息通道开放
});