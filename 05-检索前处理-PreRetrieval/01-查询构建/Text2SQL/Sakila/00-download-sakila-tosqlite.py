# download_sakila_final.py
import os
import requests
import sqlite3
import re
import tarfile
import tempfile
import shutil

def download_file(url, filename):
    """下载文件"""
    print(f"正在下载 {filename}...")
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)
    print(f"✅ {filename} 下载完成")

def extract_tar(tar_file, extract_path):
    """解压 tar.gz 文件"""
    print(f"正在解压 {tar_file}...")
    with tarfile.open(tar_file, 'r:gz') as tar:
        tar.extractall(path=extract_path)
    print(f"✅ 解压完成")

def parse_sql_value(value_str):
    """解析SQL值，处理NULL、数字、字符串等"""
    value_str = value_str.strip()
    
    if value_str.upper() == 'NULL':
        return None
    elif value_str.startswith("'") and value_str.endswith("'"):
        # 处理字符串，移除外层引号并处理转义
        return value_str[1:-1].replace("\\'", "'").replace("\\\\", "\\")
    elif value_str.startswith('"') and value_str.endswith('"'):
        # 处理双引号字符串
        return value_str[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    elif value_str.replace('.', '').replace('-', '').isdigit():
        # 处理数字
        if '.' in value_str:
            return float(value_str)
        else:
            return int(value_str)
    else:
        # 其他情况作为字符串处理
        return value_str

def parse_values_string(values_str):
    """解析VALUES字符串，正确分割多个记录"""
    records = []
    current_record = []
    current_value = ""
    in_quotes = False
    quote_char = None
    paren_level = 0
    
    i = 0
    while i < len(values_str):
        char = values_str[i]
        
        if char in ['"', "'"]:
            current_value += char
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                # 检查是否是转义的引号
                if i > 0 and values_str[i-1] == '\\':
                    pass  # 这是转义的引号，继续
                else:
                    in_quotes = False
                    quote_char = None
        elif char == '(':
            if not in_quotes:
                paren_level += 1
                if paren_level == 1:
                    # 开始新记录
                    current_record = []
                    current_value = ""
                else:
                    current_value += char
            else:
                current_value += char
        elif char == ')':
            if not in_quotes:
                paren_level -= 1
                if paren_level == 0:
                    # 结束当前记录
                    if current_value:
                        current_record.append(parse_sql_value(current_value))
                    records.append(current_record)
                    current_value = ""
                else:
                    current_value += char
            else:
                current_value += char
        elif char == ',' and not in_quotes:
            if paren_level == 1:
                # 字段分隔符
                current_record.append(parse_sql_value(current_value))
                current_value = ""
            else:
                current_value += char
        else:
            current_value += char
        
        i += 1
    
    return records

def populate_film_text_table(conn):
    """从film表填充film_text表"""
    print("正在填充film_text表...")
    cursor = conn.cursor()
    
    # 清空film_text表
    cursor.execute("DELETE FROM film_text")
    
    # 从film表复制数据到film_text表
    cursor.execute("""
        INSERT INTO film_text (film_id, title, description)
        SELECT film_id, title, description FROM film
    """)
    
    # 获取插入的记录数
    cursor.execute("SELECT COUNT(*) FROM film_text")
    count = cursor.fetchone()[0]
    
    conn.commit()
    print(f"✅ film_text表已填充 {count} 条记录")

def convert_mysql_to_sqlite(mysql_file, sqlite_file):
    """将 MySQL 数据转换为 SQLite 格式"""
    print("正在转换数据...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        # 解压下载的文件
        extract_tar(mysql_file, temp_dir)
        
        # 找到 sakila-data.sql 文件
        data_file = os.path.join(temp_dir, 'sakila-db', 'sakila-data.sql')
        if not os.path.exists(data_file):
            raise FileNotFoundError("找不到 sakila-data.sql 文件")
        
        # 读取 MySQL 数据文件
        with open(data_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 连接到 SQLite 数据库
        conn = sqlite3.connect(sqlite_file)
        cursor = conn.cursor()
        
        # 开始事务
        cursor.execute("BEGIN TRANSACTION")
        
        # 预处理：移除注释和不需要的语句
        print("正在预处理SQL文件...")
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if (line and 
                not line.startswith('--') and 
                not line.startswith('/*') and
                not line.startswith('*/') and
                not line.upper().startswith('LOCK TABLES') and
                not line.upper().startswith('UNLOCK TABLES') and
                not line.upper().startswith('USE ') and
                not line.upper().startswith('SET ') and
                not line.upper().startswith('/*!') and
                line != ''):
                cleaned_lines.append(line)
        
        content = ' '.join(cleaned_lines)
        
        # 使用更精确的正则表达式找到所有完整的INSERT语句
        print("正在解析INSERT语句...")
        insert_pattern = r'INSERT INTO\s+`?(\w+)`?\s+.*?VALUES\s*(.*?)(?=INSERT INTO|\Z)'
        matches = re.finditer(insert_pattern, content, re.DOTALL | re.IGNORECASE)
        
        total_records = 0
        processed_tables = {}  # 跟踪已处理的表以避免重复
        
        for match in matches:
            table_name = match.group(1)
            values_part = match.group(2).strip()
            
            # 移除末尾的分号
            if values_part.endswith(';'):
                values_part = values_part[:-1]
            
            if not values_part:
                continue
            
            # 如果表已经处理过，累加记录而不是重新开始
            if table_name in processed_tables:
                print(f"继续处理表: {table_name} (追加数据)")
            else:
                print(f"正在处理表: {table_name}")
                processed_tables[table_name] = 0
            
            try:
                # 获取表的列信息
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                if not columns_info:
                    print(f"警告: 表 {table_name} 不存在，跳过")
                    continue
                
                expected_columns = len(columns_info)
                
                # 解析VALUES
                records = parse_values_string(values_part)
                
                # 插入数据
                table_records = 0
                for record in records:
                    if len(record) != expected_columns:
                        # 调整记录长度
                        if len(record) > expected_columns:
                            record = record[:expected_columns]
                        else:
                            record.extend([None] * (expected_columns - len(record)))
                    
                    try:
                        placeholders = ','.join(['?' for _ in range(expected_columns)])
                        insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
                        cursor.execute(insert_sql, record)
                        table_records += 1
                        total_records += 1
                        processed_tables[table_name] += 1
                        
                        if processed_tables[table_name] % 1000 == 0:
                            print(f"  已导入 {processed_tables[table_name]} 条记录")
                            
                    except sqlite3.Error as e:
                        print(f"警告: 插入数据到表 {table_name} 时出错: {e}")
                        continue
                
                print(f"✅ 表 {table_name}: 本次导入 {table_records} 条记录，总计 {processed_tables[table_name]} 条记录")
                
            except Exception as e:
                print(f"错误: 处理表 {table_name} 时出错: {e}")
                continue
        
        # 提交事务
        conn.commit()
        
        # 填充film_text表
        populate_film_text_table(conn)
        
        conn.close()
        print(f"✅ 数据转换完成，总共导入 {total_records} 条记录")
        
        # 显示最终统计
        print(f"\n各表最终记录数:")
        print("-" * 30)
        for table_name, count in sorted(processed_tables.items()):
            print(f"{table_name:15}: {count:6,} 条记录")
        
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir)

def create_sqlite_tables(cursor):
    """创建 SQLite 表结构"""
    tables_sql = [
        '''CREATE TABLE actor (
            actor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE address (
            address_id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL,
            address2 TEXT,
            district TEXT NOT NULL,
            city_id INTEGER,
            postal_code TEXT,
            phone TEXT NOT NULL,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE category (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE city (
            city_id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            country_id INTEGER,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE country (
            country_id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE customer (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            address_id INTEGER,
            active INTEGER DEFAULT 1,
            create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE film (
            film_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            release_year INTEGER,
            language_id INTEGER,
            original_language_id INTEGER,
            rental_duration INTEGER DEFAULT 3,
            rental_rate REAL DEFAULT 4.99,
            length INTEGER,
            replacement_cost REAL DEFAULT 19.99,
            rating TEXT DEFAULT 'G',
            special_features TEXT,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE film_actor (
            actor_id INTEGER,
            film_id INTEGER,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (actor_id, film_id)
        )''',
        
        '''CREATE TABLE film_category (
            film_id INTEGER,
            category_id INTEGER,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (film_id, category_id)
        )''',
        
        '''CREATE TABLE film_text (
            film_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT
        )''',
        
        '''CREATE TABLE inventory (
            inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            film_id INTEGER,
            store_id INTEGER,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE language (
            language_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE payment (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            staff_id INTEGER,
            rental_id INTEGER,
            amount REAL NOT NULL,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE rental (
            rental_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rental_date TIMESTAMP NOT NULL,
            inventory_id INTEGER,
            customer_id INTEGER,
            return_date TIMESTAMP,
            staff_id INTEGER,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE staff (
            staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            address_id INTEGER,
            email TEXT,
            store_id INTEGER,
            active INTEGER DEFAULT 1,
            username TEXT NOT NULL,
            password TEXT,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE store (
            store_id INTEGER PRIMARY KEY AUTOINCREMENT,
            manager_staff_id INTEGER,
            address_id INTEGER,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )'''
    ]
    
    for sql in tables_sql:
        cursor.execute(sql)

def drop_existing_tables(cursor):
    """删除已存在的表"""
    print("正在清理已存在的表...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
    print("✅ 表清理完成")

def create_sqlite_triggers(cursor):
    """创建SQLite触发器来维护film_text表"""
    print("正在创建触发器...")
    
    # INSERT触发器
    cursor.execute('''
    CREATE TRIGGER ins_film 
    AFTER INSERT ON film 
    FOR EACH ROW 
    BEGIN 
        INSERT INTO film_text (film_id, title, description) 
        VALUES (NEW.film_id, NEW.title, NEW.description); 
    END
    ''')
    
    # UPDATE触发器
    cursor.execute('''
    CREATE TRIGGER upd_film 
    AFTER UPDATE ON film 
    FOR EACH ROW 
    BEGIN 
        UPDATE film_text 
        SET title = NEW.title, description = NEW.description 
        WHERE film_id = NEW.film_id; 
    END
    ''')
    
    # DELETE触发器
    cursor.execute('''
    CREATE TRIGGER del_film 
    AFTER DELETE ON film 
    FOR EACH ROW 
    BEGIN 
        DELETE FROM film_text WHERE film_id = OLD.film_id; 
    END
    ''')
    
    print("✅ 触发器创建完成")

def count_records(conn):
    """统计数据库中的记录数"""
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    
    # 统计每个表的记录数
    total_records = 0
    print("\n最终数据库表记录统计：")
    print("-" * 50)
    
    for table in sorted(tables):
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        total_records += count
        print(f"表 {table_name:15}: {count:6,} 条记录")
    
    print("-" * 50)
    print(f"总计: {total_records:,} 条记录")

def main():
    # 创建目录
    db_dir = "90-文档-Data/sakila"
    os.makedirs(db_dir, exist_ok=True)
    
    # 下载 Sakila 数据库
    url = "https://downloads.mysql.com/docs/sakila-db.tar.gz"
    tar_file = os.path.join(db_dir, "sakila-db.tar.gz")
    download_file(url, tar_file)
    
    # 创建 SQLite 数据库
    sqlite_file = os.path.join(db_dir, "sakila.db")
    conn = sqlite3.connect(sqlite_file)
    cursor = conn.cursor()
    
    # 删除已存在的表
    drop_existing_tables(cursor)
    
    # 创建表结构
    print("正在创建表结构...")
    create_sqlite_tables(cursor)
    
    # 创建触发器
    create_sqlite_triggers(cursor)
    
    # 提交更改并关闭连接
    conn.commit()
    conn.close()
    
    # 转换并导入数据
    convert_mysql_to_sqlite(tar_file, sqlite_file)
    
    # 统计记录数
    conn = sqlite3.connect(sqlite_file)
    count_records(conn)
    conn.close()
    
    # 清理下载的文件
    os.remove(tar_file)
    print("✅ 数据库创建和导入完成")

if __name__ == "__main__":
    main()