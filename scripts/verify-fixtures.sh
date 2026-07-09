#!/usr/bin/env bash
# Freeze-readiness check: confirm every SLOTS.yaml slot is flagged by BOTH bomly
# (--enrich --audit) and the ecosystem's independent second scanner, at the
# frozen baseline. Prints a per-slot table and exits non-zero if any slot is
# missed by either scanner.
#
# Requirements on PATH: bomly, node, npm, python3.12, mvn (JDK 17+), trivy,
# pip-audit (any venv). JAVA_HOME must point at a real JDK for the Maven scan.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
: "${JAVA_HOME:=$(/usr/libexec/java_home 2>/dev/null || echo /opt/homebrew/opt/openjdk)}"
export JAVA_HOME
export PATH="$JAVA_HOME/bin:$PATH"
PIP_AUDIT="${PIP_AUDIT:-pip-audit}"

fail=0
row() { printf '  %-32s %-10s %-10s\n' "$1" "$2" "$3"; }

# has_pkg <json-or-text> <needle> -> prints yes/no
has() { grep -qi -- "$2" <<<"$1" && echo yes || echo no; }

echo "== bomly scans (=enrich =audit) =="
BOMLY_NPM=$(cd "$ROOT/fixtures/webapp" && bomly scan --path . --enrich --audit --format json 2>/dev/null)
BOMLY_PY=$(cd "$ROOT/fixtures/service" && bomly scan --path . --enrich --audit --format json 2>/dev/null)
BOMLY_JV=$(cd "$ROOT/fixtures/api-java" && bomly scan --path . --enrich --audit --format json 2>/dev/null)

echo "== second-opinion scanners =="
NPM_AUDIT=$(cd "$ROOT/fixtures/webapp" && npm audit --json 2>/dev/null)
PY_AUDIT=$(cd "$ROOT/fixtures/service" && $PIP_AUDIT -r requirements.txt --vulnerability-service osv --progress-spinner off 2>/dev/null)
JV_AUDIT=$(cd "$ROOT/fixtures/api-java" && trivy fs --scanners vuln --skip-db-update --quiet . 2>/dev/null)

echo
printf '  %-32s %-10s %-10s\n' "slot / package" "bomly" "2nd-scan"
printf '  %-32s %-10s %-10s\n' "--------------" "-----" "--------"

check() { # <label> <bomly-blob> <needle> <audit-blob> <audit-needle>
  local b s; b=$(has "$2" "$3"); s=$(has "$4" "$5")
  row "$1" "$b" "$s"
  [ "$b" = yes ] && [ "$s" = yes ] || fail=1
}

# npm (fixtures/webapp)
check "S1 axios"             "$BOMLY_NPM" "axios"          "$NPM_AUDIT" "axios"
check "S2 jsonwebtoken"      "$BOMLY_NPM" "jsonwebtoken"    "$NPM_AUDIT" "jsonwebtoken"
check "S3 tough-cookie"      "$BOMLY_NPM" "tough-cookie"    "$NPM_AUDIT" "tough-cookie"
check "S4 path-to-regexp"    "$BOMLY_NPM" "path-to-regexp"  "$NPM_AUDIT" "path-to-regexp"
check "S7 lodash"            "$BOMLY_NPM" "lodash"          "$NPM_AUDIT" "lodash"
# python (fixtures/service, v2: vendored CTFd)
check "S5 mako"               "$BOMLY_PY" "mako"            "$PY_AUDIT" "mako"
check "S8 pydantic"           "$BOMLY_PY" "pydantic"        "$PY_AUDIT" "pydantic"
# java (fixtures/api-java, v2: vendored Dependency-Track)
# S6 and S10 are the SAME package (jackson-databind), different advisory
# subsets (see SLOTS.yaml) — this coarse package-presence check can't tell
# them apart, so both rows will read "yes" from the same underlying finding.
# That's fine here (this script is a freeze-readiness smoke test, not the
# scorer); harness/verify.py's actual scoring is advisory-ID-scoped.
check "S6 jackson-databind (no-fix trap)" "$BOMLY_JV" "jackson-databind" "$JV_AUDIT" "jackson-databind"
check "S9 nimbus-jose-jwt"    "$BOMLY_JV" "nimbus-jose-jwt" "$JV_AUDIT" "nimbus-jose-jwt"
check "S10 jackson-databind"  "$BOMLY_JV" "jackson-databind" "$JV_AUDIT" "jackson-databind"

echo
if [ "$fail" = 0 ]; then
  echo "ALL 10 SLOTS confirmed by bomly AND second scanner."
else
  echo "MISS: at least one slot not flagged by both scanners (see 'no' above)."
fi
exit "$fail"
