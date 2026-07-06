import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { fetchXml, importBookmarks } from "../src/importer.js";
import { createApp } from "../src/app.js";
import { listen } from "./helpers.js";

const SAMPLE = `<?xml version="1.0"?>
<bookmarks>
  <bookmark><title>Docs</title><url>https://docs.example.com</url></bookmark>
  <bookmark><title>Status</title><url>https://status.example.com</url></bookmark>
</bookmarks>`;

let origin;
let originBase;

before(async () => {
  origin = http.createServer((req, res) => {
    if (req.url === "/feed.xml") {
      res.setHeader("content-type", "application/xml");
      res.end(SAMPLE);
    } else {
      res.writeHead(404);
      res.end();
    }
  });
  await new Promise((r) => origin.listen(0, r));
  originBase = `http://127.0.0.1:${origin.address().port}`;
});

after(() => origin.close());

test("fetches a remote XML feed via request", async () => {
  const body = await fetchXml(`${originBase}/feed.xml`);
  assert.match(body, /<bookmarks>/);
});

test("parses bookmarks out of the XML", async () => {
  const items = await importBookmarks(SAMPLE);
  assert.equal(items.length, 2);
  assert.deepEqual(items[0], { title: "Docs", url: "https://docs.example.com" });
});

test("POST /import ingests an XML body", async () => {
  const { base, close } = await listen(createApp());
  try {
    const res = await fetch(`${base}/import`, {
      method: "POST",
      headers: { "content-type": "application/xml" },
      body: SAMPLE,
    });
    assert.equal(res.status, 200);
    assert.equal((await res.json()).imported, 2);
  } finally {
    close();
  }
});
