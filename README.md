# Aplikacja do manualnego kodowania sentymentu i emocji

## Opis

Aplikacja Streamlit do manualnego kodowania sentymentu i emocji w tekstach z fake newsów.

## Struktura

```
sent_emo_app/
├── streamlit_app.py       # Główna aplikacja Streamlit
├── data_to_code.json      # Dane wejściowe (tylko $oid i text)
├── results/               # Folder z wynikami kodowania
├── requirements.txt       # Zależności Python
├── .streamlit/            # Konfiguracja Streamlit i secrets
└── README.md              # Instrukcja
```

## Uruchomienie

1. **Przygotowanie danych** (już wykonane):
   ```bash
   python prepare_data.py
   ```

2. **Uruchomienie aplikacji**:
   ```bash
   streamlit run streamlit_app.py
   ```

## Funkcjonalność

### Ekran startowy
- Wyświetla instrukcję
- Przycisk START do rozpoczęcia kodowania

### Ekran kodowania
- **Kodowanie w dwóch turach** dla każdego tekstu:
  1. **Sentyment** (3 kategorie):
     - Pozytywny
     - Negatywny
     - Neutralny
  
  2. **Emocje** (8 kategorii):
     - Radość (joy)
     - Zaufanie (trust)
     - Oczekiwanie (anticipation)
     - Zaskoczenie (surprise)
     - Strach (fear)
     - Smutek (sadness)
     - Wstręt (disgust)
     - Złość (anger)

- **Skala natężenia** dla każdej kategorii:
  - 0: Brak/Niskie
  - 1: Średnie
  - 2: Wysokie

- **Proces kodowania**:
  - 20 elementów w jednej sesji
  - Wyświetlanie tekstu na górze
  - Suwaki do oceny na dole
  - Pasek postępu

### Ekran końcowy
- Podsumowanie sesji
- Informacja o zapisanych wynikach
- Możliwość rozpoczęcia nowej sesji

## Format wyników

Wyniki są zapisywane w folderze `results/` jako pliki JSON z nazwą:
```
manual_coding_YYYYMMDD_HHMMSS.json
```

Format pojedynczego rekordu:
```json
{
  "$oid": "67421ac51c0f4a032d63e507",
  "text": "Tekst do zakodowania...",
  "manual_sentiment": {
    "positive": 0,
    "negative": 1,
    "neutral": 2
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

## Wymagania

- streamlit
- json (standardowa biblioteka)
- pathlib (standardowa biblioteka)

## Uwagi

- Aplikacja koduje pierwsze 20 elementów z pliku `data_to_code.json`
- Każda sesja tworzy nowy plik wynikowy
- Wyniki są zapisywane automatycznie po zakończeniu sesji
