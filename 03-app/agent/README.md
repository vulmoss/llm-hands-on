# Agent：把工具循环展开来看

```bash
llm-lab agent '计算 2 的 10 次方，假设单位为 MiB，再转成 GiB。' --trace
llm-lab index data/notes
llm-lab agent '查询笔记：应用负责哪些事情？' --with-notes --trace
```

阅读 `src/llm_lab/tools.py`，再读 `agent.py`。

```text
用户问题 → 模型返回 tool_calls → 按名字查注册表
        → 校验参数 → 执行 Python 函数 → 追加 tool 消息
        → 再请求模型 → 最终答案或达到工具次数上限
```

模型看到工具名称、描述和 JSON 参数结构，并提出调用。
应用才真正执行函数。`trace` 展示可观察的名称、参数和结果，不等于模型内部思维。

## 已有工具

- `calculator(operation, a, b)`：加、减、乘、除、幂。没有 `eval`。
- `unit_converter(value, from_unit, to_unit)`：支持明确列出的单位组合。
- `search_notes(query)`：CLI 指定 `--with-notes` 后启用，只检索已经构建的索引。

GB/MB 使用 1000，GiB/MiB 使用 1024。复杂表达式拆成多次调用。
普通输入错误以 `{ok: false, error: ...}` 返回模型；服务连接错误传回入口层。
程序对同一响应内的多个调用也逐个计数，最多执行 `LLM_MAX_TOOL_CALLS` 次。
达到预算后不会继续执行工具，返回 `stopped: true`。

## 练习与验收

1. 直接调用普通工具函数，测试除以零、不支持的单位和错误类型。
2. 只注册一个工具，观察模型是否正确提取参数。
3. 测试多步计算，逐项核对调用顺序、参数和最终答案。
4. 故意把工具描述写含糊，比较固定题集的工具选择结果。
5. 添加一个只读工具，先写输入输出测试，再注册给 Agent。
6. 用假的模型响应不断要求调用工具，确认预算生效（见 `tests/test_agent.py`）。

工具执行正确不代表 Agent 答案必然正确。模型可能选错工具、传错参数或错误转述。
聊天能用也不代表该模型支持原生工具调用；出现异常先检查接口响应和模型能力。

兼容入口：`python 03-app/agent/demo3_agent.py '100 公里是多少英里？' --trace`。
