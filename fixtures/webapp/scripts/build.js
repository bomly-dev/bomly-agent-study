// Lightweight build step: load the full application module graph (so a broken
// or missing dependency fails the build), then emit a small build manifest.
// Dependency-free on purpose — the only devDependency is lodash (used by seed).
import { mkdirSync, writeFileSync } from "node:fs";
import { createApp } from "../src/app.js";

const app = createApp();
const routes = app._router.stack
  .filter((l) => l.route)
  .map((l) => `${Object.keys(l.route.methods)[0].toUpperCase()} ${l.route.path}`);

mkdirSync("dist", { recursive: true });
writeFileSync(
  "dist/build-manifest.json",
  JSON.stringify({ built: new Date().toISOString(), routes }, null, 2)
);
console.log(`build ok — ${routes.length} routes`);
