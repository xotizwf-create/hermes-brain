#!/usr/bin/env bash
ls -lat /root/.hermes/ | head -20
echo "=== sessions ==="
ls -lat /root/.hermes/sessions/ 2>/dev/null | head -10
ls -lat /root/.hermes/history/ 2>/dev/null | head -10
find /root/.hermes -maxdepth 2 -name "*.json" -newermt "-4 hours" -size +10k 2>/dev/null | head -10
find /root/.hermes -maxdepth 3 -type d -name "*session*" 2>/dev/null | head
