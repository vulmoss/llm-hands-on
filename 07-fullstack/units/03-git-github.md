# 阶段 3：Git + GitHub

[返回路线](../README.md)

## 目标

把一次可审查的变化交付给未来的自己。

## 阅读入口

[项目首页](../../README.md)、[全栈 CI](../../.github/workflows/fullstack.yml)

## 核心概念

工作区、暂存区和提交是三个不同位置。分支隔离开发，PR 用来解释问题、行为和验证。项目的 lockfile 应提交；node_modules、数据库和真实账号信息不应提交。

## 动手练习

1. 在自己的克隆创建 practice/fullstack-ui 分支，只改一个可观察的界面行为。
2. 用 git diff 逐行检查，再按路径 git add；提交说明写清改了什么。
3. 推送练习分支并创建 PR，附截图与测试结果，观察 GitHub Actions。

## 运行入口

以下从仓库根目录开始；如命令需要已启动的服务，先按项目 README 启动。

```bash
git switch -c practice/fullstack-ui
git status --short
git diff
# 完成修改后按实际文件路径 git add，再 git commit
```

## 验收

- [ ] PR 中没有 .env.local、SQLite 数据库、node_modules 或无关文件。
- [ ] 读者只看 PR 描述就能复现你改变的行为。
- [ ] 用 git log 和 git show 找到对应修改；能解释 revert 与 reset 的区别。

## 常见误区

不要为了“同步”使用强制推送覆盖别人的提交。

把实际结果记入 [练习记录](../practice-log.md)。

下一单元：[阶段 4：TypeScript](04-typescript.md)。
