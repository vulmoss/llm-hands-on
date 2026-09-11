# 工程化：让实验可复现、可排错

## 安装与版本

根目录 `pyproject.toml` 定义核心包和可选依赖。核心没有第三方运行时依赖。

```bash
python -m pip install -e '.[ui,api,dev]'
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

`requirements-lock.txt` 是本次验证环境的完整依赖快照。需要复用精确版本时：

```bash
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
```

快照不锁定模型文件或 Python 解释器，跨操作系统/解释器版本应重新验证兼容性。
更新依赖后运行测试，再通过 `python -m pip freeze --exclude-editable` 更新快照。
CI 在 Python 3.10 和 3.12 安装可选依赖并运行测试与静态检查。

## API

```bash
llm-lab serve
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/chat -H 'Content-Type: application/json' -d '{"question":"什么是 RAG？","history":[]}'
```

API 文档：`http://127.0.0.1:8000/docs`。

- `/health`：应用存活，不检测模型服务；连接和模型安装检查用 `llm-lab doctor`。
- `/chat`：问题加历史，返回答案；所有历史由请求传入。
- `/rag`：问题、k 和可选阈值，读取 `LLM_INDEX_PATH`，返回答案及参考片段。
- `/agent`：问题，返回答案、工具执行记录和 stopped 状态。

入口限制问题长度、历史条数和 k。请求格式错误为 422，业务输入/索引错误为 400，
Ollama 连接或协议错误为 502。同步路由交给 FastAPI 的线程池执行。
当前 API 返回完整 JSON，流式输出在 CLI 和 Gradio 中提供。

## Docker

```bash
docker build -t llm-lab .
docker run --rm -p 127.0.0.1:8000:8000 --env-file .env llm-lab
```

容器内 `127.0.0.1` 指向容器自身。使用已有远程 Ollama 时在 `.env` 填远端地址。
挂载索引时可增加 `-v "$PWD/.data:/app/.data:ro"`，先在宿主机完成 index。
镜像不包含模型服务、模型权重和索引。默认以非 root 用户运行。

## 当前边界和后续练习

这是单用户实验服务，无认证、租户隔离、队列、全局限流或集中日志。
默认仅本机监听；需要共享服务时再增加身份认证和相应访问控制。
HTTP timeout 是网络操作超时，不是整个 Agent 任务的严格墙钟时间限制。
历史裁剪按轮数，下一步可改为 Token 预算。

练习顺序：结构化日志（不记录原文）→ 请求 ID → Token 预算 → 取消与总截止时间
→ 限流与队列 → 多用户数据隔离。每增加一项，都设计一个失败场景验证。
