# 适配现有环境的操作流程

需要交给另一个 agent 实际部署时，直接使用 [部署与交接手册](AGENT-DEPLOYMENT.md)。下文保留日常学习的简化操作。

## 节点与资源安排

以下来自既有实验环境资料；具体服务是否可用应先执行检查，不把旧记录当实时状态。

| 位置 | 已有角色 | 本课程用途 |
|---|---|---|
| Mac | 编辑、Git、浏览器/Burp | 可直接运行全部离线实验；浏览器通过隧道访问 .16 |
| 192.168.2.15 | Ollama、TiDB SQL、PD/TiKV、Vulfocus、监控 | 仅调用 Ollama 11434；默认 1.5B、并发 1 |
| 192.168.2.16 | Python 开发、PD/TiKV，16 GB | 首选代码节点；新教学服务回环 8787 |
| 192.168.2.17 | TiUP 控制、PD/TiKV，16 GB | 可选重复验证节点；不改 TiDB 部署 |

现有环境为 CPU 推理。初始预算是小型标准库服务 + 单条模型请求；**不是已测得的性能保证**。不启动 7B 并发，不下载整套靶场镜像，不修改 ESXi/TiDB/Ollama 的配置。不使用 80/3000/4000/8000/11434 作为新教学端口。

## A. Mac 本地运行

```bash
git clone https://github.com/vulmoss/llm-hands-on.git
cd llm-hands-on
export PYTHONPATH="$PWD/src"
python3 -m llm_lab.web_security run --all
```

若已有仓库，先确认工作区修改再更新；不要用强制重置覆盖未提交文件。标准库模式不用 pip。要跑 pytest/ruff，使用独立虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q tests/security/test_web_course.py
```

## B. 在 .16 运行

从 Mac 登录：`ssh llm2@192.168.2.16`。在远端执行：

```bash
mkdir -p ~/labs
cd ~/labs
git clone https://github.com/vulmoss/llm-hands-on.git
cd llm-hands-on
export PYTHONPATH="$PWD/src"
python3 -m llm_lab.web_security run --all
python3 -m llm_lab.web_security serve --mode vulnerable --port 8787
```

另开 Mac 终端保留隧道：

```bash
ssh -N -L 8787:127.0.0.1:8787 llm2@192.168.2.16
```

浏览器打开 `http://127.0.0.1:8787/frontend/index.html`。固定使用这一 origin，不混用 localhost 与 IP。服务器保持回环绑定，无需对整个局域网开放。先停 Mac 上相同端口的教学服务再建隧道。

## C. 模型调用与留证

在运行代码的终端：

```bash
export OLLAMA_BASE_URL=http://192.168.2.15:11434
export OLLAMA_MODEL=qwen2.5:1.5b
export OLLAMA_TIMEOUT=180
export LLM_MAX_TOKENS=768
python3 -m llm_lab.web_security doctor
python3 -m llm_lab.web_security run --lab sqli --output .data/web-ai-course/sqli.json
python3 -m llm_lab.web_security review --evidence .data/web-ai-course/sqli.json --live --output .data/web-ai-course/sqli-review.md
```

默认模型配置来自现有 `Settings`，本课程明确设置小模型；不设置会沿用根项目的 7B。调用 Ollama 原生 `/api/chat`，不是带 `/v1` 的兼容地址。没有模型服务时省略 `--live`，仍可完成所有 Web HTTP 实验。模型响应失败退出 2，不伪造“离线模型结果”。

## D. Burp 手动对照

1. 启动教学服务，打开 Burp 自带浏览器并访问本地地址；如使用普通浏览器，配置本地代理 127.0.0.1:8080，确保回环请求未被绕过。课程用 HTTP，无需为本课安装 TLS 证书。
2. 点击教学登录、订单 1，找到 `GET /orders?id=1` 请求并送到 Repeater。
3. 保留 `Cookie: sid=alice-lab`，只改 `id=2`。漏洞版能读到 `B-book`；修复版 403。
4. 删除 Cookie，应在两个版本均得到 401；改为 `sid=bob-lab`，访问订单 2 应是 200。
5. 保存方法、路径、合成身份、状态码、响应标记和版本，写入学习记录。真实项目证据不得包含可用 Cookie/Token。

自动 runner 绕过系统代理，只连接自己创建的随机回环端口；抓包练习应使用固定 8787 的交互服务。

## E. 前端插件

Chrome 扩展管理页启用开发者模式，加载已解压目录 `05-security/web-ai-course/frontend/extension`。打开本地 8787 页面，点击插件“列出本地页面脚本”，应看到 `app.js` URL。它只使用 activeTab/scripting、点击后运行，限制到本地 8787；动态 import 模块不会作为 script 元素列出，要在 Network 查看。练习结束在扩展管理页移除。

## 常见问题

| 现象 | 原因与处理 |
|---|---|
| `No module named llm_lab` | 回到仓库根目录设置 `PYTHONPATH="$PWD/src"`，或激活已安装项目的虚拟环境 |
| 8787 被占用 | 停自己的旧进程；或用 `--port 8788` 并同步改隧道/浏览器，插件仍限定 8787 |
| 模型连接失败 | 从当前代码节点执行 doctor，检查路由与 .15 服务；不自动重启共享服务 |
| JSON 结果两个模式均 True | 符合对照预期，不表示两个模式都没有漏洞 |
| XSS 没弹框 | 核对浏览器地址/模式与输出上下文；自动测试只验证响应，不证明脚本执行 |
| CORS curl 能读数据 | curl 不执行浏览器同源策略；检查响应头只是必要观察 |
| CSRF 请求返回 403 | 修复版要求 Origin 等于服务 origin 且合成 token 正确；实际浏览器需另看 Cookie 是否发送 |
| 模型慢或输出中断 | 先用 1.5B 单实验，查看 done_reason；提高超时不代表提高准确率 |
| `/frontend/` 404 | 从源码 checkout 运行；前端材料不包含在独立 wheel 包中 |

## 停止与恢复

交互服务器和 SSH 隧道各按 Ctrl-C；临时状态随服务结束清空。自动 runner 在 finally 关闭两个回环监听器。证据保存在被 Git 忽略的 `.data/web-ai-course/`，按需归档。重新启动服务即可恢复初始数据；不需要重启虚拟机或清理 Docker。
