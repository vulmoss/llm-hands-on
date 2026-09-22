# 阶段 10：数据库：SQL + NoSQL

[返回路线](../README.md)

## 目标

理解关系、约束、索引、持久化以及什么时候换数据库。

## 阅读入口

[实际 SQL 与迁移](../taskboard/lib/db.ts)、[持久化测试](../taskboard/tests/api.test.ts)、[架构决策](../taskboard/ARCHITECTURE.md)

## 核心概念

users → tasks 是一对多，sessions 也引用 users。SQL 参数绑定保护值的边界；UNIQUE、CHECK 和外键保持数据约束。WAL 提升读写配合，但不会让 SQLite 变成多节点数据库。

## 动手练习

1. 画出四张表及关系，解释 tasks(user_id, created_at) 索引对应哪条查询。
2. 运行关闭再打开数据库的测试；新增字段时设计 schema v2 迁移，而不是删除旧库。
3. NoSQL 对照练习：为任务设计一份 MongoDB 风格文档，写出 ownerId 查询和索引，比较唯一性、事务与关系查询；需要实作时另建可选服务，不替换当前验收基线。

## 运行入口

以下从仓库根目录开始；如命令需要已启动的服务，先按项目 README 启动。

```bash
cd 07-fullstack/taskboard
npm test
# 使用过应用、已有数据库后
npm run db:backup
```

## 验收

- [ ] 服务重启后任务存在，第二个账号无法读写第一账号的任务。
- [ ] 能指出 JSON 文件、浏览器存储、SQL 数据库和文档数据库的差异。
- [ ] 提交 SQL 与文档模型的对照表，并用需求解释选型。

## 常见误区

复制正在 WAL 写入的主数据库文件可能漏数据；备份使用 SQLite backup API。

把实际结果记入 [练习记录](../practice-log.md)。

下一单元：[阶段 11：身份验证 + 授权](11-auth.md)。
