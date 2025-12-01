# Analiza Zgodności Kodowania Sentymentu i Emocji

Aplikacja Streamlit do analizy zgodności między kodowaniem manualnym a dwoma systemami kodowania automatycznego (SENT_EMO i SENT_EMO_LLM).

## 🎯 Cel aplikacji

Aplikacja umożliwia rzetelną analizę zgodności międzykoderkowej (inter-rater reliability) między kodowaniem manualnym tekstów a wynikami dwóch narzędzi do automatycznego kodowania sentymentu i emocji. 

**Priorytety:**
- ✅ Rzetelność naukowa
- ✅ Zgodność metodologiczna
- ✅ Weryfikowane wskaźniki statystyczne
- ✅ Zgodność z publikacjami naukowymi

## 📦 Instalacja

### 1. Zainstaluj zależności

```bash
cd app/wer_llm/sent_emo_app/wyniki_analiza_sent_emo
pip install -r requirements.txt
```

### 2. Skonfiguruj Google Sheets

Skopiuj plik `secrets.toml.example`:

```bash
mkdir -p .streamlit
cp secrets.toml.example .streamlit/secrets.toml
```

Następnie edytuj `.streamlit/secrets.toml` i wpisz swoje dane dostępowe do Google Sheets.

## 🚀 Uruchomienie

```bash
cd app/wer_llm/sent_emo_app/wyniki_analiza_sent_emo
streamlit run analiza_zgodnosci_app.py
```

