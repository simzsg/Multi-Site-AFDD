import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const output = fileURLToPath(
  new URL("../../docs/screenshots/", import.meta.url),
);
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
await page.goto("http://127.0.0.1:5173", { waitUntil: "domcontentloaded" });
await page.getByTestId("equipment-scene").waitFor();
await page.screenshot({
  path: `${output}/01-portfolio-overview.png`,
  fullPage: true,
});

await page.getByRole("button", { name: "Issue investigation" }).click();
await page.getByRole("button", { name: /^AHU A F02 East/ }).click();
await page
  .getByRole("heading", { name: "What triggered this issue?" })
  .waitFor();
await page.screenshot({
  path: `${output}/02-issue-investigation.png`,
  fullPage: true,
});

const rulesResponse = await page.request.get("http://127.0.0.1:5173/api/rules");
const rules = await rulesResponse.json();
if (rules.some((rule) => rule.status === "DRAFT")) {
  await page.getByRole("button", { name: "Rule library" }).click();
  await page
    .locator(".rule-list button")
    .filter({ hasText: "DRAFT" })
    .last()
    .click();
  await page.getByRole("button", { name: "Preview saved targets" }).click();
} else {
  await page.getByRole("button", { name: "Create a rule" }).click();
  await page.getByRole("button", { name: "Generate rule draft" }).click();
  await page.getByText("DRAFT READY", { exact: true }).waitFor();
  await page.getByRole("button", { name: "Review draft & targets" }).click();
}
await page.getByRole("heading", { name: "Target preview" }).waitFor();
await page.screenshot({
  path: `${output}/03-rule-preview.png`,
  fullPage: true,
});

await page.getByRole("button", { name: "Pipeline health" }).click();
await page.getByRole("heading", { name: "Event trail" }).waitFor();
const filteredAudit = page.waitForResponse((response) =>
  response.url().includes("/api/audit?limit=40&action=rejected"),
);
await page.getByLabel("Audit event type").selectOption("rejected");
await filteredAudit;
await page.locator("tbody tr").nth(1).waitFor({ state: "detached" });
await page.getByRole("table").getByText("rejected", { exact: true }).waitFor();
await page.screenshot({
  path: `${output}/04-pipeline-health.png`,
  fullPage: false,
});
await browser.close();
