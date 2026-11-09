# SKYGUARD on Google Cloud (configuration-ready)

Passive drone-detection hobby stack. On a cloud VM there are **no real sensors**, so the default profile runs in **Software Emulation Mode** with only Blackbox + Fusion enabled.

## Layout on the VM

```
/opt/skyguard/
  00_Master_Launcher/start_all.sh     # sources env, launches master
  config/skyguard.env                 # live tunables (systemd EnvironmentFile)
  config/skyguard.env.example         # commented template
  config/nodes.json                   # extra cameras / remote nodes registry
  bin/skyguard                        # helper CLI (also installed to /usr/local/bin)
```

## Quick ops

```bash
skyguard status
skyguard logs 100
skyguard config
skyguard set REF_LAT 51.98
skyguard set REF_LON 5.91
skyguard enable PIXEL_TRACKER   # after camera is reachable
skyguard restart
skyguard tailscale              # Tailscale 100.x / MagicDNS
```

Systemd:
```bash
sudo systemctl status skyguard
sudo journalctl -u skyguard -f
sudo systemctl restart skyguard
```

## Adding a camera / sensor later

1. **Reach the LAN device from the cloud VM** — `192.168.x.x` is not routable from GCP.
   Use a VPN/tunnel:
   - **Tailscale (recommended):** install on the VM *and* on a field machine that can see the camera.
     Then use the camera's Tailscale IP (`100.x.y.z`) or MagicDNS name in `RTSP_URL`.
   - Or WireGuard site-to-site / reverse SSH tunnel.
2. Register and enable:
   ```bash
   skyguard add-camera tapo-front 'rtsp://100.x.y.z:554/stream1' 100.x.y.z
   skyguard set RTSP_URL 'rtsp://100.x.y.z:554/stream1'
   skyguard set PTZ_CAMERA_IP 100.x.y.z
   skyguard set PTZ_CAMERA_USER admin
   skyguard set PTZ_CAMERA_PASSWORD 'your-password'
   skyguard enable PIXEL_TRACKER
   skyguard enable PTZ_TRACKER   # optional
   skyguard restart
   skyguard status
   ```
3. `nodes.json` is read by `furnace_master_start_all.py` at start. Enabled cameras are logged; the first can seed `RTSP_URL` if unset. Remote nodes are exported as `SKYGUARD_EXTRA_NODES` JSON for peers.

## Adding a remote node (Pixel / field box)

```bash
skyguard add-node pixel-1 100.x.y.z 9092 tactical
skyguard restart
```

Prefer Tailscale IPs or MagicDNS (`pixel-1.tailnet.ts.net`) over raw LAN addresses.

## Tailscale on this VM

```bash
# already installed by cloud bootstrap when approved
sudo tailscale up --hostname=skyguard-cloud
skyguard tailscale
```

Authorize via the printed `https://login.tailscale.com/a/...` URL. After that, field devices join the same tailnet and can reach Blackbox TCP `9090` on the VM's `100.x` address (open GCP firewall only if you also need public access).

## Default enable flags (cloud)

| Flag | Default | Why |
|------|---------|-----|
| `SKYGUARD_EMULATION` | `true` | no USB serial on GCP |
| `ENABLE_BLACKBOX` | `true` | TCP :9090 + log file |
| `ENABLE_FUSION` | `true` | production engine heartbeat |
| `ENABLE_PIXEL_TRACKER` | `false` | needs RTSP (would crash-loop) |
| `ENABLE_PTZ_TRACKER` | `false` | needs PTZ on LAN/VPN |

## Tunables in `skyguard.env`

`BLACKBOX_PORT`, `SSD_LOG_PATH`, `RTSP_URL`, `HUD_HOST`, `HUD_PORT`, `PTZ_CAMERA_IP/USER/PASSWORD`, `GEMINI_API_KEY`, `REF_LAT/LON/ALT`, `SKYGUARD_EMULATION`, `ENABLE_*`.

## Notes

- YOLOv8 / ultralytics / torch are **optional**; pixel tracker falls back to OpenCV MOG2 if missing (and is disabled by default on cloud).
- `SSD_LOG_PATH` defaults to `/var/log/skyguard/furnace_sigint.log` (writable), not `/mnt/ssd_logger/...`.


## Current deployment note (2026-11-09)

GCE (`e2-micro`) could not be created yet: the billed Firebase / Google Cloud projects
(`effective-autonomy-g5wls`, `polynomial-cogency-zsmzh`) block enabling Compute Engine
(org `gcp.restrictServiceUsage` / missing `serviceusage.services.enable`), and the
standalone project `skyguard-furnace-196386` has **no billing account linked**
(no `billing.resourceAssociations.create` on the managed billing accounts).

**Interim host:** Google Cloud Shell (`gcloud cloud-shell ssh`), with SkyGuard under
`/opt/skyguard`, Blackbox on TCP **9090**, Fusion heartbeat, PIXEL/PTZ disabled.
Home disk persists; the Cloud Shell VM itself is ephemeral — re-run
`~/bootstrap_cloudshell.sh` after a cold start, or link billing and run
`/workspace/skyguard_cloud/deploy_gcp.sh` for a real `e2-micro`.

### Tailscale authorize (do this once)

Open the auth URL printed by `sudo tailscale up` / `skyguard tailscale`, e.g.:

```
https://login.tailscale.com/a/<token>
```

Then field devices on the same tailnet can use `100.x` / MagicDNS in `RTSP_URL`,
`skyguard add-camera`, and `skyguard add-node`.
