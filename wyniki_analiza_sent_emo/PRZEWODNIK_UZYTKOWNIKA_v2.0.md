# Przewodnik użytkownika - Aplikacja Analiza Zgodności v2.0

## 🎯 Najważniejsze zmiany

### Nowa skala kodowania: 0-2
- **0** = Brak
- **1** = Obecna (nawet śladowa)
- **2** = Obecność silna

### Konfigurowalne progi konwersji
Możesz teraz dostosować sposób konwersji prawdopodobieństwa (0-1) z systemów automatycznych na skalę 0-2!

---

## 🚀 Szybki start

### 1. Uruchomienie aplikacji
```bash
cd app/wer_llm/sent_emo_app/wyniki_analiza_sent_emo
streamlit run analiza_zgodnosci_app.py
```

### 2. Pierwsze uruchomienie
Aplikacja automatycznie:
- Wczyta dane z domyślnej lokalizacji
- Ustawi progi na wartości domyślne (0.15 i 0.75)
- Połączy się z Google Sheets (jeśli skonfigurowane)

### 3. Podstawowa analiza
1. Wybierz typ analizy w panelu bocznym
2. Wybierz źródła do porównania
3. Przeglądaj wyniki w zakładkach

---

## ⚙️ Konfiguracja progów konwersji

### Gdzie znaleźć?
Panel boczny → Górna sekcja "⚙️ Progi konwersji skali (0-1 → 0-2)"

### Jak to działa?

#### SENT_EMO i SENT_EMO_LLM generują prawdopodobieństwa 0-1
Przykład:
- `sentyment_positive = 0.75` (75% prawdopodobieństwo pozytywnego sentymentu)

#### Aplikacja konwertuje to na skalę 0-2 używając progów:

**Domyślne progi:**
- Dolny próg: **0.15** (próg między "brak" a "obecna")
- Górny próg: **0.75** (próg między "obecna" a "silna")

**Przykład konwersji z domyślnymi progami:**
```
0.10 → 0 (brak)        [< 0.15]
0.45 → 1 (obecna)      [0.15-0.75]
0.85 → 2 (silna)       [≥ 0.75]
```

### Kiedy zmienić progi?

#### 🎯 Wysoka precyzja (konserwatywne podejście)
**Sytuacja:** Chcesz wykrywać tylko wyraźną obecność
```
Dolny próg: 0.50
Górny próg: 0.80
```
**Efekt:** Więcej "0" (brak), mniej fałszywych alarmów

#### 🎯 Wysoka czułość (liberalne podejście)
**Sytuacja:** Chcesz wykrywać nawet słabe sygnały
```
Dolny próg: 0.20
Górny próg: 0.50
```
**Efekt:** Więcej "1" i "2", wykrywasz więcej przypadków

#### 🎯 Zbalansowane wykrywanie (domyślne)
**Sytuacja:** Standardowa analiza z umiarkowaną czułością
```
Dolny próg: 0.15
Górny próg: 0.75
```
**Efekt:** Zbalansowane wykrywanie z większością przypadków w kategorii "obecna"

### Niezależne progi dla SENT_EMO i SENT_EMO_LLM

**Możesz ustawić różne progi dla każdego systemu!**

Przykład:
- SENT_EMO: progi 0.30 i 0.70 (bardziej liberalne)
- SENT_EMO_LLM: progi 0.40 i 0.80 (bardziej konserwatywne)

Dlaczego? Bo systemy mogą mieć różne charakterystyki:
- SENT_EMO może być bardziej "pewny siebie" (wyższe wartości)
- SENT_EMO_LLM może być bardziej "ostrożny" (niższe wartości)

---

## 🔄 Zastosowanie nowych progów

### Kiedy potrzebujesz?
Po każdej zmianie progów musisz zastosować je klikając **"🔄 Zastosuj nowe progi"**

### Co się dzieje?
1. Aplikacja ponownie wczytuje surowe dane (0-1)
2. Stosuje nowe progi do konwersji
3. Przelicza wszystkie metryki
4. Aktualizuje wykresy

**⚠️ Ważne:** Bez kliknięcia tego przycisku, zmiany progów NIE będą widoczne w analizie!

---

## 📊 Interpretacja wyników z różnymi progami

### Przykład: Sentyment pozytywny

#### Dane automatyczne (SENT_EMO):
```
Post A: 0.25
Post B: 0.55
Post C: 0.85
```

