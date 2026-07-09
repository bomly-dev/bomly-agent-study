# Dependency Vulnerability Fixes

## urllib3

Found advisories PYSEC-2026-141, PYSEC-2026-1999, PYSEC-2026-1998, PYSEC-2026-1994, and PYSEC-2026-1996 against `urllib3==1.26.20`.

Changed `urllib3` to `2.7.0`, which is at or above the highest fixed version reported by `pip-audit`.

## cryptography

Found multiple advisories against `cryptography==40.0.2`, including PYSEC-2023-112, PYSEC-2023-254, PYSEC-2024-225, PYSEC-2026-35, PYSEC-2026-1283, PYSEC-2026-1285, CVE-2026-26007, GHSA-5cpq-8wj7-hf2v, GHSA-jm77-qphf-c4w8, GHSA-v8gr-m533-ghj9, GHSA-h4gh-qq45-vh27, and GHSA-537c-gmf6-5ccf.

Changed `cryptography` to `44.0.3`, the newest version I found that remains compatible with this app's `pybluemonday==0.0.14` dependency and its `cffi~=1.1` requirement. This fixes the older advisories from the original pin, but `pip-audit` still reports PYSEC-2026-35, CVE-2026-26007, and GHSA-537c-gmf6-5ccf. The fixed `cryptography` versions for those remaining advisories require versions that cannot be installed with `pybluemonday==0.0.14`; no newer `pybluemonday` release exists to relax that `cffi` constraint.

## flask

Found advisories PYSEC-2023-62 and CVE-2026-27205 against `Flask==2.0.3`.

Changed `Flask` to `3.1.3`, the fixed version required for CVE-2026-27205. Updated Flask-adjacent dependencies and the small app compatibility points required to keep the test suite passing.

## idna

Found advisories PYSEC-2024-60 and PYSEC-2026-215 against `idna==2.10`.

Regenerated the lock so `idna` resolves to `3.18`, above the highest reported fixed version.

## mako

Found advisories PYSEC-2022-260 and CVE-2026-44307 against `Mako==1.1.3`.

Regenerated the lock so `Mako` resolves to `1.3.12`, the highest fixed version reported by `pip-audit`.

## pillow

Found advisories PYSEC-2026-165, PYSEC-2026-457, PYSEC-2026-1793, and CVE-2026-42310 against `Pillow==10.1.0`.

Changed `Pillow` to `12.2.0`, which is at or above the highest fixed version reported by `pip-audit`.

## pydantic

Found advisory PYSEC-2026-1812 against `pydantic==1.6.2`.

Changed `pydantic` to `1.10.13`, the fixed version on the existing 1.x line.

## pymysql

Found advisory PYSEC-2026-502 against `PyMySQL==1.0.2`.

Changed `PyMySQL[rsa]` to `1.1.1`, the fixed version reported by `pip-audit`.

## python-dotenv

Found advisory CVE-2026-28684 against `python-dotenv==0.13.0`.

Changed `python-dotenv` to `1.2.2`, the fixed version reported by `pip-audit`.

## requests

Found advisories PYSEC-2026-1872 and CVE-2026-25645 against `requests==2.32.3`.

Changed `requests` to `2.33.0`, the fixed version required for CVE-2026-25645.

## werkzeug

Found advisories PYSEC-2022-203, PYSEC-2023-57, PYSEC-2023-58, PYSEC-2023-221, PYSEC-2026-2046, PYSEC-2026-2045, PYSEC-2026-2044, PYSEC-2026-2043, CVE-2024-49767, and CVE-2026-27199 against `Werkzeug==2.0.3`.

Changed `Werkzeug` to `3.1.6`, the highest fixed version reported by `pip-audit`.
