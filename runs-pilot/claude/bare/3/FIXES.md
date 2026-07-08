# Dependency vulnerability remediation

Findings and actions taken for each fixture in `fixtures/`. Vulnerable
packages were identified with `npm audit` (webapp), `pip-audit` (service),
and manual OSV.dev lookups keyed off `mvn dependency:tree` (api-java, no
Java audit tool was provided). All three `make test-*` targets pass after
these changes.

## fixtures/webapp (npm)

- **axios `1.6.0` → `1.18.1`.** Found: multiple advisories (SSRF via
  absolute URL / NO_PROXY bypass, GHSA-jr5f-v2jv-69x6, GHSA-3p68-rc4w-qgx5,
  GHSA-m7pr-hjqh-92cm; DoS via unbounded response size, GHSA-4hjh-wcwx-xvwj;
  prototype-pollution auth bypass, GHSA-w9j2-pvgh-6h63; and others).
  Changed: bumped to the latest 1.x release, which resolves all of them
  without a major-version jump. No code changes needed.

- **express `4.19.2` → `4.22.2`.** Found: `body-parser` and `express` itself
  vulnerable to DoS (GHSA-qwcr-r2fm-qrc7 class), `path-to-regexp` ReDoS,
  `send`/`serve-static` open-redirect/disclosure issues, and a low-severity
  `cookie` issue — all pulled in as express's own transitive pins. Changed:
  bumped express within its 4.x line, which updates all of the above
  transitives to fixed versions. No code changes needed.

- **jsonwebtoken `8.5.1` → `9.0.3`.** Found: GHSA (CVE-2022-23529 class)
  high-severity issues in the 8.x line, `npm audit` fixAvailable pointed at
  9.x (semver-major). Changed: bumped to 9.0.3. `src/auth.js` was written
  against 8.x quirks only in a code comment, not in behavior that 9.x
  changes (payload already carrying its own `exp` without also passing
  `options.expiresIn` still works in 9.x); verified via the existing test
  suite (`test/auth.test.js`), all of which pass unmodified.

- **request `2.88.2` → removed (no fixed version exists).** Found: `request`
  is critically vulnerable and deprecated/unmaintained; `npm audit` reports
  `fixAvailable: false` for `request` itself and for the vulnerable
  transitives it alone pulled in (`form-data` critical, `tough-cookie`
  moderate, `qs` moderate, `uuid` moderate — confirmed via
  `npm ls form-data qs tough-cookie uuid` that none of these came from any
  other dependency). No version of `request` fixes these; the package has
  been unmaintained since 2020. Changed: replaced its one call site
  (`src/importer.js`'s `fetchXml`) with `axios`, which the app already uses
  elsewhere for outbound HTTP, and dropped `request` from `package.json`.
  This removes the vulnerable package and its four vulnerable
  no-fix-available transitives entirely rather than pinning a version that
  doesn't exist. Behavior (fetch a URL, return the body, reject on HTTP
  >=400) is preserved; `test/importer.test.js` passes unmodified.

- **lodash (devDependency) `4.17.20` → `4.18.1`.** Found: prototype
  pollution / command injection advisories affecting `<=4.17.23`. Changed:
  bumped to the latest 4.x release. Dev-only dependency (used by
  `scripts/seed.js`), no code changes needed.

- **xml2js `0.6.2`.** Checked, no known advisories reported by `npm audit`.
  Left unchanged.

Result: `npm audit` reports 0 vulnerabilities after these changes.

## fixtures/service (Python)

- **pyjwt `1.7.1` → `2.13.0`.** Found (via `pip-audit`): multiple advisories
  in the 1.x line, most recently PYSEC-2026-120/175/177/179 and the older
  key-confusion issue PYSEC-2022-202; fixed versions land in 2.4.0–2.13.0.
  Changed: bumped to the latest 2.x release (`requirements.in` and
  `requirements.txt`). `app/auth.py` was written against PyJWT 1.x's
  `encode()` returning `bytes` (it called `.decode("utf-8")` on the
  result); updated it to PyJWT 2.x semantics where `encode()` already
  returns `str`, removing the now-invalid `.decode()` call. Verified with
  `tests/test_auth.py`, which passes unmodified (it only asserts the
  return type is `str`).

