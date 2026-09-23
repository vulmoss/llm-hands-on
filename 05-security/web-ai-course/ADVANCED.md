# 进阶复现：从教学模型过渡到真实技术栈

这些是**可执行的学习流程与验收标准**，不是本次已完成的真实产品漏洞证明。先完成本地 12 实验。外部练习只在官方分配的隔离靶场、自建实验或你明确授权的资产内进行；每次记录实际版本与实例，不沿用图片里的成功承诺。

## 1. OAuth / SSO / OIDC

入口：[PortSwigger OAuth 专题与实验](https://portswigger.net/web-security/oauth)。

1. 阅读 authorization code 流程，画 browser、client/RP、authorization server、resource server 四方图。
2. 进入专题的 OAuth labs，创建分配给自己的实例。完成正常登录，记录 authorization、callback、token/userinfo 的顺序；只保留脱敏日志。
3. 选择 state/账户绑定相关入门实验，用自己的两个实验账号分别走正常流程。比较 state 与发起会话的关系；观察 callback 重放和切换会话的行为。
4. 对照本模块 state-only 模型，标出真实系统新增的 code、redirect_uri、PKCE、nonce、issuer、audience 与签名校验位置。
5. 复测：正确会话正常通过、错误 state 拒绝、跨会话拒绝、重复使用拒绝。账号绑定还须有原账号认证，不只依赖邮箱字符串。
6. 导出记录后停止/重置实例。没有完成真实登录链时，不写“接管成功”。

## 2. XML / XXE

入口：[PortSwigger XXE](https://portswigger.net/web-security/xxe)。

先理解 DTD、实体、外部资源加载和解析器配置。选择官方 XXE 入门靶场，先发一个合法 XML，再按该靶场的学习任务改变单个解析特性，记录服务器返回或靶场自带回调。复现时只使用靶场提供的合成资源，不读取宿主系统文件。

在自己的防护练习中，默认禁止 DTD/外部实体并关闭解析器网络访问；用一个正常 XML 和一个含实体声明的输入做回归。仅有异常信息不是 XXE 成功，必须证明解析器解析了本不应接受的资源。Python、Java、PHP 默认值不同，要固定实际库版本，不凭语言名称推断。

## 3. SSTI / 命令注入 / 反序列化 / RCE

入口：[SSTI](https://portswigger.net/web-security/server-side-template-injection)、[OS command injection](https://portswigger.net/web-security/os-command-injection)、[deserialization](https://portswigger.net/web-security/deserialization)。

1. 先做 audit-exercises 的 Python/Java/PHP 题，确定 source、可达 sink 和运行进程权限。
2. 选择一个官方入门实验，记录解释器与模板/序列化库版本。先证明模板表达式被求值或参数被当作命令语法，使用靶场定义的无破坏验证任务。
3. 不把“表达式可求值”直接写成“任意命令执行”；继续核对作用域、可用对象、沙箱和上下文。
4. 修复练习使用固定模板 + 数据参数、固定程序 + argv、不从不可信输入反序列化对象；做正常功能对照。
5. 报告记录影响止步于实际验证点；清理实例。不要在共享 .15 的宿主或 TiDB 进程中运行解释器漏洞样例。

Vulfocus 可作为选修：在其 UI 中选择一个与你要学的技术栈对应的条目，先看镜像标签、描述与上游来源，**一次只启动一个**，记下实际端口和到期时间，按该条目的官方说明复现并停止。目录是否包含某 CVE、镜像能否拉取需要当时核对，本课程没有批量启动或升级 Vulfocus。

## 4. 真实云存储 / 签名 URL / STS

参考：[AWS S3 预签名 URL](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)、[S3 阻止公共访问](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)。这里提供自有资源流程，不申请任何云资源，也不产生费用。

准备专用测试桶、两个测试身份以及 public/private 两个合成对象，禁止放真实文件。记录 principal/action/resource/condition 四项，区分 ListBucket 与 GetObject。

- 先验证匿名、身份 A、身份 B 对两个对象的预期访问结果。
- 为指定对象签发短期只读 URL；保存签名方法、对象、失效时间和签名头的说明，证据遮掉签名参数。
- 用原方法/对象做正常对照；改变 method、key、过期时间、被签 header 分别重放，观察拒绝原因。
- 对 STS 测试 token 到期、超出前缀、跨租户对象与未授予动作是否拒绝。短期凭据出现在合法客户端不自动构成泄露。
- 删除测试对象、撤销临时身份授权、清理专用资源。单次失效可能来自时间漂移，先校准时钟再判断签名实现。

S3、OSS、COS 的签名细节不完全相同，必须按供应商官方协议核对。本地 `/objects` 实验只负责先教会你对象权限矩阵。

## 5. 并发、验证码与业务重放

在独立练习数据库创建一条库存=1 的合成商品。先用两个线程加屏障，使它们都读取旧库存，再各自更新；记录成功订单数和最终库存。修复用事务内原子条件更新，例如 `UPDATE ... SET stock=stock-1 WHERE id=? AND stock>0`，仅在受影响行数为 1 时创建订单；同时测试事务失败回滚。

幂等需要独立请求键、唯一约束、结果复用和键与主体绑定；不能用“请求间 sleep”当修复。验证码使用内存状态模型记录 issued_at/expires_at/attempts/consumed，测试过期、复用、错误次数耗尽与切换账号。本地 HTTP app 串行处理请求，不包含竞态漏洞，因此该作业要独立实现和测量。

## 6. Vue / React / webpack / 前端加密

阅读 [Vue 安全指南](https://vuejs.org/guide/best-practices/security.html) 和 [React DOM API](https://react.dev/reference/react-dom/components/common)。

1. 先在本模块原生 JS 页面证明默认文本插入与 HTML sink 的差异。
2. 在现有 taskboard 跟踪 UI → fetch → route → auth → db；记录路由守卫与服务端鉴权的不同位置。
3. 对你自己构建的 Vue/React 示例记录 package-lock 和构建命令。开发与生产模式分别查看源码映射是否发布、动态 chunk 如何加载，避免拿开发构建结论套到生产。
4. 对 webpack：识别入口脚本与 runtime，在 Network 中点击懒加载功能找到实际 chunk；不同版本可能使用不同加载协议，不依赖固定全局函数名。
5. 对前端加密：跟踪输入、密钥、IV/nonce、签名范围和服务端校验。源码可恢复不代表能绕过服务端身份；写清仍缺的条件。

## 7. 中间件、子域与工具选型

对自有资产将“版本疑似”“组件可达”“前置配置成立”“最小行为验证”分层。版本横幅、开放端口或废弃 CNAME 都只是线索。子域接管练习先在合成记录里分析资源归属和释放流程，不认领别人的云资源。

WAF/RASP 属于附加控制，应用根因修复与正常业务回归仍要做。海报没有给 DeepAudit 的仓库地址与版本，本模块不假定某个同名项目就是课程工具。评估任何审计工具时用固定正/负样例，记录误报、漏报、证据路径和运行成本，再决定是否引入。
