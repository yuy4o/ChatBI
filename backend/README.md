# MapperSuggest 后端服务

## 项目简介

MapperSuggest 是一个智能数据映射和SQL建议系统，帮助用户通过自然语言查询快速获取数据库信息和SQL查询建议。系统基于向量数据库和大语言模型，提供了元数据搜索、SQL生成、智能建议等功能。

## 功能特点

- **元数据管理**：管理数据库、表、字段等元数据信息
- **智能建议**：基于用户输入提供相关的数据库对象建议
- **SQL生成**：根据自然语言描述自动生成SQL查询语句
- **SQL执行**：执行生成的SQL语句并返回结果
- **向量数据库**：使用ChromaDB存储元数据的向量表示，支持语义搜索
- **实时日志**：通过WebSocket提供实时日志显示

## 安装步骤

### 环境要求

- Python 3.8+
- SQLite 3

### 安装依赖

1. 克隆项目到本地

```bash
git clone https://github.com/whyuds/MapperSuggest.git
cd MapperSuggest/backend
```

2. 创建并激活虚拟环境（可选但推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate
```

3. 安装依赖包

```bash
pip install -r requirements.txt
```

## 配置说明

项目使用SQLite数据库，数据库文件会自动在项目根目录创建：

- `data.db`：存储实际数据
- `metadata.db`：存储元数据信息
- `config.db`：存储配置信息

如需使用火山引擎API进行向量嵌入，请在 `services/vector_db.py` 中配置您的API密钥。

## 启动服务

```bash
python app.py
```

服务默认在 http://localhost:5000 启动，并开启调试模式。

## 初始化向量数据库

首次使用或更新元数据后，需要初始化向量数据库：

```
POST http://localhost:5000/vector-db/init
```

## API文档

启动服务后，可以通过以下地址访问Swagger API文档：

```
http://localhost:5000/apidocs/
```

### 主要API

- `/suggest` - 智能建议接口
- `/sql` - SQL生成接口
- `/sql-agent` - SQLAgent生成并执行接口
- `/execute` - SQL执行接口
- `/metadata/*` - 元数据管理接口
- `/data/*` - 数据访问接口
- `/config/*` - 配置管理接口

## 开发说明

### 项目结构

- `app.py` - 主应用入口和API定义
- `config/` - 配置相关代码
- `services/` - 核心服务实现
- `initial/` - 初始化数据和元数据
- `utils/` - 工具函数
- `test/` - 测试代码

### 添加新功能

1. 在 `services/` 目录下实现相关服务
2. 在 `app.py` 中添加对应的API路由
3. 更新元数据并重新初始化向量数据库

## 许可证

[MIT License](LICENSE)