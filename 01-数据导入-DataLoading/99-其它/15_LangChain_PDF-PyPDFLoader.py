from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_deepseek import ChatDeepSeek
import os
import time

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

# 初始化 DeepSeek 模型
llm = ChatDeepSeek(
    api_key=os.getenv("DEEPSEEK_API_KEY"),  # 从环境变量获取 API 密钥
    model="deepseek-chat",  # 使用 deepseek-chat 模型
    temperature=0,
    max_tokens=1000,
    timeout=60  # 设置超时时间为60秒
)

# 设置向量存储路径
vector_store_path = "/root/autodl-tmp/rag-in-action/vector_store"

# 加载 PDF 文件
print("正在加载 PDF 文件...")
loader = PyPDFLoader("90-文档-Data/复杂PDF/uber_10q_march_2022.pdf")
documents = loader.load()
print("PDF 文件加载完成。")

# 文本分割
print("正在进行文本分割...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    add_start_index=True,
)
chunks = text_splitter.split_documents(documents)
print(f"文本分割完成，共生成 {len(chunks)} 块。")

# 创建向量存储
print("正在创建嵌入向量和向量存储...")
if os.path.exists(vector_store_path):
    print("加载已存在的向量存储...")
    vectorstore = FAISS.load_local(vector_store_path, embeddings, allow_dangerous_deserialization=True)
else:
    print("创建新的向量存储...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    # 保存向量存储
    print(f"保存向量存储到 {vector_store_path}")
    vectorstore.save_local(vector_store_path)
print("向量存储创建完成。")

# 创建检索链
print("正在创建检索链...")
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),  # 减少检索的文档数量
    return_source_documents=True,
    verbose=True
)
print("检索链创建完成。")

# 查询示例
query = "What is the change of free cash flow and what is the rate from the financial and operational highlights?"
print(f"\n正在执行查询: {query}")
print("正在检索相关文档...")
start_time = time.time()
response = qa_chain.invoke({"query": query})
end_time = time.time()
print(f"查询完成，耗时: {end_time - start_time:.2f} 秒")

print("\n************LangChain Query Response************")
print("Answer:", response["result"])
print("\nSource Documents:")
for i, doc in enumerate(response["source_documents"], 1):
    print(f"\nDocument {i}:")
    print(doc.page_content[:200] + "...")


query = "how many COVID-19 response initiatives (In millions) in year 2022?"
print(f"\n正在执行查询: {query}")
response = qa_chain.invoke({"query": query})

print("\n************LangChain Query Response************")
print("Answer:", response["result"])
print("\nSource Documents:")
for i, doc in enumerate(response["source_documents"], 1):
    print(f"\nDocument {i}:")
    print(doc.page_content[:200] + "...")


query = "how many COVID-19 response initiatives (In millions) in year 2023?"
print(f"\n正在执行查询: {query}")
response = qa_chain.invoke({"query": query})

print("\n************LangChain Query Response************")
print("Answer:", response["result"])
print("\nSource Documents:")
for i, doc in enumerate(response["source_documents"], 1):
    print(f"\nDocument {i}:")
    print(doc.page_content[:200] + "...")