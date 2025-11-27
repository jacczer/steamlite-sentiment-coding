# 🔧 Troubleshooting - Aplikacja kodowania sentymentu

## 🚨 Problem: Dane nie zapisują się do Google Sheets

### Kroki diagnostyczne:

#### 1. **Sprawdź połączenie z Google Sheets**

Na ekranie startowym aplikacji kliknij przycisk **"🧪 Testuj połączenie"**.

Jeśli widzisz:
- ✅ **"Połączono!"** - połączenie działa, problem jest gdzie indziej
- ❌ **Błąd** - przejdź do sekcji "Rozwiązywanie błędów połączenia"

---

#### 2. **Sprawdź komunikaty podczas kodowania**

Podczas kodowania, po kliknięciu "✅ Zapisz i kontynuuj":

**A) Widzisz komunikat:** ✅ "Zapisano wiersz do arkusza"
   - Dane POWINNY być w arkuszu
   - Sprawdź czy przeglądasz właściwy arkusz (ID: `1ShqRuRy_-JE8iapy9P02sDZtIdZn4FO_mkTQT3N-9K4`)
   - Odśwież stronę Google Sheets (F5)

**B) Widzisz komunikat:** ❌ "Błąd zapisu..."
   - Rozwiń sekcję **"🔍 Debug - dane do zapisania"** (jeśli dostępna)
   - Skopiuj pełny komunikat błędu i przekaż developerowi

**C) Nie widzisz ŻADNEGO komunikatu:**
   - Problem z konfiguracją Streamlit Cloud
   - Przejdź do sekcji "Weryfikacja secrets"

---

### 🔍 Rozwiązywanie błędów połączenia

#### Błąd: "Brak konfiguracji 'gsheets' w secrets"

**Rozwiązanie:**
1. Wejdź na Streamlit Cloud: https://share.streamlit.io/
2. Znajdź swoją aplikację
3. Kliknij ⚙️ **Settings** → **Secrets**
4. Sprawdź czy w sekcji secrets jest blok `[gsheets]`
5. Jeśli nie ma - dodaj zawartość z pliku `example_secrets.toml`

---

#### Błąd: "Brak 'SPREADSHEET_ID' w secrets"

**Rozwiązanie:**
1. W secrets na Streamlit Cloud dodaj linię:
   ```toml
   SPREADSHEET_ID = "1ShqRuRy_-JE8iapy9P02sDZtIdZn4FO_mkTQT3N-9K4"
   ```
2. Zapisz secrets
3. Poczekaj ~30 sekund na restart aplikacji

---

#### Błąd: "Failed to open spreadsheet" lub "Insufficient permissions"

**Przyczyna:** Service account nie ma dostępu do arkusza

**Rozwiązanie:**
1. Otwórz arkusz Google Sheets: 
   ```
   https://docs.google.com/spreadsheets/d/1ShqRuRy_-JE8iapy9P02sDZtIdZn4FO_mkTQT3N-9K4/edit
   ```
2. Kliknij **Share** (Udostępnij)
3. Sprawdź czy na liście jest email:
   ```
   steamlite-robot@steamlite-api.iam.gserviceaccount.com
   ```
4. Jeśli NIE MA - dodaj go z uprawnieniami **Editor**
5. Jeśli JEST, ale z uprawnieniami **Viewer** - zmień na **Editor**

---

#### Błąd: "Invalid credentials"

**Przyczyna:** Błąd w konfiguracji service account w secrets

**Rozwiązanie:**
1. Otwórz plik `steamlite-api-ca337c69ec99.json`
2. Skopiuj **całą** zawartość pliku
3. Na Streamlit Cloud w sekcji Secrets, w bloku `[gsheets]` upewnij się, że:
   - `private_key` zawiera **cały** klucz (wieloliniowy tekst w cudzysłowach)
   - Klucz zaczyna się od `-----BEGIN PRIVATE KEY-----\n`
   - Klucz kończy się na `\n-----END PRIVATE KEY-----\n`
   - Znaki nowej linii są zapisane jako `\n` (nie rzeczywiste nowe linie)

**Przykład poprawnej konfiguracji:**
```toml
[gsheets]
type = "service_account"
project_id = "steamlite-api"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgk...(reszta klucza)...encNWOg==\n-----END PRIVATE KEY-----\n"
client_email = "steamlite-robot@steamlite-api.iam.gserviceaccount.com"
```

---

### ✅ Weryfikacja secrets na Streamlit Cloud

Pełna zawartość secrets powinna wyglądać tak:

