#!/bin/bash
set -u
status=0
for tool in gitleaks semgrep osv-scanner; do
 if ! command -v "$tool" >/dev/null 2>&1; then printf 'MISSING %s\n' "$tool" >&2; status=1; continue; fi
 if ! "$tool" --version; then printf 'VERSION_FAIL %s\n' "$tool" >&2; status=1; continue; fi
 case "$tool" in
  gitleaks) gitleaks git . --no-banner --redact || status=1 ;;
  semgrep) semgrep scan --config auto --error . || status=1 ;;
  osv-scanner) osv-scanner scan --recursive ./ || status=1 ;;
 esac
done
if [ "$status" -eq 0 ]; then echo SCAN=OK; else echo SCAN=FAIL; fi
exit "$status"
