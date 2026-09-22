# 阶段 9：后端：Node.js / Python

[返回路线](../README.md)

## 目标

理解两种运行环境共有的服务端责任。

## 阅读入口

[Node.js 处理层](../taskboard/lib/api.ts)、[数据库层](../taskboard/lib/db.ts)、[现有 Python API](../../src/llm_lab/api.py)

## 核心概念

本项目实际使用 Node.js，原 LLM 实验室实际使用 Python/FastAPI。它们都需要解析请求、鉴权、执行业务、处理错误和管理资源。选其中一个实现业务闭环，再用另一个练习协议兼容。

## 动手练习

1. 在 lib/api.ts 找到请求体上限、异常转换和所有权检查。
2. 对照 Python API，列出框架处理与业务处理各负责什么。
3. 扩展练习：用 FastAPI 实现一个返回相同结构的 GET /api/health，并写契约测试；保持任务服务只使用一个数据库拥有者。

## 运行入口

以下从仓库根目录开始；如命令需要已启动的服务，先按项目 README 启动。

```bash
cd 07-fullstack/taskboard
npm test
# Python 对照入口的启动依赖见仓库根 README
```

## 验收

- [ ] 能说明浏览器为什么不能直接调用 SQLite。
- [ ] 密码哈希异步执行；同步 SQLite 适用少量单机请求，吞吐限制有记录。
- [ ] Python 对照服务的健康接口和 Node.js 接口返回同样的约定结构。

## 常见误区

不要一开始同时维护两个功能重复的业务后端；不要把模型密钥交给浏览器。

把实际结果记入 [练习记录](../practice-log.md)。

下一单元：[阶段 10：数据库：SQL + NoSQL](10-databases.md)。
