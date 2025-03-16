import threading
import json
import os
import time
from datetime import datetime

import bs4
import pytz
import requests
import colorama
from colorama import Fore, Style
from webdav3.client import Client

from agent import get_content_tags
from db import get_cursor
from translate import Text, translate, translate_from_html
from rtsbox import config

# 初始化colorama
colorama.init()


def log_info(message):
    """打印信息日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {timestamp} - {message}")


def log_success(message):
    """打印成功日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {timestamp} - {message}")


def log_warning(message):
    """打印警告日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {timestamp} - {message}")


def log_error(message):
    """打印错误日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {timestamp} - {message}")


class Mod:
    def __init__(self):
        self.origin_id = None
        self.platform = "new-rtsbox"
        self.img = None
        self.title = None

        self.author = None
        self.author_url = None
        self.create_time = None
        self.views = 0

        # need to get from detail page
        self.content = None
        self.content_cn = None

        # calculated
        self.title_cn = None
        self.downloads = 0  # 默认值
        self.rate = 0  # 需另外获取
        self.last_update_time = None  # 需另外获取

        self.tags = []
        self.imgs = []

    def json(self):
        return {
            "origin_id": self.origin_id,
            "img": self.img,
            "title": self.title,
            "title_cn": self.title,
            "author": self.author,
            "author_url": self.author_url,
            "content": self.content,
            "content_cn": self.content_cn,
            "create_time": str(self.create_time),
            "last_update_time": str(self.create_time),
            "downloads": int(self.views / 100),
            "views": self.views,
            "rate": 3,
            "tags": self.tags,
            "imgs": self.imgs,
        }

    def save(self):
        os.makedirs(config.PATHS["jsons"], exist_ok=True)
        with open(
            f"{config.PATHS["jsons"]}/{self.origin_id}.json", "w", encoding="utf-8"
        ) as f:
            f.write(json.dumps(self.json(), ensure_ascii=False, indent=4))
        log_success(f"已保存 Mod: {self.title} (ID: {self.origin_id})")

    def is_exist(self):
        return os.path.exists(f"{config.PATHS["jsons"]}/{self.origin_id}.json")

    def insert_db(self):
        curosr = get_cursor()
        curosr.execute(
            "INSERT INTO mods (origin_id, platform, img, title, title_cn, author, author_url, content, content_cn, create_time, last_update_time, downloads, views, rate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                self.origin_id,
                self.platform,
                self.img,
                self.title,
                self.title_cn,
                self.author,
                self.author_url,
                self.content,
                self.content_cn,
                self.create_time,
                self.last_update_time,
                self.downloads,
                self.views,
                self.rate,
            ),
        )
        # insert tags
        for tag in list(set(self.tags)):
            curosr.execute(
                "INSERT INTO mod_tags (tag, mod_id) FROM (%s, (select id from mods_info where origin_id = %s))",
                (tag, self.origin_id),
            )
        # insert imgs
        for img in list(set(self.imgs)):
            curosr.execute(
                "INSERT INTO mod_imgs (img, mod_id) FROM (%s, (select id from mods_info where origin_id = %s))",
                (img, self.origin_id),
            )
        curosr.close()

    def __str__(self):
        return json.dumps(self.json(), ensure_ascii=False, indent=4)

    def __repr__(self):
        return self.__str__()

# WebDAV服务器配置
options = {
    'webdav_hostname': config.WEBDAV_HOSTNAME,
    'webdav_login': config.WEBDAV_LOGIN,
    'webdav_password': config.WEBDAVE_PASSWORD,
}

webdav = Client(options)
webdav.verify
def upload_to_webdav(local_path, webdav_path):
    webdav.upload_sync(remote_path=webdav_path, local_path=local_path)


