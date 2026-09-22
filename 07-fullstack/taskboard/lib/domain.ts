export const stages = [
  "HTML + CSS",
  "JavaScript",
  "Git + GitHub",
  "TypeScript",
  "React",
  "Next.js",
  "响应式设计 + UI",
  "APIs + REST",
  "后端",
  "数据库",
  "身份验证 + 授权",
  "测试",
  "Docker",
  "系统设计",
  "真实项目",
  "部署 + 监控 + 扩展",
] as const;
export const statuses = ["todo", "doing", "done"] as const;
export type Status = (typeof statuses)[number];
export type Task = {
  id: string;
  title: string;
  stage: number;
  status: Status;
  createdAt: string;
};
export type User = { id: string; email: string };

export class AppError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export function object(
  value: unknown,
  keys: string[],
): Record<string, unknown> {
  if (
    !value ||
    typeof value !== "object" ||
    Array.isArray(value) ||
    Object.keys(value).some((key) => !keys.includes(key))
  ) {
    throw new AppError(400, "请求字段不正确");
  }
  return value as Record<string, unknown>;
}

export function credentials(value: unknown) {
  const body = object(value, ["email", "password"]);
  if (
    typeof body.email !== "string" ||
    body.email.length > 254 ||
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(body.email.trim())
  ) {
    throw new AppError(400, "请输入有效邮箱");
  }
  if (
    typeof body.password !== "string" ||
    body.password.length < 12 ||
    body.password.length > 128
  ) {
    throw new AppError(400, "密码长度须为 12–128 个字符");
  }
  return { email: body.email.trim().toLowerCase(), password: body.password };
}

export function taskInput(value: unknown, current?: Task) {
  const body = object(
    value,
    current ? ["title", "stage", "status"] : ["title", "stage"],
  );
  if (!Object.keys(body).length) throw new AppError(400, "请提供要保存的字段");
  const title = body.title === undefined ? current?.title : body.title;
  const stage = body.stage === undefined ? current?.stage : body.stage;
  const status =
    body.status === undefined ? (current?.status ?? "todo") : body.status;
  if (typeof title !== "string" || !title.trim() || title.trim().length > 120) {
    throw new AppError(400, "任务标题须为 1–120 个字符");
  }
  if (
    typeof stage !== "number" ||
    !Number.isInteger(stage) ||
    stage < 1 ||
    stage > stages.length
  ) {
    throw new AppError(400, "学习阶段须为 1–16 的整数");
  }
  if (!statuses.includes(status as Status))
    throw new AppError(400, "任务状态不正确");
  return { title: title.trim(), stage, status: status as Status };
}

export function progress(tasks: Task[]) {
  const done = tasks.filter((task) => task.status === "done").length;
  return {
    total: tasks.length,
    done,
    percent: tasks.length ? Math.round((done / tasks.length) * 100) : 0,
  };
}
