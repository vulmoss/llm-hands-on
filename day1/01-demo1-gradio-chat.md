# Demo1: Gradio 聊天界面 - 逐行讲解

> 目标：用 Gradio 搭建一个网页版 AI 聊天界面，连接 Ollama 进行对话。
> 难度：入门 | 运行时间：即时 | 涉及概念：LLM API、Web UI、多轮对话

## 运行效果

启动后浏览器打开 `http://192.168.2.16:7860`，可以看到一个聊天界面：
- 输入框输入问题，AI 自动回答
- 可以切换模型（1.5b 快但笨，7b 慢但聪明）
- 可以修改系统提示词改变 AI 的性格

```bash
# 在 VM2 上运行
ssh llm2@192.168.2.16
cd ~/demos
python3 demo1_chat_ui.py
```

---

## 完整代码逐行讲解

### 第一部分：导入和配置

```python
import gradio as gr
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

OLLAMA_BASE = "http://192.168.2.15:11434/v1"
```

**逐行解释：**

| 代码 | 作用 | 为什么需要 |
|------|------|-----------|
| `import gradio as gr` | 导入 Gradio 库 | 用来快速搭建 Web UI，不用写前端代码 |
| `from langchain_openai import ChatOpenAI` | 导入 ChatOpenAI 类 | 这是和 LLM 对话的核心类。虽然叫 "OpenAI"，但 Ollama 兼容 OpenAI 的 API 格式，所以用它连接 Ollama |
| `from langchain_core.messages import ...` | 导入消息类型 | LLM 对话需要区分"谁说的"：用户说的(HumanMessage)、AI 说的(AIMessage)、系统指令(SystemMessage) |
| `OLLAMA_BASE = "..."` | 定义 Ollama API 地址 | `/v1` 是 OpenAI 兼容接口的路径，所有请求都发到这里 |

**关键理解：** LangChain 的 `ChatOpenAI` 虽然名字里有 "OpenAI"，但只要目标服务兼容 OpenAI 的 API 格式（Ollama 就兼容），就能用同一个类连接不同的 LLM 服务。这就是"接口抽象"的好处。

---

### 第二部分：创建 LLM 实例

```python
def build_llm(model="qwen2.5:7b"):
    return ChatOpenAI(
        base_url=OLLAMA_BASE,
        api_key="ollama",
        model=model,
        temperature=0.7,
    )
```

**逐行解释：**

| 参数 | 含义 | 可选值 |
|------|------|--------|
| `base_url` | LLM 服务的地址 | 指向 Ollama 的 OpenAI 兼容接口 |
| `api_key` | API 密钥 | Ollama 不需要密钥，但参数不能为空，随便填 "ollama" |
| `model` | 使用哪个模型 | "qwen2.5:1.5b"（快）或 "qwen2.5:7b"（准） |
| `temperature` | 创造性程度 | 0=确定性回答，1=更有创意，0.7 是平衡值 |

**为什么封装成函数？** 因为用户可以在界面上切换模型，每次切换需要创建一个新的 LLM 实例。如果写死在代码里就没法动态切换了。

**temperature 的直觉理解：**
```
temperature=0   -> "中国的首都是？" -> "北京"（每次都一样）
temperature=0.7 -> "中国的首都是？" -> "中国的首都是北京，这是一座..."（可能每次略有不同）
temperature=1.0 -> "写一首诗" -> 每次写出完全不同的诗
```

---

### 第三部分：核心对话逻辑

```python
def chat(message, history, model_choice, system_prompt):
    llm = build_llm(model=model_choice)

    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))

    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=message))

    response = llm.invoke(messages)
    return response.content
```

**这是整个 demo 最核心的函数。** 逐行解释：

**函数参数（由 Gradio 自动传入）：**

| 参数 | 来源 | 示例 |
|------|------|------|
| `message` | 用户在输入框输入的内容 | "你好" |
| `history` | 之前的对话历史，Gradio 6.x 格式为字典列表 | `[{"role":"user","content":"你好"}, {"role":"assistant","content":"你好！"}]` |
| `model_choice` | 界面上选择的模型 | "qwen2.5:7b" |
| `system_prompt` | 系统提示词文本框的内容 | "你是一个有帮助的AI助手" |

