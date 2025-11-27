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
    
    /* Scale legend */
    .scale-legend {
        display: flex;
        justify-content: space-between;
        background: rgba(255,255,255,0.05);
        padding: 12px 20px;
        border-radius: 10px;
        margin: 15px 0;
    }
    
    .scale-item {
        text-align: center;
        flex: 1;
    }
    
    .scale-label {
        font-size: 0.85rem;
        color: #b0b0b0;
    }
    
    .scale-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-bottom: 5px;
    }
    
    .scale-dot.low { background: #4CAF50; }
    .scale-dot.mid { background: #FFC107; }
    .scale-dot.high { background: #f44336; }
    
    /* Emotion/Sentiment labels */
    .coding-label {
        font-size: 1rem;
        font-weight: 500;
        color: #ffffff;
        padding: 8px 0 5px 5px;
        margin-top: 10px;
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
    
    /* Hide slider labels */
    .stSlider label {
        display: none !important;
    }
    
    /* Slider styling */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #4CAF50, #FFC107, #f44336) !important;
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
</style>
"""


@st.cache_resource(ttl=60)
def get_worksheet(_force_refresh=None):
    """Establish connection to Google Sheets."""
    try:
        if "SPREADSHEET_ID" not in st.secrets:
            return None
        
        creds_info = None
        
        if "service_account_json" in st.secrets:
            creds_info = json.loads(st.secrets["service_account_json"])
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
        elif "gsheets" in st.secrets:
            creds_info = dict(st.secrets["gsheets"])
        
        if not creds_info:
            return None
        
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["SPREADSHEET_ID"])
        return sh.sheet1
    except Exception:
        return None


def save_to_google_sheets(oid, text, sentiment_values, emotion_values, coder_id="unknown"):
    """Save coding results to Google Sheets."""
    try:
        ws = get_worksheet()
        if ws is None:
            return False
        
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
        return True
    except Exception:
        return False


# Categories configuration
SENTIMENTS = {
    "positive": {"pl": "😊 Pozytywny", "icon": "😊"},
    "negative": {"pl": "😢 Negatywny", "icon": "😢"},
    "neutral": {"pl": "😐 Neutralny", "icon": "😐"}
}

EMOTIONS = {
    "joy": {"pl": "Radość", "icon": "😄"},
    "trust": {"pl": "Zaufanie", "icon": "🤝"},
    "anticipation": {"pl": "Oczekiwanie", "icon": "🔮"},
    "surprise": {"pl": "Zaskoczenie", "icon": "😲"},
    "fear": {"pl": "Strach", "icon": "😨"},
    "sadness": {"pl": "Smutek", "icon": "😢"},
    "disgust": {"pl": "Wstręt", "icon": "🤢"},
    "anger": {"pl": "Złość", "icon": "😠"}
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


def render_scale_legend():
    """Render the scale legend."""
    st.markdown("""
    <div class="scale-legend">
        <div class="scale-item">
            <div class="scale-dot low"></div><br>
            <span class="scale-label">Brak / Niskie</span>
        </div>
        <div class="scale-item">
            <div class="scale-dot mid"></div><br>
            <span class="scale-label">Średnie</span>
        </div>
        <div class="scale-item">
            <div class="scale-dot high"></div><br>
            <span class="scale-label">Wysokie</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def start_screen():
    """Display start screen."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Welcome header
    st.markdown("""
    <div class="welcome-card">
        <h1>🎯 Kodowanie Sentymentu i Emocji</h1>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.1rem;">
            Profesjonalne narzędzie do analizy tekstów
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Instructions
    st.markdown("""
    <div class="instruction-box">
        <h4 style="margin-bottom: 20px; color: #667eea;">📋 Jak to działa?</h4>
        
        <div class="instruction-item">
            <div class="instruction-number">1</div>
            <div>Przeczytasz <strong>20 tekstów</strong> do analizy</div>
        </div>
        
        <div class="instruction-item">
            <div class="instruction-number">2</div>
            <div>Dla każdego tekstu ocenisz <strong>sentyment</strong> (pozytywny, negatywny, neutralny)</div>
        </div>
        
        <div class="instruction-item">
            <div class="instruction-number">3</div>
            <div>Następnie ocenisz <strong>emocje</strong> (radość, zaufanie, strach i inne)</div>
        </div>
        
        <div class="instruction-item">
            <div class="instruction-number">4</div>
            <div>Użyj prostej skali: <strong>Brak/Niskie → Średnie → Wysokie</strong></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Coder ID input
    st.markdown("#### 👤 Twój identyfikator")
    coder_id = st.text_input(
        "Identyfikator",
        placeholder="Wpisz swoje inicjały (np. JK, AM)",
        max_chars=20,
        label_visibility="collapsed"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
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
    
    # Progress header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(progress / 20)
    with col2:
        st.markdown(f"<p style='text-align: right; font-size: 1.1rem; font-weight: 600; color: #667eea;'>{progress} / 20</p>", unsafe_allow_html=True)
    
    # Text card
    st.markdown(f"""
    <div class="text-card">
        <p>{current_element['text']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Coding stage
    if st.session_state.coding_stage == 'sentiment':
        sentiment_coding_ui()
    else:
        emotion_coding_ui()


def sentiment_coding_ui():
    """UI for sentiment coding."""
    # Section header
    st.markdown("""
    <div class="section-header">
        <h3>😊 Oceń Sentyment</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Scale legend (once at the top)
    render_scale_legend()
    
    sentiment_values = {}
    
    # Create sliders for each sentiment
    for key, data in SENTIMENTS.items():
        st.markdown(f"<div class='coding-label'>{data['pl']}</div>", unsafe_allow_html=True)
        value = st.select_slider(
            f"sent_{key}",
            options=["Brak/Niskie", "Średnie", "Wysokie"],
            value="Brak/Niskie",
            key=f"sentiment_{key}",
            label_visibility="collapsed"
        )
        sentiment_values[key] = {"Brak/Niskie": 0, "Średnie": 1, "Wysokie": 2}[value]
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Next button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("DALEJ → Emocje", use_container_width=True, type="primary"):
            st.session_state.current_coding['sentiment'] = sentiment_values
            st.session_state.coding_stage = 'emotion'
            st.rerun()


def emotion_coding_ui():
    """UI for emotion coding."""
    # Section header
    st.markdown("""
    <div class="section-header">
        <h3>🎭 Oceń Emocje</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Scale legend (once at the top)
    render_scale_legend()
    
    emotion_values = {}
    
    # Create two columns for emotions
    col1, col2 = st.columns(2)
    
    emotions_list = list(EMOTIONS.items())
    
    with col1:
        for key, data in emotions_list[:4]:
            st.markdown(f"<div class='coding-label'>{data['icon']} {data['pl']}</div>", unsafe_allow_html=True)
            value = st.select_slider(
                f"emo_{key}",
                options=["Brak/Niskie", "Średnie", "Wysokie"],
                value="Brak/Niskie",
                key=f"emotion_{key}",
                label_visibility="collapsed"
            )
            emotion_values[key] = {"Brak/Niskie": 0, "Średnie": 1, "Wysokie": 2}[value]
    
    with col2:
        for key, data in emotions_list[4:]:
            st.markdown(f"<div class='coding-label'>{data['icon']} {data['pl']}</div>", unsafe_allow_html=True)
            value = st.select_slider(
                f"emo_{key}",
                options=["Brak/Niskie", "Średnie", "Wysokie"],
                value="Brak/Niskie",
                key=f"emotion_{key}",
                label_visibility="collapsed"
            )
            emotion_values[key] = {"Brak/Niskie": 0, "Średnie": 1, "Wysokie": 2}[value]
    
    st.markdown("<br>", unsafe_allow_html=True)
    
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
            save_to_google_sheets(
                oid=current_element["$oid"],
                text=current_element["text"],
                sentiment_values=st.session_state.current_coding['sentiment'],
                emotion_values=emotion_values,
                coder_id=st.session_state.coder_id
            )
            
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
