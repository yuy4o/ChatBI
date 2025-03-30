/**
 * 数据看板消息处理模块
 * 用于处理SQL执行结果的可视化展示
 */

// 引入Chart.js
// 通过全局Chart变量使用（由index.html引入）

// 保存当前数据
let currentData = null;

/**
 * 执行SQL并获取结果
 * @param {string} sql - 要执行的SQL语句
 * @returns {Promise<Object>} - 执行结果
 */
async function executeSQL(sql) {
    try {
        const response = await fetch('http://localhost:5000/execute', {
            method: 'POST',
            headers: {
                'accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ sql })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('执行SQL失败:', error);
        throw error;
    }
}

/**
 * 创建数据看板消息
 * @param {Object} data - SQL执行结果数据
 * @param {string} sql - 执行的SQL语句
 * @returns {HTMLElement} - 创建的数据看板消息元素
 */
function createDashboardMessage(data, sql) {
    const chatMessages = document.getElementById('chatMessages');
    
    // 保存当前数据，用于后续导出和切换视图
    currentData = data;
    
    // 创建数据看板消息容器
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system-message dashboard-message';
    
    // 创建标题和导出按钮的容器
    const headerDiv = document.createElement('div');
    headerDiv.className = 'dashboard-header';
    
    // 创建标题
    const titleDiv = document.createElement('div');
    titleDiv.className = 'dashboard-title';
    titleDiv.textContent = 'SQL执行结果';
    headerDiv.appendChild(titleDiv);
    
    // 创建导出按钮
    const exportBtn = document.createElement('button');
    exportBtn.className = 'dashboard-export-btn';
    exportBtn.textContent = '导出数据';
    exportBtn.addEventListener('click', () => {
        exportAsCSV(data);
    });
    headerDiv.appendChild(exportBtn);
    
    messageDiv.appendChild(headerDiv);
    
    // 创建Tab切换区域
    const tabsDiv = document.createElement('div');
    tabsDiv.className = 'dashboard-tabs';
    
    // 添加各种视图的Tab
    const tabTypes = ['表格', '趋势图', '柱状图', '饼图'];
    tabTypes.forEach(tabType => {
        const tabBtn = document.createElement('button');
        tabBtn.className = 'dashboard-tab';
        tabBtn.textContent = tabType;
        tabBtn.addEventListener('click', () => {
            // 移除所有Tab的active类
            document.querySelectorAll('.dashboard-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            // 为当前Tab添加active类
            tabBtn.classList.add('active');
            
            // 更新视图
            updateView(contentDiv, tabType, data);
        });
        tabsDiv.appendChild(tabBtn);
    });
    messageDiv.appendChild(tabsDiv);
    

    
    // 创建内容区域
    const contentDiv = document.createElement('div');
    contentDiv.className = 'dashboard-content';
    messageDiv.appendChild(contentDiv);
    
    // 默认显示表格视图
    const firstTab = document.querySelector('.dashboard-tab');
    if (firstTab) {
        firstTab.classList.add('active');
    }
    updateView(contentDiv, '表格', data);
    
    // 添加到聊天界面
    chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

/**
 * 更新视图
 * @param {HTMLElement} container - 容器元素
 * @param {string} viewType - 视图类型
 * @param {Object} data - 数据
 */
function updateView(container, viewType, data) {
    // 清空容器
    container.innerHTML = '';
    
    switch (viewType) {
        case '表格':
            createTableView(container, data);
            break;
        case '趋势图':
            createLineChartView(container, data);
            break;
        case '柱状图':
            createBarChartView(container, data);
            break;
        case '饼图':
            createPieChartView(container, data);
            break;
        default:
            createTableView(container, data);
    }
}

/**
 * 创建表格视图
 * @param {HTMLElement} container - 容器元素
 * @param {Object} data - 数据
 */
// 格式化数字，添加千分位并保留两位小数
function formatNumber(value) {
    if (typeof value === 'number') {
        // 检查是否为整数
        if (Number.isInteger(value)) {
            return value.toLocaleString('en-US');
        }
        return value.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    return value;
}

function createTableView(container, data) {
    if (!data || !data.columns || !data.data) {
        container.textContent = '无有效数据';
        return;
    }
    
    const table = document.createElement('table');
    table.className = 'dashboard-table';
    
    // 创建表头
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    data.columns.forEach(column => {
        const th = document.createElement('th');
        th.textContent = column.name;
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // 创建表体
    const tbody = document.createElement('tbody');
    
    data.data.forEach(row => {
        const tr = document.createElement('tr');
        
        row.forEach(cell => {
            const td = document.createElement('td');
            td.textContent = cell !== null ? formatNumber(cell) : 'NULL';
            tr.appendChild(td);
        });
        
        tbody.appendChild(tr);
    });
    
    table.appendChild(tbody);
    container.appendChild(table);
    
    // 添加总行数信息
    if (data.totalRows !== undefined) {
        const totalInfo = document.createElement('div');
        totalInfo.className = 'dashboard-total-info';
        totalInfo.textContent = `总行数: ${data.totalRows}`;
        container.appendChild(totalInfo);
    }
}

/**
 * 创建趋势图视图
 * @param {HTMLElement} container - 容器元素
 * @param {Object} data - 数据
 */
function createLineChartView(container, data) {
    if (!data || !data.columns || !data.data || data.data.length === 0) {
        container.textContent = '无有效数据或数据不适合绘制趋势图';
        return;
    }
    
    // 检查是否有日期/时间列和数值列
    let dateColumnIndex = data.columns.findIndex(col => 
        col.name.toLowerCase().includes('date') || 
        col.name.toLowerCase().includes('time')
    );
    
    // 如果没有找到日期/时间列，则尝试通过类型识别
    if (dateColumnIndex === -1) {
        dateColumnIndex = data.columns.findIndex(col => 
            col.type.toLowerCase().includes('date') || 
            col.type.toLowerCase().includes('time') ||
            (col.type.toLowerCase().includes('text') && 
             data.data.length > 0 && 
             typeof data.data[0][col.index] === 'string' && 
             /^\d{4}[-/]\d{2}[-/]\d{2}/.test(data.data[0][col.index]))
        );
            
        // 如果仍然没有找到合适的列，使用第一列
        if (dateColumnIndex === -1) {
            dateColumnIndex = 0;
        }
    }
    
    // 找出所有数值列
    const numericColumns = data.columns
        .map((col, index) => ({ ...col, index }))
        .filter(col => 
            col.index !== dateColumnIndex && 
            (col.type.toLowerCase().includes('int') || 
             col.type.toLowerCase().includes('float') || 
             col.type.toLowerCase().includes('double') || 
             col.type.toLowerCase().includes('decimal') || 
             col.type.toLowerCase().includes('number'))
        );
    
    if (numericColumns.length === 0) {
        container.textContent = '未找到数值列，无法绘制趋势图';
        return;
    }
    
    // 创建画布
    const canvas = document.createElement('canvas');
    canvas.width = 600;
    canvas.height = 400;
    container.appendChild(canvas);
    
    // 准备数据
    const labels = data.data.map(row => row[dateColumnIndex]).reverse();
    const datasets = numericColumns.map(col => ({
        label: col.name,
        data: data.data.map(row => row[col.index]).reverse(),
        formatter: (value) => formatNumber(value),
        borderColor: getRandomColor(),
        backgroundColor: getRandomColor(0.1),
        fill: true,
        tension: 0.4
    }));
    
    // 创建图表
    new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: data.columns[dateColumnIndex].name
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: numericColumns.map(col => col.name).join(' / ')
                    }
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top'
                }
            }
        }
    });
}

/**
 * 创建柱状图视图
 * @param {HTMLElement} container - 容器元素
 * @param {Object} data - 数据
 */
function createBarChartView(container, data) {
    if (!data || !data.columns || !data.data || data.data.length === 0) {
        container.textContent = '无有效数据或数据不适合绘制柱状图';
        return;
    }
    
    // 检查是否有分类列和数值列
    const categoryColumnIndex = data.columns.findIndex(col => 
        col.type.toLowerCase().includes('text') || 
        col.type.toLowerCase().includes('varchar') || 
        col.type.toLowerCase().includes('char')
    );
    
    // 如果没有明确的分类列，使用第一列作为分类
    const labelColumnIndex = categoryColumnIndex !== -1 ? categoryColumnIndex : 0;
    
    // 找出所有数值列
    const numericColumns = data.columns
        .map((col, index) => ({ ...col, index }))
        .filter(col => 
            col.index !== labelColumnIndex && 
            (col.type.toLowerCase().includes('int') || 
             col.type.toLowerCase().includes('float') || 
             col.type.toLowerCase().includes('double') || 
             col.type.toLowerCase().includes('decimal') || 
             col.type.toLowerCase().includes('number'))
        );
    
    if (numericColumns.length === 0) {
        container.textContent = '未找到数值列，无法绘制柱状图';
        return;
    }
    
    // 创建画布
    const canvas = document.createElement('canvas');
    canvas.width = 600;
    canvas.height = 400;
    container.appendChild(canvas);
    
    // 准备数据
    const labels = data.data.map(row => row[labelColumnIndex]);
    const datasets = numericColumns.map(col => ({
        label: col.name,
        data: data.data.map(row => row[col.index]),
        formatter: (value) => formatNumber(value),
        backgroundColor: getRandomColor(0.7),
        borderColor: getRandomColor(),
        borderWidth: 1
    }));
    
    // 创建图表
    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: data.columns[labelColumnIndex].name
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: numericColumns.map(col => col.name).join(' / ')
                    }
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top'
                }
            }
        }
    });
}

