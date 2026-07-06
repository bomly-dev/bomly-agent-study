import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { parseFetchOptions, preview } from "../src/fetch.js";

// A tiny local origin so the axios path is exercised without real network.
let server;
let base;

before(async () => {
  server = http.createServer((req, res) => {
    if (req.url === "/hello") {
      res.setHeader("content-type", "text/plain");
      res.end("hello world");
    } else if (req.url === "/once") {
      res.writeHead(302, { location: "/hello" });
      res.end();
    } else {
      res.writeHead(404);
      res.end("nope");
    }
  });
  await new Promise((r) => server.listen(0, r));
  base = `http://127.0.0.1:${server.address().port}`;
});

after(() => server.close());

test("parses flat query params", () => {
  assert.deepEqual(parseFetchOptions("timeout=1234&maxRedirects=2"), {
    timeout: 1234,
    maxRedirects: 2,
  });
});

test("defaults when params are absent", () => {
  assert.deepEqual(parseFetchOptions(""), { timeout: 5000, maxRedirects: 5 });
});

test("preview returns a plain 200 response", async () => {
  const out = await preview(`${base}/hello`);
  assert.equal(out.status, 200);
  assert.match(out.snippet, /hello world/);
});

test("preview follows a redirect to the final body", async () => {
  const out = await preview(`${base}/once`, "maxRedirects=3");
  assert.equal(out.status, 200);
  assert.match(out.snippet, /hello world/);
});
