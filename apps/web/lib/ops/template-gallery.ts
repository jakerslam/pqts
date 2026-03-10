import fs from "node:fs";
import path from "node:path";

import { resolveRepoRoot } from "@/lib/ops/repo-root";

export interface TemplateRunArtifact {
  mode: string;
  generated_at: string;
  template: string;
  resolved_strategy: string;
  config_path: string;
  command: string[];
  artifact_path: string;
  diff_path: string;
  config_sha256: string;
}

function reportsRoot(): string {
  return path.join(resolveRepoRoot(), "data", "reports");
}

function normalizeRelative(filePath: string): string {
  const repoRoot = resolveRepoRoot();
  return path.relative(repoRoot, filePath).replaceAll(path.sep, "/");
}

function listModes(): string[] {
  const root = reportsRoot();
  if (!fs.existsSync(root)) {
    return [];
  }
  return fs
    .readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
}

function readJson(filePath: string): Record<string, unknown> {
  try {
    const text = fs.readFileSync(filePath, "utf-8");
    const parsed = JSON.parse(text);
    return parsed && typeof parsed === "object" ? (parsed as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

export function listTemplateRunArtifacts(mode?: string, limit = 40): TemplateRunArtifact[] {
  const root = reportsRoot();
  if (!fs.existsSync(root)) {
    return [];
  }
  const modes = mode ? [mode] : listModes();
  const rows: TemplateRunArtifact[] = [];

  for (const currentMode of modes) {
    const modeDir = path.join(root, currentMode);
    if (!fs.existsSync(modeDir)) {
      continue;
    }
    const manifests = fs
      .readdirSync(modeDir)
      .filter((name) => /^template_run_\d{8}T\d{6}Z\.json$/.test(name))
      .sort()
      .reverse();

    for (const name of manifests) {
      const artifactPath = path.join(modeDir, name);
      const payload = readJson(artifactPath);
      const stamp = name.replace("template_run_", "").replace(".json", "");
      const diffPath = path.join(modeDir, `template_run_diff_${stamp}.diff`);
      rows.push({
        mode: currentMode,
        generated_at: String(payload.generated_at ?? ""),
        template: String(payload.template ?? "unknown"),
        resolved_strategy: String(payload.resolved_strategy ?? "unknown"),
        config_path: String(payload.config_path ?? ""),
        command: Array.isArray(payload.command)
          ? payload.command.map((token) => String(token))
          : [],
        artifact_path: normalizeRelative(artifactPath),
        diff_path: fs.existsSync(diffPath) ? normalizeRelative(diffPath) : "",
        config_sha256: String(payload.config_sha256 ?? ""),
      });
      if (rows.length >= Math.max(1, limit)) {
        return rows;
      }
    }
  }

  return rows;
}
