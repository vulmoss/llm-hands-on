# REST API 契约

开发来源为 `http://127.0.0.1:3000`。所有响应禁止缓存，并附带 `X-Request-Id`。
写请求须带匹配 APP_ORIGIN 的 Origin；需要正文的请求须为 application/json，正文最多 8192 字节。
浏览器同源 fetch 自动发送 Origin 和 Cookie。命令行客户端需要显式发送。

| 方法   | 路径               | 请求                             | 成功响应                    | 身份              |
| ------ | ------------------ | -------------------------------- | --------------------------- | ----------------- |
| GET    | /api/health        | 无                               | 200，status/database/schema | 公开              |
| POST   | /api/auth/register | email, password                  | 201，user；设置 Cookie      | 公开              |
| POST   | /api/auth/login    | email, password                  | 200，user；设置 Cookie      | 公开              |
| POST   | /api/auth/logout   | 无                               | 200，ok；撤销当前会话       | 可匿名，需 Origin |
| GET    | /api/auth/me       | 无                               | 200，user                   | 登录              |
| GET    | /api/tasks         | 无                               | 200，tasks 数组             | 登录              |
| POST   | /api/tasks         | title, stage                     | 201，task                   | 登录              |
| PATCH  | /api/tasks/{id}    | title / stage / status，至少一个 | 200，task                   | 所有者            |
| DELETE | /api/tasks/{id}    | 无                               | 200，ok                     | 所有者            |

用户结构为 `{ "id": "UUID", "email": "normalized-email" }`。
任务结构：

```json
{
  "id": "UUID",
  "title": "完成第一个页面",
  "stage": 1,
  "status": "todo",
  "createdAt": "2026-01-01T00:00:00.000Z"
}
```

title 为去首尾空白后 1–120 字符，stage 为 1–16 整数；status 仅允许 todo / doing / done。
客户端不能提交 id、user_id、createdAt 或任意未知字段。

## 错误约定

```json
{ "error": "请先登录", "requestId": "request-uuid" }
```

| 状态 | 原因                                     |
| ---- | ---------------------------------------- |
| 400  | 字段、JSON 或值不合法                    |
| 401  | 未登录、会话过期、密码不正确             |
| 403  | 写请求来源不匹配                         |
| 404  | 接口不存在，或当前用户无法访问该任务     |
| 409  | 该邮箱已经注册                           |
| 413  | 正文超过 8192 字节                       |
| 415  | 正文格式不是 application/json            |
| 429  | 账号在当前 15 分钟窗口内失败达到预算     |
| 500  | 服务端内部错误；客户端不接收内部异常详情 |

## 一次可操作的命令行练习

先启动应用，命令从项目目录运行。这里的邮箱和密码仅供本地练习，首次运行注册。

```bash
mkdir -p .data
curl --fail-with-body -c .data/cookies.txt \
  -H 'Origin: http://127.0.0.1:3000' \
  -H 'Content-Type: application/json' \
  -d '{"email":"practice@example.test","password":"local-practice-passphrase"}' \
  http://127.0.0.1:3000/api/auth/register

curl --fail-with-body -b .data/cookies.txt \
  -H 'Origin: http://127.0.0.1:3000' \
  -H 'Content-Type: application/json' \
  -d '{"title":"复现 REST 请求","stage":8}' \
  http://127.0.0.1:3000/api/tasks

curl --fail-with-body -b .data/cookies.txt http://127.0.0.1:3000/api/tasks
```

重复使用账号时改请求路径为 `/api/auth/login`。cookies.txt 属于会话凭据，保存在已忽略的 .data 中。
无状态分页、搜索和并发编辑版本控制尚未实现，可作为后续需求添加。
