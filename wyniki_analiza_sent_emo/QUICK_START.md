# Quick Start - Analiza Zgodności Kodowania

## 🚀 Szybki start (5 minut)

### 1. Instalacja (1 min)

```bash
cd app/wer_llm/sent_emo_app/wyniki_analiza_sent_emo
pip install -r requirements.txt
```

### 2. Konfiguracja Google Sheets (2 min)

```bash
# Utwórz katalog .streamlit
mkdir .streamlit

# Skopiuj przykładową konfigurację
cp secrets.toml.example .streamlit/secrets.toml

# Edytuj plik i wpisz swoje dane
# notepad .streamlit/secrets.toml  (Windows)
# nano .streamlit/secrets.toml     (Linux/Mac)
```

Potrzebne dane:
- `SPREADSHEET_ID` - ID arkusza Google Sheets (z URL)
- Dane service account (z pliku JSON pobranego z Google Cloud Console)

### 3. Uruchomienie (1 min)

```bash
streamlit run analiza_zgodnosci_app.py
```

### 4. Pierwsze kroki w aplikacji (1 min)

1. **Panel boczny:** Kliknij "🔄 Wczytaj dane"
2. **Poczekaj** na potwierdzenie wczytania
3. **Sprawdź** status połączenia (powinny być dwa ✓)
4. **Przeglądaj** zakładki z wynikami

## ✅ Lista kontrolna

Przed pierwszym użyciem sprawdź:

- [ ] Zainstalowane wszystkie pakiety (`pip install -r requirements.txt`)
- [ ] Utworzony plik `.streamlit/secrets.toml`
- [ ] Wypełnione `SPREADSHEET_ID` w secrets
- [ ] Service account ma dostęp do arkusza Google Sheets
- [ ] Plik Parquet istnieje i zawiera wymagane kolumny
- [ ] Google Sheets zawiera dane z kodowaniem manualnym

## 🎯 Typowy workflow

```
1. Wczytaj dane
   └─> Panel boczny → "🔄 Wczytaj dane"

2. Zastosuj filtry (opcjonalnie)
   └─> Panel boczny → Filtry danych

3. Wybierz typ analizy
   └─> Panel boczny → Opcje analizy

4. Przeglądaj wyniki
   └─> Zakładki: Przegląd / Szczegóły / Scatter / Macierze

5. Eksportuj wykresy
   └─> Kliknij ikonę 📷 w prawym górnym rogu wykresu
```

## 📊 Przykładowe pytania analityczne

Aplikacja odpowie na pytania typu:

- ❓ Jak dobrze SENT_EMO zgadza się z kodowaniem manualnym?
- ❓ Która emocja jest najtrudniejsza do automatycznego kodowania?
- ❓ Czy LLM (SENT_EMO_LLM) jest lepszy niż SENT_EMO?
- ❓ Dla jakich poziomów natężenia (0-3) jest najwięcej błędów?
- ❓ Czy zgodność różni się między różnymi źródłami danych?

## 🆘 Najczęstsze problemy

### ❌ "Brak SPREADSHEET_ID w secrets"
**Rozwiązanie:** Sprawdź plik `.streamlit/secrets.toml`

### ❌ "Błąd połączenia z Google Sheets"
**Rozwiązanie:** 
- Sprawdź czy service account ma dostęp do arkusza
- Zweryfikuj poprawność private_key (uważaj na `\n`)

### ❌ "Brak wspólnych rekordów"
**Rozwiązanie:**
- Sprawdź czy `post_id` (Parquet) = `oid` (Google Sheets)
- Upewnij się, że oid są typu string, nie number

### ❌ Import error
**Rozwiązanie:**
```bash
pip install --upgrade -r requirements.txt
```

## 🧪 Test instalacji

Uruchom test weryfikacyjny:

```bash
python test_metrics.py
```

Jeśli wszystkie testy przechodzą (✓), instalacja jest poprawna.

## 📖 Więcej informacji

- **[INSTRUKCJA.md](INSTRUKCJA.md)** - pełna instrukcja
- **[README.md](README.md)** - dokumentacja techniczna
- **[PODSUMOWANIE.md](PODSUMOWANIE.md)** - status projektu

## 🎓 Pierwszy raz z aplikacją?

1. **Zacznij od zakładki "📊 Przegląd metryk"**
   - Zobacz wszystkie wskaźniki w jednym miejscu
   
2. **Przejdź do "🎯 Szczegółowa analiza"**
   - Wybierz konkretną kategorię do zbadania
   
3. **Sprawdź "📉 Wykresy rozproszenia"**
   - Zobacz relacje między kodowaniem manualnym a automatycznym
   
4. **Przeanalizuj "📋 Macierze konfuzji"**
   - Zidentyfikuj najczęstsze błędy kodowania

## 💡 Pro tips

- 🔄 Dane z Google Sheets aktualizują się na żywo - odśwież przyciskiem "Wczytaj dane"
- 📊 Używaj filtrów aby analizować konkretne podzbiory
- 🎯 Porównuj zawsze oba narzędzia (SENT_EMO i SENT_EMO_LLM)
- 📈 Eksportuj wykresy klikając ikonę aparatu
- 🔬 Zwracaj uwagę na przedziały ufności (CI) dla ICC

---

**Gotowy? Uruchom aplikację:**

```bash
streamlit run analiza_zgodnosci_app.py
```

🎉 **Powodzenia w analizie!**
