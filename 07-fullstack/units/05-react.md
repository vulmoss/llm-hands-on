# 阶段 5：React

[返回路线](../README.md)

## 目标

用状态驱动页面，而不是手动修改 DOM。

## 阅读入口

[看板组件](../taskboard/components/board.tsx)、[进度计算](../taskboard/lib/domain.ts)

## 核心概念

user、tasks、filter、editing 是不同职责的状态；visible 和 summary 是派生值。React 更新后重绘页面，因此异步成功后只需更新状态。表单需要同时处理等待、成功和失败。

## 动手练习

1. 追踪 save 函数，解释为什么先等待 API 再更新 tasks。
2. 增加“仅看进行中”的过滤，避免维护第二份任务数组。
3. 把统计区提取成接收 tasks 的组件；确认编辑、删除后统计依旧正确。

## 运行入口

以下从仓库根目录开始；如命令需要已启动的服务，先按项目 README 启动。

```bash
cd 07-fullstack/taskboard
npm run dev
```

## 验收

- [ ] 不使用 document 操作来修改任务内容；已有 focus 调用仅用于焦点管理。
- [ ] 请求失败时保留用户输入并显示错误，提交期间禁止重复写请求。
- [ ] 重新渲染和过滤不会把任务状态丢失。

## 常见误区

不要把可以从 tasks 计算的数量另存为容易失同步的状态。

把实际结果记入 [练习记录](../practice-log.md)。

下一单元：[阶段 6：Next.js](06-nextjs.md)。
