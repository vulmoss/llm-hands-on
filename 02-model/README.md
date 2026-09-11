# 模型实验：用自己的题目建立判断

先跑通聊天，再学习 Token、上下文、采样、Embedding 和量化。
本章不预设具体机器的速度或模型排名。

## 1. 固定问题，比较模型

```bash
mkdir -p .data/experiments
OLLAMA_MODEL=qwen2.5:1.5b llm-lab benchmark '用100字解释监督学习，并举一个例子。' --repeat 3 > .data/experiments/1.5b.json
OLLAMA_MODEL=qwen2.5:7b llm-lab benchmark '用100字解释监督学习，并举一个例子。' --repeat 3 > .data/experiments/7b.json
```

模型需先在 Ollama 主机安装。记录模型名、采样配置、机器配置和题目。
每组保留首次请求；首次可能包含模型加载，后续可能受缓存影响，分开分析。

| 指标 | 含义 |
|---|---|
| `first_text_seconds` | 客户端发起请求到收到第一段非空生成文本，空输出为 null |
| `wall_seconds` | 客户端观测的整个流式请求耗时 |
| `tokens_per_second` | 服务端输出 Token 数 / 生成时间 |
| `prompt_eval_seconds` | 服务端处理输入的时间，不是首 Token 延迟 |
| `load_seconds` | 服务端报告的模型加载时间 |

首段文本可能含多个 Token，该指标不等同于推理引擎内部精确 TTFT。
指标定义参考 [Ollama Chat API](https://docs.ollama.com/api/chat)。

## 2. 概念与实验

| 概念 | 实验 | 应理解的结论 |
|---|---|---|
| Token | 查看请求返回的 Token 数，换中文、英文与代码 | Token 不等于字符，取决于分词器 |
| 上下文 | 保留和移除 history，逐步增加文本长度 | 历史占用上下文；窗口存在上限 |
| Temperature | 用 0 和 0.7 重复同一题 | 采样影响随机性；0 不保证所有环境下完全复现 |
| 模型大小 | 对比固定题集及耗时 | 大小与速度、质量需要结合任务测量 |
| Embedding | 同义改写和无关问题的检索对比 | 向量用于相似度，分数不是事实正确率 |
| 量化 | 对同一模型的不同量化版本测题集 | 压缩节省资源，效果损失没有通用固定百分比 |

先沿用已有模型建立基线。更换 Embedding 后重新 `llm-lab index data/notes`。
不要把不同模型的向量混在同一个索引里，也不要只凭向量维数推断质量。

## 3. 质量评估

从事实问答、总结、代码、指令遵循中各选几题，预先写验收标准。
每题记录是否正确、是否遵循格式、耗时和失败原因。调参题与最终检查题分开。
本项目聚焦应用；如果要学习训练，再补线性代数、概率、梯度下降和小型神经网络实验。
