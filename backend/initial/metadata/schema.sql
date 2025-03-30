-- 数据库表
CREATE TABLE IF NOT EXISTS dbs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

-- 表信息
CREATE TABLE IF NOT EXISTS tables (
    id TEXT PRIMARY KEY,
    db_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    type TEXT,
    FOREIGN KEY (db_id) REFERENCES dbs(id)
);

-- 列信息
CREATE TABLE IF NOT EXISTS columns (
    id TEXT PRIMARY KEY,
    table_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    FOREIGN KEY (table_id) REFERENCES tables(id)
);

-- 枚举值
CREATE TABLE IF NOT EXISTS enum_values (
    id TEXT PRIMARY KEY,
    column_id TEXT NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (column_id) REFERENCES columns(id)
);


-- 用户自定义表描述
CREATE TABLE IF NOT EXISTS user_tables (
    table_name TEXT PRIMARY KEY,
    description TEXT NOT NULL
);

-- 用户自定义字段描述
CREATE TABLE IF NOT EXISTS user_columns (
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    description TEXT NOT NULL,
    PRIMARY KEY (table_name, column_name)
);

-- 用户自定义枚举值描述
CREATE TABLE IF NOT EXISTS user_enum_values (
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    enum_value TEXT NOT NULL,
    description TEXT NOT NULL,
    PRIMARY KEY (table_name, column_name, enum_value)
);


CREATE VIEW tables_view AS
SELECT 
    t.id,
    t.db_id,
    t.name,
    COALESCE(ut.description, t.description) AS description,
    t.type
FROM  tables t
LEFT JOIN  user_tables ut ON t.name = ut.table_name;


CREATE VIEW columns_view AS
SELECT 
    c.id,
    c.table_id,
    c.name,
    c.type,
    COALESCE(uc.description, c.description) AS description,
    c.is_primary
FROM columns c
LEFT JOIN tables t ON c.table_id = t.id
LEFT JOIN user_columns uc ON t.name = uc.table_name AND c.name = uc.column_name;

CREATE VIEW enum_values_view AS
SELECT 
    ev.id,
    ev.column_id,
    ev.value,
    COALESCE(uev.description, ev.description) AS description
FROM enum_values ev
LEFT JOIN columns c ON ev.column_id = c.id
LEFT JOIN tables t ON c.table_id = t.id
LEFT JOIN user_enum_values uev ON t.name = uev.table_name AND c.name = uev.column_name AND ev.value = uev.enum_value;

-- 自由查询示例表
CREATE TABLE IF NOT EXISTS freeshots (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    likes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 业务术语表
CREATE TABLE IF NOT EXISTS terms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    likes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
