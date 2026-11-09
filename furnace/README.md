# PROJECT FURNACE / SKYGUARD C4ISR v8.0 PRODUCTION RELEASE

System obrony przeciwlotniczej bardzo krótkiego zasięgu (VSHORAD / C-UAS) opartej na 4-domenowej fuzji sensorycznej (PCL Radar, SIGINT/RemoteID, Akustyka MEMS, EO/IR Wizja) z opcjonalnym API wizyjnym oraz integracją taktyczną Cursor-on-Target (CoT XML).

## 🚀 Szybki Start (One-Command Launch)

### 1. Linux / PS4 Linux / Termux Android:
```bash
cd 00_Master_Launcher
./start_all.sh
```

### 2. Uruchomienie testów jednostkowych i walidacyjnych:
```bash
python3 06_Testy_Automatyczne/test_production_engine.py
```

### 3. Kompilacja aplikacji mobilnej Android (.APK):
```bash
cd 01_Teren_Pixel/Android_App
dotnet publish -f net8.0-android -c Release -p:AndroidPackageFormat=apk
```

### 4. Kompilacja interfejsu taktycznego Windows HUD (.NET 8):
```powershell
._Gora_Windows_HUDuild_hud.ps1
```

## 📐 Struktura Strefowa Systemu:
- **`00_Master_Launcher/`**: Uruchamiacz jednopoleceniowy, silnik produkcyjny v7 oraz moduł symulacji beki v6.
- **`01_Teren_Pixel/`**: Śledzenie optyczne YOLOv8, kontrola PTZ Tapo oraz kompletny projekt .NET 8 Android `com.skyguard.tactical`.
- **`02_Blackbox_PS4_Linux/`**: Serwer pętli szeregowej USB, wyliczanie ECA-B PCL, korelacji CAF, filtracji ARUKF oraz GCC-PHAT.
- **`03_Gora_Windows_HUD/`**: Skrypty kompilacji interfejsu C# .NET 8 i wdrożenia ADB.
- **`04_Certyfikacje_i_Dokumenty/`**: Deklaracje zgodności z EU AI Act (Titan M2 SHA-256), karty techniczne i licencje UKE.
- **`05_Deploy_i_CI_CD/`**: Skrypty CI/CD GitHub Actions oraz usługi `systemd`.
- **`06_Testy_Automatyczne/`**: Zestaw testów automatycznych `unittest` weryfikujący wszystkie 4 algorytmy.
