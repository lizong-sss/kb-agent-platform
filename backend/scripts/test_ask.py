"""问答接口测试脚本。

用法：
    .venv/Scripts/python.exe scripts/test_ask.py "员工年假有多少天？"
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx

BASE_URL = "http://127.0.0.1:8000"


def main():
    question = sys.argv[1] if len(sys.argv) > 1 else "员工年假有多少天？"

    resp = httpx.post(
        f"{BASE_URL}/chat/ask",
        json={"question": question},   # httpx 会把中文正确编码为 UTF-8
        timeout=60,
    )
    print(f"HTTP {resp.status_code}")
    data = resp.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
