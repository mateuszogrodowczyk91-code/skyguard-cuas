# DEKLARACJA ZGODNOŚCI UE I KARTA SYSTEMOWA EU AI ACT
## SYSTEM DETEKCJI I ŚLEDZENIA BEZZAŁOGOWYCH STATKÓW POWIETRZNYCH SKYGUARD C-UAS

**Numer Dokumentu:** SKY-EU-DOC-2026-001  
**Data Wystawienia:** 5 Listopada 2026 r.  
**Klasyfikacja Systemu:** System Sztucznej Inteligencji Wysokiego Ryzyka (EU AI Act, Artykuł 6 i Załącznik III) / Sprzęt Dual-Use (Rozporządzenie UE 2021/821)  

---

## 1. DANE PRODUCENTA I SYSTEMU

* **Producent:** SKYGUARD Defense & Autonomous Systems Sp. z o.o. / ISV Partner
* **Nazwa Handlowa Systemu:** SKYGUARD C-UAS Tactical & Enterprise
* **Identyfikator Wersji Oprogramowania:** v14.0 (Natywne wersje: `.EXE` dla Windows, `.APK` dla Android/Pixel, Engine `.NET 8` dla Linux/PS4)
* **Węzły Sprzętowe Systemu:**
  1. Mobilna Stacja Operacyjna (Google Pixel 10 Pro z procesorem Tensor NPU i bezpiecznym mikrokontrolerem Titan M2)
  2. Węzeł Przetwarzania Sygnałowego & Obliczeniowego (PlayStation 4 z systemem Linux, 8 GB GDDR5, SSD 240 GB)
  3. Zdalna Głowica Wizyjna (Kamera PTZ z dedykowanym agentem SD `tapo-ptz-smooth-tracker-v2.py`)
  4. Pasywny Odbiornik Uniwersalny RF/SDR (KrakenSDR DoA, Radar PLFM 10.5 GHz, Sonda Wi-Fi 2.4/5GHz OpenDroneID)
  5. Stacja Monitorowania Bazy (Komputer roboczy Windows z natywną aplikacją `.EXE`)

---

## 2. DEKLARACJA ZGODNOŚCI Z DYREKTYWAMI UNII EUROPEJSKIEJ

Niniejszym deklarujemy na wyłączną odpowiedzialność producenta, że system **SKYGUARD C-UAS** spełnia zasadnicze wymagania następujących dyrektyw i rozporządzeń Parlamentu Europejskiego i Rady:

### 2.1. Dyrektywa RED 2014/53/UE (Radio Equipment Directive)
* **Zastosowane normy:** ETSI EN 301 489-1 v2.2.3, ETSI EN 300 328 v2.2.2 (pasmo 2.4 GHz), ETSI EN 301 893 v2.1.1 (pasmo 5 GHz).
* **Ocena:** System wykorzystuje wyłącznie pasywny odbiornik radiowy bez emisji zakłócającej w pasmach ISM. Pasywny nasłuch i dekodowanie ramek Wi-Fi / Bluetooth OpenDroneID (Remote ID) spełniają wymogi bezobsługowej odbiorczej kompatybilności elektromagnetycznej.

### 2.2. Dyrektywa EMC 2014/30/UE (Electromagnetic Compatibility)
* **Zastosowane normy:** PN-EN 55032:2015, PN-EN 55035:2017.
* **Ocena:** Odbiornik uniwersalny zamknięty w pancernej obudowie z filtrami przepustowymi eliminuje emisję zakłóceń własnych, zapewniając odporność na zewnętrzne pola elektromagnetyczne w środowiskach przemysłowych i wojskowych.

### 2.3. Rozporządzenie (UE) 2021/821 (Kontrola Eksportu Towarów Podwójnego Zastosowania - Dual-Use)
* **Klasyfikacja:** Kategoria 6 (Czujniki i Lasery - 6A008 Systemy Radarowe) oraz Kategoria 5 Część 2 (Ochrona Informacji - 5A002 Systemy Kryptograficzne).
* **Zastosowanie:** Zgodność z procedurami dostawy dla podmiotów infrastruktury krytycznej, wojska i służb mundurowych państw członkowskich NATO/UE.

---

## 3. ZGODNOŚC Z ROZPORZĄDZENIEM EU AI ACT (2024/1689 / EU AI ACT)

System SKYGUARD wykorzystuje modele sztucznej inteligencji (YOLOv8/YOLOv10 oraz konwolucyjne sieci klasyfikacji widmowej RF). Zgodnie z przepisami EU AI Act system został poddany ocenie zgodności dla systemów wysokiego ryzyka:

### 3.1. Nadzór Człowieka (Human-in-the-Loop - Artykuł 14 EU AI Act)
* System **nie podejmuje automatycznych decyzji o kinetycznej lub neutralizującej reakcji**.
* Algorytmy AI na urządzeniu (Pixel Tensor NPU oraz PS4 GPU) pełnią funkcję pomocniczą (*Decision Support System*), prezentując rekomendowany kąt namierzenia PTZ i trajektorię celu.
* Ostateczna decyzja i zatwierdzenie celu należą każdorazowo do uprawnionego operatora w aplikacji mobilnej lub na stacji komputerowej.

### 3.2. Szyfrowany Rejestr Zdarzeń i Audytowalność (Artykuł 12 i 51 EU AI Act)
* Każda detekcja, klasyfikacja oraz interwencja operatora jest kryptograficznie opatrzona znacznikiem czasu i podpisana cyfrowo wewnątrz bezpiecznego mikrokontrolera **Titan M2 StrongBox** na telefonie Google Pixel 10 Pro.
* Logi nie mogą być zmodyfikowane ani usunięte bez uprawnień klucza głównego HSM.

### 3.3. Zarządzanie Danymi i Jakość Treningowa (Artykuł 10 EU AI Act)
* Zbiory danych użyte do uczenia modeli detekcji wizyjnej i radiowej zostały zweryfikowane pod kątem braku przekłamań (bias) oraz przetestowane w trudnych warunkach atmosferycznych (deszcz, mgła, noc, tło optyczne).

---

## 4. OŚWIADCZENIE BEZPIECZEŃSTWA DANYCH I TRANSMISJI (AIR-GAP SECURITY)

1. **Izolacja Chmurowa:** System posiada certyfikowany tryb pełnej izolacji sieciowej (*Air-Gap Mode*). Pomiędzy kamerą, konsolą PS4, stacją Windows a Pixelem cała komunikacja odbywa się przez szyfrowany tunel **WireGuard (ChaCha20-Poly1305)**.
2. **Obejście Aplikacji Producenta Kamery:** Kamera PTZ działa na autorskim oprogramowaniu `tapo-ptz-smooth-tracker-v2.py` na karcie MicroSD. Kamera jest całkowicie odcięta od serwerów zewnętrznych i nie wymaga połączenia z siecią Internet.

---

## 5. PODPIS I DEKLARACJA WYKONAWCZA

W imieniu **SKYGUARD Defense Systems**:

*Podpisano cyfrowo:* `[Titan M2 Cryptographic Signature Validated]`  
*Stanowisko:* Główny Architekt Systemów Autonomicznych & C-UAS  
*Miejsce i Data:* Warszawa / Bruksela, 5 Listopada 2026 r.  
