# generate_ddl_yaml.py
import os
import yaml
import sqlite3
from dotenv import load_dotenv

# 1. 加载 .env 中的数据库配置
load_dotenv()  

# SQLite3 数据库文件路径
db_dir = "90-文档-Data/sakila"
db_path = os.path.join(db_dir, "sakila.db")

# 确保目录存在
os.makedirs(db_dir, exist_ok=True)

# 检查数据库文件是否存在
if not os.path.exists(db_path):
    print(f"⚠️ 数据库文件不存在: {db_path}")
    print("正在创建新的数据库文件...")
    # 创建新的数据库文件
    conn = sqlite3.connect(db_path)
    conn.close()
    print("✅ 数据库文件已创建")

# SQLite3 连接
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row  # 这样可以通过列名访问结果

ddl_map = {}
try:
    # SQLite3 实现
    cursor = conn.cursor()
    
    # 3. 获取所有表名（排除SQLite系统表）
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
    """)
    tables = [row[0] for row in cursor.fetchall()]

    # 4. 遍历表列表，获取表结构
    for tbl in tables:
        # 获取表的创建语句
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{tbl}';")
        result = cursor.fetchone()
        if result:
            ddl_map[tbl] = result['sql']

finally:
    conn.close()

# 5. 写入 YAML 文件 - 只包含表的DDL
with open(os.path.join(db_dir, "ddl_statements_sqlite.yaml"), "w", encoding='utf-8') as f:
    yaml.safe_dump(ddl_map, f, sort_keys=True, allow_unicode=True, default_flow_style=False)

print(f"✅ ddl_statements_sqlite.yaml 已生成，共包含 {len(ddl_map)} 张表：", list(ddl_map.keys()))