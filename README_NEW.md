# Aplikacje do kodowania i analizy sentymentu i emocji

## 📋 Przegląd

Ten folder zawiera dwie aplikacje Streamlit:

1. **sent_emo_app.py** - do manualnego kodowania sentymentu i emocji w tekstach
2. **wyniki_analiza_sent_emo/** - 📊 **NOWA** - do analizy zgodności kodowania manualnego z automatycznym

## 📁 Struktura

```
sent_emo_app/
├── sent_emo_app.py                    # Aplikacja do kodowania manualnego
├── data_to_code.json                  # Dane wejściowe (teksty do kodowania)
├── results/                           # Wyniki kodowania lokalnie (backup)
├── .streamlit/                        # Konfiguracja Streamlit i Google Sheets
├── requirements.txt                   # Zależności dla kodowania
├── README.md                          # Ten plik
│
└── wyniki_analiza_sent_emo/          # 📊 NOWA APLIKACJA DO ANALIZY
    ├── analiza_zgodnosci_app.py      #    Główna aplikacja Streamlit
    ├── data_loader.py                #    Moduł wczytywania danych
    ├── agreement_metrics.py          #    Obliczenia wskaźników zgodności
    ├── visualizations.py             #    Wizualizacje Plotly
    ├── test_metrics.py               #    Testy weryfikacyjne
    ├── requirements.txt              #    Zależności dla analizy
    ├── QUICK_START.md                #    Szybki start (5 min)
    ├── INSTRUKCJA.md                 #    Pełna instrukcja użytkowania
    ├── PODSUMOWANIE.md               #    Status projektu
    └── README.md                     #    Dokumentacja techniczna
```

---

## 1️⃣ Aplikacja do kodowania manualnego

### Uruchomienie

```bash
streamlit run sent_emo_app.py
```

### Funkcjonalność

- Kodowanie w dwóch turach dla każdego tekstu:
  - **Sentyment**: Pozytywny, Negatywny, Neutralny
  - **Emocje**: Radość, Zaufanie, Oczekiwanie, Zaskoczenie, Strach, Smutek, Wstręt, Złość

- Skala natężenia: Brak (0) → Niskie (1) → Średnie (2) → Wysokie (3)

- 20 tekstów w jednej sesji

- Automatyczny zapis do:
  - Lokalne pliki JSON (`results/`)
  - Google Sheets (wymaga konfiguracji)

### Format wyników

```json
{
  "$oid": "67421ac51c0f4a032d63e507",
  "text": "Tekst...",
  "manual_sentiment": {
    "positive": 0,
    "negative": 2,
    "neutral": 1
  },
  "manual_emotion": {
    "joy": 0,
    "trust": 1,
    "anticipation": 2,
    "surprise": 0,
    "fear": 1,
    "sadness": 0,
    "disgust": 0,
    "anger": 1
  }
}
```

---

## 2️⃣ 📊 Aplikacja do analizy zgodności (NOWA)

### Uruchomienie

```bash
cd wyniki_analiza_sent_emo
streamlit run analiza_zgodnosci_app.py
```

### Funkcjonalność

✅ **Porównanie kodowania manualnego z dwoma narzędziami automatycznymi:**
- SENT_EMO (narzędzie 1)
- SENT_EMO_LLM (narzędzie 2 - LLM)

✅ **Wskaźniki zgodności (zweryfikowane naukowo):**
- Cohen's Kappa (κ) - uwzględnia zgodność przypadkową
- Weighted Kappa - dla danych porządkowych
- Krippendorff's Alpha (α) - uniwersalny, obsługuje wiele koderów
- ICC - z 95% przedziałami ufności
- Korelacje (Pearson, Spearman)
- Procentowa zgodność
- Macierze konfuzji

✅ **Wizualizacje interaktywne (Plotly):**
- Wykresy rozproszenia z liniami trendu
- Heatmapy zgodności
- Rozkłady wartości
- Macierze konfuzji
- Wykresy radarowe
- Tabele podsumowujące

✅ **Filtrowanie danych:**
- Według źródeł postów
- Według dat kodowania manualnego
- Według koderów
- Według kategorii (sentyment/emocje)

### Quick Start (5 minut)

1. **Instalacja:**
```bash
cd wyniki_analiza_sent_emo
pip install -r requirements.txt
```

2. **Konfiguracja Google Sheets:**
```bash
mkdir -p .streamlit
cp secrets.toml.example .streamlit/secrets.toml
# Edytuj .streamlit/secrets.toml i wpisz swoje dane
```

3. **Uruchomienie:**
```bash
streamlit run analiza_zgodnosci_app.py
```

4. **W aplikacji:** Kliknij "🔄 Wczytaj dane"

### Test poprawności

Zweryfikuj poprawność obliczeń statystycznych:

```bash
cd wyniki_analiza_sent_emo
python test_metrics.py
```

Powinny pojawić się komunikaty ✓ dla wszystkich testów.

### Dokumentacja

- **[QUICK_START.md](wyniki_analiza_sent_emo/QUICK_START.md)** - szybki start (5 minut)
- **[INSTRUKCJA.md](wyniki_analiza_sent_emo/INSTRUKCJA.md)** - pełna instrukcja z interpretacją wskaźników
- **[README.md](wyniki_analiza_sent_emo/README.md)** - dokumentacja techniczna i API
- **[PODSUMOWANIE.md](wyniki_analiza_sent_emo/PODSUMOWANIE.md)** - status projektu i lista funkcji

---

## 🎯 Typowy Workflow

```
┌─────────────────────────────────────────────────────────┐
│  1. Kodowanie manualne                                  │
│     └─> sent_emo_app.py                                 │
│     └─> Zapisz do Google Sheets + local backup          │
└─────────────────────────────────────────────────────────┘
                        ⬇
┌─────────────────────────────────────────────────────────┐
│  2. Analiza zgodności                                   │
│     └─> wyniki_analiza_sent_emo/analiza_zgodnosci_app.py│
│     └─> Wczytaj: Parquet + Google Sheets               │
│     └─> Oblicz wskaźniki + wizualizuj                   │
│     └─> Eksportuj wykresy i tabele                      │
└─────────────────────────────────────────────────────────┘
```

## 📊 Dane wymagane dla analizy

### Plik Parquet (kodowanie automatyczne)

Ścieżka domyślna: `C:\aktywne\dysk-M\sdns\dr-fn\Analiza_Treści_Fake_News\fn_data_analysis\data\interim\posts.parquet`

Wymagane kolumny:
- `post_id` - identyfikator
- `SENT_EMO_sentyment_*` (positive, negative, neutral) - wartości 0-1
- `SENT_EMO_emocje_*` (8 emocji) - wartości 0-1
- `SENT_EMO_LLM_sentyment_*` - wartości 0-0.95
- `SENT_EMO_LLM_emocje_*` - wartości 0-0.95

### Google Sheets (kodowanie manualne)

Wymagane kolumny:
- `timestamp` - data kodowania
- `coder_id` - ID kodera
- `oid` - identyfikator posta (= post_id z Parquet)
- `sentiment_*` (positive, negative, neutral) - wartości 0-3
- `emotion_*` (8 emocji) - wartości 0-3

## 🎓 Interpretacja wskaźników

### Cohen's Kappa (Landis & Koch, 1977)
- < 0.20: Niewielka
- 0.21-0.40: Słaba
- 0.41-0.60: Umiarkowana
- 0.61-0.80: Znaczna
- 0.81-1.00: Prawie doskonała

### Krippendorff's Alpha (Krippendorff, 2004)
- < 0.667: Niedostateczna (odrzucić wnioski)
- 0.667-0.800: Wstępna
- > 0.800: Definitywna

### ICC (Koo & Li, 2016)
- < 0.50: Słaba
- 0.50-0.75: Umiarkowana
- 0.75-0.90: Dobra
- > 0.90: Doskonała

## ⚠️ Ważne uwagi

1. **Aplikacja analizy wymaga danych manualnych** - musi być połączenie z Google Sheets
2. **Dane na żywo** - dane z Google Sheets aktualizują się przy każdym wczytaniu
3. **Normalizacja automatyczna** - aplikacja sama normalizuje skale (0-1 ↔ 0-3)
4. **Sprawdzaj liczebność** - po filtracji upewnij się, że masz wystarczającą liczbę obserwacji (min. 10-20)
5. **Używaj wielu wskaźników** - nie polegaj tylko na jednym wskaźniku

## 🆘 Pomoc

### Problemy z aplikacją kodowania
Zobacz dokumentację w górnej części tego pliku lub uruchom aplikację.

### Problemy z aplikacją analizy
1. Sprawdź **[INSTRUKCJA.md](wyniki_analiza_sent_emo/INSTRUKCJA.md)** - sekcja "Rozwiązywanie problemów"
2. Uruchom test: `python wyniki_analiza_sent_emo/test_metrics.py`
3. Sprawdź połączenie z Google Sheets
4. Zweryfikuj strukturę danych (Parquet i Google Sheets)

## 📚 Bibliografia

Metodologia zaimplementowana zgodnie z:
- Cohen, J. (1960). A coefficient of agreement for nominal scales.
- Krippendorff, K. (2004). Content Analysis: An Introduction to Its Methodology.
- Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data.
- Koo, T. K., & Li, M. Y. (2016). A guideline of selecting and reporting intraclass correlation coefficients.

## ✅ Status

- ✅ **Aplikacja kodowania:** Gotowa do użycia
- ✅ **Aplikacja analizy:** Gotowa do użycia (zweryfikowana i przetestowana)

---

**Utworzono:** 2025-12-01  
**Ostatnia aktualizacja:** 2025-12-01
