import { randomUUID } from "node:crypto";
import type { DatabaseSync } from "node:sqlite";
import { getDatabase } from "./db";
import {
  AppError,
  credentials,
  taskInput,
  type Task,
  type User,
} from "./domain";
import {
  checkLoginBudget,
  checkOrigin,
  hashPassword,
  issueSession,
  readToken,
  recordLoginFailure,
  sessionCookie,
  sessionUser,
  tokenHash,
  verifyPassword,
} from "./auth";

const taskColumns = "id, title, stage, status, created_at AS createdAt";
function json(data: unknown, status = 200, headers?: HeadersInit) {
  return Response.json(data, {
    status,
    headers: { "Cache-Control": "no-store", ...headers },
  });
}

async function readJson(request: Request) {
  if (
    request.headers.get("content-type")?.split(";")[0].trim() !==
    "application/json"
  ) {
    throw new AppError(415, "请使用 application/json");
  }
  const reader = request.body?.getReader();
  if (!reader) throw new AppError(400, "请求正文不能为空");
  const chunks: Uint8Array[] = [];
  let length = 0;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    length += value.byteLength;
    if (length > 8192) {
      await reader.cancel();
      throw new AppError(413, "请求正文过大");
    }
    chunks.push(value);
  }
  try {
    return JSON.parse(Buffer.concat(chunks).toString("utf8")) as unknown;
  } catch {
    throw new AppError(400, "JSON 格式不正确");
  }
}

async function dispatch(request: Request, db: DatabaseSync) {
  const path = new URL(request.url).pathname;
  const method = request.method;
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) checkOrigin(request);
  if (path === "/api/health" && method === "GET") {
    db.prepare("SELECT 1").get();
    return json({ status: "ok", database: "ok", schema: 1 });
  }
  if (
    (path === "/api/auth/register" || path === "/api/auth/login") &&
    method === "POST"
  ) {
    const { email, password } = credentials(await readJson(request));
    let user: User;
    if (path.endsWith("register")) {
      const id = randomUUID();
      const passwordHash = await hashPassword(password);
      try {
        db.prepare("INSERT INTO users VALUES (?, ?, ?)").run(
          id,
          email,
          passwordHash,
        );
      } catch (error) {
        if (
          error instanceof Error &&
          error.message.includes("UNIQUE constraint")
        ) {
          throw new AppError(409, "该邮箱已注册，请登录");
        }
        throw error;
      }
      user = { id, email };
    } else {
      checkLoginBudget(db, email);
      const found = db
        .prepare("SELECT id, email, password_hash FROM users WHERE email = ?")
        .get(email) as (User & { password_hash: string }) | undefined;
      if (!(await verifyPassword(password, found?.password_hash)) || !found) {
        recordLoginFailure(db, email);
        throw new AppError(401, "邮箱或密码不正确");
      }
      db.prepare("DELETE FROM login_attempts WHERE email = ?").run(email);
      user = { id: found.id, email: found.email };
    }
    return json({ user }, path.endsWith("register") ? 201 : 200, {
      "Set-Cookie": sessionCookie(issueSession(db, user.id)),
    });
  }
  if (path === "/api/auth/logout" && method === "POST") {
    db.prepare("DELETE FROM sessions WHERE token_hash = ?").run(
      tokenHash(readToken(request)),
    );
    return json({ ok: true }, 200, { "Set-Cookie": sessionCookie("") });
  }
  if (path === "/api/auth/me" && method === "GET")
    return json({ user: sessionUser(db, request) });
  if (path === "/api/tasks") {
    const user = sessionUser(db, request);
    if (method === "GET") {
      return json({
        tasks: db
          .prepare(
            `SELECT ${taskColumns} FROM tasks WHERE user_id = ? ORDER BY created_at DESC, id`,
          )
          .all(user.id),
      });
    }
    if (method === "POST") {
      const input = taskInput(await readJson(request));
      const task: Task = {
        id: randomUUID(),
        ...input,
        createdAt: new Date().toISOString(),
      };
      db.prepare("INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?)").run(
        task.id,
        user.id,
        task.title,
        task.stage,
        task.status,
        task.createdAt,
      );
      return json({ task }, 201);
    }
  }
  const match = /^\/api\/tasks\/([a-f0-9-]{36})$/.exec(path);
  if (match && ["PATCH", "DELETE"].includes(method)) {
    const user = sessionUser(db, request);
    const task = db
      .prepare(`SELECT ${taskColumns} FROM tasks WHERE id = ? AND user_id = ?`)
      .get(match[1], user.id) as Task | undefined;
    if (!task) throw new AppError(404, "任务不存在");
    if (method === "DELETE") {
      db.prepare("DELETE FROM tasks WHERE id = ? AND user_id = ?").run(
        task.id,
        user.id,
      );
      return json({ ok: true });
    }
    const input = taskInput(await readJson(request), task);
    db.prepare(
      "UPDATE tasks SET title = ?, stage = ?, status = ? WHERE id = ? AND user_id = ?",
    ).run(input.title, input.stage, input.status, task.id, user.id);
    return json({ task: { ...task, ...input } });
  }
  throw new AppError(404, "接口不存在");
}

export async function handle(request: Request, database?: DatabaseSync) {
  const started = performance.now();
  const requestId = randomUUID();
  let response: Response;
  try {
    response = await dispatch(request, database ?? getDatabase());
  } catch (error) {
    const known = error instanceof AppError;
    response = json(
      { error: known ? error.message : "服务暂时不可用", requestId },
      known ? error.status : 500,
    );
    if (!known)
      console.error(
        JSON.stringify({
          event: "server_error",
          requestId,
          type: error instanceof Error ? error.name : "unknown",
        }),
      );
  }
  response.headers.set("X-Request-Id", requestId);
  console.info(
    JSON.stringify({
      event: "request",
      requestId,
      method: request.method,
      path: new URL(request.url).pathname,
      status: response.status,
      durationMs: Math.round(performance.now() - started),
    }),
  );
  return response;
}
