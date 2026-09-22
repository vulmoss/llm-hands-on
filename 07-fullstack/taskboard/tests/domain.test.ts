import assert from "node:assert/strict";
import { test } from "node:test";
import { credentials, progress, taskInput, type Task } from "../lib/domain";
import { hashPassword, verifyPassword } from "../lib/auth";

test("empty progress is zero and completion rounds", () => {
  assert.deepEqual(progress([]), { total: 0, done: 0, percent: 0 });
  assert.equal(
    progress([
      { status: "done" },
      { status: "todo" },
      { status: "doing" },
    ] as Task[]).percent,
    33,
  );
});
test("email normalizes; password and unknown fields are validated", () => {
  assert.equal(
    credentials({
      email: " Learner@Example.test ",
      password: "a-long-passphrase",
    }).email,
    "learner@example.test",
  );
  assert.throws(() =>
    credentials({ email: "invalid", password: "a-long-passphrase" }),
  );
  assert.throws(() =>
    credentials({ email: "a@example.test", password: "short" }),
  );
  assert.throws(() =>
    credentials({
      email: "a@example.test",
      password: "a-long-passphrase",
      role: "admin",
    }),
  );
});
test("task input rejects invalid stages, empty titles, unknown fields and statuses", () => {
  assert.deepEqual(taskInput({ title: "  First page  ", stage: 1 }), {
    title: "First page",
    stage: 1,
    status: "todo",
  });
  for (const stage of [0, 17, 1.5, "1", null])
    assert.throws(() => taskInput({ title: "x", stage }));
  assert.throws(() => taskInput({ title: " ", stage: 1 }));
  assert.throws(() => taskInput({ title: "x".repeat(121), stage: 1 }));
  assert.throws(() =>
    taskInput({ title: "x", stage: 1, user_id: "another-user" }),
  );
  assert.throws(() =>
    taskInput({ status: "bad" }, { title: "x", stage: 1 } as Task),
  );
});
test("password hashes use unique salts and verify correctly", async () => {
  const first = await hashPassword("a-long-passphrase");
  const second = await hashPassword("a-long-passphrase");
  assert.notEqual(first, second);
  assert.equal(await verifyPassword("a-long-passphrase", first), true);
  assert.equal(await verifyPassword("another-passphrase", first), false);
  assert.equal(await verifyPassword("a-long-passphrase"), false);
});
