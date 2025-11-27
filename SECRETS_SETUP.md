# 🔑 KONFIGURACJA SECRETS NA STREAMLIT CLOUD

## ⚠️ WAŻNE: Użyj pliku z danymi które Ci wysłałem!

Masz plik `steamlite-api-ca337c69ec99.json` z prawdziwymi danymi.

## 📋 Kroki konfiguracji:

### Krok 1: Przygotuj JSON jako string

1. Otwórz plik `steamlite-api-ca337c69ec99.json` w edytorze tekstu
2. **SKOPIUJ CAŁĄ zawartość** (od `{` do `}`)
3. Wklej do narzędzia online które **zamieni na jedną linię**:
   - Możesz użyć: https://jsonformatter.org/json-minify
   - Lub ręcznie usuń wszystkie nowe linie

4. **WAŻNE:** Upewnij się, że w kluczu prywatnym `\n` jest zapisane jako `\\n` (podwójny backslash)

### Krok 2: Skonfiguruj secrets na Streamlit Cloud

1. Wejdź na: https://share.streamlit.io/
2. Znajdź swoją aplikację
3. Kliknij **⚙️ Settings** → **Secrets**
4. **USUŃ całą obecną zawartość** w sekcji Secrets
5. **WKLEJ** dokładnie to (zamieniając wartości):

```toml
SPREADSHEET_ID = "1ShqRuRy_-JE8iapy9P02sDZtIdZn4FO_mkTQT3N-9K4"

service_account_json = 'TUTAJ_WKLEJ_CAŁY_JSON_JAKO_JEDNA_LINIA'
```

### Przykład poprawnego formatu:

```toml
SPREADSHEET_ID = "TWOJE_ID_ARKUSZA"

service_account_json = '{"type":"service_account","project_id":"TWOJ_PROJEKT","private_key_id":"TWOJ_KEY_ID","private_key":"-----BEGIN PRIVATE KEY-----\\nTWOJ_KLUCZ_Z_PLIKU_JSON\\n-----END PRIVATE KEY-----\\n","client_email":"TWOJ_EMAIL@PROJECT.iam.gserviceaccount.com","client_id":"TWOJ_CLIENT_ID","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/ZAKODOWANY_EMAIL","universe_domain":"googleapis.com"}'
```

**KLUCZOWE PUNKTY:**
- Całość w **pojedynczych cudzysłowach** `'...'`
- Jedna długa linia (bez nowych linii)
- `\\n` w kluczu prywatnym (podwójny backslash!)

### Krok 3: Zapisz i poczekaj

1. Kliknij **Save** w Streamlit Cloud
2. Poczekaj 30-60 sekund na restart aplikacji
3. Odśwież aplikację w przeglądarce

### Krok 4: Test połączenia

1. W aplikacji kliknij **"🧪 Testuj połączenie"**
2. Powinno pokazać: ✅ "Połączono! Arkusz ma X wierszy i Y kolumn"

---

## 🆘 Jeśli nadal nie działa

Wyślij mi:
1. Screenshot przycisku "🧪 Testuj połączenie" z wynikiem
2. Screenshot sekcji Secrets na Streamlit Cloud (ukryj sam klucz prywatny, ale pokaż strukturę)
3. Pełny komunikat błędu

---

## 📝 Dlaczego taki format?

Poprzedni format z TOML powodował problemy z parsowaniem wieloliniowego klucza prywatnego.
Nowy format (JSON jako string) działa niezawodnie we wszystkich przypadkach.
