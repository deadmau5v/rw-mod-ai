import random
from typing import Any

# ai
import uvicorn
# api
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
from agent import natural_language_search, execute_sql_query

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
