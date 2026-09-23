# 六语言审计题：先追数据流，再决定如何验证

以下为**阅读题片段**，不是能直接启动的应用或本次已完成的六语言复现。统一问题：输入从哪来？谁能控制？进入什么解释器/资源？缺了哪个前置条件？正常样例与异常样例各是什么？

## Python：查询拼接

```python
term = request.args["q"]
rows = db.execute("SELECT title FROM notes WHERE title='" + term + "'")
# 修复：驱动参数绑定；表名/字段名使用枚举
rows = db.execute("SELECT title FROM notes WHERE title=?", (term,))
```

与本地 sqli 实验对应。反例：把格式化后的字符串传给 execute，并没有参数化。检查 row-level 权限仍需独立条件。

## Java：命令字符串

```java
String name = request.getParameter("name");
new ProcessBuilder("sh", "-c", "echo " + name).start();
// 修复思路：尽量在 Java 内处理；必须调用外部程序时固定程序并传独立 argv
new ProcessBuilder("/usr/bin/printf", "%s", name).start();
```

危险 sink 是 shell 对字符串的解释。没有 shell 也要看目标程序是否把 `-` 开头输入当选项、是否能读写越界路径。不要只看到 ProcessBuilder 就报告 RCE。

## PHP：对象反序列化

```php
$value = unserialize($_POST['payload']);
// 数据交换若只需要 JSON，不接收带对象行为的序列化格式
$value = json_decode($_POST['payload'], true, 16, JSON_THROW_ON_ERROR);
```

仅调用 unserialize 不证明必然 RCE，还需要可用类、魔术方法与可达行为。JSON 仍需要 schema、字段与权限检查，不是所有安全问题的通用修复。

## JavaScript / Node：对象批量赋值

```javascript
Object.assign(user, req.body);
// 修复：明确可写字段，并校验类型/长度；role、tenantId 等由服务端决定
if (typeof req.body.name === 'string') user.name = req.body.name;
```

对应 mass-assignment。实际代码还需拒绝未知字段、限制长度和校验登录主体。对象合并与原型污染相关但不同，不把两者混为一个漏洞。

## Go：用户影响文件路径

```go
path := filepath.Join(baseDir, r.URL.Query().Get("name"))
data, err := os.ReadFile(path)
```

filepath.Join 规范化路径不意味着路径仍在 baseDir。修复要在规范化/解析路径后验证边界，并考虑符号链接、竞争条件和平台差异；简单字符串 `HasPrefix` 会被同名前缀目录误导。生产中优先用服务端生成的不透明文件 ID 查找受控路径。

## Rust：路径与身份无关

```rust
let order = repository.find_by_id(order_id).await?;
return Ok(Json(order));
```

内存安全不代替业务授权。应将 user/tenant/ownership 条件纳入查询或授权检查；若仅按 ID 查找后返回，攻击者如何获得或控制 order_id 需要用调用链证实。

## 答题表

| 语言 | Source | 缺失校验 | Sink | 影响前提 | 修复 | 正常回归 / 反例 |
|---|---|---|---|---|---|---|
| Python | q | 查询结构与数据未分离 | SQL 执行 | 外部可达、输入进入引号 | 参数化 | public 命中、异常字符串当数据 |
| 其他五种 | 自行填写 | | | | | |

给 AI 的任务：请检查我的数据流是否可达、是否遗漏前置条件，只指出需要补证的位置。不要依据一个函数名生成“确认漏洞”结论。
