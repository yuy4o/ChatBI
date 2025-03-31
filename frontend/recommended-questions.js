/**
 * 推荐问题模块 - 在聊天界面显示推荐问题
 */

// 推荐问题列表
const recommendedQuestions = [
    "爱奇艺最近一周每天的播放时长、播放次数、播放UV、点赞次数、评论次数",
    "最近一周的播放量怎么样，同比上周怎么样",
    "各个等级的未认证创作者有多少人"
];

/**
 * 创建推荐问题消息
 * 在聊天界面中显示系统推荐的问题
 */
function createRecommendedQuestionsMessage() {
    const chatMessages = document.getElementById('chatMessages');
    
    // 如果聊天消息区域为空，才添加推荐问题
    if (chatMessages.children.length === 0) {
        // 创建系统消息容器
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system-message recommended-questions-message';
        
        // 创建标题
        const titleDiv = document.createElement('div');
        titleDiv.className = 'recommended-questions-title';
        titleDiv.textContent = '您可能想问：';
        messageDiv.appendChild(titleDiv);
        
        // 创建问题列表
        const questionsList = document.createElement('div');
        questionsList.className = 'recommended-questions-list';
        
        // 添加每个推荐问题
        recommendedQuestions.forEach(question => {
            const questionItem = document.createElement('div');
            questionItem.className = 'recommended-question-item';
            questionItem.textContent = question;
            
            // 添加点击事件
            questionItem.addEventListener('click', () => {
                // 将问题填入输入框
                const userInput = document.getElementById('userInput');
                userInput.value = question;
                
                // 触发发送按钮点击
                document.getElementById('sendBtn').click();
            });
            
            questionsList.appendChild(questionItem);
        });
        
        messageDiv.appendChild(questionsList);
        
        // 添加到聊天界面
        chatMessages.appendChild(messageDiv);
    }
}

// 导出函数
export { createRecommendedQuestionsMessage };