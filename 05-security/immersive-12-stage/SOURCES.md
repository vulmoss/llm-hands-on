# 来源与版本核对

核对日期：2026-09-23。学习用时与评分是本项目的任务量估算和教学设计，不是图片提供的课时长度或外部研究结论。

- 用户图片 `timeline-lession.jpg`：十二阶段目标。前两张图的完整范围继续见 `../web-ai-course/`；本模块聚焦第三张图，不能把毕业理解为同时精通第一、二张图的全部云/代码审计主题。
- [DVWA 官方仓库](https://github.com/digininja/DVWA)：安装、默认登录与隔离要求。
- [DVWA 官方 Compose](https://github.com/digininja/DVWA/blob/master/compose.yml)：镜像、数据库和回环端口参考。本课增加资源限额、内部网络和摘要锁。
- [DVWA 配置](https://github.com/digininja/DVWA/blob/master/config/config.inc.php.dist)：DB_SERVER、DB_DATABASE、DB_USER、DB_PASSWORD、DEFAULT_SECURITY_LEVEL。
- [DVWA Low SQLi 实现](https://github.com/digininja/DVWA/blob/master/vulnerabilities/sqli/source/low.php)：仅对本地教学实例理解输入拼接。
- [Juice Shop 官方运行指南](https://pwning.owasp-juice.shop/companion-guide/latest/part1/running.html)：核对时指南版本为 v20.2.0；官方镜像与版本标签。部分新挑战含外部依赖，本课 internal 网络不提供这些依赖。
- [Juice Shop 官方讲解](https://pwning.owasp-juice.shop/companion-guide/latest/part2/README.html)：阶段 11 的公开案例来源；按部署版本选择实际挑战并记录标题。
- [Docker Ubuntu 安装](https://docs.docker.com/engine/install/ubuntu/)：官方 apt keyring 与 packages，Ubuntu 22.04/24.04。
- [Docker 端口发布](https://docs.docker.com/engine/network/port-publishing/)：回环绑定与旧于 28.0.0 版本的访问限制注意事项；本课要求 Engine 28+。
- [MariaDB healthcheck.sh](https://mariadb.com/docs/server/server-management/automated-mariadb-deployment-and-administration/docker-and-mariadb/using-healthcheck-sh)：数据库 ready 检查。

官方 main/master/latest 链接本身可变，运行复现以本地保存的源码提交、镜像 digest 和验收记录为准。未确认的功能不从旧博客补成“已验证”。
