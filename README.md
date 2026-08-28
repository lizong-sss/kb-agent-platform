# 企业知识库 AI Agent 平台

基于 **RAG（检索增强生成）+ Function Calling** 的企业知识库智能问答平台：上传企业文档（PDF / Word / Excel / Markdown）构建私有知识库，AI Agent 自动检索知识库、查询业务数据库、调用外部工具回答问题，支持多轮对话与 SSE 流式输出。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | Python 3.11 · FastAPI · Uvicorn |
| LLM / Agent | DeepSeek API · LangChain（Tool Calling） |
| RAG | 语义分块 · bge 中文 Embedding · Milvus 向量检索 · 重排序 |
| 存储 | MySQL 8（业务数据） · Redis 7（缓存/会话） · Milvus（向量） |
| 前端 | Vue3 · Element Plus |
| 部署 | Docker / docker-compose |

## 架构

```
Vue3 前端 ──▶ FastAPI 后端
              ├─ 认证(JWT) / 对话管理 / SSE 流式响应
              ├─ 文档入库：解析 → 清洗 → 语义分块 → 向量化 → Milvus
              └─ Agent：RAG检索 / SQL查询 / 邮件等 6+ 工具（Function Calling 自动选择）
```

## 快速开始

```bash
# 1. 启动依赖服务（MySQL / Redis / Milvus）
docker compose up -d

# 2. 启动后端
cd backend
python -m venv .venv                    # 首次
.venv\Scripts\activate                  # Windows 激活虚拟机环境
pip install -r requirements.txt
copy .env.example .env                  # 填入你的 DeepSeek API Key
uvicorn app.main:app --reload

# 3. 打开 Swagger 文档
# http://127.0.0.1:8000/docs
```

## 功能模块（开发中）

- [x] 项目骨架 / 依赖服务编排
- [ ] 文档解析与语义分块入库
- [ ] RAG 检索问答（含召回率评测）
- [ ] Agent 工具调用（6+ 工具）
- [ ] 用户认证 / 多轮对话 / SSE 流式响应
- [ ] 缓存与性能优化（重排序 / 缓存命中）
- [ ] 前端界面

## 目录结构

```
├── backend/            # FastAPI 后端
│   ├── app/
│   │   ├── core/       # 配置、安全
│   │   ├── api/        # 路由
│   │   ├── models/     # ORM 模型
│   │   ├── schemas/    # 请求/响应模型
│   │   ├── services/   # 业务逻辑（文档处理/RAG/Agent/缓存）
│   │   └── tools/      # Agent 工具集
│   ├── tests/          # 测试
│   └── scripts/        # 脚本（benchmark/数据初始化）
├── frontend/           # Vue3 前端
├── docker-compose.yml  # MySQL + Redis + Milvus 编排
└── README.md
```