def save_img(img_url: str, save_path: str):
    def target():
        try:
            img_content = requests.get(
                img_url,
                headers={
                    "User-Agent": config.HEADERS["User-Agent"],
                    "Referer": config.BASE_URL,
                },
            )
            if img_content.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(img_content.content)
        except Exception as img_err:
            log_error(f"下载图片时出错: {img_err}")

    t = threading.Thread(target=target)
    t.start()


def soup_mod_info(element: bs4.Tag):
    """从单个mod元素中提取信息"""
    mod = Mod()

    mod.origin_id = int(
        element.find("a").attrs.get("href", "").split("/")[-1].replace(".html", "")
    )

    rwmod_path = f"{config.PATHS["mods"]}/b_{mod.origin_id}.rwmod"
    if os.path.exists(rwmod_path):
        log_warning(f"Mod {mod.origin_id} {mod.title} 已存在，跳过")
        return

    mod.img = (
        element.find("div", attrs={"class": "bg"})
        .attrs["style"]
        .split("(")[1]
        .split(")")[0]
    )
    mod.title_cn = element.find("h2").text.strip("\n").strip()

    response = requests.get(
        f"{config.BASE_URL}/{mod.origin_id}.html", headers=config.HEADERS
    )
    if response.status_code == 200:
        log_success(f"获取Mod {mod.origin_id} {mod.title_cn} 成功, 开始解析")
        soup = bs4.BeautifulSoup(response.content, "lxml")

        # 作者
        log_info(f"获取Mod {mod.origin_id} {mod.title_cn} 作者信息")
        mod.author = (
            soup.find("div", "left")
            .find("div", attrs={"class": "avatar"})
            .find("a")
            .attrs.get("href", "")
        )
        log_info(f"获取Mod {mod.origin_id} {mod.title_cn} 作者URL")
        mod.author_url = (
            soup.find("div", "left")
            .find("div", attrs={"class": "name"})
            .find("a")
            .text.strip("\n")
            .strip()
        )
        log_info(f"获取Mod {mod.origin_id} {mod.title_cn} content")
        content = soup.find("div", attrs={"class": "jinsom-bbs-single-content"})
        log_success(f"获取Mod {mod.origin_id} {mod.title_cn} 解析完成")

        translate_content = translate_from_html(content.prettify())

        if "```markdown" in translate_content["content"]:
            mod.content = (
                translate_content["content"].split("```markdown")[1].split("```")[0]
            )
        else:
            mod.content = translate_content["content"]
        if "```" in translate_content["content_cn"]:
            mod.content_cn = (
                translate_content["content_cn"].split("```")[1].split("```")[0]
            )
        else:
            mod.content_cn = translate_content["content_cn"]

        log_info(f" Mod {mod.origin_id} {mod.title_cn} 翻译中")
        resoult = translate(text=Text(chinese=mod.title_cn, english=mod.title))

        mod.title_cn = resoult.chinese
        mod.title = resoult.english

        mod.tags = get_content_tags(
            f"""
                                - Title {mod.title} {mod.title_cn}
                                - Author {mod.author} 
                                # Content 
                                {mod.content}
                                {mod.content_cn}
                                """
        )
        mod.imgs = translate_content["imgs"]

        # 后续更具下载量和浏览量计算
        mod.rate = 3

        mod.create_time = datetime.now(pytz.timezone("Asia/Shanghai"))

        log_info(f"保存Mod {mod.origin_id} 详情")
        with open(
            f"{config.PATHS["mod_detail"]}/{mod.origin_id}.html", "w", encoding="utf-8"
        ) as f:
            f.write(soup.prettify())

        log_info(f"下载Mod {mod.origin_id} ")
        download_button = soup.find("div", {"class": "jinsom-file-download"})
        download_url = download_button.find("m")["data"]
        log_info(f"{mod.origin_id} 下载地址：{download_url}")

        log_info(f"下载Mod {mod.origin_id}")
        response = requests.get(download_url, headers=config.HEADERS)
        with open(rwmod_path, "wb") as f:
            f.write(response.content)
        log_success(f"下载成功 {mod.origin_id} ")

        upload_to_webdav(
            local_path=rwmod_path,
            webdav_path=f"{config.WEBDAV_UPLOAD_PATH}/b_{mod.origin_id}.rwmod",
        )

        # 下载img
        for img in list(set(mod.imgs)):
            save_img(
                img, f"{config.PATHS["imgs"]}/{mod.origin_id}_{img.split('/')[-1]}"
            )
            upload_to_webdav(
                local_path=f"{config.PATHS['imgs']}/{mod.origin_id}_{img.split('/')[-1]}",
                webdav_path=f"{config.WEBDAV_UPLOAD_PATH}/{mod.origin_id}_{img.split('/')[-1]}",
            )
        mod.imgs = [
            f"{config.CDN_URL}/{config.WEBDAV_UPLOAD_PATH}/{mod.origin_id}_{img.split('/')[-1]}"
            for img in mod.imgs
        ]
        
        save_img(mod.img)
        upload_to_webdav(
            local_path=f"{config.PATHS['imgs']}/{mod.origin_id}_{mod.img.split('/')[-1]}",
            webdav_path=f"{config.WEBDAV_UPLOAD_PATH}/{mod.origin_id}_{mod.img.split('/')[-1]}",
        )
        mod.img = f"{config.CDN_URL}/{config.WEBDAV_UPLOAD_PATH}/{mod.origin_id}_{mod.img.split('/')[-1]}"

    else:
        log_error(f"处理Mod时出错: {response.request.url}")
        log_error(f"获取Mod {mod.origin_id} {mod.title} 失败")
        log_error(f"{response.status_code} {response.text}")

    # 有效mod
    if mod.origin_id and mod.title and mod.author_url:
        if not mod.is_exist():
            mod.save()
        return mod
    else:
        log_warning("无法从元素中提取足够的MOD信息")
        return None


