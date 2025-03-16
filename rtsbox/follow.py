import requests
from .config import *

def follow_user(uid):
    data = {
        "author_id": uid,
    }
    res = requests.post(f"http://ww.rtsbox.cn/wp-content/themes/LightSNS/module/action/follow.php", headers=HEADERS,
                        data=data)
    print(uid, res.json())
    if not "取消关注" in res.json()["msg"]:
        return
    return follow_user(uid)


if __name__ == '__main__':
    for i in range(1987, 50000):
        follow_user(i)
