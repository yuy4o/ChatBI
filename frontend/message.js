// 保存所有元数据的全局变量
import { showToast } from './toast.js';

let savedMetadata = {
    ddl: [],
    freeshot: [],
    term: []
};

// 标记是否已经召回过元数据
let hasFetchedMetadata = false;

/**
 * 处理聊天消息的方法
 * @param {string} text - 用户输入的文本
 * @param {Object} schema - 收集到的高亮元数据
 * @returns {Promise<void>}
 */
async function chat(text, schema) {
    console.log('Chat method called with:', { text, schema });
    
    try {
        let requestBody = {
            query: text,
            schema: schema || []
        };
        
        // 只在第一次聊天时获取元数据
        if (!hasFetchedMetadata) {
            await fetchAndDisplayDDL(requestBody);
            await fetchAndDisplayFreeshot(requestBody);
            await fetchAndDisplayTerm(requestBody);
            hasFetchedMetadata = true;
        }
        
        // 添加用户消息到聊天界面
        addMessage(text, 'user');

        // 恢复发送按钮状态
        const sendBtn = document.getElementById('sendBtn');
        sendBtn.classList.remove('loading-state');
        sendBtn.textContent = '发送';
        window.isSending = false;
        
        await fetchAndDisplaySQL(requestBody);
    } catch (error) {
        console.error('处理消息时出错:', error);
        addMessage('处理消息时出错，请重试', 'system');
    }
}

/**
 * 添加消息到聊天界面
 * @param {string} content - 消息内容
 * @param {string} type - 消息类型 ('user' 或 'system')
 */
