import requests
import json
import os
import chromadb
import sqlite3
import time
from config.constants import METADATA_DB_PATH, CHROMA_PERSIST_DIR
from initial.config import get_config

# 从配置服务获取火山引擎API配置
from initial.config import get_embedding_config

# 自定义嵌入函数，使用火山引擎API
class VolcanoEmbeddingFunction:
    def __init__(self, api_key, api_url, model):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def __call__(self, input):
        print(f"Generating embeddings for {len(input)} documents")
        # 确保input是列表
        if isinstance(input, str):
            input = [input]
        
        # 调用API获取嵌入向量
        payload = {
            "encoding_format": "float",
            "input": input,
            "model": self.model
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            response.raise_for_status()
            result = response.json()
            
            # 提取嵌入向量
            embeddings = [item["embedding"] for item in result["data"]]
            return embeddings
        except Exception as e:
            print(f"Error getting embeddings: {e}")
            # 返回空向量作为fallback
            return [[0.0] * 2048] * len(input)

# 初始化ChromaDB客户端
def init_vector_db():
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    config = get_embedding_config()
    volcano_ef = VolcanoEmbeddingFunction(config["api_key"], config["api_url"], config["model"])
    try:
        client.delete_collection("metadata_collection")
        print("Deleted existing collection")
    except:
        print("No existing collection to delete")
    collection = client.create_collection(
        name="metadata_collection",
        embedding_function=volcano_ef
    )
    return client, collection

# 从SQLite加载元数据到向量数据库
def load_metadata_to_vector_db(collection):
    conn = sqlite3.connect(METADATA_DB_PATH)
    cursor = conn.cursor()
    
    # 清空现有集合
    try:
        # 获取所有文档ID
        all_ids = collection.get()['ids']
        if all_ids:
            # 如果有文档，按ID删除
            collection.delete(ids=all_ids)
            print(f"Deleted {len(all_ids)} existing documents")
    except Exception as e:
        print(f"Error clearing collection: {e}")
        # 如果获取失败，尝试创建新的集合
        try:
            client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
            client.delete_collection("metadata_collection")
            config = get_embedding_config()
            collection = client.create_collection(
                name="metadata_collection",
                embedding_function=VolcanoEmbeddingFunction(config["api_key"], config["api_url"], config["model"])
            )
            print("Recreated collection after error")
        except Exception as inner_e:
            print(f"Failed to recreate collection: {inner_e}")
            # 继续执行，尝试添加新文档
    
    # 加载数据库信息
    cursor.execute('SELECT id, name, description FROM dbs')
    dbs = cursor.fetchall()
    
    documents = []
    metadatas = []
    ids = []
    
    # 处理数据库信息
    for db_id, db_name, db_desc in dbs:
        # 构建文档文本 - 优先使用描述，如果没有描述则使用名称
        if db_desc and db_desc.strip():
            doc_text = f"数据库: {db_desc}"
        else:
            doc_text = f"数据库: {db_name}"
        
        # 构建元数据 - 用于返回结果
        metadata = {
            "type": "db",
            "id": db_id,
            "name": db_name,
            "description": db_desc
        }
        
        documents.append(doc_text)
        metadatas.append(metadata)
        ids.append(db_id)
        
        # 加载表信息
        cursor.execute('SELECT id, name, description FROM tables_view WHERE db_id = ?', (db_id,))
        tables = cursor.fetchall()
        
        for table_id, table_name, table_desc in tables:
            # 构建表文档文本 - 优先使用描述，如果没有描述则使用名称
            if table_desc and table_desc.strip():
                table_doc = f"数据库: {db_name}\n表: {table_desc}"
            else:
                table_doc = f"数据库: {db_name}\n表: {table_name}"
            
            table_metadata = {
                "type": "table",
                "id": table_id,
                "db_id": db_id,
                "name": table_name,
                "description": table_desc
            }
            
            documents.append(table_doc)
            metadatas.append(table_metadata)
            ids.append(table_id)
            
            # 加载列信息
            cursor.execute('SELECT id, name, type, description FROM columns_view WHERE table_id = ?', (table_id,))
            columns = cursor.fetchall()
            
            for col_id, col_name, col_type, col_desc in columns:
                # 构建列文档文本 - 优先使用描述，如果没有描述则使用名称
                if col_desc and col_desc.strip():
                    col_doc = f"数据库: {db_name}\n表: {table_name}\n字段: {col_desc}\n类型: {col_type}"
                else:
                    col_doc = f"数据库: {db_name}\n表: {table_name}\n字段: {col_name}\n类型: {col_type}"
                
                col_metadata = {
                    "type": "column",
                    "id": col_id,
                    "table_id": table_id,
                    "db_id": db_id,
                    "name": col_name,
                    "data_type": col_type,
                    "description": col_desc
                }
                
                documents.append(col_doc)
                metadatas.append(col_metadata)
                ids.append(col_id)
                
                # 如果是枚举类型，加载枚举值
                if col_type == "ENUM":
                    cursor.execute('SELECT id, value, description FROM enum_values_view WHERE column_id = ?', (col_id,))
                    enum_values = cursor.fetchall()
                    
                    for val_id, val, val_desc in enum_values:
                        # 构建枚举值文档文本 - 优先使用描述，如果没有描述则使用值本身
                        if val_desc and val_desc.strip():
                            val_doc = f"数据库: {db_name}\n表: {table_name}\n字段: {col_name}\n枚举值: {val_desc}"
                        else:
                            val_doc = f"数据库: {db_name}\n表: {table_name}\n字段: {col_name}\n枚举值: {val}"
                        
                        val_metadata = {
                            "type": "enum_value",
                            "id": val_id,
                            "column_id": col_id,
                            "table_id": table_id,
                            "db_id": db_id,
                            "value": val,
                            "description": val_desc
                        }
                        
                        documents.append(val_doc)
                        metadatas.append(val_metadata)
                        ids.append(val_id)
    
    # 分批处理文档（每批20个）
    batch_size = 20
    total_batches = (len(documents) + batch_size - 1) // batch_size
    success_count = 0
    
    for batch_idx in range(total_batches):
        start = batch_idx * batch_size
        end = start + batch_size
        batch_docs = documents[start:end]
        batch_meta = metadatas[start:end]
        batch_ids = ids[start:end]
    
        try:
            # 添加当前批次
            collection.add(
                documents=batch_docs,
                metadatas=batch_meta,
                ids=batch_ids
            )
            success_count += len(batch_docs)
            print(f'成功添加批次 {batch_idx+1}/{total_batches} ({len(batch_docs)} 条)')
            
            # 添加批处理间隔
            if batch_idx < total_batches - 1:
                time.sleep(0.5)
        
        except Exception as batch_error:
            print(f'批处理 {batch_idx+1} 失败: {str(batch_error)}')
            print(f'跳过当前批次（文档 {start}-{end}）')
            continue
    
    print(f'总共成功添加 {success_count}/{len(documents)} 个元数据项')
    conn.close()
    return len(documents)

# 搜索向量数据库
def search_metadata(query, limit=10):
    # 获取现有向量数据库集合，而不是重新初始化
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    try:
        config = get_embedding_config()
        collection = client.get_collection(
            name="metadata_collection",
            embedding_function=VolcanoEmbeddingFunction(config["api_key"], config["api_url"], config["model"])
        )
        # 检查集合是否有数据
        try:
            count = len(collection.get()['ids'])
            print(f"成功获取现有集合，包含 {count} 条数据，准备搜索: {query}")
            if count == 0:
                raise Exception("集合中没有数据")
        except Exception as check_e:
            print(f"集合数据检查失败或没有数据: {check_e}")
            # 加载数据到向量数据库
            count = load_metadata_to_vector_db(collection)
            print(f"加载了 {count} 条数据到现有向量数据库")
    except Exception as e:
        print(f"获取集合失败，尝试初始化: {e}")
        _, collection = init_vector_db()
        # 加载数据到向量数据库
        count = load_metadata_to_vector_db(collection)
        print(f"初始化并加载了 {count} 条数据到向量数据库")
    
    # 执行搜索
    results = collection.query(
        query_texts=[query],
        n_results=limit * 2,  # 增加初始搜索结果数量
        include=['documents', 'metadatas', 'distances']
    )
    
    # 处理结果
    if not results or not results['metadatas']:
        return []
    
    # 组合结果
    combined_results = []
    for i, metadata in enumerate(results['metadatas'][0]):
        # 计算相似度分数（将距离转换为0-1之间的分数）
        distance = results['distances'][0][i]
        base_score = 1.0 / (1.0 + distance)  # 基础分数
        
        # 计算文本匹配分数
        text = results['documents'][0][i].lower()
        query_terms = query.lower().split()
        text_match_score = sum(1.0 if term in text else 0.0 for term in query_terms) / max(1, len(query_terms))
        
        # 组合最终分数，确保不超过1.0
        final_score = min(1.0, (base_score + text_match_score) / 2.0)
        
        # 添加text和score字段
        result = metadata.copy()
        result['text'] = results['documents'][0][i]
        result['score'] = final_score
        combined_results.append(result)
    
    # 按分数排序并限制结果数量
    combined_results.sort(key=lambda x: x['score'], reverse=True)
    combined_results = combined_results[:limit]
    
    return combined_results

# 将搜索结果转换为suggest API格式
def format_suggest_results(search_results):
    # 按数据库和表组织结果
    organized_results = {}
    
    for item in search_results:
        item_type = item.get('type')
        db_id = item.get('db_id')
        
        # 对于数据库类型的结果
        if item_type == 'db':
            db_id = item.get('id')
            if db_id not in organized_results:
                organized_results[db_id] = {
                    "id": db_id,
                    "tables": []
                }
        
        # 对于表类型的结果
        elif item_type == 'table':
            table_id = item.get('id')
            if db_id not in organized_results:
                organized_results[db_id] = {
                    "id": db_id,
                    "tables": []
                }
            
            # 检查表是否已存在
            table_exists = False
            for table in organized_results[db_id]["tables"]:
                if table["id"] == table_id:
                    table_exists = True
                    break
            
            if not table_exists:
                organized_results[db_id]["tables"].append({
                    "id": table_id,
                    "columns": []
                })
        
        # 对于列类型的结果
        elif item_type == 'column':
            table_id = item.get('table_id')
            col_id = item.get('id')
            
            if db_id not in organized_results:
                organized_results[db_id] = {
                    "id": db_id,
                    "tables": []
                }
            
            # 查找或创建表
            table_found = False
            for table in organized_results[db_id]["tables"]:
                if table["id"] == table_id:
                    table_found = True
                    
                    # 检查列是否已存在
                    col_exists = False
                    for col in table["columns"]:
                        if col["id"] == col_id:
                            col_exists = True
                            break
                    
                    if not col_exists:
                        col_data = {"id": col_id}
                        if item.get('data_type') == 'ENUM':
                            col_data["values"] = []
                        table["columns"].append(col_data)
                    break
            
            if not table_found:
                col_data = {"id": col_id}
                if item.get('data_type') == 'ENUM':
                    col_data["values"] = []
                
                organized_results[db_id]["tables"].append({
                    "id": table_id,
                    "columns": [col_data]
                })
        
        # 对于枚举值类型的结果
        elif item_type == 'enum_value':
            table_id = item.get('table_id')
            col_id = item.get('column_id')
            val_id = item.get('id')
            
            if db_id not in organized_results:
                organized_results[db_id] = {
                    "id": db_id,
                    "tables": []
                }
            
            # 查找或创建表和列
            table_found = False
            for table in organized_results[db_id]["tables"]:
                if table["id"] == table_id:
                    table_found = True
                    
                    # 查找或创建列
                    col_found = False
                    for col in table["columns"]:
                        if col["id"] == col_id:
                            col_found = True
                            
                            # 确保values字段存在
                            if "values" not in col:
                                col["values"] = []
                            
                            # 检查值是否已存在
                            val_exists = False
                            for val in col["values"]:
                                if val["id"] == val_id:
                                    val_exists = True
                                    break
                            
                            if not val_exists:
                                col["values"].append({"id": val_id})
                            break
                    
                    if not col_found:
                        table["columns"].append({
                            "id": col_id,
                            "values": [{"id": val_id}]
                        })
                    break
            
            if not table_found:
                organized_results[db_id]["tables"].append({
                    "id": table_id,
                    "columns": [{
                        "id": col_id,
                        "values": [{"id": val_id}]
                    }]
                })
    
    # 转换为列表格式
    return list(organized_results.values())