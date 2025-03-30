// 管理模块 - 包含数据源管理和权限管理功能

// 导入toast提示组件
import { showToast } from './toast.js';

// 初始化管理模块
export function initManagementModule() {
    // 添加管理按钮到页面
    addManagementButtons();
}

// 页面加载时初始化管理模块
document.addEventListener('DOMContentLoaded', () => {
    initManagementModule();
});

// 添加管理按钮到页面
function addManagementButtons() {
    // 创建数据源管理按钮
    const dataSourceBtn = document.createElement('button');
    dataSourceBtn.id = 'dataSourceBtn';
    dataSourceBtn.className = 'config-btn';
    dataSourceBtn.textContent = '数据源管理';
    dataSourceBtn.addEventListener('click', () => showToast('功能开发中', 'info'));
    
    // 创建权限管理按钮
    const permissionBtn = document.createElement('button');
    permissionBtn.id = 'permissionBtn';
    permissionBtn.className = 'config-btn';
    permissionBtn.textContent = '权限管理';
    permissionBtn.addEventListener('click', () => showToast('功能开发中', 'info'));
    
    // 将按钮添加到页面顶部的工作台标题左侧
    const chatHeader = document.querySelector('.chat-header');
    if (chatHeader) {
        // 确保chat-header已设置为flex布局
        chatHeader.style.display = 'flex';
        chatHeader.style.alignItems = 'center';
        chatHeader.style.justifyContent = 'space-between';
        
        // 创建左侧按钮容器
        let leftButtonContainer = chatHeader.querySelector('.left-management-buttons');
        
        // 如果找不到左侧按钮容器，创建一个新的
        if (!leftButtonContainer) {
            leftButtonContainer = document.createElement('div');
            leftButtonContainer.className = 'left-management-buttons';
            leftButtonContainer.style.display = 'flex';
            leftButtonContainer.style.gap = '10px';
            leftButtonContainer.style.marginRight = 'auto'; // 确保它在左侧
            chatHeader.insertBefore(leftButtonContainer, chatHeader.firstChild); // 插入到最前面
        }
        
        // 清空现有的左侧按钮容器内容
        leftButtonContainer.innerHTML = '';
        
        // 获取系统配置按钮
        const configBtn = document.getElementById('configBtn');
        
        // 先将系统配置按钮添加到左侧容器中（如果存在）
        if (configBtn) {
            // 从原位置移除系统配置按钮
            if (configBtn.parentNode) {
                configBtn.parentNode.removeChild(configBtn);
            }
            // 添加到左侧按钮容器
            leftButtonContainer.appendChild(configBtn);
        }
        
        // 然后添加数据源管理和权限管理按钮到左侧
        leftButtonContainer.appendChild(dataSourceBtn);
        leftButtonContainer.appendChild(permissionBtn);
    } else {
        document.body.appendChild(dataSourceBtn);
        document.body.appendChild(permissionBtn);
    }
}

// 显示数据源管理对话框
function showDataSourceDialog() {
    // 创建对话框
    const dialog = document.createElement('div');
    dialog.className = 'dialog';
    
    // 创建对话框内容
    dialog.innerHTML = `
        <div class="dialog-title">数据源管理</div>
        <div class="dialog-content">
            <div class="developing-message">功能开发中，敬请期待...</div>
        </div>
        <div class="dialog-actions">
            <button id="closeDataSourceDialogBtn" class="dialog-btn dialog-btn-secondary">关闭</button>
        </div>
    `;
    
    // 添加对话框到页面
    document.body.appendChild(dialog);
    
    // 绑定事件
    document.getElementById('closeDataSourceDialogBtn').addEventListener('click', () => {
        document.body.removeChild(dialog);
    });
}

// 显示权限管理对话框
function showPermissionDialog() {
    // 创建对话框
    const dialog = document.createElement('div');
    dialog.className = 'dialog';
    
    // 创建对话框内容
    dialog.innerHTML = `
        <div class="dialog-title">权限管理</div>
        <div class="dialog-content">
            <div class="developing-message">功能开发中，敬请期待...</div>
        </div>
        <div class="dialog-actions">
            <button id="closePermissionDialogBtn" class="dialog-btn dialog-btn-secondary">关闭</button>
        </div>
    `;
    
    // 添加对话框到页面
    document.body.appendChild(dialog);
    
    // 绑定事件
    document.getElementById('closePermissionDialogBtn').addEventListener('click', () => {
        document.body.removeChild(dialog);
    });
}