# 从旧版三个 demo 迁移

## 主要变化

| 旧版 | 新版 |
|---|---|
| 每份脚本写死 VM1 IP、模型 | `.env.example` + Settings，环境变量统一覆盖 |
| ChatOpenAI → Ollama `/v1` | 标准库 HTTP → Ollama `/api/chat` |
| LangChain + Chroma 的内存 demo | 显式 RAG + 可查看的 JSON 持久化索引 |
| LangGraph 隐式 Agent 循环 | 有调用预算的 Python 循环 |
| eval 表达式计算 | operation、a、b 三参数计算工具 |
| app.py 混放主程序和练习 | `examples/` 独立课程，`src/` 共用业务实现 |
| 运行时才发现缺失依赖 | pyproject 可选依赖 + doctor + 测试 |

这是教学主线的重新组织，并不是原框架代码的逐项 API 兼容实现。
向量索引需要重新构建。先保留现有 Ollama 模型，再按需要做对比实验。

## 地址与入口

`OLLAMA_BASE_URL` 填根地址，不加 `/v1`。旧脚本没有实际读取的 `OLLAMA_HOST`
现在也不作为应用配置读取，避免与 Ollama 服务端的配置语义混淆。

```bash
python -m pip install -e '.[ui]'
export OLLAMA_BASE_URL=http://192.168.2.15:11434
python 03-app/chat-ui/demo1_chat_ui.py
llm-lab index data/notes
python 03-app/rag/demo2_rag.py '推理服务负责什么？'
python 03-app/agent/demo3_agent.py '100 公里是多少英里？' --trace
```

旧路径只是调用统一 CLI，不再保存独立业务逻辑。旧版 `~/demos` 文件如果不在仓库中，
不会被本次修改自动更新，需要在开发机拉取此项目并安装。

## 文档修正

删除了量化固定精度百分比、工具保证 100% 正确、eval 清空内置函数即可安全等说明。
计时区分输入处理、客户端首段文本和总耗时。单位换算明确区分 GB/MB 与 GiB/MiB。
原有基础设施文件是历史操作记录，不代表当前主机检测结果，也不是学习应用的必需前置步骤。
