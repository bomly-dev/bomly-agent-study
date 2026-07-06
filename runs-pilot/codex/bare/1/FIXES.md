# Vulnerability Fixes

## fixtures/webapp

- `axios`: `npm audit` reported SSRF, credential leakage, DoS, header injection, and prototype-pollution advisories affecting `1.6.0`. Updated the direct dependency to `1.18.1`, the non-major fixed version reported by npm, because it clears all axios advisories.
- `express`: `npm audit` reported an XSS advisory in `express` and vulnerable transitives under `4.19.2`. Updated the direct dependency to `4.22.2`, the non-major fixed version reported by npm, because it brings fixed middleware/router/static-file dependencies.
- `body-parser`: `npm audit` reported a denial-of-service issue in the transitive `body-parser` version pulled by old `express`. No direct dependency was added; the `express` update moved this transitive to a non-vulnerable version.
- `cookie`: `npm audit` reported invalid character handling in the transitive `cookie` version pulled by old `express`. No direct dependency was added; the `express` update moved this transitive to a non-vulnerable version.
- `path-to-regexp`: `npm audit` reported ReDoS issues in the transitive `path-to-regexp` version pulled by old `express`. No direct dependency was added; the `express` update moved this transitive to a non-vulnerable version.
- `send`: `npm audit` reported a template-injection/XSS issue in the transitive `send` version pulled by old `express`. No direct dependency was added; the `express` update moved this transitive to a non-vulnerable version.
- `serve-static`: `npm audit` reported a template-injection/XSS issue in the transitive `serve-static` version pulled by old `express`. No direct dependency was added; the `express` update moved this transitive to a non-vulnerable version.
- `jsonwebtoken`: `npm audit` reported key handling and signature validation advisories affecting `8.5.1`. Updated the direct dependency to `9.0.3`, the fixed major version reported by npm, and kept the token code compatible with the new version.
- `lodash`: `npm audit` reported command injection, ReDoS, code injection, and prototype-pollution advisories affecting `4.17.20`. Updated the direct dev dependency to `4.18.1`, the fixed version reported by npm.
- `request`: `npm audit` reported SSRF in `request@2.88.2`. There is no fixed version of `request` (`npm audit` reported `fixAvailable: false`, and `2.88.2` is the latest release), so the dependency was removed and the XML fetch helper was migrated to the already-used `axios` dependency.
- `form-data`: `npm audit` reported unsafe boundary generation and CRLF injection in the `form-data` version pulled by `request`. No direct dependency was added; removing `request` removed this vulnerable transitive package.
- `qs`: `npm audit` reported denial-of-service advisories in transitive `qs` versions pulled by old `express` and `request`. Updating `express` and removing `request` removed the vulnerable instances.
- `tough-cookie`: `npm audit` reported prototype pollution in the `tough-cookie` version pulled by `request`. No direct dependency was added; removing `request` removed this vulnerable transitive package.
- `uuid`: `npm audit` reported a missing buffer bounds check in the `uuid` version pulled by `request`. No direct dependency was added; removing `request` removed this vulnerable transitive package.

## fixtures/service

- `pyjwt`: `pip-audit` reported JWT verification advisories affecting `1.7.1`, with fixed versions up to `2.13.0`. Updated the direct dependency to `2.13.0` and adjusted token encoding for PyJWT 2.x semantics because that version clears the reported advisories.
- `urllib3`: `pip-audit` reported redirect/header/decompression advisories affecting the stale transitive pin `1.26.5`; the latest reported fixes require `2.7.0`. Added an explicit `urllib3==2.7.0` runtime pin because `requests` allows urllib3 2.x and `pip-audit` reports no vulnerabilities at that version.

## fixtures/api-java

- `jackson-databind`: The Maven fixture used direct `jackson-databind:2.13.0`, a known vulnerable pin. Updated it to `2.22.0`, the current Maven Central release found by the versions plugin, because it moves the app off the vulnerable Jackson line while keeping the same API usage and tests passing.
- `commons-text`: `commons-configuration2:2.7` pulled transitive `commons-text:1.8`, the vulnerable interpolation dependency in the fixture. Added dependency management for `commons-text:1.14.0`, an available fixed Maven Central release; `1.14.1` does not exist in Maven Central. Also added a `commons-lang3:3.20.0` dependency-management override because `commons-text:1.14.0` requires newer commons-lang3 APIs than `commons-configuration2:2.7` pulls by default.
