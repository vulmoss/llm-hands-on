# 03 · JavaScript、模块与前端攻击面

目标：由页面操作追到 fetch，再追到服务端权限。先修：单元 01；JS 不熟先看 `07-fullstack/units/02-javascript.md`。

```bash
python3 -m llm_lab.web_security frontend
python3 -m llm_lab.web_security serve --mode vulnerable
```

浏览器进入 `/frontend/index.html`：

1. 开启 Network，点击登录与两个订单按钮。查看 Cookie、资源 ID、响应体。将入口整理为“动作—方法—URL—身份—服务端检查”。
2. 在 Sources 查看 `app.js` 中 fetch 和 DOM sink。`frontend` 命令只提取字面量路径，动态字符串和函数包装需要你沿调用链跟踪。
3. 点击动态模块，Network 出现 `lazy.js`。这演示原生 `import()`；webpack JSONP/runtime 是另一层打包协议，不能把本文件当 webpack bundle。
4. 查看 `app.js.map` 的 sources/sourcesContent。本样例 mappings 为空，仅演示源码携带与提取，不演示精确断点映射。source map 暴露源码不自动构成高危漏洞，需要证明暴露了什么额外秘密或权限缺陷。
5. 地址改为 `/frontend/index.html?mode=vulnerable#%3Cb%3ELAB%3C%2Fb%3E`，看到粗体 LAB；改 mode=fixed，看到原始 `<b>LAB</b>` 文本。服务端 mode 与这个 DOM mode 是两个独立教学开关。
6. 按 OPERATIONS 加载插件，比较 document.scripts 清单与 Network 清单。解释为什么动态 import 不在 script 标签里。

Vue 的 `v-html`、React 的 `dangerouslySetInnerHTML` 与原生 innerHTML 都值得检查输入来源；默认文本插值与显式 HTML 注入是不同路径。前端路由守卫只控制界面，不能替代 `/orders` 的后端鉴权。前端加密若解密密钥也发给浏览器，不构成对客户端保密。

产物：3 条接口记录、1 条 source→sink、1 个假阳性说明、插件结果。扩展：到已有 taskboard 跟踪客户端 API 调用与服务端 auth.ts，先阅读，不修改生产业务。

下一课：[浏览器边界](04-browser.md)。
