#!/bin/bash
# Run ON the VM as root after project files are in /opt/skyguard
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv python3-pip python3-dev build-essential
mkdir -p /opt/skyguard /var/log/skyguard /opt/skyguard/config
cd /opt/skyguard
python3 -m venv /opt/skyguard/venv
# shellcheck disable=SC1091
source /opt/skyguard/venv/bin/activate
pip install --upgrade pip
pip install numpy scipy requests opencv-python-headless pyserial
# ultralytics/torch intentionally skipped on small VMs — vision node falls back / stays disabled

# Prefer venv python for service
sed -i 's|^exec python3 |exec /opt/skyguard/venv/bin/python3 |' /opt/skyguard/00_Master_Launcher/start_all.sh || true

install -m 0755 /opt/skyguard/bin/skyguard /usr/local/bin/skyguard
install -m 0644 /opt/skyguard/05_Deploy_i_CI_CD/skyguard-systemd-service.service /etc/systemd/system/skyguard.service
# Ensure env defaults
if [ ! -f /opt/skyguard/config/skyguard.env ]; then
  cp /opt/skyguard/config/skyguard.env.example /opt/skyguard/config/skyguard.env
fi
systemctl daemon-reload
systemctl enable skyguard

# Run tests once
cd /opt/skyguard
set -a; source /opt/skyguard/config/skyguard.env; set +a
/opt/skyguard/venv/bin/python3 06_Testy_Automatyczne/test_production_engine.py -v 2>&1 | tee /var/log/skyguard/test_results.txt || true

# Run production engine once
/opt/skyguard/venv/bin/python3 00_Master_Launcher/skyguard_production_engine_v7.py 2>&1 | tee /var/log/skyguard/engine_once.txt || true

systemctl restart skyguard
sleep 3
systemctl is-active skyguard || true
journalctl -u skyguard -n 40 --no-pager || true

# Tailscale (user-approved)
if ! command -v tailscale >/dev/null 2>&1; then
  curl -fsSL https://tailscale.com/install.sh | sh
fi
systemctl enable --now tailscaled
# Non-blocking auth URL capture
rm -f /tmp/tailscale-up.log
nohup tailscale up --hostname=skyguard-cloud --timeout=5s >/tmp/tailscale-up.log 2>&1 &
sleep 6
echo "=== TAILSCALE UP OUTPUT ==="
cat /tmp/tailscale-up.log || true
tailscale status || true
