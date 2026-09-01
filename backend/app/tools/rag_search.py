"""工具：企业知识库检索。

把 RAG 检索+重排序（services/rag/reranker.py）包成工具。
这样 Agent 可以在"查文档"和"查数据库"之间自动选择——同一个演示就能证明 RAG + Function Calling 两个能力。
"""
from app.services.rag.reranker import search_with_rerank
from app.tools.base import BaseTool


class RagSearchTool(BaseTool):
    name = "rag_search"
    description = "在企业知识库中检索与问题最相关的文档片段，适合回答公司制度、政策、员工手册类问题（如年假、报销、考勤）。"
    args_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "要检索的问题或关键词"},
            "top_k": {"type": "integer", "description": "返回几条结果，默认3", "default": 3},
        },
        "required": ["query"],
    }

    def run(self, query: str, top_k: int = 3) -> str:
        # 先宽召回 8 条，再按 向量相似度+词面重合度 重排序取 TopN
        hits = search_with_rerank(query, recall_top_k=8, final_top_k=top_k)
        if not hits:
            return "知识库中没有找到相关内容。"
        lines = []
        for i, h in enumerate(hits, 1):
            lines.append(
                f"[{i}] 来源:{h['source']} 第{h['chunk_index']}块 (相似度:{h['score']:.4f})\n{h['text']}"
            )
        return "\n\n".join(lines)
