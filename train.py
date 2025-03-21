import os
import json
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import PromptTemplate
from concurrent.futures import ThreadPoolExecutor
import config
import queue
import threading


class Role:
    """
    角色类
    """

    def __init__(self, role: str, content: str):
        self.role = role  # system, user, assistant
        self.content = content

    def __str__(self):
        return f"{self.role}: {self.content}"


class Message:
    """
    消息类
    """

    def __init__(self, roles: list[Role]):
        self.system_message = roles[0]
        self.assistant_message = roles[1]
        self.user_message = roles[2]

    def to_json(self):
        """
        转换为json

        Returns:
            dict: 消息
        """
        return {
            "messages": [
                {"role": self.system_message.role,
                    "content": self.system_message.content},
                {"role": self.user_message.role,
                    "content": self.user_message.content},
                {"role": self.assistant_message.role,
                    "content": self.assistant_message.content}
            ]
        }

    def save(self, path: str):
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(self.to_json(), ensure_ascii=False) + "\n")


nil, err = "", ""

train_data_dir = "data/ini"
train_data_file = os.listdir(train_data_dir)
save_jsonl_path = "data/train.jsonl"


def read_ini_content(file_name):
    """
    读取ini文件内容

    Args:
        file_name (str): 文件名

    Returns:
        str: 文件内容
    """
    file_path = os.path.join(train_data_dir, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        return content


def save_jsonl(path: str, messages: list[Message]) -> str:
    """
    保存训练数据到jsonl文件

    Args:
        path (str): 保存路径

    Returns:
        str: 错误信息
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            for message in messages:
                f.write(json.dumps(message.to_json(), ensure_ascii=False) + "\n")
    except Exception as e:
        err = str(e)
        return err
    return nil


def connect_llm() -> tuple[ChatOpenAI, str]:
    """
    连接LLM
    """
    TEST_CONTENT = "hello return me a 'hello world'"
    OPENAI_API_KEY = SecretStr(config.API_KEY)
    OPENAI_BASE_URL = config.BASE_URL

    # LLM
    try:
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            temperature=1,
            model=config.MODULE
        )
    except Exception as e:
        err = str(e)
        return nil, err

    # Test LLM
    try:
        llm.invoke(TEST_CONTENT)
    except Exception as e:
        err = str(e)
        return nil, err

    return llm, nil


def load_mod_ini() -> tuple[list[Message], str]:
    """
    读取mod.ini文件内容

    Returns:
        tuple[list[Message], str]: 消息列表, 错误信息
    """
    messages: list[Message] = []
    # 读取训练数据
    total_files = len(train_data_file)
    for i, file_name in enumerate(train_data_file):
        progress = (i + 1) / total_files * 100
        print(f"\r处理进度: [{i+1}/{total_files}] {progress:.2f}%", end="")

        content = read_ini_content(file_name)
        message = Message(content)

        system_message = Role(
            role="system",
            content="你是一个铁锈战争模组编写专家，帮助用户编写模组。"
        )

        assistant_message = Role(
            role="assistant",
            content=content
        )

        # 通过结果生成用户信息 实现蒸馏微调
        user_message = Role(
            role="user",
            content=nil
        )

        message.system_message = system_message
        message.assistant_message = assistant_message
        message.user_message = user_message

        try:
            messages.append(message)
        except Exception as e:
            err = str(e)
            print("\n", err)
            return nil, err

    print()
    return messages, nil


def clean_jsonl(messages: list[Message]) -> tuple[list[Message], str]:
    """
    清理jsonl文件

    Args:
        messages (list[Message]): 消息列表

    Returns:
        tuple[list[Message], str]: 消息列表, 错误信息
    """
    for message in messages:
        if 2000 > len(message.user_message.content) > 400:
            messages.remove(message)

    return messages, nil


def main():

    messages, err = load_mod_ini()
    if err != nil:
        print(err)
        return

    save_jsonl(save_jsonl_path + ".bak", messages)

    # 连接LLM
    llm, err = connect_llm()
    if err != nil:
        print(err)
        return
    print("已连接到LLM")

    response_schema = [
        ResponseSchema(name="user_message",
                       description="用户输入了什么样的提示词，AI生成了这样的内容，反推出来"),
    ]

    parser = StructuredOutputParser.from_response_schemas(response_schema)

    prompt = PromptTemplate(
        template=open("train.txt", "r",
                      encoding="utf-8").read(),
        input_variables=[
            "ini_content", "format_instructions"],
        partial_variables={
            "format_instructions": parser.get_format_instructions(),
        }
    )

    def generate_message(message: Message):

        chain = prompt | llm | parser
        result = chain.invoke({"ini_content": message})
        result = result["user_message"].replace(
            "\n", " ")

        print(result)

        message.user_message.content = result
        message.save(save_jsonl_path)

    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(generate_message, messages)


if __name__ == "__main__":
    main()
