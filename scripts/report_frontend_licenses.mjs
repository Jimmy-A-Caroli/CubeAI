import { readFile } from "node:fs/promises";
import process from "node:process";

const UNKNOWN_LICENSE = "UNKNOWN";

function packageNameFromPath(packagePath) {
  const marker = "node_modules/";
  const index = packagePath.lastIndexOf(marker);
  return index === -1 ? packagePath : packagePath.slice(index + marker.length);
}

function isIsoCalendarDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return false;
  }
  const [year, month, day] = value.split("-").map(Number);
  const parsed = new Date(Date.UTC(year, month - 1, day));
  return (
    parsed.getUTCFullYear() === year &&
    parsed.getUTCMonth() === month - 1 &&
    parsed.getUTCDate() === day
  );
}

function calendarDate(date) {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

export function reviewStatus(
  packageKey,
  licenseExpression,
  policy,
  today = new Date(),
) {
  if (policy.allowed_license_expressions.includes(licenseExpression)) {
    return "ALLOWED";
  }
  const exception = policy.allowlist?.[packageKey];
  if (
    !exception ||
    typeof exception !== "object" ||
    !["license", "reason", "reviewed_by", "expires_on"].every(
      (field) =>
        typeof exception[field] === "string" && exception[field].trim(),
    ) ||
    exception.license !== licenseExpression
  ) {
    return "REVIEW_REQUIRED";
  }
  if (!isIsoCalendarDate(exception.expires_on)) {
    return "REVIEW_REQUIRED";
  }
  return exception.expires_on >= calendarDate(today)
    ? "ALLOWLISTED"
    : "REVIEW_REQUIRED";
}

export async function report(
  lockPath,
  policyPath,
  output = console,
  today = new Date(),
) {
  const lock = JSON.parse(await readFile(lockPath, "utf8"));
  const policy = JSON.parse(await readFile(policyPath, "utf8"));
  if (
    !Array.isArray(policy.allowed_license_expressions) ||
    typeof policy.allowlist !== "object"
  ) {
    throw new Error("dependency license policy is malformed");
  }

  const rows = Object.entries(lock.packages ?? {})
    .filter(([packagePath]) => packagePath !== "")
    .map(([packagePath, packageInfo]) => {
      const name = packageInfo.name ?? packageNameFromPath(packagePath);
      const version = packageInfo.version ?? "UNKNOWN";
      const license =
        typeof packageInfo.license === "string" && packageInfo.license.trim()
          ? packageInfo.license.trim()
          : UNKNOWN_LICENSE;
      const status = reviewStatus(
        `frontend:${name}@${version}`,
        license,
        policy,
        today,
      );
      return { name, version, license, status };
    })
    .sort(
      (left, right) =>
        left.name.localeCompare(right.name) ||
        left.version.localeCompare(right.version),
    );

  output.log("workspace\tpackage\tversion\tlicense\tstatus");
  for (const row of rows) {
    output.log(
      `frontend\t${row.name}\t${row.version}\t${row.license}\t${row.status}`,
    );
  }
  const failures = rows.filter((row) => row.status === "REVIEW_REQUIRED");
  if (failures.length > 0) {
    output.error(`REVIEW REQUIRED: ${failures.length} frontend package(s)`);
    return 1;
  }
  return 0;
}

function argumentValue(argumentsList, name, defaultValue) {
  const index = argumentsList.indexOf(name);
  return index === -1 ? defaultValue : argumentsList[index + 1];
}

if (import.meta.main) {
  const root = new URL("..", import.meta.url);
  const lockPath = argumentValue(
    process.argv.slice(2),
    "--lock",
    new URL("frontend/package-lock.json", root),
  );
  const policyPath = argumentValue(
    process.argv.slice(2),
    "--policy",
    new URL("config/dependency-license-policy.json", root),
  );
  process.exitCode = await report(lockPath, policyPath);
}
