# SKYGUARD – podsumowanie repozytorium (stan na 02.11.2026)

## Liczby – dlaczego „ponad 120”, a PR-ów jest mniej

Numer na GitHubie jest wspólny dla **PR-ów i zgłoszeń (issues)**. Ostatni numer to **#107**, ale to nie znaczy 107 PR-ów:

| Co | Ile |
|---|---|
| Wszystkie numery (PR + zgłoszenia) | **107** (#1–#107) |
| PR-y razem | **86** |
| – otwarte | 75 |
| – scalone | 11 |
| – zamknięte bez scalania | 0 |
| Zgłoszenia (issues) razem | **21** (otwarte 17, zamknięte 4) |
| Gałęzie | **142** |
| – cały kod w wydaniu | 135 |
| – zastąpione nowszą wersją (kod też jest, w nowszej formie) | 6 |
| – gałąź wydania | 1 (`release/skyguard-complete-2026-11-02`) |
| Tagi | 45 (m.in. kopia zapasowa main: `backup/main-24c8d92-2026-11-02`) |

„Ponad 120” to najpewniej gałęzie (142) – tych jest najwięcej.

## Gdzie jest reszta

**Wszystko jest w jednej gałęzi `release/skyguard-complete-2026-11-02`** (PR #106 do main, czeka na Twoją decyzję). Sprawdzone commit po commicie (`git merge-base --is-ancestor` i `git cherry`):

* 75 otwartych PR-ów: każdy jest w całości w wydaniu.
* 11 scalonych PR-ów: kod jest w wydaniu (w tym #107 scalony dziś; 5 starszych scalono metodą squash, więc commity mają inne numery, ale zmiany są te same).
* Gałęzie bez PR-a, które nie są 1:1 w historii (`backup/work-v5.8`, `deploy/v1.1`, `deploy/sensor-events`, `ideas-1-fpv`, `ideas-2-int`, `ideas-3-speech`): ich pliki są w wydaniu w nowszej wersji (`server-stack/`, `laptop-agent/backend`, `laptop-agent/deploy`, `laptop-agent/edge-v5.8`). Szczegóły w `BRANCHES.md`.
* Nic nie zostało usunięte. Main nietknięty. Bez force push.

## Co doszło teraz (02.11.2026)

* Scalony **#107 – Realtime DSP**: pakiet Python `skyguard/` (DSP, radar FMCW + CFAR, kąt DoA, fuzja Dempster–Shafer, śledzenie, kolejka bez blokad, ZeroMQ, priorytety czasu rzeczywistego) oraz starter do Visual Studio / VS Code w `tools/realtime-dsp/`. Testy: 41/41 OK, demo: 1000 ramek, 0 zgubionych, opóźnienie mediana 2,4 ms.
* Ten plik `PODSUMOWANIE.md` i uzupełniony `BRANCHES.md` (3 nowe gałęzie).
* Jeszcze w drodze (nie ma go w repo w chwili pisania): analizator nagrań **Cyclops Ear** (`tools/ucho-cyklopa/`).

## Testy po scaleniu

| Część | Wynik |
|---|---|
| `skyguard/` (realtime DSP) | 41 OK |
| C-UAS `tools/acoustic/cuas/` | 10 OK |
| Centrum PC `tools/windows/skyguard-centrum/` | 22 OK |
| Aplikacja Android (v1.7.2, poprzedni przebieg; scalenie nie zmienia `app/`) | 310 OK |

## Wszystkie PR-y (86)

| PR | Tytuł | Stan | Gałąź → cel | Gdzie jest kod teraz |
|---|---|---|---|---|
| [#1](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/1) | Design-first scaffold: architecture + Flutter client & read-API skeleton | otwarty | `scaffold/initial-architecture` → `main` | cały kod w wydaniu → `laptop-agent/` |
| [#2](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/2) | MVP read slice: read-only API + Flutter client + watchdog | otwarty | `feature/mvp-read-slice` → `main` | cały kod w wydaniu → `laptop-agent/` |
| [#3](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/3) | Build Windows installer and Android APK | otwarty | `ci/build-installers` → `feature/mvp-read-slice` | cały kod w wydaniu → `laptop-agent/` |
| [#4](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/4) | Evidence media playback endpoint | otwarty | `feature/evidence-media` → `feature/mvp-read-slice` | cały kod w wydaniu → `laptop-agent/` |
| [#5](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/5) | Align backend with real database schema | otwarty | `feature/real-schema` → `feature/evidence-media` | cały kod w wydaniu → `laptop-agent/` |
| [#6](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/6) | feat(watchdog): alert log + real recorder status.json in /health/watchdog | otwarty | `feature/watchdog-recorder` → `feature/real-schema` | cały kod w wydaniu → `laptop-agent/` |
| [#7](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/7) | feat(ingest): /api/v1 write path for edge client (segments, live HLS, runtime) + deploy/ | otwarty | `feature/ingest` → `feature/watchdog-recorder` | cały kod w wydaniu → `laptop-agent/` |
| [#8](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/8) | feat(P12): node map, incident alerts, manual drone reports (GPS + compass bearing) | otwarty | `feature/p12-map-reports` → `feature/ingest` | cały kod w wydaniu → `laptop-agent/` |
| [#9](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/9) | feat(P2): honest evaluation harness (session split, hard negatives, Pd@FA) | otwarty | `feature/p2-eval-harness` → `feature/p12-map-reports` | cały kod w wydaniu → `laptop-agent/` |
| [#10](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/10) | feat(P3): NO_RF_LINK alert — acoustic without RF/Remote ID | otwarty | `feature/p3-no-rf-rule` → `feature/p2-eval-harness` | cały kod w wydaniu → `laptop-agent/` |
| [#11](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/11) | feat(P10): adaptive threshold (background calibration, CFAR, wind detector) | otwarty | `feature/p10-adaptive-threshold` → `feature/p3-no-rf-rule` | cały kod w wydaniu → `laptop-agent/` |
| [#12](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/12) | feat(P1): data-driven harmonic signature library + comb score + Doppler f0 tracking | otwarty | `feature/p1-harmonic-signatures` → `feature/p10-adaptive-threshold` | cały kod w wydaniu → `laptop-agent/` |
| [#13](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/13) | feat(P5): passive Remote ID — decoder, ingest, correlation, map layer | otwarty | `feature/p5-remote-id` → `feature/p1-harmonic-signatures` | cały kod w wydaniu → `laptop-agent/` |
| [#14](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/14) | SKYGUARD 1.0.0 — Unified Passive Multi-Sensor Drone Detection System | otwarty | `unified/v1` → `main` | cały kod w wydaniu → `laptop-agent/` |
| [#15](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/15) | Receive-only KrakenSDR direction finding (rf_df) | otwarty | `feature/krakensdr-df` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#16](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/16) | Shared adaptive CFAR noise-floor threshold for RF modules | otwarty | `feature/rf-adaptive-cfar` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#17](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/17) | Receive-only drone control-link detection (rf_link) | otwarty | `feature/rf-control-link` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#18](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/18) | Server-side sensor fusion confidence score | otwarty | `feature/sensor-fusion-score` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#19](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/19) | Laptop sensor agent (receive-only): acoustic, Wi-Fi drone/RID, BLE RID | scalony | `feature/laptop-sensors` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#20](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/20) | Import: laptop SKYGUARD work-v5.8 (source snapshot) | otwarty | `import/work-v5.8` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#21](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/21) | Fusion: Dempster-Shafer evidence mode | otwarty | `feature/ds-fusion` → `feature/sensor-fusion-score` | cały kod w wydaniu → `laptop-agent/` |
| [#22](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/22) | Sensor data-quality monitor: GET /api/v0/health/sensors | otwarty | `feature/sensor-health` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#23](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/23) | CI: test gate for PRs into unified/v1.1 | otwarty | `ci/github-actions` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#30](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/30) | Track fusion: Kalman CV / IMM at GET /api/v0/tracks | otwarty | `feature/tracks` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#32](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/32) | Test: synthetic drone event simulator + pipeline tests | otwarty | `test/drone-simulator` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#35](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/35) | ADS-B/FLARM exclusion: edge feed + fusion penalty | otwarty | `feature/adsb-exclusion` → `feature/sensor-fusion-score` | cały kod w wydaniu → `laptop-agent/` |
| [#36](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/36) | Laptop: SKYGUARD-Laptop.exe (PyInstaller onefile) + release workflow | scalony | `feature/laptop-exe` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#37](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/37) | Dekoder Open Drone ID (ASTM F3411, Python) + ekran Radar na Windows | otwarty | `feature/remote-id-radar-screen` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#39](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/39) | Evidence integrity: SHA-256 hash chain + optional RFC 3161 | otwarty | `feature/evidence-chain` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#42](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/42) | Edge: liczenie modeli ONNX na GPU (AMD Radeon, DirectML) z fallbackiem na CPU | otwarty | `feature/gpu-directml` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#44](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/44) | Edge: strażnik systemu na laptopie (dysk, rejestrator, kamera, serwer, SKYGUARD-Laptop.exe) | otwarty | `feature/system-watchdog` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#45](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/45) | Windows installer: SKYGUARD-Laptop agent + radar app (Inno Setup, CI-built) | otwarty | `feature/windows-installer` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#46](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/46) | Physics models: acoustic range (ISO 9613-1) + bearing/TDOA uncertainty (CRLB) | otwarty | `feature/physics-models` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#47](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/47) | rf: SigMF metadata writer + validator for SDR IQ recordings | otwarty | `feat/sigmf-writer` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#49](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/49) | rf: TAK Cursor-on-Target exporter (UDP multicast / TCP) | otwarty | `feat/tak-cot-export` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#50](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/50) | rf: hackrf_sweep ingest with robust noise floor -> rf_presence events | otwarty | `feat/hackrf-sweep-ingest` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#51](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/51) | Telefon jako drugi mikrofon, autotest źródeł i inwentarz czujników (#48: 1, 2, 6) | otwarty | `feature/phone-mic-sensor-inventory` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#53](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/53) | SDR (SoapySDR), czujnik Remote ID na ESP32 i autotest ramek ODID | otwarty | `feature/sdr-esp32-selftest` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#54](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/54) | rf: FHSS / ExpressLRS hop-pattern detector (868/915 MHz) | scalony | `feat/fhss-hop-detector` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#55](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/55) | Spektrogram na żywo (wodospad) – STFT dBFS + endpointy (#48: 5) | otwarty | `feature/live-spectrogram` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#57](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/57) | Laptop: FPV video scan (SDR) + acoustic gate + NBL fixes (#26 items 1-4) | scalony | `ideas-1-fpv` → `unified/v1.1` | kod w wydaniu przez nowszą wersję → zastąpiona – te same zmiany weszły wcześniej przez PR do unified/v1.1 i były potem rozwijane (`laptop-agent/edge-v5.8`) |
| [#58](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/58) | Remote ID: numer seryjny CTA-2063-A i lista dozwolonych dronów, monitor jakości audio kamery (#56: 1, 2, 3) | otwarty | `feature/rid-serial-audio-quality` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#59](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/59) | edge: skyguard_acoustic pre-alarm filter | scalony | `feat/edge-skyguard-acoustic` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#60](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/60) | feat(rf): DJI DroneID decoder for demodulated frames (#43) | otwarty | `feat/dji-droneid-decoder` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#61](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/61) | feat(cam): go2rtc/MediaMTX restream config helper (#43) | otwarty | `feat/camera-restream-config` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#62](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/62) | feat(rf): Sniffle BLE ingest -> Remote ID, BLE5 long range (#43) | otwarty | `feat/sniffle-ble-remoteid` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#63](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/63) | feat(rf): rtl_tcp client -> spectrogram frames (#43) | otwarty | `feat/rtl-tcp-client` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#64](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/64) | Laptop: skyguard_acoustic in exe + wideband sweep, OFDM, IQ export, hooks (#26 items 5,7,17,18) | scalony | `ideas-2-int` → `unified/v1.1` | kod w wydaniu przez nowszą wersję → zastąpiona – j.w. (`laptop-agent/edge-v5.8`) |
| [#65](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/65) | PANNs second-stage verifier after skyguard_acoustic gate (#52) | otwarty | `feat/acoustic-panns-stage` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#66](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/66) | Pozycje 4, 5 i 9 z #56: zegar RTCP, słońce w kadrze, alarm MQTT dla Home Assistant | otwarty | `feature/rtcp-sun-mqtt` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#68](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/68) | OpenSky as second ADS-B source for aircraft exclusion (#52, on #35) | otwarty | `feat/adsb-opensky-source` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#70](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/70) | edge/skyguard_acoustic: Silero VAD speech gate (on top of #59) | otwarty | `feat/acoustic-speech-gate` → `feat/edge-skyguard-acoustic` | cały kod w wydaniu → `laptop-agent/` |
| [#71](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/71) | edge: wykrywanie zagłuszania GPS, szum L1, pozycja z Windows, dowody FLAC (#56: 6, 7, 8, 10) | otwarty | `feature/gnss-location-flac` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#72](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/72) | edge: audiomentations-style test augmentations (#52) | otwarty | `feat/acoustic-augment-ext` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#73](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/73) | edge: zdrowie laptopa — temperatura CPU, SMART, bateria 80%, surowy mikrofon WASAPI (#38) | otwarty | `feature/laptop-health` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#75](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/75) | edge: SAHI-style sliced inference for small drones (#52) | otwarty | `feat/camera-sahi-tiling` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#77](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/77) | edge: audio_pipeline – integracja #51 #55 #58 #66 + test E2E + raport | otwarty | `feature/audio-pipeline` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#78](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/78) | CI: parallel Nuitka build of SKYGUARD-Laptop.exe (+optional signing via #45) | otwarty | `feature/nuitka-ci` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#79](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/79) | edge: maska nieba, blokada uśpienia, kontrola USB selective suspend (#76: 1, 2, 3) | scalony | `feature/sky-mask-keepawake-usb` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#80](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/80) | edge: Frigate-style motion masks and detection zones (#52) | otwarty | `feat/camera-zone-masks` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#81](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/81) | Laptop: optional speech gate after acoustic gate (#70 interface) | scalony | `ideas-3-speech` → `unified/v1.1` | kod w wydaniu przez nowszą wersję → zastąpiona – j.w. (`laptop-agent/edge-v5.8`) |
| [#82](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/82) | tools: Anti-UAV benchmark eval harness, no data committed (#52) | otwarty | `feat/antiuav-eval-harness` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#83](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/83) | edge: RTL-SDR ppm calibration (Część #38) | otwarty | `feat/sdr-ppm-calibration` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#84](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/84) | UPS monitoring via NUT (Część #38/5.5) | otwarty | `feature/ups-nut` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#85](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/85) | edge: ntfy push notifications for alarms (#52) | otwarty | `feat/ntfy-push` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#86](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/86) | edge: Windows Firewall confinement (Część #38) | otwarty | `feat/windows-firewall-confinement` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#87](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/87) | edge: skyguard_health BLE rate + NTP clock | otwarty | `feat/edge-skyguard-health` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#88](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/88) | Testy: koniec kolizji portów i /var/tmp (4 padające testy na unified/v1.1) | otwarty | `fix/fix-test-port-collisions` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#89](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/89) | edge: M-of-N detection confirmation (Część #38/6.1) | otwarty | `feature/lingxi-s6-1-m-of-n-confirm` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#90](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/90) | edge: cepstral rotor f0 estimator (Część #38/6.2) | otwarty | `feature/lingxi-s6-2-cepstrum-f0` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#91](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/91) | edge: mains hum 50 Hz detect + notch (Część #38/6.3) | otwarty | `feature/lingxi-s6-3-mains-hum-notch` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#92](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/92) | edge: agent config validator (Część #38/6.4) | otwarty | `feature/lingxi-s6-4-config-validator` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#93](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/93) | edge: circular bearing smoother (0/360 wrap) (Część #38/6.5) | otwarty | `feature/lingxi-s6-5-bearing-smoother` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#94](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/94) | edge: GeoJSON (RFC 7946) + CSV export (Część #38/6.6) | otwarty | `feature/lingxi-s6-6-geojson-export` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#95](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/95) | edge: alarm flood limiter (cooldown + token bucket) (Część #38/6.7) | otwarty | `feature/lingxi-s6-7-alarm-rate-limiter` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#96](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/96) | edge: spectral flatness + kurtosis features (Część #38/6.8) | otwarty | `feature/lingxi-s6-8-spectral-shape` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#97](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/97) | edge: 1/3-octave band levels (IEC 61260-1) (Część #38/6.9) | otwarty | `feature/lingxi-s6-9-third-octave` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#98](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/98) | edge: sound-card sample-rate drift + gap detector (Część #38/6.10) | otwarty | `feature/lingxi-s6-10-sample-rate-drift` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#99](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/99) | feat(client): Integracja Google Camera (GCam) ze SkyGuard | scalony | `feat/gcam-integration` → `unified/v1` | kod w wydaniu (te same zmiany, inne commity – squash) → `laptop-agent/` |
| [#100](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/100) | feat(spell): SPELL-Engine Multi-Modal Sync & Airspace Threat Defense | otwarty | `feature/spell-engine` → `main` | cały kod w wydaniu → `legacy/spell-engine/` |
| [#101](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/101) | edge: acoustic f0 tracker + DOA + wind | otwarty | `feat/acoustic-f0-doa` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#102](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/102) | fix(wifi): poprawione prefiksy MAC producentów dronów (Wireshark manuf / IEEE) | otwarty | `fix/drone-oui-registry` → `unified/v1.1` | cały kod w wydaniu → `laptop-agent/` |
| [#103](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/103) | Laptop v0.3.0: optional hooks (#87, #101, #84, #75, #80, #85, #77, #71) + #79 keep-awake | scalony | `fix/v030-optional-hooks` → `unified/v1.1` | kod w wydaniu (te same zmiany, inne commity – squash) → `laptop-agent/` |
| [#105](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/105) | feat: SkyGuard React Native — 21 real technologies, full port | otwarty | `react-native-skyguard-21tech` → `main` | cały kod w wydaniu → `legacy/react-native-21tech/` |
| [#106](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/106) | SKYGUARD – kompletne repozytorium (stan na 02.11.2026) | otwarty | `release/skyguard-complete-2026-11-02` → `main` | to jest PR wydania |
| [#107](https://github.com/mateuszogrodowczyk91-code/skyguard/pull/107) | Realtime DSP: zunifikowany pakiet skyguard + starter Visual Studio | scalony | `feature/realtime-dsp-stack` → `release/skyguard-complete-2026-11-02` | scalony teraz do wydania → `skyguard/`, `tools/realtime-dsp/` |

## Zgłoszenia (issues) (21)

| Nr | Tytuł | Stan |
|---|---|---|
| [#24](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/24) | Telefon (Motorola): czujniki SkyGuard | zamknięty |
| [#25](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/25) | Telefon (Motorola): czujniki i praca w tle dla SKYGUARD | otwarty |
| [#26](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/26) | Serwer/radio/fuzja: 10 ulepszeń | otwarty |
| [#27](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/27) | Aplikacja: Remote ID, radar i funkcje telefonu | otwarty |
| [#28](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/28) | 10 ulepszeń SKYGUARD (lista zadań) | otwarty |
| [#29](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/29) | Aplikacja SKYGUARD: lista funkcji (Remote ID, radar, AI, mapa, raporty) | zamknięty |
| [#31](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/31) | 10 ulepszeń niezawodności SKYGUARD (lista zadań) | otwarty |
| [#33](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/33) | Aplikacja: kolejne 10 (GitHub/XDA/TrebleDroid) | otwarty |
| [#34](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/34) | 10 ROM-ów dla moto g60s (lisbon) – lista zadań | otwarty |
| [#38](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/38) | Windows .exe: 10 pomysłów (lista zadań) | otwarty |
| [#40](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/40) | 10 pomysłów na laptopa | otwarty |
| [#41](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/41) | Laptop: 10 pomysłów | zamknięty |
| [#43](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/43) | pomysły pod laptopa (exe) | otwarty |
| [#48](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/48) | 10 pomysłów z XDA / TrebleDroid / 4PDA | otwarty |
| [#52](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/52) | kolejne 10 pomysłów (laptop) | otwarty |
| [#56](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/56) | kolejne 10 pomysłów (laptop) | otwarty |
| [#67](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/67) | Czwarta dziesiątka pomysłów (laptop) | otwarty |
| [#69](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/69) | 3. dziesiątka pomysłów (laptop) | otwarty |
| [#74](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/74) | 📋 Spis wszystkich list i właścicieli (porządek) | otwarty |
| [#76](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/76) | trzecia dziesiątka pomysłów (laptop) | zamknięty |
| [#104](https://github.com/mateuszogrodowczyk91-code/skyguard/issues/104) | ok | otwarty |
