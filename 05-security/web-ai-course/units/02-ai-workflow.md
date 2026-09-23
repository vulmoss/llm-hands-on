# 02 · AI 辅助证据分析

目标：把模型当审阅员，并能检查它的结论。先修：单元 01。

```bash
python3 -m llm_lab.web_security run --lab idor --output .data/web-ai-course/idor.json
python3 -m llm_lab.web_security review --evidence .data/web-ai-course/idor.json
export OLLAMA_BASE_URL=http://192.168.2.15:11434
export OLLAMA_MODEL=qwen2.5:1.5b
export OLLAMA_TIMEOUT=180
export LLM_MAX_TOKENS=768
python3 -m llm_lab.web_security review --evidence .data/web-ai-course/idor.json --live
```

第一条产出证据；第二条只显示提示消息；最后一条才发送给 Ollama。查看 `src/llm_lab/web_security/__main__.py` 的 `review_prompt`，理解 system 约束与 user 证据分开。结构分开能表达意图，但不是模型绝不会被注入的保证。代码没有给模型注册任何 shell、网络扫描或文件修改工具。

人工复核草稿：每句话标记“响应直接支持 / 根据实现推断 / 尚待验证”。例如：返回 B-book 是事实；原因是缺所有权判断需要结合源码；“能接管管理员”在本例没有证据。模型没有获得完整请求头，因此 CORS 审阅尤其不能替代原始证据。

工作流：明确问题 → 最小请求 → 正常/异常对照 → 证据存档 → 人工根因 → 模型检查遗漏 → 再验证。资产清单可以按服务、入口、身份、数据类型、风险假设五列维护。AI 可以整理清单，但不会自动获得资产授权。

产物：原始 JSON、模型名、草稿、至少一条人工纠正。进阶：同一证据分别使用 1.5B 和 7B，比较有证据结论数量、臆测数量、耗时；每次只发一条请求，不能由一次结果宣称某模型最强。

下一课：[前端入口](03-frontend.md)。
