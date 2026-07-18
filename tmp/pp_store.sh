#!/usr/bin/env bash
cd /var/www/prostye-postavki/app/backend/data/pending_contract_files
for f in *.preview.bin; do
  [ -f "$f" ] || continue
  echo "$f: $(head -c 5 "$f") size=$(stat -c %s "$f")"
done
