import sqlite3
import os
from typing import List, Dict, Any, Union, Tuple, Optional
from config.constants import METADATA_DB_PATH, DATA_DB_PATH

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass


def execute_query(db: str, sql: str, params: Optional[Union[Tuple, List, Dict]] = None, fetch_all: bool = True) -> Union[List[Dict[str, Any]], Dict[str, Any], int]:
    """
    Execute a SQL query on the specified database and return the results
    
    Args:
        db (str): Database to use ('data' or 'metadata')
        sql (str): SQL query to execute
        params (Optional[Union[Tuple, List, Dict]]): Parameters for the SQL query
        fetch_all (bool): Whether to fetch all results or just one row
    
    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any], int]: Query results as a list of dictionaries,
            a single dictionary, or the number of affected rows
    
    Raises:
        DatabaseError: If there's an error connecting to the database or executing the query
    """
    # Determine which database file to use
    if db.lower() == 'data':
        db_file = DATA_DB_PATH
    elif db.lower() == 'metadata':
        db_file = METADATA_DB_PATH
    else:
        raise DatabaseError(f"Unknown database: {db}. Use 'data' or 'metadata'.")
    
    # Check if the database file exists
    if not os.path.exists(db_file):
        raise DatabaseError(f"Database file not found: {db_file}")
    
    # Initialize connection and cursor
    conn = None
    cursor = None
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_file)
        # Enable dictionary cursor
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Execute the query
        if params is not None:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        # Determine the type of query
        if sql.strip().upper().startswith(('SELECT', 'PRAGMA', 'WITH')):
            # For SELECT queries, return the results
            if fetch_all:
                rows = cursor.fetchall()
                # Convert rows to dictionaries
                result = [{k: row[k] for k in row.keys()} for row in rows]
                return result
            else:
                row = cursor.fetchone()
                if row:
                    # Convert row to dictionary
                    return {k: row[k] for k in row.keys()}
                return {}
        else:
            # For INSERT, UPDATE, DELETE queries, commit changes and return affected rows
            conn.commit()
            return cursor.rowcount
    
    except sqlite3.Error as e:
        # Rollback transaction if an error occurred
        if conn:
            conn.rollback()
        raise DatabaseError(f"Database error: {str(e)}")
    
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def execute_script(db: str, sql_script: str) -> bool:
    """
    Execute a SQL script containing multiple statements on the specified database
    
    Args:
        db (str): Database to use ('data' or 'metadata')
        sql_script (str): SQL script to execute
    
    Returns:
        bool: True if successful
    
    Raises:
        DatabaseError: If there's an error connecting to the database or executing the script
    """
    # Determine which database file to use
    if db.lower() == 'data':
        db_file = DATA_DB_PATH
    elif db.lower() == 'metadata':
        db_file = METADATA_DB_PATH
    else:
        raise DatabaseError(f"Unknown database: {db}. Use 'data' or 'metadata'.")
    
    # Check if the database file exists
    if not os.path.exists(db_file):
        raise DatabaseError(f"Database file not found: {db_file}")
    
    # Initialize connection
    conn = None
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_file)
        
        # Execute the script
        conn.executescript(sql_script)
        
        # Commit changes
        conn.commit()
        return True
    
    except sqlite3.Error as e:
        # Rollback transaction if an error occurred
        if conn:
            conn.rollback()
        raise DatabaseError(f"Database error: {str(e)}")
    
    finally:
        # Close connection
        if conn:
            conn.close()


def get_tables(db: str) -> List[str]:
    """
    Get a list of all tables in the specified database
    
    Args:
        db (str): Database to use ('data' or 'metadata')
    
    Returns:
        List[str]: List of table names
    
    Raises:
        DatabaseError: If there's an error connecting to the database or executing the query
    """
    sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    try:
        tables = execute_query(db, sql)
        return [table['name'] for table in tables]
    except Exception as e:
        raise DatabaseError(f"Error getting tables: {str(e)}")


def get_table_schema(db: str, table_name: str) -> List[Dict[str, Any]]:
    """
    Get the schema of a table in the specified database
    
    Args:
        db (str): Database to use ('data' or 'metadata')
        table_name (str): Name of the table
    
    Returns:
        List[Dict[str, Any]]: List of column information
    
    Raises:
        DatabaseError: If there's an error connecting to the database or executing the query
    """
    sql = f"PRAGMA table_info({table_name})"
    try:
        return execute_query(db, sql)
    except Exception as e:
        raise DatabaseError(f"Error getting table schema: {str(e)}")


