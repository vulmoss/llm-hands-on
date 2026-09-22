# 启动、观察与恢复

## 发布步骤

1. 从指定 Git 提交检出，运行 npm ci、类型检查、测试和生产构建。
2. 升级已有实例前，使用 backup 脚本保存当前数据库，并记录提交 SHA。
3. 在持久磁盘上启动 standalone 或 Docker Compose。
4. 检查 /api/health，执行一次真实 HTTP 冒烟请求，再访问页面验证静态资源。
5. 观察日志中异常状态与延迟。不要把“构建成功”当成“业务可用”。

Docker 默认只向宿主机 127.0.0.1 暴露端口。公开部署时由反向代理处理 HTTPS、请求体限制和
入口限流，并将 APP_ORIGIN 设置为准确的 `https://你的域名`。Secure Cookie 据此启用。
业务账号需要的恢复、验证和访问控制能力见 README 的教学边界。

## 观察运行状态

```bash
curl --fail http://127.0.0.1:3000/api/health
docker compose ps
docker compose logs --tail=100 app
node scripts/smoke.mjs
```

每条 API 日志包含 requestId、method、path、status 和 durationMs；不记录密码、Cookie 或请求正文。
前端错误响应也包含 requestId。健康检查会读数据库，数据库不可用时不报告健康。
健康检查不是完整业务测试，因此另有 smoke 脚本验证写入路径。

自行定义告警：连续健康探测失败、5xx 比例超阈值、p95 延迟升高、磁盘将满、备份过期。
当前只提供日志和健康端点，不包含已经部署的监控 / 告警服务。

## 本地备份与恢复演练

已有数据库后运行，选择一个不存在的备份文件名：

```bash
npm run db:backup -- .data/backups/manual-01.sqlite
```

脚本使用 SQLite backup API，覆盖 WAL 中已提交的数据。它拒绝覆盖已有备份。
停止本地应用后，将备份复制为新的恢复文件，再启动测试：

```bash
cp -n .data/backups/manual-01.sqlite .data/restored-01.sqlite
DATABASE_PATH=.data/restored-01.sqlite npm run start
```

使用原学习账号登录，检查任务。原数据库保留。确认恢复文件正确后，将 DATABASE_PATH 更新进
.env.local，避免下次启动回到旧文件。不要直接覆盖正在运行的 SQLite 主文件。

## Docker 数据备份与切换

```bash
docker compose exec app node scripts/backup.mjs .data/backups/manual-01.sqlite
docker compose exec app node -e "const fs=require('node:fs');fs.copyFileSync('/app/.data/backups/manual-01.sqlite','/app/.data/restored-01.sqlite',fs.constants.COPYFILE_EXCL)"
DATABASE_PATH=/app/.data/restored-01.sqlite docker compose up -d --wait
```

复制操作拒绝覆盖已有恢复文件。切换后验证账号和任务，再把 DATABASE_PATH 保存在 Compose 的 .env
或部署环境中。应另行把备份复制到受控的独立存储，命名卷内的备份不能抵御整块磁盘损坏。
账号和会话也在备份中；限制备份访问权限并制定保留期限。

## 回滚

当前 schema 为 v1。纯应用修改可以回退至上一 Git 提交并重新构建。
新增数据库迁移后，不能假定旧程序能够读新 schema；先在独立恢复文件上验证旧版本，
必要时使用升级前备份，并记录从备份时间点到回滚期间可能丢失的新增数据。

## 常见故障

| 现象               | 检查                                                       |
| ------------------ | ---------------------------------------------------------- |
| 403 来源不匹配     | 浏览器地址与 APP_ORIGIN 的协议、主机、端口是否完全一致     |
| 找不到 node:sqlite | Node 是否为 24 或更高的支持版本；本项目不是 Edge runtime   |
| 登录失败           | 密码至少 12 字符；注册使用的是哪个数据库；是否触发失败预算 |
| 容器中数据库只读   | 挂载目录所有者与非 root 的 node 用户是否兼容               |
| 页面无样式         | 是否通过启动脚本或 Dockerfile 复制了 .next/static          |
| E2E 无法启动       | 是否先 build、安装 Chromium，3100 是否被占用               |
| 容器重建后数据没了 | 是否保留命名卷；是否执行过 down -v；是否改变 DATABASE_PATH |

Docker 基础镜像只固定 Node 24 主版本。发布需要更严格的制品追踪时保存镜像 digest、Git SHA、
依赖锁文件与数据库 schema 版本。
