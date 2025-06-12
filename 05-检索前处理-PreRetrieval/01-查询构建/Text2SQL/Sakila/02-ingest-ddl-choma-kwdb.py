# ingest_ddl_chroma_kwdb.py
import logging
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import torch
import yaml
import os
import shutil
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 1. 初始化嵌入函数
# 设置环境变量
os.environ["TRANSFORMERS_CACHE"] = "/root/autodl-tmp/huggingface_cache"
os.environ["HF_HOME"] = "/root/autodl-tmp/huggingface_cache"
os.environ["HF_DATASETS_CACHE"] = "/root/autodl-tmp/huggingface_cache"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 使用镜像
os.environ["HF_HUB_OFFLINE"] = "1"  # 强制离线模式

# 加载环境变量
load_dotenv()

# 初始化模型
model_path = "/root/autodl-tmp/huggingface_cache/hub/models--BAAI--bge-m3"
embeddings = HuggingFaceEmbeddings(
    model_name=model_path,
    model_kwargs={
        "device": "cpu",
        "local_files_only": True
    }
)

# 2. 读取 DDL 列表
with open("90-文档-Data/sakila/ddl_statements_sqlite.yaml","r") as f:
    ddl_map = yaml.safe_load(f)
    logging.info(f"[DDL] 从YAML文件加载了数据")

# 3. 准备数据
texts = []
metadatas = []

# 检查YAML文件的结构
if isinstance(ddl_map, dict):
    # 如果YAML包含database_type等信息
    if 'database_type' in ddl_map:
        texts.append(f"Database type: {ddl_map['database_type']}")
        metadatas.append({"table_name": "database_info", "type": "database_type"})
        
        # 如果有database_name信息
        if 'database_name' in ddl_map:
            texts.append(f"Database name: {ddl_map['database_name']}")
            metadatas.append({"table_name": "database_info", "type": "database_name"})
        
        # 处理tables字段中的DDL
        if 'tables' in ddl_map:
            tables_data = ddl_map['tables']
        else:
            tables_data = ddl_map
    else:
        # 如果YAML直接就是表名到DDL的映射
        tables_data = ddl_map
        # 添加默认的数据库类型信息
        texts.append("Database type: sqlite3")
        metadatas.append({"table_name": "database_info", "type": "database_type"})
        texts.append("Database name: sakila")
        metadatas.append({"table_name": "database_info", "type": "database_name"})

    # 添加所有表的DDL（排除sqlite_sequence系统表）
    for tbl, ddl in tables_data.items():
        if tbl != 'sqlite_sequence':  # 排除系统表
            texts.append(ddl)
            metadatas.append({"table_name": tbl, "type": "table_ddl"})
else:
    logging.error("[DDL] YAML文件格式不正确")
    exit(1)

logging.info(f"[DDL] 准备处理 {len(texts)} 个DDL语句和信息")

# 4. 清空旧的数据库
persist_directory = "chroma_db"
if os.path.exists(persist_directory):
    shutil.rmtree(persist_directory)
    logging.info(f"[DDL] 已清空旧的数据库目录: {persist_directory}")

# 5. 创建Chroma向量数据库
vectorstore = Chroma.from_texts(
    texts=texts,
    embedding=embeddings,
    metadatas=metadatas,
    persist_directory=persist_directory
)

# 6. 持久化存储
vectorstore.persist()
logging.info(f"[DDL] 成功将数据存储到Chroma数据库，路径：{persist_directory}")

# 7. 验证存储的数据
logging.info("[DDL] 验证存储的数据:")
for i, (text, metadata) in enumerate(zip(texts[:3], metadatas[:3])):  # 显示前3个
    logging.info(f"  [{i+1}] {metadata['table_name']}: {text[:100]}...")

logging.info("[DDL] 知识库构建完成")