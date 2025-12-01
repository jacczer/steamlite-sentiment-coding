"""
Aplikacja Streamlit do manualnego kodowania sentymentu i emocji.
#cd app/wer_llm/sent_emo_app
streamlit run sent_emo_app.py
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

# Definitions for tooltips
DEFINITIONS = {
    "sentiments": {
        "positive": "Ogólny wydźwięk afirmatywny, aprobatywny, pochwalny wobec opisywanego obiektu, osoby, grupy lub sytuacji.",
        "negative": "Ogólny wydźwięk krytyczny, potępiający, pejoratywny, deprecjonujący.",
        "neutral": "Styl informacyjny, opisowy, pozbawiony wyraźnych markerów oceny; skupienie na faktach bez emocjonalnego komentarza."
    },
    "emotions": {
        "joy": "Reakcja na zysk lub osiągnięcie celu. Obejmuje spektrum od pogody ducha po ekstazę.",
        "trust": "Reakcja na sprzymierzeńca lub członka grupy. Obejmuje spektrum od akceptacji po podziw.",
        "anticipation": "Reakcja na nowe terytorium lub przyszłe zdarzenie. Obejmuje spektrum od czujności po ekscytację.",
        "surprise": "Reakcja na nagły, nieoczekiwany bodziec. Obejmuje spektrum od zdziwienia po osłupienie.",
        "fear": "Reakcja na zagrożenie. Obejmuje spektrum od niepokoju po przerażenie.",
        "sadness": "Reakcja na utratę ważnego zasobu lub osoby. Obejmuje spektrum od przygnębienia po żałobę.",
        "disgust": "Reakcja na obiekt toksyczny lub szkodliwy (także moralnie). Obejmuje spektrum od niechęci po odrazę.",
        "anger": "Reakcja na przeszkodę w osiągnięciu celu. Obejmuje spektrum od irytacji po wściekłość."
    }
}

# Google Sheets configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Custom CSS for modern UI
CUSTOM_CSS = """
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }
    
    /* Text card styling */
    .text-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 25px 30px;
        border-radius: 15px;
        border-left: 5px solid #4CAF50;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    .text-card p {
        font-size: 17px;
        line-height: 1.8;
        color: #e0e0e0;
        margin: 0;
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 15px 25px;
        border-radius: 10px;
        margin: 25px 0 15px 0;
        text-align: center;
    }
    
    .section-header h3 {
        color: white;
        margin: 0;
        font-size: 1.3rem;
    }
    
    /* Coding container - integrated look */
    .coding-container {
        background: rgba(255,255,255,0.03);
        border-radius: 15px;
        padding: 0;
        margin-bottom: 20px;
        overflow: hidden;
    }
    
    .coding-container .section-header {
        margin: 0;
        border-radius: 15px 15px 0 0;
    }
    
    .text-card-integrated {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 20px 25px;
        margin: 0;
        border-radius: 0 0 15px 15px;
    }
    
    .text-card-integrated p {
        font-size: 16px;
        line-height: 1.7;
        color: #e0e0e0;
        margin: 0;
    }
    
    /* Progress styling */
    .progress-container {
        background: rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 3px;
        margin-bottom: 10px;
    }
    
    /* Welcome card */
    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        margin: 20px 0;
    }
    
    .welcome-card h1 {
        color: white;
        margin-bottom: 10px;
    }
    
    /* Instruction box */
    .instruction-box {
        background: rgba(255,255,255,0.05);
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
    }
    
    .instruction-item {
        display: flex;
        align-items: flex-start;
        margin: 15px 0;
    }
    
    .instruction-number {
        background: #667eea;
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 15px;
        flex-shrink: 0;
    }
    
    /* Hide default widget labels */
    [data-testid="stWidgetLabel"] {
        display: none !important;
    }
    
    /* Global spacing reduction for compact look */
    .stElementContainer {
        margin-bottom: 0px;
    }
    
    /* Rating item styling - Top part of the card */
    .rating-item, .rating-card {
        padding: 8px 12px 8px 12px;
        border-radius: 8px;
        margin-top: 2px;
        margin-bottom: 0px;
    }
    
    .rating-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 1px;
    }
    
    .rating-desc {
        font-size: 0.7rem;
        color: #c0c0c0;
        margin-bottom: 0px;
        font-style: italic;
        line-height: 1.15;
    }
    
    /* Slider container - standard Streamlit styling with top margin */
    .stSlider {
        padding-top: 8px !important;
        margin-bottom: 0px !important;
        background: transparent !important;
    }
    
    /* Success message styling */
    .success-banner {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        margin: 30px 0;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #667eea;
        padding: 10px 15px;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 25px;
        padding: 12px 30px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Dynamic thumb colors based on position */
    .slider-brak [data-baseweb="slider"] [role="slider"] {
        background: #4CAF50 !important;
    }
    .slider-niskie [data-baseweb="slider"] [role="slider"] {
        background: #8BC34A !important;
    }
    .slider-srednie [data-baseweb="slider"] [role="slider"] {
        background: #FF9800 !important;
    }
    .slider-wysokie [data-baseweb="slider"] [role="slider"] {
        background: #f44336 !important;
    }
</style>
"""


def fix_private_key(key):
    """Fix escaped newlines in private key (convert literal \\n to actual newline)."""
    # Replace literal backslash+n with actual newline character
    return key.replace(chr(92) + 'n', chr(10))


def get_google_sheets_client():
    """Create Google Sheets client (no caching to avoid stale connections)."""
    try:
        if "SPREADSHEET_ID" not in st.secrets:
            return None, "Brak SPREADSHEET_ID w secrets!"
        
        creds_info = None
        
        if "service_account_json" in st.secrets:
            creds_info = json.loads(st.secrets["service_account_json"])
            # Fix escaped newlines in private_key
            if "private_key" in creds_info:
                creds_info["private_key"] = fix_private_key(creds_info["private_key"])
        elif "type" in st.secrets and "project_id" in st.secrets:
            creds_info = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key_id": st.secrets["private_key_id"],
                "private_key": fix_private_key(st.secrets["private_key"]),
                "client_email": st.secrets["client_email"],
                "client_id": st.secrets["client_id"],
                "auth_uri": st.secrets["auth_uri"],
                "token_uri": st.secrets["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["client_x509_cert_url"],
                "universe_domain": st.secrets.get("universe_domain", "googleapis.com")
            }
        elif "gsheets" in st.secrets:
            creds_info = dict(st.secrets["gsheets"])
            if "private_key" in creds_info:
                creds_info["private_key"] = fix_private_key(creds_info["private_key"])
        
        if not creds_info:
            return None, "Nie można odczytać danych uwierzytelniających!"
        
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["SPREADSHEET_ID"])
        return sh.sheet1, None
    except Exception as e:
        return None, str(e)


def save_to_google_sheets(oid, text, sentiment_values, emotion_values, coder_id="unknown"):
    """Save coding results to Google Sheets."""
    ws, error = get_google_sheets_client()
    if ws is None:
        return False, f"Błąd połączenia: {error}"
    
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        row = [
            timestamp, str(coder_id), str(oid), str(text)[:500],
            int(sentiment_values.get("positive", 0)),
            int(sentiment_values.get("negative", 0)),
            int(sentiment_values.get("neutral", 0)),
            int(emotion_values.get("joy", 0)),
            int(emotion_values.get("trust", 0)),
            int(emotion_values.get("anticipation", 0)),
            int(emotion_values.get("surprise", 0)),
            int(emotion_values.get("fear", 0)),
            int(emotion_values.get("sadness", 0)),
            int(emotion_values.get("disgust", 0)),
            int(emotion_values.get("anger", 0))
        ]
        ws.append_row(row, value_input_option='USER_ENTERED')
        return True, None
    except Exception as e:
        return False, str(e)


# Categories configuration with unique subtle background colors
SENTIMENTS = {
    "positive": {"pl": "😊 Pozytywny", "icon": "😊", "bg": "rgba(76, 175, 80, 0.15)", "border": "#4CAF50"},
    "negative": {"pl": "😢 Negatywny", "icon": "😢", "bg": "rgba(244, 67, 54, 0.15)", "border": "#f44336"},
    "neutral": {"pl": "😐 Neutralny", "icon": "😐", "bg": "rgba(158, 158, 158, 0.15)", "border": "#9E9E9E"}
}

EMOTIONS = {
    "joy": {"pl": "Radość", "icon": "😄", "bg": "rgba(255, 235, 59, 0.12)", "border": "#FFEB3B"},
    "trust": {"pl": "Zaufanie", "icon": "🤝", "bg": "rgba(76, 175, 80, 0.12)", "border": "#4CAF50"},
    "anticipation": {"pl": "Oczekiwanie", "icon": "🔮", "bg": "rgba(156, 39, 176, 0.12)", "border": "#9C27B0"},
    "surprise": {"pl": "Zaskoczenie", "icon": "😲", "bg": "rgba(255, 152, 0, 0.12)", "border": "#FF9800"},
    "fear": {"pl": "Strach", "icon": "😨", "bg": "rgba(33, 150, 243, 0.12)", "border": "#2196F3"},
    "sadness": {"pl": "Smutek", "icon": "😢", "bg": "rgba(63, 81, 181, 0.12)", "border": "#3F51B5"},
    "disgust": {"pl": "Wstręt", "icon": "🤢", "bg": "rgba(139, 195, 74, 0.12)", "border": "#8BC34A"},
    "anger": {"pl": "Złość", "icon": "😠", "bg": "rgba(244, 67, 54, 0.12)", "border": "#f44336"}
}

# Color mapping for slider thumb based on value
SLIDER_COLORS = {
    "Brak": "#4CAF50",      # Green
    "Niskie": "#8BC34A",    # Light green
    "Średnie": "#FF9800",   # Orange
    "Wysokie": "#f44336"    # Red
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
        st.session_state.session_elements = st.session_state.data[:20]
    if 'coding_stage' not in st.session_state:
        st.session_state.coding_stage = 'sentiment'
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'current_coding' not in st.session_state:
        st.session_state.current_coding = {'sentiment': {}, 'emotion': {}}
    if 'coder_id' not in st.session_state:
        st.session_state.coder_id = ""


def start_screen():
    """Display start screen."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Welcome header
    st.markdown("""
    <div class="welcome-card">
        <h1>Kodowanie sentymentu i emocji w fake newsach</h1>
        <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">
            Narzędzie do manualnej analizy tekstów
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Instructions using native Streamlit
    st.markdown("#### 📋 Jak to działa?")
    
    st.markdown("""
    **1.** Przeczytasz **20 tekstów** z fake newsami
    
    **2.** Dla każdego tekstu ocenisz natężenie **sentymentu** (pozytywny, negatywny, neutralny)
    
    **3.** Następnie ocenisz natężenie **emocji** (radość, zaufanie, oczekiwanie, zaskoczenie, strach, smutek, wstręt, złość)
    
                 
    Do określenia poziomu natężenia użyj prostej skali: **Brak/Niskie → Średnie → Wysokie**
    """)
    
    st.markdown("---")
    
    # Coder ID input
    st.markdown("#### 👤 Twój identyfikator")
    coder_id = st.text_input(
        "Identyfikator",
        placeholder="Wpisz swoje inicjały (np. JK, AM)",
        max_chars=20,
        label_visibility="collapsed"
    )
    
    st.markdown("")
    
    # Start button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 ROZPOCZNIJ KODOWANIE", use_container_width=True, type="primary"):
            if not coder_id.strip():
                st.warning("Proszę podać identyfikator przed rozpoczęciem")
            else:
                st.session_state.coder_id = coder_id.strip()
                st.session_state.screen = 'coding'
                st.rerun()


def coding_screen():
    """Display coding screen."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    current_element = st.session_state.session_elements[st.session_state.current_index]
    progress = st.session_state.current_index + 1
    
    # Modern compact progress header
    progress_percent = int((progress / 20) * 100)
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 0; margin-bottom: 10px;">
        <div style="flex: 1; margin-right: 15px;">
            <div style="background: rgba(255,255,255,0.1); border-radius: 10px; height: 8px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; width: {progress_percent}%; border-radius: 10px; transition: width 0.3s ease;"></div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 1.2rem; font-weight: 700; color: #667eea;">{progress}</span>
            <span style="font-size: 0.85rem; color: #888;">/ 20 tekstów</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Coding stage
    if st.session_state.coding_stage == 'sentiment':
        sentiment_coding_ui(current_element['text'])
    else:
        emotion_coding_ui(current_element['text'])


def sentiment_coding_ui(text):
    """UI for sentiment coding."""
    # Step indicator
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
        <div style="background: #667eea; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1rem;">1</div>
        <div>
            <div style="font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px;">Krok 1 z 2</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: #fff;">Sentyment</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Text to analyze
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 16px 20px; border-radius: 10px; border-left: 4px solid #667eea; margin-bottom: 15px;">
        <div style="font-size: 0.7rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">📝 Tekst do oceny</div>
        <p style="font-size: 0.95rem; line-height: 1.6; color: #e0e0e0; margin: 0;">{text}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Instruction
    st.markdown("""
    <div style="font-size: 0.8rem; color: #b0b0b0; margin-bottom: 10px;">
        ↓ Dla każdego sentymentu wybierz poziom natężenia (Brak → Wysokie)
    </div>
    """, unsafe_allow_html=True)
    
    sentiment_values = {}
    slider_values_for_css = {}
    
    # Scale options
    scale_options = ["Brak", "Niskie", "Średnie", "Wysokie"]
    
    # Create sliders for each sentiment
    for idx, (key, data) in enumerate(SENTIMENTS.items()):
        # Get definition for tooltip
        definition = DEFINITIONS["sentiments"].get(key, "")
        bg_color = data.get('bg', 'rgba(255,255,255,0.05)')
        border_color = data.get('border', '#667eea')
        
        # Full card with label, description and slider background
        st.markdown(f"""
        <div class="rating-card" style="background: {bg_color}; border-left: 3px solid {border_color}; border-radius: 8px; padding: 8px 12px; margin-top: 6px;">
            <div class="rating-label">{data['pl']}</div>
            <div class="rating-desc">{definition}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Slider
        value = st.select_slider(
            f"Natężenie - {data['pl']}",
            options=scale_options,
            value="Brak",
            key=f"sentiment_{key}",
            label_visibility="collapsed"
        )
        
        slider_values_for_css[f"sentiment_{key}"] = (value, bg_color)
        
        # Convert to numeric value (0-3)
        sentiment_values[key] = scale_options.index(value)
    
    st.markdown("")
    
    # Next button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("DALEJ → Emocje", use_container_width=True, type="primary"):
            st.session_state.current_coding['sentiment'] = sentiment_values
            st.session_state.coding_stage = 'emotion'
            st.rerun()


def emotion_coding_ui(text):
    """UI for emotion coding."""
    # Step indicator
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
        <div style="background: #764ba2; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1rem;">2</div>
        <div>
            <div style="font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px;">Krok 2 z 2</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: #fff;">Emocje</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Text to analyze
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 16px 20px; border-radius: 10px; border-left: 4px solid #764ba2; margin-bottom: 15px;">
        <div style="font-size: 0.7rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">📝 Tekst do oceny</div>
        <p style="font-size: 0.95rem; line-height: 1.6; color: #e0e0e0; margin: 0;">{text}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Instruction
    st.markdown("""
    <div style="font-size: 0.8rem; color: #b0b0b0; margin-bottom: 10px;">
        ↓ Dla każdej emocji wybierz poziom natężenia (Brak → Wysokie)
    </div>
    """, unsafe_allow_html=True)
    
    emotion_values = {}
    slider_values_for_css = {}
    
    # Scale options
    scale_options = ["Brak", "Niskie", "Średnie", "Wysokie"]
    
    # Create two columns for emotions
    col1, col2 = st.columns(2)
    
    emotions_list = list(EMOTIONS.items())
    
    with col1:
        for idx, (key, data) in enumerate(emotions_list[:4]):
            definition = DEFINITIONS["emotions"].get(key, "")
            bg_color = data.get('bg', 'rgba(255,255,255,0.05)')
            border_color = data.get('border', '#667eea')
            
            st.markdown(f"""
            <div class="rating-card" style="background: {bg_color}; border-left: 3px solid {border_color}; border-radius: 8px; padding: 8px 12px; margin-top: 6px;">
                <div class="rating-label">{data['icon']} {data['pl']}</div>
                <div class="rating-desc">{definition}</div>
            </div>
            """, unsafe_allow_html=True)
            
            value = st.select_slider(
                f"{data['pl']}",
                options=scale_options,
                value="Brak",
                key=f"emotion_{key}",
                label_visibility="collapsed"
            )
            emotion_values[key] = scale_options.index(value)
            slider_values_for_css[f"emotion_{key}_col1_{idx}"] = (value, bg_color)
    
    with col2:
        for idx, (key, data) in enumerate(emotions_list[4:]):
            definition = DEFINITIONS["emotions"].get(key, "")
            bg_color = data.get('bg', 'rgba(255,255,255,0.05)')
            border_color = data.get('border', '#667eea')
            
            st.markdown(f"""
            <div class="rating-card" style="background: {bg_color}; border-left: 3px solid {border_color}; border-radius: 8px; padding: 8px 12px; margin-top: 6px;">
                <div class="rating-label">{data['icon']} {data['pl']}</div>
                <div class="rating-desc">{definition}</div>
            </div>
            """, unsafe_allow_html=True)
            
            value = st.select_slider(
                f"{data['pl']}",
                options=scale_options,
                value="Brak",
                key=f"emotion_{key}",
                label_visibility="collapsed"
            )
            emotion_values[key] = scale_options.index(value)
            slider_values_for_css[f"emotion_{key}_col2_{idx}"] = (value, bg_color)
    
    st.markdown("")
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← Wróć", use_container_width=True):
            st.session_state.coding_stage = 'sentiment'
            st.rerun()
    
    with col3:
        if st.button("ZAPISZ ✓", use_container_width=True, type="primary"):
            current_element = st.session_state.session_elements[st.session_state.current_index]
            
            # Save to Google Sheets
            success, error = save_to_google_sheets(
                oid=current_element["$oid"],
                text=current_element["text"],
                sentiment_values=st.session_state.current_coding['sentiment'],
                emotion_values=emotion_values,
                coder_id=st.session_state.coder_id
            )
            
            if not success:
                st.error(f"❌ Błąd zapisu: {error}")
                st.stop()
            
            # Local backup
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
            
            if st.session_state.current_index >= 20:
                save_results()
                st.session_state.screen = 'end'
            
            st.rerun()


def save_results():
    """Save coding results to JSON file (local backup)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RESULTS_DIR / f"manual_coding_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.results, f, ensure_ascii=False, indent=2)
    
    st.session_state.results_file = output_file


def end_screen():
    """Display end screen."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="success-banner">
        <h1 style="color: white; margin-bottom: 10px;">🎉 Gratulacje!</h1>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.2rem;">
            Pomyślnie zakończyłeś kodowanie wszystkich tekstów
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 30px; background: rgba(255,255,255,0.05); border-radius: 15px;">
            <h2 style="color: #4CAF50; margin-bottom: 10px;">20</h2>
            <p style="color: #b0b0b0;">zakodowanych tekstów</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # New session button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 ROZPOCZNIJ NOWĄ SESJĘ", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()


def main():
    """Main application logic."""
    st.set_page_config(
        page_title="Kodowanie Sentymentu i Emocji",
        page_icon="🎯",
        layout="centered"
    )
    
    initialize_session()
    
    if st.session_state.screen == 'start':
        start_screen()
    elif st.session_state.screen == 'coding':
        coding_screen()
    elif st.session_state.screen == 'end':
        end_screen()


if __name__ == "__main__":
    main()
