import json

# 数据库配置
# postgresql
db_params = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "username",
    "password": "PA$$0WRD",
    "database": "dbname"
}

# OpenAI
API_KEY = "sk-xxxxxxxxxxxxxxxxxxx"
BASE_URL = "https://api.openai.com/api/v1"
MODULE = "GPT-4o"
# 推荐问题 固定随机返回三个
with open("./data/search_recommends.json", "r", encoding='utf-8') as f:
    search_suggestions = json.loads(f.read())

# zilliz Endpoint
zilliz_endpoint = ''
zilliz_token = ''