**代码逻辑分解：**

```
步骤1: 根据用户选择的模型创建 LLM 实例
    └── build_llm(model="qwen2.5:7b")

步骤2: 构建消息列表
    ├── 先加入系统提示词（定义 AI 的角色和行为）
    ├── 遍历 history 字典列表，按 role 区分用户/AI 消息
    └── 最后加入当前用户消息

步骤3: 调用 LLM 获取回答
    └── llm.invoke(messages) -> 返回一个 AIMessage 对象

步骤4: 返回纯文本回答
    └── response.content -> "你好！有什么可以帮你的吗？"
```

**注意 Gradio 版本差异：**
- Gradio 3.x：`history` 是元组列表 `[("你好", "你好！"), ...]`
- Gradio 6.x：`history` 是字典列表 `[{"role":"user","content":"你好"}, ...]`
- 本 demo 使用 Gradio 6.26.0，按字典格式读取

**为什么需要 history？** LLM 本身没有记忆。每次调用都是独立的。要实现"多轮对话"，必须把之前的对话内容每次都传给 LLM，让它"回忆"之前说了什么。

```
第1轮: [系统提示, 用户:"你好"]                    -> AI:"你好！"
第2轮: [系统提示, 用户:"你好", AI:"你好！", 用户:"你是谁"] -> AI:"我是AI助手"
第3轮: [系统提示, 用户:"你好", AI:"你好！", 用户:"你是谁", AI:"我是AI助手", 用户:"记住我"]
```

---

### 第四部分：搭建界面

```python
demo = gr.ChatInterface(
    fn=chat,
    title="LLM Chat - Ollama + LangChain",
    description="连接本地 Ollama 的聊天机器人",
    additional_inputs=[
        gr.Radio(choices=["qwen2.5:1.5b", "qwen2.5:7b"],
                 value="qwen2.5:7b", label="选择模型"),
        gr.Textbox(value="你是一个有帮助的AI助手，请用中文回答。",
                   label="系统提示词", lines=2),
    ],
    examples=[["用简单的语言解释什么是机器学习"], ["写一首关于编程的诗"]],
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

**参数解释：**

| 参数 | 作用 |
|------|------|
| `fn=chat` | 指定处理函数，Gradio 会在用户发消息时调用 `chat()` |
| `title` | 页面标题 |
| `description` | 标题下方的说明文字 |
| `additional_inputs` | 除了聊天输入框之外的额外控件（模型选择、系统提示词） |
| `examples` | 预设的示例问题，点击即可快速提问 |
| `server_name="0.0.0.0"` | 监听所有网卡，允许从其他机器访问 |
| `server_port=7860` | 监听端口 |

**Gradio 的魔力：** 你只需要写一个 Python 函数（`chat`），Gradio 自动帮你生成完整的 Web 界面。`additional_inputs` 里的控件会自动传给 `chat()` 函数的对应参数。

---

## 数据流全景图

```
浏览器                           VM2 (192.168.2.16)              VM1 (192.168.2.15)
┌──────────┐                   ┌──────────────────┐             ┌──────────────┐
│  用户输入  │──HTTP──>         │  Gradio 服务      │             │              │
│  "你好"   │                   │  收到请求         │             │              │
│          │                   │       │           │             │              │
│          │                   │       v           │             │              │
│          │                   │  chat() 函数      │             │              │
│          │                   │  构建 messages    │             │              │
│          │                   │       │           │             │              │
│          │                   │       v           │──HTTP──>   │  Ollama      │
│          │                   │  llm.invoke()     │  /v1/...   │  qwen2.5:7b  │
│          │                   │       │           │<──HTTP──   │  推理生成     │
│          │                   │       v           │  返回回答    │              │
│          │                   │  return 回答      │             │              │
│  显示回答  │<──HTTP──         │       │           │             │              │
│ "你好！"  │                   │       v           │             │              │
└──────────┘                   │  返回给浏览器     │             └──────────────┘
                               └──────────────────┘
