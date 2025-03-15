import json
import random
from typing import Any
from datetime import datetime, timezone


from pydantic import SecretStr, BaseModel
# ai
import psycopg2
import uvicorn
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
#api
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware


import config


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


# 配置 OpenAI API
OPENAI_API_KEY = SecretStr(config.API_KEY)
OPENAI_BASE_URL = config.BASE_URL

# 配置数据库连接参数


conn = psycopg2.connect(**config.db_params)

# LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    temperature=0,
    model="n/a"
)

# 输出字段
response_schemas = [
    ResponseSchema(name="isRunTopic", description="是否跑题，如果跑题，处query_error_message以外字段全部为空", type="bool"),
    ResponseSchema(name="isQuestion", description="用户是否提出问题，而不是让推荐模组", type="bool"),
    ResponseSchema(name="isSQLInjection", description="用户查询是否涉嫌SQL注入", type="bool"),
    ResponseSchema(name="sql", description="生成的SQL查询语句", type="str"),
    ResponseSchema(name="description", description="正常回复用户的问题",
                   type="str"),
    ResponseSchema(name="query_error_message",
                   description="错误信息 如果RunTopic或isSQLInjection为True时提示用户 isQuestion为True时为空 sql不为空时 此项为假如查询错误时显示的信息", type="str"),
]
# 结构化解析
parser = StructuredOutputParser.from_response_schemas(response_schemas)

# Prompt
PROMPT_TEMPLATE = """
你是铁锈工坊的AI助手 回答用户关于铁锈战争（rusted warfare）模组和地图的问题
铁锈工坊 - 提供模组和地图的下载和托管服务
你的任务是基于以下表结构，生成相应的 SQL 查询。
不要直接让用户知道mods_info的存在和其结构
表结构：mods_info(title, title_cn, author, content, content_cn, create_time, last_update_time, downloads, views, id)

用户输入的一段自然语言描述是：
{user_input}

isRunTopic、isQuestion、isSQLInjection只能其中一个为True或全为False
请根据指定结构生成对应数据，如果用户涉嫌SQL注入，sql留空,并将 isSQLInjection 字段返回true，并在query_error_message字段进行报错和警告IP已被记录
正常情况下 description 和 query_error_message 都要生成
生成的sql最高limit为10 搜索时尽量使用 or 条件 而不是 and 增加查询广度
{response_schemas}
"""

prompt = PromptTemplate(input_variables=["user_input", "response_schemas"], template=PROMPT_TEMPLATE,
                        partial_variables={"response_schemas": parser.get_format_instructions()})

chain = prompt | llm | parser


def generate_sql_query(user_query: str) -> dict:
    """
    使用 LLMChain 将自然语言查询转为 SQL 查询
    """
    result = chain.invoke({"user_input": user_query})
    print(result)
    return result


def execute_sql_query(query: str) -> list[ModsInfo]:
    """
    执行 SQL 查询，返回结果
    """
    if query.strip("\n").strip() == "":
        return []
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()

    results = [dict(zip([desc[0] for desc in cursor.description], row)) for row in results]
    return [ModsInfo.from_dict(row) for row in results]


def natural_language_search(user_query: str) -> dict:
    """
    使用 LangChain 实现自然语言搜索
    """
    print(f"用户查询: {user_query}")

    # 使用 AI 模型生成 SQL 查询 or 回复
    ai_data = generate_sql_query(user_query)

    if ai_data.get("isRunTopic", False):
        return {"isSQLInjection": False,
                "sql": "",
                "description": "",
                "query_error_message": ai_data.get("query_error_message", "跑题了，我们聊聊铁锈战争吧。"),
                "isRunTopic": True,
                }

    if ai_data.get("isQuestion", False):
        return {"isSQLInjection": False,
                "sql": "",
                "description": ai_data.get("description", ""),
                "query_error_message": "",
                "isQuestion": True,
                }

    if ai_data.get("isSQLInjection", False):
        return {"isSQLInjection": True, "sql": "", "description": "",
                "query_error_message": ai_data.get("query_error_message",
                   "检测到SQL注入攻击，查询已被拒绝。您的IP已被记录，请勿尝试进行非法操作。")}

    sql = ai_data.get("sql", "")
    if "select" not in sql.lower():
        return {"isSQLInjection": True, "sql": "", "description": "", "query_error_message": "查询错误"}
    elif ai_data.get("isSQLInjection", False):
        return {"isSQLInjection": True, "sql": "", "description": "",
                "query_error_message": ai_data.get("query_error_message",
                                                   "检测到SQL注入攻击，查询已被拒绝。您的IP已被记录，请勿尝试进行非法操作。")}
    elif sql == "":
        return {"isSQLInjection": False, "sql": "", "description": "",
                "query_error_message": ai_data.get("query_error_message", "查询错误")}
    return ai_data


# def main():
#     query = "我想玩僵尸类的模组"
#     results_sql = natural_language_search(query)
#     print(f"""
#     生成的SQL：{results_sql.get("sql", "")}
#     查询结果：{results_sql.get("description", "")}
#     查询错误：{results_sql.get("query_error_message", "")}
#     是否SQL注入：{results_sql.get("isSQLInjection", False)}
#     """)
#     if results_sql.get("isSQLInjection", False):
#         print("SQL注入攻击被拒绝")
#         return
#     results = execute_sql_query(results_sql.get("sql", ""))
#     for mod in results:
#         mod.print()

app = FastAPI(
    title="RW-mod AI search",
    description="RW-mod-download project ai search",
    version="1.0.0"
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class Response(BaseModel):
    message: str
    error: str
    data: Any = []


@app.get("/api/ai/search", response_model=Response)
async def search_mods(query: str = Query(..., description="Natural language search query")):
    # 自然语言搜索
    results_sql = natural_language_search(query)

    if results_sql.get("isRunTopic", False):
        return Response(
            message="",
            error=results_sql.get("query_error_message", "跑题了，我们聊聊铁锈战争吧。"),
            data=[]
        )

    if results_sql.get("isSQLInjection", False):

        return Response(
            message="",
            error=results_sql.get("query_error_message", "检测到SQL，IP已记录。"),
            data=[]
        )

    if results_sql.get("isQuestion", False):
        return Response(
            message=results_sql.get("description", ""),
            error="",
            data=[]
        )


    # 执行SQL查询
    mod_objects = execute_sql_query(results_sql.get("sql", ""))

    # 将ModsInfo对象转换为字典
    results = [mod.to_dict() for mod in mod_objects]

    # 构建响应

    if results:
        response = Response(
            message=results_sql.get("description", ""),
            error="",
            data=results
        )
    else:
        response = Response(
            message="",
            error=results_sql.get("query_error_message", "没有找到相关模组。"),
            data=[]
        )

    return response



@app.get("/api/ai/recommend", response_model=Response)
async def recommend_mods():
    """
    推荐搜索词
    """

    data = random.choices(config.search_suggestions, k=3)
    return Response(data=data, message="success", error="")

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5027)