- **urllib3 `1.26.5` → `2.7.0`.** Found (via `pip-audit`): several
  advisories against the stale 1.26.5 pin, the newest of which
  (PYSEC-2026-141) is only fixed in 2.7.0; the file itself had a comment
  noting the pin had drifted behind what `requests` allows. Changed:
  bumped the pin in `requirements.txt` to 2.7.0 (compatible with the
  installed `requests==2.34.2`, verified with `pip check` and the full
  test run) and removed the stale drift comment, which no longer applies.

- **ecdsa `0.19.2` — no fix available, left unchanged.** Found (via
  `pip-audit`): PYSEC-2026-1325, a Minerva-class timing side-channel attack
  against `SigningKey.sign_digest()` on the P-256 curve, used directly by
  `app/reports.py` to sign report bodies. `0.19.2` is already the latest
  release on PyPI, and `pip-audit` reports no fix version for this
  advisory. The `python-ecdsa` maintainers have stated explicitly that
  side-channel attacks are out of scope for the project and there is no
  planned fix. **This cannot be remediated by a version bump; no fixed
  release exists.** Swapping to a different signing library (e.g.
  `cryptography`'s `ec` module) would remediate it but is a larger,
  API-incompatible change beyond a dependency bump, so it was left as a
  flagged, unfixed finding rather than guessing at a partial fix.

Result: `pip-audit -r requirements.txt -r requirements-dev.txt` reports only
the one known-unfixable `ecdsa` finding above.

## fixtures/api-java (Maven)

No Java-specific audit tool was available in this environment, so findings
were sourced from OSV.dev queries against the pinned/resolved coordinates
in `pom.xml` / `mvn dependency:tree`.

- **jackson-databind `2.13.0` → `2.22.0`.** Found: several advisories
  against 2.13.0, including CVE-2022-42003/CVE-2022-42004 (uncontrolled
  resource consumption), CVE-2021-46877, CVE-2020-36518 (deeply-nested JSON
  DoS), and CVE-2026-50193 — plus two DNS/polymorphic-type issues
  (CVE-2026-54514, CVE-2026-54512/GHSA-rmj7) that were reintroduced in
  2.19.0 and fixed again in 2.21.4. Changed: bumped to 2.22.0, the latest
  release published to Maven Central, which includes all of the above
  fixes. No code changes needed (`JsonMapper` uses default `ObjectMapper`
  settings).

  One advisory, **CVE-2026-54515 / GHSA-5jmj-h7xm-6q6v** (a mass-assignment
  bypass that only triggers when a bean combines per-property
  `@JsonIgnoreProperties` with `@JsonFormat(ACCEPT_CASE_INSENSITIVE_PROPERTIES)`,
  which nothing in this fixture uses), **has no fixed release yet on the
  2.x line**: upstream's advisory states it will be fixed in 2.18.9,
  2.21.5, and 2.22.1, none of which are published to Maven Central as of
  this writing (confirmed: `2.22.1` 404s at repo1.maven.org). This is left
  as a flagged, currently-unfixable-by-version-bump finding rather than
  pinning to a release that doesn't exist.

- **commons-configuration2 `2.7` → `2.15.1`.** Found: CVE-2022-33980 (code
  injection via interpolator lookups, e.g. `${script:...}`/`${dns:...}`,
  fixed in 2.8.0 — directly relevant here since `ConfigLoader` performs
  `${...}` variable interpolation) plus three StackOverflow DoS advisories
  (CVE-2024-29131, CVE-2024-29133, CVE-2026-45205) fixed by 2.10.1 and
  2.15.0 respectively. Changed: bumped to 2.15.1, the latest release on
  Maven Central, which includes all four fixes. No code changes needed.

- **Transitive dependencies** pulled in by the above two bumps
  (`jackson-core`/`jackson-annotations` 2.22.x, `commons-text` 1.15.0,
  `commons-lang3` 3.20.0, `commons-logging` 1.3.6, `commons-io` 2.22.0) and
  the existing `junit-jupiter` 5.10.2 were checked individually against
  OSV.dev; none currently have open advisories.

Result: `mvn -o test` builds and passes (4/4 tests) with the above pins;
only the one known-unreleased jackson-databind fix above remains open.
