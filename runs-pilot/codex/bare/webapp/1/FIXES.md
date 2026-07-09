# Dependency Vulnerability Fixes

- `axios`: Found multiple SSRF, DoS, credential leakage, header injection, and prototype pollution advisories affecting `1.6.0`. Updated the direct dependency to `1.18.1`, the fixed version reported by `npm audit`, because the app still uses axios for outbound HTTP requests.
- `body-parser`: Found a denial-of-service advisory in the transitive Express parser stack. Updated `express` to `4.22.2`, which brought in a remediated `body-parser` version.
- `cookie`: Found an out-of-bounds character handling advisory through Express. Updated `express` to `4.22.2`, which brought in a remediated `cookie` version.
- `express`: Found advisories for `response.redirect()` XSS and vulnerable transitive middleware packages in `4.19.2`. Updated the direct dependency to `4.22.2`, the fixed 4.x version reported by `npm audit`, to avoid a major framework migration.
- `form-data`: Found unsafe boundary generation and CRLF injection advisories through the deprecated `request` dependency. No fixed version is available by changing `request` versions, so `request` was removed and the XML fetch path was migrated to axios.
- `jsonwebtoken`: Found key handling and signature verification advisories affecting `8.5.1`. Updated the direct dependency to `9.0.3`, the fixed version reported by `npm audit`; existing token tests still pass.
- `lodash`: Found command/code injection, ReDoS, and prototype pollution advisories affecting `4.17.20`. Updated the dev dependency to `4.18.1`, the fixed version reported by `npm audit`.
- `path-to-regexp`: Found ReDoS advisories through Express routing. Updated `express` to `4.22.2`, which brought in a remediated `path-to-regexp` version.
- `qs`: Found denial-of-service advisories through Express/body-parser and `request`. Updated `express` to `4.22.2` for the Express path. The vulnerable `request` path had no fixed `request` version, so `request` was removed.
- `request`: Found an SSRF advisory in `2.88.2`, and `npm audit` reported no fixed version for `request`. Removed the dependency and replaced its narrow XML GET usage with axios.
- `send`: Found a template injection/XSS advisory through Express static response handling. Updated `express` to `4.22.2`, which brought in a remediated `send` version.
- `serve-static`: Found a template injection/XSS advisory through Express. Updated `express` to `4.22.2`, which brought in a remediated `serve-static` version.
- `tough-cookie`: Found a prototype pollution advisory through `request`. No fixed version is available by changing `request` versions, so `request` was removed and this transitive package left the dependency graph.
- `uuid`: Found a missing bounds check advisory through `request`. No fixed version is available by changing `request` versions, so `request` was removed and this transitive package left the dependency graph.
