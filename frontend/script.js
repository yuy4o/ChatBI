// 导入日志模块
import { addLogMessage, sendLog } from './logs.js';

// 全局变量
let currentUser = 'user1'; // 默认用户
let highlightedItems = new Set(); // 存储自动高亮项的ID
let manualHighlightedItems = new Set(); // 存储手动高亮项的ID
let isHidingNonHighlighted = false; // 是否隐藏非高亮项
let suggestTimer = null; // suggest请求的定时器
let isSending = false; // 是否正在发送消息
let isMetadataRetrieved = false; // 是否已完成元数据召回
let pendingUserInput = ''; // 待发送的用户输入

// DOM元素
const databaseTree = document.getElementById('databaseTree');
const toggleBtn = document.getElementById('toggleBtn');
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const metadataSearch = document.getElementById('metadataSearch');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 加载数据库列表
    loadDatabases();
    
    // 绑定事件
    toggleBtn.addEventListener('click', toggleNonHighlightedItems);
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 元数据搜索框的suggest功能
    metadataSearch.addEventListener('input', () => {
        // 清除之前的定时器
        if (suggestTimer) {
            clearTimeout(suggestTimer);
        }
        
        // 设置新的定时器，1秒后触发suggest请求
        suggestTimer = setTimeout(() => {
            const text = metadataSearch.value.trim();
            if (text) {
                requestSuggest(text);
            } else {
                // 如果输入为空，清除所有高亮
                clearHighlights();
                updateTreeVisibility();
            }
        }, 1000);
    });
});

// 加载数据库列表
async function loadDatabases() {
    try {
        const response = await fetch(`http://localhost:5000/metadata/dbs?user=${currentUser}`);
        const data = await response.json();
        
        // 清空现有内容
        databaseTree.innerHTML = '';
        
        // 创建数据库树形结构
        data.forEach(db => {
            const dbItem = createTreeItem(db.id, db.db, db.description, 'database');
            databaseTree.appendChild(dbItem);
        });
    } catch (error) {
        console.error('加载数据库失败:', error);
        // 显示错误消息
        databaseTree.innerHTML = '<div class="error">加载数据库失败，请重试</div>';
    }
}

// 加载表格列表
async function loadTables(dbId, dbElement) {
    try {
        const response = await fetch(`http://localhost:5000/metadata/tables?user=${currentUser}&db=${dbId}`);
        const data = await response.json();
        
        // 获取内容容器
        const contentContainer = dbElement.querySelector('.tree-item-content');
        contentContainer.innerHTML = '';
        
        // 创建表格树形结构
        data.forEach(table => {
            const tableItem = createTreeItem(table.id, table.table, table.description, 'table');
            contentContainer.appendChild(tableItem);
        });
    } catch (error) {
        console.error('加载表格失败:', error);
        // 显示错误消息
        const contentContainer = dbElement.querySelector('.tree-item-content');
        contentContainer.innerHTML = '<div class="error">加载表格失败，请重试</div>';
    }
}

// 加载字段列表
async function loadColumns(dbId, tableId, tableElement) {
    try {
        const response = await fetch(`http://localhost:5000/metadata/columns?user=${currentUser}&db=${dbId}&table=${tableId}`);
        const data = await response.json();
        
        // 获取内容容器
        const contentContainer = tableElement.querySelector('.tree-item-content');
        contentContainer.innerHTML = '';
        
        // 创建字段树形结构
        data.forEach(column => {
            const columnItem = createTreeItem(column.id, column.column, column.description, 'column', column.type);
            contentContainer.appendChild(columnItem);
        });
    } catch (error) {
        console.error('加载字段失败:', error);
        // 显示错误消息
        const contentContainer = tableElement.querySelector('.tree-item-content');
        contentContainer.innerHTML = '<div class="error">加载字段失败，请重试</div>';
    }
}

