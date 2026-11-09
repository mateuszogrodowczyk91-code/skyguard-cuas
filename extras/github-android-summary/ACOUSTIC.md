# SKYGUARD – akustyka (dźwięk drona): gdzie co jest

Jeden model, **SG-NET v1** (`sg_drone_net_v1.sgan`, 143 KB, SHA-256 `d3e942c4…adf6`), działa
w obu programach z tymi samymi cechami wejściowymi, bez dodatkowych bibliotek:

| Urządzenie | Program | Kod | Model |
|---|---|---|---|
| Telefon (Pixel) | SKYGUARD Android ≥ 1.3.2 | `app/src/main/java/com/skyguard/radar/sensors/DroneNetClassifier.kt` (inferencja + decymacja 48→8 kHz), `AcousticFusion.kt` (decyzja), `AcousticMonitor.kt` (mikrofon w usłudze w tle) | `app/src/main/assets/sg_drone_net_v1.sgan` |
| Komputer | SKYGUARD Centrum ≥ 1.1.0 | `tools/windows/skyguard-centrum/` (gałąź feature/acoustic-net) `acoustic_net.py` (inferencja: numpy jeśli jest, inaczej czysty Python), `acoustic_pc.py` (analiza dźwięku z nagrań kamery) | `tools/windows/skyguard-centrum/` (gałąź feature/acoustic-net) `models/sg_drone_net_v1.sgan` |
| Trening | – | `tools/acoustic/training/` (`prep.py`, `sgnet.py`, `train.py`, `evalexp.py`) | wynik: `metrics.json` |

## Jak działa
- Cechy: 8 kHz mono, okno 0,5 s co 0,25 s, Hann 512 / hop 128 (28 ramek), 40 pasm mel 50–4000 Hz,
  10·log10 mocy minus średnia okna (niezależne od głośności). Mała sieć CNN 16/32/64 kanały, ~25 tys. parametrów.
  8 kHz celowo: kamera nagrywa dźwięk G.711 8 kHz, więc ten sam model działa na kamerze i telefonie.
- **Telefon:** analizator harmonicznych (DSP, `DroneAcousticAnalyzer` + `AcousticGate`) i SG-NET głosują razem
  (`AcousticFusion`): DSP+NET (DSP potwierdza, SG-NET ≥ 2 z 6 okien), albo sam NET (≥ 4 z 6 okien i poziom ≥ −58 dBFS).
  Gdy DSP „widzi” drona, a SG-NET nie, alarm jest blokowany (to były fałszywe alarmy od brumu sieci z v1.2.x).
  Zdarzenie dostaje `ml_prob`, `ml_votes`, `decided_by`, `confidence` i idzie dalej jak dotąd (dziennik, Drive, ADS-B z OpenSky).
- **Komputer:** co minutę `acoustic_pc` dekoduje ffmpeg-iem tylko NOWY dźwięk z `SKYGUARD_Nagrania\<data>\SG_*.mkv`
  (tylko odczyt, niski priorytet), ocenia okna SG-NET, wykrycie = ≥ 4 z 6 okien (~1,5 s) powyżej progu, max 1 zdarzenie/min/plik.
  Zdarzenia: `data\acoustic\skyguard_events_pc_acoustic_RRRRMMDD.jsonl` → zakładka Zdarzenia (kolumna Pewność),
  kopia na Drive `SKYGUARD/pc/acoustic`. Świeże wykrycie jest od razu sprawdzane w OpenSky
  („znany samolot: …” → zagrożenie LOW, albo „brak ADS-B — podejrzane”). Stan w zakładce Kamera i nagrania → Akustyka.
  Przy pierwszym starcie analizuje tylko ostatnie 6 h nagrań. Nic nie jest usuwane.

## Dane treningowe (pobrane 29.10.2026 na serwer roboczy, `/workspace/acoustic-data`, 8,6 GB)
- **DADS** – Drone Audio Detection Samples (Hugging Face `geronimobasso/drone-audio-detection-samples`, MIT), 6,4 GB,
  180 320 nagrań (163 591 z dronem, 16 729 bez). Zbiór łączy kilka publicznych repozytoriów nagrań dronów.
- **ESC-50** (dźwięki otoczenia, w tym silnik, piła, helikopter, samolot, deszcz, wiatr) – 1,5 GB, tylko jako „nie dron”.
- **LibriSpeech dev-clean** (mowa) – 0,7 GB, „nie dron”.
- Syntetyczne: brum sieci 50/60/100/120 Hz z harmonicznymi, wiatr (szum brązowy z porywami), kodek G.711 µ-law.
Podział bez przecieków: drony z innych części DADS (shardy 35–38) w teście, ESC-50 fold 5, inni mówcy.

