"""
Aplikacja Streamlit do manualnego kodowania sentymentu i emocji.
#cd app/wer_llm/sent_emo_app
streamlit run sent_emo_app.py
"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime, timezone
import re
import gspread
from google.oauth2.service_account import Credentials

# ===== KONFIGURACJA SESJI KODOWANIA =====
# Ustaw liczbę tekstów do zakodowania
NUM_TEXTS_TO_CODE = 30

# Ustaw zakres elementów do kodowania (numeracja od 0)
# None = od początku, lub podaj numer startu (np. 150)
START_INDEX = 196
# None = do końca, lub podaj numer końca (np. 230)
END_INDEX = 226
# =========================================

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
        "anticipation": "Reakcja na nowe i przyszłe zdarzenie. Obejmuje spektrum od czujności po ekscytację.",
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
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        padding: 25px 30px;
        border-radius: 15px;
        border-left: 5px solid #5d6d7e;
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
    
    /* Welcome card */
    .welcome-card {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        margin: 20px 0;
    }
    
    .welcome-card h1 {
        color: white;
        margin-bottom: 10px;
    }
    
    /* Hide default widget labels */
    [data-testid="stWidgetLabel"] {
        display: none !important;
    }
    
    /* Success message styling */
    .success-banner {
        background: linear-gradient(135deg, #5d7e69 0%, #4a6358 100%);
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        margin: 30px 0;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #5d6d7e;
        padding: 10px 15px;
    }
    
    /* Rating box - container for each category */
    .rating-box {
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 4px;
    }
    
    .rating-label-container {
        flex: 1;
    }
    
    .rating-label {
        font-size: 0.95rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 2px;
    }
    
    .rating-desc {
        font-size: 0.65rem;
        color: #c0c0c0;
        font-style: italic;
        line-height: 1.3;
    }
    
    /* Smaller spacing between elements */
    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
    }
    
    /* Rating buttons - secondary (not selected) - nested columns */
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        background: rgba(40, 40, 50, 0.9) !important;
        border: 2px solid rgba(255,255,255,0.2) !important;
        border-radius: 8px !important;
        padding: 3px 6px !important;
        font-size: 0.55rem !important;
        color: #d0d0d0 !important;
        font-weight: 500 !important;
        min-height: 29px !important;
    }
    
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
        background: rgba(60, 60, 70, 0.9) !important;
        border-color: rgba(255,255,255,0.4) !important;
    }
    
    /* Rating buttons - primary (selected) - stonowany niebieski border */
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] button[kind="primary"] {
        background: rgba(40, 40, 50, 0.95) !important;
        border: 2px solid #5d6d7e !important;
        border-radius: 8px !important;
        padding: 3px 6px !important;
        font-size: 0.55rem !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        min-height: 29px !important;
    }
    
    /* Main action buttons (DALEJ, ZAPISZ, etc.) */
    .stButton > button[kind="primary"] {
        border-radius: 25px !important;
        padding: 12px 30px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        background: linear-gradient(135deg, #5d6d7e 0%, #34495e 100%) !important;
        border: 2px solid #c85a54 !important;
        font-size: 1rem !important;
        min-height: auto !important;
        box-shadow: none !important;
        color: white !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(200, 90, 84, 0.5) !important;
        border-color: #d67771 !important;
    }
    
    .stButton > button[kind="secondary"] {
        border-radius: 25px !important;
        padding: 12px 30px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        min-height: auto !important;
        border: 2px solid #c85a54 !important;
        transition: all 0.3s ease !important;
        box-shadow: none !important;
        color: #d0d0d0 !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(200, 90, 84, 0.4) !important;
        border-color: #d67771 !important;
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
    "positive": {"pl": "😊 Pozytywny", "icon": "😊", "bg": "rgba(76, 140, 80, 0.08)", "border": "#4a7a4d"},
    "negative": {"pl": "😢 Negatywny", "icon": "😢", "bg": "rgba(180, 67, 60, 0.08)", "border": "#8a4a46"},
    "neutral": {"pl": "😐 Neutralny", "icon": "😐", "bg": "rgba(120, 120, 120, 0.08)", "border": "#6a6a6a"}
}

EMOTIONS = {
    "joy": {"pl": "Radość", "icon": "😄", "bg": "rgba(190, 180, 80, 0.07)", "border": "#a09a5a"},
    "trust": {"pl": "Zaufanie", "icon": "🤝", "bg": "rgba(76, 140, 80, 0.07)", "border": "#4a7a4d"},
    "anticipation": {"pl": "Oczekiwanie", "icon": "🔮", "bg": "rgba(120, 60, 130, 0.07)", "border": "#6a4a70"},
    "surprise": {"pl": "Zaskoczenie", "icon": "😲", "bg": "rgba(180, 120, 60, 0.07)", "border": "#9a7a50"},
    "fear": {"pl": "Strach", "icon": "😨", "bg": "rgba(60, 110, 160, 0.07)", "border": "#4a6a8a"},
    "sadness": {"pl": "Smutek", "icon": "😢", "bg": "rgba(70, 80, 130, 0.07)", "border": "#4a5575"},
    "disgust": {"pl": "Wstręt", "icon": "🤢", "bg": "rgba(110, 140, 80, 0.07)", "border": "#5a7a4a"},
    "anger": {"pl": "Gniew", "icon": "😠", "bg": "rgba(180, 67, 60, 0.07)", "border": "#8a4a46"}
}

# Color mapping for slider thumb based on value
SLIDER_COLORS = {
    "Brak": "#4CAF50",                           # Green
    "Obecna": "#FF9800",         # Orange
    "Silna / Dominująca": "#f44336"              # Red
}

RGBA_PATTERN = re.compile(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)")


def adjust_rgba_alpha(color: str, alpha: float) -> str:
    """Return rgba color with adjusted alpha (falls back to original on parse failure)."""
    match = RGBA_PATTERN.match(color.strip())
    if not match:
        return color
    r, g, b, _ = match.groups()
    alpha = max(0.0, min(alpha, 1.0))
    return f"rgba({r}, {g}, {b}, {alpha})"


def render_scale_row(row_key: str,
                     data: dict,
                     definition: str,
                     state_prefix: str,
                     scale_options,
                     scale_mapping,
                     layout=(2.4, 1.6),
                     buttons_below=False,
                     desc_max_width="100%",
                     button_font_size="0.55rem",
                     button_padding="4px 8px") -> str:
    """Render a single labeled scale row and return selected label."""
    state_key = f"{state_prefix}_val_{row_key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = scale_options[0]
    bg_color = data.get('bg', 'rgba(255,255,255,0.08)')
    border_color = data.get('border', '#667eea')
    button_bg = adjust_rgba_alpha(bg_color, 0.45)
    button_bg_selected = adjust_rgba_alpha(bg_color, 0.8)
    marker_class = f"{state_prefix}-marker-{row_key}"
    label_text = data.get('pl', row_key.title())
    icon = data.get('icon')
    label_display = f"{icon} {label_text}" if icon and icon not in label_text else label_text

    with st.container():
        st.markdown(f"""
        <style>
        div[data-testid="stVerticalBlock"]:has(> .element-container > .stMarkdown .{marker_class}) {{
            background: {bg_color} !important;

            border-radius: 12px !important;
            padding: 16px 18px !important;
            margin-bottom: -5px !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        }}
        div[data-testid="stVerticalBlock"]:has(> .element-container > .stMarkdown .{marker_class}) > div {{
            background: transparent !important;
        }}
        div[data-testid="stVerticalBlock"]:has(> .element-container > .stMarkdown .{marker_class}) button[kind="secondary"],
        div[data-testid="stVerticalBlock"]:has(> .element-container > .stMarkdown .{marker_class}) button[kind="primary"] {{
            background: {button_bg} !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            font-size: {button_font_size} !important;
            padding: {button_padding} !important;
            min-height: 30px !important;
        }}
        div[data-testid="stVerticalBlock"]:has(> .element-container > .stMarkdown .{marker_class}) button[kind="secondary"] {{
            border: 2px solid rgba(255,255,255,0.25) !important;
        }}
        div[data-testid="stVerticalBlock"]:has(> .element-container > .stMarkdown .{marker_class}) button[kind="primary"] {{
            background: {button_bg_selected} !important;
            border: 3px solid #FFFFFF !important;
            font-weight: 600 !important;
        }}
        </style>
        <div class="{marker_class}"></div>
        """, unsafe_allow_html=True)

        if buttons_below:
            st.markdown(f"""
            <div style="padding-right: 8px; margin-bottom: 14px; margin-top: -18px">
                <div style="font-size: 1.05rem; font-weight: 600; color: #ffffff; margin-bottom: 4px;">
                    {label_display}
                </div>
                <div style="font-size: 0.75rem; color: #d0d0d0; font-style: italic; line-height: 1.4; max-width: {desc_max_width};">
                    {definition}
                </div>
            </div>
            """, unsafe_allow_html=True)
            btn_cols = st.columns(len(scale_options))
        else:
            col_label, col_buttons = st.columns(layout)
            with col_label:
                st.markdown(f"""
                <div style="padding-right: 12px; max-width: {desc_max_width}; margin-top: -18px;">
                    <div style="font-size: 1.05rem; font-weight: 600; color: #ffffff; margin-bottom: 4px;">
                        {label_display}
                    </div>
                    <div style="font-size: 0.75rem; color: #d0d0d0; font-style: italic; line-height: 1.4;">
                        {definition}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_buttons:
                btn_cols = st.columns(len(scale_options))

        for option, btn_col in zip(scale_options, btn_cols):
            with btn_col:
                is_selected = (st.session_state[state_key] == option)
                btn_type = "primary" if is_selected else "secondary"
                if st.button(
                    option,
                    key=f"{state_prefix}_btn_{row_key}_{option}",
                    type=btn_type,
                    use_container_width=True
                ):
                    st.session_state[state_key] = option
                    st.rerun()

    return st.session_state[state_key]


