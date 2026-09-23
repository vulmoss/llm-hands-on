# 04 · XSS、CSRF、CORS 与重定向

目标：把“浏览器执行”“浏览器携带身份”“浏览器允许读取”区分开。先修：单元 03。

```bash
python3 -m llm_lab.web_security run --lab xss
python3 -m llm_lab.web_security run --lab csrf
python3 -m llm_lab.web_security run --lab cors
python3 -m llm_lab.web_security run --lab redirect
```

每条默认覆盖 evidence.json；需要并存时指定 `--output .data/web-ai-course/xss.json` 等。

XSS：漏洞版 `/reflect` 把 q 直接拼接进 HTML 文本上下文，修复版使用 html.escape。启动交互漏洞版后在浏览器打开 `/reflect?q=%3Csvg%20onload%3Dalert%281%29%3E`，观察本地 alert(1)；修复版显示文本。自动化只检查未转义字符串是否出现，不能把它写成已做浏览器执行验证。此修复只适用于这里的 HTML 文本上下文，不是 JavaScript/URL/CSS 上下文通用方案。

CSRF：请求携带教学 Cookie，同时 Origin 是 other.example.test。漏洞版修改邮箱，修复版拒绝；正常 Origin + 合成 token 通过。这是 HTTP 重放实验，curl 可任意设置头，浏览器不可以。真实场景还要记录 SameSite、请求类型、凭据是否发送、token 是否与会话绑定；本例固定 token 不能用于生产。

CORS：漏洞版回显任意 Origin 并允许 credentials。修复版仅接受明确的 dashboard origin。检查响应头只是必要步骤，跨站可读敏感数据还要求浏览器允许携带凭据、端点确实返回该用户数据。本例 `/cors` 只返回教学说明，不宣称发生了数据泄露。

重定向：runner 不跟随 302，只比较 Location。修复版采用站内目的地枚举。若要讨论 OAuth 链，必须进一步证明跳转能影响授权码/token 流向；单个开放跳转并不能证明账号接管。

产物：四个实验各一组证据；一段话区分 CORS 与 CSRF；至少两个浏览器前提。延伸：点击劫持检查 frame-ancestors / X-Frame-Options 和敏感动作，不只凭“能 iframe”定影响。

下一课：[认证授权](05-auth.md)。
