# Demo3: Agent 工具调用 - 逐行讲解

> 目标：让 AI 不仅能聊天，还能"动手做事"——调用计算器、查知识库、做单位转换。
> 难度：中级 | 运行时间：~20秒 | 涉及概念：Tool、Agent、ReAct 模式、LangGraph

## 什么是 Agent？

```
普通 LLM:
  用户: "计算 123 * 456"
  LLM: "123 * 456 = 56088"  ← 可能算错！LLM 不擅长精确计算

Agent:
  用户: "计算 123 * 456"
  Agent 思考: "这需要精确计算，我应该用计算器工具"
  Agent 行动: 调用 calculator("123 * 456")
  工具返回: "123 * 456 = 56088"
  Agent 回答: "123 乘以 456 等于 56088"  ← 100% 准确
```

**核心区别：** Agent 能根据问题**自主决定**是否使用工具、使用哪个工具。

---

## 运行方式

```bash
# 在 VM2 上运行
ssh llm2@192.168.2.16
cd ~/demos
python3 demo3_agent.py
```

---

## 完整代码逐段讲解

### 第一部分：导入模块

```python
import math
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
```

| 导入 | 作用 |
|------|------|
| `math` | Python 标准数学库，给计算器工具用 |
| `ChatOpenAI` | LLM 对话类（和 demo1 一样） |
| `@tool` | 装饰器，把普通 Python 函数变成 Agent 可调用的工具 |
| `create_react_agent` | 创建一个 ReAct 模式的 Agent |

**什么是 ReAct？**
ReAct = Reasoning + Acting（推理 + 行动）

```
用户问题 → LLM 思考(Reason) → 决定行动(Act) → 观察结果(Observe) → 再思考 → ... → 最终回答
```

这个循环会一直进行，直到 Agent 认为已经收集到足够信息可以回答。

---

### 第二部分：定义工具

Agent 的能力完全取决于你给它什么工具。这里定义了 3 个工具。

#### 工具 1：计算器

```python
@tool
def calculator(expression: str) -> str:
    """计算数学表达式。输入一个数学表达式字符串，如 '2 + 3 * 4' 或 'sqrt(16)'。
    支持: +, -, *, /, **, sqrt, sin, cos, tan, log, pi, e"""
    try:
        safe_expr = expression.replace("^", "**")
        allowed = {
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "pi": math.pi,
            "e": math.e,
            "abs": abs,
            "pow": pow,
        }
        result = eval(safe_expr, {"__builtins__": {}}, allowed)
        return f"{expression} = {result}"
    except Exception as ex:
        return f"计算错误: {ex}"
```

**关键点解析：**

**`@tool` 装饰器做了什么？**
1. 把函数变成 LangChain 的 `Tool` 对象
2. **函数的 docstring（"""..."""）会变成工具的描述**，Agent 靠它理解工具能做什么
3. 参数类型注解（`expression: str`）会告诉 Agent 该传什么类型的参数

**为什么 docstring 如此重要？**

```python
# Agent 看到的不是代码，而是这个描述：
"""计算数学表达式。输入一个数学表达式字符串，如 '2 + 3 * 4' 或 'sqrt(16)'。
支持: +, -, *, /, **, sqrt, sin, cos, tan, log, pi, e"""
```

Agent 根据这段描述判断：
- 这个工具能做什么？→ 计算数学表达式
- 输入什么参数？→ 一个字符串形式的数学表达式
- 什么时候该用它？→ 需要精确计算时

**如果 docstring 写得含糊，Agent 就不知道什么时候该调用这个工具。**

**eval() 的安全处理：**

```python
eval(safe_expr, {"__builtins__": {}}, allowed)
#         ↑           ↑                    ↑
#     表达式      禁用所有内置函数      只允许白名单函数
```

`eval()` 默认可以执行任何 Python 代码，非常危险。这里：
- `{"__builtins__": {}}`：禁用 `open()`、`import`、`exec()` 等所有内置功能
- `allowed`：只允许白名单里的数学函数

这样即使输入恶意表达式也无法执行危险操作。

---

#### 工具 2：单位转换器

