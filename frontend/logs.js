// 全局变量
let logSocket = null; // Socket.IO连接
let isLogPanelOpen = true; // 日志面板默认展开
let autoCloseTimer = null; // 自动关闭计时器
let lastMessageTime = null; // 最后一条消息的接收时间

// DOM元素引用
let logPanel;
let logContent;
let logToggleBtn;

// 初始化日志功能
document.addEventListener('DOMContentLoaded', () => {
    // 获取DOM元素
    logPanel = document.getElementById('logPanel');
    logContent = document.getElementById('logContent');
    logToggleBtn = document.getElementById('logToggleBtn');
    
    // 绑定事件
    logToggleBtn.addEventListener('click', toggleLogPanel);
    
    // 设置初始状态 - 默认展开日志面板
    if (isLogPanelOpen) {
        logPanel.classList.add('open');
        logToggleBtn.textContent = '关闭日志';
    }
    
    // 初始化WebSocket连接
    initWebSocket();
});

// 初始化Socket.IO连接
function initWebSocket() {
    // 关闭之前的连接
    if (logSocket) {
        logSocket.disconnect();
    }
    
    // 创建新的Socket.IO连接
    logSocket = io('http://172.29.83,147:5000', {
        path: '/socket.io',
        reconnection: true,
        reconnectionDelay: 5000,
        reconnectionAttempts: Infinity
    });
    
    // 连接事件
    logSocket.on('connect', () => {
        addLogMessage('系统日志', '已连接工作台');
    });
    
    // 接收日志消息事件
    logSocket.on('log', (data) => {
        try {
            // 更新最后一条消息的接收时间
            lastMessageTime = new Date();
            
            // 自动展开日志面板
            if (!isLogPanelOpen) {
                openLogPanel();
            }
            
            // 重置自动关闭计时器
            resetAutoCloseTimer();
            
            // 检查是否有summary字段
            if (data.summary) {
                addLogMessage(data.type, data.message, data.summary);
            } else {
                addLogMessage(data.type, data.message);
            }
        } catch (error) {
            console.error('处理日志消息失败:', error);
            addLogMessage('系统日志', `接收到未知格式的消息`);
        }
    });
    
    // 接收流式日志消息事件
    logSocket.on('stream_log', (data) => {
        try {
            // 更新最后一条消息的接收时间
            lastMessageTime = new Date();
            
            // 自动展开日志面板
            if (!isLogPanelOpen) {
                openLogPanel();
            }
            
            // 重置自动关闭计时器
            resetAutoCloseTimer();
            
            // 处理流式日志
            handleStreamLog(data);
        } catch (error) {
            console.error('处理流式日志消息失败:', error);
            addLogMessage('系统日志', `接收到未知格式的流式消息`);
        }
    });
    
    // 重新连接事件
    logSocket.on('reconnect_attempt', () => {
        addLogMessage('系统日志', '正在尝试重新连接...');
    });
    
    // 连接错误事件
    logSocket.on('connect_error', (error) => {
        console.error('Socket.IO连接错误:', error);
        addLogMessage('系统日志', 'Socket.IO连接发生错误');
    });
    
    // 连接断开事件
    logSocket.on('disconnect', (reason) => {
        addLogMessage('系统日志', 'Socket.IO连接已断开: ' + reason);
    });
}

// 重置自动关闭计时器
function resetAutoCloseTimer() {
    // 清除之前的计时器
    if (autoCloseTimer) {
        clearTimeout(autoCloseTimer);
    }
    
    // 设置新的计时器，3秒后自动关闭日志面板
    autoCloseTimer = setTimeout(() => {
        // 只有在没有新消息的情况下才关闭
        const now = new Date();
        if (lastMessageTime && (now - lastMessageTime) >= 5000) {
            closeLogPanel();
        }
    }, 3000);
}

// 打开日志面板
function openLogPanel() {
    isLogPanelOpen = true;
    logPanel.classList.add('open');
    logToggleBtn.textContent = '关闭日志';
    // 移除新日志提示
    logToggleBtn.classList.remove('has-new-logs');
}

// 关闭日志面板
function closeLogPanel() {
    isLogPanelOpen = false;
    logPanel.classList.remove('open');
    logToggleBtn.textContent = '查看日志';
}

