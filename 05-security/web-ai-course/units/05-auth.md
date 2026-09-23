# 05 · 身份、对象权限与 OAuth 状态

目标：区分认证、角色、所有权与流程状态。先修：单元 01、04。

```bash
python3 -m llm_lab.web_security run --lab idor
python3 -m llm_lab.web_security run --lab mass-assignment
python3 -m llm_lab.web_security run --lab oauth
```

在交互服务中使用 Repeater 或 curl，完成矩阵：匿名访问订单 1/2 均 401；Alice 访问 1 为 200、访问 2 在修复版 403；Bob 反之。对象 ID 改成 UUID 只增加猜测成本，不能代替检查 owner。扩展为多租户时，条件必须同时包含 tenant 与资源关系，单独检查登录不足。

批量赋值：向 `/profile` POST `{"name":"Alice","role":"admin"}`。漏洞版把所有键直接更新到 profile，修复版只允许 name。profile 里的 admin 是演示字段；没有管理员后台或真正权限升级效果，报告只能写到已观察字段改变。

OAuth 模型：请求 `/oauth/start` 取得 state（带 Alice Cookie）；用同 Cookie 请求 `/oauth/callback?code=lab-code&state=取得的值`，首次 200，重复回调 403。用 Bob Cookie 携带 Alice 的 state 也应拒绝。state 要绑定发起会话并一次性消费。此处 code 是固定演示值，不是授权服务器发行的 code。

完整 OAuth/OIDC 还需要精确 redirect_uri、code 兑换绑定、PKCE、issuer/audience/nonce、签名与账户关联策略。本模块没有真实 IdP，不声称实现完整 SSO。去进阶流程的官方 OAuth 靶场继续做端到端验证。

产物：权限矩阵、批量赋值前后字段、正常 state/错误 state/重放/跨会话四项。前端隐藏按钮不能作为矩阵里的服务端控制。

下一课：[服务与文件](06-service-files.md)。
