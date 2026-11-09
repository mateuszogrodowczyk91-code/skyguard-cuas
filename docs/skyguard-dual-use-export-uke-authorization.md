# DOKUMENTACJA KONCESYJNA I ZGŁOSZENIE UKE / DUAL-USE EXPORT
## SYSTEM BEZZAŁOGOWY SKYGUARD C-UAS

**Kategoria Prawna:** Ustawa o obrocie z zagranicą towarami, technologiami i usługami o znaczeniu strategicznym dla bezpieczeństwa państwa / Rozporządzenie UE 2021/821  
**Organ Nadzorczy:** Urząd Komunikacji Elektronicznej (UKE) / Ministerstwo Rozwoju i Technologii / MSWiA  

---

## 1. ZGŁOSZENIE SYSTEMU PASYWNEGO MONITOROWANIA WIDMA RADIOWEGO (UKE)

### 1.1. Charakterystyka Częstotliwościowa i Odbiorcza
System SKYGUARD wykorzystuje **wyłącznie metody pasywnej detekcji radiowej i optycznej**. System nie emituje fal radiowych o charakterze zakłócającym (brak aktywnego zagłuszania / jammera w wersji podstawowej):

* **Pasmo ISM 2.4 GHz (2400 MHz – 2483.5 MHz):** Pasywny nasłuch sygnałów sterowania FPV, sygnałów telemetrycznych oraz transmisji ramek Wi-Fi / Bluetooth (OpenDroneID / Remote ID).
* **Pasmo ISM 5.8 GHz (5725 MHz – 5875 MHz):** Pasywna analiza widmowa cyfrowych i analogowych transmisji wideo z drona (FFT na procesorze PS4 z tunerów SDR).
* **Pasmo Radiolokacyjne 10.5 GHz (PLFM Radar):** Pasywny/Odbiorczy odbiór fal ciągłych modulowanych liniowo z małą mocą szczytową w bezpiecznych normach promieniowania cywilnego.

### 1.2. Deklaracja Zgodności Prawo Telekomunikacyjne
Zgodnie z Artykułem 144 Ustawy Prawo Telekomunikacyjne, używanie urządzeń odbiorczych nie wymaga posiadania pozwolenia radiowego. Przechwytywanie i dekodowanie publicznie nadawanych ramek identyfikacyjnych drona (Remote ID) odbywa się zgodnie z rozporządzeniem wykonawczym Komisji (UE) 2019/945.

---

## 2. KLASYFIKACJA KONTROLI EKSPORTU TOWARÓW PODWÓJNEGO ZASTOSOWANIA (DUAL-USE)

System SKYGUARD C-UAS podlega pod listę towarów podwójnego zastosowania Unii Europejskiej w następujących pozycjach:

| Kod Towaru (Dual-Use) | Opis Techniczny Systemu SKYGUARD | Klasa Zezwolenia |
| :--- | :--- | :--- |
| **6A008** | Systemy radarowe i czujniki mikrofalowe z obróbką sygnału cyfrowego FFT. | Zezwolenie Ogólne UE (EU001) / Krajowe |
| **5A002** | Sprzęt zabezpieczenia informacji wykorzystujący symetryczne algorytmy kryptograficzne (WireGuard ChaCha20, Titan M2). | Zezwolenie Komercyjne (ISV) |
| **6A002** | Czujniki optyczne i kamery PTZ z automatycznym śledzeniem obiektów (Śledzenie "z gracją" na karcie SD). | Zezwolenie Dystrybucyjne |

---

## 3. WAŻNOŚĆ I PROCEDURY BEZPIECZEŃSTWA

1. **Procedura End-User Certificate (EUC):** Wszystkie komercyjne i wojskowe dostawy zestawu taktycznego SKYGUARD wymagają podpisania Deklaracji Użytkownika Końcowego zapobiegającej nieautoryzowanej reexportacji poza obszar NATO/UE.
2. **Klucze Bezpieczeństwa:** W przypadku wykrycia nieautoryzowanej próby otwarcia obudowy odbiornika uniwersalnego lub wyciągnięcia dysku SSD z konsoli PS4, bezpieczny mikrokontroler **Titan M2** unieważnia cyfrowe klucze szyfrujące, uniemożliwiając inżynierię wsteczną oprogramowania.
