# Dependency remediation log

Scope: `fixtures/webapp` (npm), `fixtures/service` (pip), `fixtures/api-java`
(Maven). Tools used: `npm audit`, `pip-audit`, `trivy fs`, plus Maven Central /
PyPI / npm registry metadata to confirm which fixed versions actually exist.
One entry per vulnerable package.

## fixtures/webapp (npm)

- **axios `1.6.0` → `1.18.1`.** `npm audit` reported multiple SSRF, prototype
  pollution, and DoS advisories affecting axios up to 1.15.2 (e.g.
  GHSA-8hc4-vh64-cxmj, GHSA-jr5f-v2jv-69x6, GHSA-pf86-5x62-jrwf,
  GHSA-6chq-wfr3-2hj9, GHSA-43fc-jf86-j433). Bumped to the latest published
  release (1.18.1); no code changes needed (`src/fetch.js` usage is unaffected).

- **express `4.19.2` → `4.22.2`.** Direct advisory plus transitive advisories
  in `body-parser`, `cookie`, `path-to-regexp`, `send`, and `serve-static` that
  ship inside express. `4.22.2` is the latest release on the `4.x` line (no
  major bump needed) and resolves all of the above per `npm audit`.

- **jsonwebtoken `8.5.1` → `9.0.3`.** `npm audit` flagged the 8.x line
  entirely (range `<=8.5.1`); the fix requires the 9.x major. Verified the
  app's actual usage (`src/auth.js`) only relies on `sign()`/`verify()`/
  `decode()` with an explicit `HS256` algorithm and a payload carrying its own
  `exp` claim — behavior that is unchanged in 9.x — so the bump required no
  code changes beyond removing a stale comment that described 8.x-specific
  semantics. All webapp tests still pass.

- **lodash (devDependency) `4.17.20` → `4.18.1`.** `npm audit` flagged lodash
  `<=4.17.23` (prototype pollution / ReDoS family of advisories). Bumped to
  latest; it's a devDependency only, not shipped.

- **`request` `2.88.2` → removed.** `request` has been deprecated/unmaintained
  since before this fixture's pin and there is no non-vulnerable released
  version — `2.88.2` is the last release. It was also the sole source of four
  transitive vulnerable packages that `npm audit` could not offer any fix for
  (`fixAvailable: false` in every case) because `request` itself pins them and
  will never be updated:
  - `form-data@2.3.3` (critical, GHSA-fjxv-7rqg-78g4-style unsafe boundary
    generation)
  - `tough-cookie@2.5.0` (prototype pollution, CVE-2023-26136)
  - `qs@6.5.5` (prototype pollution)
  - `uuid@3.4.0` (insecure randomness advisory)

  Since no version fix exists for `request`, we removed it and rewrote its one
  call site (`src/importer.js`'s `fetchXml`) to use `axios`, which is already
  a maintained, already-updated dependency of this project. This eliminates
  `request` and all four of its vulnerable transitives from the dependency
  graph entirely. Behavior (GET the URL, reject on `>=400` status, return the
  body) is preserved and the existing importer tests pass unchanged.

- **xml2js `0.6.2`.** No advisory reported by `npm audit` — this is already
  the latest release. No change made.

Final state: `npm audit` reports **0 vulnerabilities**.

## fixtures/service (pip)

- **pyjwt `1.7.1` → `2.13.0`.** `pip-audit` reported the 1.x line as
  vulnerable to algorithm-confusion (PYSEC-2022-202 / CVE-2022-29217) plus
  several PyJWT 2.x-era advisories fixed progressively up through 2.13.0
  (`crit` header handling, JWK/HMAC confusion, JWKS client SSRF/DoS). Bumped
  `requirements.in`'s pin and recompiled `requirements.txt` with `pip-compile`.
  The app's `app/auth.py` was written against PyJWT 1.x's behavior where
  `jwt.encode()` returns `bytes` (needing `.decode("utf-8")`); PyJWT 2.x
  returns `str` directly, so that call site was updated to return the
  `encode()` result as-is. All service tests pass. One advisory,
  PYSEC-2025-183 ("weak encryption" due to short HMAC secrets), is disputed by
  PyJWT's maintainers — key length is the caller's responsibility, not
  something the library can enforce — and `pip-audit` no longer flags 2.13.0
  against it at all, so no further action was needed there.

- **urllib3 `1.26.5` → `2.7.0`.** This was the fixture's flagged case: the
  compiled pin had drifted behind what `requests` (`urllib3<3,>=1.26`) allows,
  carrying CVE-2023-43804, CVE-2023-45803, CVE-2024-37891, CVE-2025-50181,
  CVE-2025-66418, CVE-2025-66471, and CVE-2026-21441 (cookie/redirect leakage
  and decompression-bomb DoS issues). Bumped to the latest release (2.7.0),
  which satisfies `requests`' constraint and resolves every reported advisory.
  Recompiled via `pip-compile --upgrade-package urllib3 --upgrade-package
  pyjwt`.

- **ecdsa `0.19.2`.** Already the latest published release. Neither
  `pip-audit` nor PyPI's advisory feed (`pypi.org/pypi/ecdsa/json`) lists any
  vulnerability against this package/version in this environment, so it was
  left as-is (not reported as a false positive).

- **requests `2.34.2`.** Already the latest published release and not flagged
  by `pip-audit`. No change made.

Final state: `pip-audit` on the fully-installed environment reports **no
known vulnerabilities**.

## fixtures/api-java (Maven)

- **jackson-databind `2.13.0` → `2.22.0`** (jackson-core/jackson-annotations
  bumped transitively to match). `trivy fs` reported ten advisories against
  2.13.0, including CVE-2020-36518, CVE-2021-46877, CVE-2022-42003/42004
  (deserialization DoS/gadget issues) and several 2026-dated CVEs. `2.22.0` is
  the latest release published to Maven Central and resolves nine of the ten.
  **One advisory does not have a usable fix in this environment:
  CVE-2026-54515** (medium severity) lists fixed versions `2.18.9`, `2.21.5`,
  `2.22.1`, and `3.1.4` — none of `2.18.9`, `2.21.5`, or `2.22.1` exist on
  Maven Central yet (`404` for all three as of this writing); the only real
  artifact is `3.1.4`, which lives under the Jackson 3.x line with a different
  Maven coordinate (`tools.jackson.core` instead of
  `com.fasterxml.jackson.core`) and its own breaking API/package changes.
  That's a migration, not a version bump, and out of scope for this
  remediation pass — flagging it here rather than claiming it's fixed.

- **commons-configuration2 `2.7` → `2.15.1`.** `trivy fs` reported
  CVE-2022-33980 (critical — arbitrary script/DNS/URL interpolation via
  `StringSubstitutor`, i.e. Log4Shell-adjacent interpolation RCE), plus
  CVE-2024-29131, CVE-2024-29133, and CVE-2026-45205. `2.15.1` is the latest
  release and fixes all four. This transitively brought commons-lang3 up to
  `3.20.0` (fixing CVE-2025-48924) and commons-text up to `1.15.0` (fixing the
  critical CVE-2022-42889 `StringSubstitutor` interpolation RCE) — both were
  flagged separately by `trivy` at their old transitive pins (3.9 and 1.8).

Final state: `trivy fs --scanners vuln` reports one remaining, unfixable-by
-version advisory (CVE-2026-54515, documented above); everything else is
clean. `mvn -o test` passes (4/4 tests) after resolving the new versions into
the local repo once online (as required by any dependency bump in this
fixture).
