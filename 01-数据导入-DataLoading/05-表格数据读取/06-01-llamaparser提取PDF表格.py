from llama_index.llms.openai import OpenAI 
from llama_index.llms.deepseek import DeepSeek
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings
from llama_parse import LlamaParse
import time
from dotenv import load_dotenv
import re

# 加载环境变量（确保有OpenAI API密钥）
load_dotenv()

# 设置基础模型
embed_model = OpenAIEmbedding(model="text-embedding-3-small")
llm = DeepSeek(model="deepseek-v3")

Settings.llm = llm
Settings.embed_model = embed_model

# 定义PDF路径
pdf_path = "90-文档-Data/复杂PDF/billionaires_page-1-5.pdf"

# 记录开始时间
start_time = time.time()

# 使用LlamaParse解析PDF
documents = LlamaParse(
    result_type="markdown",
    api_key="llx-HXVbF4X7cegQD3hj1CIyxg4hl755jO5oGFDEYhJi7INXW2ez",
    bounding_box="0.05,0,0.05,0",  # 可选，粗略去掉顶部5%和底部5%
    language="en",
    disable_ocr=False
).load_data(pdf_path)

# 页眉页脚过滤规则
def is_header_or_footer(line):
    if "wikipedia.org/wiki/The_World%27s_Billionaires" in line:
        return True
    if re.fullmatch(r'\d{1,2}/\d{2}', line.strip()):  # 页码如 2/33
        return True
    if re.match(r'\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{2} (AM|PM)', line.strip()):
        return True  # 时间戳
    if "The World's Billionaires - Wikipedia" in line:
        return True
    return False

def is_year_title(line):
    return re.match(r'#\s*\d{4}$', line.strip()) is not None

def is_markdown_title(line):
    return line.strip().startswith("#")

# 后处理：去除页眉页脚、只保留年份标题
cleaned_docs = []
for idx, doc in enumerate(documents):
    lines = doc.text.splitlines()
    filtered_lines = [
        line for line in lines
        if not is_header_or_footer(line)
    ]
    # 只保留年份标题和非标题内容
    filtered_lines = [
        line for line in filtered_lines
        if not (is_markdown_title(line) and not is_year_title(line))
    ]
    cleaned_text = "\n".join(filtered_lines)
    # 获取页码，若无则用顺序编号
    page_number = getattr(doc, "metadata", {}).get("page_number", idx)
    cleaned_docs.append({
        "text": cleaned_text,
        "page_number": page_number
    })

# 按页码排序
cleaned_docs = sorted(cleaned_docs, key=lambda x: x["page_number"])

# 按页码顺序分组到年份（每页只归到该页最先出现的年份组）
year_pattern = re.compile(r'#\s*(\d{4})')
year_docs = {}
last_year = None

for doc in cleaned_docs:
    lines = doc["text"].splitlines()
    page_year = None
    # 查找该页第一个年份
    for line in lines:
        m = year_pattern.match(line.strip())
        if m:
            page_year = m.group(1)
            break
    if page_year is None:
        page_year = last_year  # 没有新年份就归到上一个年份
    else:
        last_year = page_year
    if page_year is not None:
        if page_year not in year_docs:
            year_docs[page_year] = []
        year_docs[page_year].extend(lines)

# 记录结束时间
end_time = time.time()
print(f"PDF解析耗时: {end_time - start_time:.2f}秒")

# 打印每个年份下的内容
print("\n按年份分组后的内容（只保留年份标题）：")
for year, content in year_docs.items():
    print(f"\n==== {year} ====")
    print("\n".join(content))