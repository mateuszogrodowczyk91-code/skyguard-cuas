#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
mkdir -p ~/.cloudshell
touch ~/.cloudshell/no-apt-get-warning

echo "=== apt ==="
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip python3-dev build-essential rsync

echo "=== layout ==="
sudo mkdir -p /opt/skyguard /var/log/skyguard
sudo rsync -a ~/skyguard/ /opt/skyguard/
sudo cp -n /opt/skyguard/config/skyguard.env.example /opt/skyguard/config/skyguard.env || true
sudo chmod 0755 /opt/skyguard/bin/skyguard /opt/skyguard/00_Master_Launcher/start_all.sh
sudo install -m 0755 /opt/skyguard/bin/skyguard /usr/local/bin/skyguard

echo "=== venv ==="
sudo python3 -m venv /opt/skyguard/venv
sudo /opt/skyguard/venv/bin/pip install --upgrade pip
sudo /opt/skyguard/venv/bin/pip install numpy scipy requests opencv-python-headless pyserial
sudo sed -i 's|^exec python3 |exec /opt/skyguard/venv/bin/python3 |' /opt/skyguard/00_Master_Launcher/start_all.sh || true

echo "=== tests ==="
set -a
# shellcheck disable=SC1091
source /opt/skyguard/config/skyguard.env
set +a
cd /opt/skyguard
sudo -E /opt/skyguard/venv/bin/python3 06_Testy_Automatyczne/test_production_engine.py -v | tee /tmp/skyguard_test_results.txt
sudo cp /tmp/skyguard_test_results.txt /var/log/skyguard/test_results.txt || true

echo "=== engine once ==="
sudo -E /opt/skyguard/venv/bin/python3 00_Master_Launcher/skyguard_production_engine_v7.py | tee /tmp/skyguard_engine_once.txt
sudo cp /tmp/skyguard_engine_once.txt /var/log/skyguard/engine_once.txt || true

echo "=== start master (nohup; Cloud Shell is ephemeral / limited systemd) ==="
sudo pkill -f furnace_master_start_all.py || true
sudo bash -c 'cd /opt/skyguard/00_Master_Launcher && set -a && . /opt/skyguard/config/skyguard.env && set +a && nohup /bin/bash ./start_all.sh >/var/log/skyguard/master.out 2>&1 &'
sleep 5
ps aux | grep -E 'furnace_master|furnace_blackbox|fusion_heartbeat|pixel_tracker|tapo-ptz' | grep -v grep || true
echo "--- master.out ---"
sudo tail -n 50 /var/log/skyguard/master.out || true

# Try systemd unit anyway (may not persist / may lack systemd)
if [ -d /run/systemd/system ]; then
  sudo install -m 0644 /opt/skyguard/05_Deploy_i_CI_CD/skyguard-systemd-service.service /etc/systemd/system/skyguard.service
  sudo systemctl daemon-reload || true
  sudo systemctl enable skyguard || true
  sudo systemctl restart skyguard || true
  sleep 2
  systemctl is-active skyguard || true
fi

echo "=== Tailscale ==="
if ! command -v tailscale >/dev/null 2>&1; then
  curl -fsSL https://tailscale.com/install.sh | sudo sh
fi
# Start tailscaled
if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
  sudo systemctl enable --now tailscaled || true
else
  sudo mkdir -p /var/lib/tailscale
  sudo pkill tailscaled || true
  sudo nohup tailscaled --state=/var/lib/tailscale/tailscaled.state >/var/log/skyguard/tailscaled.out 2>&1 &
  sleep 2
fi

rm -f /tmp/tailscale-up.log /tmp/tailscale-up2.log
# Non-blocking: capture login URL
set +e
sudo timeout 10s tailscale up --hostname=skyguard-cloud --timeout=5s >/tmp/tailscale-up.log 2>&1
sudo nohup timeout 60s tailscale up --hostname=skyguard-cloud >/tmp/tailscale-up2.log 2>&1 &
sleep 6
set -e
echo "=== TAILSCALE_UP_LOG ==="
cat /tmp/tailscale-up.log 2>/dev/null || true
echo "=== TAILSCALE_UP_LOG2 ==="
cat /tmp/tailscale-up2.log 2>/dev/null || true
echo "=== TAILSCALE_STATUS ==="
tailscale status 2>/dev/null || sudo tailscale status 2>/dev/null || true
# Extract URL
grep -Eo 'https://login\.tailscale\.com/a/[A-Za-z0-9]+' /tmp/tailscale-up.log /tmp/tailscale-up2.log 2>/dev/null || true
echo BOOTSTRAP_DONE
