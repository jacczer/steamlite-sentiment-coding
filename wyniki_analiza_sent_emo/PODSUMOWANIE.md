# Podsumowanie aplikacji analizy zgodności kodowania

## ✅ Status: Gotowa do użycia

Aplikacja została pomyślnie stworzona i przetestowana.

## 📁 Struktura plików

```
app/wer_llm/sent_emo_app/wyniki_analiza_sent_emo/
├── analiza_zgodnosci_app.py      # Główna aplikacja Streamlit
├── data_loader.py                 # Moduł wczytywania danych
├── agreement_metrics.py           # Obliczenia wskaźników zgodności
├── visualizations.py              # Wizualizacje (Plotly)
├── test_metrics.py                # Testy weryfikacyjne
├── requirements.txt               # Zależności
├── INSTRUKCJA.md                  # Szczegółowa instrukcja użytkowania
└── README.md                      # Dokumentacja
```

## 🎯 Zaimplementowane funkcje

### 1. Wczytywanie danych ✓
- ✅ Wczytywanie z pliku Parquet (kodowanie automatyczne)
- ✅ Połączenie z Google Sheets (kodowanie manualne) 
- ✅ Automatyczne łączenie danych po post_id/oid
- ✅ Obsługa brakujących danych

### 2. Wskaźniki zgodności ✓
Wszystkie wskaźniki zweryfikowane i zgodne z metodologią naukową:

- ✅ **Cohen's Kappa** - uwzględnia zgodność przypadkową
- ✅ **Weighted Kappa** - dla danych porządkowych
- ✅ **Krippendorff's Alpha** - uniwersalny, obsługuje wiele koderów
- ✅ **ICC** - z przedziałami ufności (95% CI)
- ✅ **Korelacje** - Pearson i Spearman
- ✅ **Procentowa zgodność** - jako uzupełnienie
- ✅ **Macierze konfuzji** - dla każdej kategorii

### 3. Filtrowanie danych ✓
- ✅ Wybór źródeł danych (source)
- ✅ Filtrowanie po dacie kodowania
- ✅ Wybór konkretnego kodera
- ✅ Dynamiczne aktualizowanie wyników

### 4. Opcje analizy ✓
- ✅ Wybór typu: Sentyment / Emocje / Wszystko
- ✅ Porównanie z: SENT_EMO / SENT_EMO_LLM / Oba
- ✅ Wybór metryk do obliczenia
- ✅ Normalizacja skal (0-1 ↔ 0-3)

### 5. Wizualizacje ✓
Wszystkie wykresy interaktywne (Plotly):

- ✅ **Tabele podsumowujące** - wszystkie metryki
- ✅ **Wykresy słupkowe** - porównanie metryk między kategoriami
- ✅ **Wykresy radarowe** - profile metryk
- ✅ **Wykresy rozproszenia** - z liniami trendu i zgodnością
- ✅ **Macierze konfuzji** - z wartościami bezwzględnymi i %
- ✅ **Wykresy rozkładów** - porównanie częstości
- ✅ **Heatmapy** - zgodność między kategoriami

### 6. Interface użytkownika ✓
- ✅ Panel boczny z ustawieniami
- ✅ Status połączenia (live)
- ✅ 4 zakładki z różnymi widokami
- ✅ Responsywny layout (wide mode)
- ✅ Nowoczesny design

## 🔬 Weryfikacja naukowa

### Testy statystyczne ✓
Wszystkie testy zakończone sukcesem:

```
✓ TEST 1: Cohen's Kappa - działa poprawnie
✓ TEST 2: Weighted Kappa - wyższa dla małych różnic
✓ TEST 3: Krippendorff's Alpha - obsługuje brakujące dane
✓ TEST 4: ICC - z przedziałami ufności
✓ TEST 5: Procentowa zgodność - 100% accuracy
✓ TEST 6: Macierz konfuzji - poprawne wymiary
✓ TEST 7: Wszystkie metryki - kompletne
✓ TEST 8: Przypadki brzegowe - obsługa NaN
```

