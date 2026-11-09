# Mapa gałęzi → release/skyguard-complete-2026-11-02

Stan na 02.11.2026. Żadna gałąź nie została usunięta ani nadpisana – ta tabela mówi tylko, gdzie jej zawartość jest teraz w gałęzi `release/skyguard-complete-2026-11-02`.

* **w środku** – cała gałąź (wszystkie jej commity) jest częścią historii wydania; kolumna „Gdzie” mówi, w którym katalogu.
* **zastąpiona** – nie scalona, bo nowsza wersja tych samych zmian już jest w wydaniu (powód w tabeli).

Podsumowanie: w środku: 135, zastąpiona: 6, gałąź wydania: 1 (razem 142). Pełne podsumowanie PR-ów: `PODSUMOWANIE.md`.

Kopia zapasowa main sprzed zmian: tag `backup/main-24c8d92-2026-11-02`.

| Gałąź | Commit | Data | Status | Gdzie / dlaczego | Ostatni commit |
|---|---|---|---|---|---|
| `release/skyguard-complete-2026-11-02` | bed0835 | 2026-11-02 | wydanie | gałąź wydania (PR #106 → main) | Merge feature/android-clean-recorder: Android v1.7.2 Czysty nagrywacz |
| `feature/realtime-dsp-stack` | 686710d | 2026-11-02 | w środku | pakiet `skyguard/` + `tools/realtime-dsp/` (PR #107, scalony 02.11.2026) | feat(python): unified skyguard package (dsp/radar/doa/fusion/realtime) + realtime DSP VS s… |
| `feature/android-clean-recorder` | f09c79a | 2026-11-02 | w środku | aplikacja Android (katalog główny: `app/`), v1.7.2 | Android v1.7.2: Czysty nagrywacz (UNPROCESSED 48 kHz WAV, no AGC/NS/AEC/HPF, live 0-500 Hz… |
| `feature/android-gps-drift-check` | 6075c9a | 2026-11-02 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.7.1: GPS UCIEKA – slow-drift GPS spoofing check while the phone lies still: no … |
| `feature/android-upload-md5-verify` | 21bfcb8 | 2026-11-02 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.7.0: SPRAWDZONE MD5 – a phone recording/photo is deleted only after Drive itsel… |
| `feature/android-rid-spoof-check` | e967199 | 2026-11-02 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.6.9: FAŁSZYWY RID – physics/range sanity check of Remote ID + DJI Wi-Fi DroneID… |
| `feature/android-dji-wifi-droneid` | 9f91e67 | 2026-11-02 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.6.8: DJI WI-FI ID – passive decoding of DJI's own DroneID telemetry (vendor IE … |
| `feature/android-wind-noise-gate` | 338e2b3 | 2026-11-02 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.6.7: WIATR – wykrywanie wiatru na mikrofonie (stereo MSC 50–300 Hz / mono LF+fl… |
| `feature/android-v165-cloud-storage` | 6bb6c7d | 2026-11-02 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.6.6: 'Kamera w tle' OFF by default and forced OFF once on upgrade (PrivacyMigra… |
| `feature/android-record-gate-88` | 1e3dba4 | 2026-11-02 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.6.4: auto-save only at >=88% drone confidence (RecordGate) – phone keeps listen… |
| `feature/android-cell-tower-screen` | 5a2d542 | 2026-11-02 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.6.3: MASZTY tab – every seen cell tower colour-coded (green OK = known here / '… |
| `feature/android-fake-cell-tower` | b79dac4 | 2026-11-01 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.6.2: FAŁSZYWY MASZT – read-only fake cell tower / IMSI-catcher signs from Telep… |
| `feature/cuas-reference-module` | ca7b200 | 2026-11-01 | w środku | moduł C-UAS (`tools/acoustic/cuas/`) | C-UAS reference module: real bug fixes (short clips, Doppler fit outliers, digital silence… |
| `feature/android-yamnet-level-norm` | c2d411d | 2026-11-01 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.6.1: SG-FUZJA v2.1 – YAMNet input level-normalised to -30 dBFS (max +40 dB, sam… |
| `feature/android-acoustic-ensemble-160` | 5c17026 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.6.0: SG-FUZJA acoustic ensemble – YAMNet (LiteRT, Apache-2.0) embedding+scores … |
| `feature/centrum-opensky-auth` | 4dd48b7 | 2026-10-29 | w środku | Centrum PC (`tools/windows/skyguard-centrum/`) | SKYGUARD Centrum 1.2.1: OpenSky auto-login – OAuth2 client credentials from opensky_creden… |
| `feature/android-attack-tools` | 99b3bb0 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.5.2: OpenSky auto-login – built-in OAuth2 client-credentials account from gitig… |
| `feature/android-opensky-auth` | 99b3bb0 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.5.2: OpenSky auto-login – built-in OAuth2 client-credentials account from gitig… |
| `feature/android-wifi-lure` | 772062e | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.5.1: WI-FI – WABIKI (read-only lure/rogue AP detection: follower 'Sieć jedzie z… |
| `feature/android-sky-camera` | f046427 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.5.0: sky camera (night blink/motion, day dots), auto GPS photos, TFLite stub, G… |
| `feature/centrum-atak-cot` | fa2b97c | 2026-10-29 | w środku | Centrum PC (`tools/windows/skyguard-centrum/`) | SKYGUARD Centrum 1.2.0: ATAK/TAK node – CoT multicast 239.2.3.1:6969 (station, OpenSky air… |
| `feature/android-atak-cot` | 8070ec2 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | Android v1.4.0: ATAK/TAK node – CoT multicast 239.2.3.1:6969 on by default, optional TAK S… |
| `feature/drive-backup-handoff` | e2888f3 | 2026-10-29 | w środku | kopia na Dysk / NBL (`tools/windows/drive-backup/`) | fix(windows): Drive backup v2.3.1 – wrap running-copy lookup in @() (single CimInstance ha… |
| `feature/acoustic-net` | fd9524c | 2026-10-29 | w środku | Centrum PC (`tools/windows/skyguard-centrum/`) | SKYGUARD Centrum 1.1.0: automatic SG-NET acoustic drone detection on the camera recordings… |
| `feature/android-acoustic-net` | 75a604c | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | v1.3.2: SG-NET acoustic drone classifier in the background mic pipeline – small CNN (25k p… |
| `feature/opensky` | 92ee4fc | 2026-10-29 | w środku | Centrum PC (`tools/windows/skyguard-centrum/`) | SKYGUARD Centrum 1.0.0: one integrated PC program (map + OpenSky ADS-B + detections + reco… |
| `feature/android-opensky` | d0db76e | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | v1.3.1: OpenSky ADS-B sensor fusion – automatic anonymous polling within 400 credits/day (… |
| `feature/drive-backup-progress` | 1282a64 | 2026-10-29 | w środku | kopia na Dysk / NBL (`tools/windows/drive-backup/`) | feat(windows): Drive backup v2.2 – live progress in status.json (heartbeat, current_job, %… |
| `feature/android-drive-webhook` | db454e8 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | v1.3.0: Drive upload without Google Cloud OAuth client – phone posts straight to a user-ow… |
| `feature/android-drive-log-parts` | bca9e92 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | v1.2.9: Drive log upload in parts (≤256 KiB open part, finished parts never re-sent) inste… |
| `feature/android-drive-upload` | bc35d19 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | v1.2.8: real-time Google Drive upload (drive.file, SKYGUARD/phone/<date>): events/location… |
| `feature/android-false-positive-filter` | 9d83176 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | v1.2.7: all evidence written automatically to Documents/SKYGUARD (audio in /audio) + Movie… |
| `feature/android-alarm-sound-settings` | b001c60 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | v1.2.6: alarm settings – 'Dźwięk alarmu' (default OFF, also after update), 'Wibracja' (def… |
| `feature/android-usb-debug-toggle` | f482efd | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | v1.2.5: in-app developer panel – 'Debugowanie USB' (adb_enabled) and 'Ograniczanie skanowa… |
| `feature/android-release-signing` | d9e0883 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | v1.2.4: stable release signing (v1+v2+v3, keystore outside git), non-debuggable release bu… |
| `feature/android-fgs-fallback` | 796cb62 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | v1.2.3: foreground-service fallback – background (sticky) restart no longer stops monitori… |
| `feature/android-event-log` | 826c3a1 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | v1.2.2: Dziennik tab (persistent detection history, filters, summary, CSV/KML/JSONL export… |
| `feature/android-storage-guard` | 7f4ea78 | 2026-10-29 | w środku | aplikacja Android (katalog główny: `app/`) | v1.2.1: storage guard (pause new video/audio when phone storage low, never delete; video s… |
| `feature/disk-compact` | 6a64f57 | 2026-10-29 | w środku | kopia na Dysk / NBL (`tools/windows/drive-backup/`) | feat(windows): compact_dev_tools -IncludeApps (IDEs, Python); guard Opera |
| `feature/disk-guard` | 9f9fcd8 | 2026-10-29 | w środku | kopia na Dysk / NBL (`tools/windows/drive-backup/`) | feat(windows): Drive backup v2.1 disk guard – atomic status.json, recorder-stopped warning… |
| `feature/drive-backup-v2` | f89d87c | 2026-10-28 | w środku | kopia na Dysk / NBL (`tools/windows/drive-backup/`) | feat(windows): Drive backup v2 – resumable hourly loop, single-instance, status.json with … |
| `unify/skyguard` | 7756dc4 | 2026-10-28 | w środku | `server-stack/` | Merge branch 'feature/pixel10pro' into unify/skyguard |
| `feature/pixel10pro` | 9ed2425 | 2026-10-28 | w środku | aplikacja Android (katalog główny: `app/`) | Cloud sync: tag position quality (exact RID / estimated / unknown) for other nodes |
| `backup/work-v5.8` | 2f53323 | 2026-10-28 | zastąpiona | zastąpiona – oczyszczona wersja tej kopii (bez plików *.pre-*, .pi) to `unify/skyguard` → `server-stack/` | backup: snapshot of local work-v5.8 working tree (2026-10-28; .github/workflows kept local… |
| `react-native-skyguard-21tech` | 7e90188 | 2026-10-28 | w środku | `legacy/react-native-21tech/` | Real code: OpenDroneID F3411, WebRTC, Firebase RTDB, TensorInference, CoT/ATAK MIL-STD-601… |
| `release/laptop-v0.3.0` | 6b52c34 | 2026-10-27 | w środku | `laptop-agent/` | release laptop-v0.3.0: include Lingxi's #102 MAC prefix fix (PR not merged) |
| `unified/v1.1` | d337daf | 2026-10-27 | w środku | `laptop-agent/` | Laptop agent v0.3.0: optional hooks #87 health, #101 f0_track/DOA/wind, #84 UPS, #75 SAHI,… |
| `fix/drone-oui-registry` | 78ffc25 | 2026-10-27 | w środku | `laptop-agent/` | fix(wifi): ignore locally-administered (randomized) MACs in drone OUI lookup |
| `feat/acoustic-f0-doa` | 64f0a17 | 2026-10-27 | w środku | `laptop-agent/` | edge: acoustic wind indicator |
| `main` | 24c8d92 | 2026-10-22 | w środku | baza (cała historia main jest w środku) | Merge remote-tracking branch 'origin/main' |
| `feature/spell-engine` | e36bb66 | 2026-10-20 | w środku | `legacy/spell-engine/` | feat(radar): Add 2D Tactical Airspace Radar, SkyGuard Incursion simulation, and standalone… |
| `unified/v1` | eaff67a | 2026-10-20 | w środku | `laptop-agent/` | feat(client): integrate Google Camera quick capture into SkyGuard drone reporting (#99) |
| `feature/lingxi-s6-10-sample-rate-drift` | 865a668 | 2026-10-20 | w środku | `laptop-agent/` | edge: sound-card sample-rate drift + gap detector (Część #38/6.10) |
| `feature/lingxi-s6-9-third-octave` | 23d398e | 2026-10-20 | w środku | `laptop-agent/` | edge: 1/3-octave band levels (IEC 61260-1) (Część #38/6.9) |
| `feature/lingxi-s6-8-spectral-shape` | 182f04e | 2026-10-20 | w środku | `laptop-agent/` | edge: spectral flatness + kurtosis features (Część #38/6.8) |
| `feat/i69-duckdb-events` | d0951ac | 2026-10-20 | w środku | `laptop-agent/` | edge: Parquet + DuckDB event log, false alarms per hour (#69 item 9) |
| `feature/lingxi-s6-7-alarm-rate-limiter` | 3f3244a | 2026-10-20 | w środku | `laptop-agent/` | edge: alarm flood limiter (cooldown + token bucket) (Część #38/6.7) |
| `feature/lingxi-s6-6-geojson-export` | d7deb02 | 2026-10-20 | w środku | `laptop-agent/` | edge: GeoJSON (RFC 7946) + CSV export (Część #38/6.6) |
| `feat/i69-fiftyone-review` | cc66b0e | 2026-10-20 | w środku | `laptop-agent/` | tools: FiftyOne review export + hard negatives (#69 item 8) |
| `feature/lingxi-s6-5-bearing-smoother` | ccaa08f | 2026-10-20 | w środku | `laptop-agent/` | edge: circular bearing smoother (0/360 wrap) (Część #38/6.5) |
| `feature/lingxi-s6-4-config-validator` | a895845 | 2026-10-20 | w środku | `laptop-agent/` | edge: agent config validator (Część #38/6.4) |
| `feat/i69-rfuav-bench` | 5857c77 | 2026-10-20 | w środku | `laptop-agent/` | tests: RFUAV IQ evaluation harness for RF detectors (#69 item 7) |
| `feature/lingxi-s6-3-mains-hum-notch` | 4a18499 | 2026-10-20 | w środku | `laptop-agent/` | edge: mains hum 50 Hz detect + notch (Część #38/6.3) |
| `feature/lingxi-s6-2-cepstrum-f0` | 589388f | 2026-10-20 | w środku | `laptop-agent/` | edge: cepstral rotor f0 estimator (Część #38/6.2) |
| `feat/i69-dronerf-classifier` | c756a28 | 2026-10-20 | w środku | `laptop-agent/` | rf: DroneRF-style 2.4 GHz spectrum classifier, numpy model (#69 item 6) |
| `feature/lingxi-s6-1-m-of-n-confirm` | 9043889 | 2026-10-20 | w środku | `laptop-agent/` | edge: M-of-N detection confirmation (Część #38/6.1) |
| `feat/i69-mavlink-sik` | 4367100 | 2026-10-20 | w środku | `laptop-agent/` | rf: receive-only MAVLink v1/v2 telemetry decoder for SiK (#69 item 5) |
| `feat/i69-meshtastic-alerts` | 42ecc27 | 2026-10-20 | w środku | `laptop-agent/` | edge: opt-in LoRa alerts via Meshtastic (#69 item 4) |
| `feat/i69-pl-uas-zones` | 3184dfa | 2026-10-20 | w środku | `laptop-agent/` | backend: Polish UAS geozones (drony.gov.pl, ED-269) (#69 item 3) |
| `feature/windows-installer` | 7d19e5b | 2026-10-20 | w środku | `laptop-agent/` | Installer: optional firewall confinement component (PR #86 tool), allowlist ini incl. Open… |
| `feat/i69-openaip-zones` | c7d7824 | 2026-10-20 | w środku | `laptop-agent/` | backend: OpenAIP airspaces + airports offline zone check (#69 item 2) |
| `feat/i69-birdnet-veto` | 5a718ed | 2026-10-20 | w środku | `laptop-agent/` | edge: BirdNET bird veto after acoustic gate (#69 item 1) |
| `fix/fix-test-port-collisions` | cff729a | 2026-10-20 | w środku | `laptop-agent/` | tests: wolne porty i katalogi tymczasowe zamiast stałych 8798/8898/8899 i /var/tmp/skyguar… |
| `feat/edge-skyguard-health` | cf742bc | 2026-10-20 | w środku | `laptop-agent/` | edge: skyguard_health v2, NTP clock check (Część #67/8) |
| `feat/windows-firewall-confinement` | f40601e | 2026-10-20 | w środku | `laptop-agent/` | edge: Windows Firewall confinement of SKYGUARD to LAN + chosen hosts |
| `feat/ntfy-push` | 2ec04da | 2026-10-20 | w środku | `laptop-agent/` | edge: ntfy push notifications for alarms (#52) |
| `feature/ups-nut` | c0ecaa5 | 2026-10-20 | w środku | `laptop-agent/` | UPS monitoring via NUT (upsc / TCP 3493): on-battery, charge, runtime; null + 'brak odczyt… |
| `feat/sdr-ppm-calibration` | 0daa830 | 2026-10-20 | w środku | `laptop-agent/` | edge: RTL-SDR ppm calibration from known reference carrier |
| `feat/antiuav-eval-harness` | 4f44257 | 2026-10-20 | w środku | `laptop-agent/` | tools: Anti-UAV benchmark eval harness, no data committed (#52) |
| `ideas-3-speech` | 51b01dd | 2026-10-20 | zastąpiona | zastąpiona – j.w. (`laptop-agent/edge-v5.8`) | Acoustic gate: optional Silero speech gate (PR #70 gate_alarm with stricter re-check), spe… |
| `feat/camera-zone-masks` | 6c374af | 2026-10-20 | w środku | `laptop-agent/` | edge: Frigate-style motion masks and detection zones (#52) |
| `feature/sky-mask-keepawake-usb` | eba3eab | 2026-10-20 | w środku | `laptop-agent/` | edge: auto sky mask, keep-awake, USB selective suspend check (#76 items 1-3) |
| `feature/nuitka-ci` | 7cd9166 | 2026-10-20 | w środku | `laptop-agent/` | ci: parallel Nuitka build of SKYGUARD-Laptop.exe (optional signing via #45 helper) |
| `feature/audio-pipeline` | 5ad1be1 | 2026-10-20 | w środku | `laptop-agent/` | edge: audio_pipeline - optional audio->quality->spectrogram->MQTT pipeline with sun weight … |
| `feat/camera-sahi-tiling` | c7e1889 | 2026-10-20 | w środku | `laptop-agent/` | edge: SAHI-style sliced inference for small drones (#52) |
| `feature/live-spectrogram` | 2e34da6 | 2026-10-20 | w środku | `laptop-agent/` | spectrogram: validate n_fft/hop, NaN-safe STFT, reset ring on clock step back, clean tmp o… |
| `feature/phone-mic-sensor-inventory` | c4b9b29 | 2026-10-20 | w środku | `laptop-agent/` | phone_mic: find WAV 'data' chunk instead of fixed 44-byte offset (#48) |
| `feature/rid-serial-audio-quality` | a2988dd | 2026-10-20 | w środku | `laptop-agent/` | rid_serial: strip mixed NUL/space padding, accept bytes; audio_quality: int32/uint8 scalin… |
| `feature/rtcp-sun-mqtt` | 1a0c6cf | 2026-10-20 | w środku | `laptop-agent/` | mqtt_alarm: no publish before connect, numpy-safe JSON, check publish rc; sun_glare: valid… |
| `feature/laptop-health` | e5da1de | 2026-10-20 | w środku | `laptop-agent/` | edge: laptop_health readers (CPU temp/throttling via LHM WMI, SMART via smartctl, battery … |
| `feat/acoustic-augment-ext` | aa4b11c | 2026-10-20 | w środku | `laptop-agent/` | edge: audiomentations-style test augmentations (#52) |
| `feat/acoustic-speech-gate` | 5ace059 | 2026-10-20 | w środku | `laptop-agent/` | speech gate: raise comb requirements under speech instead of blocking alarm |
| `feature/gnss-location-flac` | 69ddd0e | 2026-10-20 | w środku | `laptop-agent/` | edge: GNSS jamming/spoofing (UBX), L1 noise monitor, Windows location, FLAC evidence (#56 … |
| `feat/adsb-opensky-source` | 803341b | 2026-10-20 | w środku | `laptop-agent/` | edge: OpenSky REST as second ADS-B source for aircraft exclusion (#52, on #35) |
| `feat/acoustic-panns-stage` | f583517 | 2026-10-20 | w środku | `laptop-agent/` | edge/skyguard_acoustic: PANNs second-stage alarm verifier (#52) |
| `ideas-2-int` | 9fb0631 | 2026-10-20 | zastąpiona | zastąpiona – j.w. (`laptop-agent/edge-v5.8`) | Laptop agent: skyguard_acoustic wired + bundled, wideband sweep with signature table, OFDM… |
| `feat/rtl-tcp-client` | 431b7f7 | 2026-10-20 | w środku | `laptop-agent/` | feat(rf): rtl_tcp client -> spectrogram frames for FHSS detector (#43) |
| `feat/sniffle-ble-remoteid` | a603dc6 | 2026-10-20 | w środku | `laptop-agent/` | feat(rf): Sniffle BLE pcap ingest -> Remote ID (BLE5 Coded PHY) (#43) |
| `feat/camera-restream-config` | 6c5b0a4 | 2026-10-20 | w środku | `laptop-agent/` | feat(cam): go2rtc/MediaMTX restream config helper, no secrets (#43) |
| `feat/edge-skyguard-acoustic` | 93bece4 | 2026-10-20 | w środku | `laptop-agent/` | edge: skyguard_acoustic pre-alarm filter (propeller harmonic comb, wind/impulse rejection,… |
| `feat/dji-droneid-decoder` | 0b16a37 | 2026-10-20 | w środku | `laptop-agent/` | feat(rf): DJI DroneID flight-info decoder for demodulated frames (#43) |
| `ideas-1-fpv` | aa19e01 | 2026-10-20 | zastąpiona | zastąpiona – te same zmiany weszły wcześniej przez PR do unified/v1.1 i były potem rozwijane (`laptop-agent/edge-v5.8`) | Laptop agent: FPV analog video scan via SDR (items 1-4), acoustic gate hook (persistence +… |
| `feat/fhss-hop-detector` | 87b713c | 2026-10-20 | w środku | `laptop-agent/` | rf: FHSS / ExpressLRS hop-pattern detector (868/915 MHz) |
| `feature/sdr-esp32-selftest` | dadd39a | 2026-10-20 | w środku | `laptop-agent/` | feat(backend): SDR abstraction (SoapySDR, optional), ESP32 Remote ID serial reader, ODID s… |
| `feat/hackrf-sweep-ingest` | bcb6cb6 | 2026-10-20 | w środku | `laptop-agent/` | rf: hackrf_sweep ingest with robust noise floor -> rf_presence events |
| `feat/tak-cot-export` | b7cc51c | 2026-10-20 | w środku | `laptop-agent/` | rf: TAK Cursor-on-Target exporter (UDP multicast / TCP) |
| `feat/sigmf-writer` | efedf15 | 2026-10-20 | w środku | `laptop-agent/` | rf: SigMF metadata writer + validator for SDR IQ recordings |
| `feature/physics-models` | 52f9c55 | 2026-10-20 | w środku | `laptop-agent/` | physics: ISO 9613-1 acoustic range + bearing/TDOA CRLB uncertainty, GET /api/v0/physics/un… |
| `feature/remote-id-radar-screen` | bba95f3 | 2026-10-20 | w środku | `laptop-agent/` | feat(radar): RangeEstimator (log-distance path loss with shadowing band, haversine + beari… |
| `feature/system-watchdog` | 97909ec | 2026-10-20 | w środku | `laptop-agent/` | edge: laptop system watchdog (disk, recorder, camera, server, SKYGUARD-Laptop.exe) with ta… |
| `feature/gpu-directml` | 39d8397 | 2026-10-20 | w środku | `laptop-agent/` | edge: ONNX Runtime backend with DirectML GPU (AMD Radeon) and CPU fallback |
| `feature/laptop-exe` | 30c92c3 | 2026-10-20 | w środku | `laptop-agent/` | laptop-exe: exe + ffmpeg zip only (installer/Flutter owned elsewhere) |
| `feature/evidence-chain` | b3f1293 | 2026-10-20 | w środku | `laptop-agent/` | evidence: SHA-256 hash chain over sensor events and recordings, optional RFC 3161 anchor (… |
| `feature/adsb-exclusion` | 02019e0 | 2026-10-20 | w środku | `laptop-agent/` | adsb: receive-only dump1090/readsb/FLARM feed + fusion lowers score for detections matchin… |
| `test/drone-simulator` | d56eaa3 | 2026-10-20 | w środku | `laptop-agent/` | test: synthetic drone event simulator + scenarios (drone, birds, airplane) with pipeline t… |
| `feature/tracks` | ef1ad31 | 2026-10-20 | w środku | `laptop-agent/` | tracks: constant-velocity Kalman / IMM track fusion over Remote ID positions and triangula… |
| `ci/github-actions` | 088fb28 | 2026-10-20 | w środku | `laptop-agent/` | ci: pr-tests workflow (backend, edge, client dart tests) on PRs into unified/v1.1 |
| `feature/sensor-health` | b7587e4 | 2026-10-20 | w środku | `laptop-agent/` | health: sensor data-quality monitor GET /api/v0/health/sensors (brak odbioru / zawieszony … |
| `feature/ds-fusion` | ef20be4 | 2026-10-20 | w środku | `laptop-agent/` | fusion: Dempster-Shafer evidence mode (GET /api/v0/fusion?mode=ds), weighted mode kept; co… |
| `import/work-v5.8` | e2a847d | 2026-10-20 | w środku | `laptop-agent/` | work-v5.8: fix 11 failing tests (env.example placeholders, test env isolation, ffmpeg auto… |
| `feature/laptop-sensors` | ae96f5b | 2026-10-20 | w środku | `laptop-agent/` | fix(edge): BLE Remote ID scan in passive mode (no scan requests) |
| `feature/sensor-fusion-score` | e807d36 | 2026-10-20 | w środku | `laptop-agent/` | feat(api): server-side sensor fusion confidence score (GET /api/v0/fusion) |
| `feature/rf-control-link` | 56c80e2 | 2026-10-20 | w środku | `laptop-agent/` | feat(edge): receive-only drone control-link detection (rf_link) 433/868/915 MHz, 2.4/5.8 G… |
| `feature/rf-adaptive-cfar` | e282f45 | 2026-10-20 | w środku | `laptop-agent/` | feat(edge): shared adaptive CFAR noise-floor threshold for RF modules |
| `feature/krakensdr-df` | d242b62 | 2026-10-20 | w środku | `laptop-agent/` | feat(edge): receive-only KrakenSDR direction finding (rf_df) |
| `deploy/v1.1` | 3b8480f | 2026-10-20 | zastąpiona | zastąpiona – API sygnatur i zdarzeń w nowszej wersji jest w `laptop-agent/backend`; stara lista OUI (niesprawdzona) celowo pominięta | deploy v1.1: signatures API (unverified starter list), sensor-event aliases + rf_presence,… |
| `unified/desktop` | 824b429 | 2026-10-19 | w środku | `laptop-agent/` | 1.0.3: camera evidence snapshots (alarm + manual, real RTSP frame, added to evidence zip);… |
| `deploy/sensor-events` | 7031187 | 2026-10-19 | zastąpiona | zastąpiona – nowsza wersja tych samych plików (API zdarzeń, tokeny) jest już w `laptop-agent/backend` i `laptop-agent/deploy` | remove stray test-generated files |
| `hotfix/ingest-segment-drain` | d58147b | 2026-10-12 | w środku | `laptop-agent/` | fix(ingest): accept 12-digit (epoch) X-Skyguard-Sequence used by edge spool v2 |
| `feature/p5-remote-id` | a2ed128 | 2026-10-12 | w środku | `laptop-agent/` | feat(P5): Remote ID decoder, ingest endpoint, correlation and map layer |
| `feature/p1-harmonic-signatures` | 3149dc8 | 2026-10-12 | w środku | `laptop-agent/` | feat(P1): data-driven harmonic signature templates, comb score and f0/Doppler tracking |
| `feature/p10-adaptive-threshold` | 5e08d5e | 2026-10-12 | w środku | `laptop-agent/` | feat(P10): adaptive per-band background, CA-CFAR and wind detector |
| `feature/p3-no-rf-rule` | 065f001 | 2026-10-12 | w środku | `laptop-agent/` | feat(P3): NO_RF_LINK rule (acoustic/visual detection without RF/Remote ID) |
| `feature/p2-eval-harness` | 3574b30 | 2026-10-12 | w środku | `laptop-agent/` | feat(P2): session-grouped evaluation harness with hard negatives and Pd@FA |
| `feature/p12-map-reports` | c5b5f48 | 2026-10-12 | w środku | `laptop-agent/` | deploy: entrypoint only reads secret files (tolerate missing optional report_token) |
| `feature/ingest` | f46ef74 | 2026-10-11 | w środku | `laptop-agent/` | deploy: pin compose project name (keeps caddy cert volume) |
| `feature/watchdog-recorder` | 540f258 | 2026-10-10 | w środku | `laptop-agent/` | feat(watchdog): parse real recorder status.json (skyguard-continuous-1.0); disk state from… |
| `feature/real-schema` | 9da3d8e | 2026-10-10 | w środku | `laptop-agent/` | CI: build Windows installer and Android APK |
| `feature/evidence-media` | f636b31 | 2026-10-10 | w środku | `laptop-agent/` | feat(api): GET /api/v0/evidence/{id}/media with Range support and media-root confinement |
| `ci/build-installers` | 299f142 | 2026-10-10 | w środku | `laptop-agent/` | CI: build Windows installer and Android APK |
| `feature/mvp-read-slice` | 3f3b978 | 2026-10-10 | w środku | `laptop-agent/` | feat: real read-only MVP slice (backend API + Flutter client + watchdog) |
| `scaffold/initial-architecture` | b06835e | 2026-10-10 | w środku | `laptop-agent/` | scaffold: design-first architecture, Flutter client + read API skeleton |
