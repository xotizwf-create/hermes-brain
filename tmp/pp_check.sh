#!/usr/bin/env bash
export DEBIAN_FRONTEND=noninteractive
apt-get install -y -q poppler-utils 2>&1 | tail -2
command -v pdftoppm && pdftoppm -v 2>&1 | head -1
