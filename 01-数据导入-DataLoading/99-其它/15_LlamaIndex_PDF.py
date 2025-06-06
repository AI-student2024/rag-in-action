from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import VectorStoreIndex
from llama_index.core import Settings
from llama_index.readers.file import PDFReader

from dotenv import load_dotenv
load_dotenv()   

import os
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.deepseek.base import DeepSeek


# Setup LLM and embedding models
model_path = "/root/autodl-tmp/huggingface_cache/hub/models--BAAI--bge-m3"
embed_model = HuggingFaceEmbedding(
    model_name=model_path,
    # 对于本地模型，通常不需要指定 device 或 local_files_only，
    # 但为了与 LangChain 代码保持一致且确保本地加载，可以保留
    model_kwargs={
        "device": "cpu",
        "local_files_only": True
    }
)
llm = DeepSeek(
    api_key=os.getenv("DEEPSEEK_API_KEY"),  # 从环境变量获取 API 密钥
    model="deepseek-chat",  # 使用 deepseek-chat 模型
    temperature=0,
    max_tokens=1000,
    timeout=60  # 设置超时时间为60秒
)

Settings.llm = llm
Settings.embed_model = embed_model

# Load PDF using standard PDFReader
loader = PDFReader()
documents = loader.load_data(
    file="90-文档-Data/复杂PDF/uber_10q_march_2022.pdf"
)

# Create index directly from documents
index = VectorStoreIndex.from_documents(documents)

# Create query engine
query_engine = index.as_query_engine(
    similarity_top_k=3,
    verbose=True
)

query = "What is the change of free cash flow and what is the rate from the financial and operational highlights?"
query = "how many COVID-19 response initiatives in year 2021?"
query = "how much the COVID-19 response initiatives inpact the EBITDA?" # 重塑问题的重要性
# query = "After the year of COVID-19, how much EBITDA profit improved?"
# query = "What is the Adjusted EBITDA loss in year COVID-19?"
# query = "how much is the Loss from operations?"
# query = "how much is the Loss from operations for 2021?"


response = query_engine.query(query)
print("\n************LlamaIndex Query Response************")
print(response)

# Display retrieved chunks
print("\n************Retrieved Text Chunks************")
for i, source_node in enumerate(response.source_nodes):
    print(f"\nChunk {i+1}:")
    print("Text content:")
    print(source_node.text)
    print("-" * 50)