// 加载维度值列表
async function loadValues(dbId, tableId, columnId, columnElement) {
    try {
        const response = await fetch(`http://localhost:5000/metadata/values?user=${currentUser}&db=${dbId}&table=${tableId}&column=${columnId}`);
        const data = await response.json();
        
        // 获取内容容器
        const contentContainer = columnElement.querySelector('.tree-item-content');
        contentContainer.innerHTML = '';
        
        // 创建维度值树形结构
        data.forEach(value => {
            const valueItem = createTreeItem(value.id, value.value, value.description, 'value');
            contentContainer.appendChild(valueItem);
        });
    } catch (error) {
        console.error('加载维度值失败:', error);
        // 显示错误消息
        const contentContainer = columnElement.querySelector('.tree-item-content');
        contentContainer.innerHTML = '<div class="error">加载维度值失败，请重试</div>';
    }
}

// 创建树形项
function createTreeItem(id, name, description, type, dataType = '') {
    const item = document.createElement('div');
    item.className = 'tree-item';
    item.dataset.id = id;
    item.dataset.type = type;
    item.dataset.dataType = dataType;

    // 创建标题行
    const header = document.createElement('div');
    header.className = 'tree-item-header';

    // 创建展开/折叠图标（仅ENUM类型列和可展开层级显示）
    if (type !== 'value' && !(type === 'column' && dataType !== 'ENUM')) {
        const toggle = document.createElement('span');
        toggle.className = 'tree-toggle';
        toggle.textContent = '▶';
        header.appendChild(toggle);
    }

    // 创建名称，将字段英文名和类型信息放入title属性
    const nameSpan = document.createElement('span');
    nameSpan.className = 'tree-item-name';
    // 显示备注而不是字段名
    nameSpan.textContent = description || name;
    
    // 构建悬浮提示信息
    let tooltipText = '';
    // 将字段英文名放入悬浮提示
    if (dataType) {
        tooltipText = `字段名：${name}\n类型：${dataType}`;
    } else {
        tooltipText = name;
    }
    if (tooltipText) {
        nameSpan.title = tooltipText;
    }
    
    header.appendChild(nameSpan);
    
    item.appendChild(header);
    
    // 创建内容容器
    const content = document.createElement('div');
    content.className = 'tree-item-content';
    item.appendChild(content);
    
    // 绑定点击事件 - 展开/折叠功能
    header.addEventListener('click', async (e) => {
        if (type === 'value' || (type === 'column' && item.dataset.dataType !== 'ENUM')) return;

        // 阻止事件冒泡
        e.stopPropagation();
        
        // 切换展开/折叠状态
        item.classList.toggle('expanded');
        
        // 如果是展开状态且内容为空，则加载子项
        if (item.classList.contains('expanded') && content.children.length === 0) {
            // 显示加载中
            content.innerHTML = '<div class="loading"></div>';
            
            // 根据类型加载不同的数据
            switch (type) {
                case 'database':
                    await loadTables(id, item);
                    break;
                case 'table':
                    // 获取数据库ID
                    const dbId = item.closest('.tree-item[data-type="database"]').dataset.id;
                    await loadColumns(dbId, id, item);
                    break;
                case 'column':
                    // 获取数据库ID和表ID
                    const dbElement = item.closest('.tree-item[data-type="database"]');
                    const tableElement = item.closest('.tree-item[data-type="table"]');
                    const dbId2 = dbElement.dataset.id;
                    const tableId = tableElement.dataset.id;
                    await loadValues(dbId2, tableId, id, item);
                    break;
            }
        }
    });
    
    // 添加右键点击事件 - 手动高亮功能
    header.addEventListener('contextmenu', (e) => {
        // 阻止默认右键菜单
        e.preventDefault();
        
        // 切换手动高亮状态
        toggleManualHighlight(id, header);
    });
    
    return item;
}