```toml
[gsheets]
type = "service_account"
project_id = "steamlite-api"
private_key_id = "ca337c69ec99675a43a890cf3f5e8e7ca1fdd764"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQC3Z8YctQyftSUx\n9xmL65hcgH1XxRJNtyClbTpnXh68S4NU3ezE4o6lauli77tzzQzuYCS3/bV94Mui\nZOolfnZozSfZChSPj6oVeuDiNsYR0ZSNNq9BRsMqvhEcTWF7UwFtCiRvEbEBzYAX\nRD4Es1f4JrGA9+R2VeE9WUk0I030BoZPxXZh17jTYchk1FacwL9kfenWpZHUgHWU\nOiJTWna0ouhMHepVUEqQVvJWvmv+wvG7u7IzDbhYeuFHjqZSr3me9UH1xLM16luz\nJaGHjWvyH405aqnJM3pgSDiJ0Ku9Dnimnmw8UwIqGqEkqWERI9FsjGLijpVo1GPz\nuQCjVpLbAgMBAAECggEARC4MxOE9NyXVFPUCBzTm6ARQFE/LlR5twXGQk5q2nFMK\nGIODoFGEq9PJvSDXs53Xn8oX/FoRnSDzMoSHUrbnd+BEXvfTWucSWHfcn9uy2C7s\nJW7dyctvhDUyES5m/byGvC1YC/4sqjnl00BoOcEeA78Gn6YHxUH5wJ+vifVR5lPh\nXmkQRtVVRPvpx6Qm9r7xRpUzF5ory0pIliusDAyac9H7FuV74LqUg7JwU3J1W78E\n4XVPVYuXKeRXaJF+rJacmmb7uatg3Y8YwNUmtGYze12VQYaRLWlGGpKevZ+lszed\nNtie2hXTsh1NHU2kzLu1sRh21gcUiH3k+qC+GnKl+QKBgQDh0qFR3Sk6WXggFdOd\nC4C5emjADRSdEBiG6pT8UWebQY7UyDg5dEn/JAuGetTsDBB7Hhn1Pood/9Gt8LGX\n7iZuqg32VkCruA5Kdw1ID8lQ0VMgPWjaK6tdkmlT95Bzu4qs2tJ2ATwxkSo8/GlD\nMKdN+cw+fRPsfIduwFwOB1/ElwKBgQDP6gyhLuPZ6/Y3eH+kN3vFFi271iQnpA1F\n1zGE39geygaATZkEsm2wLcYpdjsi7nABfdKnX67rOtWtODFDPuokjaioThRmYz5y\nryqV1Dl/6ZG2Y+uBlcsSqnO17MVb4XkzIoTRLwIzcb7Fc9h9Ao7AHIhuTXr4HSWH\nIGj4q5IYXQKBgQDKLZ0WwQ4vWnjtKP17phfKd6ifAVcKQ6Xh7NYUjQFYhDpPkS6d\nadryHiBfd0t4RljfEZUl96cKssXUmCE4KBSqkX/Mo25lD3Vj//CZKuEPhUmKHNDq\nO5zCOtooPgZLR4YhugwhcHum2RPa5BWN/Vpcup+89pjG6rsKUhhYywtX4wKBgQCl\neeITZv5xsxuDiqQMTxxy//PmS8j6w9bMfzkqR/36g1ApTZk748bpMYVF+pOWea8r\ngLjn/X96OJlYBCExJCG2dgiF657Q3qwVGtUJ6p7Y70zJnT0TJeU6Ne9iG8/4ELwl\ntpN+6asWxrDO9iSXWjHDNPJg18nHL2tu4JyrTeI5AQKBgQCq5t0Thh3de+isI8/B\neyPh30iy/0BxQF+Kjh6z6+qLJekCMIar6o1sIWoJnW52Kws4VswtJ9xCiCWalOcK\nmxsWlNC8eU4GRkv6D5qQgxEmYAuyWR3CnAIJqdUhokLDIJed3pLBqO2uF1rFYhuf\nNhfjY3zIBFqQvKff7wmencNWOg==\n-----END PRIVATE KEY-----\n"
client_email = "steamlite-robot@steamlite-api.iam.gserviceaccount.com"
client_id = "100499984497557336964"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/steamlite-robot%40steamlite-api.iam.gserviceaccount.com"
universe_domain = "googleapis.com"

SPREADSHEET_ID = "1ShqRuRy_-JE8iapy9P02sDZtIdZn4FO_mkTQT3N-9K4"
```

---

### 🧪 Test lokalny

Jeśli chcesz przetestować aplikację lokalnie:

1. Upewnij się, że istnieje plik `.streamlit/secrets.toml` (ignorowany przez Git)
2. Skopiuj do niego zawartość z powyższej sekcji
3. Uruchom aplikację:
   ```bash
   streamlit run app.py
   ```
4. Kliknij "🧪 Testuj połączenie"

---

### 📊 Sprawdzanie czy dane rzeczywiście nie zapisują się

1. Otwórz arkusz: https://docs.google.com/spreadsheets/d/1ShqRuRy_-JE8iapy9P02sDZtIdZn4FO_mkTQT3N-9K4/edit
2. Sprawdź czy pierwszy wiersz ma nagłówki:
   ```
   timestamp | coder_id | oid | text | positive | negative | neutral | joy | trust | anticipation | surprise | fear | sadness | disgust | anger
   ```
3. Sprawdź czy są jakieś wiersze poniżej nagłówków
4. Jeśli są wiersze - dane ZAPISUJĄ SIĘ! (może tylko nie widać ich od razu - odśwież stronę)
5. Jeśli nie ma wierszy - użyj diagnostyki powyżej

---

### 🆘 Nadal nie działa?

Skontaktuj się z developerem i dostarcz:

1. Screenshot komunikatów błędów z aplikacji
2. Screenshot sekcji "🔍 Debug - dane do zapisania" (jeśli widoczna)
3. Informację czy przycisk "🧪 Testuj połączenie" działa
4. Screenshot arkusza Google Sheets (pokaż nagłówki i pierwsze wiersze)

---

## ✅ Checklist przed zgłoszeniem problemu

- [ ] Kliknąłem "🧪 Testuj połączenie" - czy działa?
- [ ] Odświeżyłem stronę Google Sheets (F5)
- [ ] Sprawdziłem czy przeglądam właściwy arkusz (ID kończy się na `-9K4`)
- [ ] Service account (`steamlite-robot@...`) ma uprawnienia **Editor** do arkusza
- [ ] W secrets na Streamlit Cloud jest `SPREADSHEET_ID`
- [ ] W secrets jest cały blok `[gsheets]` z `private_key`
- [ ] Poczekałem 30 sekund po zmianie secrets (restart aplikacji)
