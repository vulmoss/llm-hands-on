# 阶段 8：APIs + REST

[返回路线](../README.md)

## 目标

用 HTTP 契约表达资源和错误。

## 阅读入口

[API 契约](../taskboard/API.md)、[处理函数](../taskboard/lib/api.ts)、[冒烟脚本](../taskboard/scripts/smoke.mjs)

## 核心概念

GET 读取任务，POST 创建，PATCH 局部更新，DELETE 删除。状态码解释结果，JSON 提供内容。服务端从会话推导所有者，不接受浏览器指定 user_id。

## 动手练习

1. 启动应用，在 Network 面板记录一次 POST 和 PATCH 的 URL、方法、状态码和响应。
2. 运行冒烟脚本，再故意省略 Cookie、修改 Origin、发送非法阶段，观察 401/403/400。
3. 给文档补一组合法和非法请求的实际脱敏输出。

## 运行入口

以下从仓库根目录开始；如命令需要已启动的服务，先按项目 README 启动。

```bash
cd 07-fullstack/taskboard
# 另一个终端中已经启动应用
node scripts/smoke.mjs
```

## 验收

- [ ] 401 与 403 的原因不同；找不到自己拥有的任务返回 404。
- [ ] 写请求要求 application/json 与准确 Origin，缓存头为 no-store。
- [ ] requestId 可以连接前端错误和服务端同一次请求日志。

## 常见误区

不要只在前端校验输入，也不要把 HTTP 200 当成所有操作的固定结果。

把实际结果记入 [练习记录](../practice-log.md)。

下一单元：[阶段 9：后端：Node.js / Python](09-backend.md)。
