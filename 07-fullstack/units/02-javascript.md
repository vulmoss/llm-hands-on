# 阶段 2：JavaScript

[返回路线](../README.md)

## 目标

理解事件、数组状态、DOM 更新与异步请求。

## 阅读入口

[原生交互](../foundations/app.js)、[完整项目的请求封装](../taskboard/components/board.tsx)

## 核心概念

原生示例的唯一状态是 tasks 数组。每次动作先改变数据，再保存和渲染。localStorage 是浏览器存储；它既不是服务器数据库，也不能替你提供用户权限。

## 动手练习

1. 画出 submit/change/click 到 save/render 的调用顺序。
2. 增加“只看未完成”的过滤按钮，保留原数组，只过滤显示结果。
3. 在开发者工具中把保存的 JSON 改坏并刷新，观察错误分支；再比较 fetch 在 HTTP 400 与网络断开时的区别。

## 运行入口

以下从仓库根目录开始；如命令需要已启动的服务，先按项目 README 启动。

```bash
python3 -m http.server 8080 --bind 127.0.0.1 --directory 07-fullstack/foundations
```

## 验收

- [ ] 添加、完成、删除都更新统计，刷新后任务仍在。
- [ ] 输入包含 HTML 标签的任务只显示文字，不生成 HTML 节点。
- [ ] 能够解释为什么 catch 无法自动捕获所有 HTTP 400，以及 response.ok 的作用。

## 常见误区

不要把不可信文字交给 innerHTML；也不要把 JSON.parse 的失败当成“不可能”。

把实际结果记入 [练习记录](../practice-log.md)。

下一单元：[阶段 3：Git + GitHub](03-git-github.md)。
