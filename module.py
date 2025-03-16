import json
import os.path
from datetime import datetime, timezone
import re


class ModsInfo:
    def __init__(self,
                 steam_id=None,
                 img=None,
                 title=None,
                 title_cn=None,
                 author=None,
                 author_url=None,
                 content=None,
                 content_cn=None,
                 create_time=None,
                 last_update_time=None,
                 downloads=0,
                 views=0,
                 rate=0,
                 id=None,
                 origin_id=None,
                 platform=None):
        self.steam_id = steam_id
        self.img = img
        self.title = title
        self.title_cn = title_cn
        self.author = author
        self.author_url = author_url
        self.content = content
        self.content_cn = content_cn
        self.create_time = create_time if create_time else datetime.now(timezone.utc)
        self.last_update_time = last_update_time
        self.downloads = downloads
        self.views = views
        self.rate = rate
        self.id = id
        self.origin_id = origin_id
        self.platform = platform

    @staticmethod
    def from_dict(data_dict):
        return ModsInfo(
            steam_id=data_dict.get('steam_id'),
            img=data_dict.get('img'),
            title=data_dict.get('title'),
            title_cn=data_dict.get('title_cn'),
            author=data_dict.get('author'),
            author_url=data_dict.get('author_url'),
            content=data_dict.get('content'),
            content_cn=data_dict.get('content_cn'),
            create_time=data_dict.get('create_time'),
            last_update_time=data_dict.get('last_update_time'),
            downloads=data_dict.get('downloads', 0),
            views=data_dict.get('views', 0),
            rate=data_dict.get('rate', 0),
            id=data_dict.get('id'),
            origin_id=data_dict.get('origin_id'),
            platform=data_dict.get('platform')
        )

    def to_dict(self):
        """
        将对象转换为字典
        """
        return {
            'steam_id': self.steam_id,
            'img': self.img,
            'title': self.title,
            'title_cn': self.title_cn,
            'author': self.author,
            'author_url': self.author_url,
            'content': self.content,
            'content_cn': self.content_cn,
            'create_time': self.create_time.isoformat(),
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None,
            'downloads': self.downloads,
            'views': self.views,
            'rate': self.rate,
            'id': self.id,
            'origin_id': self.origin_id,
            'platform': self.platform
        }

    def __repr__(self):
        return f"<ModsInfo(id={self.id}, title='{self.title}', author='{self.author}')>"

    __str__ = __repr__

    def print(self):
        print(json.dumps(self.to_dict(), indent=4, ensure_ascii=False))

    def to_meta_data(self):
        return {
            'id': self.id,
            'title': self.title,
            'title_cn': self.title_cn,
            'author': self.author,
            'author_url': self.author_url,
            'create_time': self.create_time.isoformat(),
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None,
            'downloads': self.downloads,
            'views': self.views,
            'rate': self.rate,
        }

    def to_markdown(self, path: str) -> None:
        if not os.path.exists(path):
            os.makedirs(path)
        path = os.path.abspath(path)
        # Clean filename path
        filename = f"{self.title_cn or self.title}"
        chars = [
            " ", "-", "*", "_", "[", "]", "(", ")", "#", "=", "+", "-", ".", ":", "!", "~", "`", "\\", "/", "|", "<",
            ">", "^", "$", "%", "&", "{", "！", '"', '\n', '\t', '\r']
        for char in chars:
            filename = filename.replace(char, "")
        filename = f"[{self.id}]{filename}.md"
        file_path = os.path.join(path, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"""
    # Metadata
    - **ID:** {self.id}
    - **English Title:** {self.title}
    - **Chinese Title:** {self.title_cn}
    - **Author:** {self.author}
    - **Author URL:** {self.author_url}
    - **Create Time:** {self.create_time.strftime("%Y-%m-%d %H:%M:%S")}
    - **Last Update Time:** {self.last_update_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_update_time else "N/A"}
    - **Downloads:** {self.downloads}
    - **Views:** {self.views}
    - **Rate:** {self.rate}
    - **Platform:** {self.platform}
    # English Content
    ---
    ## {self.title}
    {self.content}
    ---
    # Chinese Content
    ---
    ## {self.title_cn}
    {self.content_cn}
    ---
    """)

def split_markdown(text):
    sections = re.split(r'(^#+\s.*$)', text, flags=re.MULTILINE)
    sections = [section.strip() for section in sections if section.strip()]

    all_parts = []
    for section in sections:
        if section.startswith('#'):
            all_parts.append(section)
        else:
            paragraphs = section.split('\n\n')
            all_parts.extend(paragraphs)

    return all_parts
