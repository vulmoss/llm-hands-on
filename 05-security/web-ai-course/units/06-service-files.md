# 06 · SSRF、下载与上传边界

目标：辨别请求从哪里发出、数据最终到哪里。先修：单元 01、05。

```bash
python3 -m llm_lab.web_security run --lab ssrf
python3 -m llm_lab.web_security run --lab upload
```

SSRF：`/fetch?service=internal` 让教学服务发起一次真实 HTTP 到它自己启动的回环服务，返回 LAB_INTERNAL_MARKER。修复版只允许 public。网络日志与响应构成一跳证据；不会接受自定义主机、探测真实内网或访问云 metadata。生产中 URL 解析、解析后 IP、重定向、DNS 变化与出站网络策略仍需单独评估。

路径：`/download?name=../private.txt` 漏洞版返回合成标记，修复版拒绝。这里是虚拟文件字典，不是 OS 路径规范化实现。真实文件操作需要规范化后校验根目录、考虑符号链接与 TOCTOU；不要直接把字符串白名单代码当通用文件沙箱。

上传：对 `/upload` POST `{"name":"../note.html","content":"<b>LAB</b>"}`，漏洞版 201，修复版 400。正常 `note.txt` 应 201。文件存在内存字典中，不执行；对修复版只保留 readme 下载白名单，不提供通用上传文件分发。

真实上传还要限制大小、文件种类与内容、存储位置、下载 Content-Type/Disposition、随机名称和对象权限。前端 accept 和客户端 MIME 都不是服务端验证。

产物：请求源/目标图；一个正常 public 请求、一个 internal 请求；上传命名反例；说明当前模型未覆盖的两项真实系统问题。

下一课：[数据库注入](07-injection.md)。
