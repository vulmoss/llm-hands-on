import { randomUUID } from "node:crypto";
import { test, expect } from "@playwright/test";

test("register, create, edit, complete, refresh, login and delete", async ({
  page,
}) => {
  const email = `learner-${randomUUID()}@example.test`;
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "开启你的学习空间" }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/welcome-desktop.png",
    fullPage: true,
  });
  await page.getByLabel("邮箱", { exact: true }).fill(email);
  await page.getByLabel("密码", { exact: true }).fill("my-learning-passphrase");
  await page.getByRole("button", { name: "创建账号，开始学习" }).click();
  await expect(
    page.getByRole("heading", { name: "每一步，都算数。" }),
  ).toBeVisible();
  await page.getByLabel("任务标题", { exact: true }).fill("完成第一个页面");
  await page
    .getByRole("combobox", { name: "学习阶段", exact: true })
    .selectOption("1");
  await page.getByRole("button", { name: "+ 添加任务", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "完成第一个页面", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "编辑 完成第一个页面", exact: true })
    .click();
  await page.getByLabel("任务标题", { exact: true }).fill("完成响应式页面");
  await page
    .getByRole("combobox", { name: "学习阶段", exact: true })
    .selectOption("7");
  await page.getByRole("button", { name: "保存修改", exact: true }).click();
  await page
    .getByLabel("完成响应式页面 的状态", { exact: true })
    .selectOption("done");
  await expect(
    page.getByRole("progressbar", { name: "任务完成率" }),
  ).toHaveAttribute("value", "100");
  await page.getByRole("combobox", { name: "筛选阶段" }).selectOption("1");
  await expect(
    page.getByRole("heading", { name: "完成响应式页面", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("combobox", { name: "筛选阶段" }).selectOption("0");
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "完成响应式页面", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/board-desktop.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "退出登录" }).click();
  await page.getByLabel("邮箱", { exact: true }).fill(email);
  await page.getByLabel("密码", { exact: true }).fill("my-learning-passphrase");
  await page.getByRole("button", { name: "登录看板" }).click();
  await page
    .getByRole("button", { name: "删除 完成响应式页面", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "完成响应式页面", exact: true }),
  ).toHaveCount(0);
  await expect(page.getByText("任务已删除", { exact: true })).toBeVisible();
});

test("mobile layout fits viewport and renders user content as text", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page
    .getByLabel("邮箱", { exact: true })
    .fill(`mobile-${randomUUID()}@example.test`);
  await page.getByLabel("密码", { exact: true }).fill("my-mobile-passphrase");
  await page.getByRole("button", { name: "创建账号，开始学习" }).click();
  const title = '<img src=x onerror="alert(1)">';
  await page.getByLabel("任务标题", { exact: true }).fill(title);
  await page.getByRole("button", { name: "+ 添加任务", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: title, exact: true }),
  ).toBeVisible();
  await expect(page.locator("article img")).toHaveCount(0);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/board-mobile.png",
    fullPage: true,
  });
});
