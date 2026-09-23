"""Synthetic requests and normal controls."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Case:
    id: str
    title: str
    method: str
    path: str
    vulnerable_status: int
    fixed_status: int
    marker: str = ""
    headers: dict = field(default_factory=lambda: {"Cookie": "sid=alice-lab"})
    body: dict | None = None
    control_path: str = "/health"
    control_method: str = "GET"
    control_body: dict | None = None
    control_headers: dict = field(default_factory=lambda: {"Cookie": "sid=alice-lab"})
    control_status: int = 200
    limitation: str = "教学数据；不能据此判断真实业务影响。"


CASES = [
    Case(
        "idor",
        "跨用户对象访问",
        "GET",
        "/orders?id=2",
        200,
        403,
        "B-book",
        control_path="/orders?id=1",
    ),
    Case(
        "mass-assignment",
        "角色字段批量赋值",
        "POST",
        "/profile",
        200,
        400,
        '"admin"',
        body={"name": "Alice", "role": "admin"},
        control_path="/profile",
        control_method="POST",
        control_body={"name": "Alice"},
    ),
    Case(
        "sqli",
        "SQLite 查询边界",
        "GET",
        "/search?q=%27%20OR%201%3D1--",
        200,
        200,
        "LAB_DRAFT_MARKER",
        control_path="/search?q=public",
    ),
    Case(
        "xss",
        "HTML 文本上下文反射",
        "GET",
        "/reflect?q=%3Csvg%20onload%3Dalert%281%29%3E",
        200,
        200,
        "<svg onload=alert(1)>",
        control_path="/reflect?q=hello",
        limitation="自动检查 HTML 转义；JavaScript 执行须另做浏览器验收。",
    ),
    Case(
        "csrf",
        "跨站修改请求",
        "POST",
        "/email",
        200,
        403,
        "changed@example.test",
        headers={"Cookie": "sid=alice-lab", "Origin": "https://other.example.test"},
        body={"email": "changed@example.test"},
        control_path="/email",
        control_method="POST",
        control_body={"email": "alice@example.test"},
        control_headers={
            "Cookie": "sid=alice-lab",
            "Origin": "{base}",
            "X-CSRF-Token": "lab-csrf-alice",
        },
        limitation="HTTP 重放人为携带 Cookie，不证明浏览器 SameSite 绕过；固定 token 仅教学。",
    ),
    Case(
        "cors",
        "凭据型 Origin 反射",
        "GET",
        "/cors",
        200,
        200,
        headers={"Origin": "https://other.example.test"},
        control_path="/cors",
        control_headers={"Origin": "https://dashboard.example.test"},
        limitation="响应头检查；敏感数据可读性、Cookie 策略需浏览器与业务证据。",
    ),
    Case(
        "redirect",
        "跳转白名单",
        "GET",
        "/redirect?next=https%3A%2F%2Fother.example.test",
        302,
        400,
        control_path="/redirect?next=%2Fhealth",
        control_status=302,
        limitation="客户端禁止跟随跳转，不会访问外部站点。",
    ),
    Case(
        "oauth",
        "OAuth state 缺失",
        "GET",
        "/oauth/callback?code=lab-code&state=wrong",
        200,
        403,
        "lab-account",
        control_path="/oauth/start",
        limitation="仅模拟回调 state/session/replay；不是完整 OAuth/OIDC、JWT 或 PKCE。",
    ),
    Case(
        "ssrf",
        "服务端越界取数",
        "GET",
        "/fetch?service=internal",
        200,
        403,
        "LAB_INTERNAL_MARKER",
        control_path="/fetch?service=public",
        limitation="真实 HTTP 仅到同进程回环回调；无云 metadata、DNS 重绑定或任意 URL。",
    ),
    Case(
        "upload",
        "文件名与下载边界",
        "GET",
        "/download?name=..%2Fprivate.txt",
        200,
        403,
        "LAB_PRIVATE_MARKER",
        control_path="/download?name=readme.txt",
        limitation="虚拟文件字典模拟路径，不读系统文件或执行上传内容；另有上传端点。",
    ),
    Case(
        "cloud-storage",
        "对象级读权限",
        "GET",
        "/objects?key=private.txt",
        200,
        403,
        "LAB_OBJECT_MARKER",
        headers={},
        control_path="/objects?key=public.txt",
        control_headers={},
        limitation="对象访问策略模型，不是 S3/OSS/COS 协议兼容模拟器。",
    ),
    Case(
        "business-logic",
        "价格与数量信任边界",
        "POST",
        "/checkout",
        200,
        400,
        '"total": -1',
        body={"quantity": -1, "unit_price": 1},
        control_path="/checkout",
        control_method="POST",
        control_body={"quantity": 2},
        limitation="整数分，不发起支付；未模拟真实并发与优惠叠加。",
    ),
]
BY_ID = {case.id: case for case in CASES}
