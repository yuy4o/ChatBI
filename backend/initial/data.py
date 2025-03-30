import sqlite3
import json
import os
import glob
from config.constants import DATA_DB_PATH, INITIAL_DATA_DIR, INITIAL_METADATA_DIR

def init_data():    
    # 每次初始化时先删除数据库文件
    if os.path.exists(DATA_DB_PATH):
        os.remove(DATA_DB_PATH)
    
    # Connect to SQLite database
    conn = sqlite3.connect(DATA_DB_PATH)
    cursor = conn.cursor()
    
    # Dictionary to store table schemas
    table_schemas = {}
    
    # First pass: read metadata files to create table schemas
    for filename in os.listdir(INITIAL_METADATA_DIR):
        if filename.endswith('.json') and filename != 'template.json':
            file_path = os.path.join(INITIAL_METADATA_DIR, filename)
            db_name = os.path.splitext(filename)[0]  # Get database name without extension
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    
                # Process each table in the metadata
                for table in metadata.get('tables', []):
                    table_name = table['name']
                    columns = table.get('columns', [])
                    
                    # Create SQL for table creation
                    create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
                    column_defs = []
                    primary_keys = []
                    
                    for column in columns:
                        col_name = column['name']
                        col_type = column['type']
                        
                        # Map JSON column types to SQLite types
                        if col_type.startswith('VARCHAR'):
                            sqlite_type = 'TEXT'
                        elif col_type in ['INT', 'BIGINT']:
                            sqlite_type = 'INTEGER'
                        elif col_type == 'DECIMAL':
                            sqlite_type = 'REAL'
                        elif col_type in ['TIMESTAMP', 'DATETIME']:
                            sqlite_type = 'TEXT'
                        elif col_type == 'ENUM':
                            sqlite_type = 'TEXT'
                        elif col_type == 'BOOLEAN':
                            sqlite_type = 'INTEGER'
                        elif col_type == 'TEXT':
                            sqlite_type = 'TEXT'
                        else:
                            sqlite_type = 'TEXT'
                        
                        column_def = f"    {col_name} {sqlite_type}"
                        column_defs.append(column_def)
                        
                        # Track primary keys
                        if column.get('is_primary', False):
                            primary_keys.append(col_name)
                    
                    # Add primary key constraint if any
                    if primary_keys:
                        column_defs.append(f"    PRIMARY KEY ({', '.join(primary_keys)})")
                    
                    create_table_sql += ",\n".join(column_defs)
                    create_table_sql += "\n);"
                    
                    # Store the create table SQL
                    table_schemas[table_name] = create_table_sql
            except Exception as e:
                print(f"Error processing metadata file {filename}: {e}")
    
    # Create tables in the database
    for table_name, create_sql in table_schemas.items():
        try:
            cursor.execute(create_sql)
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")
    
    # Second pass: load data from data files
    data_files = glob.glob(os.path.join(INITIAL_DATA_DIR, "*.json"))
    
    for data_file in data_files:
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # Process each table in the data file
                    for table_name, records in data.items():
                        if table_name in table_schemas and isinstance(records, list):
                            for record in records:
                                # Prepare insert statement
                                columns = list(record.keys())
                                placeholders = ['?'] * len(columns)
                                values = [record[col] for col in columns]
                                
                                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                                
                                try:
                                    cursor.execute(insert_sql, values)
                                except Exception as e:
                                    print(f"Error inserting data into {table_name}: {e}")
                except Exception as e:
                    print(f"Error processing data file {data_file}: {e}")
    
    conn.commit()
    conn.close()
    print(f"Data database initialized successfully: {DATA_DB_PATH}")

def get_table_data(table_name, limit=100, offset=0, filters=None):
    """
    Get data from a specific table with pagination and optional filtering
    
    Args:
        table_name (str): Name of the table to query
        limit (int): Maximum number of records to return
        offset (int): Number of records to skip
        filters (dict): Optional dictionary of column:value pairs for filtering
        
    Returns:
        list: List of dictionaries containing the data
    """
    conn = sqlite3.connect(DATA_DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    try:
        # Build the query
        query = f"SELECT * FROM {table_name}"
        params = []
        
        # Add filters if provided
        if filters and isinstance(filters, dict):
            where_clauses = []
            for column, value in filters.items():
                where_clauses.append(f"{column} = ?")
                params.append(value)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        # Add pagination
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute the query
        cursor.execute(query, params)
        
        # Convert rows to dictionaries
        result = [dict(row) for row in cursor.fetchall()]
        return result
    except Exception as e:
        print(f"Error querying table {table_name}: {e}")
        return []
    finally:
        conn.close()

def get_table_count(table_name, filters=None):
    """
    Get the total count of records in a table with optional filtering
    
    Args:
        table_name (str): Name of the table to query
        filters (dict): Optional dictionary of column:value pairs for filtering
        
    Returns:
        int: Total count of records
    """
    conn = sqlite3.connect(DATA_DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Build the query
        query = f"SELECT COUNT(*) FROM {table_name}"
        params = []
        
        # Add filters if provided
        if filters and isinstance(filters, dict):
            where_clauses = []
            for column, value in filters.items():
                where_clauses.append(f"{column} = ?")
                params.append(value)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        # Execute the query
        cursor.execute(query, params)
        
        # Get the count
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"Error counting records in table {table_name}: {e}")
        return 0
    finally:
        conn.close()