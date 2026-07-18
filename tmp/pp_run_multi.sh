#!/usr/bin/env bash
set -uo pipefail
ENVF=/opt/hermes/secure/projects/prostye-postavki/.env
IP=$(grep -a -m1 -E '^IP=' "$ENVF" | cut -d= -f2- | tr -d '\r "')
RUSER=$(grep -a -m1 -E '^USER=' "$ENVF" | cut -d= -f2- | tr -d '\r "')
PW=$(grep -a -m1 -E '^PASSWORD=' "$ENVF" | cut -d= -f2- | tr -d '\r')
sshpass -p "$PW" scp -o StrictHostKeyChecking=accept-new /tmp/pp_multi_look.py "$RUSER@$IP:/tmp/pp_multi_look.py" || exit 3
sshpass -p "$PW" ssh -o StrictHostKeyChecking=accept-new "$RUSER@$IP" '/var/www/prostye-postavki/app/.venv/bin/python /tmp/pp_multi_look.py'
