# Dependency Vulnerability Remediation

## Pillow

Found `pillow==10.1.0` with GHSA-3f63-hfp8-52jq / CVE-2023-50447, GHSA-44wm-f244-xhp3 / CVE-2024-28219, GHSA-r73j-pqj5-w3x7 / CVE-2026-42310, and GHSA-wjx4-4jcj-g98j / CVE-2026-42308. Updated `Pillow` to `12.2.0` in `fixtures/service/requirements.in` and regenerated `fixtures/service/requirements.txt` because that version is at or above the fixed versions for all listed advisories.

## PyMySQL

Found `pymysql==1.0.2` with GHSA-v9hf-5j83-6xpp / CVE-2024-36039. Updated `PyMySQL[rsa]` to `1.1.1` in `fixtures/service/requirements.in` and regenerated `fixtures/service/requirements.txt` because `1.1.1` is the fixed version.

## Werkzeug

Found `werkzeug==2.0.3` with GHSA-2g68-c3qc-8985 / CVE-2024-34069, GHSA-xg9f-g7g7-2323 / CVE-2023-25577, GHSA-29vq-49wr-vm6x / CVE-2026-27199, GHSA-87hc-h4r5-73f7 / CVE-2026-21860, GHSA-f9vj-2wh5-fj8j / CVE-2024-49766, GHSA-hgf8-39gv-g3f2 / CVE-2025-66221, GHSA-hrfv-mqp8-q5rw / CVE-2023-46136, GHSA-q34m-jh98-gwm2 / CVE-2024-49767, and GHSA-px8h-6qxv-m22q / CVE-2023-23934. Updated `Werkzeug` to `3.1.6` in `fixtures/service/requirements.in` and regenerated `fixtures/service/requirements.txt` because that version is at or above the fixed versions for all listed advisories.

## cryptography

Found `cryptography==40.0.2` with GHSA-3ww4-gg4f-jr7f / CVE-2023-50782, GHSA-537c-gmf6-5ccf, GHSA-6vqw-3v5j-54x4 / CVE-2024-26130, GHSA-cf7p-gm2m-833m / CVE-2023-38325, GHSA-r6ph-v2qm-q3c2 / CVE-2026-26007, GHSA-9v9h-cgj8-h64p / CVE-2024-0727, GHSA-h4gh-qq45-vh27, GHSA-jfhm-5ghh-2f97 / CVE-2023-49083, GHSA-5cpq-8wj7-hf2v, GHSA-jm77-qphf-c4w8, GHSA-m959-cc7f-wv43 / CVE-2026-34073, and GHSA-v8gr-m533-ghj9. Updated `cryptography` to `45.0.7`, the newest installable version compatible with this app's dependency graph, which fixes the advisories with fixed versions up to that release.

Could not update to the scanner-recommended `cryptography==48.0.1`, or to the `46.x` releases needed for GHSA-r6ph-v2qm-q3c2, GHSA-p423-j2cm-9vmq / CVE-2026-39892, and GHSA-m959-cc7f-wv43, because those releases require `cffi>=2` while the app directly depends on `pybluemonday==0.0.14`, and `pybluemonday` has no newer release and requires `cffi~=1.1`. The final scan still reports GHSA-537c-gmf6-5ccf, GHSA-r6ph-v2qm-q3c2 / CVE-2026-26007, GHSA-p423-j2cm-9vmq / CVE-2026-39892, and GHSA-m959-cc7f-wv43 / CVE-2026-34073 for `cryptography==45.0.7`; these were not claimed fixed.

## urllib3

Found `urllib3==1.26.20` with GHSA-2xpw-w6gg-jr37 / CVE-2025-66471, GHSA-38jv-5279-wg99 / CVE-2026-21441, GHSA-gm62-xv2j-4w53 / CVE-2025-66418, GHSA-qccp-gfcp-xxvc / CVE-2026-44431, and GHSA-pq67-6m6q-mj2v / CVE-2025-50181. Updated `urllib3` to `2.7.0` in `fixtures/service/requirements.in` and regenerated `fixtures/service/requirements.txt` because that version is at or above the fixed versions for all listed advisories.

## Mako

Found `mako==1.1.3` with GHSA-2h4p-vjrc-8xpq / CVE-2026-44307, GHSA-v92g-xgxw-vvmm / CVE-2026-41205, and GHSA-v973-fxgf-6xhp / CVE-2022-40023. Added a direct `Mako==1.3.12` pin to `fixtures/service/requirements.in` and regenerated `fixtures/service/requirements.txt` because `Mako` was previously transitive and `1.3.12` is at or above the fixed versions for all listed advisories.

## Flask

Found `flask==2.0.3` with GHSA-m2qf-hxjv-5gpq / CVE-2023-30861 and GHSA-68rp-wp8r-4726 / CVE-2026-27205. Updated `Flask` to `3.1.3` in `fixtures/service/requirements.in` and regenerated `fixtures/service/requirements.txt` because `3.1.3` is the fixed version for the newest listed advisory. Supporting Flask extension pins were updated as needed to keep the app installable.

## idna

Found `idna==2.10` with GHSA-65pc-fj4g-8rjx / CVE-2026-45409 and GHSA-jjg7-2v4v-x38h / CVE-2024-3651. Added a direct `idna==3.15` pin to `fixtures/service/requirements.in` and regenerated `fixtures/service/requirements.txt` because `idna` was previously transitive and `3.15` is the fixed version for the newest listed advisory.

## pydantic

Found `pydantic==1.6.2` with GHSA-mr82-8j83-vxmv / CVE-2024-3772. Updated `pydantic` to `1.10.13` in `fixtures/service/requirements.in` and regenerated `fixtures/service/requirements.txt` because `1.10.13` is the fixed version while staying on the app's existing pydantic major version.

## requests

Found `requests==2.32.3` with GHSA-9hjg-9r4m-mvj7 / CVE-2024-47081 and GHSA-gc5v-m9x4-r6x2 / CVE-2026-25645. Updated `requests` to `2.33.0` in `fixtures/service/requirements.in` and regenerated `fixtures/service/requirements.txt` because `2.33.0` is the fixed version for the newest listed advisory.

## python-dotenv

Found `python-dotenv==0.13.0` with GHSA-mf9w-mj56-hr94 / CVE-2026-28684. Updated `python-dotenv` to `1.2.2` in `fixtures/service/requirements.in` and regenerated `fixtures/service/requirements.txt` because `1.2.2` is the fixed version.

## Compatibility changes required by remediation

To keep `make test` passing after the vulnerability-driven Flask and Werkzeug upgrades, updated supporting dependency pins for `Flask-Caching`, `Flask-SQLAlchemy`, `Flask-Migrate`, `flask-restx`, `Flask-Babel`, and `attrs`. Also made narrow Flask/Werkzeug compatibility updates in the app's response, session, and redirect handling code.
