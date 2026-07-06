import express from "express";
import { issueToken, verifyToken } from "./auth.js";
import { preview } from "./fetch.js";
import { importBookmarks } from "./importer.js";

// In-memory store — this is a fixture, not a real service.
const bookmarks = [];

export function createApp() {
  const app = express();
  app.use(express.json());
  app.use(express.text({ type: ["application/xml", "text/xml"] }));

  app.post("/login", (req, res) => {
    const { user } = req.body || {};
    if (!user) return res.status(400).json({ error: "user required" });
    const token = issueToken({ sub: user, role: "member" });
    res.json({ token });
  });

  app.get("/me", (req, res) => {
    const header = req.get("authorization") || "";
    const token = header.replace(/^Bearer\s+/i, "");
    try {
      const claims = verifyToken(token);
      res.json({ user: claims.sub, role: claims.role });
    } catch {
      res.status(401).json({ error: "invalid token" });
    }
  });

  app.get("/preview", async (req, res) => {
    const { url } = req.query;
    if (!url) return res.status(400).json({ error: "url required" });
    const rawQuery = req.originalUrl.split("?")[1] || "";
    try {
      const result = await preview(String(url), rawQuery);
      res.json(result);
    } catch (err) {
      res.status(502).json({ error: String(err.message || err) });
    }
  });

  app.post("/import", async (req, res) => {
    const xml = typeof req.body === "string" ? req.body : "";
    if (!xml) return res.status(400).json({ error: "xml body required" });
    try {
      const imported = await importBookmarks(xml);
      bookmarks.push(...imported);
      res.json({ imported: imported.length, total: bookmarks.length });
    } catch (err) {
      res.status(400).json({ error: String(err.message || err) });
    }
  });

  app.get("/bookmarks", (_req, res) => res.json({ bookmarks }));

  return app;
}
