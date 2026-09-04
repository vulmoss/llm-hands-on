"""
Demo 3: Agent 工具调用
=======================
用 LangChain 实现一个能调用自定义工具的 AI Agent。
Agent 可以根据用户问题自动选择并调用合适的工具。

工具示例：
- 计算器：执行数学运算
- 知识查询：查询预设的知识库
- 单位转换：常见单位换算

用法:
    python3 demo3_agent.py
"""

import math
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

OLLAMA_BASE = "http://192.168.2.15:11434/v1"

# ===== 1. 定义工具 =====

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


@tool
def knowledge_base(query: str) -> str:
    """查询本地知识库。可以查询关于 LLM 推理学习环境、Ollama、LangChain 的信息。"""
    knowledge = {
        "ollama": "Ollama v0.32.14 通过 snap 安装在 VM1 (192.168.2.15) 上。API 地址: http://192.168.2.15:11434。已安装模型: qwen2.5:1.5b 和 qwen2.5:7b。配置: host=0.0.0.0, num-parallel=2。",
        "环境": "LLM推理学习环境部署在 ESXi 6.7.0 上。VM1(llm-inference): 16vCPU/64GB RAM, 运行 Ollama。VM2(llm-dev): 8vCPU/32GB RAM, Python开发环境。两台VM在 data_sata  datastore上。",
        "langchain": "LangChain 1.3.18 安装在 VM2 上。通过 langchain-openai 包连接 Ollama。配合 ChromaDB 1.5.9 和 FAISS-CPU 1.15.0 做向量检索。",
        "模型": "已安装两个模型: qwen2.5:1.5b (986MB, 适合快速测试) 和 qwen2.5:7b (4.7GB, 更准确)。都是 Q4_K_M 量化, 32768 上下文长度。CPU推理, 无GPU。",
    }
    query_lower = query.lower()
    results = []
    for key, value in knowledge.items():
        if key in query_lower or any(word in query_lower for word in key.split()):
            results.append(value)
    if results:
        return "\n\n".join(results)
    return "未找到相关信息。知识库涵盖: ollama, 环境, langchain, 模型"


# ===== 2. 创建 Agent =====

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

# ===== 3. 测试 Agent =====

SYSTEM_HINT = "请用中文回答。"

test_questions = [
    f"计算 (15 + 27) * 3 - 18 的结果。{SYSTEM_HINT}",
    f"100 公里等于多少英里？{SYSTEM_HINT}",
    f"这个 LLM 学习环境是怎么配置的？{SYSTEM_HINT}",
    f"帮我算一下 2 的 10 次方，然后把结果从 MB 转换成 GB（假设结果是 MB）。{SYSTEM_HINT}",
]

print("=" * 60)
print("Agent 工具调用 Demo")
print("=" * 60)

for q in test_questions:
    print(f"\n用户: {q}")
    print("-" * 40)
    try:
        result = agent.invoke({"messages": [("user", q)]})
        final_msg = result["messages"][-1]
        print(f"助手: {final_msg.content}")
    except Exception as ex:
        print(f"(Agent 执行出错: {ex})")
    print("=" * 40)

print("\nDemo 完成！Agent 会自动判断是否需要调用工具。")
