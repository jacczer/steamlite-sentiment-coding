# 🔑 KONFIGURACJA SECRETS NA STREAMLIT CLOUD

## ⚠️ WAŻNE: Użyj pliku z danymi które Ci wysłałem!

Masz plik `steamlite-api-ca337c69ec99.json` z prawdziwymi danymi.

## 📋 Kroki konfiguracji:

### Krok 1: Przygotuj dane z pliku JSON

1. Otwórz plik `steamlite-api-ca337c69ec99.json` w edytorze tekstu (Notatnik, VS Code, itp.)
2. Znajdź każdą wartość, którą będziesz wklejać do Streamlit Cloud:
   - `project_id`
   - `private_key_id`
   - `private_key` (cały blok z BEGIN/END)
   - `client_email`
   - `client_id`
   - `client_x509_cert_url`

### Krok 2: Skonfiguruj secrets na Streamlit Cloud

1. Wejdź na: https://share.streamlit.io/
2. Znajdź swoją aplikację
3. Kliknij **⚙️ Settings** → **Secrets**
4. **USUŃ całą obecną zawartość** w sekcji Secrets
5. **WKLEJ** dokładnie to (zamieniając wartości z pliku `steamlite-api-ca337c69ec99.json`):

```toml
SPREADSHEET_ID = "1ShqRuRy_-JE8iapy9P02sDZtIdZn4FO_mkTQT3N-9K4"

type = "service_account"
project_id = "WKLEJ_Z_JSON"
private_key_id = "WKLEJ_Z_JSON"
private_key = """-----BEGIN PRIVATE KEY-----
WKLEJ_TUTAJ_KLUCZ_WIELOLINIOWO
-----END PRIVATE KEY-----
"""
client_email = "WKLEJ_Z_JSON"
client_id = "WKLEJ_Z_JSON"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "WKLEJ_Z_JSON"
universe_domain = "googleapis.com"
```

**KLUCZOWE PUNKTY:**
- Każde pole w osobnej linii (format TOML)
- `private_key` w **potrójnych cudzysłowach** `"""..."""` - może być wieloliniowy!
- **Skopiuj klucz prywatny z JSON dokładnie tak jak jest** (z nowymi liniami)

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

Streamlit Cloud wymaga formatu TOML (nie pozwala na wieloliniowy JSON).
Format z osobnymi polami i potrójnymi cudzysłowami dla `private_key` działa niezawodnie.

## 💡 PRZYKŁAD Z PRAWDZIWYMI DANYMI

Jeśli w Twoim pliku JSON jest:
```json
{
  "project_id": "steamlite-api",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBg...\n-----END PRIVATE KEY-----\n"
}
```

To w Streamlit Cloud wklejasz:
```toml
project_id = "steamlite-api"
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBg...
-----END PRIVATE KEY-----
"""
```

**Uwaga:** W JSON klucz ma `\n` - w TOML po prostu **skopiuj z nowymi liniami** między potrójne cudzysłowy!
