# Dependency vulnerability remediation

Scope: `fixtures/webapp`. Findings were identified with the `bomly` MCP
server (`bomly_scan` / `bomly_explain`, both with `enrich=true audit=true`)
against `fixtures/webapp/package-lock.json`, then verified with
`npm install`, `npm run build`, and `npm test` (also exercised end-to-end via
`make test` at the repo root).

Initial scan: 15 vulnerable packages (1 critical, 16 high, 17 medium, 5 low
across 39 findings). After remediation: 2 vulnerable packages remain, both
with no fix available without breaking the application (see below).

## Direct dependencies bumped

- **axios** `1.6.0` → `1.16.0`. Fixed 15 advisories (SSRF, prototype
  pollution leading to MITM/credential theft/header injection/DoS, ReDoS,
  proxy-auth header leak, etc.), the most severe being
  GHSA-35jp-ww65-95wh / CVE-2026-44494 (high). All fixes landed by 1.16.0.
- **express** `4.19.2` → `4.20.0`. Fixed GHSA-qw6h-vgh9-j6wx /
  CVE-2024-43796 (XSS via `response.redirect()`). Express's transitive
  dependencies still needed manifest-level overrides — see below.
- **jsonwebtoken** `8.5.1` → `9.0.3`. Fixed GHSA-8cf7-32gw-wr33 (unrestricted
  key type usage), GHSA-hjrf-2m68-5959 (RSA-to-HMAC key confusion), and
  GHSA-qwph-4952-7xr6 (insecure default `algorithms` in `jwt.verify()`) —
  all high/medium. `8.5.1` is the newest 8.x release, so no in-range fix
  existed; the major bump was required. `src/auth.js` carries a comment
  claiming the code depends on "8.x semantics" for `sign()`/`verify()`, but
  the full existing test suite (`test/auth.test.js`, 4 tests) passes
  unmodified against 9.0.3 — the behaviors it relies on (payload-supplied
  `exp` without `options.expiresIn`, default algorithm inference for a
  string/HMAC secret) are unchanged in 9.x. No code changes were needed.
- **lodash** (devDependency) `4.17.20` → `4.18.1`. Fixes GHSA-35jh-r3h4-6jhm
  (command injection, high), GHSA-r5fr-rjxr-66jc (code injection via
  `_.template`, high), GHSA-29mw-wpgm-hmr9 (ReDoS, medium),
  GHSA-f23m-r3pf-42rh (prototype pollution via `_.unset`/`_.omit`, medium),
  and GHSA-xxjr-mmjv-4gpg (prototype pollution, medium). Note: `4.18.0` (the
  version the scanner initially pointed at) is marked "Bad release" on the
  npm registry with an explicit deprecation notice recommending `4.17.21`;
  `4.18.1` is the current, non-deprecated release and carries the same
  fixes, so that's what was pinned instead.
- **xml2js** `0.6.2` — no known vulnerabilities; left unchanged.

## Transitive dependencies pinned via `overrides`

Added to `fixtures/webapp/package.json`:

```json
"overrides": {
  "form-data": "2.5.6",
  "qs": "6.15.2",
  "tough-cookie": "4.1.3",
  "path-to-regexp": "0.1.13",
  "body-parser": "1.20.3",
  "send": "0.19.0",
  "cookie": "0.7.0"
}
```

- **form-data** (via `request`) `2.3.3` → `2.5.6`. Fixes
  GHSA-fjxv-7rqg-78g4 (unsafe random multipart boundary, critical) and
  GHSA-hmw2-7cc7-3qxx (CRLF injection in field/file names, high).
- **qs** (via both `request` and `express`) → `6.15.2`. Fixes
  GHSA-6rw7-vpxm-498p (arrayLimit bypass DoS), GHSA-w7fw-mjwx-w883
  (comma-parsing arrayLimit bypass DoS), and GHSA-q8mj-m7cp-5q26 (crash on
  null/undefined entries in `qs.stringify`) — the last of which only
  surfaced after bumping express to 4.20.0 pulled in a newer `qs`.
- **tough-cookie** (via `request`) `2.5.0` → `4.1.3`. Fixes
  GHSA-72xf-g2v4-qvf3 (prototype pollution, medium).
- **path-to-regexp** (via `express`) `0.1.7` → `0.1.13`. Fixes
  GHSA-37ch-88jc-xwx2, GHSA-9wv6-86v2-598j, and GHSA-rhx6-c78j-4q9w
  (ReDoS, high).
- **body-parser** (via `express`) `1.20.2` → `1.20.3`. Fixes
  GHSA-qwcr-r2fm-qrc7 (DoS with URL encoding enabled, high).
- **send** / **cookie** (via `express`) → `0.19.0` / `0.7.0`. Fix
  GHSA-m6fv-jmcg-4jfg (template-injection XSS) and GHSA-pxg6-pf52-xh8x
  (out-of-bounds characters accepted in cookie name/path/domain).

All overrides were verified by re-running `bomly_scan` (findings for these
packages dropped out) and `npm test` / `make test`.

## Not fixed — no viable remediation

- **request** `2.88.2` — GHSA-p8p7-x288-28g6 / CVE-2023-28155 (SSRF via
  redirect handling, medium). `request` has been deprecated upstream since
  2020 and **2.88.2 is its final release**; no newer version exists that
  fixes this, so it cannot be remediated by a version bump. Replacing the
  library is a code change beyond the scope of dependency remediation, so
  it was left in place and is called out here explicitly rather than
  claiming a nonexistent fix.
- **uuid** `3.4.0` (transitive, via `request`) — GHSA-w5hq-g745-h8pq /
  CVE-2026-41907 (missing buffer bounds check in v3/v5/v6 when a `buf` is
  supplied, medium). A fix exists (`11.1.1`), but it cannot be applied here:
  `request`'s own code (`lib/oauth.js`, `lib/multipart.js`, `lib/auth.js`)
  does `require('uuid/v4')`, a legacy subpath. `uuid` added a restrictive
  `exports` map starting at `8.0.0` that removes that subpath entirely, so
  any override to a fixed version (`8.0.0`+) breaks module resolution at
  build time (`ERR_PACKAGE_PATH_NOT_EXPORTED`) — confirmed by actually
  applying the override and running `npm run build`. Since `request` is
  unmaintained (see above) and never updated its `uuid` usage to the new
  export style, there is no version of `uuid` that is both fixed and
  compatible with the installed `request`. Left at the version npm
  resolves by default (`3.4.0`) and documented here rather than forcing a
  broken override.

Both remaining findings trace back to the same root cause: `request` is an
unmaintained package pinned at its last-ever release. Removing/replacing it
would resolve both, but that is a code change (there is exactly one call
site, `src/importer.js`), not a dependency-version remediation, so it was
left out of this pass per scope.