function addMessage(content, type) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    // 如果是系统消息，支持Markdown格式
    if (type === 'system') {
        // 创建内容容器
        const contentDiv = document.createElement('div');
        contentDiv.className = 'markdown-content';
        
        // 处理Markdown格式
        // 处理代码块
        let formattedContent = content.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="code-block"><code class="language-$1">$2</code></pre>');
        
        // 处理行内代码
        formattedContent = formattedContent.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
        
        // 处理标题
        formattedContent = formattedContent.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        formattedContent = formattedContent.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        formattedContent = formattedContent.replace(/^# (.+)$/gm, '<h1>$1</h1>');
        
        // 处理列表
        formattedContent = formattedContent.replace(/^- (.+)$/gm, '<li>$1</li>');
        formattedContent = formattedContent.replace(/(<li>.+<\/li>\n)+/g, '<ul>$&</ul>');
        
        // 处理粗体和斜体
        formattedContent = formattedContent.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        formattedContent = formattedContent.replace(/\*(.+?)\*/g, '<em>$1</em>');
        
        // 处理换行
        formattedContent = formattedContent.replace(/\n/g, '<br>');
        
        contentDiv.innerHTML = formattedContent;
        messageDiv.appendChild(contentDiv);
    } else {
        messageDiv.textContent = content;
    }
    
    chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * 添加元数据消息到聊天界面
 * @param {string} title - 元数据标题
 * @param {string} type - 元数据类型 ('ddl', 'freeshot', 或 'term')
 * @param {Array} metadata - 元数据列表
 * @returns {HTMLElement} - 创建的元数据消息元素
 */
function addMetadataMessage(title, type, metadata) {
    const chatMessages = document.getElementById('chatMessages');
    
    // 创建元数据消息容器
    const messageDiv = document.createElement('div');
    messageDiv.className = `message system-message metadata-message ${type}-message`;
    messageDiv.dataset.type = type;
    
    // 创建标题
    const titleDiv = document.createElement('div');
    titleDiv.className = 'metadata-title';
    titleDiv.textContent = title;
    messageDiv.appendChild(titleDiv);
    
    // 创建元数据列表容器
    const metadataList = document.createElement('div');
    metadataList.className = 'metadata-list';
    messageDiv.appendChild(metadataList);
    
    // 添加元数据项
    metadata.forEach((item, index) => {
        const metadataItem = createMetadataItem(item, index, type);
        metadataList.appendChild(metadataItem);
    });
    
    // 添加到聊天界面
    chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

/**
 * 创建元数据项
 * @param {Object} item - 元数据项
 * @param {number} index - 索引
 * @param {string} type - 元数据类型
 * @returns {HTMLElement} - 创建的元数据项元素
 */
function createMetadataItem(item, index, type) {
    const metadataItem = document.createElement('div');
    metadataItem.className = 'metadata-item';
    metadataItem.dataset.index = index;
    
    // 创建名称容器
    const nameContainer = document.createElement('div');
    nameContainer.className = 'metadata-name-container';
    
    // 创建名称标签
    const nameLabel = document.createElement('div');
    nameLabel.className = 'metadata-label';
    nameLabel.textContent = '名称:';
    nameContainer.appendChild(nameLabel);
    
    // 创建名称内容（可编辑）
    const nameContent = document.createElement('div');
    nameContent.className = 'metadata-name';
    nameContent.contentEditable = true;
    nameContent.textContent = item.name;
    nameContent.addEventListener('blur', () => {
        // 更新保存的元数据
        savedMetadata[type][index].name = nameContent.textContent;
    });
    nameContainer.appendChild(nameContent);
    
    metadataItem.appendChild(nameContainer);
    
    // 创建内容容器
    const contentContainer = document.createElement('div');
    contentContainer.className = 'metadata-content-container';
    
    // 创建内容标签
    const contentLabel = document.createElement('div');
    contentLabel.className = 'metadata-label';
    contentLabel.textContent = '内容:';
    contentContainer.appendChild(contentLabel);
    
    // 创建内容（可编辑）
    const content = document.createElement('pre');
    content.className = 'metadata-content';
    content.contentEditable = true;
    content.textContent = item.content;
    content.addEventListener('blur', () => {
        // 更新保存的元数据
        savedMetadata[type][index].content = content.textContent;
    });
    contentContainer.appendChild(content);
    
    metadataItem.appendChild(contentContainer);
    
    // 创建删除按钮
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'metadata-delete-btn';
    deleteBtn.textContent = '删除';
    deleteBtn.addEventListener('click', () => {
        // 从DOM中移除
        metadataItem.remove();
        // 从保存的元数据中移除
        savedMetadata[type].splice(index, 1);
        // 更新后续元素的索引
        const items = document.querySelectorAll(`.metadata-message.${type}-message .metadata-item`);
        items.forEach((item, i) => {
            if (i >= index) {
                item.dataset.index = i;
            }
        });
    });
    metadataItem.appendChild(deleteBtn);
    
    return metadataItem;
}

/**
 * 添加SQL消息到聊天界面
 * @param {Object} data - SQL数据
 * @returns {HTMLElement} - 创建的SQL消息元素
 */
function addSQLMessage(data) {
    const chatMessages = document.getElementById('chatMessages');
    
    // 创建SQL消息容器
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system-message sql-message';
    
    // 如果有文本内容，添加文本部分
    if (data.content) {
        const contentDiv = document.createElement('div');
        contentDiv.className = 'sql-content-text';
        
        // 支持Markdown格式
        try {
            // 处理Markdown格式
            // 处理代码块
            let formattedContent = data.content.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="code-block"><code class="language-$1">$2</code></pre>');
            
            // 处理行内代码
            formattedContent = formattedContent.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
            
            // 处理标题
            formattedContent = formattedContent.replace(/^### (.+)$/gm, '<h3>$1</h3>');
            formattedContent = formattedContent.replace(/^## (.+)$/gm, '<h2>$1</h2>');
            formattedContent = formattedContent.replace(/^# (.+)$/gm, '<h1>$1</h1>');
            
            // 处理列表
            formattedContent = formattedContent.replace(/^- (.+)$/gm, '<li>$1</li>');
            formattedContent = formattedContent.replace(/(<li>.+<\/li>\n)+/g, '<ul>$&</ul>');
            
            // 处理粗体和斜体
            formattedContent = formattedContent.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            formattedContent = formattedContent.replace(/\*(.+?)\*/g, '<em>$1</em>');
            
            // 处理换行
            formattedContent = formattedContent.replace(/\n/g, '<br>');
            
            contentDiv.innerHTML = formattedContent;
        } catch (e) {
            contentDiv.textContent = data.content;
        }
        
        messageDiv.appendChild(contentDiv);
    }
    
    // 如果有SQL内容，添加SQL部分
    if (data.sql) {
        // 创建SQL部分容器
        const sqlContainer = document.createElement('div');
        sqlContainer.className = 'sql-container';
        
        // 创建SQL标签
        const sqlLabel = document.createElement('div');
        sqlLabel.className = 'sql-label';
        sqlLabel.textContent = 'SQL:';
        sqlContainer.appendChild(sqlLabel);
        
        // 创建SQL内容（可编辑）
        const sqlContent = document.createElement('pre');
        sqlContent.className = 'sql-content';
        sqlContent.contentEditable = true;
        sqlContent.textContent = data.sql;
        sqlContainer.appendChild(sqlContent);
        
        messageDiv.appendChild(sqlContainer);
        
        // 创建按钮容器
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'sql-button-container';

        // 创建执行按钮
        const executeBtn = document.createElement('button');
        executeBtn.className = 'sql-execute-btn';
        executeBtn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>';
        executeBtn.title = '执行SQL';
        executeBtn.addEventListener('click', async () => {
            try {
                // 获取SQL内容
                const sqlContent = sqlContainer.querySelector('.sql-content');
                const sql = sqlContent.textContent.trim();
                
                if (!sql) {
                    alert('SQL不能为空');
                    return;
                }
                
                // 显示加载中消息
                const loadingMessage = createLoadingMessage('正在执行SQL');
                document.getElementById('chatMessages').appendChild(loadingMessage);
                document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
                
                // 导入并执行SQL
                const { executeSQL, createDashboardMessage } = await import('./dashboard.js');
                const result = await executeSQL(sql);
                
                // 移除加载中消息
                loadingMessage.remove();
                
                // 创建数据看板消息
                createDashboardMessage(result, sql);
            } catch (error) {
                console.error('执行SQL失败:', error);
                alert(`执行SQL失败: ${error.message}`);
            }
        });
        
        // 创建点赞按钮
        const likeBtn = document.createElement('button');
        likeBtn.className = 'sql-like-btn';
        likeBtn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/></svg>';
        likeBtn.title = '点赞';
        likeBtn.addEventListener('click', async () => {
            try {
                // 获取SQL内容
                const sqlContent = sqlContainer.querySelector('.sql-content');
                const sql = sqlContent.textContent.trim();
                
                // 获取聊天消息历史
                const chatMessages = document.querySelectorAll('.message');
                const messages = [];
                
                // 构建消息历史
                chatMessages.forEach(msg => {
                    if (msg.classList.contains('user-message')) {
                        messages.push({ role: 'user', content: msg.textContent });
                    } else if (msg.classList.contains('system-message') && !msg.classList.contains('metadata-message') && !msg.classList.contains('loading-message')) {
                        let content = msg.textContent;
                        // 如果是SQL消息，添加SQL内容
                        if (msg.classList.contains('sql-message')) {
                            const sqlContent = msg.querySelector('.sql-content');
                            if (sqlContent) {
                                content += '\nSQL:\n' + sqlContent.textContent;
                            }
                        }
                        messages.push({ role: 'assistant', content: content });
                    }
                });
                
                // 构建请求体，与/sql-agent接口参数格式一致
                const requestBody = {
                    metadata: {
                        ddl: savedMetadata.ddl,
                        freeshot: savedMetadata.freeshot,
                        term: savedMetadata.term
                    },
                    messages: messages
                };
                
                // 调用/feedback_good接口
                fetch('http://localhost:5000/feedback_good', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestBody)
                });
                
                // 直接显示点赞成功提示，不等待接口返回
                showToast('点赞成功', 'success');
            } catch (error) {
                console.error('点赞失败:', error);
                showToast('点赞失败', 'error');
            }
        });

        // 将按钮添加到按钮容器中
        buttonContainer.appendChild(executeBtn);
        buttonContainer.appendChild(likeBtn);

        // 将按钮容器添加到SQL容器中
        sqlContainer.appendChild(buttonContainer);
    }
    
    // 添加到聊天界面
    chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

/**
 * 创建加载中消息
 * @param {string} text - 加载提示文本
 * @returns {HTMLElement} - 创建的加载中消息元素
 */
function createLoadingMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system-message loading-message';
    
    const textSpan = document.createElement('span');
    textSpan.textContent = text;
    messageDiv.appendChild(textSpan);
    
    const loadingSpan = document.createElement('span');
    loadingSpan.className = 'loading';
    messageDiv.appendChild(loadingSpan);
    
    return messageDiv;
}

/**
 * 获取并显示DDL元数据
 * @param {Object} schema - 高亮元数据
 */
async function fetchAndDisplayDDL(schema) {
    // 创建加载中消息
    const loadingMessage = createLoadingMessage('正在获取相关表信息');
    document.getElementById('chatMessages').appendChild(loadingMessage);
    document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
    
    try {
        // 发送请求获取DDL元数据
        const response = await fetch('http://localhost:5000/ddl', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(schema)
        });
        
        const data = await response.json();
        
        // 保存元数据
        savedMetadata.ddl = data.metadata;
        
        // 移除加载中消息
        loadingMessage.remove();
        
        // 添加元数据消息
        addMetadataMessage('相关表信息', 'ddl', data.metadata);
    } catch (error) {
        console.error('获取DDL元数据失败:', error);
        // 移除加载中消息
        loadingMessage.remove();
        // 添加错误消息
        addMessage('获取相关表信息失败，请重试', 'system');
        throw error;
    }
}

/**
 * 获取并显示Freeshot元数据
 * @param {Object} schema - 高亮元数据
 */
async function fetchAndDisplayFreeshot(schema) {
    // 创建加载中消息
    const loadingMessage = createLoadingMessage('正在获取相关示例');
    document.getElementById('chatMessages').appendChild(loadingMessage);
    document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
    
    try {
        // 发送请求获取Freeshot元数据
        const response = await fetch('http://localhost:5000/freeshot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(schema)
        });
        
        const data = await response.json();
        
        // 保存元数据
        savedMetadata.freeshot = data.metadata;
        
        // 移除加载中消息
        loadingMessage.remove();
        
        // 添加元数据消息
        addMetadataMessage('相关示例', 'freeshot', data.metadata);
    } catch (error) {
        console.error('获取Freeshot元数据失败:', error);
        // 移除加载中消息
        loadingMessage.remove();
        // 添加错误消息
        addMessage('获取相关示例失败，请重试', 'system');
        throw error;
    }
}

/**
 * 获取并显示Term元数据
 * @param {Object} schema - 高亮元数据
 */
async function fetchAndDisplayTerm(schema) {
    // 创建加载中消息
    const loadingMessage = createLoadingMessage('正在获取相关术语');
    document.getElementById('chatMessages').appendChild(loadingMessage);
    document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
    
    try {
        // 发送请求获取Term元数据
        const response = await fetch('http://localhost:5000/term', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(schema)
        });
        
        const data = await response.json();
        
        // 保存元数据
        savedMetadata.term = data.metadata;
        
        // 移除加载中消息
        loadingMessage.remove();
        
        // 添加元数据消息
        addMetadataMessage('相关术语', 'term', data.metadata);
    } catch (error) {
        console.error('获取Term元数据失败:', error);
        // 移除加载中消息
        loadingMessage.remove();
        // 添加错误消息
        addMessage('获取相关术语失败，请重试', 'system');
        throw error;
    }
}

