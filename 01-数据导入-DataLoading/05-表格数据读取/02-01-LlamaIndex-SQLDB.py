from llama_index.readers.database import DatabaseReader
from sqlalchemy import create_engine, text

# 数据库创建和表结构说明：
# 我们将直接在脚本中创建表和插入数据

db_uri = "sqlite:////root/autodl-tmp/rag-in-action/90-文档-Data/example.db"
engine = create_engine(db_uri)

create_table_sql = """
CREATE TABLE game_scenes (
  id INTEGER PRIMARY KEY,
  scene_name VARCHAR(100) NOT NULL,
  description TEXT,
  difficulty_level INT,
  boss_name VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

insert_data_sql = """
INSERT INTO game_scenes (scene_name, description, difficulty_level, boss_name)
VALUES 
  ('花果山', '悟空的出生地，山清水秀，仙气缭绕', 2, '六耳猕猴'),
  ('水帘洞', '花果山中的洞穴，悟空的老家', 1, NULL),
  ('火焰山', '炙热难耐的火山地带，充满岩浆与烈焰', 4, '牛魔王'),
  ('龙宫', '东海龙王的宫殿，水下奇景', 3, '敖广'),
  ('灵山', '如来佛祖居住的圣地，佛光普照', 5, '如来佛祖');
"""

try:
    with engine.connect() as connection:
        # 检查表是否存在，如果不存在则创建并插入数据
        # SQLite 的 master 表可以用来检查表是否存在
        result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='game_scenes';"))
        if result.fetchone() is None:
            print("game_scenes 表不存在，正在创建并插入数据...")
            connection.execute(text(create_table_sql))
            connection.execute(text(insert_data_sql))
            connection.commit()
            print("game_scenes 表创建并数据插入完成。")
        else:
            print("game_scenes 表已存在，跳过创建和插入数据。")

except Exception as e:
    print(f"数据库初始化时出错: {e}")

reader = DatabaseReader(
    uri=db_uri,
    # 你可能需要在这里指定 engine，取决于 DatabaseReader 的实现和版本
    # engine=engine # 如果需要的话，取消注释这一行
)

query = "SELECT * FROM game_scenes" # 选择所有游戏场景 -> Text-to-SQL
documents = reader.load_data(query=query)

print(f"从数据库加载的文档数量: {len(documents)}")
print(documents)

# 参考文献
# https://docs.llamaindex.ai/en/stable/examples/index_structs/struct_indices/SQLIndexDemo/