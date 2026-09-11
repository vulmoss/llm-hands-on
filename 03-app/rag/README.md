# RAG：先查资料，再生成答案

```bash
llm-lab index data/notes
llm-lab rag '为什么模型能接着上一句话回答？' --retrieve-only
llm-lab rag '为什么模型能接着上一句话回答？' --json
python examples/03_rag.py
```

## 阅读顺序

阅读 `src/llm_lab/rag.py`：

1. `load_chunks`：读取 UTF-8 文本，按字符切块，记录文件名和偏移。
2. `VectorIndex.build`：批量调用 Embedding，标准化向量。
3. `save/load`：原子保存 JSON，检查格式、模型和维度。
4. `search`：对查询向量做余弦相似度排序，返回 top-k。
5. `answer_question`：明确拼接片段与问题，再调用生成模型。

生成模型和 Embedding 模型负责不同任务。RAG 不修改生成模型的参数。
JSON 索引适合学习时查看；实现为线性扫描，不适合大量文档或高并发。

## 实验

- 固定题集，对比 `--chunk-size 200 --overlap 40` 与 `500 / 80`；每次重新 index。
- 固定索引，对比 `-k 1`、`-k 3`、`-k 5`，记录命中的原文。
- 加一篇自己的笔记，确认原文、索引和答案都更新。
- 尝试 `--min-score 0.5`，同时观察可回答和不可回答问题；不要把该值当通用标准。
- 换 Embedding 模型后重建索引，对比中文题集；向量维数更大不自动意味着更准确。

使用 `data/eval/questions.jsonl`，先人工判断正确来源是否进入 top-k，再判断答案是否有依据。
`--json` 中的 sources 是提供给模型的候选证据，程序尚未验证模型写出的每个引用。
空候选直接返回信息不足；有候选仍可能与问题无关，需要评估拒答表现。

## 数据边界

只读取显式指定目录下的 `.md`、`.txt`，忽略隐藏路径，拒绝指向目录外的文件链接。
每个文件最多 1 MB，最多 5000 个片段。PDF/OCR、增量更新、混合检索是后续练习。
索引会保存原文；请为学习准备独立的资料目录。

兼容入口：`python 03-app/rag/demo2_rag.py '问题'`，运行前先构建索引。