/**
 * 获取并显示SQL消息
 */
async function fetchAndDisplaySQL(schema) {
    // 创建加载中消息
    const loadingMessage = createLoadingMessage('正在生成SQL');
    document.getElementById('chatMessages').appendChild(loadingMessage);
    document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
    
    try {
        // 获取用户输入的查询文本
        const userInput = schema.query;
        
        // 获取聊天消息历史
        const chatMessages = document.querySelectorAll('.message');
        const messages = [];
        
        // 构建消息历史
        chatMessages.forEach(msg => {
            if (msg.classList.contains('user-message')) {
                messages.push({ role: 'user', content: msg.textContent });
            } else if (msg.classList.contains('system-message') && !msg.classList.contains('metadata-message') && !msg.classList.contains('loading-message')) {
                let content = msg.textContent;
                // 如果是SQL消息，添加SQL内容
                if (msg.classList.contains('sql-message')) {
                    const sqlContent = msg.querySelector('.sql-content');
                    if (sqlContent) {
                        content += '\nSQL:\n' + sqlContent.textContent;
                    }
                }
                messages.push({ role: 'assistant', content: content });
            }
        });
        
        // 检查是否已存在相同的用户消息，避免重复添加
        const isDuplicate = messages.some(msg => 
            msg.role === 'user' && msg.content === userInput
        );
        
        if (!isDuplicate) {
            messages.push({ role: 'user', content: userInput });
        }
        
        // 发送请求获取SQL，使用新的请求体格式
        const response = await fetch('http://localhost:5000//sql-agent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                metadata: {
                    ddl: savedMetadata.ddl,
                    freeshot: savedMetadata.freeshot,
                    term: savedMetadata.term
                },
                messages: messages
            })
        });
        
        const data = await response.json();
        
        // 移除加载中消息
        loadingMessage.remove();
        
        // 处理返回的数据
        if (data.content || data.sql) {
            // 创建消息对象
            const messageData = {
                content: data.content || '',
                sql: data.sql || ''
            };
            
            // 如果只有content，显示为普通消息
            if (messageData.content && !messageData.sql) {
                addMessage(messageData.content, 'system');
            } else {
                // 否则显示为SQL消息
                addSQLMessage(messageData);
            }
        } else {
            // 如果没有返回内容，显示错误消息
            addMessage('未能生成有效的响应', 'system');
        }
    } catch (error) {
        console.error('获取SQL失败:', error);
        // 移除加载中消息
        loadingMessage.remove();
        // 添加错误消息
        addMessage('生成SQL失败，请重试', 'system');
        throw error;
    }
}

// 导出方法，使其可以被其他JS文件引用
export { chat };