```python
@tool
def unit_converter(value: float, from_unit: str, to_unit: str) -> str:
    """单位转换。支持: km->miles, miles->km, kg->lbs, lbs->kg, c->f (摄氏转华氏), f->c"""
    conversions = {
        ("km", "miles"): lambda v: v * 0.621371,
        ("miles", "km"): lambda v: v * 1.60934,
        ("kg", "lbs"): lambda v: v * 2.20462,
        ("lbs", "kg"): lambda v: v * 0.453592,
        ("c", "f"): lambda v: v * 9 / 5 + 32,
        ("f", "c"): lambda v: (v - 32) * 5 / 9,
        ("m", "ft"): lambda v: v * 3.28084,
        ("ft", "m"): lambda v: v / 3.28084,
        ("gb", "mb"): lambda v: v * 1024,
        ("mb", "gb"): lambda v: v / 1024,
    }
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        result = conversions[key](value)
        return f"{value} {from_unit} = {result:.4f} {to_unit}"
    return f"不支持的转换: {from_unit} -> {to_unit}。支持: km/miles, kg/lbs, c/f, m/ft, gb/mb"
```

**注意参数类型：** `value: float, from_unit: str, to_unit: str`

Agent 会根据类型注解来构造参数。当用户说"100公里等于多少英里"时，Agent 会：
1. 识别出需要单位转换
2. 提取参数：`value=100.0, from_unit="km", to_unit="miles"`
3. 调用 `unit_converter(100.0, "km", "miles")`

**多参数工具的挑战：** Agent 需要从自然语言中正确提取多个参数。如果用户说"把 100 公里转成英里"，Agent 需要理解：
- 100 → value
- 公里 → km → from_unit
- 英里 → miles → to_unit

---

#### 工具 3：知识库查询

```python
@tool
def knowledge_base(query: str) -> str:
    """查询本地知识库。可以查询关于 LLM 推理学习环境、Ollama、LangChain 的信息。"""
    knowledge = {
        "ollama": "Ollama v0.32.14 通过 snap 安装在 VM1...",
        "环境": "LLM推理学习环境部署在 ESXi 6.7.0 上...",
        "langchain": "LangChain 1.3.18 安装在 VM2 上...",
        "模型": "已安装两个模型: qwen2.5:1.5b 和 qwen2.5:7b...",
    }
    query_lower = query.lower()
    results = []
    for key, value in knowledge.items():
        if key in query_lower or any(word in query_lower for word in key.split()):
            results.append(value)
    if results:
        return "\n\n".join(results)
    return "未找到相关信息。知识库涵盖: ollama, 环境, langchain, 模型"
```

**这个工具模拟了什么？** 实际项目中，这个工具可以：
- 查询数据库
- 调用内部 API
- 搜索文档
- 访问文件系统

**匹配逻辑：** 简单的关键词匹配。如果 query 中包含 key（如 "ollama"）或 key 的任一分词，就返回对应信息。

---

### 第三部分：创建 Agent

```python
tools = [calculator, unit_converter, knowledge_base]

llm = ChatOpenAI(
    base_url=OLLAMA_BASE,
    api_key="ollama",
    model="qwen2.5:7b",
    temperature=0,
)

agent = create_react_agent(
    model=llm,
    tools=tools,
)
```

**create_react_agent 做了什么？**

它创建了一个有状态的 Agent，内部维护一个消息列表：

```
消息列表的演变过程:

初始状态:
  [用户消息: "计算 123 * 456"]

Agent 思考后:
  [用户消息: "计算 123 * 456",
   AI消息: 我需要调用 calculator 工具,
   ToolMessage: "123 * 456 = 56088"]

Agent 最终回答:
  [用户消息: "计算 123 * 456",
   AI消息: 我需要调用 calculator 工具,
   ToolMessage: "123 * 456 = 56088",
   AI消息: "123 乘以 456 等于 56088"]
```

**temperature=0 的原因：** Agent 需要稳定地选择工具，不需要创造性。如果 temperature 太高，Agent 可能会做出不合理的工具选择。

---

### 第四部分：测试 Agent

```python
SYSTEM_HINT = "请用中文回答。"

test_questions = [
    f"计算 (15 + 27) * 3 - 18 的结果。{SYSTEM_HINT}",
    f"100 公里等于多少英里？{SYSTEM_HINT}",
    f"这个 LLM 学习环境是怎么配置的？{SYSTEM_HINT}",
    f"帮我算一下 2 的 10 次方，然后把结果从 MB 转换成 GB（假设结果是 MB）。{SYSTEM_HINT}",
]
```

**为什么需要 SYSTEM_HINT？**

因为 `create_react_agent` 在当前版本中没有 system prompt 参数，所以把"请用中文回答"直接附加在每个问题后面。

**第 4 个问题是多步推理：**

```
用户: "帮我算一下 2 的 10 次方，然后把结果从 MB 转换成 GB"

Agent 的执行过程:
  步骤1: 调用 calculator("2 ** 10")
  结果: "2 ** 10 = 1024"

  步骤2: 调用 unit_converter(1024.0, "mb", "gb")
  结果: "1024.0 mb = 1.0000 gb"

  步骤3: 综合两个工具的结果，给出最终回答
```

