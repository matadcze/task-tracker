import { test, expect } from "@playwright/test";

const uniqueUser = () => {
  const stamp = Date.now();
  return {
    email: `smoke+${stamp}@example.com`,
    password: "Playwright!23",
    name: "Smoke User",
  };
};

const createTask = async (page: any, title: string) => {
  await page.getByRole("button", { name: "Add a task" }).click();
  await page.getByLabel(/Title/).fill(title);
  await page.getByLabel(/Description/).fill("Smoke test task created by Playwright");
  await page.getByRole("button", { name: /Create Task/i }).click();
  await expect(page.getByText(title)).toBeVisible();
};

test("user can register, create a task, and manage attachments", async ({ page }) => {
  const user = uniqueUser();
  const taskTitle = `Smoke Task ${Date.now()}`;

  await page.goto("/register");
  await page.getByPlaceholder("Full Name (optional)").fill(user.name);
  await page.getByPlaceholder("Email address").fill(user.email);
  await page.getByPlaceholder("Password (min 8 characters)").fill(user.password);
  await page.getByPlaceholder("Confirm password").fill(user.password);
  await page.getByRole("button", { name: /Sign up/i }).click();

  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByText("Task Tracker")).toBeVisible();

  await createTask(page, taskTitle);

  const card = page.locator("div", { hasText: taskTitle }).first();
  await card.getByRole("button", { name: "View" }).click();

  await expect(page.getByText("Attachments", { exact: false })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Files' })).toBeVisible();

  const fileName = `note-${Date.now()}.txt`;
  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles({ name: fileName, mimeType: "text/plain", buffer: Buffer.from("playwright smoke upload") });

  await expect(page.getByText(fileName)).toBeVisible({ timeout: 15_000 });
});

test("existing user can login and see dashboard", async ({ page }) => {
  // Assumes the first test already created a user; otherwise use an env-configured account.
  const email = process.env.SMOKE_USER_EMAIL;
  const password = process.env.SMOKE_USER_PASSWORD;

  test.skip(!email || !password, "SMOKE_USER_EMAIL and SMOKE_USER_PASSWORD must be set for login-only smoke test");

  await page.goto("/login");
  await page.getByPlaceholder("Email address").fill(email as string);
  await page.getByPlaceholder("Password").fill(password as string);
  await page.getByRole("button", { name: /Sign in/i }).click();

  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByText("Task Tracker")).toBeVisible();
});
