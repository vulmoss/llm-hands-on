# 阶段 12：测试：单元 + 集成 + E2E

[返回路线](../README.md)

## 目标

用不同层次的证据定位问题。

## 阅读入口

[纯逻辑测试](../taskboard/tests/domain.test.ts)、[API 与 SQLite](../taskboard/tests/api.test.ts)、[浏览器测试](../taskboard/e2e/board.spec.ts)

## 核心概念

单元测试验证独立规则；集成测试使用真实 SQLite 和标准 Request/Response 调用处理层；E2E 启动生产构建，用 Chromium 验证真实 HTTP 与页面。每层解决不同的问题，不要把同一实现抄进测试当答案。

## 动手练习

1. 运行三层测试，找到每种测试覆盖的边界。
2. 临时去掉一个任务查询的 user_id 条件，确认越权测试失败，再恢复。
3. 给一个之前遗漏的用户行为增加测试，例如阶段过滤或错误密码提示。

## 运行入口

以下从仓库根目录开始；如命令需要已启动的服务，先按项目 README 启动。

```bash
cd 07-fullstack/taskboard
npm run check
npx playwright install chromium
npm run test:e2e
```

## 验收

- [ ] 类型检查、单元/集成、生产构建与 E2E 全部通过。
- [ ] 失败可定位到具体功能；测试使用独立数据库与随机账号。
- [ ] 记录环境版本和未执行的检查，不把模拟结果写成真实服务成绩。

## 常见误区

E2E 的测试账号不应使用自己的真实账号；测试通过不代表容量和所有攻击面都已评估。

把实际结果记入 [练习记录](../practice-log.md)。

下一单元：[阶段 13：Docker](13-docker.md)。
