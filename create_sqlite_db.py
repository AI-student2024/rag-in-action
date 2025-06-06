from sqlalchemy import create_engine, text

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
        # 删除已存在的表（如果需要的话），确保干净的环境
        connection.execute(text("DROP TABLE IF EXISTS game_scenes"))
        print("已删除旧的 game_scenes 表 (如果存在)。")
        
        # 创建表
        connection.execute(text(create_table_sql))
        print("已创建 game_scenes 表。")

        # 插入数据
        connection.execute(text(insert_data_sql))
        connection.commit()
        print("已插入数据到 game_scenes 表。")

except Exception as e:
    print(f"执行数据库操作时出错: {e}") 