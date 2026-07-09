# Dependency vulnerability remediation

Findings and actions taken for each fixture app, one entry per package.
Vulnerability data sources: `npm audit` (webapp), `pip-audit` (service),
Maven Central metadata + dependency tree inspection (api-java).

## fixtures/webapp (npm)

### axios `1.6.0` → `1.18.1`
Found: multiple SSRF advisories (GHSA-8hc4-vh64-cxmj, GHSA-jr5f-v2jv-69x6,
GHSA-3p68-rc4w-qgx5, GHSA-m7pr-hjqh-92cm, ...), several prototype-pollution
gadgets enabling auth bypass / header injection / response tampering
(GHSA-w9j2-pvgh-6h63, GHSA-pf86-5x62-jrwf, GHSA-6chq-wfr3-2hj9, GHSA-q8qp-cvcw-x6jj,
GHSA-43fc-jf86-j433), and a DoS via unbounded response size (GHSA-4hjh-wcwx-xvwj).
Action: bumped to `1.18.1`, the latest release, which resolves all of the above
per `npm audit`. Non-breaking (same major version); `src/fetch.js` and tests
required no changes.

### express `4.19.2` → `4.22.2`
Found: reflected XSS via `response.redirect()` (GHSA-qw6h-vgh9-j6wx), plus
transitively vulnerable `body-parser`, `cookie`, `path-to-regexp`, `send`, and
`serve-static`.
Action: bumped to `4.22.2` (latest 4.x), which pulls in patched versions of all
the above transitives. Non-breaking; no code changes required.

### jsonwebtoken `8.5.1` → `9.0.3`
Found: unrestricted key type usable to force legacy/weak keys
(GHSA-8cf7-32gw-wr33), insecure key-retrieval allowing RSA→HMAC key confusion
forgery (GHSA-hjrf-2m68-5959), and an insecure default algorithm in
`jwt.verify()` (GHSA-qwph-4952-7xr6).
Action: bumped to `9.0.3` (major version — no fix exists on the 8.x line). This
is a breaking API change; verified `src/auth.js` and `test/auth.test.js`
continue to pass unmodified (the code already always passes an explicit
`algorithm`/relies on default HS256 verification, so no source changes were
needed). Full webapp test suite (12/12) passes.

