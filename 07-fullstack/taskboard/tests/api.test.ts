import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { handle } from "../lib/api";
import { openDatabase } from "../lib/db";
import { tokenHash } from "../lib/auth";

const base = "http://127.0.0.1:3000";
process.env.APP_ORIGIN = base;
function client(db: ReturnType<typeof openDatabase>, cookie = "") {
  return async (
    path: string,
    method = "GET",
    body?: unknown,
    extra?: Record<string, string>,
  ) => {
    const response = await handle(
      new Request(base + path, {
        method,
        headers: {
          Origin: base,
          "Content-Type": "application/json",
          Cookie: cookie,
          ...extra,
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      }),
      db,
    );
    return { response, data: await response.json() };
  };
}
async function register(db: ReturnType<typeof openDatabase>, email: string) {
  const result = await client(db)("/api/auth/register", "POST", {
    email,
    password: "a-long-passphrase",
  });
  assert.equal(result.response.status, 201);
  const cookie = result.response.headers.get("set-cookie")!;
  assert.match(cookie, /HttpOnly; SameSite=Lax/);
  return {
    ...result,
    cookie: cookie.split(";")[0],
    call: client(db, cookie.split(";")[0]),
  };
}

test("registration, CRUD, per-user authorization and logout", async () => {
  const db = openDatabase(":memory:");
  try {
    assert.equal((await client(db)("/api/tasks")).response.status, 401);
    const alice = await register(db, "alice@example.test");
    const bob = await register(db, "bob@example.test");
    const created = await alice.call("/api/tasks", "POST", {
      title: "First page",
      stage: 1,
    });
    assert.equal(created.response.status, 201);
    const id = created.data.task.id;
    assert.equal((await alice.call("/api/tasks")).data.tasks.length, 1);
    assert.deepEqual((await bob.call("/api/tasks")).data.tasks, []);
    assert.equal(
      (await bob.call(`/api/tasks/${id}`, "PATCH", { status: "done" })).response
        .status,
      404,
    );
    assert.equal(
      (await bob.call(`/api/tasks/${id}`, "DELETE")).response.status,
      404,
    );
    const edited = await alice.call(`/api/tasks/${id}`, "PATCH", {
      title: "React page",
      stage: 5,
      status: "done",
    });
    assert.equal(edited.data.task.status, "done");
    assert.equal(edited.data.task.stage, 5);
    assert.equal(
      (await alice.call(`/api/tasks/${id}`, "DELETE")).response.status,
      200,
    );
    assert.equal((await alice.call("/api/tasks")).data.tasks.length, 0);
    await alice.call("/api/auth/logout", "POST");
    assert.equal((await alice.call("/api/auth/me")).response.status, 401);
  } finally {
    db.close();
  }
});

test("input, duplicate registration, invalid JSON and origin checks", async () => {
  const db = openDatabase(":memory:");
  try {
    const alice = await register(db, "alice@example.test");
    assert.equal(
      (
        await client(db)("/api/auth/register", "POST", {
          email: "ALICE@example.test",
          password: "a-long-passphrase",
        })
      ).response.status,
      409,
    );
    assert.equal(
      (
        await alice.call("/api/tasks", "POST", {
          title: "x",
          stage: 1,
          user_id: "bob",
        })
      ).response.status,
      400,
    );
    assert.equal(
      (await alice.call("/api/tasks", "POST", { title: "x", stage: 17 }))
        .response.status,
      400,
    );
    assert.equal(
      (
        await alice.call(
          "/api/tasks",
          "POST",
          { title: "x", stage: 1 },
          { Origin: "https://other.example" },
        )
      ).response.status,
      403,
    );
    assert.equal(
      (await alice.call("/api/auth/logout", "POST", undefined, { Origin: "" }))
        .response.status,
      403,
    );
    const malformed = await handle(
      new Request(base + "/api/tasks", {
        method: "POST",
        headers: {
          Origin: base,
          Cookie: alice.cookie,
          "Content-Type": "application/json",
        },
        body: "{",
      }),
      db,
    );
    assert.equal(malformed.status, 400);
    assert.equal(
      (
        await alice.call("/api/tasks", "POST", {
          title: "x".repeat(9000),
          stage: 1,
        })
      ).response.status,
      413,
    );
    assert.equal(
      (
        await alice.call(
          "/api/tasks",
          "POST",
          {},
          { "Content-Type": "text/plain" },
        )
      ).response.status,
      415,
    );
    assert.equal(
      (
        await alice.call("/api/tasks", "POST", {
          title: "literal ' SQL; --",
          stage: 1,
        })
      ).response.status,
      201,
    );
  } finally {
    db.close();
  }
});

test("session expiry, hashed tokens and failed-login budget", async () => {
  const db = openDatabase(":memory:");
  try {
    const alice = await register(db, "alice@example.test");
    const token = alice.cookie.split("=")[1];
    const stored = db.prepare("SELECT token_hash FROM sessions").get()!;
    assert.equal(stored.token_hash, tokenHash(token));
    assert.notEqual(stored.token_hash, token);
    db.prepare("UPDATE sessions SET expires_at = 0").run();
    assert.equal((await alice.call("/api/auth/me")).response.status, 401);
    for (let i = 0; i < 10; i++) {
      assert.equal(
        (
          await client(db)("/api/auth/login", "POST", {
            email: "alice@example.test",
            password: "incorrect-passphrase",
          })
        ).response.status,
        401,
      );
    }
    assert.equal(
      (
        await client(db)("/api/auth/login", "POST", {
          email: "alice@example.test",
          password: "a-long-passphrase",
        })
      ).response.status,
      429,
    );
    db.prepare("UPDATE login_attempts SET started_at = 0").run();
    assert.equal(
      (
        await client(db)("/api/auth/login", "POST", {
          email: "alice@example.test",
          password: "a-long-passphrase",
        })
      ).response.status,
      200,
    );
  } finally {
    db.close();
  }
});

test("data and session survive closing and reopening the SQLite file", async () => {
  const dir = mkdtempSync(join(tmpdir(), "learning-db-"));
  let db = openDatabase(join(dir, "test.sqlite"));
  try {
    const alice = await register(db, "persist@example.test");
    await alice.call("/api/tasks", "POST", { title: "Persist me", stage: 10 });
    db.close();
    db = openDatabase(join(dir, "test.sqlite"));
    const result = await client(db, alice.cookie)("/api/tasks");
    assert.equal(result.response.status, 200);
    assert.equal(result.data.tasks[0].title, "Persist me");
    assert.equal(db.prepare("PRAGMA user_version").get()!.user_version, 1);
  } finally {
    db.close();
    rmSync(dir, { recursive: true, force: true });
  }
});
