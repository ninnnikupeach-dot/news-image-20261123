import { fileURLToPath } from "node:url";
import fs from "node:fs";
import path from "node:path";

// Pin paths to this file so the copy still works when the process
// is launched from another working directory.
const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const sourceImage = path.join(scriptDir, "entry.png");

// Judges set MAKEFUN_OUTPUT_DIR; fall back to /output for local runs.
const outputDir = process.env.MAKEFUN_OUTPUT_DIR || "/output";
const destination = path.join(outputDir, "entry.png");

fs.mkdirSync(outputDir, { recursive: true });
fs.copyFileSync(sourceImage, destination);
