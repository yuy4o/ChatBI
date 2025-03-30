import sqlite3
import json
import os
import uuid
from config.constants import METADATA_DB_PATH, INITIAL_METADATA_SCHEMA_SQL_PATH, INITIAL_METADATA_DIR

def init_metadata():
    # 检查数据库文件是否存在，如果存在则检查表是否为空
    if os.path.exists(METADATA_DB_PATH):
        # 连接到SQLite数据库检查表是否为空
        conn = sqlite3.connect(METADATA_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dbs")
        count = cursor.fetchone()[0]
        conn.close()
        
        # 如果表不为空，则直接返回
        if count > 0:
            return
    
    # 连接到SQLite数据库
    conn = sqlite3.connect(METADATA_DB_PATH)
    cursor = conn.cursor()
    
    # 读取并执行DDL语句
    with open(INITIAL_METADATA_SCHEMA_SQL_PATH, 'r', encoding='utf-8') as f:
        ddl = f.read()
        cursor.executescript(ddl)
    
    # 从initial_data目录读取所有JSON文件（除template.json外）
    all_data = []
    
    for filename in os.listdir(INITIAL_METADATA_DIR):
        if filename.endswith('.json') and filename != 'template.json':
            file_path = os.path.join(INITIAL_METADATA_DIR, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    db_data = json.load(f)
                    all_data.append(db_data)
                except json.JSONDecodeError as e:
                    print(f"Error loading {filename}: {e}")
    
    # 导入数据
    for db in all_data:
        # 检查是否是freeshot_term.json文件的数据
        if 'freeshots' in db or 'terms' in db:
            continue  # 跳过，这个文件会在后面单独处理
            
        # 生成数据库ID
        db_id = db['name']
        
        # 插入数据库信息
        cursor.execute(
            'INSERT INTO dbs (id, name, description) VALUES (?, ?, ?)',
            (db_id, db['name'], db.get('description', ''))
        )
        
        # 插入表信息
        for table in db['tables']:
            # 生成表ID
            table_id = f"table_id_{db_id}_{table['name']}"
            
            cursor.execute(
                'INSERT INTO tables (id, db_id, name, description, type) VALUES (?, ?, ?, ?, ?)',
                (table_id, db_id, table['name'], table.get('description', ''), table.get('type', ''))
            )
            
            # 插入列信息
            for column in table['columns']:
                # 生成列ID
                column_id = f"columnu_id_{db_id}_{table['name']}_{column['name']}"
                
                cursor.execute(
                    'INSERT INTO columns (id, table_id, name, type, description, is_primary) VALUES (?, ?, ?, ?, ?, ?)',
                    (column_id, table_id, column['name'], column['type'], column.get('description', ''), column.get('is_primary', False))
                )
                
                # 如果是枚举类型，插入枚举值
                if 'values' in column:
                    for value in column['values']:
                        # 生成枚举值ID
                        value_id = f"columnu_id_{db_id}_{table['name']}_{column['name']}_{value['value']}"
                        
                        cursor.execute(
                            'INSERT INTO enum_values (id, column_id, value, description) VALUES (?, ?, ?, ?)',
                            (value_id, column_id, value['value'], value.get('description', ''))
                        )
        
    # 初始化freeshot和term数据
    for filename in os.listdir(INITIAL_METADATA_DIR):
        if filename == 'freeshot_term.json':
            file_path = os.path.join(INITIAL_METADATA_DIR, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    
                    # 插入freeshot数据
                    if 'freeshots' in data:
                        for freeshot in data['freeshots']:
                            cursor.execute(
                                'INSERT INTO freeshots (id, name, content, likes) VALUES (?, ?, ?, ?)',
                                (freeshot['id'], freeshot['name'], freeshot['content'], freeshot.get('likes', 0))
                            )
                    
                    # 插入term数据
                    if 'terms' in data:
                        for term in data['terms']:
                            cursor.execute(
                                'INSERT INTO terms (id, name, content, likes) VALUES (?, ?, ?, ?)',
                                (term['id'], term['name'], term['content'], term.get('likes', 0))
                            )
                except json.JSONDecodeError as e:
                    print(f"Error loading {filename}: {e}")
    
    conn.commit()
    
    return conn

def get_dbs():
    conn = sqlite3.connect(METADATA_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description FROM dbs')
    rows = cursor.fetchall()
    conn.close()
    return [{'id': row[0], 'name': row[1], 'description': row[2] or ''} for row in rows]

def get_tables(db_id):
    conn = sqlite3.connect(METADATA_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, type FROM tables_view WHERE db_id = ?', (db_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': row[0], 'table': row[1], 'description': row[2] or '', 'type': row[3] or ''} for row in rows]

def get_columns(table_id):
    conn = sqlite3.connect(METADATA_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, type, is_primary, description FROM columns_view WHERE table_id = ?', (table_id,))
    rows = cursor.fetchall()
    result = []
    for row in rows:
        col_data = {
            'id': row[0],
            'column': row[1],
            'type': row[2],
            'is_primary': row[3],
            'description': row[4] or ''
        }
        if row[2] == 'ENUM':
            col_data['values'] = []
        result.append(col_data)
    conn.close()
    return result

def get_values(column_id):
    conn = sqlite3.connect(METADATA_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, value, description FROM enum_values_view WHERE column_id = ?', (column_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': row[0], 'value': row[1], 'description': row[2] or ''} for row in rows]