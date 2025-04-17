import psycopg2
import logging
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any

import config

# 配置日志
logger = logging.getLogger(__name__)

# 全局数据库连接变量
conn = None

def get_db_connection():
    """获取数据库连接，如果连接不存在或已关闭则尝试重新连接"""
    global conn
    if conn is None or conn.closed != 0:
        try:
            conn = psycopg2.connect(**config.db_params)
            logger.info("Successfully connected to the database.")
        except psycopg2.OperationalError as e:
            logger.error(f"Failed to connect to database: {e}")
            conn = None  # 确保连接失败时 conn 为 None
    return conn

def search_knowledge_base(query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """在 PostgreSQL 数据库中执行向量相似性搜索"""
    connection = get_db_connection()
    if not connection:
        logger.error("Database connection is not available.")
        return []
    if not query_embedding:
        logger.error("Invalid query embedding provided.")
        return []

    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cur:
            # 使用 <=> 操作符执行向量相似性搜索
            sql = """
            SELECT id, content, metadata
            FROM mod_em
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """
            # psycopg2 需要将 list 转为字符串来传递 vector
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            cur.execute(sql, (embedding_str, top_k))
            results = cur.fetchall()
            logger.info(f"Found {len(results)} relevant documents in the knowledge base.")
            return results
    except psycopg2.Error as e:
        logger.error(f"Database query failed: {e}")
        # 尝试关闭可能损坏的连接，以便下次重连
        global conn
        if conn:
            conn.close()
            conn = None
            logger.info("Closed database connection due to error.")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during knowledge base search: {e}")
        return [] 