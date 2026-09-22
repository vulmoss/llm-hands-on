import { cpSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { spawn } from "node:child_process";

if (!existsSync(".next/standalone/server.js")) {
  console.error("请先运行 npm run build");
  process.exit(1);
}
cpSync(".next/static", ".next/standalone/.next/static", { recursive: true });
const server = spawn(process.execPath, [".next/standalone/server.js"], {
  stdio: "inherit",
  env: {
    ...process.env,
    HOSTNAME: process.env.BIND_HOST || "127.0.0.1",
    DATABASE_PATH: resolve(
      process.env.DATABASE_PATH || ".data/taskboard.sqlite",
    ),
  },
});
for (const signal of ["SIGINT", "SIGTERM"])
  process.on(signal, () => server.kill(signal));
server.on("exit", (code) => process.exit(code ?? 0));
server.on("error", (error) => {
  console.error(error.message);
  process.exit(1);
});
