# 阶段 13：Docker

[返回路线](../README.md)

## 目标

将依赖、应用与持久数据的生命周期分开。

## 阅读入口

[Dockerfile](../taskboard/Dockerfile)、[Compose](../taskboard/compose.yaml)

## 核心概念

构建阶段安装依赖并产出 standalone；运行阶段只携带运行所需文件，并使用非 root 用户。容器可替换，命名卷保留数据。健康检查调用真实数据库健康接口。

## 动手练习

1. 构建并启动容器，完成一次账号和任务操作。
2. 重启 app 容器，确认账号、Cookie 会话和任务仍然有效。
3. 查看日志和健康状态，解释 localhost 端口绑定与容器内部 0.0.0.0 的区别。

## 运行入口

以下从仓库根目录开始；如命令需要已启动的服务，先按项目 README 启动。

```bash
cd 07-fullstack/taskboard
docker compose up --build -d --wait
docker compose ps
docker compose logs --tail=30 app
```

## 验收

- [ ] docker compose up --build -d --wait 成功。
- [ ] 服务只绑定宿主机回环地址，卷持久化不依赖容器文件层。
- [ ] 知道 down 会保留数据，而 down -v 会删除练习数据库。

## 常见误区

不要把 .env.local、node_modules 或个人数据库复制到镜像中。

把实际结果记入 [练习记录](../practice-log.md)。

下一单元：[阶段 14：系统设计](14-system-design.md)。
