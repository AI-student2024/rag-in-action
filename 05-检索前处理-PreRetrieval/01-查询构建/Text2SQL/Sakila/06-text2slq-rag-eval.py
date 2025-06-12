import json
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Tuple
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import re
import logging
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from sqlalchemy import create_engine, text
from langchain_deepseek import ChatDeepSeek

class Text2SQLEvaluator:
    def __init__(self, db_path: str, eval_data_path: str):
        """初始化评估器
        
        Args:
            db_path: SQLite数据库路径
            eval_data_path: 评估数据集路径
        """
        self.db_path = db_path
        self.eval_data_path = eval_data_path
        self.conn = sqlite3.connect(db_path)
        self.eval_data = self._load_eval_data()
        
        # 初始化Text2SQL组件
        self._init_text2sql_components()
        
    def _init_text2sql_components(self):
        """初始化Text2SQL相关组件"""
        # 加载环境变量
        load_dotenv()
        
        # 初始化 DeepSeek API
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.llm = ChatDeepSeek(
            api_key=deepseek_api_key,
            model="deepseek-chat",
            temperature=0.2,
            max_tokens=1000,
            timeout=60
        )
        
        # 初始化嵌入模型
        model_path = "/root/autodl-tmp/huggingface_cache/hub/models--BAAI--bge-m3"
        embeddings = HuggingFaceEmbeddings(
            model_name=model_path,
            model_kwargs={
                "device": "cpu",
                "local_files_only": True
            }
        )
        
        # 加载Chroma数据库
        persist_directory = "chroma_db"
        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings
        )
        
        # 数据库连接
        DB_URL = f"sqlite:///{self.db_path}"
        self.engine = create_engine(DB_URL)
        
    def _load_eval_data(self) -> List[Dict[str, Any]]:
        """加载评估数据"""
        with open(self.eval_data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_sql(self, text: str) -> str:
        """从LLM输出中提取SQL语句"""
        # 尝试匹配 SQL 代码块
        sql_blocks = re.findall(r'```sql\n(.*?)\n```', text, re.DOTALL)
        if sql_blocks:
            return sql_blocks[0].strip()
        
        # 尝试匹配各种SQL语句
        sql_patterns = [
            r'(SELECT.*?;)',
            r'(INSERT.*?;)',
            r'(UPDATE.*?;)',
            r'(DELETE.*?;)'
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # 如果都没有找到，返回原始文本
        return text.strip()
    
    def generate_sql(self, question: str) -> str:
        """使用Text2SQL生成SQL语句"""
        try:
            # RAG 检索：DDL
            ddl_results = self.vectorstore.similarity_search(question, k=3)
            ddl_context = "\n".join(doc.page_content for doc in ddl_results)
            
            # Prompt 组装
            prompt = (
                f"### Schema Definitions:\n{ddl_context}\n"
                f"### Query:\n\"{question}\"\n"
                "请只返回SQL语句，不要包含任何解释或说明。"
            )
            
            # 调用 DeepSeek API
            response = self.llm.invoke(prompt)
            raw_sql = response.content.strip()
            sql = self.extract_sql(raw_sql)
            
            return sql
        except Exception as e:
            logging.error(f"生成SQL失败: {e}")
            return ""
    
    def execute_sql(self, sql: str) -> pd.DataFrame:
        """执行SQL查询并返回结果"""
        try:
            # 处理SQLite特定的函数
            sql_cleaned = sql.replace('NOW()', 'datetime("now")')
            return pd.read_sql_query(sql_cleaned, self.conn)
        except Exception as e:
            logging.error(f"执行SQL出错: {e}")
            return pd.DataFrame()
    
    def execute_sql_with_engine(self, sql: str) -> pd.DataFrame:
        """使用SQLAlchemy执行SQL（支持修改操作）"""
        try:
            sql_cleaned = sql.replace('NOW()', 'datetime("now")')
            
            with self.engine.connect() as conn:
                if sql_cleaned.strip().upper().startswith('SELECT'):
                    # 处理SELECT查询
                    result = conn.execute(text(sql_cleaned))
                    columns = result.keys()
                    rows = result.fetchall()
                    return pd.DataFrame(rows, columns=columns)
                else:
                    # 对于修改操作，我们不执行，只返回空DataFrame
                    # 这是为了评估安全，避免修改测试数据
                    return pd.DataFrame()
        except Exception as e:
            logging.error(f"执行SQL出错: {e}")
            return pd.DataFrame()
    
    def normalize_sql_for_comparison(self, sql: str) -> str:
        """标准化SQL语句用于比较"""
        # 移除多余的空格和换行
        sql = re.sub(r'\s+', ' ', sql.strip())
        # 统一大小写
        return sql.upper()
    
    def compare_sql_syntax(self, pred_sql: str, true_sql: str) -> float:
        """比较SQL语法相似度"""
        pred_normalized = self.normalize_sql_for_comparison(pred_sql)
        true_normalized = self.normalize_sql_for_comparison(true_sql)
        
        if pred_normalized == true_normalized:
            return 1.0
        
        # 简单的词级别相似度
        pred_words = set(pred_normalized.split())
        true_words = set(true_normalized.split())
        
        if len(true_words) == 0:
            return 0.0
            
        intersection = len(pred_words.intersection(true_words))
        union = len(pred_words.union(true_words))
        
        return intersection / union if union > 0 else 0.0
    
    def compare_results(self, pred_df: pd.DataFrame, true_df: pd.DataFrame) -> Tuple[float, float, float]:
        """比较预测结果和真实结果"""
        if pred_df.empty and true_df.empty:
            return 1.0, 1.0, 1.0
        elif pred_df.empty or true_df.empty:
            return 0.0, 0.0, 0.0
            
        try:
            # 标准化列名
            pred_df.columns = [col.lower() for col in pred_df.columns]
            true_df.columns = [col.lower() for col in true_df.columns]
            
            # 如果列数不同，返回0
            if len(pred_df.columns) != len(true_df.columns):
                return 0.0, 0.0, 0.0
            
            # 按列名排序
            pred_df = pred_df.reindex(sorted(pred_df.columns), axis=1)
            true_df = true_df.reindex(sorted(true_df.columns), axis=1)
            
            # 将DataFrame转换为集合进行比较
            pred_set = set(map(tuple, pred_df.values))
            true_set = set(map(tuple, true_df.values))
            
            # 计算交集
            intersection = len(pred_set.intersection(true_set))
            
            # 计算精确率、召回率和F1分数
            precision = intersection / len(pred_set) if len(pred_set) > 0 else 0
            recall = intersection / len(true_set) if len(true_set) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            return precision, recall, f1
        except Exception as e:
            logging.error(f"比较结果时出错: {e}")
            return 0.0, 0.0, 0.0
    
    def evaluate(self) -> Dict[str, Any]:
        """执行评估"""
        results = {
            'total': len(self.eval_data),
            'successful_generation': 0,
            'successful_execution': 0,
            'failed_generation': 0,
            'failed_execution': 0,
            'syntax_similarity': [],
            'execution_precision': [],
            'execution_recall': [],
            'execution_f1': [],
            'errors': [],
            'details': []
        }
        
        print(f"开始评估 {len(self.eval_data)} 个样本...")
        
        for i, item in enumerate(self.eval_data, 1):
            print(f"处理第 {i}/{len(self.eval_data)} 个样本...")
            
            detail = {
                'question': item['question'],
                'true_sql': item['sql'],
                'predicted_sql': '',
                'syntax_similarity': 0.0,
                'execution_success': False,
                'execution_metrics': (0.0, 0.0, 0.0),
                'error': None
            }
            
            try:
                # 生成SQL
                predicted_sql = self.generate_sql(item['question'])
                detail['predicted_sql'] = predicted_sql
                
                if predicted_sql.strip():
                    results['successful_generation'] += 1
                    
                    # 计算语法相似度
                    syntax_sim = self.compare_sql_syntax(predicted_sql, item['sql'])
                    detail['syntax_similarity'] = syntax_sim
                    results['syntax_similarity'].append(syntax_sim)
                    
                    # 尝试执行并比较结果（仅对SELECT语句）
                    if predicted_sql.strip().upper().startswith('SELECT') and item['sql'].strip().upper().startswith('SELECT'):
                        try:
                            pred_df = self.execute_sql(predicted_sql)
                            true_df = self.execute_sql(item['sql'])
                            
                            if not pred_df.empty or not true_df.empty:
                                precision, recall, f1 = self.compare_results(pred_df, true_df)
                                detail['execution_success'] = True
                                detail['execution_metrics'] = (precision, recall, f1)
                                results['successful_execution'] += 1
                                results['execution_precision'].append(precision)
                                results['execution_recall'].append(recall)
                                results['execution_f1'].append(f1)
                                
                                print(f"样本 {i} 评估结果: 语法相似度={syntax_sim:.4f}, P={precision:.4f}, R={recall:.4f}, F1={f1:.4f}")
                            else:
                                results['failed_execution'] += 1
                                detail['error'] = "执行结果为空"
                        except Exception as e:
                            results['failed_execution'] += 1
                            detail['error'] = f"执行错误: {str(e)}"
                    else:
                        # 对于非SELECT语句，只评估语法相似度
                        print(f"样本 {i} 评估结果: 语法相似度={syntax_sim:.4f} (非SELECT语句)")
                else:
                    results['failed_generation'] += 1
                    detail['error'] = "SQL生成失败"
                    
            except Exception as e:
                results['failed_generation'] += 1
                detail['error'] = f"生成错误: {str(e)}"
                print(f"样本 {i} 处理失败: {str(e)}")
            
            results['details'].append(detail)
        
        # 计算平均指标
        if results['syntax_similarity']:
            results['avg_syntax_similarity'] = np.mean(results['syntax_similarity'])
        else:
            results['avg_syntax_similarity'] = 0.0
            
        if results['execution_precision']:
            results['avg_execution_precision'] = np.mean(results['execution_precision'])
            results['avg_execution_recall'] = np.mean(results['execution_recall'])
            results['avg_execution_f1'] = np.mean(results['execution_f1'])
        else:
            results['avg_execution_precision'] = 0.0
            results['avg_execution_recall'] = 0.0
            results['avg_execution_f1'] = 0.0
        
        return results
    
    def generate_report(self, results: Dict[str, Any], output_path: str = None):
        """生成评估报告"""
        report = []
        report.append("# Text2SQL 评估报告")
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("\n## 总体评估")
        report.append(f"- 总样本数: {results['total']}")
        report.append(f"- SQL生成成功: {results['successful_generation']}")
        report.append(f"- SQL生成失败: {results['failed_generation']}")
        report.append(f"- SQL执行成功: {results['successful_execution']}")
        report.append(f"- SQL执行失败: {results['failed_execution']}")
        report.append(f"- 平均语法相似度: {results['avg_syntax_similarity']:.4f}")
        report.append(f"- 平均执行精确率: {results['avg_execution_precision']:.4f}")
        report.append(f"- 平均执行召回率: {results['avg_execution_recall']:.4f}")
        report.append(f"- 平均执行F1分数: {results['avg_execution_f1']:.4f}")
        
        # 创建输出目录
        if output_path:
            os.makedirs(output_path, exist_ok=True)
        
        # 绘制图表
        if results['syntax_similarity'] or results['execution_f1']:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            if results['syntax_similarity']:
                axes[0, 0].hist(results['syntax_similarity'], bins=20, alpha=0.7)
                axes[0, 0].set_title('语法相似度分布')
                axes[0, 0].set_xlabel('语法相似度')
                axes[0, 0].set_ylabel('频次')
            
            if results['execution_precision']:
                axes[0, 1].hist(results['execution_precision'], bins=20, alpha=0.7)
                axes[0, 1].set_title('执行精确率分布')
                axes[0, 1].set_xlabel('精确率')
                axes[0, 1].set_ylabel('频次')
            
            if results['execution_recall']:
                axes[1, 0].hist(results['execution_recall'], bins=20, alpha=0.7)
                axes[1, 0].set_title('执行召回率分布')
                axes[1, 0].set_xlabel('召回率')
                axes[1, 0].set_ylabel('频次')
            
            if results['execution_f1']:
                axes[1, 1].hist(results['execution_f1'], bins=20, alpha=0.7)
                axes[1, 1].set_title('执行F1分数分布')
                axes[1, 1].set_xlabel('F1分数')
                axes[1, 1].set_ylabel('频次')
            
            plt.tight_layout()
            
            # 保存图表
            if output_path:
                plt.savefig(f"{output_path}/metrics_distribution.png")
                plt.show()
        
        # 添加详细结果
        report.append("\n## 详细结果")
        for i, detail in enumerate(results['details'], 1):
            report.append(f"\n### 样本 {i}")
            report.append(f"**问题**: {detail['question']}")
            report.append(f"**真实SQL**: {detail['true_sql']}")
            report.append(f"**预测SQL**: {detail['predicted_sql']}")
            report.append(f"**语法相似度**: {detail['syntax_similarity']:.4f}")
            if detail['execution_success']:
                p, r, f1 = detail['execution_metrics']
                report.append(f"**执行结果**: P={p:.4f}, R={r:.4f}, F1={f1:.4f}")
            if detail['error']:
                report.append(f"**错误**: {detail['error']}")
        
        # 保存报告
        report_text = '\n'.join(report)
        if output_path:
            with open(f"{output_path}/evaluation_report.md", 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        return report_text

def main():
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 设置路径
    db_path = "90-文档-Data/sakila/sakila.db"
    eval_data_path = "90-文档-Data/sakila/q2sql_pairs.json"
    output_path = "90-文档-Data/sakila/evaluation"
    
    # 创建评估器
    evaluator = Text2SQLEvaluator(db_path, eval_data_path)
    
    # 执行评估
    results = evaluator.evaluate()
    
    # 生成报告
    report = evaluator.generate_report(results, output_path)
    print("\n" + "="*50)
    print("评估完成！")
    print(f"详细报告已保存到: {output_path}/evaluation_report.md")

if __name__ == "__main__":
    main()