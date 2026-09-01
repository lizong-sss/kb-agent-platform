"""召回率评测脚本：自建 QA 测试集，跑 Top3 召回率。

用法（backend 目录下）：
    .venv\\Scripts\\python.exe scripts/eval_recall.py

指标口径：对每个问题，检索 Top3 文本块，若任一召回块包含"期望关键词"之一则记为命中。
输出：命中数 / 总数 = Top3 召回率。这是简历"Top3 召回率达 90%+"的数据来源。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")

from app.services.rag.reranker import search_with_rerank

# 测试集：(问题, [期望关键词])，全部来自 scripts/测试文档-员工手册.md 的真实内容
QA_SET = [
    ("员工年假有多少天", ["年假", "5天", "10天"]),
    ("公司考勤工作时间是几点到几点", ["9:00-18:00", "18:00", "午休"]),
    ("差旅报销要在几天内提交", ["15个工作日", "15"]),
    ("一线城市住宿标准是多少", ["400"]),
    ("每天餐饮补贴多少钱", ["100"]),
    ("单笔采购5000元以下怎么处理", ["部门", "自行审批", "5000"]),
    ("泄露公司机密有什么后果", ["严重违纪", "追究"]),
    ("病假期间工资怎么发", ["80%"]),
    ("离职时未休年假怎么折算", ["300%"]),
    ("出差交通标准是什么", ["高铁", "经济舱"]),
]


def main():
    print(f"{'问题':<24} {'是否命中':<8} 命中片段")
    print("-" * 70)
    hit_count = 0
    for question, keywords in QA_SET:
        hits = search_with_rerank(question, final_top_k=3)
        texts = " ".join(h["text"] for h in hits)
        matched = [kw for kw in keywords if kw in texts]
        hit = len(matched) > 0
        hit_count += 1 if hit else 0
        frag = hits[0]["text"][:30].replace("\n", " ") if hits else "(无召回)"
        print(f"{question:<24} {'✅' if hit else '❌':<8} {frag}")
    total = len(QA_SET)
    recall = hit_count / total * 100
    print("-" * 70)
    print(f"\nTop3 召回率 = {hit_count}/{total} = {recall:.1f}%")


if __name__ == "__main__":
    main()
