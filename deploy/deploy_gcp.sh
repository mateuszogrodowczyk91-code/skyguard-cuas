#!/bin/bash
# Deploy SkyGuard to GCE once billing + Compute API are available.
set -euo pipefail
export PATH="/workspace/google-cloud-sdk/bin:$PATH"
PROJECT="${1:-skyguard-furnace-196386}"
ZONE="${ZONE:-us-central1-a}"
MACHINE="${MACHINE:-e2-micro}"
NAME="${NAME:-skyguard-cloud}"
gcloud config set project "$PROJECT"
gcloud services enable compute.googleapis.com --project="$PROJECT"
# Create VM if missing
if ! gcloud compute instances describe "$NAME" --zone="$ZONE" --project="$PROJECT" >/dev/null 2>&1; then
  gcloud compute instances create "$NAME" \
    --project="$PROJECT" \
    --zone="$ZONE" \
    --machine-type="$MACHINE" \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size=20GB \
    --tags=skyguard \
    --metadata=enable-oslogin=TRUE
fi
# Firewall for blackbox TCP 9090 (tagged)
if ! gcloud compute firewall-rules describe skyguard-allow-9090 --project="$PROJECT" >/dev/null 2>&1; then
  gcloud compute firewall-rules create skyguard-allow-9090 \
    --project="$PROJECT" \
    --allow=tcp:9090 \
    --target-tags=skyguard \
    --description="SkyGuard Blackbox TCP"
fi
# Copy project
gcloud compute ssh "$NAME" --zone="$ZONE" --project="$PROJECT" --command='sudo mkdir -p /opt/skyguard && sudo chown $(whoami) /opt/skyguard'
gcloud compute scp --recurse --zone="$ZONE" --project="$PROJECT" \
  /workspace/skyguard_cloud/skyguard-project/* "$NAME":/opt/skyguard/ \
  --compress
# Also copy nested dirs properly via tar
tar -C /workspace/skyguard_cloud/skyguard-project -czf /tmp/skyguard-deploy.tgz .
gcloud compute scp --zone="$ZONE" --project="$PROJECT" /tmp/skyguard-deploy.tgz "$NAME":/tmp/
gcloud compute scp --zone="$ZONE" --project="$PROJECT" /workspace/skyguard_cloud/bootstrap_vm.sh "$NAME":/tmp/
gcloud compute ssh "$NAME" --zone="$ZONE" --project="$PROJECT" --command='
  sudo mkdir -p /opt/skyguard && sudo tar -C /opt/skyguard -xzf /tmp/skyguard-deploy.tgz
  sudo bash /tmp/bootstrap_vm.sh
  echo EXTERNAL_IP=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)
  echo TAILSCALE_LOG:
  cat /tmp/tailscale-up.log || true
'
