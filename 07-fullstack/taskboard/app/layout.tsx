import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "进度 · 全栈学习看板",
  description: "把全栈学习路线，变成每天可以完成的小任务。",
};
export default function Layout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