def like_mod(mod: Mod, retry=3):
    if retry == 0:
        log_error(f"点赞Mod {mod.origin_id} {mod.title} 失败")
    data = {
        "post_id": mod.origin_id,
    }
    res = requests.post(
        f"{config.BASE_URL}{config.APIS["like_post"]}",
        headers=config.HEADERS,
        data=data,
    )
    if res.json()["code"] == 2:
        return like_mod(mod, retry - 1)


def soup_mods(soup: bs4.BeautifulSoup):
    mod_elements = soup.find_all("li")
    log_success(f"找到 {len(mod_elements)} 个Mod")

    mods = []
    for element in mod_elements:
        try:
            mod = soup_mod_info(element)
            if mod:
                mods.append(mod)
        except Exception as e:
            log_error(f"解析Mod信息时出错: {e}")

    return mods


def get_mods(page=1):
    if page >= 3:
        return
    log_info(f"正在获取第 {page} 页的Mod列表")
    data = {
        "page": page,
        "bbs_id": 4,
        "type": "new",
        "topic": "",
    }

    url = f"{config.BASE_URL}/{config.APIS['get_mods']}"
    try:
        response = requests.post(url, data=data, headers=config.HEADERS)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, "lxml")

        # 解析 mods
        mods = soup_mods(soup)
        log_success(f"第 {page} 页成功获取 {len(mods)} 个Mod")

        if len(mods) == 0:
            log_warning(f"第 {page} 页未找到任何Mod，停止获取")
            return

    except requests.exceptions.RequestException as e:
        log_error(f"请求出错: {e}")

    except Exception as e:
        log_error(f"获取Mod列表出错: {e}")

    get_mods(page + 1)


if __name__ == "__main__":
    log_info("启动Mod信息采集程序")

    while True:
        try:
            get_mods()
            log_success("本次采集完成")
        except Exception as e:
            log_error(f"采集过程中发生错误: {e}")

        log_info("等待10分钟后进行下次采集...")
        time.sleep(60 * 10)
