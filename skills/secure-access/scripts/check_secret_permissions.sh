#!/usr/bin/env bash
set -euo pipefail

for path in /root/.hermes/secure /root/.hermes/secure/access-map.yaml /root/.hermes/secure/secrets.yaml; do
  if [ -e "$path" ]; then
    stat -c "%a %U:%G %n" "$path"
  else
    echo "missing $path"
  fi
done
