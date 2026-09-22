# 阶段 4：TypeScript

[返回路线](../README.md)

## 目标

区分编译期类型与运行时输入校验。

## 阅读入口

[类型与校验](../taskboard/lib/domain.ts)、[配置](../taskboard/tsconfig.json)

## 核心概念

Task 和 Status 帮助代码调用者在编辑时发现错误；来自浏览器的 JSON 仍然是 unknown。需要通过 taskInput 校验后才能写入数据库。as 断言不会在运行时验证任何内容。

## 动手练习

1. 把一次合法的 status 临时改成拼错的值，运行类型检查，记录报错后恢复。
2. 给 taskInput 传入字符串阶段 "1"，确认服务端拒绝它。
3. 尝试给 Task 增加 priority 类型，先列出 UI、API、SQL、测试分别需要改动的位置。

## 运行入口

以下从仓库根目录开始；如命令需要已启动的服务，先按项目 README 启动。

```bash
cd 07-fullstack/taskboard
npm run typecheck
npm test
```

## 验收

- [ ] npm run typecheck 通过。
- [ ] 运行时仍拒绝非法状态、未知字段、超长标题和非整数阶段。
- [ ] 写出一个“类型检查通过但运行时仍可能错误”的 JSON 输入例子。

## 常见误区

不要用 any 或连续类型断言绕过边界；类型不能替代数据校验。

把实际结果记入 [练习记录](../practice-log.md)。

下一单元：[阶段 5：React](05-react.md)。
