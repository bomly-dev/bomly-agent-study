# Dependency Vulnerability Fixes

- `axios`: `npm audit` reported multiple SSRF, DoS, credential leakage, header injection, and prototype-pollution advisories affecting `axios@1.6.0` (`>=1.0.0` ranges, with fixes available). Changed the direct dependency to `axios@1.18.1`, which npm identified as the fixed non-major version, and regenerated `package-lock.json`.

- `express`: `npm audit` reported `express@4.19.2` vulnerable to XSS in `response.redirect()` and as the parent of vulnerable middleware dependencies. Changed the direct dependency to `express@4.22.2`, which npm identified as the fixed non-major version.

- `jsonwebtoken`: `npm audit` reported unrestricted key type, insecure key retrieval, and default algorithm verification issues in `jsonwebtoken@8.5.1`. Changed the direct dependency to `jsonwebtoken@9.0.3`, the fixed major version reported by npm. The existing code already signs with `HS256` explicitly and the tests still cover token issue, verify, and decode behavior.

- `lodash`: `npm audit` reported command injection, ReDoS, code injection, and prototype-pollution advisories in `lodash@4.17.20`. Changed the direct dev dependency to `lodash@4.18.1`, the fixed non-major version reported by npm.

- `request`: `npm audit` reported SSRF in `request@2.88.2` and marked `fixAvailable: false`; there is no fixed `request` version to upgrade to. Removed the direct `request` dependency and migrated the XML feed fetcher to the already-used `axios` dependency, preserving the existing fetch behavior and error message for upstream HTTP errors.

- `body-parser`: `npm audit` reported DoS issues in the transitive `body-parser` version pulled by `express@4.19.2`. No direct dependency existed. Upgrading `express` to `4.22.2` moved the tree to `body-parser@1.20.6`, resolving the advisory.

- `cookie`: `npm audit` reported invalid character handling issues in the transitive `cookie` version pulled by `express@4.19.2`. No direct dependency existed. Upgrading `express` to `4.22.2` moved the tree to `cookie@0.7.2`, resolving the advisory.

- `form-data`: `npm audit` reported unsafe boundary generation and CRLF injection in `request`'s transitive `form-data@2.x` dependency, and the `request` path had no fixed version. Removed `request`, which removed that vulnerable transitive copy. The remaining `form-data` in the tree is `form-data@4.0.6` through `axios@1.18.1`.

- `path-to-regexp`: `npm audit` reported ReDoS advisories in the transitive `path-to-regexp` version pulled by `express@4.19.2`. No direct dependency existed. Upgrading `express` to `4.22.2` moved the tree to `path-to-regexp@0.1.13`, resolving the advisory.

- `qs`: `npm audit` reported DoS advisories in `qs` copies pulled by `express`/`body-parser` and `request`; npm showed no fixed version for the `request` path. Upgrading `express` moved its copy to `qs@6.15.3`, and removing `request` removed the vulnerable nested copy.

- `send`: `npm audit` reported XSS template injection in the transitive `send` version pulled by `express@4.19.2`. No direct dependency existed. Upgrading `express` to `4.22.2` moved the tree to `send@0.19.2`, resolving the advisory.

- `serve-static`: `npm audit` reported XSS template injection in the transitive `serve-static` version pulled by `express@4.19.2`. No direct dependency existed. Upgrading `express` to `4.22.2` moved the tree to `serve-static@1.16.3`, resolving the advisory.

- `tough-cookie`: `npm audit` reported prototype pollution in the transitive `tough-cookie` version pulled by `request`, and npm showed no fixed version through the `request` dependency path. Removed `request`, which removed `tough-cookie` from the dependency tree.

- `uuid`: `npm audit` reported a buffer bounds-check issue in the transitive `uuid` version pulled by `request`, and npm showed no fixed version through the `request` dependency path. Removed `request`, which removed `uuid` from the dependency tree.
