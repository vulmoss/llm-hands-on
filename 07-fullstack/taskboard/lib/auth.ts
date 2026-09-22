import { createHash, randomBytes, scrypt, timingSafeEqual } from "node:crypto";
import type { DatabaseSync } from "node:sqlite";
import { AppError, type User } from "./domain";

export const SESSION_SECONDS = 60 * 60 * 24 * 7;
export const COOKIE = "learning_session";

function derive(password: string, salt: string): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    scrypt(
      password,
      salt,
      64,
      { N: 16384, r: 8, p: 1, maxmem: 64 * 1024 * 1024 },
      (error, key) => (error ? reject(error) : resolve(key)),
    );
  });
}
export async function hashPassword(password: string) {
  const salt = randomBytes(16).toString("hex");
  return `${salt}:${(await derive(password, salt)).toString("hex")}`;
}
export async function verifyPassword(password: string, stored?: string) {
  const [salt, hash] = stored?.split(":") ?? ["0".repeat(32), "0".repeat(128)];
  const actual = await derive(password, salt);
  const expected = Buffer.from(hash, "hex");
  return (
    expected.length === actual.length &&
    timingSafeEqual(expected, actual) &&
    Boolean(stored)
  );
}
export function tokenHash(token: string) {
  return createHash("sha256").update(token).digest("hex");
}
export function readToken(request: Request) {
  const value = request.headers
    .get("cookie")
    ?.split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${COOKIE}=`))
    ?.slice(COOKIE.length + 1);
  return value && /^[a-f0-9]{64}$/.test(value) ? value : "";
}
export function sessionUser(db: DatabaseSync, request: Request): User {
  const user = db
    .prepare(
      `SELECT users.id, users.email FROM sessions
    JOIN users ON users.id = sessions.user_id WHERE token_hash = ? AND expires_at > ?`,
    )
    .get(tokenHash(readToken(request)), Date.now()) as User | undefined;
  if (!user) throw new AppError(401, "请先登录");
  return user;
}
export function issueSession(db: DatabaseSync, userId: string) {
  const token = randomBytes(32).toString("hex");
  db.prepare("DELETE FROM sessions WHERE expires_at <= ?").run(Date.now());
  db.prepare("INSERT INTO sessions VALUES (?, ?, ?)").run(
    tokenHash(token),
    userId,
    Date.now() + SESSION_SECONDS * 1000,
  );
  return token;
}
export function origin() {
  return new URL(process.env.APP_ORIGIN || "http://127.0.0.1:3000").origin;
}
export function sessionCookie(token: string) {
  const secure = origin().startsWith("https:") ? "; Secure" : "";
  return `${COOKIE}=${token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${token ? SESSION_SECONDS : 0}${secure}`;
}
export function checkOrigin(request: Request) {
  if (request.headers.get("origin") !== origin())
    throw new AppError(403, "请求来源不匹配，请使用配置的应用地址");
}
export function checkLoginBudget(db: DatabaseSync, email: string) {
  db.prepare("DELETE FROM login_attempts WHERE started_at < ?").run(
    Date.now() - 15 * 60 * 1000,
  );
  const attempt = db
    .prepare("SELECT failures FROM login_attempts WHERE email = ?")
    .get(email);
  if (attempt && Number(attempt.failures) >= 10)
    throw new AppError(429, "尝试次数过多，请在 15 分钟后重试");
}
export function recordLoginFailure(db: DatabaseSync, email: string) {
  db.prepare(
    `INSERT INTO login_attempts VALUES (?, 1, ?)
    ON CONFLICT(email) DO UPDATE SET failures = failures + 1`,
  ).run(email, Date.now());
}
