# Dependency vulnerability remediation

Scope: `fixtures/webapp`. Findings are from `npm audit` against the original
lockfile, cross-checked against the npm registry for available fixed
versions. One entry per package.

## Direct dependencies

### axios (1.6.0 → 1.18.1)
Multiple advisories affecting axios `>=1.0.0 <1.15.2`: SSRF via absolute URL
and `NO_PROXY` bypass (GHSA-8hc4-vh64-cxmj, GHSA-jr5f-v2jv-69x6,
GHSA-3p68-rc4w-qgx5, GHSA-m7pr-hjqh-92cm, GHSA-pmwg-cvhr-8vh7), DoS via
missing response size checks and `__proto__` handling in `mergeConfig`
(GHSA-4hjh-wcwx-xvwj, GHSA-43fc-jf86-j433), and several prototype-pollution
gadgets enabling auth bypass, header injection, and response tampering
(GHSA-w9j2-pvgh-6h63, GHSA-3w6x-2g7m-8v23, GHSA-pf86-5x62-jrwf,
GHSA-6chq-wfr3-2hj9, GHSA-xx6v-rp6x-q39c, GHSA-q8qp-cvcw-x6jj,
GHSA-fvcv-3m26-pcqx, GHSA-445q-vr5w-6q77, GHSA-5c9x-8gcm-mpgx,
GHSA-vf2m-468p-8v99, GHSA-xhjh-pmcv-23jw). Bumped to the latest 1.x release,
1.18.1, which resolves all of the above. No code changes needed.

### express (4.19.2 → 4.22.2)
express itself carries a high-severity advisory for `<=4.21.2` plus pulls in
vulnerable transitive versions of `body-parser`, `cookie`, `path-to-regexp`,
`send`, and `serve-static` (see below). Bumped to 4.22.2, the latest 4.x
release, which upgrades all of these transitive deps at once without a
major-version jump. No code changes needed.

### jsonwebtoken (8.5.1 → 9.0.3)
High-severity advisory affecting `jsonwebtoken <=8.5.1`. No fixed 8.x release
exists — the fix requires the 9.x major. Verified the app's usage
(`src/auth.js`) against 9.x: it signs a payload that already contains its own
`exp`/`iat` without also passing `options.expiresIn`, which is still
supported in 9.x, so no code changes were required. Removed a stale comment
that said the code specifically depended on 8.x `sign()`/`decode()`
semantics — the behavior is unchanged under 9.x and all `test/auth.test.js`
cases still pass.

### request (2.88.2 → removed)
Critical advisory, and `request` has been deprecated by its maintainers with
no newer release published (2.88.2 is the final version on npm) — **there is
no version bump that fixes this package**. It was also the sole source of
several other vulnerable transitive packages in the tree: `form-data@2.3.3`
(critical, GHSA advisory for `<=2.5.5`), `qs@6.5.5`, `tough-cookie@2.5.0`,
and `uuid@3.4.0`.

Remediation: removed `request` entirely and rewrote its one call site,
`fetchXml` in `src/importer.js`, to use `axios` (already a direct dependency,
now on a patched version) instead. This drops `request` and its
vulnerable-only-transitively-required dependency subtree from the tree
completely. The previous implementation passed `jar: true` to enable
`request`'s cookie-jar support; that option had no test coverage and relied
on the vulnerable `tough-cookie` package, so it was dropped rather than
reimplemented — nothing in the app currently depends on cookie persistence
across the XML-feed fetch.

### xml2js (0.6.2)
No known vulnerability and no newer version exists (0.6.2 is latest). No
action taken.

## Transitive dependencies (fixed by upgrading the direct dependency above)

### body-parser (via express)
High-severity advisory for `express`-bundled `body-parser <=1.20.3`. Fixed by
the express 4.22.2 bump (now resolves to 1.20.6).

### cookie (via express)
Low-severity advisory for `cookie <0.7.0`. Fixed by the express 4.22.2 bump
(now resolves to 0.7.2).

### path-to-regexp (via express)
High-severity advisory for `path-to-regexp <=0.1.12`. Fixed by the express
4.22.2 bump (now resolves to 0.1.13).

### send (via express)
Low-severity advisory for `send <0.19.0`. Fixed by the express 4.22.2 bump
(now resolves to 0.19.2).

### serve-static (via express)
Low-severity advisory for `serve-static <=1.16.0`. Fixed by the express
4.22.2 bump (now resolves to 1.16.3).

### form-data (via request), qs (via request), tough-cookie (via request), uuid (via request)
All four were only present in the dependency tree because `request` pinned
old, vulnerable versions of each (`form-data@2.3.3`, `qs@6.5.5`,
`tough-cookie@2.5.0`, `uuid@3.4.0`) and `npm audit` could not auto-remediate
them for that reason (`fixAvailable: false`). `npm audit` reported the same
top-level `form-data` and `qs` advisory names as separate tree entries
because a second, unaffected copy of each (`form-data@4.0.6` via axios,
`qs@6.15.3` via express) also existed in the graph. Removing `request` (see
above) removes the vulnerable copies entirely; the app no longer depends on
`tough-cookie` or `uuid` at all.

## devDependencies

### lodash (4.17.20 → 4.18.1)
High-severity advisory for `lodash <=4.17.23` (used in `scripts/seed.js`).
Bumped to the latest release, 4.18.1. No code changes needed.

## Verification

- `npm audit` on the updated lockfile reports **0 vulnerabilities** (was 14:
  3 low, 3 moderate, 6 high, 2 critical).
- `make test` (clean `npm ci` + build + full test suite) passes: 12/12 tests
  green.
