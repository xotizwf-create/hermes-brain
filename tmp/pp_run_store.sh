#!/usr/bin/env bash
set -uo pipefail
ENVF=/opt/hermes/secure/projects/prostye-postavki/.env
IP=$(grep -a -m1 -E '^IP=' "$ENVF" | cut -d= -f2- | tr -d '\r "')
RUSER=$(grep -a -m1 -E '^USER=' "$ENVF" | cut -d= -f2- | tr -d '\r "')
PW=$(grep -a -m1 -E '^PASSWORD=' "$ENVF" | cut -d= -f2- | tr -d '\r')
sshpass -p "$PW" scp -o StrictHostKeyChecking=accept-new /tmp/pp_store.sh "$RUSER@$IP:/tmp/pp_store.sh" || exit 3
sshpass -p "$PW" ssh -o StrictHostKeyChecking=accept-new "$RUSER@$IP" 'bash /tmp/pp_store.sh'
