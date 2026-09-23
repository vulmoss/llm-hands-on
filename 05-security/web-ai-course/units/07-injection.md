# 07 · SQL 与解释器边界

目标：利用已有 DBA 经验解释查询结构变化。先修：单元 01。

```bash
python3 -m llm_lab.web_security run --lab sqli --output .data/web-ai-course/sqli.json
```

看 `server.py` 的 `/search` 分支。漏洞版将用户 q 放进 SQL 字符串；固定样例使 WHERE 条件改变，返回本不公开的 LAB_DRAFT_MARKER。修复版 `WHERE published=1 AND title=?` 用参数绑定，数据库把输入当成 title 值，因此异常查询返回空列表。

手动对照：q=public 返回 public；q=missing 返回空；异常 q 在漏洞版出现 draft、修复版为空。记录的不只是 SQL 报错，而是越过 published=1 数据边界。不能因为参数化不报错就略过正常业务回归。

给你背景的扩展：在独立练习库分别写 PostgreSQL/Oracle 驱动查询，核对占位符和参数类型；不连接现有业务数据库。不在本课 TiDB 集群上建立具有真实敏感数据的靶库。ORM 原生 SQL 拼接仍可能引入风险；排序字段通常需要枚举而不是把字段名当绑定参数。

NoSQL/LDAP/XPath 都是“输入影响解释器结构”这一类问题，但语法、类型与逃逸规则不相同。不能拿单引号测试当成对所有类型的覆盖。进阶作业：为 JSON 查询对象定义允许字段和允许操作符，给出非法类型与嵌套操作符反例，而不是只过滤几个符号。

产物：两段查询、三组结果、参数绑定解释、跨数据库不可直接照搬的两点。

下一课：[云与进阶](08-cloud-advanced.md)。
