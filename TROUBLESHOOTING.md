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

**Przykład poprawnej konfiguracji (UWAGA: użyj POTRÓJNYCH cudzysłowów dla private_key!):**
```toml
[gsheets]
type = "service_account"
project_id = "steamlite-api"
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgk...(reszta klucza na wielu liniach)...encNWOg==
-----END PRIVATE KEY-----
"""
client_email = "steamlite-robot@steamlite-api.iam.gserviceaccount.com"
```

**KRYTYCZNE:** `private_key` MUSI być w potrójnych cudzysłowach `"""` bo zawiera wiele linii!

---

### ✅ Weryfikacja secrets na Streamlit Cloud

**NOWY FORMAT (PROSTSZY!):** Zamiast parsować poszczególne pola TOML, używamy całego JSON jako string.

**UWAGA:** Skopiuj całą zawartość z pliku `example_secrets.toml` (między znacznikami `===`).

Pełna zawartość secrets powinna wyglądać tak:

```toml
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"

service_account_json = '{"type":"service_account","project_id":"YOUR_PROJECT","private_key_id":"YOUR_KEY_ID","private_key":"-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY_HERE\\n-----END PRIVATE KEY-----\\n","client_email":"YOUR_EMAIL@PROJECT.iam.gserviceaccount.com",...}'
```

**JAK UZYSKAĆ POPRAWNĄ WARTOŚĆ:**
1. Otwórz plik `steamlite-api-ca337c69ec99.json`
2. Skopiuj **CAŁĄ** zawartość pliku
3. Usuń wszystkie nowe linie - zmień w jedną linię
4. Owinięto w pojedyncze cudzysłowy `'...'`
5. Upewnij się, że `\n` w `private_key` są zapisane jako `\\n` (podwójny backslash)

**WAŻNE:** 
- To jest CAŁY JSON service account jako jeden string
- Używamy pojedynczych cudzysłowów `'...'` żeby uniknąć problemów z escapowaniem
- `private_key` wewnątrz JSON ma `\\n` (podwójne backslash, nie pojedyncze!)
- Ten format ZAWSZE działa w Streamlit Cloud!

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
