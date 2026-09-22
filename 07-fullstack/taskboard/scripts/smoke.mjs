import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";

const base = process.env.APP_ORIGIN || "http://127.0.0.1:3000";
const stateFile = process.env.SMOKE_STATE;
let cookie = "";
async function request(path, method = "GET", body) {
  const response = await fetch(base + path, {
    method,
    headers: {
      Origin: base,
      Cookie: cookie,
      "Content-Type": "application/json",
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
    signal: AbortSignal.timeout(10000),
  });
  return { response, data: await response.json() };
}
assert.equal((await request("/api/health")).data.database, "ok");
if (process.argv.includes("--verify")) {
  if (!stateFile)
    throw new Error("Set SMOKE_STATE to the state file from the first run");
  const state = JSON.parse(readFileSync(stateFile, "utf8"));
  cookie = state.cookie;
  assert.ok(
    (await request("/api/tasks")).data.tasks.some(
      (task) => task.id === state.taskId,
    ),
  );
  await request(`/api/tasks/${state.taskId}`, "DELETE");
  await request("/api/auth/logout", "POST");
  console.log(
    "PASS: task and session survived server restart; task cleaned up",
  );
} else {
  assert.equal((await request("/api/tasks")).response.status, 401);
  const created = await request("/api/auth/register", "POST", {
    email: `smoke-${randomUUID()}@example.test`,
    password: randomUUID(),
  });
  assert.equal(created.response.status, 201);
  cookie = created.response.headers.get("set-cookie").split(";")[0];
  const result = await request("/api/tasks", "POST", {
    title: "HTTP smoke verification",
    stage: 16,
  });
  assert.equal(result.response.status, 201);
  const taskId = result.data.task.id;
  assert.equal(
    (await request(`/api/tasks/${taskId}`, "PATCH", { status: "done" })).data
      .task.status,
    "done",
  );
  if (stateFile)
    writeFileSync(stateFile, JSON.stringify({ cookie, taskId }), {
      mode: 0o600,
    });
  else {
    assert.equal(
      (await request(`/api/tasks/${taskId}`, "DELETE")).response.status,
      200,
    );
    await request("/api/auth/logout", "POST");
  }
  console.log("PASS: real HTTP health, authentication, create and update");
}
