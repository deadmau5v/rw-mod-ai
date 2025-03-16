import os

BASE_URL = "http://XXX.XXXXX.XXX"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Cookie": "xxxxxxx",
    "Referer": f"{BASE_URL}/category/mod",
}

APIS = {
    "get_mods": "/wp-content/themes/LightSNS/module/data/bbs.php",
    "like_post": "/wp-content/themes/LightSNS/module/action/like-post.php",
}


DATABASE = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "XXXXX",
    "password": "XXXXXXX",
    "dbname": "XXXXX"
}

# save paths
PATHS = {
    "mod_detail": "./mod_detail",
    "mods": "./mods",
    "jsons": "./jsons",
    "images": "./images",
}

WEBDAV_UPLOAD_PATH = "/XXXXXXX/mods"
WEBDAV_HOSTNAME = "https://XXXXXXX/dav"
WEBDAV_LOGIN = "XXXXXXX@qq.com"
WEBDAVE_PASSWORD = "XXXXXX"

for path in PATHS.values():
    os.makedirs(path, exist_ok=True)