### Metodologia
Implementacja zgodna z publikacjami:
- **Landis & Koch (1977)** - interpretacja Cohen's Kappa
- **Krippendorff (2004)** - algorytm Krippendorff's Alpha
- **Koo & Li (2016)** - interpretacja ICC

## 📊 Dane wejściowe

### Plik Parquet
Kolumny wymagane:
- `post_id` - identyfikator
- `SENT_EMO_sentyment_*` (positive, negative, neutral) - wartości 0-1
- `SENT_EMO_emocje_*` (joy, trust, anticipation, surprise, fear, sadness, disgust, anger) - wartości 0-1
- `SENT_EMO_LLM_sentyment_*` - wartości 0-0.95
- `SENT_EMO_LLM_emocje_*` - wartości 0-0.95

### Google Sheets
Kolumny wymagane:
- `timestamp` - data kodowania
- `coder_id` - identyfikator kodera
- `oid` - identyfikator posta (= post_id)
- `text` - tekst (opcjonalnie)
- `sentiment_*` (positive, negative, neutral) - wartości 0-3
- `emotion_*` (joy, trust, anticipation, surprise, fear, sadness, disgust, anger) - wartości 0-3

Skala manualna: 0 = Brak, 1 = Niskie, 2 = Średnie, 3 = Wysokie

## 🚀 Uruchomienie

### 1. Instalacja zależności
```bash
cd app/wer_llm/sent_emo_app/wyniki_analiza_sent_emo
pip install -r requirements.txt
```

### 2. Konfiguracja Google Sheets
Utwórz plik `.streamlit/secrets.toml` z danymi dostępowymi (patrz INSTRUKCJA.md)

### 3. Uruchomienie aplikacji
```bash
streamlit run analiza_zgodnosci_app.py
```

### 4. Test weryfikacyjny (opcjonalnie)
```bash
python test_metrics.py
```

## 📖 Dokumentacja

- **INSTRUKCJA.md** - szczegółowa instrukcja użytkowania
- **README.md** - przegląd funkcji
- Komentarze w kodzie - dokumentacja funkcji

## 🎓 Wskaźniki i interpretacje

### Cohen's Kappa
- < 0.20: Niewielka
- 0.21-0.40: Słaba
- 0.41-0.60: Umiarkowana
- 0.61-0.80: Znaczna
- 0.81-1.00: Prawie doskonała

### Krippendorff's Alpha
- < 0.667: Niedostateczna (odrzucić wnioski)
- 0.667-0.800: Wstępna
- \> 0.800: Definitywna

### ICC
- < 0.50: Słaba
- 0.50-0.75: Umiarkowana
- 0.75-0.90: Dobra
- \> 0.90: Doskonała

## ⚠️ Uwagi

1. **Wymaga danych manualnych** - aplikacja potrzebuje danych z Google Sheets do działania
2. **Live update** - dane z Google Sheets są wczytywane na żywo przy każdym uruchomieniu
3. **Normalizacja** - aplikacja automatycznie normalizuje skale (0-1 → 0-3)
4. **Filtrowanie** - zawsze sprawdzaj ile rekordów zostało po filtracji
5. **Interpretacja** - używaj wielu wskaźników, nie polegaj tylko na jednym

## 🎯 Zalecenia użytkowania

1. **Najpierw mała próbka** - przetestuj na kilku rekordach
2. **Porównaj oba narzędzia** - zawsze analizuj SENT_EMO i SENT_EMO_LLM
3. **Sprawdź rozkłady** - upewnij się, że dane są zbalansowane
4. **Uwzględnij CI** - przedziały ufności są ważne dla ICC
5. **Dokumentuj filtry** - zapisuj jakie filtry zastosowałeś

## ✨ Gotowe do użycia!

Aplikacja jest w pełni funkcjonalna i gotowa do analizy zgodności kodowania manualnego z automatycznym. Wszystkie obliczenia zostały zweryfikowane i są zgodne z metodologią naukową.

---

**Utworzono:** 2025-12-01  
**Status:** ✅ Kompletna i przetestowana  
**Wersja:** 1.0
