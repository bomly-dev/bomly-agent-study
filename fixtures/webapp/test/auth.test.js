import { test } from "node:test";
import assert from "node:assert/strict";
import { createApp } from "../src/app.js";
import { issueToken, verifyToken, inspect } from "../src/auth.js";
import { listen } from "./helpers.js";

test("issues a token whose payload round-trips through verify", () => {
  const token = issueToken({ sub: "alice", role: "member" }, 3600);
  const claims = verifyToken(token);
  assert.equal(claims.sub, "alice");
  assert.equal(claims.role, "member");
  assert.equal(typeof claims.exp, "number");
  assert.equal(claims.exp - claims.iat, 3600);
});

test("signs with HS256 and exposes the header via decode(complete)", () => {
  const decoded = inspect(issueToken({ sub: "bob" }));
  assert.equal(decoded.header.alg, "HS256");
  assert.equal(decoded.header.typ, "JWT");
});

test("login then /me returns the authenticated user", async () => {
  const { base, close } = await listen(createApp());
  try {
    const login = await fetch(`${base}/login`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ user: "carol" }),
    });
    assert.equal(login.status, 200);
    const { token } = await login.json();
    const me = await fetch(`${base}/me`, {
      headers: { authorization: `Bearer ${token}` },
    });
    assert.equal(me.status, 200);
    assert.equal((await me.json()).user, "carol");
  } finally {
    close();
  }
});

test("rejects a garbage token", async () => {
  const { base, close } = await listen(createApp());
  try {
    const me = await fetch(`${base}/me`, {
      headers: { authorization: "Bearer not.a.jwt" },
    });
    assert.equal(me.status, 401);
  } finally {
    close();
  }
});
