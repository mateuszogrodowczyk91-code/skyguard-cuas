# C-UAS „Wzorcowy Moduł Referencyjny” – stan na 01.11.2026

Plik `cuas_reference.py` to moduł dostarczony przez Mateusza (kondycjonowanie sygnału: declipping, HPF, HPSS, MMSE;
tracker BPF metodą HPS, liczba łopat, cepstrum, modulacja obwiedni; Doppler CPA; MVDR + Kalman; adapter PANNs/AST;
orkiestrator zwracający JSON). **Moduł badawczy – nie jest jeszcze podpięty ani do Centrum, ani do aplikacji na telefon.**

Uruchomienie (potrzebne `numpy` + `scipy`):

    python cuas_reference.py                       # syntetyczny przelot Phantoma 4 (autotest z pliku)
    python cuas_reference.py nagranie.wav 529 12   # 12 s od 529. sekundy, dowolne sr, mono/stereo PCM16
    python -m pytest -q test_cuas_reference.py     # 10 testów (2 na nagraniach z /workspace/evidence, jeśli są)

## Co poprawiono (logika obliczeń bez zmian, każde miejsce oznaczone `# FIX:`)
1. Linia 27: wklejone znaczniki `[span_24](start_span)…` w `from scipy.ndimage …` – plik w ogóle się nie uruchamiał (SyntaxError).
2. Krótkie nagranie (< ok. 9 s): okno przelotu 2,8–9,2 s było puste → `IndexError`. Teraz fit na całym śladzie, a przy < 6 ramkach bez fitu.
3. Fit Dopplera: jedna ramka z błędem oktawy (np. 300 Hz zamiast 150 Hz) dawała dla stojącego drona „165,7 Hz, 121 km/h, CPA 1 m”.
   Teraz ramki > 20 % od mediany są odrzucane i fit ma odporną funkcję straty (`soft_l1`). Dodane pole `Doppler_Fit` (1 = fit zbieżny).
4. Cisza cyfrowa / dropout w nagraniu: `log10(0)` → `math domain error` w liczeniu łopat.
5. Fazy lotu: średnia z pustego wycinka dawała `NaN` (niepoprawny JSON) – teraz `null`.
6. `detection_confidence` i `identified_model` były wypełniane także przy `uav_detected = false` (biały szum → „Shahed-136, 0,76”).
   Teraz 0,0 / `"none"`; surowy wynik katalogu jest w `catalog_match_confidence` i `candidate_ranking`.
7. „Dominujące piki” brały 6 najniższych częstotliwości zamiast 6 najsilniejszych; `find_peaks(distance=0)` mógł rzucić błąd.
8. Pasmo obwiedni 600–2500 Hz przekraczało Nyquista przy sr < 5 kHz.
9. Wejście: int16 / stereo / NaN są teraz akceptowane; za krótki klip (< 8192 próbek) daje czytelny `ValueError`. Dodano `analyze_wav()` i CLI.

Znane ograniczenia zostawione bez zmian (to są decyzje autora, nie literówki):
- `snr_post_dsp_db` = `snr_raw_est_db` + 9,21 dB zawsze (stały współczynnik 0,12) – `snr_gain_db` nie jest pomiarem.
- `uav_detected` = `snr_post_dsp_db > 5` i mediana SFM < 0,65 – reguła ręczna, nie wytrenowany detektor; SFM po odejmowaniu widma wychodzi ~0 prawie zawsze.
- Kinematyka (prędkość, CPA) liczy się zawsze, także dla szumu – ma sens tylko po wykryciu.
- Fazy lotu mają sztywne okna 0–2,5 / 2,5–9,5 / 9,5–koniec s z syntetycznego przykładu.
- Adapter PANNs/AST nie uruchamia żadnej sieci – zwraca tylko kształt spektrogramu i informację, czy torch/transformers są zainstalowane.

## Wyniki (01.11.2026, skrypty w `eval/`, surowe wyniki `eval/results_2026-11-01.json`)
Porównanie z SG-FUZJA (YAMNet + SG-NET + SG-HARM, `acoustic_fusion.py` z gałęzi roboczej Centrum 1.3.0, próg 0,925).
Uwaga: SG-FUZJA była trenowana m.in. na DADS, NEAPTIDE i ESC-50 (fold 1–4), więc na tych zbiorach ma przewagę – uczciwy dla niej jest ESC-50 fold 5.

| zbiór (8 kHz jak kamera) | C-UAS wykrywa | SG-FUZJA wykrywa |
|---|---|---|
| prawdziwe drony na zewnątrz, NEAPTIDE (196 klipów 2 s; 4 drony) | **0 %** | 63,8 % |
| te same drony, sklejone po 14–70 s (28 nagrań) | **0 / 28** (44,1 kHz: 1 / 28) | – |
| drony w pomieszczeniu (DroneAudioDataset, 100) | 6 % | 68 % |
| „nie dron” DroneAudioDataset (150) – fałszywe alarmy | 8,7 % | 1,3 % |
| ESC-50 (2000) – fałszywe alarmy | 11,1 % | 3,5 % |
| ESC-50 fold 5 (400) – fałszywe alarmy | 12,0 % | 4,5 % |

Najczęstsze fałszywe alarmy C-UAS: helikopter 33/40, odkurzacz 28/40, dzwony 28/40, budzik 25/40, pralka 21/40, samolot 19/40, silnik 17/40.

Nagrania kamery z 29.10 (22:30–23:26, okna 12 s co 6 s): C-UAS zgłosił 2 okna na 467 – 22:45:15 i 22:54:07 (w środku
szumu z 22:53:49), oba jako „Bayraktar TB2” przy BPF 75–85 Hz, czyli pomylił niski szum z napędem tłokowym. SG-FUZJA: 0 alarmów,
maksimum 0,947 w jednym oknie 23:18:34 (alarm wymaga 3 z 5 okien).

## Wniosek
- Jako **detektor** moduł w obecnej postaci nie nadaje się: na prawdziwych dronach praktycznie nic nie wykrywa, a fałszywych alarmów ma 3× więcej niż SG-FUZJA.
  Reguła SNR/SFM działa tylko na sztucznym, idealnie harmonicznym sygnale.
- Przydatne części to **opis drona po wykryciu**: tracker BPF (HPS), liczba łopat, prędkość i odległość najbliższego przejścia z Dopplera,
  oraz MVDR + Kalman, gdy będzie kilka mikrofonów (test na fali płaskiej z 30° trafia w ±3°).
- Integracja: Centrum (Python) może wywołać `UAVAcousticOrchestrator.analyze_stream()` na 12 s wokół alarmu SG-FUZJA i dopisać BPF/obroty/prędkość do zdarzenia.
  Telefon (Kotlin) wymaga przepisania na Kotlina (scipy nie ma na Androidzie) – sensownie tylko tracker BPF i fit Dopplera.
