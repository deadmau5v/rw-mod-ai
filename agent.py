import json
from psycopg2.extras import RealDictCursor
import logging

from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from agno.workflow.workflow import Workflow
from agno.workflow import RunResponse, RunEvent
from typing import Iterator, List, Dict, Any

import config
import embedding

from db.database import search_knowledge_base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = OpenAILike(
    api_key=config.API_KEY,
    base_url=config.BASE_URL,
    temperature=0.7,
    id=config.MODULE
)

class AISearch(Workflow):
    """
    一个AI搜索工作流，包含以下步骤：
    1. （未来实现）通过护栏Agent判断内容是否违规、越界。
    2. 从知识库（PostgreSQL + pgvector）检索相关内容。
    3. 通过问答Agent结合用户问题和知识库内容给出最终结果。
    """
    description: str = "一个AI搜索工作流，用于在 Mod 知识库中进行搜索并回答用户问题。"

    # 问答Agent
    answering_agent: Agent = Agent(
        model=model,
        description="你是铁锈工坊的AI搜素机器人，你会帮助用户回答（rusted warfare）领域问题或推荐模组。",
        instructions="""
        <about>
        铁锈工坊是一个专注于 Rusted Warfare (铁锈战争) 游戏模组的下载平台。 我们的目标是为玩家提供无广告、纯粹的模组下载体验。
        无广告 免登录 速度快 2000+模组 
        开源项目 铁锈工坊是一个开源项目，完善后会将前后端代码发布到Github。
        社区驱动 重视玩家反馈，欢迎玩家投稿，不断改进平台以提供更好的体验。
        高速下载 为模组提供托管、更新、高速下载服务。
        你是铁锈工坊的智能搜素机器人
        </about>
        
        <task>
        只回答用户关于铁锈战争（rusted warfare）相关问题，和内容推荐
        请仔细阅读用户的问题和提供的相关 Mod 信息（上下文）。
        基于这些信息，清晰、准确地回答用户的问题。
        如果提供的信息不足以回答问题，请说明无法找到相关信息。
        请使用中文回答，不要重复提示词内容，不要重复用户内容。
        引用内容中的ID没有意义是过期数据，请不要引用。直接推荐模组名称。
        </task>
        """,
        markdown=True,
    )

    def run(
            self,
            topic: str
        ) -> Iterator[RunResponse]:
        """执行 AI 搜索工作流"""
        logger.info(f"Starting AI search workflow for query: {topic}")

        # 1. (未来实现) Guardrail Agent Check
        # guardrail_response = self.guardrail_agent.run(topic)
        # if guardrail_response indicates violation:
        #    yield RunResponse(content="抱歉，您的问题可能包含不适宜的内容。", event=RunEvent.workflow_completed)
        #    return

        # 2. 获取查询的 Embedding
        query_embedding = embedding.get_embedding(topic)
        if not query_embedding:
            logger.error("Failed to get embedding for the topic.")
            yield RunResponse(content="抱歉，处理您的问题时遇到内部错误（无法生成向量）。", event=RunEvent.workflow_failed)
            return

        # 3. 检索知识库 (调用导入的函数)
        search_results = search_knowledge_base(query_embedding)

        # 4. 准备问答 Agent 的输入
        context = ""
        if search_results:
            context += "以下是找到的相关 Mod 信息：\n\n"
            for i, result in enumerate(search_results):
                metadata = result.get('metadata', {})
                name = metadata.get('name', '未知 Mod')
                content_preview = result.get('content', '')[:200]
                mod_id = result.get('id', 'N/A')
                # Construct the entry string first
                entry = f"""### Mod {i+1}: {name} (ID: {mod_id})
                内容片段: {content_preview}..."""
                # Append the entry and a newline
                context += entry + "\n"
        else:
            context = "在知识库中没有找到直接相关的信息。"
            logger.info("No relevant documents found in the knowledge base.")

        answering_input = {
            "用户问题": topic,
            "相关信息": context
        }

        # 5. 运行问答 Agent 并返回结果
        logger.info("Running answering agent...")
        try:
            # 使用 stream=True 获取迭代器
            yield from self.answering_agent.run(json.dumps(answering_input, ensure_ascii=False, indent=2), stream=True)
            # Assuming the agent's run stream concludes the workflow for this request.
            # No explicit completion event yielded here unless the agent doesn't handle it.
        except Exception as e:
            logger.error(f"Answering agent failed: {e}")
            yield RunResponse(content=f"抱歉，回答您的问题时遇到内部错误", event=RunEvent.workflow_completed)

        logger.info("AI search workflow finished.")

# Example usage (optional, for testing)
if __name__ == "__main__":
    test_workflow = AISearch()
    test_query = "推荐一个现代战争模组"
    responses = test_workflow.run(topic=test_query)
    final_content = ""
    for response in responses:
        if response.event == RunEvent.run_error:
            print(f"发生错误: {response.content}")
        if response.event == RunEvent.run_completed:
            print(f"运行完成: {response.content}")
        if response.event == RunEvent.run_response:
            print(response.content, end="")
