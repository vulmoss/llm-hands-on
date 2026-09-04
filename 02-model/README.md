# 02 - 模型层

> 理解 LLM 本身：从"会用"到"理解为什么能工作"。
> 配套环境：VM1 (192.168.2.15) CPU 推理，Ollama + qwen2.5 系列。

## 学习路线

```
2.1 理解 LLM 基础        2.2 模型选型           2.3 量化
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Token/上下文  │      │ 参数量 vs 效果 │      │ Q4/Q5/Q8    │
│ 注意力机制    │  -->  │ 中文模型对比   │  -->  │ 速度 vs 精度  │
│ 温度/Top-P    │      │ 场景驱动选择   │      │ 你的环境实测  │
└──────────────┘      └──────────────┘      └──────────────┘
         │
         v
2.4 Embedding 模型       2.5 推理性能基准
┌──────────────┐      ┌──────────────┐
│ 向量化原理    │      │ tokens/s     │
│ 维度/相似度   │  -->  │ 首 token 延迟 │
│ 中文模型选型  │      │ 并发 vs 串行  │
└──────────────┘      └──────────────┘
```

## 学完这层你应该会

- 解释 Token、上下文窗口、Temperature 的含义
- 根据场景选择合适的模型大小和量化方式
- 理解 Embedding 的原理和选型标准
- 用 Ollama 做推理性能基准测试

---

## 2.1 理解 LLM 基础

你已经会用 LLM 了（Demo1-3），这层补"为什么能工作"。

| 概念 | 需要理解到什么程度 | 推荐资源 |
|------|-------------------|----------|
| Token | 中文大约 1 字 ≈ 1-2 token，影响费用和上下文长度 | 用下面的代码实测 |
| 上下文窗口 | 32K 是什么意思，为什么对话太长会变慢 | 自己试：发 100 轮对话看响应变化 |
| Temperature / Top-P | 控制输出随机性的采样参数 | 3Blue1Brown 可视化视频 |
| Transformer/Attention | 不需要推公式，理解"注意力"的直觉 | 3Blue1Brown "But what is a GPT?" 系列 |

### 动手：在你的环境上验证概念

```python
import requests

# 用 Ollama API 看 token 用量和生成速度
r = requests.post("http://192.168.2.15:11434/api/generate", json={
    "model": "qwen2.5:7b",
    "prompt": "用100字介绍北京",
    "stream": False
})
data = r.json()
print(f"输入 token: {data['prompt_eval_count']}")
print(f"输出 token: {data['eval_count']}")
print(f"生成速度: {data['eval_count']/data['eval_duration']*1e9:.1f} tokens/s")
```

### 推荐视频