```

---

## 动手练习

### 练习 1：修改默认模型（难度：★）

**目标：** 把默认模型从 7b 改为 1.5b，体验速度差异。

**操作：** 找到这行代码，修改 value 参数：
```python
# 修改前
gr.Radio(choices=["qwen2.5:1.5b", "qwen2.5:7b"], value="qwen2.5:7b", ...)
# 修改后
gr.Radio(choices=["qwen2.5:1.5b", "qwen2.5:7b"], value="qwen2.5:1.5b", ...)
```

**思考：** 同一个问题，1.5b 和 7b 的回答质量有什么区别？

---

### 练习 2：添加流式输出（难度：★★）

**目标：** 让回答像 ChatGPT 一样逐字显示，而不是一次性返回。

**提示：** 把 `chat()` 函数改为 `yield` 生成器：
```python
def chat(message, history, model_choice, system_prompt):
    llm = build_llm(model=model_choice)
    # ... 构建 messages ...

    # 使用 stream 模式
    full_response = ""
    for chunk in llm.stream(messages):
        full_response += chunk.content
        yield full_response  # 每次 yield 都会更新界面
```

**关键概念：** `yield` vs `return`
- `return`：函数执行完毕，一次性返回所有结果
- `yield`：函数可以多次产出值，每次产出一个就发给调用方

---

### 练习 3：添加角色设定（难度：★★）

**目标：** 预设几个角色，用户选择后 AI 以该角色身份回答。

**思路：** 在 `additional_inputs` 中添加一个角色选择下拉框：
```python
gr.Dropdown(
    choices=["通用助手", "Python老师", "段子手", "诗人"],
    value="通用助手",
    label="选择角色"
)
```

然后在 `chat()` 函数中根据角色生成不同的 system_prompt：
```python
role_prompts = {
    "通用助手": "你是一个有帮助的AI助手。",
    "Python老师": "你是一个Python编程老师，用简单易懂的方式教学。",
    "段子手": "你是一个幽默的段子手，用搞笑的方式回答问题。",
    "诗人": "你是一个诗人，尽量用诗意的语言回答。",
}
system_prompt = role_prompts[role_choice]
```

---

### 练习 4：添加对话历史持久化（难度：★★★）

**目标：** 刷新页面后对话历史不丢失。

**思路：**
1. 把 history 保存到 JSON 文件
2. 每次新对话时从文件加载
3. 每次回答后追加保存到文件

```python
import json

HISTORY_FILE = "/tmp/chat_history.json"

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def load_history():
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return []
```

---

### 练习 5：不用 LangChain，直接调用 Ollama API（难度：★★）

**目标：** 理解 LangChain 底层到底做了什么。

**用 requests 库直接调用 Ollama API：**
```python
import requests

def chat_direct(message, history):
    # 构建 Ollama 的 /api/chat 接口请求
    messages = []
    for user_msg, ai_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": ai_msg})
    messages.append({"role": "user", "content": message})

    response = requests.post(
        "http://192.168.2.15:11434/api/chat",
        json={"model": "qwen2.5:7b", "messages": messages, "stream": False}
    )
    return response.json()["message"]["content"]
```

**思考：** LangChain 的 `ChatOpenAI` 帮你做了什么？（提示：API 格式转换、错误处理、重试、流式输出等）

---

## 常见问题

**Q: 为什么用 `ChatOpenAI` 连接 Ollama 而不是直接用 Ollama 的 API？**
A: LangChain 提供了统一的接口。如果你以后换成 OpenAI、Claude 或其他 LLM，只需要改 `base_url` 和 `api_key`，其他代码不用动。

**Q: `temperature` 设多少合适？**
A: 事实问答用 0（需要准确），创意写作用 0.7-1.0（需要多样性），日常对话 0.5-0.7。

**Q: 为什么 1.5b 模型回答质量差？**
A: 参数量决定了模型的理解和生成能力。1.5b 只有 15 亿参数，7b 有 76 亿。小模型适合快速测试，大模型适合正式使用。

**Q: Gradio 的 `additional_inputs` 参数顺序重要吗？**
A: 重要！它们按顺序传给 `chat()` 函数的对应参数。`additional_inputs` 列表中的第一个控件对应 `chat()` 的第三个参数（前两个是 `message` 和 `history`，由 ChatInterface 自动管理）。
