import json
import time
import redis
import hashlib
from openai import OpenAI

import config

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=config.embedder_api_key,
    base_url=config.embedder_base_url
)

# 初始化 Redis 连接
try:
    r = redis.Redis(**config.redis_params)
    r.ping()
    print("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"Failed to connect to Redis: {e}")
    r = None

# 获取嵌入向量的函数
def get_embedding(text):
    if not r:
        print("Redis connection not available. Skipping cache.")
        return call_openai_embedding(text)

    # 生成缓存键
    cache_key = f"embedding:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"

    # 检查缓存
    try:
        cached_embedding_json = r.get(cache_key)
        if cached_embedding_json:
            return json.loads(cached_embedding_json) # 反序列化
    except redis.exceptions.RedisError as e:
        print(f"Redis error when getting cache: {e}. Proceeding without cache.")

    # 缓存未命中，调用 OpenAI API
    embedding = call_openai_embedding(text)

    # 存入缓存
    if embedding:
        try:
            r.set(cache_key, json.dumps(embedding))
        except redis.exceptions.RedisError as e:
            print(f"Redis error when setting cache: {e}")

    return embedding

def call_openai_embedding(text):
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            response = client.embeddings.create(
                model=config.embedder_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            retry_count += 1
            error_message = f"Error getting embedding: {type(e).__name__}: {str(e)}"
            if retry_count >= max_retries:
                print(f"Failed to get embedding after {retry_count} retries. {error_message}")
                return None 
            print(f"Retrying ({retry_count}/{max_retries}) after error. {error_message}")
            time.sleep(2 ** retry_count)
    return None