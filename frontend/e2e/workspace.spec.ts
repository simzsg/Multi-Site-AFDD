import { test, expect } from "@playwright/test";

test("portfolio, evidence and reviewed activation", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.setViewportSize({ width: 1440, height: 1040 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Your portfolio, in perspective." }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: /^(North Campus|Building A)$/ }),
  ).toBeVisible();
  await expect(page.getByTestId("equipment-scene")).toBeVisible();
  await page.getByRole("button", { name: "Table", exact: true }).click();
  await page
    .getByRole("button", { name: /^Investigate/ })
    .first()
    .click();
  await expect(
    page.getByRole("heading", { name: "What triggered this issue?" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Potentially affected spaces" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Create a rule" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Generate rule draft" }).click();
  await expect(page.getByText("DRAFT READY", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Review draft & targets" }).click();
  await expect(
    page.getByRole("heading", { name: "Target preview" }),
  ).toBeVisible();
  const activate = page.getByRole("button", { name: "Confirm & activate" });
  await expect(activate).toBeDisabled();
  await page
    .getByRole("textbox", { name: "Reviewer name" })
    .fill("Browser test reviewer");
  await page.getByRole("checkbox").check();
  await expect(activate).toBeEnabled();
  await activate.click();
  await expect(page.getByRole("status")).toContainText("Rule activated");
  expect(errors).toEqual([]);
});

test("mobile layout and no matching equipment", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /^(North Campus|Building A)$/ }),
  ).toBeVisible();
  await page
    .getByRole("textbox", { name: "Search equipment" })
    .fill("does-not-exist");
  await expect(
    page.getByRole("heading", { name: "No equipment matches this scope" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
});

test("3D models follow equipment selection, anatomy, cameras and measurement scope", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.setViewportSize({ width: 1440, height: 1040 });
  await page.goto("/");
  const scene = page.getByTestId("equipment-scene");
  await scene.scrollIntoViewIfNeeded();
  await expect(scene).toHaveAttribute("data-scene-state", "ready");
  await expect(page.locator("canvas")).toHaveCount(1);
  await page
    .getByRole("button", { name: "Inspect AHU A F02 East in 3D", exact: true })
    .click();
  await expect(page.getByTestId("inspector-equipment-name")).toHaveText(
    "AHU A F02 East",
  );
  await expect(
    page.getByRole("button", { name: "Inspect recovered issue" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Explore anatomy", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Close anatomy", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await scene.scrollIntoViewIfNeeded();
  await page.getByRole("button", { name: "front", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "front", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Reset 3D view" }).click();
  await expect(
    page.getByRole("button", { name: "isometric", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Air quality", exact: true }).click();
  await expect(page.getByTestId("inspector-equipment-name")).toHaveText(
    "IAQ A F01 East Room 1",
  );
  await expect(scene).toHaveAttribute("data-scene-state", "ready");
  await expect(page.locator("canvas")).toHaveCount(1);
  await page
    .getByRole("button", { name: "Energy meters", exact: true })
    .click();
  await expect(page.getByTestId("inspector-equipment-name")).toHaveText(
    "Building A Floor 1 Electricity Meter",
  );
  const inspector = page.getByRole("region", {
    name: /3D equipment inspector/,
  });
  await expect(inspector).toContainText("Building A Plant Room");
  await expect(inspector).toContainText("Floor 1");
  await expect(page.locator("canvas")).toHaveCount(1);
  await expect(scene).toHaveAttribute("data-scene-state", "ready");
  await page
    .getByRole("textbox", { name: "Search equipment" })
    .fill("does-not-exist");
  await expect(
    page.getByRole("heading", { name: "No equipment matches this scope" }),
  ).toBeVisible();
  await expect(page.locator("canvas")).toHaveCount(0);
  expect(errors).toEqual([]);
});

test("3D mobile controls and reduced motion remain usable", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const scene = page.getByTestId("equipment-scene");
  await scene.scrollIntoViewIfNeeded();
  await expect(scene).toHaveAttribute("data-scene-state", "ready");
  await page
    .getByRole("button", { name: "Explore anatomy", exact: true })
    .click();
  await page.getByRole("button", { name: "top", exact: true }).click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
});

test("equipment data remains available when WebGL is unavailable", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (
      type: string,
      ...args: unknown[]
    ) {
      if (
        type === "webgl" ||
        type === "webgl2" ||
        type === "experimental-webgl"
      )
        return null;
      return Reflect.apply(original, this, [type, ...args]);
    } as typeof original;
  });
  await page.goto("/");
  await expect(page.getByTestId("equipment-scene")).toHaveAttribute(
    "data-scene-state",
    "fallback",
  );
  await expect(
    page.getByRole("heading", { name: "3D preview unavailable" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Equipment readings" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Table", exact: true }).click();
  await expect(
    page.getByRole("columnheader", { name: "Supply air" }),
  ).toBeVisible();
});

test("3D telemetry uses API values and opens the selected point history", async ({
  page,
}) => {
  await page.goto("/");
  const scene = page.getByTestId("equipment-scene");
  await expect(scene).toHaveAttribute("data-scene-state", "ready");
  const sensor = page.getByTestId("sensor-Supply_Air_Temperature_Sensor");
  await expect(sensor).toContainText("GOOD");
  await expect(sensor).toContainText(/Fresh|Stale/);
  const before = await scene.locator('[data-line="0"]').getAttribute("x2");
  await page.getByRole("button", { name: "front", exact: true }).click();
  await expect
    .poll(() => scene.locator('[data-line="0"]').getAttribute("x2"))
    .not.toBe(before);
  const responsePromise = page.waitForResponse((r) =>
    r.url().includes("/history?limit=120"),
  );
  await sensor.click();
  const response = await responsePromise;
  const rows = await response.json();
  expect(rows.length).toBeGreaterThan(0);
  await expect(sensor).toContainText(rows.at(-1).value.toFixed(1));
  const history = page.getByRole("region", { name: "Selected point history" });
  await expect(history).toBeVisible();
  await expect(history).toContainText(rows.at(-1).point_id);
  await page.getByRole("button", { name: "Close history" }).click();
  await expect(history).toHaveCount(0);
});
