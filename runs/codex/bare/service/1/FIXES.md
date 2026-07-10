# Vulnerability Remediation Log

## urllib3

Found `urllib3==1.26.20` vulnerable to `PYSEC-2026-141`, `PYSEC-2026-1999`, `PYSEC-2026-1998`, `PYSEC-2026-1994`, and `PYSEC-2026-1996`. Updated the direct pin to `urllib3==2.7.0`, which is at or above every reported fixed version. This keeps the requests/botocore dependency satisfied while removing all reported urllib3 advisories.

## cryptography

Found `cryptography==40.0.2` as a vulnerable transitive dependency from `PyMySQL[rsa]`, with advisories including `PYSEC-2023-112`, `PYSEC-2023-254`, `PYSEC-2024-225`, `PYSEC-2026-35`, `PYSEC-2026-1283`, `PYSEC-2026-1285`, `GHSA-5cpq-8wj7-hf2v`, `GHSA-jm77-qphf-c4w8`, `GHSA-v8gr-m533-ghj9`, `GHSA-h4gh-qq45-vh27`, `CVE-2026-26007`, and `GHSA-537c-gmf6-5ccf`. Changed `PyMySQL[rsa]==1.0.2` to `PyMySQL==1.1.1`, removing the RSA extra that pulled cryptography into the production lock. A complete cryptography version fix would require `cryptography>=48.0.1`, which requires `cffi>=2`, but `pybluemonday==0.0.14` has no newer release and requires `cffi<2`; removing the unused extra avoids that incompatible dependency set.

## Flask

Found `Flask==2.0.3` vulnerable to `PYSEC-2023-62` and `CVE-2026-27205`. Updated Flask to `3.1.3`, the fixed version for the newest advisory. Bumped companion Flask extensions (`Flask-Caching`, `Flask-SQLAlchemy`, `Flask-Migrate`, `Flask-Babel`, and `flask-restx`) and added small compatibility shims for sessions and redirects so the app still builds and tests pass on Flask 3.

## idna

Found `idna==2.10` vulnerable to `PYSEC-2024-60` and `PYSEC-2026-215`. Regenerated the lock with `idna==3.18`, above the reported fixed versions. This is a transitive dependency of `requests` and remains compatible with the updated requests stack.

## Mako

Found `Mako==1.1.3` vulnerable to `PYSEC-2022-260` and `CVE-2026-44307`. Regenerated the lock with `Mako==1.3.12`, matching the latest reported fixed version. This remains compatible with the updated Alembic/Flask-Migrate set.

## Pillow

Found `Pillow==10.1.0` vulnerable to `PYSEC-2026-165`, `PYSEC-2026-457`, `PYSEC-2026-1793`, and `CVE-2026-42310`. Updated the direct pin to `Pillow==12.2.0`, which satisfies the highest reported fixed version.

## pydantic

Found `pydantic==1.6.2` vulnerable to `PYSEC-2026-1812`. Updated the direct pin to `pydantic==1.10.13`, the fixed 1.x release, avoiding a larger application migration to pydantic 2.

## PyMySQL

Found `PyMySQL==1.0.2` vulnerable to `PYSEC-2026-502`. Updated the direct pin to `PyMySQL==1.1.1`, the reported fixed version. Removed the `rsa` extra as noted under cryptography to avoid pulling in an incompatible vulnerable transitive dependency.

## python-dotenv

Found `python-dotenv==0.13.0` vulnerable to `CVE-2026-28684`. Updated the direct pin to `python-dotenv==1.2.2`, the reported fixed version.

## requests

Found `requests==2.32.3` vulnerable to `PYSEC-2026-1872` and `CVE-2026-25645`. Updated the direct pin to `requests==2.33.0`, the highest reported fixed version.

## Werkzeug

Found `Werkzeug==2.0.3` vulnerable to `PYSEC-2022-203`, `PYSEC-2023-57`, `PYSEC-2023-58`, `PYSEC-2023-221`, `PYSEC-2026-2046`, `PYSEC-2026-2045`, `PYSEC-2026-2044`, `PYSEC-2026-2043`, `CVE-2024-49767`, and `CVE-2026-27199`. Updated the direct pin to `Werkzeug==3.1.6`, the highest reported fixed version. Adjusted the custom session interface for Flask/Werkzeug 3 cookie APIs and string-only cookie values.

## pytest

Found dev/test dependency `pytest==7.3.1` vulnerable to `PYSEC-2026-1845`. Updated `development.txt` to `pytest==9.0.3`, the reported fixed version. The root `make test` target installs this filtered dev dependency set and passes with the updated version.
