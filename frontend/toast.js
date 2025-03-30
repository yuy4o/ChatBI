// Toast提示组件

/**
 * 显示一个自动消失的toast提示
 * @param {string} message - 提示消息内容
 * @param {string} type - 提示类型 ('success', 'error', 'info')
 * @param {number} duration - 显示持续时间(毫秒)，默认3000ms
 */
export function showToast(message, type = 'info', duration = 3000) {
    // 检查是否已存在toast容器
    let toastContainer = document.querySelector('.toast-container');
    
    // 如果不存在，创建一个新的toast容器
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // 创建toast元素
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // 添加到容器
    toastContainer.appendChild(toast);
    
    // 添加显示动画
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // 设置自动消失
    setTimeout(() => {
        toast.classList.remove('show');
        toast.classList.add('hide');
        
        // 动画结束后移除元素
        setTimeout(() => {
            toastContainer.removeChild(toast);
            
            // 如果容器中没有toast了，移除容器
            if (toastContainer.children.length === 0) {
                document.body.removeChild(toastContainer);
            }
        }, 300);
    }, duration);
}