---

### 第五部分：调用 Agent

```python
for q in test_questions:
    print(f"\n用户: {q}")
    print("-" * 40)
    try:
        result = agent.invoke({"messages": [("user", q)]})
        final_msg = result["messages"][-1]
        print(f"助手: {final_msg.content}")
    except Exception as ex:
        print(f"(Agent 执行出错: {ex})")
```

**invoke 的参数格式：**

```python
agent.invoke({"messages": [("user", q)]})
#            ↑         ↑      ↑
#         消息列表   角色    内容
```

- `messages`：消息列表，格式为 `[(角色, 内容), ...]`
- `("user", q)`：一条用户消息
- `result["messages"]`：返回完整的消息列表（包含中间的工具调用过程）
- `[-1]`：取最后一条消息，即 Agent 的最终回答

---

## Agent 决策流程图

```
                    Agent 的思考和行动循环

                    ┌──────────────────┐
                    │   用户提出问题    │
                    └────────┬─────────┘
                             │
                             v
                    ┌──────────────────┐
                    │  LLM 分析问题     │
                    │  "我需要用什么    │
                    │   工具？"         │
                    └────────┬─────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
              需要工具            不需要工具
                    │                 │
                    v                 v
          ┌─────────────────┐  ┌──────────────┐
          │ 选择并调用工具   │  │ 直接生成回答  │
          │ (如 calculator) │  │              │
          └────────┬────────┘  └──────────────┘
                   │
                   v
          ┌─────────────────┐
          │ 观察工具返回结果 │
          └────────┬────────┘
                   │
                   v
          ┌─────────────────┐
          │ 还需要更多工具吗？│
          └───┬─────────┬───┘
              │         │
            是         否
              │         │
              v         v
        回到"选择工具"  生成最终回答
```

---

## 动手练习

### 练习 1：添加一个新工具（难度：★）

**目标：** 给 Agent 添加一个"天气查询"工具（模拟数据）。

```python
@tool
def weather_checker(city: str) -> str:
    """查询指定城市的当前天气。输入城市名称，如 '北京'、'上海'。"""
    weather_data = {
        "北京": "晴，25°C，湿度 40%",
        "上海": "多云，28°C，湿度 65%",
        "广州": "小雨，30°C，湿度 80%",
        "深圳": "阴，27°C，湿度 70%",
    }
    if city in weather_data:
        return f"{city}的天气: {weather_data[city]}"
    return f"暂无{city}的天气数据。支持的城市: {', '.join(weather_data.keys())}"
```

然后把工具加入列表：

```python
tools = [calculator, unit_converter, knowledge_base, weather_checker]
```

重新创建 agent 并测试：

```python
agent = create_react_agent(model=llm, tools=tools)
result = agent.invoke({"messages": [("user", "北京今天天气怎么样？请用中文回答。")]})
```

---

### 练习 2：添加时间查询工具（难度：★）

**目标：** 让 Agent 能回答"现在几点"之类的问题。

```python
from datetime import datetime

@tool
def time_checker(query: str) -> str:
    """查询当前日期和时间。可以问'现在几点'、'今天星期几'、'今天日期'等。"""
    now = datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return (
        f"当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}\n"
        f"今天是{weekdays[now.weekday()]}"
    )
```

---

### 练习 3：创建一个能调用多个工具的问题（难度：★★）

**目标：** 设计一个问题，需要 Agent 依次调用 2 个以上的工具才能回答。

**示例问题：**

```python
questions = [
    "帮我算一下，如果 VM1 有 16 个 vCPU，每个 vCPU 能处理 2.5 个请求/秒，"
    "那一分钟能处理多少个请求？把结果从'个'转换成'千个'（除以1000）。",
    # Agent 需要: 1) calculator 算 16*2.5*60  2) unit_converter 转换
]
```

**思考：** Agent 是如何决定工具调用顺序的？如果顺序错了会怎样？

---

### 练习 4：实现一个真正的文件搜索工具（难度：★★★）

**目标：** 让 Agent 能搜索 VM2 上的文件内容。

