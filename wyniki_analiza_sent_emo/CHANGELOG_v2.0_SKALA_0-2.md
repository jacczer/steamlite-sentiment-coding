# Changelog v2.0 - Przejście na skalę 0-2

## Data: 2 grudnia 2025

## Główne zmiany

### 1. Zmiana skali kodowania manualnego: 0-3 → 0-2

**Poprzednio:**
- Skala 4-stopniowa: 0 (brak), 1 (niskie), 2 (średnie), 3 (wysokie)

**Teraz:**
- Skala 3-stopniowa: 
  - **0** = Brak
  - **1** = Obecna (nawet śladowa)
  - **2** = Obecność silna

### 2. Nowe funkcjonalności - Progi konwersji dla kodowania automatycznego

#### Dodano konfigurowalne progi w panelu bocznym

Użytkownik może teraz ustawiać niezależne progi dla SENT_EMO i SENT_EMO_LLM do konwersji prawdopodobieństwa (0-1) na skalę ordinalną (0-2):

**Panel boczny zawiera:**
- Sekcję "⚙️ Progi konwersji skali (0-1 → 0-2)" na górze
- Dwa rozwijane ekspandery:
  - 🔧 SENT_EMO
  - 🔧 SENT_EMO_LLM
- W każdym ekspanderze:
  - Suwak "Próg: brak → obecność słaba" (dolny próg)
  - Suwak "Próg: obecność słaba → silna" (górny próg)
  - Podgląd aktualnego mapowania

**Domyślne progi:**
- Dolny próg: 0.15
- Górny próg: 0.75

**Mapowanie:**
- Wartości < dolny próg → 0 (brak)
- Wartości >= dolny próg i < górny próg → 1 (obecna)
- Wartości >= górny próg → 2 (obecność silna)

#### Przycisk "🔄 Zastosuj nowe progi"
- Umożliwia ponowne przeliczenie danych z nowymi progami
- Pojawia się w sekcji progów po wczytaniu danych

### 3. Zmiany w strukturze danych

#### data_loader.py

**Nowe funkcje:**
- `apply_thresholds()` - konwertuje wartości ciągłe (0-1) na ordynalne (0-2) zgodnie z progami
- `convert_automatic_coding_to_ordinal()` - aplikuje progi do wszystkich kolumn kodowania automatycznego
- Zaktualizowano `normalize_to_scale()` - dodano parametry threshold_low i threshold_high

**Zmodyfikowane funkcje:**
- `get_sentiment_columns(use_ordinal=True)` - zwraca kolumny z sufiksem '_ordinal' dla kodowania automatycznego
- `get_emotion_columns(use_ordinal=True)` - analogicznie dla emocji
- `load_manual_coding_data()` - zaktualizowano dokumentację do skali 0-2

**Nowa struktura kolumn:**
- Oryginalne kolumny SENT_EMO/SENT_EMO_LLM (0-1 continuous): `SENT_EMO_sentyment_positive`, etc.
- Nowe kolumny ordinalne (0-2 discrete): `SENT_EMO_sentyment_positive_ordinal`, etc.
- Kolumny manualne bez zmian: `sentiment_positive` (już w skali 0-2)

### 4. Zmiany w analiza_zgodnosci_app.py

**Session state:**
- Dodano `sent_emo_threshold_low` (default: 0.33)
- Dodano `sent_emo_threshold_high` (default: 0.67)
- Dodano `sent_emo_llm_threshold_low` (default: 0.33)
- Dodano `sent_emo_llm_threshold_high` (default: 0.67)
- Dodano `parquet_path` - przechowuje ostatnią używaną ścieżkę do pliku

**Funkcja load_data():**
- Po wczytaniu Parquet automatycznie konwertuje dane do skali ordinalnej
- Używa aktualnych progów z session_state
- Stosuje `convert_automatic_coding_to_ordinal()` przed dalszym przetwarzaniem

**Usunięto wywołania normalize_to_scale():**
- Dane są już w odpowiedniej skali po wczytaniu
- Wszystkie wywołania `normalize_to_scale(..., target_scale='0-3')` zostały zastąpione bezpośrednim użyciem danych

**Ekran powitalny:**
- Dodano info box z wyjaśnieniem skal kodowania
- Opis skali manualnej (0-2)
- Opis konwersji kodowania automatycznego
- Informacja o możliwości dostosowania progów

### 5. Zmiany w visualizations.py

**Aktualizacje:**
- Wykresy rozproszenia: oś (0-3) → (0-2)
- Rozkłady wartości: 
  - Usunięto normalizację (dane już w skali 0-2)
  - Zaktualizowano etykiety osi: "Wartość (0=Brak, 1=Obecność słaba, 2=Obecność silna)"

