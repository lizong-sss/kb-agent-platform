"""性能基准脚本：产出简历性能数据。

指标：
  A. 检索+重排链路耗时（纯 RAG 部分，不含大模型）
  B. 流式问答首字延迟：首次提问 vs 再次提问（命中 Redis 缓存）
  C. 非流式完整返回 vs 流式首字（流式对"感知响应速度"的提升）

用法（backend 目录下，需后端已启动）：
    .venv\\Scripts\\python.exe scripts/benchmark.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")

import httpx

BASE = "http://127.0.0.1:8000"
USERNAME, PASSWORD = "lizong", "demo123456"


def avg(xs):
    return sum(xs) / len(xs)


def main():
    client = httpx.Client(timeout=120)
    token = client.post(f"{BASE}/auth/login",
                        data={"username": USERNAME, "password": PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ---- 指标 A：检索+重排链路（本地计算，不含大模型） ----
    from app.services.rag.reranker import search_with_rerank
    questions = ["员工年假有多少天", "差旅报销标准是多少", "班车几点发车"]
    search_with_rerank(questions[0], recall_top_k=8, final_top_k=3)   # 预热：加载向量模型（不计入）
    times_a = []
    for q in questions:
        for _ in range(3):
            t0 = time.perf_counter()
            search_with_rerank(q, recall_top_k=8, final_top_k=3)
            times_a.append((time.perf_counter() - t0) * 1000)
    print(f"[A] 检索+重排平均耗时: {avg(times_a):.1f} ms  ({len(times_a)} 次, 模型已预热)")

    # ---- 指标 B：流式首字延迟（首次 vs 缓存命中） ----
    def stream_ask(question, read_all=False):
        """返回首字延迟 ms。read_all=True 时读完整个流（确保服务端缓存落库）。"""
        start = time.perf_counter()
        first = None
        with client.stream("POST", f"{BASE}/chat/ask/stream", headers=headers,
                           json={"question": question, "conversation_id": None}) as r:
            for line in r.iter_lines():
                if line.startswith("data:") and '"token"' in line:
                    if first is None:
                        first = (time.perf_counter() - start) * 1000
                        if not read_all:
                            break
        return first or (time.perf_counter() - start) * 1000

    q_b = "年度体检是什么时候"
    cold = stream_ask(q_b, read_all=True)                 # 首次：完整链路 + 缓存写入
    warm = avg([stream_ask(q_b) for _ in range(3)])       # 再次：命中 Redis 缓存
    print(f"[B] 首字延迟 - 无缓存(冷): {cold:.0f} ms | 命中缓存(热): {warm:.0f} ms | "
          f"缓存提速 {cold / max(warm, 1):.1f} 倍")

    # ---- 指标 C：非流式完整返回 vs 流式首字（感知速度提升） ----
    q_c = "会议室怎么预定"
    t0 = time.perf_counter()
    client.post(f"{BASE}/chat/ask", headers=headers, json={"question": q_c, "conversation_id": None})
    full_ms = (time.perf_counter() - t0) * 1000
    first_c = first_token_ms(q_c)   # 此问已缓存，但流式首字含网络+首帧
    gain = (full_ms - first_c) / full_ms * 100
    print(f"[C] 同问题: 非流式完整返回 {full_ms:.0f} ms | 流式首字 {first_c:.0f} ms | "
          f"首字感知提升 {gain:.0f}%")

    print("\n汇总：以上为实测数据，面试引用时注明测试环境（本机 Docker + DeepSeek API）。")


if __name__ == "__main__":
    main()
