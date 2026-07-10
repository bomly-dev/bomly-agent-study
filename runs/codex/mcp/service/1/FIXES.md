# Dependency Vulnerability Fixes

## Pillow

Found `pillow==10.1.0` with GHSA-3f63-hfp8-52jq / CVE-2023-50447, GHSA-44wm-f244-xhp3 / CVE-2024-28219, GHSA-r73j-pqj5-w3x7 / CVE-2026-42310, and GHSA-wjx4-4jcj-g98j / CVE-2026-42308. Updated the direct pin to `Pillow==12.2.0` in `fixtures/service/requirements.in` and regenerated `fixtures/service/requirements.txt` because bomly identified 12.2.0 as the version that closes all reported Pillow advisories.

## PyMySQL

Found `pymysql==1.0.2` with GHSA-v9hf-5j83-6xpp / CVE-2024-36039. Updated the direct dependency to `PyMySQL==1.1.1` in `fixtures/service/requirements.in` and regenerated `fixtures/service/requirements.txt` because 1.1.1 is the fixed version.

## Werkzeug

Found `werkzeug==2.0.3` with GHSA-2g68-c3qc-8985 / CVE-2024-34069, GHSA-xg9f-g7g7-2323 / CVE-2023-25577, GHSA-29vq-49wr-vm6x / CVE-2026-27199, GHSA-87hc-h4r5-73f7 / CVE-2026-21860, GHSA-f9vj-2wh5-fj8j / CVE-2024-49766, GHSA-hgf8-39gv-g3f2 / CVE-2025-66221, GHSA-hrfv-mqp8-q5rw / CVE-2023-46136, GHSA-q34m-jh98-gwm2 / CVE-2024-49767, and GHSA-px8h-6qxv-m22q / CVE-2023-23934. Updated the direct pin to `Werkzeug==3.1.6` because bomly identified 3.1.6 as the version that closes all reported Werkzeug advisories.

## cryptography

Found `cryptography==40.0.2` transitively from the `PyMySQL[rsa]` extra with multiple advisories, including GHSA-3ww4-gg4f-jr7f / CVE-2023-50782, GHSA-537c-gmf6-5ccf, GHSA-6vqw-3v5j-54x4 / CVE-2024-26130, GHSA-cf7p-gm2m-833m / CVE-2023-38325, GHSA-r6ph-v2qm-q3c2 / CVE-2026-26007, GHSA-9v9h-cgj8-h64p / CVE-2024-0727, GHSA-h4gh-qq45-vh27, GHSA-jfhm-5ghh-2f97 / CVE-2023-49083, GHSA-5cpq-8wj7-hf2v, GHSA-jm77-qphf-c4w8, GHSA-m959-cc7f-wv43 / CVE-2026-34073, and GHSA-v8gr-m533-ghj9. Fixed versions of `cryptography` require `cffi>=2.0`, but `pybluemonday==0.0.14` has no available release that allows `cffi` 2.x. Removed the optional PyMySQL `rsa` extra by changing `PyMySQL[rsa]==1.0.2` to `PyMySQL==1.1.1`, which removes vulnerable `cryptography` from the runtime dependency graph while still fixing PyMySQL itself.

## urllib3

Found `urllib3==1.26.20` with GHSA-2xpw-w6gg-jr37 / CVE-2025-66471, GHSA-38jv-5279-wg99 / CVE-2026-21441, GHSA-gm62-xv2j-4w53 / CVE-2025-66418, GHSA-qccp-gfcp-xxvc / CVE-2026-44431, and GHSA-pq67-6m6q-mj2v / CVE-2025-50181. Updated the direct pin to `urllib3==2.7.0` because bomly identified 2.7.0 as the version that closes all reported urllib3 advisories.

## Mako

Found `mako==1.1.3` with GHSA-2h4p-vjrc-8xpq / CVE-2026-44307, GHSA-v92g-xgxw-vvmm / CVE-2026-41205, and GHSA-v973-fxgf-6xhp / CVE-2022-40023. Regenerated `requirements.txt` with `mako==1.3.12` because bomly identified 1.3.12 as the version that closes all reported Mako advisories.

## Flask

Found `flask==2.0.3` with GHSA-m2qf-hxjv-5gpq / CVE-2023-30861 and GHSA-68rp-wp8r-4726 / CVE-2026-27205. Updated the direct pin to `Flask==3.1.3` because bomly identified 3.1.3 as the version that closes all reported Flask advisories. Compatibility bumps to `Flask-Caching==2.4.1`, `Flask-SQLAlchemy==3.0.5`, `Flask-Babel==4.0.0`, and `flask-restx==1.3.2` were required for the application to run on the fixed Flask/Werkzeug versions.

## idna

Found `idna==2.10` with GHSA-65pc-fj4g-8rjx / CVE-2026-45409 and GHSA-jjg7-2v4v-x38h / CVE-2024-3651. Regenerated `requirements.txt` with `idna==3.18`, which is newer than the fixed versions bomly listed and closes both advisories.

## pydantic

Found `pydantic==1.6.2` with GHSA-mr82-8j83-vxmv / CVE-2024-3772. Updated the direct pin to `pydantic==1.10.13` because bomly identified 1.10.13 as the fixed version.

## requests

Found `requests==2.32.3` with GHSA-9hjg-9r4m-mvj7 / CVE-2024-47081 and GHSA-gc5v-m9x4-r6x2 / CVE-2026-25645. Updated the direct pin to `requests==2.33.0` because bomly identified 2.33.0 as the version that closes all reported Requests advisories.

## python-dotenv

Found `python-dotenv==0.13.0` with GHSA-mf9w-mj56-hr94 / CVE-2026-28684. Updated the direct pin to `python-dotenv==1.2.2` because bomly identified 1.2.2 as the fixed version.
