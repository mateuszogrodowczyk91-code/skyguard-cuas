# SKYGUARD

SKYGUARD to domowy system do wykrywania dronów nad posesją. Działa na kilku urządzeniach jednocześnie:

* **telefon (Pixel 10 Pro)** – słucha mikrofonem (akustyka: śmigła 80–500 Hz), patrzy kamerą, sprawdza GPS i Remote ID, a nagrania wysyła do chmury,
* **komputer PC (NBL, Windows)** – „Centrum”: zbiera zgłoszenia z telefonu, porównuje z samolotami z OpenSky (ADS-B), nagrywa ciągle z kamery i kopiuje nagrania na Dysk Google,
* **laptop / serwer** – agent z modułami SDR, Remote ID, fuzją czujników, raportami i panelem WWW.

Kolory statusu wszędzie te same: **OK** (zielony), **DO WERYFIKACJI** (żółty), **UWAGA** (czerwony).

> Ta gałąź (`release/skyguard-complete-2026-11-02`) zbiera w jednym miejscu najnowszy stan **wszystkich** części projektu na dzień 02.11.2026. Mapa starych gałęzi: [BRANCHES.md](BRANCHES.md).

## Status

Bieżący status prac i zadań: **[arkusz „SKYGUARD – status” (Google Sheets)](https://docs.google.com/spreadsheets/d/1f0oJ1TfMs2axHI4OndvZCF4QEW3s2hO-1h_DkuLCscE/edit)**

| Część | Katalog | Wersja | Testy (02.11.2026) | Stan |
|---|---|---|---|---|
| Aplikacja Android | `app/` | 1.7.2 | 310/310 OK | OK |
| Centrum PC (Windows) | `tools/windows/skyguard-centrum/` | 1.2.1 | 22/22 OK | OK |
| Moduł C-UAS (referencyjny) | `tools/acoustic/cuas/` | – | 10/10 OK | OK |
| Kopia na Dysk Google (NBL) | `tools/windows/drive-backup/` | upload.ps1 2.3.1 | – (PowerShell) | OK |
| Nagrywanie ciągłe kamery (NBL) | `tools/windows/recorder/` | 1.2-raw | – (PowerShell) | DO WERYFIKACJI – wersja odtworzona, NBL był offline |
| Diagnostyka NBL | `tools/windows/nbl-diagnostics/` | – | – | OK |
| Narzędzia akustyczne | `tools/acoustic/` | – | – | OK |
| Przekaźnik Drive (Apps Script) | `cloud-relay/` | – | – | OK |
| Agent laptopa (backend, edge, klient) | `laptop-agent/` | 0.3.0+ | backend 469 OK; edge-v5.8 431/432 (1 test czasowy – był już wcześniej); moduły edge OK | DO WERYFIKACJI |
| Stos serwerowy (chmura + edge) | `server-stack/` | – | 152 OK, 7 nieudanych (identycznie na gałęzi źródłowej `unify/skyguard`) | DO WERYFIKACJI |
| Stare prototypy | `legacy/` | – | nie uruchamiane | archiwum |
| Audyty i plan | `docs/audit/`, `docs/plan/` | – | – | – |

**Brakuje:** Centrum 1.3.0 – nie znaleziono tego kodu w żadnej gałęzi ani na serwerze roboczym; tu jest ostatnia znaleziona wersja 1.2.1.

## Części projektu

### Aplikacja Android – `app/`
Aplikacja na Pixel 10 Pro (Kotlin). Wykrywanie akustyczne (sieć + filtr wiatru), kamera, kontrola dryfu GPS, Remote ID, OpenSky, kolejka wysyłki do chmury, podwójne potwierdzenie przed nagrywaniem. Szczegóły budowania: [ANDROID_RELEASE.md](ANDROID_RELEASE.md), akustyka: [ACOUSTIC.md](ACOUSTIC.md).

**Nowość 1.7.2 – zakładka „Nagrywacz” (Czysty nagrywacz):** ręczne nagrywanie surowego dźwięku do analizy dronów.
* źródło `UNPROCESSED` (gdy telefon go nie ma: `VOICE_RECOGNITION`, potem `MIC`), 48 kHz, stereo gdy są dwa kanały, 24-bit (albo 16-bit) WAV,
* bez AGC, bez redukcji szumu, bez usuwania echa, bez filtra górnoprzepustowego – zapisuje dokładnie to, co daje mikrofon,
* na żywo: widmo 0–500 Hz (z zaznaczeniem częstotliwości szczytu) i miernik poziomu w kolorach OK / DO WERYFIKACJI / UWAGA (przesterowanie),
* start wymaga **dwóch** potwierdzeń, stop jednym dotknięciem,
* plik `Documents/SKYGUARD/audio/SKYGUARD_CLEAN_<data>.wav` trafia do kolejki wysyłki na Dysk **tylko przez Wi-Fi**; z telefonu znika dopiero po sprawdzeniu, że Dysk ma ten sam rozmiar i tę samą sumę MD5.

### Centrum PC – `tools/windows/skyguard-centrum/`
Serwer Python na komputerze NBL: panel WWW, odbiór zdarzeń z telefonu, OpenSky (`opensky.py`), eksport do ATAK/CoT (`tak.py`), sieć akustyczna (`acoustic_net.py`). Instalacja: `install.ps1`, opis: [README](tools/windows/skyguard-centrum/README.md).

### Skrypty NBL (Windows) – `tools/windows/`
* `drive-backup/` – `upload.ps1` 2.3.1: kopiowanie nagrań na Dysk Google (rclone), zadanie harmonogramu `install_task.ps1`, sprzątanie dysku.
* `recorder/` – `record.ps1` 1.2-raw: ciągłe nagrywanie kamery (ffmpeg) z **surowym** dźwiękiem (bez filtra górnoprzepustowego, bez wzmocnienia i limitera). Hasło kamery jest czytane z zaszyfrowanego pliku DPAPI na komputerze – nie ma go w repozytorium.
* `nbl-diagnostics/` – szybki stan systemu, dysku i wersji.

### Narzędzia akustyczne – `tools/acoustic/`
`cuas/` (moduł referencyjny C-UAS), `ensemble/` (zespół modeli – skrypty i wyniki), `training/`, `wind-eval/` (ocena filtra wiatru na prawdziwych nagraniach).

### Przekaźnik chmury – `cloud-relay/`
Google Apps Script, który przyjmuje nagrania z telefonu i zapisuje je na Dysku.

### Agent laptopa – `laptop-agent/`
Połączone 90 gałęzi (funkcje laptopa i edge) (SDR/KrakenSDR, HackRF, Remote ID BLE, DJI DroneID, fuzja czujników, ADS-B, łańcuch dowodowy, spektrogram na żywo, TAK/CoT, ntfy, UPS, watchdog…). `backend/` (FastAPI), `edge/` (moduły czujników), `edge-v5.8/`, `client/` (Flutter), `deploy/`.

### Stos serwerowy – `server-stack/`
Monorepo chmura + edge + panel WWW (z gałęzi `unify/skyguard`, bez kopii aplikacji Android, która jest w `app/`).

### Archiwum – `legacy/`
`react-native-21tech/` i `spell-engine/` – wczesne prototypy, tylko do wglądu.

## Budowanie i instalacja

### Android (APK do telefonu)
```bash
export JAVA_HOME=/ścieżka/do/jdk-17   ANDROID_HOME=/ścieżka/do/android-sdk
./gradlew testDebugUnitTest           # testy
./build-release.sh                    # testy + podpisany APK release
```
APK musi być podpisany **zawsze tym samym kluczem** (inaczej trzeba odinstalować aplikację i traci się dane). Klucz i hasła są poza repozytorium – patrz [ANDROID_RELEASE.md](ANDROID_RELEASE.md). Instalacja: skopiuj APK na telefon i otwórz (albo `adb install -r plik.apk`).

Dane logowania OpenSky są dołączane przy budowaniu z pliku poza repozytorium (`.opensky_credentials.json` – jest w `.gitignore`).

### Centrum PC (Windows)
```powershell
cd tools\windows\skyguard-centrum
powershell -ExecutionPolicy Bypass -File install.ps1
python -m pytest -q          # testy
```

### Skrypty NBL
Skopiuj `tools/windows/drive-backup` i `tools/windows/recorder` na komputer i uruchom `install_task.ps1` (kopie na Dysk). Hasło kamery zapisuje się raz lokalnie (DPAPI), nigdy w pliku w repozytorium.

### Agent laptopa / stos serwerowy (Python 3.11+)
```bash
cd laptop-agent/backend && python -m pytest -q
cd laptop-agent/edge-v5.8 && python -m pytest -q
cd server-stack && python -m pytest -q tests
```

## Bezpieczeństwo
W repozytorium nie ma haseł, kluczy ani danych logowania (sprawdzone skanem przed wysłaniem). `.gitignore` blokuje m.in. pliki `*cred*.txt`, `.env`, `*.jks`/`*.p12`/`*.pem`/`*.key`, `opensky_credentials.json`, `google-services.json` oraz nagrania (`*.wav`, `*.mkv`).
