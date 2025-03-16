import psycopg2
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

import config


class Text:
    def __init__(self, chinese="", english="", chinese_markdown="", english_markdown=""):
        self.chinese = chinese
        self.english = english
        self.chinese_markdown = chinese_markdown
        self.english_markdown = english_markdown

    def print(self):
        if self.chinese or self.english:
            print(f"{'=' * 20}{'Chinese':^20}{'=' * 20}")
            print(self.chinese)
            print(f"{'=' * 20}{'English':^20}{'=' * 20}")
            print(self.english)
        if self.chinese_markdown or self.english_markdown:
            print(f"{'=' * 20}{'Chinese Markdown':^20}{'=' * 20}")
            print(self.chinese_markdown)
            print(f"{'=' * 20}{'English Markdown':^20}{'=' * 20}")
            print(self.english_markdown)

    def to_params(self):
        """
        转为提示词
        """
        result = ""
        if self.chinese:
            result += f"中文：{self.chinese}\n"
        if self.english:
            result += f"英文：{self.english}\n"
        if self.chinese_markdown:
            result += f"中文 markdown：{self.chinese_markdown}\n"
        if self.english_markdown:
            result += f"英文 markdown：{self.english_markdown}\n"
        return result


def translate(text: Text):
    response_schemas = [
        ResponseSchema(name="chinese", description="如果没有提供中文，则根据英文翻译出中文，否则使用原文中文"),
        ResponseSchema(name="english", description="如果没有提供英文，则根据中文翻译出英文，否则使用原文英文"),
    ]
    parser = StructuredOutputParser.from_response_schemas(response_schemas)
    template = """
    分析以下文本:
    {text}
    
    根据用户提供的信息 翻译出chinese和english内容 如果其中一个有则使用原文
    
    {format_instructions}
    """
    prompt = PromptTemplate(
        template=template,
        input_variables=["text"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    llm = ChatOpenAI(base_url=config.BASE_URL, api_key=SecretStr(config.API_KEY), model=config.MODULE, temperature=0)
    chain = prompt | llm | parser
    result = chain.invoke({"text": text.to_params()})

    text.chinese = result.get("chinese")
    text.english = result.get("english")

    return text


def translate_Markdown(text: Text):
    response_schemas = [
        ResponseSchema(name="chinese", description="如果没有提供中文，则根据英文翻译出中文，否则使用原文中文"),
        ResponseSchema(name="english", description="如果没有提供英文，则根据中文翻译出英文，否则使用原文英文"),
        ResponseSchema(name="chinese_markdown", description="中文翻译后的Markdown格式"),
        ResponseSchema(name="english_markdown", description="英文翻译后的Markdown格式"),
    ]

    parser = StructuredOutputParser.from_response_schemas(response_schemas)

    template = """
    分析以下文本:
    {text}
    
    根据用户提供的信息 翻译出chinese和english内容 如果其中一个有则使用原文
    再进行markdown格式化和美化
    并且输出chinese_markdown和english_markdown的Markdown格式
    
    {format_instructions}
    """

    prompt = PromptTemplate(
        template=template,
        input_variables=["text"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    llm = ChatOpenAI(base_url=config.BASE_URL, api_key=SecretStr(config.API_KEY), model=config.MODULE, temperature=0)
    chain = prompt | llm | parser

    result = chain.invoke({"text": text.to_params()})

    text.chinese = result.get("chinese")
    text.english = result.get("english")
    text.chinese_markdown = result.get("chinese_markdown")
    text.english_markdown = result.get("english_markdown")

    return text


def connect_db():
    conn = psycopg2.connect(**config.db_params)
    return conn

def get_mods_to_process() -> list[tuple[int, Text, Text]]:
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""SELECT id, title, title_cn, content, content_cn FROM mods_info""")
    results = cursor.fetchall()

    mods = []
    for row in results:
        title_text = Text()
        title_text.english = row[1]
        title_text.chinese = row[2]

        content_text = Text()
        content_text.english = row[3]
        content_text.chinese = row[4]
        mods.append((
            int(row[0]),
            title_text,
            content_text,
        ))
    cursor.close()
    return mods


def update_mod(id, title, title_cn, content, content_cn):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE mods_info SET title = %s, title_cn = %s, content = %s, content_cn = %s WHERE id=%s""",
        (title, title_cn, content, content_cn, id)

    )
    cursor.close()
    conn.commit()
    print(id, "update success")


def translate_from_html(html: str):
    response_schemas = [
        ResponseSchema(name="markdown_english", description="格式化后的英语markdown介绍", type="string"),
        ResponseSchema(name="markdown_chinese", description="格式化后的中文markdown介绍", type="string"),
        ResponseSchema(name="imgs", description="引用的img地址列表", type="list[str]"),
    ]
    
    parser = StructuredOutputParser.from_response_schemas(response_schemas)
    template = """
    将以上模组介绍信息进行markdown格式化:
      - 不保留格式化后的img内容
      - 将img地址存到单独字段
    {html}
    
    根据用户提供的html原始信息 翻译出markdown格式的英文和中文介绍
    {format_instructions}
    """
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["html"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    llm = ChatOpenAI(base_url=config.BASE_URL, api_key=SecretStr(config.API_KEY), model=config.MODULE, temperature=0)
    chain = prompt | llm | parser
    result = chain.invoke({"html": html})
    return {
        "content": result.get("markdown_english"),
        "content_cn": result.get("markdown_chinese"),
        "imgs": result.get("imgs")
    }
    

if __name__ == '__main__':
    # 批处理
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=10) as thread_loop:
        for id, title_text, content_text in get_mods_to_process():
            def target(id, title_text, content_text):
                translate(title_text)
                translate_Markdown(content_text)
                update_mod(id, title_text.english, title_text.chinese, content_text.english, content_text.chinese)


            thread_loop.submit(target, id, title_text, content_text)