# Metadata DB specific functions
def get_all_dbs() -> List[Dict[str, Any]]:
    """
    Get a list of all databases in the metadata database
    
    Returns:
        List[Dict[str, Any]]: List of databases with id, db name, and description
    
    Raises:
        DatabaseError: If there's an error connecting to the database or executing the query
    """
    try:
        result = execute_query('metadata', 'SELECT id, name, description FROM dbs')
        return [{
            "id": row["id"],
            "db": row["name"],
            "description": row["description"],
            "tables": []
        } for row in result]
    except Exception as e:
        raise DatabaseError(f"Error getting databases: {str(e)}")


def get_db_tables(db_id: str) -> List[Dict[str, Any]]:
    """
    Get a list of all tables for a specific database in the metadata database
    
    Args:
        db_id (str): Database ID
    
    Returns:
        List[Dict[str, Any]]: List of tables with id, name, description, and type
    
    Raises:
        DatabaseError: If there's an error connecting to the database or executing the query
    """
    try:
        sql = '''
            SELECT id, name, description, type 
            FROM tables_view
            WHERE db_id = ?
        '''
        result = execute_query('metadata', sql, (db_id,))
        return [{
            "id": row["id"],
            "table": row["name"],
            "description": row["description"],
            "type": row["type"] or ''
        } for row in result]
    except Exception as e:
        raise DatabaseError(f"Error getting tables: {str(e)}")


def get_table_columns(table_id: str) -> List[Dict[str, Any]]:
    """
    Get a list of all columns for a specific table in the metadata database
    
    Args:
        table_id (str): Table ID
    
    Returns:
        List[Dict[str, Any]]: List of columns with id, name, type, description, is_primary, and optional enum values
    
    Raises:
        DatabaseError: If there's an error connecting to the database or executing the query
    """
    try:
        # Get table name from table_id
        table_sql = '''
            SELECT name
            FROM tables_view
            WHERE id = ?
        '''
        table_result = execute_query('metadata', table_sql, (table_id,))
        if not table_result:
            raise DatabaseError(f"Table with id {table_id} not found")
        table_name = table_result[0]["name"]
        
        # Get user-defined table description
        user_table_sql = '''
            SELECT description
            FROM user_tables
            WHERE table_name = ?
        '''
        user_table_desc = execute_query('metadata', user_table_sql, (table_name,))
        
        # Get column basic information
        sql = '''
            SELECT id, name, type, description, is_primary
            FROM columns_view
            WHERE table_id = ?
        '''
        columns = execute_query('metadata', sql, (table_id,))
        
        # Get user-defined column descriptions
        user_column_sql = '''
            SELECT column_name, description
            FROM user_columns
            WHERE table_name = ?
        '''
        user_column_descs = execute_query('metadata', user_column_sql, (table_name,))
        user_column_desc_map = {row["column_name"]: row["description"] for row in user_column_descs}
        
        result = []
        for col in columns:
            col_data = {
                "id": col["id"],
                "column": col["name"],
                "type": col["type"],
                "description": user_column_desc_map.get(col["name"], col["description"]),
                "is_primary": col["is_primary"]
            }
            
            # Check for enum values
            if col["type"] == 'ENUM':
                enum_sql = '''
                    SELECT id, value, description
                    FROM enum_values_view
                    WHERE column_id = ?
                '''
                enum_values = execute_query('metadata', enum_sql, (col["id"],))
                
                # Get user-defined enum value descriptions
                user_enum_sql = '''
                    SELECT enum_value, description
                    FROM user_enum_values
                    WHERE table_name = ? AND column_name = ?
                '''
                user_enum_descs = execute_query('metadata', user_enum_sql, (table_name, col["name"]))
                user_enum_desc_map = {row["enum_value"]: row["description"] for row in user_enum_descs}
                
                if enum_values:
                    col_data["values"] = [{
                        "id": ev["id"],
                        "value": ev["value"],
                        "description": user_enum_desc_map.get(ev["value"], ev["description"])
                    } for ev in enum_values]
            
            result.append(col_data)
        
        return result
    except Exception as e:
        raise DatabaseError(f"Error getting columns: {str(e)}")


def get_column_enum_values(column_id: str) -> List[Dict[str, Any]]:
    """
    Get a list of all enum values for a specific column in the metadata database
    
    Args:
        column_id (str): Column ID
    
    Returns:
        List[Dict[str, Any]]: List of enum values with value, description, and id
    
    Raises:
        DatabaseError: If there's an error connecting to the database or executing the query
    """
    try:
        sql = 'SELECT value, description, id FROM enum_values_view WHERE column_id = ?'
        result = execute_query('metadata', sql, (column_id,))
        return [{
            "value": row["value"],
            "description": row["description"],
            "id": row["id"]
        } for row in result]
    except Exception as e:
        raise DatabaseError(f"Error getting enum values: {str(e)}")