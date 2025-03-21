import psycopg2
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

import config
from module import ModsInfo

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
    model=config.MODULE
)


def generate_sql_query(user_query: str) -> dict:
    """
    使用 LLMChain 将自然语言查询转为 SQL 查询
    """

    # 输出字段
    response_schemas = [
        ResponseSchema(name="isRunTopic", description="是否跑题，如果跑题，处query_error_message以外字段全部为空",
                       type="bool"),
        ResponseSchema(name="isQuestion",
                       description="用户是否提出问题，而不是让推荐模组", type="bool"),
        ResponseSchema(name="isSQLInjection",
                       description="用户查询是否涉嫌SQL注入", type="bool"),
        ResponseSchema(name="sql", description="生成的SQL查询语句", type="str"),
        ResponseSchema(name="description", description="正常回复用户的问题",
                       type="str"),
        ResponseSchema(name="query_error_message",
                       description="错误信息 如果RunTopic或isSQLInjection为True时提示用户 isQuestion为True时为空 sql不为空时 此项为假如查询错误时显示的信息",
                       type="str"),
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

    results = [dict(zip([desc[0] for desc in cursor.description], row))
               for row in results]
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


def get_content_tags(content: str) -> list[str]:
    """
    更具mod内容打标签
    """
    response_schemas = [
        ResponseSchema(name="tags", description="标签", type="list[str]"),
    ]

    parser = StructuredOutputParser.from_response_schemas(response_schemas)
    template = """
    分析以下文本:
    {content}
    
    请更具用户提供的内容生成标签，不要重复 每个词在2-4字以内，名词，中文 例如["机甲", "地图", "僵尸", "单位", "PVP", "8P"...]
      - 最高生成4个标签
    {format_instructions}
    """

    prompt = PromptTemplate(
        template=template,
        input_variables=["content"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()}
    )
    chain = prompt | llm | parser

    result = chain.invoke({"content": content})

    return result
