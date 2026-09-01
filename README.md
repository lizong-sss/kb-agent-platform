# 企业知识库 AI Agent 平台

基于 **RAG（检索增强生成）+ Function Calling** 的企业知识库智能问答平台：上传企业文档（PDF / Word / Excel / Markdown）构建私有知识库，AI Agent 自动检索知识库、查询业务数据库、调用外部工具回答问题，支持多轮对话与 SSE 流式输出。

## 核心特性

- 📄 **多格式文档入库**：PDF / Word / Excel / Markdown / TXT 解析 → 语义分块 → 向量化 → Milvus
- 🔍 **RAG 检索增强**：向量语义检索 + 重排序（向量相似度 × 词面重合度混合精排）
- 🤖 **Agent 工具调用**：基于 LangChain `bind_tools` 的 Function Calling 循环，6 个工具自动选择执行
  - 知识库检索 `rag_search` · SQL 查询 `sql_query` · 人员查询 `hr_lookup` · 政策查询 `policy_lookup` · 邮件发送 `send_email` · 时间查询 `get_time`
- 💬 **多轮对话**：会话与消息持久化（MySQL），上下文窗口管理
- ⚡ **SSE 流式响应**：答案逐字输出，工具调用过程实时可视
- 🚀 **Redis 缓存**：高频问题毫秒级返回（实测命中首字 43ms），Redis 异常自动降级
- 🔐 **JWT 认证**：注册登录 + 密码加盐哈希 + 依赖注入式接口保护

## 实测指标

| 指标 | 结果 | 说明 |
|---|---|---|
| Top3 召回率 | **100%**（10/10） | 自建 QA 测试集，`scripts/eval_recall.py` 可复现 |
| 检索 + 重排链路 | 29.5 ms | 模型预热后（bge-small-zh，CPU） |
| 缓存命中首字延迟 | **43 ms** | 同问题二次提问（Redis） |
| 无缓存首字延迟 | ~1.9 s | 含 DeepSeek 生成（大模型为主耗时） |
| 流式 vs 非流式 | 首字感知提升 **99%** | 3050 ms 完整返回 → 42 ms 首字 |

## 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | Python 3.11+ · FastAPI · Uvicorn · SQLAlchemy |
| LLM / Agent | DeepSeek API · **LangChain**（ChatOpenAI / bind_tools / ToolMessage） |
| RAG | RecursiveCharacterTextSplitter 语义分块 · bge-small-zh-v1.5 向量化 · Milvus 检索 · 混合重排序 |
| 存储 | MySQL 8（用户/会话/业务数据） · Redis 7（答案缓存） · Milvus（向量） |
| 前端 | 单页应用（原生 HTML/CSS/JS，零构建依赖，FastAPI 托管） |
| 部署 | Docker Compose（MySQL + Redis + etcd + MinIO + Milvus） |

## 快速开始

```bash
# 1. 启动依赖服务（MySQL / Redis / Milvus）
docker compose up -d
docker compose ps          # 确认 5 个容器全部 Up

# 2. 启动后端
cd backend
python -m venv .venv                     # 首次
.venv\Scripts\activate                   # Windows 激活
pip install -r requirements.txt
copy .env.example .env                   # 填入你的 DeepSeek API Key
uvicorn app.main:app --reload

# 3. 浏览器打开
#    http://127.0.0.1:8000          → 产品界面（注册登录 → 上传文档 → 提问）
#    http://127.0.0.1:8000/docs     → Swagger 接口文档
```

## 使用流程

1. **注册/登录** → 获得 JWT 令牌
2. **上传文档**（左侧拖拽区）→ 自动解析、分块（默认 500 字/50 重叠）、向量化入库
3. **提问** → Agent 自动选择工具：制度类问题走知识库检索，人员/数据类问题走 SQL 查询
4. 回答流式输出，末尾标注来源文档，可验证可追溯

## 架构

```
浏览器 ──▶ FastAPI
            ├─ api/auth        JWT 注册登录
            ├─ api/documents   上传 → 解析 → 清洗 → 语义分块 → 向量化 → Milvus
            ├─ api/chat        问答(SSE流式) / 会话管理
            │      │
            │      ▼
            │   services/agent  LangChain Function Calling 循环
            │      │
            │      ├── tools/rag_search   → Milvus 检索 + 重排序
            │      ├── tools/sql_query / hr_lookup / policy_lookup → MySQL
            │      ├── tools/send_email / get_time
            │      └── DeepSeek API（生成）
            │
            ├─ services/cache  Redis 高频问答缓存
            └─ services/conversation  多轮会话持久化
```

## 目录结构

```
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口：路由注册、CORS、前端托管
│   │   ├── api/               # 接口层：auth / documents / chat / deps(鉴权)
│   │   ├── core/              # config(.env 配置) / security(JWT、密码哈希)
│   │   ├── models/            # ORM 模型：user / conversation / business
│   │   ├── services/
│   │   │   ├── document/      # parser(解析) / chunker(分块) / embedder(向量化)
│   │   │   ├── rag/           # retriever(检索) / reranker(重排) / generator(生成)
│   │   │   ├── agent/         # Function Calling 循环
│   │   │   ├── conversation/  # 多轮会话
│   │   │   └── cache/         # Redis 缓存
│   │   ├── tools/             # Agent 工具集（base 基类 + registry 注册表 + 6 工具）
│   │   └── db/                # mysql / milvus 连接管理
│   ├── static/index.html      # 前端单页应用
│   ├── scripts/               # 测试与运维脚本（见下）
│   └── tests/
├── docker-compose.yml         # MySQL + Redis + etcd + MinIO + Milvus
└── README.md
```

## 测试脚本

```bash
cd backend
.venv\Scripts\python.exe scripts/verify_ingestion.py "报销标准"   # 验证向量检索
.venv\Scripts\python.exe scripts/test_e2e.py                      # 端到端：登录→流式问答
.venv\Scripts\python.exe scripts/eval_recall.py                   # Top3 召回率评测
.venv\Scripts\python.exe scripts/benchmark.py                     # 性能基准（首字延迟等）
```

## Roadmap

- [x] 文档解析与语义分块入库
- [x] RAG 检索问答 + 召回率评测
- [x] Agent 工具调用（6 工具）
- [x] 用户认证 / 多轮对话 / SSE 流式响应
- [x] 缓存与性能优化（重排序 / 缓存命中）
- [x] 前端单页界面
- [ ] 迁移 pymilvus MilvusClient 新接口（消除 ORM deprecation）
- [ ] 重排序升级 bge-reranker 交叉编码器
- [ ] 大规模文档场景：异步入库队列（Celery）+ HNSW 索引
