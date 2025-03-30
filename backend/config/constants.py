import os

# 获取项目根目录的绝对路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 初始化相关目录
INITIAL_DIR = os.path.join(ROOT_DIR, 'initial')

# 初始数据目录
INITIAL_METADATA_DIR = os.path.join(INITIAL_DIR, 'metadata')
# metadata.sql文件路径
INITIAL_METADATA_SCHEMA_SQL_PATH = os.path.join(INITIAL_METADATA_DIR, 'schema.sql')

# 初始数据目录
INITIAL_DATA_DIR = os.path.join(INITIAL_DIR, 'data')


# metadata数据库文件路径
METADATA_DB_PATH = os.path.join(ROOT_DIR, 'metadata.db')

# 数据数据库文件路径
DATA_DB_PATH = os.path.join(ROOT_DIR, 'data.db')

# 配置数据库文件路径
CONFIG_DB_PATH = os.path.join(ROOT_DIR, 'config.db')

# ChromaDB持久化目录
CHROMA_PERSIST_DIR = os.path.join(ROOT_DIR, 'chroma_db')

