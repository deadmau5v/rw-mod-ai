"""
下载数据库文件为Markdown 用于向量化 优化搜索
"""
import psycopg2

import config
from module import ModsInfo

conn = psycopg2.connect(**config.db_params)
conn.autocommit = True
def get_cursor():
    return conn.cursor()

def get_mods_info() -> list[ModsInfo]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mods_info")
    results = cursor.fetchall()
    mods = []
    for row in results:
        mod = ModsInfo.from_dict(dict(zip([desc[0] for desc in cursor.description], row)))
        mods.append(mod)

    return mods