| 视频 | 时长 | 说明 |
|------|------|------|
| [But what is a GPT?](https://www.youtube.com/watch?v=wjZofJX0v4M) | ~50min | 3Blue1Brown，最好的 Transformer 可视化讲解 |
| [Visualizing Attention](https://www.youtube.com/watch?v=eMlx5fFNoYc) | ~30min | 3Blue1Brown，注意力机制直觉 |
| [Let's build GPT from scratch](https://www.youtube.com/watch?v=kCc8FmEb1nY) | ~2h | Andrej Karpathy，从零手写 mini-GPT |

---

## 2.2 模型选型

### 参数量与效果的关系

| 参数量 | 典型模型 | 适合场景 | 你的环境 |
|--------|---------|---------|---------|
| 0.5-1.5B | qwen2.5:1.5b | 快速测试、简单问答 | 已安装，986MB |
| 3-7B | qwen2.5:7b | 日常对话、代码生成 | 已安装，4.7GB |
| 14-32B | qwen2.5:32b | 复杂推理、长文写作 | CPU 推理太慢，不推荐 |
| 70B+ | qwen2.5:72b | 生产级任务 | 需要 GPU，不适合当前环境 |

### 中文模型生态

| 模型系列 | 来源 | 特点 |
|----------|------|------|
| Qwen (通义千问) | 阿里 | 中文能力强，系列完整（0.5B-72B） |
| GLM / ChatGLM | 智谱 AI | 中英双语，推理效率高 |
| DeepSeek | 深度求索 | 推理能力突出，代码能力强 |
| Yi (零一万物) | 01.AI | 多语言能力好 |

### 动手：模型对比实验

```bash
# 拉一个推理型模型对比
ollama pull deepseek-r1:7b

# 同一个问题跑两个模型，对比速度和质量
# 问题示例：
# - "解释量子计算的基本原理"（测试知识深度）
# - "写一个 Python 快速排序"（测试代码能力）
# - "用一句话总结红楼梦"（测试中文理解）
```

### 推荐资源

| 资源 | 说明 |
|------|------|
| [LMSYS Chatbot Arena](https://chat.lmsys.org/) | 模型能力 ELO 排名，选模型参考 |
| [HuggingFace Open LLM Leaderboard](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard) | 开源模型评测排行 |
| [Ollama Model Library](https://ollama.com/library) | 所有可拉取的模型列表 |

---

## 2.3 量化

### 为什么需要量化

模型训练时用的是 FP16（16位浮点），每个参数占 2 字节。量化把参数压缩到更低的精度：

```
FP16 (原始)  →  Q8_0      →  Q5_K_M    →  Q4_K_M (你当前用的)
15GB           7.5GB         5.5GB         4.7GB
精度 100%      精度 ~99%     精度 ~97%     精度 ~95%
```

**直觉理解：** 就像图片压缩——JPEG 压缩后文件小很多，肉眼几乎看不出区别，但放大看会有损失。

### 量化格式对比

| 格式 | 大小比例 | 精度损失 | 推荐场景 |
|------|---------|---------|---------|
| Q8_0 | ~50% | 极小 | 内存充足，追求质量 |
| Q5_K_M | ~37% | 很小 | 平衡选择 |
| Q4_K_M | ~28% | 较小 | **你的选择** — CPU 推理的最佳平衡 |
| Q2_K | ~15% | 明显 | 极端节省，质量下降多 |

### 你的环境已经是量化的

```
qwen2.5:1.5b → 986MB (Q4_K_M)  ← 原始 FP16 约 3GB
qwen2.5:7b   → 4.7GB (Q4_K_M)  ← 原始 FP16 约 15GB
```

Ollama 默认下载 Q4_K_M 量化版本，不需要手动处理。

### 推荐资源

| 资源 | 说明 |
|------|------|
| [HuggingFace 量化指南](https://huggingface.co/docs/optimum/concept_guides/quantization) | 量化原理和格式对比 |
| [GGUF 规范](https://github.com/ggerganov/gguf) | Ollama 使用的模型格式 |

---

## 2.4 Embedding 模型

Embedding 模型你在 Demo2 (RAG) 中已经用了（all-minilm:33m），这层深入理解它。

### 向量化原理

```
"VM1 的内存" → Embedding 模型 → [0.12, -0.34, 0.78, ..., 0.56]  (384维向量)
"服务器配置" → Embedding 模型 → [0.11, -0.32, 0.75, ..., 0.54]  ← 距离近！语义相似
"今天天气"   → Embedding 模型 → [-0.45, 0.67, -0.12, ..., 0.89]  ← 距离远！语义不同
```

### 维度选择

| 维度 | 典型模型 | 存储开销 | 精度 |
|------|---------|---------|------|
| 384 | all-minilm:33m | 最小 | 英文好，中文一般 |
| 768 | nomic-embed-text | 中等 | 多语言，中文更好 |
| 1536 | text-embedding-3-small (OpenAI) | 较大 | 高精度 |

### 动手：对比 Embedding 模型

```bash
# 拉一个中文更好的 embedding 模型
ollama pull nomic-embed-text

# 在 Demo2 中替换 all-minilm:33m 为 nomic-embed-text
# 观察中文文档的检索效果是否提升
```

### 推荐资源

| 资源 | 说明 |
|------|------|
| [MTEB Embedding 排行榜](https://huggingface.co/spaces/mteb/leaderboard) | Embedding 模型选型参考 |
| [Sentence Transformers 文档](https://www.sbert.net/) | Embedding 模型的详细教程 |

---

## 2.5 推理性能基准

### 关键指标

| 指标 | 含义 | 怎么测 |
|------|------|--------|
| tokens/s | 每秒生成的 token 数 | Ollama API 的 eval_duration |
| 首 token 延迟 | 从提问到第一个字出现的时间 | Ollama API 的 prompt_eval_duration |
| 内存占用 | 模型加载后占多少 RAM | `ollama ps` + `top` |
| 并发能力 | 同时处理几个请求 | Ollama 的 num-parallel 配置 |

### 动手：在你的 VM1 上跑基准测试

```python
import requests
import time

MODELS = ["qwen2.5:1.5b", "qwen2.5:7b"]
PROMPT = "请用200字解释什么是机器学习，包括 supervised learning 和 unsupervised learning 的区别。"

for model in MODELS:
    r = requests.post("http://192.168.2.15:11434/api/generate", json={
        "model": model,
        "prompt": PROMPT,
        "stream": False
    })
    data = r.json()
    tps = data["eval_count"] / data["eval_duration"] * 1e9
    first_token = data["prompt_eval_duration"] / 1e9

    print(f"\n{'='*50}")
    print(f"模型: {model}")
    print(f"输入 token: {data['prompt_eval_count']}")
    print(f"输出 token: {data['eval_count']}")
    print(f"首 token 延迟: {first_token:.2f}s")
    print(f"生成速度: {tps:.1f} tokens/s")
    print(f"总耗时: {(data['total_duration']/1e9):.2f}s")
```

### 你的环境预期值

| 指标 | qwen2.5:1.5b | qwen2.5:7b |
|------|-------------|------------|
| 生成速度 | ~20-40 tokens/s | ~5-10 tokens/s |
| 首 token 延迟 | < 1s | 1-3s |
| 内存占用 | ~1.5GB | ~5-6GB |
| 并发 | num-parallel=2 | 同时只能加载 1-2 个模型 |

### 动手：并发测试

```python
import requests
import time
from concurrent.futures import ThreadPoolExecutor

def single_request(i):
    start = time.time()
    r = requests.post("http://192.168.2.15:11434/api/generate", json={
        "model": "qwen2.5:1.5b",
        "prompt": f"第{i}个请求：用一句话介绍Python",
        "stream": False
    })
    elapsed = time.time() - start
    return elapsed

# 同时发 5 个请求
with ThreadPoolExecutor(max_workers=5) as pool:
    results = list(pool.map(single_request, range(5)))

print(f"5 个并发请求耗时: {results}")
print(f"平均: {sum(results)/len(results):.2f}s")
print(f"最慢: {max(results):.2f}s")
```

---

## 推荐资源汇总

| 类型 | 资源 | 说明 |
|------|------|------|
| 视频 | [3Blue1Brown GPT 系列](https://www.youtube.com/watch?v=wjZofJX0v4M) | Transformer 可视化讲解 |
| 视频 | [Karpathy Let's build GPT](https://www.youtube.com/watch?v=kCc8FmEb1nY) | 从零手写 mini-GPT |
| 文档 | [Ollama 官方文档](https://github.com/ollama/ollama/tree/main/docs) | 模型管理、API、配置 |
| 文档 | [LangChain 概念文档](https://python.langchain.com/docs/concepts/) | LLM/Embedding 概念 |
| 排行榜 | [LMSYS Chatbot Arena](https://chat.lmsys.org/) | 模型能力排名 |
| 排行榜 | [MTEB Embedding 排行榜](https://huggingface.co/spaces/mteb/leaderboard) | Embedding 模型选型 |
| 实战 | [HuggingFace Models](https://huggingface.co/models) | 浏览和下载模型 |

## 学习建议

1. **先看视频**：3Blue1Brown 的 GPT 系列（2.1），建立直觉理解
2. **跑基准测试**（2.5），用数据感受 1.5b 和 7b 的差异
3. **对比模型**（2.2），拉一个 deepseek-r1:7b 对比 qwen2.5:7b
4. **换 Embedding**（2.4），在 Demo2 中把 all-minilm 换成 nomic-embed-text，观察中文检索效果
5. 每完成一个小节，把实验结果记录到本目录下的笔记文件中
