#!/usr/bin/env bash
# Runs ON 217: jump-host runner for prostye-postavki prod. Secrets stay in memory.
set -uo pipefail
ENVF=/opt/hermes/secure/projects/prostye-postavki/.env
IP=$(grep -a -m1 -E '^IP=' "$ENVF" | cut -d= -f2- | tr -d '\r "')
RUSER=$(grep -a -m1 -E '^USER=' "$ENVF" | cut -d= -f2- | tr -d '\r "')
PW=$(grep -a -m1 -E '^PASSWORD=' "$ENVF" | cut -d= -f2- | tr -d '\r')
if [ -z "$IP" ] || [ -z "$RUSER" ] || [ -z "$PW" ]; then echo "MISSING_CREDS"; exit 1; fi
command -v sshpass >/dev/null || { echo "NO_SSHPASS"; exit 2; }
sshpass -p "$PW" scp -o StrictHostKeyChecking=accept-new /tmp/pp_rollback.sh "$RUSER@$IP:/tmp/pp_rollback.sh" || exit 3
sshpass -p "$PW" ssh -o StrictHostKeyChecking=accept-new "$RUSER@$IP" 'bash /tmp/pp_rollback.sh'
