# 01 · HTTP、范围与实验基线

目标：能独立读懂请求，知道每次实验测了什么。先修：能运行 Python。

本课把 `127.0.0.1` 上本模块服务列为测试范围。正常业务、账户、资源都由我们生成。图片里的外部信息收集、搜索语法与 SRC 平台不是本次要扫描的目标。测试外部项目时，需要重新确认它的实际范围和规则。

1. 从仓库根目录设置 `export PYTHONPATH="$PWD/src"`。
2. 运行 `python3 -m llm_lab.web_security list`，写出你能解释的实验名称。
3. 运行 `python3 -m llm_lab.web_security run --lab idor`，打开 `.data/web-ai-course/evidence.json`，找出 request、response、normal_control。
4. 启动 `python3 -m llm_lab.web_security serve --mode fixed`。用 `curl -i http://127.0.0.1:8787/health` 查看 HTTP 200 与 JSON。
5. 请求 `curl -i 'http://127.0.0.1:8787/orders?id=1'`，观察 401。加入 `-H 'Cookie: sid=alice-lab'` 后应为 200。

理解 method 表示动作、path/query 定位对象、Cookie 表示教学会话、status 是服务端处理结果。200 不是权限正确的证明；403 也不自动证明所有分支安全。真正判断要结合谁访问什么对象以及响应内容。

产物：环境版本、一次正常请求、一次未登录请求和解释。反例：只凭 200 宣称“越权”。验收：你能在不调用模型时解释为什么这两次结果不同。

下一课：[AI 工作流](02-ai-workflow.md)。
