import os
from dotenv import load_dotenv
load_dotenv()
import numpy as np
from datasets import Dataset
from ragas.metrics import Faithfulness, AnswerRelevancy
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_huggingface import HuggingFaceEmbeddings
from ragas import evaluate



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
llm_model = ChatDeepSeek(
    api_key=os.getenv("DEEPSEEK_API_KEY"),  # 从环境变量获取 API 密钥
    model="deepseek-chat",  # 使用 deepseek-chat 模型
    temperature=0,
    max_tokens=1000,
    timeout=60  # 设置超时时间为60秒
)

# 准备评估用的LLM（使用DeepSeek）
llm = LangchainLLMWrapper(llm_model)




# 准备数据集
data = {
    "question": [
        "Who is the main character in Black Myth: Wukong?",
        "What are the special features of the combat system in Black Myth: Wukong?",
        "How is the visual quality of Black Myth: Wukong?",
    ],
    "answer": [
        "The main character in Black Myth: Wukong is Sun Wukong, based on the Chinese classic 'Journey to the West' but with a new interpretation. This version of Sun Wukong is more mature and brooding, showing a different personality from the traditional character.",
        "Black Myth: Wukong's combat system combines Chinese martial arts with Soulslike game features, including light and heavy attack combinations, technique transformations, and magic systems. Notably, Wukong can transform between different weapon forms during combat, such as his iconic staff and nunchucks, and use various mystical abilities.",
        "Black Myth: Wukong is developed using Unreal Engine 5, showcasing stunning visual quality. The game's scene modeling, lighting effects, and character details are all top-tier, particularly in its detailed recreation of traditional Chinese architecture and mythological settings.",
    ],
    "contexts": [
        [
            "Black Myth: Wukong is an action RPG developed by Game Science, featuring Sun Wukong as the protagonist based on 'Journey to the West' but with innovative interpretations. In the game, Wukong has a more composed personality and carries a special mission.",
            "The game is set in a mythological world, telling a new story that presents a different take on the traditional Sun Wukong character."
        ],
        [
            "The game's combat system is heavily influenced by Soulslike games while incorporating traditional Chinese martial arts elements. Players can utilize different weapon forms, including the iconic staff and other transforming weapons.",
            "During combat, players can unleash various mystical abilities, combined with light and heavy attacks and combo systems, creating a fluid and distinctive combat experience. The game also features a unique transformation system."
        ],
        [
            "Black Myth: Wukong demonstrates exceptional visual quality, built with Unreal Engine 5, achieving extremely high graphical fidelity. The game's environments and character models are meticulously crafted.",
            "The lighting effects, material rendering, and environmental details all reach AAA-level standards, perfectly capturing the atmosphere of an Eastern mythological world."
        ]
    ]
}

dataset = Dataset.from_dict(data)

print("\n=== Ragas评估指标说明 ===")
print("\n1. Faithfulness（忠实度）")
print("- 评估生成的答案是否忠实于上下文内容")
print("- 通过将答案分解为简单陈述，然后验证每个陈述是否可以从上下文中推断得出")
print("- 该指标仅依赖LLM，不需要embedding模型")

# 评估Faithfulness
faithfulness_metric = [Faithfulness(llm=llm)] # 只需要提供生成模型
print("\n正在评估忠实度...")
faithfulness_result = evaluate(dataset, faithfulness_metric)
scores = faithfulness_result['faithfulness']
mean_score = np.mean(scores) if isinstance(scores, (list, np.ndarray)) else scores
print(f"忠实度评分: {mean_score:.4f}")

# print("\n2. AnswerRelevancy（答案相关性）")
# print("- 评估生成的答案与问题的相关程度")
# print("- 使用embedding模型计算语义相似度")
# print("- 我们将比较开源embedding模型和OpenAI的embedding模型")

# 设置两种embedding模型
opensource_embedding = LangchainEmbeddingsWrapper(
    embeddings=embeddings
)
# openai_embedding = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name="BAAI/bge-m3"))

# 创建答案相关性评估指标
opensource_relevancy = [AnswerRelevancy(llm=llm, embeddings=opensource_embedding)]
# openai_relevancy = [AnswerRelevancy(llm=llm, embeddings=openai_embedding)]

print("\n正在评估答案相关性...")
print("\n使用开源Embedding模型评估:")
opensource_result = evaluate(dataset, opensource_relevancy)
scores = opensource_result['answer_relevancy']
opensource_mean = np.mean(scores) if isinstance(scores, (list, np.ndarray)) else scores
print(f"相关性评分: {opensource_mean:.4f}")

# print("\n使用OpenAI Embedding模型评估:")
# openai_result = evaluate(dataset, openai_relevancy)
# scores = openai_result['answer_relevancy']
# openai_mean = np.mean(scores) if isinstance(scores, (list, np.ndarray)) else scores
# print(f"相关性评分: {openai_mean:.4f}")

# 比较两种embedding模型的结果
print("\n=== Embedding模型比较 ===")
# diff = openai_mean - opensource_mean
# print(f"开源模型评分: {opensource_mean:.4f}")
# print(f"OpenAI模型评分: {openai_mean:.4f}")
# print(f"差异: {diff:.4f} ({'OpenAI更好' if diff > 0 else '开源模型更好' if diff < 0 else '相当'})")


'''
我做了以下修改：
移除了 ragas.embeddings.base 中的 HuggingfaceEmbeddings 导入
改为导入 LangChain 的 HuggingFaceEmbeddings
使用 LangchainEmbeddingsWrapper 来包装 LangChain 的 HuggingFaceEmbeddings
这样做的原因是：
LangChain 的 HuggingFaceEmbeddings 是一个完整的实现，包含了所有必要的方法
LangchainEmbeddingsWrapper 会将 LangChain 的嵌入模型适配到 RAGAS 的接口
这个包装器会自动处理同步和异步方法的转换
1. Faithfulness（忠实度）
- 评估生成的答案是否忠实于上下文内容
- 通过将答案分解为简单陈述，然后验证每个陈述是否可以从上下文中推断得出
- 该指标仅依赖LLM，不需要embedding模型

正在评估忠实度...
Evaluating: 100%|███████████████████████████████████████████████████████████████████████████████████████| 3/3 [00:05<00:00,  1.87s/it]
忠实度评分: 0.6071

正在评估答案相关性...

使用开源Embedding模型评估:
Evaluating: 100%|███████████████████████████████████████████████████████████████████████████████████████| 3/3 [00:01<00:00,  1.54it/s]
相关性评分: 0.8565

使用OpenAI Embedding模型评估:
Evaluating: 100%|███████████████████████████████████████████████████████████████████████████████████████| 3/3 [00:06<00:00,  2.11s/it]
相关性评分: 0.9426

=== Embedding模型比较 ===
开源模型评分: 0.8565
OpenAI模型评分: 0.9426
差异: 0.0861 (OpenAI更好)


'''