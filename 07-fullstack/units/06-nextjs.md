# 阶段 6：Next.js

[返回路线](../README.md)

## 目标

理解 App Router 的页面、客户端组件和服务端路由边界。

## 阅读入口

[页面](../taskboard/app/page.tsx)、[布局](../taskboard/app/layout.tsx)、[API 路由](../taskboard/app/api/%5B...path%5D/route.ts)

## 核心概念

page.tsx 是服务端入口，board.tsx 用 use client 声明浏览器交互。API 路由在 Node.js 运行，才能使用 node:sqlite。数据库、密码处理和环境配置不应被导入客户端组件。

## 动手练习

1. 画出 page → Board → fetch → route → handle → SQLite 的流程。
2. 在浏览器 Network 面板查看 /api/auth/me 与 /api/tasks，比较页面 HTML 与 API JSON。
3. 运行生产构建，观察首页预渲染、API 动态执行的差异。

## 运行入口

以下从仓库根目录开始；如命令需要已启动的服务，先按项目 README 启动。

```bash
cd 07-fullstack/taskboard
npm run build
npm run start
```

## 验收

- [ ] npm run build 成功，npm run start 可独立运行构建产物。
- [ ] 浏览器包不包含数据库读写和密码哈希逻辑。
- [ ] 能够解释为什么不能把这个含 API 的项目直接上传为纯静态 GitHub Pages 站点。

## 常见误区

Route Handler 的请求也需要鉴权；隐藏前端按钮不会保护后端。

把实际结果记入 [练习记录](../practice-log.md)。

下一单元：[阶段 7：响应式设计 + UI](07-responsive-ui.md)。
