"""
Aplikacja Streamlit do manualnego kodowania sentymentu i emocji.
#cd app\wer_llm\sent_emo_app
streamlit run app.py
"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime, timezone
import gspread
from google.oauth2.service_account import Credentials

# Configuration
DATA_FILE = Path(__file__).parent / "data_to_code.json"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Google Sheets configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


@st.cache_resource(ttl=60)  # Cache tylko na 60 sekund, potem odświeża
def get_worksheet(_force_refresh=None):
    """
    Establish connection to Google Sheets using service account credentials.
    Returns the first worksheet of the spreadsheet.
    """
    try:
        # Check if secrets are available
        if "SPREADSHEET_ID" not in st.secrets:
            st.error("❌ Brak 'SPREADSHEET_ID' w secrets!")
            return None
        
        # Build credentials dict - try different formats
        creds_info = None
        
        # Method 1: Full JSON as string (for local development)
        if "service_account_json" in st.secrets:
            import json
            creds_info = json.loads(st.secrets["service_account_json"])
        
        # Method 2: Individual fields as TOML (for Streamlit Cloud)
        elif "type" in st.secrets and "project_id" in st.secrets:
            creds_info = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key_id": st.secrets["private_key_id"],
                "private_key": st.secrets["private_key"],
                "client_email": st.secrets["client_email"],
                "client_id": st.secrets["client_id"],
                "auth_uri": st.secrets["auth_uri"],
                "token_uri": st.secrets["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["client_x509_cert_url"],
                "universe_domain": st.secrets.get("universe_domain", "googleapis.com")
            }
        
        # Method 3: Dict with fields (backward compatibility)
        elif "gsheets" in st.secrets:
            creds_info = dict(st.secrets["gsheets"])
        
        if not creds_info:
            st.error("❌ Brak konfiguracji credentials w secrets! Dodaj 'service_account_json' (JSON string) lub osobne pola TOML (type, project_id, private_key, etc.)")
            return None
        
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
        sh = client.open_by_key(SPREADSHEET_ID)
        worksheet = sh.sheet1  # pierwszy arkusz (first worksheet)
        
        st.success(f"✅ Połączono z arkuszem: {sh.title}")
        return worksheet
    except Exception as e:
        st.error(f"❌ Błąd połączenia z Google Sheets: {type(e).__name__}: {str(e)}")
        import traceback
        st.error(f"Szczegóły: {traceback.format_exc()}")
        return None


def save_to_google_sheets(oid, text, sentiment_values, emotion_values, coder_id="unknown"):
    """
    Save coding results to Google Sheets.
    Appends a new row with all coding information.
    """
    try:
        ws = get_worksheet()
        if ws is None:
            st.error("❌ Nie można zapisać - brak połączenia z arkuszem")
            return False
        
        # Use timezone-aware datetime
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Prepare row data: [timestamp, coder_id, oid, text, sentiment values, emotion values]
        row = [
            timestamp,
            str(coder_id),
            str(oid),
            str(text)[:500],  # Limit text length to 500 chars
            # Sentiment values
            int(sentiment_values.get("positive", 0)),
            int(sentiment_values.get("negative", 0)),
            int(sentiment_values.get("neutral", 0)),
            # Emotion values
            int(emotion_values.get("joy", 0)),
            int(emotion_values.get("trust", 0)),
            int(emotion_values.get("anticipation", 0)),
            int(emotion_values.get("surprise", 0)),
            int(emotion_values.get("fear", 0)),
            int(emotion_values.get("sadness", 0)),
            int(emotion_values.get("disgust", 0)),
            int(emotion_values.get("anger", 0))
        ]
        
        # Debug: Show what we're trying to save
        with st.expander("🔍 Debug - dane do zapisania", expanded=False):
            st.write("Przygotowany wiersz:", row)
            st.write("Liczba kolumn:", len(row))
        
        # Append row to sheet
        ws.append_row(row, value_input_option='USER_ENTERED')
        
        st.success(f"✅ Zapisano wiersz do arkusza (timestamp: {timestamp})")
        return True
        
    except Exception as e:
        st.error(f"❌ Błąd zapisu do Google Sheets: {type(e).__name__}")
        st.error(f"Szczegóły: {str(e)}")
        import traceback
        st.error(f"Stack trace: {traceback.format_exc()}")
        return False


# Sentiment and emotion categories
SENTIMENTS = ["positive", "negative", "neutral"]
EMOTIONS = ["joy", "trust", "anticipation", "surprise", "fear", "sadness", "disgust", "anger"]

# Polish labels for sentiment and emotions
SENTIMENT_LABELS_PL = {
    "positive": "Pozytywny",
    "negative": "Negatywny", 
    "neutral": "Neutralny"
}

EMOTION_LABELS_PL = {
    "joy": "Radość",
    "trust": "Zaufanie",
    "anticipation": "Oczekiwanie",
    "surprise": "Zaskoczenie",
    "fear": "Strach",
    "sadness": "Smutek",
    "disgust": "Wstręt",
    "anger": "Złość"
}

# Scale labels
SCALE_LABELS = {
    0: "Brak/Niskie",
    1: "Średnie",
    2: "Wysokie"
}


def load_data():
    """Load data to code from JSON file."""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def initialize_session():
    """Initialize session state variables."""
    if 'screen' not in st.session_state:
        st.session_state.screen = 'start'
    
    if 'data' not in st.session_state:
        st.session_state.data = load_data()
    
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    
    if 'session_elements' not in st.session_state:
        # Select 20 elements for this session
        st.session_state.session_elements = st.session_state.data[:20]
    
    if 'coding_stage' not in st.session_state:
        st.session_state.coding_stage = 'sentiment'  # 'sentiment' or 'emotion'
    
    if 'results' not in st.session_state:
        st.session_state.results = []
    
    if 'current_coding' not in st.session_state:
        st.session_state.current_coding = {
            'sentiment': {},
            'emotion': {}
        }
    
    if 'coder_id' not in st.session_state:
        st.session_state.coder_id = ""


def start_screen():
    """Display start screen."""
    st.title("🎯 Aplikacja do kodowania sentymentu i emocji")
    
    st.markdown("""
    ### Witamy w aplikacji do manualnego kodowania!
    
    **Instrukcja:**
    1. W tej sesji zakodujemy **20 elementów tekstowych**
    2. Dla każdego tekstu zakodujemy:
       - **Sentyment** (3 kategorie: pozytywny, negatywny, neutralny)
       - **Emocje** (8 kategorii: radość, zaufanie, oczekiwanie, zaskoczenie, strach, smutek, wstręt, złość)
    3. Dla każdej kategorii określ natężenie na skali:
       - **Brak/Niskie** (0)
       - **Średnie** (1)
       - **Wysokie** (2)
    """)
    
    st.markdown("---")
    
    # Test connection button
    st.markdown("### 🔌 Test połączenia z Google Sheets")
    col_test1, col_test2, col_test3 = st.columns([1, 1, 1])
    with col_test1:
        if st.button("🔄 Wyczyść cache", use_container_width=True):
            st.cache_resource.clear()
            st.success("Cache wyczyszczony! Kliknij 'Testuj połączenie'")
            st.rerun()
    with col_test2:
        if st.button("🧪 Testuj połączenie", use_container_width=True):
            # Force fresh connection by clearing cache first
            st.cache_resource.clear()
            with st.spinner("Sprawdzam połączenie..."):
                ws = get_worksheet()
                if ws:
                    try:
                        row_count = ws.row_count
                        col_count = ws.col_count
                        st.success(f"✅ Połączono! Arkusz ma {row_count} wierszy i {col_count} kolumn")
                        st.info(f"📊 Nazwa arkusza: {ws.title}")
                    except Exception as e:
                        st.error(f"❌ Błąd odczytu arkusza: {e}")
    
    st.markdown("---")
    
    # Coder ID input
    st.markdown("### 👤 Identyfikacja kodera")
    coder_id = st.text_input(
        "Podaj swój identyfikator (np. inicjały):",
        placeholder="np. JK, AM, PW",
        max_chars=20,
        help="Ten identyfikator będzie zapisany wraz z Twoimi kodowaniami"
    )
    
    st.markdown("---")
    st.markdown("**Kliknij przycisk START, aby rozpocząć kodowanie.**")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 START", use_container_width=True, type="primary"):
            if not coder_id.strip():
                st.warning("⚠️ Proszę podać identyfikator przed rozpoczęciem!")
            else:
                st.session_state.coder_id = coder_id.strip()
                st.session_state.screen = 'coding'
                st.rerun()


def coding_screen():
    """Display coding screen."""
    current_element = st.session_state.session_elements[st.session_state.current_index]
    progress = st.session_state.current_index + 1
    
    # Progress indicator
    st.progress(progress / 20)
    st.caption(f"Element {progress} / 20")
    
    # Display text
    st.markdown("### 📄 Tekst do zakodowania:")
    st.markdown(f"<div style='background-color: #0e1117; padding: 20px; border-radius: 5px; border-left: 5px solid #1f77b4;'><p style='color: white; font-size: 16px; line-height: 1.6;'>{current_element['text']}</p></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Coding stage: Sentiment or Emotion
    if st.session_state.coding_stage == 'sentiment':
        sentiment_coding_ui()
    else:
        emotion_coding_ui()


def sentiment_coding_ui():
    """UI for sentiment coding."""
    st.markdown("### 😊😐😢 Kodowanie sentymentu")
    st.markdown("**Określ natężenie każdego typu sentymentu:**")
    
    # Scale description at the top
    st.markdown("""
    <div style='display: flex; justify-content: space-between; padding: 0 10px; margin-bottom: 5px;'>
        <span style='color: #ffffff;'><strong>0</strong><br/>Brak/Niskie</span>
        <span style='color: #ffffff;'><strong>1</strong><br/>Średnie</span>
        <span style='color: #ffffff;'><strong>2</strong><br/>Wysokie</span>
    </div>
    """, unsafe_allow_html=True)
    
    sentiment_values = {}
    
    for sentiment in SENTIMENTS:
        st.markdown(f"**{SENTIMENT_LABELS_PL[sentiment]}:**")
        value = st.slider(
            f"slider_{sentiment}",
            min_value=0,
            max_value=2,
            value=0,
            step=1,
            key=f"sentiment_{sentiment}",
            label_visibility="collapsed"
        )
        sentiment_values[sentiment] = value
    
    # Scale description at the bottom
    st.markdown("""
    <div style='display: flex; justify-content: space-between; padding: 0 10px; margin-top: 5px;'>
        <span style='color: #ffffff;'><strong>0</strong><br/>Brak/Niskie</span>
        <span style='color: #ffffff;'><strong>1</strong><br/>Średnie</span>
        <span style='color: #ffffff;'><strong>2</strong><br/>Wysokie</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("➡️ Dalej do emocji", use_container_width=True, type="primary"):
            st.session_state.current_coding['sentiment'] = sentiment_values
            st.session_state.coding_stage = 'emotion'
            st.rerun()


