#!/usr/bin/env bash
# Reproducible network-boundary check. Benign: a harmless curl to a LOCAL loopback
# service. No exploit, no dsh control API, no credentials. Shows that dsh's sandbox
# profile does NOT confine the network, while Codex's --unshare-net profile does.
set -u
PORT=58080
# 1. A plain loopback service (stand-in for "a service listening on 127.0.0.1").
python3 -m http.server $PORT --bind 127.0.0.1 >/dev/null 2>&1 &
SRV=$!; sleep 1
trap "kill $SRV 2>/dev/null" EXIT

probe='curl -s -o /dev/null -w "%{http_code}" --max-time 4 http://127.0.0.1:'$PORT'/'

# dsh's Linux sandbox profile  (packages/sandbox/sandbox-local/src/profiles.ts:17)
DSH="--ro-bind / / --dev /dev --unshare-pid --proc /proc --die-with-parent"
# Codex CLI's profile adds a separate network namespace (codex-rs/.../bwrap.rs:290)
CODEX="$DSH --unshare-net"

run() { timeout 10 bwrap $1 bash -c "$probe" 2>/dev/null; }

echo "Service: http://127.0.0.1:$PORT  (plain python http.server on loopback)"
echo
D_OUT=$(run "$DSH");  echo "[dsh profile]    curl 127.0.0.1:$PORT  -> HTTP ${D_OUT:-BLOCKED}"
C_OUT=$(run "$CODEX"); echo "[codex profile]  curl 127.0.0.1:$PORT  -> HTTP ${C_OUT:-BLOCKED}"
echo
# curl prints 000 when it cannot connect at all.
[ "$D_OUT" = "200" ] && echo "dsh:   sandboxed process REACHED the loopback service  (network NOT confined)" \
                     || echo "dsh:   blocked, code $D_OUT (unexpected)"
{ [ "$C_OUT" = "000" ] || [ -z "$C_OUT" ]; } && echo "codex: sandboxed process COULD NOT connect  (network confined by --unshare-net)" \
                     || echo "codex: reached it, HTTP $C_OUT (unexpected)"
