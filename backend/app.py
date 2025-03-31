import sqlite3
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from services.ddl import generate_ddl_metadata_from_schema
from services.term import generate_term_metadata_from_schema
from services.freeshot import generate_freeshot_metadata_from_schema
from initial.data import init_data, get_table_data, get_table_count
from initial.metadata import init_metadata
from config.constants import DATA_DB_PATH
from initial.config import init_config_db
import random
import time
from flasgger import Swagger
from services.logger import socketio, handle_log_post, broadcast_log, broadcast_stream_log

app = Flask(__name__)
CORS(app)
Swagger(app)
socketio.init_app(app)

from utils.mock_data_generator import generate_mock_data

generate_mock_data()
init_metadata()
init_data()
init_config_db()  # 初始化配置数据库


# 获取数据库列表
@app.route('/metadata/dbs', methods=['GET'])
def get_dbs_api():
    """
    获取数据库列表
    ---
    tags:
      - 元数据
    responses:
      200:
        description: 数据库列表
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
              db:
                type: string
              description:
                type: string
              tables:
                type: array
                items: {}
    """
    try:
        from services.db_service import get_all_dbs
        dbs = get_all_dbs()
        return jsonify(dbs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取数据表列表
@app.route('/metadata/tables', methods=['GET'])
def get_tables():
    """
    获取数据表列表
    ---
    tags:
      - 元数据
    parameters:
      - name: db
        in: query
        type: string
        required: true
    responses:
      200:
        description: 数据表列表
    """
    db_id = request.args.get('db', '')
    
    try:
        from services.db_service import get_db_tables
        tables = get_db_tables(db_id)
        
        if not tables:
            return jsonify({"error": "Database not found"}), 404
            
        return jsonify(tables)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取数据表字段列表
@app.route('/metadata/columns', methods=['GET'])
def get_columns():
    """
    获取表字段元数据
    ---
    tags:
      - 元数据
    parameters:
      - name: db
        in: query
        type: string
        required: true
      - name: table
        in: query
        type: string
        required: true
    responses:
      200:
        description: 字段列表
        schema:
          type: array
          items:
            type: object
            properties:
              id: {type: string}
              column: {type: string}
              type: {type: string}
              description: {type: string}
              values: 
                type: array
                items:
                  type: object
                  properties:
                    value: {type: string}
                    description: {type: string}
    """
    db_id = request.args.get('db', '')
    table_id = request.args.get('table', '')
    
    try:
        from services.db_service import get_table_columns
        columns = get_table_columns(table_id)
        
        if not columns:
            return jsonify({"error": "Table not found"}), 404
            
        return jsonify(columns)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取字段纬度值列表
# Data API endpoints
@app.route('/data/tables/<table_name>', methods=['GET'])
def get_table_data_api(table_name):
    """
    获取表数据
    ---
    tags:
      - 数据
    parameters:
      - name: table_name
        in: path
        type: string
        required: true
        description: 表名
      - name: limit
        in: query
        type: integer
        required: false
        default: 100
        description: 每页记录数
      - name: offset
        in: query
        type: integer
        required: false
        default: 0
        description: 偏移量
      - name: filter
        in: query
        type: string
        required: false
        description: 过滤条件，格式为JSON字符串，如{"column":"value"}
    responses:
      200:
        description: 表数据
        schema:
          type: object
          properties:
            data:
              type: array
              items: {}
            total:
              type: integer
            limit:
              type: integer
            offset:
              type: integer
    """
    try:
        # Get pagination parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Get filter parameters
        filter_json = request.args.get('filter', '{}')
        try:
            filters = json.loads(filter_json)
        except json.JSONDecodeError:
            filters = {}
        
        # Get data
        data = get_table_data(table_name, limit, offset, filters)
        total = get_table_count(table_name, filters)
        
        return jsonify({
            "data": data,
            "total": total,
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data/tables', methods=['GET'])
def get_available_data_tables():
    """
    获取可用的数据表列表
    ---
    tags:
      - 数据
    responses:
      200:
        description: 可用的数据表列表
        schema:
          type: array
          items:
            type: string
    """
    try:
        conn = sqlite3.connect(DATA_DB_PATH)
        cursor = conn.cursor()
        
        # Get list of tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(tables)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/metadata/values', methods=['GET'])
def get_values():
    """
    获取字段纬度值列表
    ---
    tags:
      - 元数据
    parameters:
      - name: db
        in: query
        type: string
        required: true
      - name: table
        in: query
        type: string
        required: true
      - name: column
        in: query
        type: string
        required: true
    responses:
      200:
        description: 字段纬度值列表
        schema:
          type: array
          items:
            type: object
            properties:
              value: {type: string}
              description: {type: string}
    """

    db_id = request.args.get('db', '')
    table_id = request.args.get('table', '')
    column_id = request.args.get('column', '')
    
    try:
        from services.db_service import get_column_enum_values
        values = get_column_enum_values(column_id)
        
        if not values:
            return jsonify({"error": "No enum values found"}), 404
            
        return jsonify(values)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Suggest接口
@app.route('/suggest', methods=['POST'])
def suggest():
    """
    智能建议接口
    ---
    tags:
      - 智能建议
    """
    # 获取用户输入的文本
    data = request.get_json()
    user_input = data.get('text', '')
    # 如果查询为空，返回空结果
    if not user_input:
        return jsonify([])
    # 导入向量数据库服务
    from services.vector_db import search_metadata, format_suggest_results
    # 搜索向量数据库
    search_results = search_metadata(user_input, limit=20)    
    # 格式化结果为suggest API格式
    formatted_results = format_suggest_results(search_results)
    # 打印结果
    import json
    broadcast_log('system', json.dumps(search_results, ensure_ascii=False, indent=2), "已召回问题相关元数据")
    return jsonify(formatted_results)

# 初始化向量数据库接口
@app.route('/vector-db/init', methods=['POST'])
def init_vector_db():
    """
    初始化向量数据库接口
    ---
    tags:
      - 向量数据库
    responses:
      200:
        description: 初始化结果
        schema:
          type: object
          properties:
            success: {type: boolean}
            message: {type: string}
    :return:
    """
    try:
        from services.vector_db import init_vector_db, load_metadata_to_vector_db
        
        # 初始化向量数据库
        _, collection = init_vector_db()
        
        # 加载元数据
        count = load_metadata_to_vector_db(collection)
        
        return jsonify({
            'success': True,
            'message': f'Successfully loaded {count} metadata items to vector database'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# DDL接口
@app.route('/ddl', methods=['POST'])
def ddl():
    """
    根据数据库元数据生成DDL语句
    ---
    tags:
      - 智能建议
    """
    try:
        data = request.get_json()
        if not data or 'schema' not in data:
            return jsonify({'error': 'Missing schema data'}), 400

        metadata = generate_ddl_metadata_from_schema(data)
        return jsonify({
            'metadata': metadata,
            'count': len(metadata)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Freeshot API接口
@app.route('/freeshot', methods=['POST'])
def freeshot_api():
    """
    获取相似查询和SQL建议
    ---
    tags:
      - 智能建议
    """
    try:
        data = request.get_json()
        import time
        time.sleep(1)
        metadata = generate_freeshot_metadata_from_schema(data)
        return jsonify({
                'metadata': metadata,
                'count': len(metadata)
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Term API接口
@app.route('/term', methods=['POST'])
def term_api():
    """
    获取数据库相关术语和概念
    ---
    tags:
      - 智能建议
    """
    try:
        data = request.get_json()
        import time
        time.sleep(1)
        metadata = generate_term_metadata_from_schema(data)
        return jsonify({
                'metadata': metadata,
                'count': len(metadata)
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# SQL生成API接口
@app.route('/sql', methods=['POST'])
def sql_api():
    """
    生成SQL查询语句
    ---
    tags:
      - 智能建议
    """
    data = request.get_json()
    query = data.get('query', '')
    ddl = data['metadata'].get('ddl', [])
    freeshot = data['metadata'].get('freeshot', [])
    term = data['metadata'].get('term', [])
    history_message = data.get('history_message', [])
    # 导入SQL生成服务
    from services.sql_generator import generate_sql_from_query
    # 调用大模型API生成SQL
    response_data = generate_sql_from_query(query, ddl, freeshot, term)
    return jsonify(response_data)

# SQLAgent API接口
@app.route('/sql-agent', methods=['POST'])
def sql_agent_api():
    """
    使用SQLAgent生成并执行SQL查询语句
    ---
    tags:
      - 智能建议
    """
    data = request.get_json()
    ddl = data['metadata'].get('ddl', [])
    freeshot = data['metadata'].get('freeshot', [])
    term = data['metadata'].get('term', [])
    messages = data.get('messages', [])
    
    # 导入SQLAgent服务
    from services.sql_agent_generator import generate_sql_with_react_agent
    
    # 调用SQLAgent生成并执行SQL
    broadcast_log('system', json.dumps(messages, ensure_ascii=False, indent=2), "SQLAgent-开始执行")
    response_data = generate_sql_with_react_agent(ddl, freeshot, term, messages)
    
    return jsonify(response_data)

# 用户点赞反馈API接口
@app.route('/feedback_good', methods=['POST'])
def feedback_good_api():
    """
    处理用户点赞反馈，更新元数据描述
    ---
    tags:
      - 智能建议
    """
    data = request.get_json()
    ddl = data['metadata'].get('ddl', [])
    freeshot = data['metadata'].get('freeshot', [])
    term = data['metadata'].get('term', [])
    messages = data.get('messages', [])
    
    # 导入FeedbackAgent服务
    from services.feedback_agent_generator import generate_feedback_with_agent
    
    # 调用FeedbackAgent处理用户反馈
    broadcast_log('system', json.dumps(messages, ensure_ascii=False, indent=2), "FeedbackAgent-开始分析用户反馈")
    response_data = generate_feedback_with_agent(ddl, freeshot, term, messages)
    
    return jsonify(response_data)

# SQL执行API接口
@app.route('/execute', methods=['POST'])
def execute_api():
    """
    执行SQL查询语句
    ---
    tags:
      - 智能建议
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            sql:
              type: string
              description: 要执行的SQL查询语句
        required: true
    responses:
      200:
        description: SQL执行结果
        schema:
          type: object
          properties:
            columns:
              type: array
              items:
                type: object
                properties:
                  name: {type: string}
                  type: {type: string}
                  nullable: {type: boolean}
            data:
              type: array
              items:
                type: array
                items: {}
            totalRows: {type: integer}
    """
    # 获取请求数据
    data = request.get_json()
    print("api_execute: %s", data)
    sql = data.get('sql', '')    
    
    # 使用SQLExecutor执行SQL
    from services.sql_executor import SQLExecutor
    
    # 执行SQL查询
    result = SQLExecutor.execute_sql(sql)
    
    if result["success"]:
        # 如果执行成功
        if "columns" in result:
            # SELECT查询
            response_data = {
                "columns": result["columns"],
                "data": result["data"],
                "totalRows": result["totalRows"]
            }
        else:
            # 非SELECT查询
            response_data = {
                "affectedRows": result["affectedRows"],
                "message": result["message"]
            }
    else:
        # 执行失败
        return jsonify({
            "error": result["error"],
            "message": result["message"]
        }), 400
    
    return jsonify(response_data)

# 配置管理API接口
@app.route('/config/list', methods=['GET'])
def get_config_list():
    """
    获取当前配置项列表
    ---
    tags:
      - 配置管理
    responses:
      200:
        description: 配置项列表
        schema:
          type: array
          items:
            type: object
            properties:
              key: {type: string}
              value: {type: string}
              name: {type: string}
    """
    try:
        from initial.config import get_all_configs
        configs = get_all_configs()
        return jsonify(configs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/config/update', methods=['POST'])
def update_config():
    """
    更新配置项
    ---
    tags:
      - 配置管理
    parameters:
      - in: body
        name: body
        schema:
          type: array
          items:
            type: object
            properties:
              key:
                type: string
                description: 要修改的配置key
              value:
                type: string
                description: 新的配置值
        required: true
    responses:
      200:
        description: 更新结果
        schema:
          type: object
          properties:
            success: {type: boolean}
            message: {type: string}
    """
    try:
        data = request.get_json()
        if not data or not isinstance(data, list):
            return jsonify({"error": "请求体必须是配置项数组"}), 400
            
        from initial.config import update_configs
        result = update_configs(data)
        
        return jsonify({
            "success": result,
            "message": "配置更新成功" if result else "配置更新失败"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 日志API接口
@app.route('/api/log', methods=['POST'])
def log_api():
    """
    发送日志
    ---
    tags:
      - 日志
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            type:
              type: string
              description: 日志类型 (system|ai)
            message:
              type: string
              description: 日志内容
        required: true
    responses:
      200:
        description: 日志发送结果
        schema:
          type: object
          properties:
            type: {type: string}
            message: {type: string}
            timestamp: {type: string}
    """
    return handle_log_post()

if __name__ == '__main__':    
    # 使用socketio运行应用
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)