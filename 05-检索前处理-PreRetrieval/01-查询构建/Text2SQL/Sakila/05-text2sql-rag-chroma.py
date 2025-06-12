# text2sql_chroma.py
import os
import logging
import yaml
import re
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from sqlalchemy import create_engine, text
from langchain_deepseek import ChatDeepSeek

# 1. 环境与日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()  # 加载 .env 环境变量

# 2. 初始化 DeepSeek API
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
llm = ChatDeepSeek(
    api_key=deepseek_api_key,
    model="deepseek-chat",
    temperature=0.2,
    max_tokens=1000,
    timeout=60
)

# 3. 初始化嵌入模型
model_path = "/root/autodl-tmp/huggingface_cache/hub/models--BAAI--bge-m3"
embeddings = HuggingFaceEmbeddings(
    model_name=model_path,
    model_kwargs={
        "device": "cpu",
        "local_files_only": True
    }
)

# 4. 加载Chroma数据库
persist_directory = "chroma_db"
vectorstore = Chroma(
    persist_directory=persist_directory,
    embedding_function=embeddings
)

# 5. 数据库连接（SQLite）
DB_URL = os.getenv(
    "SAKILA_DB_URL", 
    "sqlite:////root/autodl-tmp/rag-in-action/90-文档-Data/sakila/sakila.db"
)
engine = create_engine(DB_URL)

# 6. SQL 提取函数
def extract_sql(text: str) -> str:
    # 尝试匹配 SQL 代码块
    sql_blocks = re.findall(r'```sql\n(.*?)\n```', text, re.DOTALL)
    if sql_blocks:
        return sql_blocks[0].strip()
    
    # 如果没有找到代码块，尝试匹配 SELECT 语句
    select_match = re.search(r'SELECT.*?;', text, re.DOTALL)
    if select_match:
        return select_match.group(0).strip()
    
    # 如果都没有找到，返回原始文本
    return text.strip()

# 7. 核心流程：自然语言 -> SQL -> 执行 -> 返回
def text2sql(question: str):
    # 7.1 RAG 检索：DDL
    ddl_results = vectorstore.similarity_search(question, k=3)
    ddl_context = "\n".join(doc.page_content for doc in ddl_results)
    logging.info(f"[检索] DDL检索结果: {ddl_context}")

    # 7.2 Prompt 组装
    prompt = (
        f"### Schema Definitions:\n{ddl_context}\n"
        f"### Query:\n\"{question}\"\n"
        "请只返回SQL语句，不要包含任何解释或说明。"
    )
    logging.info("[生成] 开始生成SQL")

    # 7.3 调用 DeepSeek API
    response = llm.invoke(prompt)
    raw_sql = response.content.strip()
    sql = extract_sql(raw_sql)
    logging.info(f"[生成] 原始输出: {raw_sql}")
    logging.info(f"[生成] 提取的SQL: {sql}")

    # 7.4 执行并打印结果
    try:
        with engine.connect() as conn:
            if sql.strip().upper().startswith('SELECT'):
                # 处理SELECT查询
                result = conn.execute(text(sql))
                cols = result.keys()
                rows = result.fetchall()
                print("\n查询结果：")
                print("列名：", cols)
                for r in rows:
                    print(r)
            else:
                # 处理INSERT/UPDATE/DELETE等修改操作
                conn.execute(text(sql))
                conn.commit()
                print("\n执行成功！")
                
                # 验证修改结果
                if sql.strip().upper().startswith('UPDATE'):
                    # 从UPDATE语句中提取表名和WHERE条件
                    table_match = re.search(r'UPDATE\s+(\w+)', sql, re.IGNORECASE)
                    where_match = re.search(r'WHERE\s+(.*?);', sql, re.IGNORECASE)
                    if table_match and where_match:
                        table_name = table_match.group(1)
                        where_clause = where_match.group(1)
                        verify_sql = f"SELECT * FROM {table_name} WHERE {where_clause}"
                        result = conn.execute(text(verify_sql))
                        rows = result.fetchall()
                        if rows:
                            print("\n验证结果：")
                            print("列名：", result.keys())
                            for r in rows:
                                print(r)
                elif sql.strip().upper().startswith('INSERT'):
                    # 对于INSERT，获取最后插入的ID
                    result = conn.execute(text("SELECT last_insert_rowid();"))
                    last_id = result.scalar()
                    if last_id:
                        # 获取插入的记录
                        table_match = re.search(r'INSERT\s+INTO\s+(\w+)', sql, re.IGNORECASE)
                        if table_match:
                            table_name = table_match.group(1)
                            verify_sql = f"SELECT * FROM {table_name} WHERE rowid = {last_id}"
                            result = conn.execute(text(verify_sql))
                            rows = result.fetchall()
                            if rows:
                                print("\n验证结果：")
                                print("列名：", result.keys())
                                for r in rows:
                                    print(r)
    except Exception as e:
        logging.error(f"[执行] 执行失败: {e}")
        print("执行错误：", e)

# 8. 程序入口
if __name__ == "__main__":
    user_q = input("请输入您的自然语言查询： ")
    text2sql(user_q) 