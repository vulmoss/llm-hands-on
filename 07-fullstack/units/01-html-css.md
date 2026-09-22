# 阶段 1：HTML + CSS

[返回路线](../README.md)

## 目标

做出无需框架也能理解的语义化任务页面。

## 阅读入口

[原生页面](../foundations/index.html)、[样式](../foundations/styles.css)、[运行说明](../foundations/README.md)

## 核心概念

HTML 描述内容与语义，CSS 控制布局。先分清 main、form、label、button 的职责，再学习盒模型、Flex 与 Grid。按钮是否可用键盘触发，比页面是否看起来像按钮更重要。

## 动手练习

1. 按运行说明启动原生页面，临时移除 script 标签，解释哪些能力仍然存在。
2. 给页面增加“本周目标”区块；用正确层级的标题和 label，而不是大量 div 模拟控件。
3. 把最大宽度改成 720px，再缩小浏览器，观察固定宽度与 max-width 的差异。

## 运行入口

以下从仓库根目录开始；如命令需要已启动的服务，先按项目 README 启动。

```bash
python3 -m http.server 8080 --bind 127.0.0.1 --directory 07-fullstack/foundations
```

## 验收

- [ ] 只用 Tab、Shift+Tab、Enter 可以到达和提交表单。
- [ ] 每个输入框有可见标签，390px 宽度下没有横向滚动。
- [ ] 提交前后两张截图与一份自己的 HTML 结构说明。

## 常见误区

不要靠绝对定位拼出整个页面，也不要用占位文字代替 label。

把实际结果记入 [练习记录](../practice-log.md)。

下一单元：[阶段 2：JavaScript](02-javascript.md)。
