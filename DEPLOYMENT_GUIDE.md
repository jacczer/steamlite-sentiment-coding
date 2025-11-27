# 📊 Aplikacja do kodowania sentymentu i emocji

Aplikacja Streamlit do manualnego kodowania sentymentu i emocji w tekstach z automatycznym zapisem do Google Sheets.

## ✨ Funkcje

- 🎯 Kodowanie 20 tekstów w sesji
- 😊 Sentyment: pozytywny, negatywny, neutralny (skala 0-2)
- 🎭 Emocje: 8 kategorii Plutchika (radość, zaufanie, oczekiwanie, zaskoczenie, strach, smutek, wstręt, złość)
- ☁️ Automatyczny zapis do Google Sheets w czasie rzeczywistym
- 👥 Wspólny arkusz dla wielu użytkowników
- 💾 Lokalny backup w formacie JSON

## 🚀 Deploy na Streamlit Cloud

### Krok 1: Przygotowanie Google Sheets

1. Utwórz nowy arkusz Google Sheets
2. Skopiuj ID arkusza z URL (część między `/d/` a `/edit`)
   ```
   https://docs.google.com/spreadsheets/d/[ID_ARKUSZA]/edit
   ```
3. Dodaj nagłówki w pierwszym wierszu:
   ```
   timestamp | coder_id | oid | text | positive | negative | neutral | joy | trust | anticipation | surprise | fear | sadness | disgust | anger
   ```

### Krok 2: Udostępnij arkusz service account

1. Znajdź w pliku `steamlite-api-ca337c69ec99.json` wartość `client_email`:
   ```
   steamlite-robot@steamlite-api.iam.gserviceaccount.com
   ```
2. W Google Sheets kliknij **Share** (Udostępnij)
3. Dodaj powyższy email jako **Editor**
4. Wyślij zaproszenie

### Krok 3: Deploy na Streamlit Cloud

1. Wejdź na https://share.streamlit.io/
2. Zaloguj się kontem GitHub
3. Kliknij **New app**
4. Wypełnij formularz:
   - **Repository:** `jacczer/steamlite-sentiment-coding`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Kliknij **Advanced settings**
6. W sekcji **Secrets** wklej zawartość z `example_secrets.toml`, zastępując wartości danymi z pliku `steamlite-api-ca337c69ec99.json`:

```toml
[gsheets]
type = "service_account"
project_id = "steamlite-api"
private_key_id = "ca337c69ec99675a43a890cf3f5e8e7ca1fdd764"
private_key = "-----BEGIN PRIVATE KEY-----\n[TWÓJ_KLUCZ]\n-----END PRIVATE KEY-----\n"
client_email = "steamlite-robot@steamlite-api.iam.gserviceaccount.com"
client_id = "100499984497557336964"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/steamlite-robot%40steamlite-api.iam.gserviceaccount.com"
universe_domain = "googleapis.com"

SPREADSHEET_ID = "1ShqRuRy_-JE8iapy9P02sDZtIdZn4FO_mkTQT3N-9K4"
```

7. Kliknij **Deploy**
8. Poczekaj na zakończenie procesu (2-5 minut)

### Krok 4: Test

1. Otwórz link do aplikacji (np. `https://twoja-aplikacja.streamlit.app`)
2. Podaj identyfikator kodera
3. Zakoduj kilka tekstów
4. Sprawdź, czy dane pojawiają się w Google Sheets

## 🛠️ Uruchomienie lokalne

### Wymagania

- Python 3.8+
- pip

### Instalacja

```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Utwórz folder .streamlit i plik secrets.toml
mkdir .streamlit
# Skopiuj dane z example_secrets.toml do .streamlit/secrets.toml

# Uruchom aplikację
streamlit run app.py
```

## 📁 Struktura danych

### Google Sheets

Każdy wiersz w arkuszu reprezentuje jedno zakodowane obserwacje:

| Kolumna | Opis | Przykład |
|---------|------|----------|
| `timestamp` | Data i czas zapisu (UTC) | `2025-11-27T10:30:45.123456` |
| `coder_id` | Identyfikator kodera | `JK` |
| `oid` | ID rekordu MongoDB | `507f1f77bcf86cd799439011` |
| `text` | Zakodowany tekst | `To jest przykładowy tekst...` |
| `positive` | Sentyment pozytywny (0-2) | `1` |
| `negative` | Sentyment negatywny (0-2) | `0` |
| `neutral` | Sentyment neutralny (0-2) | `2` |
| `joy` | Emocja: radość (0-2) | `1` |
| `trust` | Emocja: zaufanie (0-2) | `0` |
| `anticipation` | Emocja: oczekiwanie (0-2) | `2` |
| `surprise` | Emocja: zaskoczenie (0-2) | `0` |
| `fear` | Emocja: strach (0-2) | `1` |
| `sadness` | Emocja: smutek (0-2) | `0` |
| `disgust` | Emocja: wstręt (0-2) | `0` |
| `anger` | Emocja: złość (0-2) | `1` |

### Lokalny backup

Dodatkowo, po zakończeniu sesji 20 tekstów, tworzy się lokalny plik JSON w folderze `results/`:
- Format: `manual_coding_YYYYMMDD_HHMMSS.json`
- Zawiera wszystkie zakodowane elementy z sesji

## 🔧 Konfiguracja

### Zmiana liczby tekstów w sesji

W pliku `app.py`, linia 106:

```python
st.session_state.session_elements = st.session_state.data[:20]  # Zmień 20 na inną liczbę
```

### Zmiana skali kodowania

Obecnie używana jest skala 0-2. Aby zmienić:

1. Zmodyfikuj słownik `SCALE_LABELS` (linie 33-37)
2. Dostosuj parametry `max_value` w funkcjach `sentiment_coding_ui()` i `emotion_coding_ui()`

## 📝 Licencja

MIT License

## 👤 Autor

jacczer
