import random

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config

app = FastAPI(
    title="RW-mod AI search",
    description="RW-mod-download project ai search",
    version="1.0.1"
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5005"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Response(BaseModel):
    message: str
    error: str
    data: dict


@app.get("/api/ai/search", response_model=Response)
async def search_mods(query: str = Query(..., description="Natural language search query")):
    """
    AI 搜索接口，对接前端搜索功能
    """
    from agent import AISearch
    try:
        ai_search = AISearch()
        result = ""
        for resp in ai_search.run(topic=query):
            if hasattr(resp, "content"):
                result += resp.content
        return Response(data={"result": result}, message="success", error="")
    except Exception as e:
        return Response(data={}, message="fail", error=str(e))


@app.get("/api/ai/recommend", response_model=Response)
async def recommend_mods():
    """
    推荐搜索词
    """

    suggestions = random.choices(config.search_suggestions, k=3)
    return Response(data={"suggestions": suggestions}, message="success", error="")


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5027)
