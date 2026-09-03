import assert from "node:assert/strict";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { report, reviewStatus } from "./report_frontend_licenses.mjs";

test("an unknown license requires review", () => {
  assert.equal(
    reviewStatus("frontend:unlicensed@1.0.0", "UNKNOWN", {
      allowed_license_expressions: ["MIT"],
      allowlist: {},
    }),
    "REVIEW_REQUIRED",
  );
});

test("report surfaces a controlled unknown license", async () => {
  const directory = await mkdtemp(join(tmpdir(), "cubeai-license-report-"));
  const lockPath = join(directory, "package-lock.json");
  const policyPath = join(directory, "policy.json");
  await writeFile(
    lockPath,
    JSON.stringify({
      lockfileVersion: 3,
      packages: {
        "": { name: "fixture" },
        "node_modules/unlicensed": { version: "1.0.0" },
      },
    }),
  );
  await writeFile(
    policyPath,
    JSON.stringify({ allowed_license_expressions: ["MIT"], allowlist: {} }),
  );
  const messages = [];
  const errors = [];
  const status = await report(lockPath, policyPath, {
    log(message) {
      messages.push(message);
    },
    error(message) {
      errors.push(message);
    },
  });

  assert.equal(status, 1);
  assert.ok(
    messages.includes("frontend\tunlicensed\t1.0.0\tUNKNOWN\tREVIEW_REQUIRED"),
  );
  assert.deepEqual(errors, ["REVIEW REQUIRED: 1 frontend package(s)"]);
});
