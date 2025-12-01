# Instrukcja użytkowania aplikacji analizy zgodności kodowania

## 1. Przygotowanie środowiska

### Instalacja zależności

```bash
cd app/wer_llm/sent_emo_app/wyniki_analiza_sent_emo
pip install -r requirements.txt
```

### Konfiguracja dostępu do Google Sheets

Aplikacja wymaga skonfigurowania dostępu do Google Sheets w pliku `.streamlit/secrets.toml` (w głównym katalogu projektu lub w katalogu aplikacji).

Przykładowa konfiguracja:

```toml
SPREADSHEET_ID = "twoj_id_arkusza"

[gsheets]
type = "service_account"
project_id = "twoj-projekt"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "twoj-email@twoj-projekt.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

## 2. Uruchomienie aplikacji

```bash
cd app/wer_llm/sent_emo_app/wyniki_analiza_sent_emo
streamlit run analiza_zgodnosci_app.py
```

Aplikacja otworzy się w przeglądarce (domyślnie: http://localhost:8501)

## 3. Korzystanie z aplikacji

### Krok 1: Wczytanie danych

1. W panelu bocznym sprawdź lub zmień ścieżkę do pliku Parquet z danymi automatycznymi
2. Kliknij przycisk **"🔄 Wczytaj dane"**
3. Poczekaj na potwierdzenie wczytania danych z Parquet i Google Sheets
4. Sprawdź status połączenia

### Krok 2: Filtrowanie danych (opcjonalne)

Po wczytaniu danych możesz zastosować filtry:

- **Źródła danych** - wybierz konkretne źródła postów
- **Zakres dat** - ogranicz do konkretnego okresu kodowania manualnego
- **Koder** - wybierz konkretnego kodera lub analizuj wszystkich

### Krok 3: Konfiguracja analizy

Wybierz opcje analizy:

- **Typ analizy**:
  - Sentyment - analiza tylko kategorii sentymentu
  - Emocje - analiza tylko emocji
  - Wszystko - pełna analiza

- **Porównaj z**:
  - SENT_EMO - porównanie z pierwszym narzędziem automatycznym
  - SENT_EMO_LLM - porównanie z narzędziem LLM
  - Oba - porównanie z oboma narzędziami

- **Metryki** - zaznacz metryki do obliczenia:
  - Cohen's Kappa
  - Krippendorff's Alpha
  - ICC
  - Korelacje

### Krok 4: Analiza wyników

Aplikacja oferuje cztery zakładki z różnymi widokami:

#### 📊 Przegląd metryk
- Tabele podsumowujące wszystkie metryki dla każdej kategorii
- Wykresy słupkowe porównujące wartości Cohen's Kappa
- Wykresy radarowe pokazujące profile metryk

#### 🎯 Szczegółowa analiza
- Wybierz konkretną kategorię do głębszej analizy
- Tabela wszystkich metryk zgodności
- Porównanie rozkładów wartości
- Macierz konfuzji

#### 📉 Wykresy rozproszenia
- Wykresy punktowe pokazujące relację między kodowaniem manualnym a automatycznym
- Linia ideałnej zgodności (czerwona przerywana)
- Linia trendu (niebieska)
- Współczynniki korelacji (Spearman i Pearson)

#### 📋 Macierze konfuzji
- Macierze konfuzji dla wszystkich kategorii
- Pokazują dokładność kodowania automatycznego dla każdego poziomu natężenia
- Wartości bezwzględne i procentowe

## 4. Interpretacja wskaźników

### Cohen's Kappa (κ)
Mierzy zgodność uwzględniając losowe zgadywanie.

**Interpretacja (Landis & Koch, 1977):**
- < 0.00: Zła (gorsza niż losowa)
- 0.00 - 0.20: Niewielka
- 0.21 - 0.40: Słaba
- 0.41 - 0.60: Umiarkowana
- 0.61 - 0.80: Znaczna
- 0.81 - 1.00: Prawie doskonała

### Krippendorff's Alpha (α)
Najbardziej uniwersalny wskaźnik, działa dla wielu koderów i brakujących danych.

**Interpretacja (Krippendorff, 2004):**
- < 0.667: Niedostateczna (odrzucić wnioski)
- 0.667 - 0.800: Wstępna (tentative conclusions)
- \> 0.800: Definitywna (definite conclusions)

### ICC (Intraclass Correlation Coefficient)
Odpowiedni dla danych ciągłych i porządkowych.

**Interpretacja (Koo & Li, 2016):**
- < 0.50: Słaba (Poor)
- 0.50 - 0.75: Umiarkowana (Moderate)
- 0.75 - 0.90: Dobra (Good)
- \> 0.90: Doskonała (Excellent)

### Korelacje
- **Pearson's r** - dla relacji liniowych
- **Spearman's ρ** - bardziej odpowiednia dla danych porządkowych

**Interpretacja:**
- 0.00 - 0.30: Słaba
- 0.30 - 0.50: Umiarkowana
- 0.50 - 0.70: Silna
- \> 0.70: Bardzo silna

## 5. Struktura danych

### Dane wejściowe (Parquet)
Plik musi zawierać kolumny:
- `post_id` - identyfikator posta (do łączenia z danymi manualnymi)
- `SENT_EMO_sentyment_*` - sentyment z narzędzia 1 (wartości 0-1)
- `SENT_EMO_emocje_*` - emocje z narzędzia 1 (wartości 0-1)
- `SENT_EMO_LLM_sentyment_*` - sentyment z LLM (wartości 0-0.95)
- `SENT_EMO_LLM_emocje_*` - emocje z LLM (wartości 0-0.95)

### Dane manualne (Google Sheets)
Arkusz musi zawierać kolumny:
- `timestamp` - data i czas kodowania
- `coder_id` - identyfikator kodera
- `oid` - identyfikator posta (odpowiada post_id w Parquet)
- `text` - tekst posta
- `sentiment_positive`, `sentiment_negative`, `sentiment_neutral` - wartości 0-3
- `emotion_joy`, `emotion_trust`, `emotion_anticipation`, `emotion_surprise`,
  `emotion_fear`, `emotion_sadness`, `emotion_disgust`, `emotion_anger` - wartości 0-3

Skala manualna: 0 = Brak, 1 = Niskie, 2 = Średnie, 3 = Wysokie

## 6. Eksport wyników

Wyniki można zapisać poprzez:
1. Screenshot wykresów (przycisk kamery w prawym górnym rogu każdego wykresu Plotly)
2. Pobieranie tabel (użyj funkcji przeglądarki do zapisu)
3. Kopiowanie danych z tabel Streamlit

## 7. Rozwiązywanie problemów

### Błąd połączenia z Google Sheets
- Sprawdź poprawność SPREADSHEET_ID
- Upewnij się, że service account ma dostęp do arkusza
- Zweryfikuj poprawność klucza prywatnego

### Brak wspólnych rekordów
- Sprawdź czy post_id w Parquet odpowiadają oid w Google Sheets
- Upewnij się, że oid są zapisane jako tekst (nie jako liczby)

### Błędy obliczeń metryk
- Sprawdź czy dane zawierają wystarczającą liczbę obserwacji (minimum 3-5)
- Upewnij się, że wartości manualne są w zakresie 0-3
- Sprawdź czy nie ma zbyt wielu brakujących danych

## 8. Najlepsze praktyki

1. **Rozpocznij od małej próbki** - przetestuj na kilku rekordach przed pełną analizą
2. **Regularnie aktualizuj dane** - dane z Google Sheets są wczytywane na żywo
3. **Dokumentuj filtry** - zapisuj jakie filtry zastosowałeś przy analizie
4. **Analizuj wielokrotnie** - sprawdź zgodność dla różnych podzbiorów danych
5. **Porównuj oba narzędzia** - zawsze analizuj SENT_EMO i SENT_EMO_LLM
6. **Zwracaj uwagę na CI** - przedziały ufności dla ICC są ważne dla interpretacji

## 9. Referencje metodologiczne

- Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. Biometrics, 33(1), 159-174.
- Krippendorff, K. (2004). Content Analysis: An Introduction to Its Methodology (2nd ed.). Sage Publications.
- Koo, T. K., & Li, M. Y. (2016). A guideline of selecting and reporting intraclass correlation coefficients for reliability research. Journal of Chiropractic Medicine, 15(2), 155-163.
- Cohen, J. (1960). A coefficient of agreement for nominal scales. Educational and Psychological Measurement, 20(1), 37-46.
