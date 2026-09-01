"""端到端测试：注册/登录 → 鉴权 → 流式问答（SSE 全事件打印）。

用法（backend 目录下）：
    .venv/Scripts/python.exe scripts/test_e2e.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")

import httpx

BASE = "http://127.0.0.1:8000"
USER, PASS = "lizong", "demo123456"


def main():
    client = httpx.Client(timeout=120)

    # 1. 注册（已存在就忽略）+ 登录
    r = client.post(f"{BASE}/auth/register", json={"username": USER, "password": PASS})
    print(f"[注册] HTTP {r.status_code} {'(用户已存在,跳过)' if r.status_code == 400 else ''}")
    r = client.post(f"{BASE}/auth/login", data={"username": USER, "password": PASS})
    assert r.status_code == 200, f"登录失败: {r.text}"
    token = r.json()["access_token"]
    print(f"[登录] 成功, token 前 20 位: {token[:20]}...")

    headers = {"Authorization": f"Bearer {token}"}

    # 2. 鉴权验证
    r = client.get(f"{BASE}/auth/me", headers=headers)
    print(f"[鉴权] 当前用户: {r.json()['username']}")

    # 3. 流式问答
    question = "员工年假有多少天？"
    print(f"\n[流式问答] 问题: {question}\n" + "-" * 60)
    answer_parts, sources, tool_names = [], [], []
    with client.stream("POST", f"{BASE}/chat/ask/stream", headers=headers,
                       json={"question": question}) as r:
        print(f"[HTTP] {r.status_code} content-type={r.headers.get('content-type')}")
        for line in r.iter_lines():
            if not line.startswith("data:"):
                continue
            evt = json.loads(line[5:])
            t = evt["type"]
            if t == "start":
                print(f"  [start] conversation_id={evt['conversation_id']}")
            elif t == "tool":
                tool_names.append(evt.get("tool_name"))
                print(f"  [tool]  {evt.get('tool_name')} 参数={evt.get('args')} 结果={str(evt.get('result'))[:60]}")
            elif t == "token":
                answer_parts.append(evt["content"])
            elif t == "done":
                sources = evt.get("sources", [])
                print(f"  [done]  sources={sources}")

    print("-" * 60)
    print("AI 回答:", "".join(answer_parts))
    print(f"调用工具: {tool_names}, 来源: {sources}")
    ok = bool(answer_parts)
    print("\n✅ 端到端测试通过" if ok else "\n❌ 未收到任何回答内容")


if __name__ == "__main__":
    main()