// 添加日志消息到面板
function addLogMessage(type, message, summary = null) {
    // 创建日志项
    const logItem = document.createElement('div');
    logItem.className = `log-item ${type === 'ai' ? 'ai-log' : 'system-log'}`;
    
    // 创建时间戳
    const timestamp = document.createElement('span');
    timestamp.className = 'log-timestamp';
    timestamp.textContent = new Date().toLocaleTimeString();
    logItem.appendChild(timestamp);
    
    // 创建类型标签
    const typeLabel = document.createElement('span');
    typeLabel.className = 'log-type';
    typeLabel.textContent = `[${type}]`;
    logItem.appendChild(typeLabel);
    
    // 创建消息内容
    const messageContent = document.createElement('span');
    messageContent.className = 'log-message';
    
    // 如果有summary则显示summary，否则显示message
    if (summary) {
        messageContent.textContent = summary;
        messageContent.title = message; // 添加title属性用于悬停提示
        messageContent.dataset.fullMessage = message; // 存储完整消息用于复制
        
        // 添加鼠标悬停事件
        messageContent.style.cursor = 'pointer'; // 改变鼠标样式
        
        // 添加点击事件，复制message到剪贴板
        messageContent.addEventListener('click', () => {
            navigator.clipboard.writeText(message).then(() => {
                // 可以添加一个临时提示，表示复制成功
                const originalText = messageContent.textContent;
                messageContent.textContent = '已复制到剪贴板!';
                setTimeout(() => {
                    messageContent.textContent = originalText;
                }, 1000);
            }).catch(err => {
                console.error('复制失败:', err);
            });
        });
    } else {
        messageContent.textContent = message;
    }
    
    logItem.appendChild(messageContent);
    
    // 添加到日志内容区域
    logContent.appendChild(logItem);
    
    // 滚动到底部
    logContent.scrollTop = logContent.scrollHeight;
    
    // 如果日志面板关闭，显示提示标记
    if (!isLogPanelOpen) {
        logToggleBtn.classList.add('has-new-logs');
    }
    
    // 返回创建的日志项，以便其他函数可以引用
    return logItem;
}

// 切换日志面板显示/隐藏
function toggleLogPanel() {
    isLogPanelOpen = !isLogPanelOpen;
    
    if (isLogPanelOpen) {
        // 打开日志面板
        openLogPanel();
        // 重置自动关闭计时器
        resetAutoCloseTimer();
    } else {
        // 关闭日志面板
        closeLogPanel();
        // 清除自动关闭计时器
        if (autoCloseTimer) {
            clearTimeout(autoCloseTimer);
            autoCloseTimer = null;
        }
    }
}

// 发送HTTP日志（供其他模块调用）
async function sendLog(type, message, summary = null) {
    try {
        const logData = { type, message };
        
        // 如果有summary，添加到请求体中
        if (summary) {
            logData.summary = summary;
        }
        
        const response = await fetch('http://localhost:5000/api/log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(logData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        return true;
    } catch (error) {
        console.error('发送日志失败:', error);
        // 本地添加错误日志
        addLogMessage('系统日志', `发送日志失败: ${error.message}`);
        return false;
    }
}

// 处理流式日志消息
let currentStreamLogItem = null;
let currentStreamSummary = null;

function handleStreamLog(data) {
    // 如果是流式输出的第一个token，创建新的日志项
    if (data.is_first) {
        currentStreamLogItem = addLogMessage(data.type, data.message, data.summary);
        currentStreamSummary = data.summary;
        
        // 创建或获取消息内容元素
        let messageContent = currentStreamLogItem.querySelector('.log-message');
        if (!messageContent) {
            messageContent = document.createElement('span');
            messageContent.className = 'log-message';
            currentStreamLogItem.appendChild(messageContent);
        }
        
        // 初始化内容
        messageContent.textContent = data.message;
    } else if (currentStreamLogItem) {
        // 获取消息内容元素
        const messageContent = currentStreamLogItem.querySelector('.log-message');
        if (messageContent) {
            // 追加新的token
            messageContent.textContent += data.message;
        }
    } else {
        // 如果没有当前流式日志项，创建一个新的
        currentStreamLogItem = addLogMessage(data.type, data.message, data.summary);
        currentStreamSummary = data.summary;
    }
    
    // 滚动到底部
    logContent.scrollTop = logContent.scrollHeight;
}

// 导出函数供其他模块使用
export { addLogMessage, sendLog };