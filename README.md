<div id="readme-top"></div>

<!-- Logo -->
<div align="center">

<h3><b>铁锈工坊 AI Service</b></h3>

[![Python][Python]][Python-url]
[![FastAPI][FastAPI]][FastAPI-url]
[![LangChain][langchain]][langchain-url]

</div>

<!-- 项目描述 -->

# 📖 AI 翻译与搜索模组 <a id="about-project"></a>

> 一个基于 LangChain 的模组内容翻译与搜索系统，支持模组的双语翻译（中英）和自然语言搜索功能,以及Markdown内容的格式化。
> 并且提供AI搜索pg数据库的支持，提供模组的智能搜索功能。

## ✨ 主要功能

- 🌐 **双语翻译**：自动将模组标题和内容翻译为中文和英文，支持 Markdown 格式优化。
- 🔍 **AI 搜索**：通过自然语言处理，将用户查询转化为 SQL，实现模组智能搜索。
- ⚡ **高性能**：多线程翻译与快速响应 API。
- 🛡️ **安全性**：检测并阻止 SQL 注入攻击。
- 🛡️ **护栏**：检测并忽略跑题聊天。

## 🛠 技术栈 <a id="built-with"></a>

### 技术栈详情 <a id="tech-stack"></a>


<details>
  <summary>AI搜索 服务端</summary>
  <ul>
    <li><a href="https://www.python.org/">Python</a> - LangChain 结构化 数据处理</li>
    <li><a href="https://fastapi.tiangolo.com/">FastAPI</a> - 高性能 API 框架</li>
    <li><a href="https://www.postgresql.org/">PostgreSQL</a> - 数据存储</li>
  </ul>
</details>

<details>
  <summary>AI 批处理翻译</summary>
  <ul>
    <li><a href="https://www.python.org/">Python</a> - LangChain 翻译脚本</li>
    <li><a href="https://digitalocean.com/">DigitalOcean</a> - llama 3.3 模型 (批处理翻译)</li>
    <li><a href="https://xai.com/">xAI</a> - Grok2.0 模型 (批处理翻译)</li>
  </ul>
</details>

## 📁 项目结构

```
.
├── translate.py      # AI翻译批处理脚本
├── ai_search.py      # Fastapi 服务入口
├── config.py         # 配置文件
└── requirements.txt  # Python 依赖
```

## 🚀 在线演示 <a id="live-demo"></a>

- [在线网站](https://rw.d5v.cc/ai-search)

## 💻 快速开始 <a id="getting-started"></a>

### 前置要求

- Python 3.8+
- PostgreSQL

### 安装与运行

#### 搜索服务API
```shell
# 安装 Python 依赖
pip install -r requirements.txt

# 启动服务端（默认端口 5027）
python ai_search.py

# 默认启用了CORS
```

## 🤝 贡献 <a id="contributing"></a>

欢迎提交 Issue 或 Pull Request：

1. Fork 项目
2. 创建分支 (`git checkout -b feature/NewFeature`)
3. 提交更改 (`git commit -m 'Add NewFeature'`)
4. 推送分支 (`git push origin feature/NewFeature`)
5. 创建 Pull Request

## 📝 许可证 <a id="license"></a>

基于 MIT 许可证开源，详见 [LICENSE](LICENSE) 文件。

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->

[FastAPI]: https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white
[FastAPI-url]: https://fastapi.tiangolo.com/
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[langchain]: https://img.shields.io/badge/LangChain-FF9900?style=for-the-badge&logo=langchain&logoColor=white
[langchain-url]: https://langchain.readthedocs.io/en/latest/