def load_data():
    """Load data to code from JSON file."""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def initialize_session():
    """Initialize session state variables."""
    if 'screen' not in st.session_state:
        st.session_state.screen = 'start'  # Start with main start screen
    if 'start_screen_passed' not in st.session_state:
        st.session_state.start_screen_passed = False
    if 'data' not in st.session_state:
        st.session_state.data = load_data()
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'session_elements' not in st.session_state:
        # Zastosuj zakres i liczbę tekstów z konfiguracji
        all_data = st.session_state.data
        start = START_INDEX if START_INDEX is not None else 0
        end = END_INDEX if END_INDEX is not None else len(all_data)
        selected_data = all_data[start:end]
        st.session_state.session_elements = selected_data[:NUM_TEXTS_TO_CODE]
    if 'coding_stage' not in st.session_state:
        st.session_state.coding_stage = 'sentiment'
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'current_coding' not in st.session_state:
        st.session_state.current_coding = {'sentiment': {}, 'emotion': {}}
    if 'coder_id' not in st.session_state:
        st.session_state.coder_id = ""


def instructions_screen():
    """Display instructions screen with coding guidelines."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Header - spójny z głównym ekranem startowym
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); padding: 16px 25px; border-radius: 12px; text-align: center; margin: 10px 0 15px 0;">
        <h2 style="color: white; margin: 0; font-size: 1.4rem;">📋 Zasady Kodowania</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Rule 1: Operational definitions - kompaktowy
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); padding: 14px 18px; border-radius: 10px; margin: 8px 0; border-left: 4px solid #3498db;">
        <div style="display: flex; align-items: flex-start; gap: 10px;">
            <div style="background: #3498db; color: white; min-width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.85rem;">1</div>
            <div>
                <div style="font-size: 0.92rem; font-weight: 600; color: #fff; margin-bottom: 4px;">📖 Oceniaj według definicji operacyjnych</div>
                <p style="font-size: 0.8rem; line-height: 1.4; color: #c8c8c8; margin: 0;">
                    Intensywność sentymentu i emocji oceniaj <strong style="color: #3498db;">wyłącznie na podstawie definicji</strong> wyświetlanych przy każdej kategorii. Nie kieruj się intuicją – stosuj podane kryteria.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Rule 2: Sender's emotions - kompaktowy
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); padding: 14px 18px; border-radius: 10px; margin: 8px 0; border-left: 4px solid #e74c3c;">
        <div style="display: flex; align-items: flex-start; gap: 10px;">
            <div style="background: #e74c3c; color: white; min-width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.85rem;">2</div>
            <div>
                <div style="font-size: 0.92rem; font-weight: 600; color: #fff; margin-bottom: 4px;">🎭 Koduj emocje nadawcy, nie odbiorców</div>
                <p style="font-size: 0.8rem; line-height: 1.4; color: #c8c8c8; margin: 0;">
                    Oceniaj <strong style="color: #e74c3c;">ton wypowiedzi autora tekstu</strong> – czyli emocje nadawcy/głosu narracji. <br>
                    <span style="color: #888; font-size: 0.75rem;">❌ Nie koduj: hipotetycznych reakcji czytelników ani emocji osób opisywanych w tekście.</span>
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Rule 3: Mixed emotions - kompaktowy
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); padding: 14px 18px; border-radius: 10px; margin: 8px 0; border-left: 4px solid #f39c12;">
        <div style="display: flex; align-items: flex-start; gap: 10px;">
            <div style="background: #f39c12; color: white; min-width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.85rem;">3</div>
            <div>
                <div style="font-size: 0.92rem; font-weight: 600; color: #fff; margin-bottom: 4px;">🔀 Tekst może zawierać mieszany wydźwięk</div>
                <p style="font-size: 0.8rem; line-height: 1.4; color: #c8c8c8; margin: 0;">
                    Jeden tekst może wyrażać <strong style="color: #f39c12;">kilka emocji i sentymentów jednocześnie</strong>. <br>
                    <span style="color: #aaa; font-size: 0.75rem;">Przykład: sucha informacja o wypadku → częściowo negatywny i neutralny sentyment.</span>
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Rule 4: Hidden tone priority - kompaktowy
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); padding: 14px 18px; border-radius: 10px; margin: 8px 0; border-left: 4px solid #9b59b6;">
        <div style="display: flex; align-items: flex-start; gap: 10px;">
            <div style="background: #9b59b6; color: white; min-width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.85rem;">4</div>
            <div>
                <div style="font-size: 0.92rem; font-weight: 600; color: #fff; margin-bottom: 4px;">🎯Ukryty ton, nie dosłowne słowa</div>
                <p style="font-size: 0.8rem; line-height: 1.4; color: #c8c8c8; margin: 0;">
                    Oceń <strong style="color: #9b59b6;">faktyczny, prawdziwy ton wypowiedzi</strong>, to co autor naprawdę chce przekazać, nawet jeśli słowa brzmią neutralnie lub pozytywnie.
                </p>
                <div style="background: rgba(155, 89, 182, 0.15); padding: 8px 12px; border-radius: 6px; margin-top: 8px;">
                    <p style="font-size: 0.75rem; color: #d0d0d0; margin: 0; font-style: italic;">
                        💡 <strong style="color: #bb8fce;">Przykład:</strong> „No wspaniale, że znowu nas okłamali" <span style="color: #e74c3c;">→ negatywny sentyment + silny gniew </span>
                    </p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
   
    # Continue button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✓ ROZUMIEM – ROZPOCZNIJ KODOWANIE", use_container_width=True, type="primary"):
            st.session_state.screen = 'coding'
            st.rerun()


def start_screen():
    """Display start screen."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Welcome header - compact
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); padding: 18px 25px; border-radius: 12px; text-align: center; margin: 10px 0 15px 0;">
        <h2 style="color: white; margin: 0; font-size: 1.4rem;">Oceń sentyment i emocje w fake newsach</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Instructions
    st.markdown(f"""
    <div style="font-size: 0.98rem; color: #d0d0d0; margin-bottom: 10px;">
    Twoim zadaniem jest ocena <strong>{len(st.session_state.session_elements)} tekstów</strong> pod kątem obecności sentymentu i emocji. Zadanie składa się z dwóch kroków:
    </div>
    """, unsafe_allow_html=True)
    
    # Step 1 - Sentiment
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); padding: 12px 16px; border-radius: 8px; border-left: 3px solid #5d6d7e; border-right: 3px solid #5d6d7e; margin: 8px 0;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px;">
            <div style="background: #5d6d7e; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.8rem;">1</div>
            <div style="font-size: 0.92rem; font-weight: 600; color: #fff;">Sentyment</div>
        </div>
        <p style="font-size: 0.8rem; line-height: 1.4; color: #c8c8c8; margin: 0 0 0 32px;">
            Oceń natężenie trzech rodzajów sentymentu: pozytywny, negatywny, neutralny
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Step 2 - Emotions
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); padding: 12px 16px; border-radius: 8px; border-left: 3px solid #34495e; border-right: 3px solid #34495e; margin: 8px 0;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px;">
            <div style="background: #34495e; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.8rem;">2</div>
            <div style="font-size: 0.92rem; font-weight: 600; color: #fff;">Emocje</div>
        </div>
        <p style="font-size: 0.8rem; line-height: 1.4; color: #c8c8c8; margin: 0 0 0 32px;">
            Oceń natężenie ośmiu emocji: radość, zaufanie, oczekiwanie, zaskoczenie, strach, smutek, wstręt, gniew
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Scale explanation - compact
    st.markdown("""
    <div style="background: rgba(200, 90, 84, 0.1); padding: 12px 16px; border-radius: 8px; border: 2px solid #c85a54; margin: 12px 0 10px 0;">
        <div style="font-size: 0.82rem; font-weight: 600; color: #e8e8e8; margin-bottom: 8px;">📊 Skala oceny:</div>
        <div style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="background: rgba(40, 40, 50, 0.9); border: 2px solid rgba(255,255,255,0.3); border-radius: 6px; padding: 4px 10px; font-size: 0.7rem; color: #d0d0d0; font-weight: 500; min-width: 70px; text-align: center;">Brak</div>
                <span style="font-size: 0.78rem; color: #b8b8b8;">— całkowita nieobecność</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="background: rgba(40, 40, 50, 0.9); border: 2px solid rgba(255,255,255,0.3); border-radius: 6px; padding: 4px 10px; font-size: 0.7rem; color: #d0d0d0; font-weight: 500; min-width: 70px; text-align: center;">Obecna</div>
                <span style="font-size: 0.78rem; color: #b8b8b8;">— obecna, <strong>nawet śladowo</strong></span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="background: rgba(40, 40, 50, 0.9); border: 2px solid rgba(255,255,255,0.3); border-radius: 6px; padding: 4px 10px; font-size: 0.7rem; color: #d0d0d0; font-weight: 500; min-width: 70px; text-align: center;">Silna</div>
                <span style="font-size: 0.78rem; color: #b8b8b8;">— wyraźnie dominująca</span>
            </div>
        </div>
        <div style="padding: 8px; background: rgba(0,0,0,0.2); border-radius: 5px;">
            <p style="font-size: 0.75rem; line-height: 1.4; color: #f4a582; margin: 0; font-weight: 500;">
                *Zaznacz "Obecna" nawet przy subtelnej obecności. "Brak" = całkowity brak.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Coder ID input
    st.markdown('<div style="font-size: 0.82rem; font-weight: 600; color: #d0d0d0; margin: 12px 0 6px 0;">👤 Twój identyfikator:</div>', unsafe_allow_html=True)
    coder_id = st.text_input(
        "Identyfikator",
        placeholder="np. JK, AM, K01",
        max_chars=20,
        label_visibility="collapsed"
    )
    
    # Buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 DALEJ – ZASADY KODOWANIA", use_container_width=True, type="primary"):
            if not coder_id.strip():
                st.warning("Proszę podać identyfikator przed rozpoczęciem")
            else:
                st.session_state.coder_id = coder_id.strip()
                st.session_state.start_screen_passed = True
                st.session_state.screen = 'instructions'
                st.rerun()


def coding_screen():
    """Display coding screen."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    current_element = st.session_state.session_elements[st.session_state.current_index]
    progress = st.session_state.current_index + 1
    total_texts = len(st.session_state.session_elements)
    
    # Modern compact progress header
    progress_percent = int((progress / total_texts) * 100)
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 0; margin-bottom: 10px;">
        <div style="flex: 1; margin-right: 15px;">
            <div style="background: rgba(255,255,255,0.1); border-radius: 10px; height: 8px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #5d6d7e 0%, #34495e 100%); height: 100%; width: {progress_percent}%; border-radius: 10px; transition: width 0.3s ease;"></div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 1.2rem; font-weight: 700; color: #5d6d7e;">{progress}</span>
            <span style="font-size: 0.85rem; color: #888;">/ {total_texts} tekstów</span>
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
        <div style="background: #5d6d7e; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1rem;">1</div>
        <div>
            <div style="font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px;">Krok 1 z 2</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: #fff;">Sentyment</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Text to analyze
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); padding: 16px 20px; border-radius: 10px; border-left: 4px solid #5d6d7e; border-right: 4px solid #5d6d7e; margin-bottom: 15px;">
        <div style="font-size: 0.7rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;"> Tekst do oceny</div>
        <p style="font-size: 1.05rem; line-height: 1.6; color: #e0e0e0; margin: 0;">{text}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Instruction
    st.markdown("""
    <div style="font-size: 0.8rem; color: #b0b0b0; margin-bottom: 10px;">
        ↓ Dla każdego sentymentu wybierz poziom natężenia
    </div>
    """, unsafe_allow_html=True)
    
    sentiment_values = {}
    
    # Scale options (3-level)
    scale_options = ["Brak", "Obecna", "Silna"]
    scale_mapping = {"Brak": 0, "Obecna": 1, "Silna": 2}
    
    # Initialize session state for sentiment buttons if needed
    for key in SENTIMENTS.keys():
        if f"sent_val_{key}" not in st.session_state:
            st.session_state[f"sent_val_{key}"] = "Brak"
    
    # Create compact rows for each sentiment
    for key, data in SENTIMENTS.items():
        definition = DEFINITIONS["sentiments"].get(key, "")
        selected_label = render_scale_row(
            row_key=key,
            data=data,
            definition=definition,
            state_prefix="sent",
            scale_options=scale_options,
            scale_mapping=scale_mapping,
            layout=(2.0, 2.0),
            desc_max_width="100%",
            button_font_size="0.55rem"
        )
        sentiment_values[key] = scale_mapping[selected_label]
    
    st.markdown("")
    
    # Navigation buttons - Wróć (puste), Zasady (środek), DALEJ (prawo)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📋 Zasady kodowania", key="rules_btn_sent", use_container_width=True):
            st.session_state.screen = 'instructions'
            st.rerun()
    with col3:
        if st.button("DALEJ → Emocje", use_container_width=True, type="primary"):
            st.session_state.current_coding['sentiment'] = sentiment_values
            st.session_state.coding_stage = 'emotion'
            st.rerun()


