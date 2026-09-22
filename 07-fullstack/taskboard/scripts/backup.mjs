import { existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { DatabaseSync, backup } from "node:sqlite";

const source = resolve(process.env.DATABASE_PATH || ".data/taskboard.sqlite");
const destination = resolve(
  process.argv[2] || `.data/backups/taskboard-${Date.now()}.sqlite`,
);
if (!existsSync(source) || source === destination || existsSync(destination)) {
  throw new Error("源数据库必须存在，备份目标必须是新的独立文件");
}
mkdirSync(dirname(destination), { recursive: true });
const db = new DatabaseSync(source, { readOnly: true });
try {
  await backup(db, destination);
  console.log(`Backup created: ${destination}`);
} finally {
  db.close();
}
