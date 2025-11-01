#!/usr/bin/env bash
# Simple health check script for local monitoring.

set -euo pipefail

print_section() {
  printf '\n==== %s ====\n' "$1"
}

print_section "Disk Usage"
if command -v df >/dev/null 2>&1; then
  df -h
else
  echo "df command not available"
fi

print_section "Memory Usage"
if command -v free >/dev/null 2>&1; then
  free -h
else
  echo "free command not available"
fi

print_section "Top CPU Consumers"
if command -v ps >/dev/null 2>&1; then
  ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head
else
  echo "ps command not available"
fi
