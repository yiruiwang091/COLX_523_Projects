#!/usr/bin/env bash
# start_annotation.sh
# Start the Label Studio annotation service and set up all projects.
#
# Usage:
#   cd Sprint_3
#   bash start_annotation.sh
#
# To stop the service later:
#   cd Sprint_3
#   docker-compose down

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── 1. Start Label Studio ─────────────────────────────────────────────────────
echo "=== Starting Label Studio via Docker Compose ==="
docker-compose up -d

# ── 2. Install requests if needed ────────────────────────────────────────────
python3 -c "import requests" 2>/dev/null || pip3 install --quiet requests

# ── 3. Run project setup (waits for LS to be ready, then creates projects) ───
echo ""
echo "=== Creating projects and importing annotation data ==="
python3 src/setup_labelstudio.py

# ── 4. Print sharing instructions ────────────────────────────────────────────
echo ""
echo "================================================================"
echo " SHARING THE SERVICE WITH YOUR TEAM"
echo "================================================================"
echo ""
echo " Label Studio is running on port 8080."
echo ""
echo " Your WSL2 IP (internal, not for WiFi sharing):"
ip addr show eth0 2>/dev/null | grep 'inet ' | awk '{print "   " $2}' || echo "   (could not detect)"
echo ""
echo " To get your WINDOWS WiFi IP (the one to share):"
echo "   1. Open Windows Start Menu → search 'cmd' → open Command Prompt"
echo "   2. Run: ipconfig"
echo "   3. Look for 'Wireless LAN adapter Wi-Fi' → 'IPv4 Address'"
echo "   Example: 192.168.1.42"
echo ""
echo " Share this URL with your team:"
echo "   http://<YOUR-WIFI-IP>:8080"
echo ""
echo " Login credentials:"
echo "   Email:    admin@colx523.com"
echo "   Password: colx523admin"
echo ""
echo " NOTE: Docker Desktop on Windows automatically bridges WSL2 ports"
echo " to the Windows host, so port 8080 should be reachable on WiFi."
echo " If it is NOT reachable, run this in Windows PowerShell (as admin):"
echo "   netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=127.0.0.1"
echo "================================================================"