### request `2.88.2` → removed
Found: SSRF in `request` (GHSA-p8p7-x288-28g6, critical) plus critical/moderate
advisories in its unmaintained transitive deps `form-data`, `qs`,
`tough-cookie`, and `uuid`.
Action: **no fixed version exists** — `request` has been deprecated/unmaintained
since 2020 and received no further releases. Removed it from `package.json`
entirely and rewrote its sole call site (`fetchXml` in `src/importer.js`) to
use `axios` (already a dependency, now patched — see above) instead. This also
eliminates the `form-data`/`qs`/`tough-cookie`/`uuid` transitive advisories,
since `request` was the only thing pulling them in. `npm audit` now reports
**0 vulnerabilities**. Test `test/importer.test.js` ("fetches a remote XML feed
via request") passes unchanged against the new implementation.

### lodash `4.17.20` → `4.18.1` (devDependency)
Found: command injection (GHSA-35jh-r3h4-6jhm), ReDoS (GHSA-29mw-wpgm-hmr9),
code injection via `_.template` (GHSA-r5fr-rjxr-66jc), and prototype pollution
in `_.unset`/`_.omit` (GHSA-f23m-r3pf-42rh, GHSA-xxjr-mmjv-4gpg).
Action: bumped to `4.18.1` (latest). Non-breaking, dev-only dependency, no
usage in source to update.

### xml2js `0.6.2`
Checked: no advisory reported by `npm audit` for this version. Left unchanged.

## fixtures/service (Python / pip)

### ecdsa `0.19.2`
Found (`pip-audit`, PYSEC-2026-1325): Minerva timing-attack side channel in
`ecdsa.SigningKey.sign_digest()` on the P-256 curve, allowing private-key
recovery from signature timing.
Action: **no fixed version exists** — `0.19.2` is already the newest release on
PyPI, and the `python-ecdsa` maintainers have stated that constant-time
execution (and thus a fix for this class of timing attack) cannot be
guaranteed by a pure-Python implementation, so no patched release is planned.
Left the pin as-is; this is a known, currently-unfixable-by-upgrade risk in
this fixture. (Mitigation would require switching away from pure-Python ECDSA
to a binding over a constant-time native implementation, which is outside the
scope of a version bump.)

### pyjwt `1.7.1` → `2.13.0`
Found (`pip-audit`): algorithm-confusion signature bypass (PYSEC-2022-202),
missing validation of the `crit` header parameter (PYSEC-2026-120), several
JWKS-handling issues fixed in 2.13.0 including SSRF-adjacent URL handling in
`PyJWKClient` and unbounded JWKS refetch (PYSEC-2026-175/177/179).
Action: bumped to `2.13.0` (latest), updated in both `requirements.in` and
`requirements.txt`. This is a breaking major-version change: PyJWT 2.x's
`jwt.encode()` returns `str` instead of `bytes`. Updated
`fixtures/service/app/auth.py::make_token` to handle both return types
(`token.decode("utf-8") if isinstance(token, bytes) else token`) instead of
unconditionally decoding, since the code was previously written assuming 1.x
bytes-return semantics. `read_token` already passed `algorithms=["HS256"]`
explicitly, so no other changes were required. Full test suite (8/8) passes.

### urllib3 `1.26.5` → `2.7.0`
Found (`pip-audit`): HTTP redirect body-retention when method changes
(PYSEC-2023-212), several cookie/proxy-header leakage and decompression-bomb
issues (PYSEC-2026-141, PYSEC-2026-1994/1995/1996/1998/1999). The pinned
`requirements.txt` comment noted this pin had drifted behind what `requests`
actually allows (`urllib3<3`).
Action: bumped to `2.7.0` (latest, within the range `requests==2.34.2` allows).
No code changes required; `app/fetcher.py` uses only the high-level `requests`
API.

## fixtures/api-java (Maven)

### jackson-databind `2.13.0` → `2.22.1`
Found: `jackson-databind` 2.13.0 predates numerous deserialization-gadget CVEs
fixed across the 2.13.x–2.22.x lines.
Action: bumped to `2.22.1` (latest release). `jackson-core`/`jackson-annotations`
are pulled transitively at matching versions. `JsonMapper` uses only the
standard `ObjectMapper` API; no source changes required. Verified via
`mvn dependency:tree` and `mvn test`/`mvn -o test` (4/4 tests pass).

### commons-configuration2 `2.7` → `2.15.1`
Found: `commons-configuration2` 2.7 enables default interpolation lookups
(`script`, `dns`, `url`) that allow attacker-controlled config values to
trigger script execution (CVE-2022-33980, fixed in 2.8.0). It also transitively
pulled `commons-text:1.8`, which is vulnerable to the Text4Shell RCE
(CVE-2022-42889, fixed in `commons-text` 1.10.0) via `StringSubstitutor`
interpolation — the exact interpolation path this fixture's `ConfigLoader`
exercises.
Action: bumped to `2.15.1` (latest release), which pulls `commons-text` up to
`1.15.0` (well past the 1.10.0 fix) and disables the risky default lookups.
No source changes required; `ConfigLoaderTest`'s interpolation behavior is
unaffected (2/2 tests pass).

### Local Maven repo cache note
The Makefile's `test-java` target runs `mvn -o test` (offline). The sandbox's
pre-seeded `~/.m2` cache only had the vulnerable pinned versions available, so
after bumping versions in `pom.xml` a one-time online `mvn test` was run to
resolve and cache the new artifacts (network access to Maven Central was
available). `mvn -o test` was then re-verified to succeed fully offline. This
was also true, unrelated to this change, of the default `maven-resources-plugin`
binding for Maven 3.8.7 the first time any build ran — confirmed pre-existing
by reproducing the same offline failure against the unmodified `pom.xml`.

## Verification

`make test` (webapp + service + api-java, clean installs) passes in full:
- webapp: 12/12 tests, `npm audit` → 0 vulnerabilities
- service: 8/8 tests, `pip-audit` → 1 remaining finding (`ecdsa`, no fix
  available, documented above)
- api-java: 4/4 tests, `mvn -o test` builds and passes offline