Aplikacja otworzy się w przeglądarce (domyślnie: http://localhost:8501)

## ✅ Test weryfikacyjny

Aby sprawdzić poprawność obliczeń statystycznych:

```bash
python test_metrics.py
```

## 📊 Funkcje

### Wskaźniki zgodności
Wszystkie wskaźniki zweryfikowane i zgodne z metodologią naukową:

- **Cohen's Kappa (κ)** - uwzględnia zgodność przypadkową
  - Interpretacja wg Landis & Koch (1977)
  - Weighted Kappa dla danych porządkowych
  
- **Krippendorff's Alpha (α)** - najbardziej uniwersalny wskaźnik
  - Działa dla wielu koderów
  - Obsługuje brakujące dane
  - Interpretacja wg Krippendorff (2004)
  
- **ICC** - Intraclass Correlation Coefficient
  - Z 95% przedziałami ufności
  - Model ICC(2,1) - two-way random effects
  - Interpretacja wg Koo & Li (2016)
  
- **Korelacje** - Pearson i Spearman
- **Procentowa zgodność** - jako uzupełnienie
- **Macierze konfuzji** - dla każdej kategorii

### Wizualizacje

Wszystkie wykresy są interaktywne (Plotly):

- 📊 **Tabele podsumowujące** - wszystkie metryki w jednym miejscu
- 📈 **Wykresy słupkowe** - porównanie metryk między kategoriami
- 🎯 **Wykresy radarowe** - profile metryk zgodności
- 📉 **Wykresy rozproszenia** - relacje manual vs automatyczne + linie trendu
- 🎨 **Macierze konfuzji** - z wartościami bezwzględnymi i procentowymi
- 📊 **Rozkłady wartości** - porównanie częstości
- 🔥 **Heatmapy** - zgodność między kategoriami

### Filtrowanie danych

- 🔍 **Źródła** - wybór konkretnych źródeł postów
- 📅 **Daty** - zakres dat kodowania manualnego
- 👤 **Koderzy** - analiza dla konkretnych koderów
- 🎯 **Kategorie** - sentyment / emocje / wszystko
- 🤖 **Narzędzia** - SENT_EMO / SENT_EMO_LLM / oba

## 📂 Struktura danych

### Plik Parquet (dane automatyczne)

Wymagane kolumny:
```
post_id                          - identyfikator posta (string/int)
source                           - źródło posta (opcjonalnie)

SENT_EMO_sentyment_positive      - wartości 0-1 (float)
SENT_EMO_sentyment_negative      - wartości 0-1 (float)
SENT_EMO_sentyment_neutral       - wartości 0-1 (float)

SENT_EMO_emocje_joy             - wartości 0-1 (float)
SENT_EMO_emocje_trust           - wartości 0-1 (float)
SENT_EMO_emocje_anticipation    - wartości 0-1 (float)
SENT_EMO_emocje_surprise        - wartości 0-1 (float)
SENT_EMO_emocje_fear            - wartości 0-1 (float)
SENT_EMO_emocje_sadness         - wartości 0-1 (float)
SENT_EMO_emocje_disgust         - wartości 0-1 (float)
SENT_EMO_emocje_anger           - wartości 0-1 (float)

SENT_EMO_LLM_sentyment_*        - wartości 0-0.95 (float)
SENT_EMO_LLM_emocje_*           - wartości 0-0.95 (float)
```

### Google Sheets (dane manualne)

Wymagane kolumny w Google Sheets (automatycznie mapowane):
```
timestamp                        - data/czas kodowania (datetime)
coder_id                        - identyfikator kodera (string)
oid                             - identyfikator posta = post_id (string)
text                            - tekst posta (string, opcjonalnie)

positive                        - wartości 0-3 (int) → mapowane do sentiment_positive
negative                        - wartości 0-3 (int) → mapowane do sentiment_negative
neutral                         - wartości 0-3 (int) → mapowane do sentiment_neutral

joy                             - wartości 0-3 (int) → mapowane do emotion_joy
trust                           - wartości 0-3 (int) → mapowane do emotion_trust
anticipation                    - wartości 0-3 (int) → mapowane do emotion_anticipation
surprise                        - wartości 0-3 (int) → mapowane do emotion_surprise
fear                            - wartości 0-3 (int) → mapowane do emotion_fear
sadness                         - wartości 0-3 (int) → mapowane do emotion_sadness
disgust                         - wartości 0-3 (int) → mapowane do emotion_disgust
anger                           - wartości 0-3 (int) → mapowane do emotion_anger
```

**Uwaga:** Aplikacja automatycznie dodaje prefiksy `sentiment_` i `emotion_` do krótkich nazw kolumn z Google Sheets.
Można używać zarówno krótkich nazw (positive, joy) jak i pełnych nazw (sentiment_positive, emotion_joy).

**Skala manualna:**
- 0 = Brak
- 1 = Niskie natężenie
- 2 = Średnie natężenie
- 3 = Wysokie natężenie

## 📖 Dokumentacja

- **[INSTRUKCJA.md](INSTRUKCJA.md)** - szczegółowa instrukcja użytkowania aplikacji
- **[PODSUMOWANIE.md](PODSUMOWANIE.md)** - status projektu i pełne podsumowanie
- **test_metrics.py** - skrypt testowy do weryfikacji obliczeń

## 🎓 Interpretacja wskaźników

### Cohen's Kappa
| Wartość | Interpretacja |
|---------|---------------|
| < 0.00 | Zła (gorsza niż losowa) |
| 0.00 - 0.20 | Niewielka |
| 0.21 - 0.40 | Słaba |
| 0.41 - 0.60 | Umiarkowana |
| 0.61 - 0.80 | Znaczna |
| 0.81 - 1.00 | Prawie doskonała |

*Źródło: Landis & Koch (1977)*

### Krippendorff's Alpha
| Wartość | Interpretacja |
|---------|---------------|
| < 0.667 | Niedostateczna (odrzucić wnioski) |
| 0.667 - 0.800 | Wstępna (tentative conclusions) |
| > 0.800 | Definitywna (definite conclusions) |

*Źródło: Krippendorff (2004)*

### ICC
| Wartość | Interpretacja |
|---------|---------------|
| < 0.50 | Słaba (Poor) |
| 0.50 - 0.75 | Umiarkowana (Moderate) |
| 0.75 - 0.90 | Dobra (Good) |
| > 0.90 | Doskonała (Excellent) |

*Źródło: Koo & Li (2016)*

## 🔧 Struktura projektu

```
wyniki_analiza_sent_emo/
├── analiza_zgodnosci_app.py      # Główna aplikacja Streamlit
├── data_loader.py                 # Wczytywanie i łączenie danych
├── agreement_metrics.py           # Obliczenia statystyczne
├── visualizations.py              # Wizualizacje Plotly
├── test_metrics.py                # Testy weryfikacyjne
├── requirements.txt               # Zależności Python
├── INSTRUKCJA.md                  # Instrukcja użytkowania
├── PODSUMOWANIE.md                # Podsumowanie projektu
├── README.md                      # Ten plik
├── secrets.toml.example           # Przykład konfiguracji
└── .gitignore                     # Ignorowane pliki
```

## ⚠️ Ważne uwagi

1. **Dane manualne są wymagane** - aplikacja potrzebuje danych z Google Sheets
2. **Dane na żywo** - dane z Google Sheets są wczytywane przy każdym uruchomieniu
3. **Normalizacja automatyczna** - aplikacja automatycznie normalizuje skale między 0-1 i 0-3
4. **Sprawdzaj liczebność** - upewnij się, że po filtracji masz wystarczającą liczbę obserwacji
5. **Używaj wielu wskaźników** - nie polegaj tylko na jednym wskaźniku

## 📚 Bibliografia

- Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement*, 20(1), 37-46.

- Krippendorff, K. (2004). *Content Analysis: An Introduction to Its Methodology* (2nd ed.). Sage Publications.

- Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1), 159-174.

- Koo, T. K., & Li, M. Y. (2016). A guideline of selecting and reporting intraclass correlation coefficients for reliability research. *Journal of Chiropractic Medicine*, 15(2), 155-163.

## 📞 Pomoc

Jeśli napotkasz problemy:

1. Sprawdź **[INSTRUKCJA.md](INSTRUKCJA.md)** - sekcja "Rozwiązywanie problemów"
2. Uruchom **test_metrics.py** - zweryfikuj poprawność obliczeń
3. Sprawdź połączenie z Google Sheets - upewnij się, że secrets.toml jest poprawny
4. Zweryfikuj strukturę danych - sprawdź czy wszystkie wymagane kolumny istnieją

## ✅ Status

**Aplikacja jest gotowa do użycia!**

Wszystkie komponenty zostały zaimplementowane, przetestowane i zweryfikowane pod kątem poprawności metodologicznej.