def emotion_coding_ui(text):
    """UI for emotion coding."""
    # Step indicator
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
        <div style="background: #34495e; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1rem;">2</div>
        <div>
            <div style="font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px;">Krok 2 z 2</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: #fff;">Emocje</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Text to analyze
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); padding: 16px 20px; border-radius: 10px; border-left: 4px solid #34495e; border-right: 4px solid #34495e; margin-bottom: 15px;">
        <div style="font-size: 0.7rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;"> Tekst do oceny</div>
        <p style="font-size: 1.05rem; line-height: 1.6; color: #e0e0e0; margin: 0;">{text}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Instruction
    st.markdown("""
    <div style="font-size: 0.8rem; color: #b0b0b0; margin-bottom: 10px;">
        ↓ Dla każdej emocji wybierz poziom natężenia
    </div>
    """, unsafe_allow_html=True)
    
    emotion_values = {}
    
    # Scale options (3-level)
    scale_options = ["Brak", "Obecna", "Silna"]
    scale_mapping = {"Brak": 0, "Obecna": 1, "Silna": 2}
    
    # Initialize session state for emotion buttons if needed
    for key in EMOTIONS.keys():
        if f"emo_val_{key}" not in st.session_state:
            st.session_state[f"emo_val_{key}"] = "Brak"
    
    emotions_list = list(EMOTIONS.items())
    
    # Display emotions in two columns
    for idx in range(0, len(emotions_list), 2):
        row_cols = st.columns(2)
        for offset in range(2):
            if idx + offset >= len(emotions_list):
                continue
            key, data = emotions_list[idx + offset]
            definition = DEFINITIONS["emotions"].get(key, "")
            with row_cols[offset]:
                selected_label = render_scale_row(
                    row_key=key,
                    data=data,
                    definition=definition,
                    state_prefix="emo",
                    scale_options=scale_options,
                    scale_mapping=scale_mapping,
                    buttons_below=True,
                    desc_max_width="320px",
                    button_font_size="calc(0.7rem - 2px)",
                    button_padding="4px 8px"
                )
                emotion_values[key] = scale_mapping[selected_label]
    
    st.markdown("")
    
    # Navigation buttons - Wróć (lewo), Zasady (środek), ZAPISZ (prawo)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← Wróć", use_container_width=True):
            st.session_state.coding_stage = 'sentiment'
            st.rerun()
    
    with col2:
        if st.button("📋 Zasady kodowania", key="rules_btn_emo", use_container_width=True):
            st.session_state.screen = 'instructions'
            st.rerun()
    
    with col3:
        if st.button("ZAPISZ i dalej →", use_container_width=True, type="primary"):
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
            
            # Reset for next element - clear all button states
            for skey in SENTIMENTS.keys():
                st.session_state[f"sent_val_{skey}"] = "Brak"
            for ekey in EMOTIONS.keys():
                st.session_state[f"emo_val_{ekey}"] = "Brak"
            
            st.session_state.current_coding = {'sentiment': {}, 'emotion': {}}
            st.session_state.coding_stage = 'sentiment'
            st.session_state.current_index += 1
            
            if st.session_state.current_index >= len(st.session_state.session_elements):
                save_results()
                st.session_state.screen = 'end'
            
            st.rerun()
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
    total_coded = len(st.session_state.results)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 30px; background: rgba(255,255,255,0.05); border-radius: 15px;">
            <h2 style="color: #4CAF50; margin-bottom: 10px;">{total_coded}</h2>
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
        page_title="Kodowanie sentymentu i emocji",
        page_icon="📋",
        layout="centered"
    )
    
    initialize_session()
    
    if st.session_state.screen == 'start':
        start_screen()
    elif st.session_state.screen == 'instructions':
        instructions_screen()
    elif st.session_state.screen == 'coding':
        coding_screen()
    elif st.session_state.screen == 'end':
        end_screen()


if __name__ == "__main__":
    main()
