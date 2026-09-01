"""批量回归测试：覆盖知识库问答 / 工具调用 / 反幻觉三大类场景。

用法（backend 目录下）：
    .venv/Scripts/python.exe scripts/batch_test.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")

import httpx

BASE = "http://127.0.0.1:8000"

# (问题, 期望要点/期望行为说明)
CASES = [
    ("员工年假有多少天？",                 "知识库/年假天数"),
    ("年终奖一般发多少？",                 "知识库/年终奖"),
    ("远程办公一周可以几天？",             "知识库/远程办公"),
    ("班车几点发车？",                     "知识库/班车"),
    ("加班怎么调休？",                     "知识库/调休比例"),
    ("试用期离职要提前几天？",             "知识库/离职"),
    ("张三是什么部门的？",                 "工具/hr或sql"),
    ("现在几点了？",                       "工具/get_time"),
    ("公司今年的经营战略是什么？",         "反幻觉/应说没找到"),
]


def main():
    client = httpx.Client(timeout=120)
    r = client.post(f"{BASE}/auth/login", data={"username": "lizong", "password": "demo123456"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    conv_id = None

    results = []
    for question, expect in CASES:
        answer_parts, tools, cached_src = [], [], ""
        with client.stream("POST", f"{BASE}/chat/ask/stream", headers=headers,
                           json={"question": question, "conversation_id": conv_id}) as r:
            for line in r.iter_lines():
                if not line.startswith("data:"):
                    continue
                evt = json.loads(line[5:])
                if evt["type"] == "start":
                    conv_id = evt["conversation_id"]
                elif evt["type"] == "tool":
                    tools.append(evt.get("tool_name"))
                elif evt["type"] == "token":
                    answer_parts.append(evt["content"])
                elif evt["type"] == "done":
                    cached_src = "、".join(evt.get("sources", []))
        answer = "".join(answer_parts).replace("\n", " ")
        short = answer[:88] + ("…" if len(answer) > 88 else "")
        results.append((question, expect, tools, short))
        print(f"\nQ: {question}   [期望:{expect}]")
        print(f"   工具: {tools}")
        print(f"   答: {short}")

    print("\n" + "=" * 70)
    print("全部用例执行完毕，请人工核对以上回答质量")


if __name__ == "__main__":
    main()