// 收集高亮元素的元数据信息
function collectHighlightedMetadata() {
    const schema = [];
    const highlightedElements = document.querySelectorAll('.tree-item-header.highlighted, .tree-item-header.manual-highlighted');
    
    highlightedElements.forEach(header => {
        const item = header.closest('.tree-item');
        const id = item.dataset.id;
        const type = item.dataset.type;
        
        // 根据元素类型构建元数据
        switch (type) {
            case 'database':
                schema.push({
                    id,
                    db: item.querySelector('.tree-item-name').title,
                    description: item.querySelector('.tree-item-name').textContent
                });
                break;
            case 'table':
                const dbItem = item.closest('.tree-item[data-type="database"]');
                if (dbItem) {
                    const tableInfo = {
                        id,
                        table: item.querySelector('.tree-item-name').title,
                        description: item.querySelector('.tree-item-name').textContent
                    };
                    
                    // 查找或创建数据库对象
                    let dbInfo = schema.find(db => db.id === dbItem.dataset.id);
                    if (!dbInfo) {
                        dbInfo = {
                            id: dbItem.dataset.id,
                            db: dbItem.querySelector('.tree-item-name').title,
                            description: dbItem.querySelector('.tree-item-name').textContent,
                            tables: []
                        };
                        schema.push(dbInfo);
                    }
                    if (!dbInfo.tables) dbInfo.tables = [];
                    dbInfo.tables.push(tableInfo);
                }
                break;
            case 'column':
                const tableElement = item.closest('.tree-item[data-type="table"]');
                const dbElement = item.closest('.tree-item[data-type="database"]');
                if (tableElement && dbElement) {
                    const columnInfo = {
                        id,
                        column: item.querySelector('.tree-item-name').title.split('\n')[0].replace('字段名：', ''),
                        type: item.dataset.dataType,
                        description: item.querySelector('.tree-item-name').textContent
                    };
                    
                    // 查找或创建数据库和表对象
                    let dbInfo = schema.find(db => db.id === dbElement.dataset.id);
                    if (!dbInfo) {
                        dbInfo = {
                            id: dbElement.dataset.id,
                            db: dbElement.querySelector('.tree-item-name').title,
                            description: dbElement.querySelector('.tree-item-name').textContent,
                            tables: []
                        };
                        schema.push(dbInfo);
                    }
                    
                    let tableInfo = dbInfo.tables?.find(table => table.id === tableElement.dataset.id);
                    if (!tableInfo) {
                        tableInfo = {
                            id: tableElement.dataset.id,
                            table: tableElement.querySelector('.tree-item-name').title,
                            description: tableElement.querySelector('.tree-item-name').textContent,
                            columns: []
                        };
                        if (!dbInfo.tables) dbInfo.tables = [];
                        dbInfo.tables.push(tableInfo);
                    }
                    if (!tableInfo.columns) tableInfo.columns = [];
                    tableInfo.columns.push(columnInfo);
                }
                break;
            case 'value':
                const columnElement = item.closest('.tree-item[data-type="column"]');
                const valueTableElement = item.closest('.tree-item[data-type="table"]');
                const valueDbElement = item.closest('.tree-item[data-type="database"]');
                if (columnElement && valueTableElement && valueDbElement) {
                    const valueInfo = {
                        id,
                        value: item.querySelector('.tree-item-name').title,
                        desc: item.querySelector('.tree-item-name').textContent
                    };
                    
                    // 查找或创建数据库、表和列对象
                    let dbInfo = schema.find(db => db.id === valueDbElement.dataset.id);
                    if (!dbInfo) {
                        dbInfo = {
                            id: valueDbElement.dataset.id,
                            db: valueDbElement.querySelector('.tree-item-name').title,
                            description: valueDbElement.querySelector('.tree-item-name').textContent,
                            tables: []
                        };
                        schema.push(dbInfo);
                    }
                    
                    let tableInfo = dbInfo.tables?.find(table => table.id === valueTableElement.dataset.id);
                    if (!tableInfo) {
                        tableInfo = {
                            id: valueTableElement.dataset.id,
                            table: valueTableElement.querySelector('.tree-item-name').title,
                            description: valueTableElement.querySelector('.tree-item-name').textContent,
                            columns: []
                        };
                        if (!dbInfo.tables) dbInfo.tables = [];
                        dbInfo.tables.push(tableInfo);
                    }
                    
                    let columnInfo = tableInfo.columns?.find(col => col.id === columnElement.dataset.id);
                    if (!columnInfo) {
                        columnInfo = {
                            id: columnElement.dataset.id,
                            column: columnElement.querySelector('.tree-item-name').title.split('\n')[0].replace('字段名：', ''),
                            type: columnElement.dataset.dataType,
                            description: columnElement.querySelector('.tree-item-name').textContent,
                            values: []
                        };
                        if (!tableInfo.columns) tableInfo.columns = [];
                        tableInfo.columns.push(columnInfo);
                    }
                    if (!columnInfo.values) columnInfo.values = [];
                    columnInfo.values.push(valueInfo);
                }
                break;
        }
    });
    
    return schema;
}

