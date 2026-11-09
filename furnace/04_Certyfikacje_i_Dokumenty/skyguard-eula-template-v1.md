# UMOWA LICENCYJNA DLA UŻYTKOWNIKA KOŃCOWEGO (EULA)
## System Detekcji i Śledzenia Bezpilotowych Statków Powietrznych SKYGUARD C-UAS

**Wersja:** 1.0 (Komercyjna / Wdrożeniowa)  
**Data wydania:** 5 listopada 2026 r.  

---

### 1. DEFINICJE I PRZEDMIOT UMOWY
1.1. **Licencjodawca**: Zespół / Podmiot Rozwijający System SKYGUARD C-UAS.  
1.2. **Licencjobiorca**: Osoba fizyczna, podmiot gospodarczy lub jednostka budżetowa uzyskująca prawo do korzystania z Oprogramowania.  
1.3. **Oprogramowanie**: Pakiet oprogramowania **SKYGUARD C-UAS**, obejmujący:
   - Silnik analityczny i orkiestracyjny C# (.NET 8) dla stacji Windows.
   - Węzeł przeliczeniowy przetwarzania brzegowego dla systemu Linux (PlayStation 4 GDDR5 Edge Engine).
   - Aplikację mobilną i kontroler taktyczny na platformę Android / Google Pixel (**SKYGUARD Tactical APK**).
   - Skrypty autonomicznej kontroli urządzeń brzegowych (**Tapo SD Agent / Smooth PTZ Tracker**).
   - Moduły integracji chmurowej Google Cloud Enterprise (Spanner, Vertex AI, TPU v5p Trillium, Titan M2).

---

### 2. UDZIELENIE LICENCJI I ZAKRES STOSOWANIA
2.1. Licencjodawca udziela Licencjobiorcy niewyłącznej, niezbywalnej i ograniczonej terytorialnie licencji na użytkowanie Oprogramowania w celach detekcji, identyfikacji oraz śledzenia obiektów bezzałogowych (C-UAS).  
2.2. Licencja obejmuje model **BYOL (Bring Your Own License)** oraz **Node-Based Licensing**:
   - **Węzeł Stacyjny (PC / PS4)**: Jeden klucz licencyjny przypisany do unikalnego identyfikatora sprzętowego (TPM 2.0 / Hardware ID).
   - **Węzeł Mobilny (Pixel 10 Pro)**: Dostęp autoryzowany poprzez bezpieczny certyfikat krypto-procesora Titan M2.

---

### 3. WYMAGANIA PRAWNE I ZGODNOŚĆ Z EU AI ACT
3.1. **Nadzór Człowieka (Human-in-the-Loop)**: Zgodnie z Rozporządzeniem Parlamentu Europejskiego i Rady (EU AI Act - Artykuł 14 oraz 51), Oprogramowanie działa w trybie wspomagania decyzji. Ostateczna decyzja o podjęciu działań przeciwdziałających należy do Operatora.  
3.2. **Niepodważalny Rejestr Zdarzeń**: Wszytkie trajektorie, detekcje i autoryzacje są podpisane cyfrowo przy użyciu kluczy asymetrycznych w bezpiecznym procesorze **Titan M2**.

---

### 4. BEZPIECZEŃSTWO I OCHRONA DANYCH
4.1. **Izolacja Danych (Air-Gap Support)**: Oprogramowanie posiada zdolność do pełnej pracy w warunkach braku łączności z siecią globalną (Local Standalone / Field Mode).  
4.2. **Prywatność i Szyfrowanie**: Transmisja między węzłem mobilnym (Pixel) a bazą (PS4/PC) realizowana jest za pośrednictwem szyfrowanych tuneli **WireGuard / WPA3-Enterprise**.

---

### 5. OGRANICZENIA I ZAKAZY
5.1. Licencjobiorca nie ma prawa do inżynierii wstecznej (dekompilacji), modyfikacji natywnych modułów C++ NDK ani usuwania cyfrowych znaków wodnych i podpisów Titan M2.  
5.2. Eksport Oprogramowania poza granicę Unii Europejskiej lub obszaru NATO wymaga uzyskania odpowiednich zezwoleń na towary podwójnego zastosowania (*Dual-Use Regulation* UE 2021/821).

---

### 6. GWARANCJA I WSPARCIE TECHNICZNE
6.1. Oprogramowanie jest dostarczane w stanie „takim, w jakim się znajduje” (*As-Is*), z gwarancją ciągłości bezusterkowej pętli detekcji potwierdzonej standardami branżowymi.  
6.2. Wszelkie aktualizacje modeli neuronowych (YOLO / RF Fingerprinting) dostarczane są kanałem uczenia federacyjnego (*Vertex AI Federated Edge*).

---
**Podpis Licencjodawcy:** System SKYGUARD C-UAS Core Team  
**Zaakceptowano przez Licencjobiorcę:** [Wpisz nazwę podmiotu / użytkownika]