```python
import os

@tool
def file_searcher(pattern: str) -> str:
    """在 ~/demos 目录下搜索包含指定内容的文件。输入要搜索的关键词。"""
    search_dir = os.path.expanduser("~/demos")
    results = []

    for filename in os.listdir(search_dir):
        filepath = os.path.join(search_dir, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, "r") as f:
                    content = f.read()
                    if pattern in content:
                        # 找到包含 pattern 的行
                        matching_lines = [
                            line.strip()
                            for line in content.split("\n")
                            if pattern in line
                        ]
                        results.append(
                            f"文件: {filename}\n"
                            f"匹配行 ({len(matching_lines)} 行):\n"
                            + "\n".join(matching_lines[:5])  # 最多显示5行
                        )
            except Exception:
                continue

    if results:
        return "\n\n".join(results)
    return f"在 {search_dir} 下未找到包含 '{pattern}' 的文件"
```

**安全提示：** 这个工具限制了搜索范围在 `~/demos` 目录内。永远不要让 Agent 能随意读写系统文件。

---

### 练习 5：观察 Agent 的推理过程（难度：★★）

**目标：** 打印 Agent 的完整思考过程，理解它如何决策。

```python
result = agent.invoke({"messages": [("user", "计算 2**10 然后转成 GB。请用中文回答。")]})

print("=== Agent 完整执行过程 ===")
for i, msg in enumerate(result["messages"]):
    print(f"\n--- 消息 {i+1} ---")
    print(f"类型: {type(msg).__name__}")
    print(f"内容: {msg.content if hasattr(msg, 'content') else msg}")

    # 如果是 AI 消息，检查是否有工具调用
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tc in msg.tool_calls:
            print(f"  工具调用: {tc['name']}({tc['args']})")
```

**预期输出：**

```
=== Agent 完整执行过程 ===

--- 消息 1 ---
类型: HumanMessage
内容: 计算 2**10 然后转成 GB。请用中文回答。

--- 消息 2 ---
类型: AIMessage
内容:
  工具调用: calculator({'expression': '2**10'})

--- 消息 3 ---
类型: ToolMessage
内容: 2**10 = 1024

--- 消息 4 ---
类型: AIMessage
内容:
  工具调用: unit_converter({'value': 1024.0, 'from_unit': 'mb', 'to_unit': 'gb'})

--- 消息 5 ---
类型: ToolMessage
内容: 1024.0 mb = 1.0000 gb

--- 消息 6 ---
类型: AIMessage
内容: 2 的 10 次方等于 1024，转换为 GB 是 1.0000 GB。
```

---

## 工具定义速查表

| 要素 | 说明 | 示例 |
|------|------|------|
| `@tool` | 装饰器，标记函数为工具 | `@tool` |
| docstring | Agent 理解工具用途的唯一途径 | `"""计算数学表达式..."""` |
| 参数类型注解 | Agent 根据类型构造参数 | `value: float, unit: str` |
| 返回值 | 必须是字符串，Agent 会读取并理解 | `return f"结果是 {result}"` |
| 错误处理 | 工具出错不要抛异常，返回错误信息 | `return f"计算错误: {ex}"` |

---

## 常见问题

**Q: Agent 怎么知道该用哪个工具？**
A: 它读取每个工具的 docstring（描述），然后根据你的问题判断哪个工具最合适。这就是为什么 docstring 必须写得清晰准确。

**Q: 如果 Agent 选错了工具怎么办？**
A: 小模型（如 qwen2.5:7b）有时会选错。改善方法：
1. 让工具的 docstring 更明确（说明什么时候该用、什么时候不该用）
2. 用更大的模型
3. 减少工具数量（工具太多容易混淆）

**Q: 工具可以调用其他工具吗？**
A: 不建议。工具应该是独立的、原子化的操作。复杂的编排由 Agent 自己完成。

**Q: 为什么用 `create_react_agent` 而不是自己写循环？**
A: `create_react_agent` 封装了 ReAct 循环的所有细节：消息管理、工具调用解析、错误重试、停止条件判断。自己写很容易出 bug。

**Q: 工具执行出错了怎么办？**
A: 工具函数内部应该 try/except 捕获所有异常，返回错误信息字符串。Agent 看到错误信息后会尝试其他方式或告诉用户。

**Q: 怎么限制 Agent 的工具调用次数？**
A: 在 `create_react_agent` 中传入 `recursion_limit` 参数：
```python
agent = create_react_agent(
    model=llm,
    tools=tools,
    recursion_limit=10,  # 最多执行 10 步
)
```

---

## 下一步学习

掌握了 Agent 基础后，可以继续学习：

1. **自定义 Agent 提示词**：控制 Agent 的行为风格和决策策略
2. **记忆（Memory）**：让 Agent 记住跨会话的对话历史
3. **多 Agent 协作**：多个 Agent 分工合作完成复杂任务
4. **工具的高级用法**：数据库查询、API 调用、文件操作等真实工具
5. **LangGraph 状态图**：用图结构定义更复杂的 Agent 工作流