// 导入chat方法
import { chat } from './message.js';

// 发送消息
async function sendMessage() {
    const text = userInput.value.trim();
    if (!text || isSending) return;
    
    // 设置发送状态
    isSending = true;
    sendBtn.classList.add('loading-state');
    
    // 如果尚未完成元数据召回，先进行元数据召回
    if (!isMetadataRetrieved) {
        // 保存当前用户输入，以便稍后发送
        pendingUserInput = text;
        
        // 禁用输入框，但保留文本
        userInput.disabled = true;
        
        // 更新发送按钮状态
        sendBtn.textContent = '正在匹配相关元数据';
        
        try {
            // 调用suggest接口进行元数据召回
            await requestSuggest(text);
            
            // 标记元数据召回已完成
            isMetadataRetrieved = true;
            
            // 恢复输入框状态
            userInput.disabled = false;
            
            // 自动发送之前保存的用户输入
            await sendSQLRequest(pendingUserInput);
        } catch (error) {
            console.error('元数据召回失败:', error);
            addMessage('元数据召回失败，请重试', 'system');
            
            // 恢复输入框状态
            userInput.disabled = false;
            userInput.value = pendingUserInput;
            pendingUserInput = '';
        } finally {
            // 恢复发送按钮状态
            isSending = false;
            sendBtn.classList.remove('loading-state');
            sendBtn.textContent = '发送';
        }
    } else {
        // 已完成元数据召回，直接发送SQL请求
        userInput.value = '';
        await sendSQLRequest(text);
        
        // 恢复发送按钮状态
        isSending = false;
        sendBtn.classList.remove('loading-state');
        sendBtn.textContent = '发送';
    }
}

// 发送SQL请求
async function sendSQLRequest(text) {
    try {
        // 收集高亮元素的元数据
        const schema = collectHighlightedMetadata();
        // 调用chat方法，将用户输入和高亮元数据作为参数传递
        await chat(text, schema);
    } catch (error) {
        console.error('发送消息失败:', error);
    }
}