### 6. Zmiany w macierzach konfuzji

**Nowe etykiety:**
- Poprzednio: ['Brak', 'Niskie', 'Średnie', 'Wysokie'] (0-3)
- Teraz: ['Brak', 'Obecność słaba', 'Obecność silna'] (0-2)

**Wszystkie wywołania confusion_matrix:**
- Zmieniono `labels=[0, 1, 2, 3]` → `labels=[0, 1, 2]`

### 7. Metryki zgodności

**Bez zmian w obliczeniach:**
- Cohen's Kappa, Krippendorff's Alpha, ICC działają tak samo
- Wszystkie używają `data_type='ordinal'`
- Automatycznie dostosowują się do liczby kategorii

## Instrukcja użycia

### Podstawowy przepływ pracy:

1. **Uruchom aplikację:**
   ```bash
   cd app/wer_llm/sent_emo_app/wyniki_analiza_sent_emo
   streamlit run analiza_zgodnosci_app.py
   ```

2. **Ustaw progi konwersji** (opcjonalne, w panelu bocznym):
   - Rozwiń sekcję "🔧 SENT_EMO" lub "🔧 SENT_EMO_LLM"
   - Dostosuj progi używając suwaków
   - Zobacz podgląd aktualnego mapowania

3. **Wczytaj dane:**
   - Dane wczytają się automatycznie przy pierwszym uruchomieniu
   - Lub użyj przycisku "🔄 Wczytaj dane" w rozwijanej sekcji "📁 Dane wejściowe"

4. **Zastosuj nowe progi** (jeśli zmieniono):
   - Kliknij "🔄 Zastosuj nowe progi" w sekcji progów
   - Dane zostaną przetworzone ponownie

5. **Analizuj wyniki:**
   - Wybierz typ analizy (Sentyment/Emocje/Wszystko)
   - Wybierz źródła do porównania
   - Przeglądaj zakładki z metrykami, wykresami i macierzami

### Przykłady użycia progów:

**Konserwatywne (wysokie wymagania na "obecność"):**
- Dolny próg: 0.5
- Górny próg: 0.8
- Rezultat: Więcej wartości "0" (brak), mniej "2" (silna obecność)

**Liberalne (niskie wymagania):**
- Dolny próg: 0.2
- Górny próg: 0.5
- Rezultat: Więcej wartości "1" i "2", mniej "0"

**Równomierne (domyślne):**
- Dolny próg: 0.33
- Górny próg: 0.67
- Rezultat: Równomierne rozłożenie w trzech kategoriach

## Kompatybilność wsteczna

**⚠️ UWAGA:** Ta wersja NIE jest kompatybilna wstecz z danymi w skali 0-3.

**Wymagane zmiany w danych:**
- Dane w Google Sheets muszą używać skali 0-2
- Kolumny: positive, negative, neutral, joy, trust, anticipation, surprise, fear, sadness, disgust, anger
- Wartości: tylko 0, 1, lub 2

**Migracja danych ze skali 0-3 do 0-2:**
Jeśli masz istniejące dane w skali 0-3, musisz je przekonwertować:
```python
# Przykład konwersji (jeśli stosowano równomiernie):
# 0 → 0 (brak)
# 1 → 1 (niskie → słabe)
# 2 → 1 (średnie → słabe)
# 3 → 2 (wysokie → silne)

# Lub bardziej konserwatywnie:
# 0 → 0 (brak)
# 1 → 1 (niskie → słabe)
# 2, 3 → 2 (średnie/wysokie → silne)
```

## Testy

Przed wdrożeniem należy przetestować:

- [ ] Wczytywanie danych z Parquet
- [ ] Wczytywanie danych z Google Sheets
- [ ] Konwersję progową dla SENT_EMO
- [ ] Konwersję progową dla SENT_EMO_LLM
- [ ] Przycisk "Zastosuj nowe progi"
- [ ] Obliczanie metryk zgodności
- [ ] Wyświetlanie macierzy konfuzji (3x3)
- [ ] Wykresy rozproszenia (skala 0-2)
- [ ] Rozkłady wartości
- [ ] Filtrowanie danych

## Pliki zmodyfikowane

1. `data_loader.py` - nowe funkcje konwersji, zaktualizowane funkcje get_*_columns()
2. `analiza_zgodnosci_app.py` - UI progów, session state, load_data(), usunięto normalize_to_scale()
3. `visualizations.py` - aktualizacje etykiet i osi (0-3 → 0-2)
4. `agreement_metrics.py` - bez zmian (automatycznie obsługuje 0-2)

## Autor zmian

Modyfikacje wykonane 2 grudnia 2025 przez GitHub Copilot
