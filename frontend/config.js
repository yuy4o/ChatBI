// 配置管理模块

// 全局变量
let configItems = [];

// 初始化配置管理
export function initConfigManager() {
    // 添加配置按钮到页面
    addConfigButton();
}

// 页面加载时初始化配置管理
document.addEventListener('DOMContentLoaded', () => {
    initConfigManager();
});

// 添加配置按钮到页面
function addConfigButton() {
    // 创建配置按钮
    const configBtn = document.createElement('button');
    configBtn.id = 'configBtn';
    configBtn.className = 'config-btn';
    configBtn.textContent = '系统配置';
    configBtn.addEventListener('click', showConfigDialog);
    
    // 将按钮添加到页面顶部的工作台标题右侧
    const chatHeader = document.querySelector('.chat-header');
    if (chatHeader) {
        // 确保chat-header已设置为flex布局
        chatHeader.style.display = 'flex';
        chatHeader.style.alignItems = 'center';
        chatHeader.style.justifyContent = 'space-between';
        
        // 查找已有的管理按钮容器
        let buttonContainer = chatHeader.querySelector('.management-buttons');
        
        // 如果找到按钮容器，将配置按钮添加到容器中
        if (buttonContainer) {
            buttonContainer.appendChild(configBtn);
        } else {
            // 如果没有找到按钮容器，直接添加到chat-header
            chatHeader.appendChild(configBtn);
        }
    } else {
        document.body.appendChild(configBtn);
    }
}

// 显示配置对话框
async function showConfigDialog() {
    // 获取当前配置
    await fetchConfigList();
    
    // 创建对话框
    const dialog = document.createElement('div');
    dialog.className = 'dialog config-dialog';
    
    // 设置对话框样式，确保可见
    dialog.style.position = 'fixed';
    dialog.style.top = '50%';
    dialog.style.left = '50%';
    dialog.style.transform = 'translate(-50%, -50%)';
    dialog.style.zIndex = '1000';
    
    // 创建对话框内容
    dialog.innerHTML = `
        <div class="dialog-title">系统配置</div>
        <div class="dialog-content" id="configContent">
            ${generateConfigFormHtml()}
        </div>
        <div class="dialog-actions">
            <button id="saveConfigBtn" class="dialog-btn dialog-btn-primary">保存</button>
            <button id="cancelConfigBtn" class="dialog-btn dialog-btn-secondary">取消</button>
        </div>
    `;
    
    // 添加对话框到页面
    document.body.appendChild(dialog);
    
    // 绑定事件
    document.getElementById('saveConfigBtn').addEventListener('click', saveConfig);
    
    // 添加背景遮罩
    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    overlay.style.zIndex = '999';
    document.body.appendChild(overlay);
    
    // 点击遮罩关闭对话框
    overlay.addEventListener('click', () => {
        document.body.removeChild(dialog);
        document.body.removeChild(overlay);
    });
    
    // 绑定取消按钮事件，确保同时移除对话框和遮罩
    document.getElementById('cancelConfigBtn').addEventListener('click', () => {
        document.body.removeChild(dialog);
        document.body.removeChild(overlay);
    });
    
    // 更新保存按钮事件，成功后同时移除遮罩
    const originalSaveBtn = document.getElementById('saveConfigBtn');
    const newSaveBtn = originalSaveBtn.cloneNode(true);
    originalSaveBtn.parentNode.replaceChild(newSaveBtn, originalSaveBtn);
    newSaveBtn.addEventListener('click', async () => {
        const success = await saveConfig();
        if (success) {
            document.body.removeChild(dialog);
            document.body.removeChild(overlay);
        }
    });
}

// 生成配置表单HTML
function generateConfigFormHtml() {
    if (configItems.length === 0) {
        return '<div class="config-empty">暂无配置项</div>';
    }
    
    let html = '<div class="config-form">';
    
    configItems.forEach(item => {
        html += `
            <div class="config-item" data-key="${item.key}">
                <label class="config-label">${item.name}</label>
                <input type="text" class="config-input" value="${item.value}" />
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

// 获取配置列表
async function fetchConfigList() {
    try {
        const response = await fetch('http://localhost:5000/config/list');
        const data = await response.json();
        configItems = data;
    } catch (error) {
        console.error('获取配置列表失败:', error);
        configItems = [];
    }
}

// 导入toast提示组件
import { showToast } from './toast.js';

// 保存配置
async function saveConfig() {
    // 收集表单数据
    const updatedConfig = [];
    const configForm = document.querySelector('.config-form');
    
    if (configForm) {
        const configItemElements = configForm.querySelectorAll('.config-item');
        configItemElements.forEach(item => {
            const key = item.getAttribute('data-key');
            const value = item.querySelector('.config-input').value;
            updatedConfig.push({ key, value });
        });
    }
    
    // 发送更新请求
    try {
        const response = await fetch('http://localhost:5000/config/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatedConfig)
        });
        
        if (response.ok) {
            showToast('配置更新成功', 'success');
            return true; // 返回成功状态
        } else {
            showToast('配置更新失败', 'error');
            return false; // 返回失败状态
        }
    } catch (error) {
        console.error('更新配置失败:', error);
        showToast('更新配置失败: ' + error.message, 'error');
        return false; // 返回失败状态
    }
}