// 请求建议
async function requestSuggest(text) {
    try {
        const response = await fetch('http://localhost:5000/suggest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });
        
        const data = await response.json();
        
        // 清除所有高亮
        clearHighlights();
        
        // 处理建议结果
        await processSuggestResult(data);
        
        // 自动切换到隐藏非高亮元素的状态
        if (!isHidingNonHighlighted && data.length > 0) {
            isHidingNonHighlighted = true;
            toggleBtn.textContent = '显示所有元素';
        }
        
        // 更新树形结构可见性
        updateTreeVisibility();
        
        // 标记元数据召回已完成
        if (data.length > 0) {
            isMetadataRetrieved = true;
            return true;
        }
        return false;
    } catch (error) {
        console.error('获取建议失败:', error);
        return false;
    }
}

// 处理建议结果
async function processSuggestResult(data) {
    // 清空高亮项集合
    highlightedItems.clear();
    
    // 遍历数据库
    for (const db of data) {
        // 高亮数据库
        highlightItem(db.id);
        
        // 展开数据库
        await expandItem(db.id);
        
        // 遍历表格
        if (db.tables) {
            for (const table of db.tables) {
                // 高亮表格
                highlightItem(table.id);
                
                // 展开表格
                await expandItem(table.id);
                
                // 遍历字段
                if (table.columns) {
                    for (const column of table.columns) {
                        // 高亮字段
                        highlightItem(column.id);
                        
                        // 展开字段
                        await expandItem(column.id);
                        
                        // 遍历维度值
                        if (column.values) {
                            for (const value of column.values) {
                                // 高亮维度值
                                highlightItem(value.id);
                            }
                        }
                    }
                }
            }
        }
    }
    
    // 确保所有异步加载完成后再次更新可见性
    updateTreeVisibility();
}

// 高亮项（自动高亮）
function highlightItem(id) {
    highlightedItems.add(id);
    
    // Use the correct attribute selector that matches how you set it
    const item = document.querySelector(`.tree-item[data-id="${id}"]`);
    if (item) {
        const header = item.querySelector('.tree-item-header');
        header.classList.add('highlighted');
        if (header.classList.contains('manual-highlighted')) {
            header.classList.remove('manual-highlighted');
            manualHighlightedItems.delete(id);
        }
    }
}


// 切换手动高亮状态
function toggleManualHighlight(id, headerElement) {
    // 检查是否已经是手动高亮
    if (manualHighlightedItems.has(id)) {
        // 移除手动高亮
        manualHighlightedItems.delete(id);
        headerElement.classList.remove('manual-highlighted');
    } else {
        // 添加手动高亮
        manualHighlightedItems.add(id);
        headerElement.classList.add('manual-highlighted');
        // 如果已经是自动高亮，则移除自动高亮样式
        if (headerElement.classList.contains('highlighted')) {
            headerElement.classList.remove('highlighted');
            highlightedItems.delete(id);
        }
    }
    
    // 更新树形结构可见性
    updateTreeVisibility();
}

// 展开项
async function expandItem(id) {
    // 获取对应元素
    const item = document.querySelector(`.tree-item[data-id="${id}"]`);
    if (item && !item.classList.contains('expanded')) {
        // 模拟点击展开
        item.querySelector('.tree-item-header').click();
        
        // 等待加载完成
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // 确保子项已加载完成
        const contentContainer = item.querySelector('.tree-item-content');
        if (contentContainer && contentContainer.querySelector('.loading')) {
            // 如果还在加载中，多等待一段时间
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
}

// 清除所有高亮
function clearHighlights() {
    // 清空高亮项集合
    highlightedItems.clear();
    
    // 移除所有自动高亮样式
    document.querySelectorAll('.tree-item-header.highlighted').forEach(item => {
        item.classList.remove('highlighted');
    });
    
    // 注意：不清除手动高亮
}

// 更新树形结构可见性
function updateTreeVisibility() {
    // 获取所有树形项
    const items = document.querySelectorAll('.tree-item');
    
    // 遍历所有项
    items.forEach(item => {
        // 如果是隐藏非高亮项模式
        if (isHidingNonHighlighted) {
            // 如果不在高亮项集合中且不在手动高亮项集合中，则隐藏
            if (!highlightedItems.has(item.dataset.id) && !manualHighlightedItems.has(item.dataset.id)) {
                item.classList.add('hidden');
            } else {
                item.classList.remove('hidden');
            }
        } else {
            // 否则显示所有项
            item.classList.remove('hidden');
        }
    });
}

// 切换非高亮项的显示/隐藏
function toggleNonHighlightedItems() {
    // 切换状态
    isHidingNonHighlighted = !isHidingNonHighlighted;
    
    // 更新按钮文本
    toggleBtn.textContent = isHidingNonHighlighted ? '显示所有元素' : '隐藏非高亮元素';
    
    // 更新树形结构可见性
    updateTreeVisibility();
}