def emotion_coding_ui():
    """UI for emotion coding."""
    st.markdown("### 🎭 Kodowanie emocji")
    st.markdown("**Określ natężenie każdej emocji:**")
    
    # Scale description at the top
    st.markdown("""
    <div style='display: flex; justify-content: space-between; padding: 0 10px; margin-bottom: 5px;'>
        <span style='color: #ffffff;'><strong>0</strong><br/>Brak/Niskie</span>
        <span style='color: #ffffff;'><strong>1</strong><br/>Średnie</span>
        <span style='color: #ffffff;'><strong>2</strong><br/>Wysokie</span>
    </div>
    """, unsafe_allow_html=True)
    
    emotion_values = {}
    
    for emotion in EMOTIONS:
        st.markdown(f"**{EMOTION_LABELS_PL[emotion]}:**")
        value = st.slider(
            f"slider_{emotion}",
            min_value=0,
            max_value=2,
            value=0,
            step=1,
            key=f"emotion_{emotion}",
            label_visibility="collapsed"
        )
        emotion_values[emotion] = value
    
    # Scale description at the bottom
    st.markdown("""
    <div style='display: flex; justify-content: space-between; padding: 0 10px; margin-top: 5px;'>
        <span style='color: #ffffff;'><strong>0</strong><br/>Brak/Niskie</span>
        <span style='color: #ffffff;'><strong>1</strong><br/>Średnie</span>
        <span style='color: #ffffff;'><strong>2</strong><br/>Wysokie</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("✅ Zapisz i kontynuuj", use_container_width=True, type="primary"):
            # Save current coding
            current_element = st.session_state.session_elements[st.session_state.current_index]
            
            # Save to Google Sheets immediately
            success = save_to_google_sheets(
                oid=current_element["$oid"],
                text=current_element["text"],
                sentiment_values=st.session_state.current_coding['sentiment'],
                emotion_values=emotion_values,
                coder_id=st.session_state.coder_id
            )
            
            if success:
                st.success("✅ Zapisano do Google Sheets!", icon="✅")
            
            # Also save to local results for backup (optional)
            result = {
                "$oid": current_element["$oid"],
                "text": current_element["text"],
                "manual_sentiment": st.session_state.current_coding['sentiment'],
                "manual_emotion": emotion_values
            }
            st.session_state.results.append(result)
            
            # Reset for next element
            st.session_state.current_coding = {'sentiment': {}, 'emotion': {}}
            st.session_state.coding_stage = 'sentiment'
            st.session_state.current_index += 1
            
            # Check if session is complete
            if st.session_state.current_index >= 20:
                save_results()  # Local backup
                st.session_state.screen = 'end'
            
            st.rerun()


def save_results():
    """
    Save coding results to JSON file (LOCAL BACKUP ONLY).
    Primary data storage is Google Sheets.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RESULTS_DIR / f"manual_coding_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.results, f, ensure_ascii=False, indent=2)
    
    st.session_state.results_file = output_file


def end_screen():
    """Display end screen."""
    st.title("🎉 Gratulacje!")
    
    st.markdown("""
    ### Zakończyłeś kodowanie!
    
    Pomyślnie zakodowano **20 elementów**.
    """)
    
    st.success(f"✅ Wyniki zapisano w pliku: `{st.session_state.results_file.name}`")
    
    st.markdown("---")
    
    # Display summary
    st.markdown("### 📊 Podsumowanie sesji:")
    st.metric("Zakodowane elementy", "20")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Nowa sesja", use_container_width=True, type="primary"):
            # Reset session
            st.session_state.clear()
            st.rerun()


def main():
    """Main application logic."""
    st.set_page_config(
        page_title="Kodowanie sentymentu i emocji",
        page_icon="🎯",
        layout="wide"
    )
    
    initialize_session()
    
    # Route to appropriate screen
    if st.session_state.screen == 'start':
        start_screen()
    elif st.session_state.screen == 'coding':
        coding_screen()
    elif st.session_state.screen == 'end':
        end_screen()


if __name__ == "__main__":
    main()
