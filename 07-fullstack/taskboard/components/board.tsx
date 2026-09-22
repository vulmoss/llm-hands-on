"use client";

import { useEffect, useState, type FormEvent } from "react";
import {
  progress,
  stages,
  statuses,
  type Status,
  type Task,
  type User,
} from "@/lib/domain";

const labels: Record<Status, string> = {
  todo: "待开始",
  doing: "进行中",
  done: "已完成",
};
async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...options,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "操作失败，请重试");
  return data as T;
}

export default function Board() {
  const [user, setUser] = useState<User | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [ready, setReady] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("register");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [filter, setFilter] = useState(0);
  const [title, setTitle] = useState("");
  const [stage, setStage] = useState(1);
  const [editing, setEditing] = useState<Task | null>(null);
  const summary = progress(tasks);
  const visible = tasks.filter((task) => !filter || task.stage === filter);

  useEffect(() => {
    let active = true;
    async function restore() {
      try {
        const response = await fetch("/api/auth/me", { cache: "no-store" });
        if (response.status === 401) return;
        if (!response.ok) throw new Error("无法恢复会话，请稍后重试");
        const identity = await response.json();
        const data = await api<{ tasks: Task[] }>("/api/tasks");
        if (active) {
          setUser(identity.user);
          setTasks(data.tasks);
        }
      } catch (cause) {
        if (active)
          setError(cause instanceof Error ? cause.message : "连接失败");
      } finally {
        if (active) setReady(true);
      }
    }
    void restore();
    return () => {
      active = false;
    };
  }, []);

  async function action(work: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await work();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "操作失败，请重试");
    } finally {
      setBusy(false);
    }
  }

  function authenticate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    void action(async () => {
      const result = await api<{ user: User }>(`/api/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify({
          email: form.get("email"),
          password: form.get("password"),
        }),
      });
      const data = await api<{ tasks: Task[] }>("/api/tasks");
      setUser(result.user);
      setTasks(data.tasks);
      setNotice("欢迎回来，开始今天的一小步。");
    });
  }

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void action(async () => {
      const { task } = await api<{ task: Task }>(
        editing ? `/api/tasks/${editing.id}` : "/api/tasks",
        {
          method: editing ? "PATCH" : "POST",
          body: JSON.stringify({ title, stage }),
        },
      );
      setTasks((previous) =>
        editing
          ? previous.map((item) => (item.id === task.id ? task : item))
          : [task, ...previous],
      );
      setTitle("");
      setEditing(null);
      setNotice(editing ? "任务已更新" : "任务已添加");
    });
  }

  function changeStatus(task: Task, status: Status) {
    void action(async () => {
      const result = await api<{ task: Task }>(`/api/tasks/${task.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      setTasks((previous) =>
        previous.map((item) => (item.id === task.id ? result.task : item)),
      );
      setNotice(
        status === "done" ? "又完成了一步，做得好。" : "任务状态已更新",
      );
    });
  }

  const message = (
    <div className="messages" aria-live="polite">
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {notice && <p className="notice">{notice}</p>}
    </div>
  );

  if (!ready)
    return (
      <main className="loading" aria-busy="true">
        正在准备你的学习空间…
      </main>
    );

  if (!user)
    return (
      <main className="welcome">
        <header className="brand">
          <span className="brand-mark">进</span>
          <strong>
            进度<span>LEARNING STUDIO</span>
          </strong>
        </header>
        <div className="welcome-grid">
          <section className="intro">
            <span className="eyebrow">从一个小任务，到一个真实项目</span>
            <h1>
              让学过的知识，
              <br />
              变成<span>做出来的东西。</span>
            </h1>
            <p>
              一条全栈路线，一个自己的看板。拆小目标，记录进展，
              <br className="desktop-break" />
              每天离完成更近一点。
            </p>
            <div className="path-preview">
              <span>01 · 页面</span>
              <i>→</i>
              <span>08 · API</span>
              <i>→</i>
              <span>16 · 上线</span>
            </div>
            <div className="sample-card">
              <span className="sample-tag">下一小步</span>
              <h2>让第一个页面跑起来</h2>
              <p>HTML + CSS · 基础从实践开始</p>
              <span className="sample-check">
                ✓ 写下目标 &nbsp; → &nbsp; 动手验证 &nbsp; → &nbsp; 记录成果
              </span>
            </div>
            <p className="intro-foot">
              16 个学习阶段 · 个人任务空间 · 进度始终可见
            </p>
          </section>
          <section className="auth-card" aria-label="账号">
            <span className="eyebrow">YOUR NEXT CHAPTER</span>
            <h2>
              {mode === "register" ? "开启你的学习空间" : "继续你的学习旅程"}
            </h2>
            <p>用自己的账号，保存每一次小小的进步。</p>
            <form onSubmit={authenticate}>
              <label htmlFor="email">邮箱</label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                maxLength={254}
                placeholder="you@example.com"
                required
              />
              <label htmlFor="password">密码</label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete={
                  mode === "register" ? "new-password" : "current-password"
                }
                minLength={12}
                maxLength={128}
                aria-describedby="password-help"
                required
              />
              <small id="password-help">
                12–128 个字符，可以使用一句容易记住的话。
              </small>
              <button className="primary full" disabled={busy}>
                {busy
                  ? "请稍候…"
                  : mode === "register"
                    ? "创建账号，开始学习 →"
                    : "登录看板 →"}
              </button>
            </form>
            {message}
            <p className="auth-switch">
              {mode === "register" ? "已经有账号？" : "第一次来？"}
              <button
                className="text-button"
                disabled={busy}
                onClick={() => {
                  setMode(mode === "register" ? "login" : "register");
                  setError("");
                }}
              >
                {mode === "register" ? "去登录" : "创建账号"}
              </button>
            </p>
            <div className="auth-note">先做好一件小事，再让它变得更好。</div>
          </section>
        </div>
        <footer>
          LLM HANDS-ON <span>学习是一条路，进度属于你。</span>
        </footer>
      </main>
    );

  return (
    <div className="workspace">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">进</span>
          <strong>
            进度<span>LEARNING STUDIO</span>
          </strong>
        </div>
        <p className="nav-heading">我的学习路线</p>
        <nav aria-label="学习阶段">
          <button
            className={filter === 0 ? "selected" : ""}
            onClick={() => setFilter(0)}
          >
            全部任务 <span>{tasks.length}</span>
          </button>
          {stages.map((name, index) => (
            <button
              key={name}
              className={filter === index + 1 ? "selected" : ""}
              onClick={() => setFilter(index + 1)}
            >
              <span className="stage-number">
                {String(index + 1).padStart(2, "0")}
              </span>
              {name}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          把目标变小，
          <br />
          把行动变成习惯。
        </div>
      </aside>
      <main className="main-board">
        <header className="board-header">
          <span className="eyebrow">MY LEARNING WORKSPACE</span>
          <div className="account">
            <span>{user.email}</span>
            <button
              className="text-button"
              disabled={busy}
              onClick={() =>
                void action(async () => {
                  await api("/api/auth/logout", { method: "POST" });
                  setUser(null);
                  setTasks([]);
                  setMode("login");
                  setEditing(null);
                  setTitle("");
                  setFilter(0);
                  setNotice("");
                })
              }
            >
              退出登录
            </button>
          </div>
        </header>
        <section className="board-intro">
          <div>
            <h1>每一步，都算数。</h1>
            <p>今天要完成哪一件小事？</p>
          </div>
          <span className="journey-badge">16 阶段 · 持续前进 ↗</span>
        </section>
        <section className="stats" aria-label="学习概览">
          <div>
            <span>全部任务</span>
            <strong>
              {summary.total}
              <small>项计划</small>
            </strong>
          </div>
          <div>
            <span>进行中</span>
            <strong>
              {tasks.filter((task) => task.status === "doing").length}
              <small>正在探索</small>
            </strong>
          </div>
          <div className="completion">
            <span>已完成</span>
            <strong>
              {summary.done}
              <small>{summary.percent}% 的任务</small>
            </strong>
            <progress
              aria-label="任务完成率"
              max={100}
              value={summary.percent}
            />
          </div>
        </section>
        <section
          className="composer"
          aria-label={editing ? "编辑任务" : "添加任务"}
        >
          <h2>{editing ? "编辑这一步" : "写下你的下一步"}</h2>
          <form onSubmit={save}>
            <div className="title-field">
              <label htmlFor="task-title">任务标题</label>
              <input
                id="task-title"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                required
                maxLength={120}
                placeholder="例如：用 CSS Grid 完成一个响应式页面"
              />
            </div>
            <div>
              <label htmlFor="task-stage">学习阶段</label>
              <select
                id="task-stage"
                value={stage}
                onChange={(event) => setStage(Number(event.target.value))}
              >
                {stages.map((name, index) => (
                  <option key={name} value={index + 1}>
                    {String(index + 1).padStart(2, "0")} · {name}
                  </option>
                ))}
              </select>
            </div>
            <button className="primary" disabled={busy}>
              {editing ? "保存修改" : "+ 添加任务"}
            </button>
            {editing && (
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  setEditing(null);
                  setTitle("");
                }}
              >
                取消
              </button>
            )}
          </form>
        </section>
        {message}
        <div className="board-toolbar">
          <h2>
            我的看板 <span>{visible.length}</span>
          </h2>
          <label>
            筛选阶段{" "}
            <select
              value={filter}
              onChange={(event) => setFilter(Number(event.target.value))}
            >
              <option value={0}>全部阶段</option>
              {stages.map((name, index) => (
                <option key={name} value={index + 1}>
                  {index + 1} · {name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="kanban">
          {statuses.map((status) => (
            <section
              className={`column ${status}`}
              key={status}
              aria-label={labels[status]}
            >
              <h3>
                <span className="dot" />
                {labels[status]}
                <span className="count">
                  {visible.filter((task) => task.status === status).length}
                </span>
              </h3>
              {visible
                .filter((task) => task.status === status)
                .map((task) => (
                  <article className="task-card" key={task.id}>
                    <span className="task-stage">
                      {String(task.stage).padStart(2, "0")} /{" "}
                      {stages[task.stage - 1]}
                    </span>
                    <h4>{task.title}</h4>
                    <div className="task-controls">
                      <label className="sr-only" htmlFor={`status-${task.id}`}>
                        {task.title} 的状态
                      </label>
                      <select
                        id={`status-${task.id}`}
                        disabled={busy}
                        value={task.status}
                        onChange={(event) =>
                          changeStatus(task, event.target.value as Status)
                        }
                      >
                        {statuses.map((value) => (
                          <option value={value} key={value}>
                            {labels[value]}
                          </option>
                        ))}
                      </select>
                      <button
                        className="text-button"
                        aria-label={`编辑 ${task.title}`}
                        disabled={busy}
                        onClick={() => {
                          setEditing(task);
                          setTitle(task.title);
                          setStage(task.stage);
                          document.getElementById("task-title")?.focus();
                        }}
                      >
                        编辑
                      </button>
                      <button
                        className="text-button danger"
                        aria-label={`删除 ${task.title}`}
                        disabled={busy}
                        onClick={() =>
                          void action(async () => {
                            await api(`/api/tasks/${task.id}`, {
                              method: "DELETE",
                            });
                            setTasks((previous) =>
                              previous.filter((item) => item.id !== task.id),
                            );
                            if (editing?.id === task.id) {
                              setEditing(null);
                              setTitle("");
                            }
                            setNotice("任务已删除");
                          })
                        }
                      >
                        删除
                      </button>
                    </div>
                  </article>
                ))}
              {!visible.some((task) => task.status === status) && (
                <div className="empty">
                  <span>{status === "done" ? "✓" : "+"}</span>
                  <p>
                    {status === "todo"
                      ? "一个清晰的小目标，\n就是很好的开始。"
                      : status === "doing"
                        ? "准备好了，就迈出第一步。"
                        : "完成的每一步，都会在这里。"}
                  </p>
                </div>
              )}
            </section>
          ))}
        </div>
        <footer>
          少一点收藏，多一点完成。<span>LLM HANDS-ON / FULLSTACK</span>
        </footer>
      </main>
    </div>
  );
}
