import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { DatabaseSync } from "node:sqlite";

// Versioned, transactional migration; the SQL travels with the standalone build.
export function openDatabase(filename: string) {
  if (filename !== ":memory:")
    mkdirSync(dirname(resolve(filename)), { recursive: true });
  const db = new DatabaseSync(filename, { timeout: 5000 });
  db.exec("PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL;");
  const version = db.prepare("PRAGMA user_version").get() as {
    user_version: number;
  };
  if (version.user_version > 1) {
    db.close();
    throw new Error("Database schema is newer than this app");
  }
  if (version.user_version === 0) {
    db.exec(`BEGIN IMMEDIATE;
      CREATE TABLE users (
        id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL
      ) STRICT;
      CREATE TABLE sessions (
        token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at INTEGER NOT NULL
      ) STRICT;
      CREATE TABLE tasks (
        id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 120),
        stage INTEGER NOT NULL CHECK(stage BETWEEN 1 AND 16),
        status TEXT NOT NULL CHECK(status IN ('todo','doing','done')),
        created_at TEXT NOT NULL
      ) STRICT;
      CREATE INDEX tasks_by_owner ON tasks(user_id, created_at);
      CREATE TABLE login_attempts (
        email TEXT PRIMARY KEY, failures INTEGER NOT NULL, started_at INTEGER NOT NULL
      ) STRICT;
      PRAGMA user_version = 1;
      COMMIT;`);
  }
  return db;
}

const globalDb = globalThis as typeof globalThis & {
  taskboardDb?: DatabaseSync;
};
export function getDatabase() {
  return (globalDb.taskboardDb ??= openDatabase(
    process.env.DATABASE_PATH || ".data/taskboard.sqlite",
  ));
}