## Wyniki na danych testowych, których model nie widział (okno 0,5 s, próg 0,655)
- Wykrywalność (recall) drona: **99.3%** (8000 okien), fałszywe alarmy (FPR): **0.66%** okien (16356 okien bez drona); dokładność zbalansowana 99.3%.
- FPR wg źródła: DADS bez drona 0.83%, ESC-50 0.25%, mowa 0.00%.
- Sam brum sieci: 0.0% fałszywych, sam wiatr: 0.0%, mowa + brum: 0.0%.
- Dron zagłuszony (wykrywalność): brum 10/5/0/−5 dB: 99%/98%/95%/77%; wiatr: 99%/99%/99%/99%; hałas ESC-50 (ruch uliczny, silniki…): 99%/98%/96%/70%.
- Po kodeku kamery G.711 µ-law: 99.2%.
Uczciwie: to wyniki na nagraniach z publicznych zbiorów i na mieszankach. Nie było jeszcze testu na prawdziwym dronie
nagranym kamerą/telefonem użytkownika. Najczęstsze pomyłki: piła łańcuchowa, otwieranie puszki, klakson (~3–4% okien;
głosowanie 4 z 6 okien dodatkowo je tłumi).

## Starszy kod akustyczny (zostaje, nic nie usunięto)
- GitHub `unified/v1` i kopie `edge-v5.8/edge/` – demon edge z NBL (`C:\Users\Public\skyguard_unified_edge.py`):
  `dads_crnn.py` + `ml_drone/drone_classifier_aug_{mixed,pw10}.pt` (CRNN 1,49 mln parametrów, 2×8,5 MB, wymaga PyTorch+torchaudio –
  dlatego nie trafił do Centrum ani telefonu). SG-NET to jego lekki następca trenowany na tym samym DADS.
- Gałęzie `feat/acoustic-augment-ext`, `feat/acoustic-f0-doa`, `feat/acoustic-panns-stage`, `feat/acoustic-speech-gate`,
  `feat/edge-skyguard-acoustic` – eksperymenty (augmentacja, f0/DOA, PANNs, bramka mowy) dla demona edge.
- `skyguard_acoustic` (bramka DSP numpy/scipy, testy tylko syntetyczne) – moduł pomocniczy, zastąpiony przez `AcousticGate.kt` + SG-NET.

## Ponowny trening
```
python -m venv v && v/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu && v/bin/pip install numpy scipy pyarrow soundfile
python prep.py && python train.py 14 && python evalexp.py   # ~10 min na 8 rdzeniach CPU
```
Potem skopiować `sg_drone_net_v1.sgan` do obu miejsc z tabeli i `parity.bin` jako `sgnet_parity.bin` (testy porównują wynik z PyTorch).

## WIATR – wykrywanie wiatru na mikrofonie (Android v1.6.7)
`app/src/main/java/com/skyguard/radar/sensors/WindNoiseDetector.kt` (czysty Kotlin, testy `WindNoiseTest`).
- Co 0,5 s ocenia ostatnią 1 s (8 kHz): **stereo** (dwa różne mikrofony) – koherencja MSC 50–300 Hz
  (wiatr na otworze mikrofonu jest niespójny między mikrofonami, prawdziwy dźwięk, np. dron, jest spójny);
  **mono** – stosunek energii < 200 Hz do 200–2000 Hz, wahania poziomu co 50 ms (porywy), brak grzebienia harmonicznych (SG-HARM).
- Stan BRAK / SŁABY / SILNY z histerezą: 3 s, żeby wejść wyżej, 5 s, żeby zejść. Wiatr 10 m z Open-Meteo ≥ 30 km/h
  (świeży) obniża próg SILNY; bez internetu działa sam mikrofon.
- Przy SILNYM wietrze: alarm z samego DSP zablokowany; DSP+NET / NET / SG-FUZJA potrzebują +1 okna; alarm akustyczny
  jest żółty „DO WERYFIKACJI – wiatr” (MEDIUM), chyba że RF / Remote ID potwierdza. Reguła 88 % (RecordGate), Remote ID,
  RF, kamera i nagrywanie ręczne – bez zmian. Zdarzenia mają `wind_state`, `wind_score`, `wind_capped`.
- Sprawdzenie offline na prawdziwych nagraniach (tylko mono – te zbiory nie mają stereo), 1 s okna co 0,5 s:
  drony (450 nagrań pl, 196 neaptide, 247 DroneAudioDataset, 4 DADS; 23 732 okna) – stan SILNY / SŁABY po histerezie: 0 okien;
  ESC-50 „wind” (40 klipów): też 0 – to głównie nagrania szumu wiatru w drzewach, nie podmuchy w mikrofon, więc tryb mono
  (celowo ostrożny) ich nie łapie. Ścieżka stereo (koherencja) sprawdzona tylko na sygnałach syntetycznych.
