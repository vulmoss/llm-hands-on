# 前三课的原生页面

不需要 npm 或框架。从仓库根目录启动：

```bash
python3 -m http.server 8080 --bind 127.0.0.1 --directory 07-fullstack/foundations
```

访问 http://127.0.0.1:8080 。添加、勾选和删除任务；刷新后由 localStorage 恢复。
这份数据只属于当前浏览器，不具有账号隔离或跨设备同步能力。

- 阶段 1：先读 index.html 和 styles.css；临时移除 script 标签，观察语义结构与布局。
- 阶段 2：读 app.js，画出“提交 → 更新数组 → 保存 → 重新渲染”的流程。
- 阶段 3：用 Git 保存一次有针对性的变化。

打开 DevTools 查看 localStorage。备份自己的记录后，可在 Application 面板删除
`fullstack-foundations-tasks` 项来重置练习。
