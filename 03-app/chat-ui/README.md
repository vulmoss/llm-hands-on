# 聊天：消息、历史与流式输出

先读 `examples/01_direct_http.py`，然后读 `src/llm_lab/chat.py` 和 `ui.py`。

```bash
python examples/01_direct_http.py
python examples/02_chat.py
llm-lab chat
python -m pip install -e '.[ui]'
llm-lab ui
```

数据流：用户输入 → 系统提示词 + 历史 + 当前问题 → `/api/chat` → 文本片段 → 界面。
`OllamaClient.stream()` 产出增量文本，网页回调累计文本后 `yield`；这不意味着每块恰好一个 Token。

## 练习

1. 第一轮说“我在学 Python”，第二轮问“我学什么”。删除历史再试。
2. 用相同问题比较不同系统提示词，每种重复三次，记录变化。
3. 比较 `llm-lab ask` 与 `--stream` 的体验，区分首段输出时间与总完成时间。
4. 设置 `LLM_HISTORY_TURNS=1`，进行三轮对话，打印实际消息列表。
5. 在网页保存会话并刷新页面，验证浏览器历史恢复；新建会话验证上下文不串用。

## 边界

历史由 CLI 会话或浏览器持有，核心模块没有全局聊天记录。
Gradio 的保存历史在浏览器本地，不是跨设备账号存储；在共用浏览器时自行清理会话。
API 调用者需要显式传入 history。历史按轮数裁剪，不是精确 Token 预算。
当前支持文本消息，附件会得到明确错误。

旧入口 `python 03-app/chat-ui/demo1_chat_ui.py` 和 `app.py` 都启动同一个 UI。
必须先安装项目及 `ui` extra，或设置 `PYTHONPATH=src`。