#### Kodowanie manualne:
```
Post A: 0 (brak)
Post B: 1 (słaba)
Post C: 2 (silna)
```

#### Z progami 0.33 / 0.67:
```
Post A: 0 → zgodność ✓
Post B: 1 → zgodność ✓
Post C: 2 → zgodność ✓
Kappa = wysoka
```

#### Z progami 0.50 / 0.80:
```
Post A: 0 → zgodność ✓
Post B: 0 → NIEZGODNOŚĆ ✗ (manual=1, auto=0)
Post C: 1 → NIEZGODNOŚĆ ✗ (manual=2, auto=1)
Kappa = niska
```

### Wniosek
Progi wpływają na zgodność! Eksperymentuj, aby znaleźć optymalne wartości.

---

## 🎨 Wizualizacje z nowymi progami

### Wykresy rozproszenia
- Oś X i Y: skala 0-2
- Punkty na przekątnej = pełna zgodność
- Punkty dalej od przekątnej = większe rozbieżności

### Macierze konfuzji (3×3)
```
        Manual
        0   1   2
      ┌─────────┐
    0 │ ■   □   □ │
A   1 │ □   ■   □ │
u   2 │ □   □   ■ │
t     └─────────┘
o
```
- Przekątna = zgodność
- Poza przekątną = rozbieżności

### Rozkłady wartości
- Bezpośrednie porównanie częstości
- 3 słupki dla każdego źródła (0, 1, 2)
- Idealna zgodność = identyczne rozkłady

---

## 💡 Wskazówki praktyczne

### 1. Znajdź optymalne progi
```
1. Zacznij od domyślnych (0.33 / 0.67)
2. Sprawdź zgodność (Kappa, Alpha)
3. Jeśli niska:
   - Spróbuj różnych progów
   - Porównaj macierze konfuzji
   - Szukaj systematycznych różnic
4. Zapisz progi które dają najlepszą zgodność
```

### 2. Porównaj systemy
```
1. Ustaw takie same progi dla SENT_EMO i SENT_EMO_LLM
2. Porównaj ich zgodność z manualnym
3. Który system lepiej pasuje do manualnego kodowania?
```

### 3. Dostosuj do charakterystyki danych
```
- Dane z silnymi sygnałami → wyższe progi (0.4 / 0.8)
- Dane z subtelnym sygnałami → niższe progi (0.25 / 0.55)
- Zbalansowane dane → domyślne (0.33 / 0.67)
```

---

## ❓ Najczęściej zadawane pytania

### Q: Czy progi wpływają na dane manualne?
**A:** Nie! Dane manualne są już w skali 0-2 i nie są przetwarzane.

### Q: Czy mogę zapisać moje ulubione progi?
**A:** Obecnie nie, ale możesz je zanotować. Po ponownym uruchomieniu aplikacji wrócą do domyślnych.

### Q: Które progi wybrać?
**A:** To zależy od Twoich danych i celu analizy. Eksperymentuj i obserwuj zgodność.

### Q: Czy progi powinny być takie same dla sentymentu i emocji?
**A:** Niekoniecznie. Możesz ustawić różne progi dla każdego systemu (SENT_EMO vs SENT_EMO_LLM), ale te same progi są stosowane do wszystkich kategorii w ramach jednego systemu.

### Q: Co jeśli mam stare dane w skali 0-3?
**A:** Musisz je przekonwertować do skali 0-2 w Google Sheets przed użyciem tej wersji aplikacji. Zobacz CHANGELOG_v2.0 dla instrukcji migracji.

---

## 📞 Wsparcie

Problemy? Pytania?
1. Sprawdź CHANGELOG_v2.0_SKALA_0-2.md
2. Sprawdź README.md
3. Sprawdź logi w aplikacji (czerwone komunikaty)

---

## 📝 Notatki do eksperymentów

Użyj tej sekcji do zapisania swoich odkryć:

**Optymalne progi dla moich danych:**
```
SENT_EMO:
  - Dolny próg: _______
  - Górny próg: _______
  - Kappa z manual: _______

SENT_EMO_LLM:
  - Dolny próg: _______
  - Górny próg: _______
  - Kappa z manual: _______
```

**Obserwacje:**
- 
- 
- 

---

*Przewodnik utworzony: 2 grudnia 2025*
*Wersja aplikacji: 2.0*
