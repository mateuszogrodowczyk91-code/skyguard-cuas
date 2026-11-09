# KARTA TECHNICZNO-HANDLOWA I SPECYFIKACJA PRZETARGOWA
## AUTONOMICZNY SYSTEM DETEKCJI I ŚLEDZENIA DRONÓW SKYGUARD C-UAS

**Przeznaczenie:** Ochrona obiektów infrastruktury krytycznej, imprez masowych, lotnisk, obiektów wojskowych i posiadłości VIP przed nieautoryzowanymi bezzałogowymi statkami powietrznymi (dronami).

---

## 1. KLUCZOWE ATUTY SYSTEMU (USP - UNIQUE SELLING PROPOSITIONS)

* **Ultra-Niski Koszt TCO (Total Cost of Ownership):** Wykorzystanie przełomowego przetwarzania brzegowego na dedykowanych układach akceleracji graficznej i sieciach NPU.
* **Pełny Tryb Terenowy (Field Standalone):** Smartfon **Google Pixel 10 Pro** na własnej baterii wykonuje 100% detekcji wizyjnej YOLOv10 (30 FPS) oraz steruje głowicą PTZ z opóźnieniem < 3 ms w przypadku braku zasilania w stacji głównej.
* **Głowica PTZ Śledząca "Z Gracją":** Unikalny algorytm tłumienia drgań i wykładniczej korekty prędkości silników krokowych eliminuje zrywanie klatek i szarpanie obiektywu podczas prowadzenia drona.
* **Całkowita Izolacja Chmurowa (Air-Gap):** Oprogramowanie na karcie MicroSD kamery odcina komunikację z serwerami chińskich producentów (TP-Link/Tapo) i przesyła czysty, szyfrowany strumień RTSP/UDP bezpośrednio do węzła taktycznego.
* **Architektura Wielo-Węzłowa:** Płynna współpraca silnika obliczeniowego na szybkimi dysku SSD (Linux/PS4), monitora podglądowego Windows (`.EXE`) oraz mobilnej aplikacji terenowej Android (`.APK`).

---

## 2. DANE TECHNICZNE I PARAMETRY OPERACYJNE

### 2.1. Zasięg i Metody Detekcji

| Metoda Detekcji | Zasięg Skuteczny | Czas Reakcji | Wymagane Środowisko |
| :--- | :--- | :--- | :--- |
| **RF / SDR Fingerprinting (KrakenSDR DoA)** | Do 3 000 m | < 100 ms | Pasywny nasłuch widma 2.4 / 5.8 GHz |
| **Wi-Fi / BT Remote ID (OpenDroneID)** | Do 1 200 m | < 50 ms | Sonda Wi-Fi (TC7200.U Monitor Mode) |
| **Wizyjna Detekcja AI (YOLO PTZ Camera)** | Do 800 m (optics) | < 30 ms | Płynne śledzenie "z gracją" na żywo |
| **Radar PLFM 10.5 GHz** | Do 1 500 m | < 200 ms | Pasywne/Aktywne skanowanie przestrzeni |

### 2.2. Specyfikacja Sprzętowa i Wymagania Zasilania

* **Węzeł Obliczeniowy (Linux/PS4):** Procesor x86-64 8 rdzeni, GPU AMD Radeon GCN (8 GB GDDR5 - przepustowość 176 GB/s), Szybki Dysk SSD 240 GB. Pobór mocy: ~90W.
* **Mobilny Węzeł Terenowy (Google Pixel 10 Pro):** Procesor Google Tensor NPU, mikrokontroler Titan M2, bateria 5050 mAh (do 8 godzin ciągłej detekcji AI w terenie bez zasilania zewnętrznego).
* **Zdalna Kamera PTZ:** Przetwornik Full HD / 4K, łączność Wi-Fi/Ethernet, zasilanie 12V DC lub PoE.
* **Stacja Podglądowa (Windows PC):** Dowolny komputer z systemem Windows 10/11, 12 GB RAM, aplikacja natywna `.EXE` (użycie CPU < 5%).

---

## 3. MODEL FORMALNO-PRAWNY I BIZNESOWY

1. **Model Dystrybucji:**
   * **Zestaw Taktyczny (Hardware + Software Package):** Pełny zestaw gotowy do pracy w terenie.
   * **Licencja SaaS / BYOL:** Subskrypcja na aktualizację bazy sygnatur i modeli AI z Google Cloud Marketplace.
2. **Certyfikacja i Zgodność:**
   * Zgodność z **EU AI Act** (Human-in-the-Loop, logi na czipie Titan M2).
   * Zgodność z normami **RED 2014/53/UE** i **EMC 2014/30/UE**.
   * Dopuszczenie eksportowe **Dual-Use (Rozporządzenie UE 2021/821)**.
