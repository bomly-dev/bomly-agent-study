import jwt from "jsonwebtoken";

// Signing/verifying session tokens for the bookmarks API.
//
// NOTE (fixture): this module is written against jsonwebtoken 8.x semantics.
// The tests in test/auth.test.js exercise the 8.x behaviour on purpose.
const SECRET = process.env.JWT_SECRET || "dev-only-fixture-secret";

// In 8.x, sign() accepts a payload that already carries its own `exp` claim
// as long as we do NOT also pass options.expiresIn. We build the expiry into
// the payload ourselves so callers can hand us fully-formed claim sets.
export function issueToken(claims, ttlSeconds = 3600) {
  const now = Math.floor(Date.now() / 1000);
  const payload = { ...claims, iat: now, exp: now + ttlSeconds };
  return jwt.sign(payload, SECRET, { algorithm: "HS256" });
}

export function verifyToken(token) {
  return jwt.verify(token, SECRET);
}

// 8.x returns the decoded payload (or null); we surface the raw header too.
export function inspect(token) {
  return jwt.decode(token, { complete: true });
}
