# 阶段 11：身份验证 + 授权

[返回路线](../README.md)

## 目标

证明“你是谁”和“你能操作哪条数据”分别成立。

## 阅读入口

[会话与密码](../taskboard/lib/auth.ts)、[API 集成测试](../taskboard/tests/api.test.ts)

## 核心概念

身份验证通过密码哈希与随机会话识别用户；授权通过 WHERE id = ? AND user_id = ? 限制每次访问。Cookie 为 HttpOnly/SameSite=Lax，HTTPS 来源启用 Secure。数据库只保存会话 token 的 SHA-256 摘要。

## 动手练习

1. 用正常窗口和无痕窗口注册两个账号。
2. 复制自己测试账号 A 的任务 ID，以 B 的会话发出 PATCH/DELETE，确认均为 404。
3. 退出后重用旧 Cookie，确认变为 401；在集成测试中检查过期会话和 10 次失败后的限流。

## 运行入口

以下从仓库根目录开始；如命令需要已启动的服务，先按项目 README 启动。

```bash
cd 07-fullstack/taskboard
npm test
```

## 验收

- [ ] 密码不以明文保存，登录与注册响应不包含密码哈希或会话 token 字段。
- [ ] 所有任务读取和变更都按当前用户过滤。
- [ ] 能解释 HttpOnly、SameSite、Origin 校验各解决什么问题，以及不能解决什么。

## 常见误区

这里没有忘记密码、邮箱验证或 MFA；公开产品应接入成熟身份系统，而不是把教学会话方案直接当完整身份平台。

把实际结果记入 [练习记录](../practice-log.md)。

下一单元：[阶段 12：测试：单元 + 集成 + E2E](12-testing.md)。
