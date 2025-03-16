import psycopg2
from .config import DATABASE

# 建立数据库连接
try:
    conn = psycopg2.connect(**DATABASE)
    conn.autocommit = True
    print("成功连接到数据库")
except Exception as e:
    print(f"连接数据库时出错: {e}")


def get_cursor():
    return conn.cursor()


def insert_mod_data(
        platform: str,
        origin_id: str,
        img: str,
        title: str,
        title_cn: str,
        author: str,
        author_url: str,
        content: str,
        content_cn: str,
        last_update_time: str,
        downloads: int,
        views: int,
        rate: int
):
    cursor = get_cursor()
    cursor.execute("""
    insert into mods_info (platform, origin_id, img, title, title_cn, author, author_url, content, content_cn, last_update_time, downloads, views, rate)
    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        platform, origin_id, img, title, title_cn, author, author_url, content, content_cn, last_update_time,
        downloads, views, rate
    ))
    cursor.execute("""
    insert into mod_tags (tag, mod_id) values ('%s', (select id from mods_info where origin_id = %s))
    """, ("铁锈盒子", origin_id))
    cursor.close()