/**
 * 创建饼图视图
 * @param {HTMLElement} container - 容器元素
 * @param {Object} data - 数据
 */
function createPieChartView(container, data) {
    if (!data || !data.columns || !data.data || data.data.length === 0) {
        container.textContent = '无有效数据或数据不适合绘制饼图';
        return;
    }
    
    // 检查是否有分类列和数值列
    const categoryColumnIndex = data.columns.findIndex(col => 
        col.type.toLowerCase().includes('text') || 
        col.type.toLowerCase().includes('varchar') || 
        col.type.toLowerCase().includes('char')
    );
    
    // 如果没有明确的分类列，使用第一列作为分类
    const labelColumnIndex = categoryColumnIndex !== -1 ? categoryColumnIndex : 0;
    
    // 找出第一个数值列
    const valueColumnIndex = data.columns.findIndex((col, index) => 
        index !== labelColumnIndex && 
        (col.type.toLowerCase().includes('int') || 
         col.type.toLowerCase().includes('float') || 
         col.type.toLowerCase().includes('double') || 
         col.type.toLowerCase().includes('decimal') || 
         col.type.toLowerCase().includes('number'))
    );
    
    if (valueColumnIndex === -1) {
        container.textContent = '未找到数值列，无法绘制饼图';
        return;
    }
    
    // 创建画布
    const canvas = document.createElement('canvas');
    canvas.width = 600;
    canvas.height = 400;
    container.appendChild(canvas);
    
    // 准备数据
    const labels = data.data.map(row => row[labelColumnIndex]);
    const values = data.data.map(row => row[valueColumnIndex]);
    const backgroundColors = labels.map(() => getRandomColor(0.7));
    
    // 创建图表
    new Chart(canvas, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: data.columns[valueColumnIndex].name,
                data: values,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors.map(color => color.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        generateLabels: (chart) => {
                            const data = chart.data;
                            const total = data.datasets[0].data.reduce((sum, value) => sum + value, 0);
                            return data.labels.map((label, i) => ({
                                text: `${label} (${((data.datasets[0].data[i] / total) * 100).toFixed(1)}%)`,
                                fillStyle: data.datasets[0].backgroundColor[i],
                                strokeStyle: data.datasets[0].borderColor[i],
                                lineWidth: data.datasets[0].borderWidth,
                                hidden: isNaN(data.datasets[0].data[i])
                            }));
                        }
                    }
                },
                title: {
                    display: true,
                    text: `${data.columns[labelColumnIndex].name} vs ${data.columns[valueColumnIndex].name}`
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const value = context.raw;
                            const total = context.dataset.data.reduce((sum, val) => sum + val, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${context.label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 导出数据
 * @param {Object} data - 要导出的数据
 */
function exportData(data) {
    if (!data || !data.columns || !data.data) {
        alert('无有效数据可导出');
        return;
    }
    
    // 创建导出选项菜单
    const exportMenu = document.createElement('div');
    exportMenu.className = 'export-menu';
    
    const exportCSVBtn = document.createElement('button');
    exportCSVBtn.textContent = '导出为CSV';
    exportCSVBtn.addEventListener('click', () => {
        exportAsCSV(data);
        document.body.removeChild(exportMenu);
    });
    exportMenu.appendChild(exportCSVBtn);
    
    const exportExcelBtn = document.createElement('button');
    exportExcelBtn.textContent = '导出为Excel';
    exportExcelBtn.addEventListener('click', () => {
        exportAsExcel(data);
        document.body.removeChild(exportMenu);
    });
    exportMenu.appendChild(exportExcelBtn);
    
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = '取消';
    cancelBtn.addEventListener('click', () => {
        document.body.removeChild(exportMenu);
    });
    exportMenu.appendChild(cancelBtn);
    
    // 添加到body
    document.body.appendChild(exportMenu);
    
    // 点击其他区域关闭菜单
    document.addEventListener('click', function closeMenu(e) {
        if (!exportMenu.contains(e.target) && e.target !== document.querySelector('.dashboard-export-btn')) {
            document.body.removeChild(exportMenu);
            document.removeEventListener('click', closeMenu);
        }
    });
}

/**
 * 导出为CSV
 * @param {Object} data - 要导出的数据
 */
function exportAsCSV(data) {
    // 创建CSV内容
    const headers = data.columns.map(col => col.name).join(',');
    const rows = data.data.map(row => row.join(',')).join('\n');
    const csvContent = `${headers}\n${rows}`;
    
    // 创建Blob对象
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    
    // 创建下载链接
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `sql_result_${new Date().toISOString().slice(0, 10)}.csv`);
    link.style.visibility = 'hidden';
    
    // 添加到DOM并触发下载
    document.body.appendChild(link);
    link.click();
    
    // 清理
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 100);
}

/**
 * 导出为Excel
 * @param {Object} data - 要导出的数据
 */
function exportAsExcel(data) {
    // 创建工作簿
    const wb = XLSX.utils.book_new();
    
    // 准备数据
    const headers = data.columns.map(col => col.name);
    const wsData = [headers, ...data.data];
    
    // 创建工作表
    const ws = XLSX.utils.aoa_to_sheet(wsData);
    
    // 添加工作表到工作簿
    XLSX.utils.book_append_sheet(wb, ws, 'SQL结果');
    
    // 导出Excel文件
    XLSX.writeFile(wb, `sql_result_${new Date().toISOString().slice(0, 10)}.xlsx`);
}

/**
 * 生成随机颜色
 * @param {number} opacity - 透明度
 * @returns {string} - 颜色字符串
 */
function getRandomColor(opacity = 1) {
    const r = Math.floor(Math.random() * 255);
    const g = Math.floor(Math.random() * 255);
    const b = Math.floor(Math.random() * 255);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

// 导出方法，使其可以被其他JS文件引用
export { executeSQL, createDashboardMessage };