"""
Aplikacja Streamlit do analizy zgodności kodowania sentymentu i emocji.

Porównuje kodowanie manualne z dwoma systemami kodowania automatycznego:
- SENT_EMO (narzędzie 1)
- SENT_EMO_LLM (narzędzie 2 - LLM)

Uruchomienie:
cd app/wer_llm/sent_emo_app/wyniki_analiza_sent_emo
streamlit run analiza_zgodnosci_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import plotly.graph_objects as go
import plotly.express as px

# Import custom modules
import data_loader
import agreement_metrics
import visualizations


# Page configuration
st.set_page_config(
    page_title="Analiza Zgodności Kodowania",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
CUSTOM_CSS = """
<style>
    /* Main styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        color: white;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2rem;
    }
    
    .main-header p {
        margin: 5px 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin: 10px 0;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Status indicators */
    .status-success {
        color: #4CAF50;
        font-weight: 600;
    }
    
    .status-error {
        color: #f44336;
        font-weight: 600;
    }
    
    .status-warning {
        color: #FF9800;
        font-weight: 600;
    }
    
    /* Info boxes */
    .info-box {
        background: rgba(102, 126, 234, 0.1);
        border-left: 4px solid #667eea;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #667eea;
        margin: 25px 0 15px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid #667eea;
    }
    
    /* Data summary */
    .data-summary {
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'parquet_data' not in st.session_state:
        st.session_state.parquet_data = None
    if 'manual_data' not in st.session_state:
        st.session_state.manual_data = None
    if 'merged_data' not in st.session_state:
        st.session_state.merged_data = None
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'gsheets_connected' not in st.session_state:
        st.session_state.gsheets_connected = False
    if 'auto_load_attempted' not in st.session_state:
        st.session_state.auto_load_attempted = False
    if 'has_sent_emo' not in st.session_state:
        st.session_state.has_sent_emo = False
    if 'has_sent_emo_llm' not in st.session_state:
        st.session_state.has_sent_emo_llm = False
    if 'has_manual' not in st.session_state:
        st.session_state.has_manual = False
    
    # Threshold settings for automatic coding systems
    if 'sent_emo_threshold_low' not in st.session_state:
        st.session_state.sent_emo_threshold_low = 0.15
    if 'sent_emo_threshold_high' not in st.session_state:
        st.session_state.sent_emo_threshold_high = 0.75
    if 'sent_emo_llm_threshold_low' not in st.session_state:
        st.session_state.sent_emo_llm_threshold_low = 0.15
    if 'sent_emo_llm_threshold_high' not in st.session_state:
        st.session_state.sent_emo_llm_threshold_high = 0.75
    
    # Manual coding settings
    if 'selected_coders' not in st.session_state:
        st.session_state.selected_coders = ['1_JA']  # Default to main coder
    if 'use_aggregated_manual' not in st.session_state:
        st.session_state.use_aggregated_manual = False
    if 'aggregation_method' not in st.session_state:
        st.session_state.aggregation_method = 'majority'  # majority, mean, or median


def sidebar_panel():
    """Create sidebar with data loading and filtering options."""
    st.sidebar.markdown("## ⚙️ Konfiguracja")
    
    # Section 1: Source Selection (at the top - always visible if data loaded)
    if st.session_state.get('data_loaded', False):
        st.sidebar.markdown("#### 📊 Źródła danych")
        
        # Available sources - checkboxes in columns
        col1, col2, col3 = st.sidebar.columns(3)
        
        selected_sources = []
        
        with col1:
            if st.session_state.get('has_sent_emo', False):
                if st.checkbox("SENT_EMO", value=True, key="source_select_sent_emo"):
                    selected_sources.append("SENT_EMO")
        
        with col2:
            if st.session_state.get('has_sent_emo_llm', False):
                if st.checkbox("LLM", value=True, key="source_select_sent_emo_llm"):
                    selected_sources.append("SENT_EMO_LLM")
        
        with col3:
            # Manual is always available if Google Sheets is connected
            if st.session_state.get('gsheets_connected', False):
                if st.checkbox("Manual", value=True, key="source_select_manual"):
                    selected_sources.append("Manual")
                    st.session_state.has_manual = True
            else:
                st.checkbox("Manual", value=False, disabled=True, key="source_select_manual_disabled", help="Brak połączenia z Google Sheets")
        
        # Update selected sources in session state
        if len(selected_sources) >= 2:
            st.session_state.selected_sources = selected_sources
        else:
            st.sidebar.caption("⚠️ Wybierz min. 2 źródła")
            all_sources = []
            if st.session_state.get('has_sent_emo', False):
                all_sources.append("SENT_EMO")
            if st.session_state.get('has_sent_emo_llm', False):
                all_sources.append("SENT_EMO_LLM")
            if st.session_state.get('gsheets_connected', False):
                all_sources.append("Manual")
            st.session_state.selected_sources = all_sources
        
        st.sidebar.markdown("---")
    
    # Section 2: Analysis Options (compact)
    if st.session_state.get('data_loaded', False):
        st.sidebar.markdown("#### 📈 Analiza")
        
        analysis_type = st.sidebar.radio(
            "Typ",
            options=["Sentyment", "Emocje", "Wszystko"],
            horizontal=True,
            label_visibility="collapsed"
        )
        st.session_state.analysis_type = analysis_type
        
        # Metric selection - compact
        col1, col2 = st.sidebar.columns(2)
        with col1:
            show_kappa = st.checkbox("Kappa", value=True, key="metric_kappa")
            show_alpha = st.checkbox("Alpha", value=True, key="metric_alpha")
        with col2:
            show_icc = st.checkbox("ICC", value=True, key="metric_icc")
            show_correlation = st.checkbox("Korelacje", value=True, key="metric_corr")
        
        st.session_state.metrics_config = {
            'kappa': show_kappa,
            'alpha': show_alpha,
            'icc': show_icc,
            'correlation': show_correlation
        }
        
        # Update filtered data (no filtering, just copy)
        st.session_state.filtered_data = st.session_state.merged_data
        
        st.sidebar.markdown("---")
    
    # Section 3: Settings (compact)
    st.sidebar.markdown("#### ⚙️ Ustawienia")
    
    # Threshold Settings
    if st.session_state.get('has_sent_emo', False) or st.session_state.get('has_sent_emo_llm', False):
        with st.sidebar.expander("Progi konwersji (0-1 → Brak/Obecna/Silna)", expanded=False):
            st.caption("Brak | Obecna | Silna")
            
            # SENT_EMO thresholds
            if st.session_state.get('has_sent_emo', False):
                st.markdown("**SENT_EMO**")
                col1, col2 = st.columns(2)
                with col1:
                    sent_emo_low = st.slider("Dolny", 0.0, 1.0, st.session_state.sent_emo_threshold_low, 0.05, key="settings_sent_emo_low_slider")
                with col2:
                    sent_emo_high = st.slider("Górny", sent_emo_low, 1.0, max(st.session_state.sent_emo_threshold_high, sent_emo_low), 0.05, key="settings_sent_emo_high_slider")
                st.session_state.sent_emo_threshold_low = sent_emo_low
                st.session_state.sent_emo_threshold_high = sent_emo_high
            
            # SENT_EMO_LLM thresholds
            if st.session_state.get('has_sent_emo_llm', False):
                st.markdown("**SENT_EMO_LLM**")
                col1, col2 = st.columns(2)
                with col1:
                    sent_emo_llm_low = st.slider("Dolny", 0.0, 1.0, st.session_state.sent_emo_llm_threshold_low, 0.05, key="settings_sent_emo_llm_low_slider")
                with col2:
                    sent_emo_llm_high = st.slider("Górny", sent_emo_llm_low, 1.0, max(st.session_state.sent_emo_llm_threshold_high, sent_emo_llm_low), 0.05, key="settings_sent_emo_llm_high_slider")
                st.session_state.sent_emo_llm_threshold_low = sent_emo_llm_low
                st.session_state.sent_emo_llm_threshold_high = sent_emo_llm_high
            
            # Button to apply threshold changes
            if st.session_state.get('data_loaded', False):
                if st.button("🔄 Zastosuj progi", type="primary", use_container_width=True, key="settings_apply_thresholds_btn"):
                    parquet_path = st.session_state.get('parquet_path', r"C:\aktywne\dysk-M\sdns\dr-fn\Analiza_Treści_Fake_News\fn_data_analysis\data\interim\posts.parquet")
                    load_data(parquet_path)
                    st.success("✅ Zastosowano!")
    
    # === MANUAL CODING SETTINGS ===
    if st.session_state.get('gsheets_connected', False) and st.session_state.get('manual_data') is not None:
        with st.sidebar.expander("👥 Ustawienia kodowania manualnego", expanded=True):
            manual_df = st.session_state.manual_data
            
            # Get available coders
            available_coders = sorted(manual_df['coder_id'].unique().tolist())
            
            # Coder selection
            st.markdown("**Wybierz koderów:**")
            default_coders = ['1_JA'] if '1_JA' in available_coders else available_coders[:1]
            
            selected_coders = st.multiselect(
                "Koderzy",
                options=available_coders,
                default=st.session_state.get('selected_coders', default_coders),
                key="coder_multiselect",
                label_visibility="collapsed"
            )
            
            if selected_coders:
                st.session_state.selected_coders = selected_coders
            else:
                st.warning("Wybierz co najmniej jednego kodera")
                st.session_state.selected_coders = default_coders
            
            # Show coder statistics
            coder_stats = manual_df.groupby('coder_id')['oid'].nunique()
            st.caption(f"📊 Kodowania: {', '.join([f'{c}: {coder_stats.get(c, 0)}' for c in selected_coders])}")
            
            st.markdown("---")
            
            # === AGGREGATION OPTIONS ===
            st.markdown("**Agregacja wielu koderów:**")
            
            use_aggregated = st.checkbox(
                "Używaj zagregowanych danych",
                value=st.session_state.use_aggregated_manual,
                key="use_aggregated_checkbox",
                help="Gdy włączone, dane od wybranych koderów będą agregowane do jednej wartości"
            )
            st.session_state.use_aggregated_manual = use_aggregated
            
            if use_aggregated and len(selected_coders) > 1:
                aggregation_method = st.radio(
                    "Metoda agregacji:",
                    options=['majority', 'mean', 'median'],
                    format_func=lambda x: {
                        'majority': '📊 Większość (moda)',
                        'mean': '📈 Średnia (zaokrąglona)',
                        'median': '📉 Mediana'
                    }[x],
                    index=['majority', 'mean', 'median'].index(st.session_state.aggregation_method),
                    key="aggregation_method_radio"
                )
                st.session_state.aggregation_method = aggregation_method
                
                # Explanation
                with st.expander("ℹ️ Jak działa agregacja?"):
                    st.markdown("""
                    **Agregacja danych od wielu koderów:**
                    
                    Gdy wybierzesz więcej niż jednego kodera, system może zagregować 
                    ich oceny do pojedynczej wartości dla każdego elementu. 
                    Jest to przydatne przy porównywaniu z systemami automatycznymi.
                    
                    **Metody agregacji:**
                    
                    1. **Większość (moda)** - wybiera najczęściej występującą wartość
                       - Zalecana dla danych kategorycznych/porządkowych
                       - Przy remisie wybiera niższą wartość
                    
                    2. **Średnia (zaokrąglona)** - oblicza średnią i zaokrągla
                       - Daje wartość "konsensusową"
                       - Może dawać wartości pośrednie
                    
                    3. **Mediana** - wybiera wartość środkową
                       - Odporna na wartości skrajne
                       - Dobra przy nierównych rozkładach
                    
                    **Uwaga metodologiczna:**
                    - Agregacja zakłada, że każdy koder ma równą wagę
                    - Elementy zakodowane przez mniej koderów mają mniejszą pewność
                    - W raporcie pokazany będzie poziom zgodności między koderami
                    """)
            elif use_aggregated:
                st.info("Wybierz więcej niż jednego kodera, aby używać agregacji")
    
    # Data Loading
    with st.sidebar.expander("Dane wejściowe", expanded=False):
        # Parquet file selection
        default_path = r"C:\aktywne\dysk-M\sdns\dr-fn\Analiza_Treści_Fake_News\fn_data_analysis\data\interim\posts.parquet"
        parquet_path = st.text_input("Plik Parquet", value=default_path, key="parquet_path_input", label_visibility="collapsed")
        
        if st.button("🔄 Wczytaj dane", type="primary", use_container_width=True, key="load_data_btn"):
            st.session_state.parquet_path = parquet_path
            load_data(parquet_path)
        
        # Connection status - compact
        st.caption("**Status:**")
        parquet_ok = st.session_state.get('parquet_data') is not None
        gsheets_ok = st.session_state.get('gsheets_connected', False)
        st.markdown(f"📊 Parquet: {'✓' if parquet_ok else '✗'} &nbsp; 📝 Sheets: {'✓' if gsheets_ok else '✗'}", unsafe_allow_html=True)
        
        # Link to Google Sheets
        spreadsheet_id = st.secrets.get("SPREADSHEET_ID", "")
        if spreadsheet_id:
            sheets_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            st.link_button("🔗 Otwórz arkusz", sheets_url)
    
    # Auto-load data on first run
    if not st.session_state.get('data_loaded', False) and not st.session_state.get('auto_load_attempted', False):
        st.session_state.auto_load_attempted = True
        default_path = r"C:\aktywne\dysk-M\sdns\dr-fn\Analiza_Treści_Fake_News\fn_data_analysis\data\interim\posts.parquet"
        st.session_state.parquet_path = default_path
        load_data(default_path)


def load_data(parquet_path):
    """Load data from Parquet and Google Sheets (stored separately, not merged)."""
    with st.spinner("Wczytywanie danych..."):
        # Load Parquet
        parquet_df, parquet_error = data_loader.load_parquet_data(parquet_path)
        if parquet_error:
            st.sidebar.error(f"❌ {parquet_error}")
            return
        
        # Apply thresholds to convert continuous (0-1) to ordinal (0-2) scale
        parquet_df = data_loader.convert_automatic_coding_to_ordinal(
            parquet_df,
            sent_emo_threshold_low=st.session_state.sent_emo_threshold_low,
            sent_emo_threshold_high=st.session_state.sent_emo_threshold_high,
            sent_emo_llm_threshold_low=st.session_state.sent_emo_llm_threshold_low,
            sent_emo_llm_threshold_high=st.session_state.sent_emo_llm_threshold_high
        )
        
        st.session_state.parquet_data = parquet_df
        
        # Check which data sources are available in Parquet (check original columns)
        sent_emo_cols_orig = data_loader.get_sentiment_columns(use_ordinal=False)['sent_emo']
        sent_emo_llm_cols_orig = data_loader.get_sentiment_columns(use_ordinal=False)['sent_emo_llm']
        
        st.session_state.has_sent_emo = all(col in parquet_df.columns for col in sent_emo_cols_orig[:1])
        st.session_state.has_sent_emo_llm = all(col in parquet_df.columns for col in sent_emo_llm_cols_orig[:1])
        
        st.sidebar.success(f"✅ Parquet: {len(parquet_df)} rekordów")
        
        # Load Google Sheets (stored separately, not merged yet)
        manual_df, manual_error = data_loader.load_manual_coding_data()
        if manual_error:
            st.sidebar.warning(f"⚠️ Google Sheets: {manual_error}")
            st.session_state.gsheets_connected = False
            st.session_state.has_manual = False
            st.session_state.manual_data = None
        elif manual_df is None or len(manual_df) == 0:
            st.sidebar.warning("⚠️ Google Sheets: Brak danych")
            st.session_state.gsheets_connected = True
            st.session_state.has_manual = False
            st.session_state.manual_data = None
        else:
            st.session_state.manual_data = manual_df
            st.session_state.gsheets_connected = True
            st.session_state.has_manual = True
            # Count unique oids in manual data
            unique_oids = manual_df['oid'].nunique()
            total_codings = len(manual_df)
            st.sidebar.success(f"✅ Manual: {unique_oids} elementów ({total_codings} kodowań)")
        
        # Mark as loaded - merged_data will be created dynamically in main_panel
        st.session_state.data_loaded = True


def main_panel():
    """Create main panel with visualizations and statistics."""
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Analiza Zgodności Kodowania Sentymentu i Emocji</h1>
        <p>Porównanie kodowania manualnego z dwoma systemami automatycznymi</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.get('data_loaded', False):
        # Welcome screen
        st.markdown("## 👋 Witaj!")
        
        st.markdown("""
        <div class="info-box">
            <h3>Jak korzystać z aplikacji:</h3>
            <ol>
                <li><strong>Wczytaj dane</strong> - użyj panelu bocznego aby wczytać dane z pliku Parquet i Google Sheets</li>
                <li><strong>Zastosuj filtry</strong> - wybierz interesujące Cię dane (źródła, daty, koderów)</li>
                <li><strong>Wybierz analizę</strong> - określ typ analizy i metryki do obliczenia</li>
                <li><strong>Przeglądaj wyniki</strong> - analizuj wykresy i statystyki zgodności</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Cohen's Kappa</div>
                <div class="metric-value">κ</div>
                <p style="font-size: 0.8rem; margin-top: 10px;">
                Uwzględnia zgodność przypadkową
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Krippendorff's Alpha</div>
                <div class="metric-value">α</div>
                <p style="font-size: 0.8rem; margin-top: 10px;">
                Uniwersalny dla wielu koderów
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">ICC</div>
                <div class="metric-value">ICC</div>
                <p style="font-size: 0.8rem; margin-top: 10px;">
                Dla danych ciągłych i porządkowych
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("👈 **Rozpocznij od wczytania danych w panelu bocznym**")
        
        # Information about data scale
        st.markdown("""
        <div class="info-box">
            <h3>📏 Skala kodowania:</h3>
            <p><strong>Kodowanie manualne (Google Sheets):</strong> Skala 3-punktowa</p>
            <ul style="margin-left: 20px;">
                <li><strong>Brak</strong> - brak cechy</li>
                <li><strong>Obecna</strong> - cecha obecna (nawet śladowo)</li>
                <li><strong>Silna</strong> - silna obecność cechy</li>
            </ul>
            <p style="margin-top: 10px;"><strong>Kodowanie automatyczne (SENT_EMO, SENT_EMO_LLM):</strong> Prawdopodobieństwo 0-1 → konwersja na skalę 3-punktową</p>
            <ul style="margin-left: 20px;">
                <li>Progi konwersji można dostosować w panelu bocznym</li>
                <li>Domyślnie: &lt;0.15 = Brak, 0.15-0.75 = Obecna, ≥0.75 = Silna</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        return
    
    # Get analysis configuration
    analysis_type = st.session_state.get('analysis_type', 'Wszystko')
    selected_sources = st.session_state.get('selected_sources', [])
    
    # Map UI names to internal names
    source_mapping = {
        'SENT_EMO': 'sent_emo',
        'SENT_EMO_LLM': 'sent_emo_llm',
        'Manual': 'manual'
    }
    
    # Convert selected sources to internal format
    sources_to_compare = [source_mapping.get(s, s.lower()) for s in selected_sources if s in source_mapping]
    
    # If no sources available or less than 2, show warning
    if len(sources_to_compare) < 2:
        st.warning("⚠️ Wybierz co najmniej 2 źródła danych do porównania w panelu bocznym.")
        return
    
    # === DYNAMICALLY PREPARE DATA BASED ON SELECTED SOURCES ===
    parquet_df = st.session_state.get('parquet_data')
    manual_df = st.session_state.get('manual_data')
    
    if parquet_df is None:
        st.error("❌ Brak danych z Parquet. Wczytaj dane w panelu bocznym.")
        return
    
    # Get manual coding settings from session state
    selected_coders = st.session_state.get('selected_coders', ['1_JA'])
    use_aggregated_manual = st.session_state.get('use_aggregated_manual', False)
    aggregation_method = st.session_state.get('aggregation_method', 'majority')
    
    # Determine if we should aggregate manual data
    # Aggregate if: option enabled AND more than one coder selected
    should_aggregate = use_aggregated_manual and len(selected_coders) > 1
    
    # Prepare analysis data - this handles the logic of:
    # - Using ALL parquet records when only SENT_EMO/SENT_EMO_LLM are selected
    # - Filtering to common oids when Manual is also selected
    # - Aggregating multiple coders per oid for manual data (if enabled)
    merged_df, data_stats = data_loader.prepare_analysis_data(
        parquet_df,
        manual_df,
        sources_to_compare,
        aggregate_manual=should_aggregate,
        selected_coders=selected_coders,
        aggregation_method=aggregation_method
    )
    
    # Data summary with dynamic info
    st.markdown("## 📈 Podsumowanie danych")
    
    has_manual = 'manual' in sources_to_compare and manual_df is not None
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Rekordów w analizie", data_stats['analysis_records'])
    
    with col2:
        st.metric("Rekordów w Parquet", data_stats['parquet_total'])
    
    with col3:
        if has_manual:
            coders_info = f"{data_stats.get('manual_coders_used', 1)} koderów"
            st.metric("Zakodowanych manualnie", data_stats['manual_unique_oid'], help=coders_info)
        else:
            st.metric("Zakodowanych manualnie", "—")
    
    with col4:
        if has_manual:
            coverage = (data_stats['analysis_records'] / data_stats['parquet_total'] * 100) if data_stats['parquet_total'] > 0 else 0
            st.metric("Pokrycie", f"{coverage:.1f}%")
        else:
            st.metric("Pokrycie", "100%")
    
    # Show info about data scope
    if has_manual:
        coders_str = ", ".join(selected_coders)
        if should_aggregate:
            method_names = {'majority': 'większość (moda)', 'mean': 'średnia', 'median': 'mediana'}
            st.info(f"""ℹ️ **Analiza dla {data_stats['analysis_records']} rekordów**  
            Koderzy: {coders_str}  
            Agregacja: {method_names.get(aggregation_method, aggregation_method)}""")
        else:
            st.info(f"ℹ️ **Analiza dla {data_stats['analysis_records']} rekordów** - koderzy: {coders_str}")
    else:
        st.info(f"ℹ️ **Analiza dla {data_stats['analysis_records']} rekordów** - wszystkie elementy z pliku Parquet")
    
    st.markdown("---")
    
    # Determine which categories to analyze
    if analysis_type == 'Sentyment':
        categories_to_analyze = ['sentiment']
    elif analysis_type == 'Emocje':
        categories_to_analyze = ['emotion']
    else:
        categories_to_analyze = ['sentiment', 'emotion']
    
    # Generate all possible pairs for comparison
    from itertools import combinations
    source_pairs = list(combinations(sources_to_compare, 2))
    
    st.session_state.source_pairs = source_pairs
    
    # Check if all 3 sources are available for comprehensive analysis
    has_all_sources = len(sources_to_compare) == 3
    
    # Check if manual data has multiple coders (for inter-coder tab)
    has_multiple_coders = False
    manual_df_for_intercoder = st.session_state.get('manual_data')
    if manual_df_for_intercoder is not None and len(manual_df_for_intercoder) > 0:
        unique_coders = manual_df_for_intercoder['coder_id'].unique()
        has_multiple_coders = len(unique_coders) > 1
    
    # Tabs for different views - Comprehensive analysis as default first tab
    if has_all_sources:
        if has_multiple_coders:
            tab0, tab_coders, tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🔬 Analiza zbiorcza (3 źródła)",
                "👥 Zgodność koderów",
                "📊 Przegląd metryk parami",
                "🎯 Szczegółowa analiza",
                "📉 Wykresy rozproszenia",
                "📋 Macierze konfuzji",
                "🔍 Podgląd elementów"
            ])
        else:
            tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🔬 Analiza zbiorcza (3 źródła)",
                "📊 Przegląd metryk parami",
                "🎯 Szczegółowa analiza",
                "📉 Wykresy rozproszenia",
                "📋 Macierze konfuzji",
                "🔍 Podgląd elementów"
            ])
            tab_coders = None
        
        with tab0:
            show_comprehensive_analysis(merged_df, categories_to_analyze, sources_to_compare)
        
        if tab_coders is not None:
            with tab_coders:
                show_intercoder_agreement(manual_df_for_intercoder, categories_to_analyze)
    else:
        if has_multiple_coders:
            tab_coders, tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "👥 Zgodność koderów",
                "📊 Przegląd metryk",
                "🎯 Szczegółowa analiza",
                "📉 Wykresy rozproszenia",
                "📋 Macierze konfuzji",
                "🔍 Podgląd elementów"
            ])
            
            with tab_coders:
                show_intercoder_agreement(manual_df_for_intercoder, categories_to_analyze)
        else:
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Przegląd metryk",
                "🎯 Szczegółowa analiza",
                "📉 Wykresy rozproszenia",
                "📋 Macierze konfuzji",
                "🔍 Podgląd elementów"
            ])
    
    with tab1:
        show_metrics_overview(merged_df, categories_to_analyze, sources_to_compare)
    
    with tab2:
        show_detailed_analysis(merged_df, categories_to_analyze, sources_to_compare)
    
    with tab3:
        show_scatter_plots(merged_df, categories_to_analyze, sources_to_compare)
    
    with tab4:
        show_confusion_matrices(merged_df, categories_to_analyze, sources_to_compare)
    
    with tab5:
        show_element_preview(merged_df, categories_to_analyze, sources_to_compare)


def show_comprehensive_analysis(df, categories, sources):
    """
    Comprehensive analysis comparing all 3 sources simultaneously.
    Uses multi-rater agreement metrics (Krippendorff's Alpha, Fleiss' Kappa).
    """
    from itertools import combinations
    
    st.markdown("### 🔬 Analiza zbiorcza zgodności trzech źródeł")
    
    # Detailed methodology info
    with st.expander("📚 **Metodologia analizy zgodności międzykoderowej**", expanded=False):
        st.markdown("""
        ### Podstawy teoretyczne
        
        Ta analiza stosuje **zgodność międzykoderową** (inter-rater reliability, IRR) - standardową metodę
        w naukach społecznych do oceny, czy różni koderzy (lub systemy) przypisują te same wartości
        tym samym jednostkom analizy.
        
        ---
        
        ### 📊 Stosowane metryki
        
        #### 1. Krippendorff's Alpha (α)
        **Najbardziej uniwersalna i rygorystyczna miara zgodności.**
        
        - ✅ Obsługuje dowolną liczbę koderów
        - ✅ Obsługuje brakujące dane  
        - ✅ Dostosowuje się do poziomu pomiaru (nominalny, porządkowy, interwałowy)
        - ✅ Poprawia na zgodność przypadkową
        
        **Interpretacja** (Krippendorff, 2004):
        | Wartość | Interpretacja | Rekomendacja |
        |---------|---------------|--------------|
        | α ≥ 0.80 | Wysoka | Wnioski definitywne |
        | 0.667 ≤ α < 0.80 | Akceptowalna | Wnioski wstępne |
        | α < 0.667 | Niska | Odrzucić wnioski |
        
        ---
        
        #### 2. Fleiss' Kappa (κ)
        **Uogólnienie κ Cohena dla więcej niż 2 koderów.**
        
        - Mierzy zgodność ponad przypadkową dla wielu koderów
        - Odpowiednia dla danych kategorycznych
        
        **Interpretacja** (Landis & Koch, 1977):
        | Wartość | Interpretacja |
        |---------|---------------|
        | κ ≥ 0.81 | Prawie doskonała |
        | 0.61 ≤ κ < 0.81 | Znaczna |
        | 0.41 ≤ κ < 0.61 | Umiarkowana |
        | 0.21 ≤ κ < 0.41 | Słaba |
        | κ < 0.21 | Niewielka |
        
        ---
        
        #### 3. ICC (Intraclass Correlation Coefficient)
        **Korelacja wewnątrzklasowa - odpowiednia dla danych ciągłych i porządkowych.**
        
        Model: ICC(2,1) - dwuczynnikowy losowy, pojedyncza miara, zgodność absolutna.
        
        **Interpretacja** (Koo & Li, 2016):
        | Wartość | Interpretacja |
        |---------|---------------|
        | ICC ≥ 0.90 | Doskonała |
        | 0.75 ≤ ICC < 0.90 | Dobra |
        | 0.50 ≤ ICC < 0.75 | Umiarkowana |
        | ICC < 0.50 | Słaba |
        
        ---
        
        #### 4. Cohen's Kappa (ważona) - dla par koderów
        **Stosowana z wagami kwadratowymi dla danych porządkowych.**
        
        Wagi kwadratowe (quadratic weights) są standardem dla skal porządkowych,
        ponieważ większe różnice w kodowaniu (np. 0 vs 2) są penalizowane bardziej
        niż mniejsze różnice (0 vs 1).
        
        ---
        
        ### 📏 Poziom pomiaru danych
        
        **Skala 3-punktowa (0-2) jest traktowana jako porządkowa (ordinal):**
        - Brak (0) < Obecna (1) < Silna (2)
        - Zachowuje porządek, ale odległości między kategoriami nie są równe
        
        ---
        
        ### 📖 Literatura
        
        - Krippendorff, K. (2004). *Content Analysis: An Introduction to Its Methodology*. Sage.
        - Landis, J.R. & Koch, G.G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33, 159-174.
        - Koo, T.K. & Li, M.Y. (2016). A guideline of selecting and reporting intraclass correlation coefficients. *Journal of Chiropractic Medicine*, 15(2), 155-163.
        - Cohen, J. (1968). Weighted kappa. *Psychological Bulletin*, 70(4), 213-220.
        """)
    
    st.info("""
    **Analizowane źródła kodowania:**
    - **SENT_EMO** - kodowanie automatyczne (model ML)
    - **SENT_EMO_LLM** - kodowanie automatyczne (LLM)
    - **Manual** - kodowanie manualne (ekspert)
    
    **Typ danych:** Skala porządkowa 3-punktowa (Brak → Obecna → Silna)
    """)
    
    labels = data_loader.get_category_labels()
    
    source_names = {
        'sent_emo': 'SENT_EMO',
        'sent_emo_llm': 'SENT_EMO_LLM',
        'manual': 'Manual'
    }
    
    for cat_type in categories:
        cat_name = 'Sentyment' if cat_type == 'sentiment' else 'Emocje'
        st.markdown(f"## {cat_name}")
        
        if cat_type == 'sentiment':
            cols_dict = data_loader.get_sentiment_columns()
            cat_labels = labels['sentiments']
        else:
            cols_dict = data_loader.get_emotion_columns()
            cat_labels = labels['emotions']
        
        # Collect data for all sources
        comprehensive_results = []
        
        for i, (cat_key, cat_label) in enumerate(cat_labels.items()):
            cols = [cols_dict[s][i] for s in sources if s in cols_dict]
            
            # Check if all columns exist
            if not all(c in df.columns for c in cols):
                continue
            
            # Get data from all sources
            data_matrix = df[cols].copy()
            
            # Remove rows with any NaN
            valid_mask = ~data_matrix.isna().any(axis=1)
            if valid_mask.sum() < 10:
                continue
            
            clean_data = data_matrix[valid_mask]
            n_samples = len(clean_data)
            
            # Compute multi-rater metrics
            # Krippendorff's Alpha for multiple raters (with CI for detailed analysis)
            alpha = None
            alpha_ci = None
            try:
                # Use the enhanced version with bootstrap CI (slower but more informative)
                alpha_result = agreement_metrics.compute_krippendorff_alpha_with_ci(
                    clean_data.values,
                    level_of_measurement='ordinal',
                    n_bootstrap=500  # Reduced for performance
                )
                if alpha_result and not np.isnan(alpha_result['value']):
                    alpha = alpha_result['value']
                    alpha_ci = (alpha_result['ci_lower'], alpha_result['ci_upper'])
            except:
                # Fallback to simple version
                try:
                    alpha = agreement_metrics.compute_krippendorff_alpha_multi(
                        clean_data.values.T,
                        data_type='ordinal'
                    )
                except:
                    alpha = None
            
            # Fleiss' Kappa
            try:
                fleiss_kappa = agreement_metrics.compute_fleiss_kappa(clean_data.values)
            except:
                fleiss_kappa = None
            
            # ICC for multiple raters
            try:
                icc_result = agreement_metrics.compute_icc_multi(clean_data.values)
            except:
                icc_result = None
            
            # Pairwise agreement statistics (with quadratic weights for ordinal data)
            pairwise_kappas = []
            source_pairs = list(combinations(range(len(sources)), 2))
            for idx1, idx2 in source_pairs:
                try:
                    kappa = agreement_metrics.compute_cohens_kappa(
                        clean_data.iloc[:, idx1].values,
                        clean_data.iloc[:, idx2].values,
                        weights='quadratic'  # quadratic weights for ordinal data
                    )
                    if kappa:
                        pairwise_kappas.append(kappa['value'])
                except:
                    pass
            
            avg_kappa = np.mean(pairwise_kappas) if pairwise_kappas else None
            
            # Distribution statistics
            distributions = {}
            for j, source in enumerate(sources):
                source_data = clean_data.iloc[:, j]
                distributions[source_names[source]] = {
                    'mean': source_data.mean(),
                    'std': source_data.std(),
                    'mode': source_data.mode().iloc[0] if len(source_data.mode()) > 0 else None,
                    'dist_0': (source_data == 0).sum() / len(source_data) * 100,
                    'dist_1': (source_data == 1).sum() / len(source_data) * 100,
                    'dist_2': (source_data == 2).sum() / len(source_data) * 100,
                }
            
            comprehensive_results.append({
                'category': cat_label,
                'n_samples': n_samples,
                'krippendorff_alpha': alpha,
                'krippendorff_alpha_ci': alpha_ci,  # Confidence interval tuple
                'fleiss_kappa': fleiss_kappa,
                'icc': icc_result,
                'avg_pairwise_kappa': avg_kappa,
                'distributions': distributions
            })
        
        if not comprehensive_results:
            st.warning(f"Brak wystarczających danych dla {cat_name.lower()}")
            continue
        
        # === Summary Table ===
        st.markdown("### 📋 Tabela zbiorcza metryk zgodności")
        
        summary_data = []
        for result in comprehensive_results:
            row = {
                'Kategoria': result['category'],
                'N': result['n_samples'],
            }
            
            # Krippendorff's Alpha with optional CI
            if result['krippendorff_alpha'] is not None:
                alpha_val = result['krippendorff_alpha']
                ci = result.get('krippendorff_alpha_ci')
                if ci and ci[0] is not None and not np.isnan(ci[0]):
                    row["Krippendorff's α"] = f"{alpha_val:.3f} [{ci[0]:.2f}, {ci[1]:.2f}]"
                else:
                    row["Krippendorff's α"] = f"{alpha_val:.3f}"
            else:
                row["Krippendorff's α"] = "—"
            
            if result['fleiss_kappa'] is not None:
                row["Fleiss' κ"] = f"{result['fleiss_kappa']:.3f}"
            else:
                row["Fleiss' κ"] = "—"
            
            if result['icc'] is not None:
                row['ICC'] = f"{result['icc']:.3f}"
            else:
                row['ICC'] = "—"
            
            if result['avg_pairwise_kappa'] is not None:
                row['Śr. κ parami'] = f"{result['avg_pairwise_kappa']:.3f}"
            else:
                row['Śr. κ parami'] = "—"
            
            # Interpretation
            alpha_val = result['krippendorff_alpha']
            if alpha_val is not None:
                if alpha_val >= 0.8:
                    row['Interpretacja'] = '✅ Wysoka'
                elif alpha_val >= 0.667:
                    row['Interpretacja'] = '⚠️ Akceptowalna'
                elif alpha_val >= 0.4:
                    row['Interpretacja'] = '⚡ Umiarkowana'
                else:
                    row['Interpretacja'] = '❌ Niska'
            else:
                row['Interpretacja'] = "—"
            
            summary_data.append(row)
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        # === Interpretation Guide ===
        with st.expander("📖 Interpretacja metryk", expanded=False):
            st.markdown("""
            **Krippendorff's Alpha (α):**
            - ≥ 0.80: Wysoka zgodność (wymagana dla wniosków definitywnych)
            - 0.667–0.80: Akceptowalna (pozwala na wstępne wnioski)
            - 0.40–0.667: Umiarkowana (wymaga ostrożności w interpretacji)
            - < 0.40: Niska (dane nierzetelne)
            
            **Fleiss' Kappa (κ):**
            - ≥ 0.75: Doskonała zgodność
            - 0.40–0.75: Dobra do umiarkowanej
            - < 0.40: Słaba zgodność
            
            **ICC (Intraclass Correlation):**
            - ≥ 0.90: Doskonała
            - 0.75–0.90: Dobra
            - 0.50–0.75: Umiarkowana
            - < 0.50: Słaba
            """)
        
        # === Visualization: Heatmap of metrics ===
        st.markdown("### 📊 Wizualizacja porównawcza")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Bar chart comparing Krippendorff's Alpha across categories
            alpha_values = {r['category']: r['krippendorff_alpha'] 
                          for r in comprehensive_results 
                          if r['krippendorff_alpha'] is not None}
            
            if alpha_values:
                fig = go.Figure()
                
                categories_list = list(alpha_values.keys())
                values = list(alpha_values.values())
                
                # Color based on interpretation
                colors = ['#2ecc71' if v >= 0.8 else '#f39c12' if v >= 0.667 else '#e74c3c' 
                         for v in values]
                
                fig.add_trace(go.Bar(
                    x=categories_list,
                    y=values,
                    marker_color=colors,
                    text=[f'{v:.3f}' for v in values],
                    textposition='outside'
                ))
                
                # Add reference lines
                fig.add_hline(y=0.8, line_dash="dash", line_color="green", 
                             annotation_text="Wysoka (0.8)")
                fig.add_hline(y=0.667, line_dash="dash", line_color="orange", 
                             annotation_text="Akceptowalna (0.667)")
                
                fig.update_layout(
                    title="Krippendorff's Alpha według kategorii",
                    xaxis_title="Kategoria",
                    yaxis_title="Alpha",
                    yaxis_range=[0, 1],
                    showlegend=False,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True, key=f"alpha_bar_{cat_type}")
        
        with col2:
            # Distribution comparison across sources
            if comprehensive_results:
                # Select first category for detailed distribution
                first_result = comprehensive_results[0]
                
                fig = go.Figure()
                
                x_labels = ['Brak', 'Obecna', 'Silna']
                
                for source_name, dist in first_result['distributions'].items():
                    fig.add_trace(go.Bar(
                        name=source_name,
                        x=x_labels,
                        y=[dist['dist_0'], dist['dist_1'], dist['dist_2']],
                        text=[f'{dist["dist_0"]:.1f}%', f'{dist["dist_1"]:.1f}%', f'{dist["dist_2"]:.1f}%'],
                        textposition='outside'
                    ))
                
                fig.update_layout(
                    title=f"Rozkład wartości: {first_result['category']}",
                    xaxis_title="Poziom natężenia",
                    yaxis_title="Procent przypadków",
                    barmode='group',
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02)
                )
                
                st.plotly_chart(fig, use_container_width=True, key=f"dist_bar_{cat_type}")
        
        # === Pairwise Comparison Matrix ===
        st.markdown("### 🔗 Macierz zgodności parami")
        
        # Create a heatmap showing pairwise agreement
        st.markdown("""
        Poniższa macierz pokazuje średnią zgodność (ważona κ) między każdą parą źródeł
        dla wszystkich kategorii łącznie.
        """)
        
        # Compute average pairwise metrics
        source_list = [source_names[s] for s in sources]
        n_sources = len(source_list)
        
        pairwise_matrix = np.zeros((n_sources, n_sources))
        pairwise_counts = np.zeros((n_sources, n_sources))
        
        for result in comprehensive_results:
            for j, source in enumerate(sources):
                for k, source2 in enumerate(sources):
                    if j == k:
                        pairwise_matrix[j, k] = 1.0
                        pairwise_counts[j, k] = 1
                    elif j < k:
                        col1 = cols_dict[source][list(cat_labels.keys()).index(
                            [key for key, val in cat_labels.items() if val == result['category']][0]
                        )]
                        col2 = cols_dict[source2][list(cat_labels.keys()).index(
                            [key for key, val in cat_labels.items() if val == result['category']][0]
                        )]
                        
                        if col1 in df.columns and col2 in df.columns:
                            data1 = df[col1]
                            data2 = df[col2]
                            valid = ~(data1.isna() | data2.isna())
                            
                            if valid.sum() > 0:
                                try:
                                    kappa = agreement_metrics.compute_cohens_kappa(
                                        data1[valid].values,
                                        data2[valid].values,
                                        weights='quadratic'  # quadratic weights for ordinal data
                                    )
                                    if kappa:
                                        pairwise_matrix[j, k] += kappa['value']
                                        pairwise_matrix[k, j] += kappa['value']
                                        pairwise_counts[j, k] += 1
                                        pairwise_counts[k, j] += 1
                                except:
                                    pass
        
        # Average
        with np.errstate(divide='ignore', invalid='ignore'):
            pairwise_matrix = np.where(pairwise_counts > 0, 
                                       pairwise_matrix / pairwise_counts, 
                                       np.nan)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pairwise_matrix,
            x=source_list,
            y=source_list,
            colorscale='RdYlGn',
            zmin=0,
            zmax=1,
            text=[[f'{v:.3f}' if not np.isnan(v) else '—' for v in row] for row in pairwise_matrix],
            texttemplate='%{text}',
            textfont={"size": 14},
            hovertemplate='%{y} vs %{x}: %{z:.3f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Średnia zgodność (ważona κ) między źródłami",
            height=350,
            xaxis_title="",
            yaxis_title=""
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"pairwise_heatmap_{cat_type}")
        
        # === Statistical Summary ===
        st.markdown("### 📈 Podsumowanie statystyczne")
        
        col1, col2, col3 = st.columns(3)
        
        # Calculate overall statistics
        all_alphas = [r['krippendorff_alpha'] for r in comprehensive_results 
                     if r['krippendorff_alpha'] is not None]
        all_iccs = [r['icc'] for r in comprehensive_results 
                   if r['icc'] is not None]
        
        with col1:
            if all_alphas:
                mean_alpha = np.mean(all_alphas)
                st.metric(
                    "Średnia Krippendorff's α",
                    f"{mean_alpha:.3f}",
                    delta="Wysoka" if mean_alpha >= 0.8 else "Akceptowalna" if mean_alpha >= 0.667 else "Umiarkowana"
                )
        
        with col2:
            if all_iccs:
                mean_icc = np.mean(all_iccs)
                st.metric(
                    "Średnia ICC",
                    f"{mean_icc:.3f}",
                    delta="Dobra" if mean_icc >= 0.75 else "Umiarkowana"
                )
        
        with col3:
            # Count categories with high agreement
            high_agreement = sum(1 for a in all_alphas if a >= 0.667)
            total_cats = len(all_alphas)
            st.metric(
                "Kategorie z akceptowalną zgodnością",
                f"{high_agreement}/{total_cats}",
                delta=f"{high_agreement/total_cats*100:.0f}%" if total_cats > 0 else "0%"
            )
        
        st.markdown("---")
    
    # === Final Conclusions ===
    st.markdown("## 🎯 Wnioski końcowe")
    
    # Generate automatic conclusions based on results
    all_results = []
    for cat_type in categories:
        if cat_type == 'sentiment':
            cols_dict = data_loader.get_sentiment_columns()
            cat_labels = labels['sentiments']
        else:
            cols_dict = data_loader.get_emotion_columns()
            cat_labels = labels['emotions']
        
        for i, (cat_key, cat_label) in enumerate(cat_labels.items()):
            cols = [cols_dict[s][i] for s in sources if s in cols_dict]
            if all(c in df.columns for c in cols):
                data_matrix = df[cols].dropna()
                if len(data_matrix) >= 10:
                    try:
                        alpha = agreement_metrics.compute_krippendorff_alpha_multi(
                            data_matrix.values.T, data_type='ordinal'
                        )
                        all_results.append({'category': cat_label, 'type': cat_type, 'alpha': alpha})
                    except:
                        pass
    
    if all_results:
        # High agreement categories
        high = [r for r in all_results if r['alpha'] and r['alpha'] >= 0.8]
        acceptable = [r for r in all_results if r['alpha'] and 0.667 <= r['alpha'] < 0.8]
        low = [r for r in all_results if r['alpha'] and r['alpha'] < 0.667]
        
        st.markdown(f"""
        **Podsumowanie analizy zgodności trzech źródeł kodowania:**
        
        - ✅ **Wysoka zgodność** ({len(high)} kategorii): {', '.join([r['category'] for r in high]) or 'brak'}
        - ⚠️ **Akceptowalna zgodność** ({len(acceptable)} kategorii): {', '.join([r['category'] for r in acceptable]) or 'brak'}
        - ❌ **Niska zgodność** ({len(low)} kategorii): {', '.join([r['category'] for r in low]) or 'brak'}
        
        **Rekomendacje:**
        - Kategorie z wysoką zgodnością (α ≥ 0.8) mogą być wykorzystane do analiz statystycznych
        - Kategorie z akceptowalną zgodnością (α ≥ 0.667) wymagają ostrożności w interpretacji
        - Kategorie z niską zgodnością wymagają rewizji definicji lub dodatkowego szkolenia koderów
        """)


def show_intercoder_agreement(manual_df, categories):
    """
    Show inter-coder agreement analysis for manual coders only.
    This allows comparison of agreement between human coders before comparing with automatic systems.
    """
    import numpy as np
    from itertools import combinations
    
    st.markdown("### 👥 Analiza zgodności międzykoderowej (koderzy manualni)")
    
    if manual_df is None or len(manual_df) == 0:
        st.warning("Brak danych z kodowania manualnego")
        return
    
    # Get available coders
    coders = sorted(manual_df['coder_id'].unique().tolist())
    
    if len(coders) < 2:
        st.info("Potrzebnych jest co najmniej 2 koderów do analizy zgodności")
        return
    
    # Methodology explanation
    with st.expander("📚 **O analizie zgodności międzykoderowej**", expanded=False):
        st.markdown("""
        ### Cel analizy
        
        Ta zakładka pozwala ocenić **zgodność między koderami ludzkimi** zanim 
        porównasz ich z systemami automatycznymi. Jest to kluczowy krok w analizie 
        treści - jeśli koderzy nie zgadzają się między sobą, trudno oczekiwać 
        wysokiej zgodności z systemami automatycznymi.
        
        ### Dlaczego to ważne?
        
        1. **Walidacja schematu kodowania** - niska zgodność może oznaczać 
           niejasne definicje kategorii
        2. **Identyfikacja trudnych kategorii** - niektóre cechy są trudniejsze 
           do obiektywnej oceny
        3. **Punkt odniesienia** - zgodność między koderami stanowi "górną granicę" 
           dla zgodności z systemami automatycznymi
        
        ### Stosowane metryki
        
        - **Krippendorff's Alpha** - uniwersalna, obsługuje wielu koderów i brakujące dane
        - **Cohen's Kappa** (parami) - dla porównań 2 koderów, z wagami kwadratowymi
        - **Procent zgodności** - prosta miara, ile razy koderzy zgodzili się
        
        ### Interpretacja
        
        | Wartość α/κ | Interpretacja |
        |-------------|---------------|
        | ≥ 0.80 | Wysoka zgodność - można używać do wnioskowania |
        | 0.667 - 0.80 | Akceptowalna - wnioski wstępne |
        | < 0.667 | Niska - wymaga rewizji schematu kodowania |
        """)
    
    # Summary statistics
    st.markdown("#### 📊 Statystyki koderów")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Liczba koderów", len(coders))
    
    with col2:
        total_oid = manual_df['oid'].nunique()
        st.metric("Unikalnych elementów", total_oid)
    
    with col3:
        # Average overlap - how many coders coded each item on average
        avg_coders_per_item = manual_df.groupby('oid')['coder_id'].nunique().mean()
        st.metric("Śr. koderów/element", f"{avg_coders_per_item:.2f}")
    
    # Coder breakdown
    with st.expander("📋 Szczegóły koderów"):
        coder_stats = manual_df.groupby('coder_id').agg({
            'oid': 'nunique',
            'timestamp': 'first'
        }).reset_index()
        coder_stats.columns = ['Koder', 'Zakodowanych elementów', 'Pierwsze kodowanie']
        st.dataframe(coder_stats, use_container_width=True)
    
    st.markdown("---")
    
    # Get column mappings for manual data
    labels = data_loader.get_category_labels()
    
    # Define manual columns for each category type
    manual_cols = {
        'sentiment': ['sentiment_positive', 'sentiment_negative', 'sentiment_neutral'],
        'emotion': [
            'emotion_joy', 'emotion_trust', 'emotion_anticipation', 'emotion_surprise',
            'emotion_fear', 'emotion_sadness', 'emotion_disgust', 'emotion_anger'
        ]
    }
    
    # Filter to available columns
    for cat_type in manual_cols:
        manual_cols[cat_type] = [c for c in manual_cols[cat_type] if c in manual_df.columns]
    
    # === OVERALL AGREEMENT (ALL CODERS) ===
    st.markdown("#### 🔬 Ogólna zgodność wszystkich koderów")
    
    for cat_type in categories:
        if cat_type not in manual_cols or not manual_cols[cat_type]:
            continue
            
        cat_name = 'Sentyment' if cat_type == 'sentiment' else 'Emocje'
        st.markdown(f"##### {cat_name}")
        
        cols_to_analyze = manual_cols[cat_type]
        results = []
        
        for col in cols_to_analyze:
            # Prepare data matrix for Krippendorff's Alpha
            # Rows = coders, Columns = items
            pivot = manual_df.pivot_table(
                index='coder_id', 
                columns='oid', 
                values=col, 
                aggfunc='first'
            )
            
            if pivot.shape[0] < 2:
                continue
            
            # Calculate Krippendorff's Alpha
            data_matrix = pivot.values
            
            try:
                # Use krippendorff library
                import krippendorff
                alpha = krippendorff.alpha(
                    reliability_data=data_matrix,
                    level_of_measurement='ordinal'
                )
            except Exception:
                alpha = np.nan
            
            # Calculate pairwise agreement (average)
            pairwise_agreements = []
            for i, coder1 in enumerate(pivot.index):
                for j, coder2 in enumerate(pivot.index):
                    if i < j:
                        # Find common items
                        c1_data = pivot.loc[coder1]
                        c2_data = pivot.loc[coder2]
                        mask = c1_data.notna() & c2_data.notna()
                        if mask.sum() > 0:
                            agree = (c1_data[mask] == c2_data[mask]).mean()
                            pairwise_agreements.append(agree)
            
            avg_agreement = np.mean(pairwise_agreements) if pairwise_agreements else np.nan
            
            label = labels.get(col, col)
            results.append({
                'Kategoria': label,
                'Krippendorff α': alpha,
                'Śr. % zgodności': avg_agreement * 100 if not np.isnan(avg_agreement) else np.nan,
                'Koderów': pivot.shape[0],
                'Elementów': pivot.shape[1]
            })
        
        if results:
            results_df = pd.DataFrame(results)
            
            # Format and display
            def format_alpha(val):
                if pd.isna(val):
                    return "—"
                color = '#00ff00' if val >= 0.8 else '#ffff00' if val >= 0.667 else '#ff6600'
                return f'<span style="color:{color}">{val:.3f}</span>'
            
            def format_pct(val):
                if pd.isna(val):
                    return "—"
                return f"{val:.1f}%"
            
            # Display with styling
            display_df = results_df.copy()
            display_df['Krippendorff α'] = display_df['Krippendorff α'].apply(lambda x: f"{x:.3f}" if not pd.isna(x) else "—")
            display_df['Śr. % zgodności'] = display_df['Śr. % zgodności'].apply(format_pct)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Summary
            valid_alphas = [r['Krippendorff α'] for r in results if not pd.isna(r['Krippendorff α'])]
            if valid_alphas:
                avg_alpha = np.mean(valid_alphas)
                status = "✅ Wysoka" if avg_alpha >= 0.8 else "⚠️ Akceptowalna" if avg_alpha >= 0.667 else "❌ Niska"
                st.caption(f"Średnia α dla {cat_name.lower()}: {avg_alpha:.3f} ({status})")
    
    st.markdown("---")
    
    # === PAIRWISE AGREEMENT ===
    st.markdown("#### 🔗 Zgodność parami między koderami")
    
    if len(coders) >= 2:
        # Let user select which coders to compare
        col1, col2 = st.columns(2)
        with col1:
            coder1 = st.selectbox("Koder 1", coders, index=0, key="intercoder_coder1")
        with col2:
            coder2 = st.selectbox("Koder 2", [c for c in coders if c != coder1], key="intercoder_coder2")
        
        # Get data for both coders
        c1_df = manual_df[manual_df['coder_id'] == coder1]
        c2_df = manual_df[manual_df['coder_id'] == coder2]
        
        # Find common oids
        common_oids = set(c1_df['oid']) & set(c2_df['oid'])
        
        if len(common_oids) == 0:
            st.warning(f"Brak wspólnych elementów między {coder1} i {coder2}")
        else:
            st.info(f"Wspólnych elementów: {len(common_oids)}")
            
            # Merge on common oids
            c1_common = c1_df[c1_df['oid'].isin(common_oids)].set_index('oid')
            c2_common = c2_df[c2_df['oid'].isin(common_oids)].set_index('oid')
            
            for cat_type in categories:
                if cat_type not in manual_cols or not manual_cols[cat_type]:
                    continue
                    
                cat_name = 'Sentyment' if cat_type == 'sentiment' else 'Emocje'
                st.markdown(f"##### {cat_name} - {coder1} vs {coder2}")
                
                cols_to_analyze = manual_cols[cat_type]
                pairwise_results = []
                
                for col in cols_to_analyze:
                    if col not in c1_common.columns or col not in c2_common.columns:
                        continue
                    
                    # Get aligned data
                    data1 = c1_common[col].reindex(sorted(common_oids))
                    data2 = c2_common[col].reindex(sorted(common_oids))
                    
                    # Remove NaN pairs
                    mask = data1.notna() & data2.notna()
                    d1 = data1[mask].values
                    d2 = data2[mask].values
                    
                    if len(d1) < 2:
                        continue
                    
                    # Calculate metrics
                    try:
                        kappa_result = agreement_metrics.compute_cohens_kappa(d1, d2)
                        kappa = kappa_result['kappa']
                        kappa_ci = kappa_result.get('ci_95', (np.nan, np.nan))
                    except Exception:
                        kappa = np.nan
                        kappa_ci = (np.nan, np.nan)
                    
                    # Percent agreement
                    pct_agree = (d1 == d2).mean() * 100
                    
                    label = labels.get(col, col)
                    pairwise_results.append({
                        'Kategoria': label,
                        'Cohen\'s κ': kappa,
                        'CI 95%': f"[{kappa_ci[0]:.2f}, {kappa_ci[1]:.2f}]" if not np.isnan(kappa_ci[0]) else "—",
                        '% zgodności': pct_agree,
                        'N': len(d1)
                    })
                
                if pairwise_results:
                    pairwise_df = pd.DataFrame(pairwise_results)
                    pairwise_df['Cohen\'s κ'] = pairwise_df['Cohen\'s κ'].apply(lambda x: f"{x:.3f}" if not pd.isna(x) else "—")
                    pairwise_df['% zgodności'] = pairwise_df['% zgodności'].apply(lambda x: f"{x:.1f}%")
                    st.dataframe(pairwise_df, use_container_width=True)
    
    st.markdown("---")
    
    # === AGREEMENT HEATMAP ===
    st.markdown("#### 🗺️ Macierz zgodności między koderami")
    
    # Select category for heatmap
    all_cols = []
    for cat_type in categories:
        if cat_type in manual_cols:
            all_cols.extend(manual_cols[cat_type])
    
    if all_cols:
        selected_col = st.selectbox(
            "Wybierz kategorię",
            all_cols,
            format_func=lambda x: labels.get(x, x),
            key="intercoder_heatmap_col"
        )
        
        # Create agreement matrix
        pivot = manual_df.pivot_table(
            index='coder_id',
            columns='oid',
            values=selected_col,
            aggfunc='first'
        )
        
        agreement_matrix = pd.DataFrame(
            index=pivot.index,
            columns=pivot.index,
            dtype=float
        )
        
        for c1 in pivot.index:
            for c2 in pivot.index:
                if c1 == c2:
                    agreement_matrix.loc[c1, c2] = 1.0
                else:
                    d1 = pivot.loc[c1]
                    d2 = pivot.loc[c2]
                    mask = d1.notna() & d2.notna()
                    if mask.sum() > 0:
                        agreement_matrix.loc[c1, c2] = (d1[mask] == d2[mask]).mean()
                    else:
                        agreement_matrix.loc[c1, c2] = np.nan
        
        # Display heatmap
        fig = px.imshow(
            agreement_matrix.values.astype(float),
            x=agreement_matrix.columns,
            y=agreement_matrix.index,
            labels=dict(x="Koder", y="Koder", color="Zgodność"),
            aspect="auto",
            color_continuous_scale="RdYlGn",
            zmin=0,
            zmax=1,
            text_auto='.2f'
        )
        fig.update_layout(
            title=f"Macierz zgodności - {labels.get(selected_col, selected_col)}",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Interpretation
        avg_off_diag = agreement_matrix.values[np.triu_indices_from(agreement_matrix.values, k=1)].mean()
        st.caption(f"Średnia zgodność (poza diagonalą): {avg_off_diag:.1%}")


def show_metrics_overview(df, categories, sources):
    """Show overview of all metrics for all source pairs."""
    st.markdown("### 📊 Przegląd wszystkich metryk")
    
    labels = data_loader.get_category_labels()
    source_pairs = st.session_state.get('source_pairs', [])
    
    if not source_pairs:
        st.info("Wybierz co najmniej 2 źródła do porównania")
        return
    
    # Source name mapping
    source_names = {
        'sent_emo': 'SENT_EMO',
        'sent_emo_llm': 'SENT_EMO_LLM',
        'manual': 'Manual'
    }
    
    for cat_type in categories:
        cat_name = 'sentymentu' if cat_type == 'sentiment' else 'emocji'
        st.markdown(f"#### Analiza {cat_name}")
        
        if cat_type == 'sentiment':
            cols_dict = data_loader.get_sentiment_columns()
            cat_labels = labels['sentiments']
        else:
            cols_dict = data_loader.get_emotion_columns()
            cat_labels = labels['emotions']
        
        # Iterate through all pairs
        for source1, source2 in source_pairs:
            source1_name = source_names.get(source1, source1.upper())
            source2_name = source_names.get(source2, source2.upper())
            st.markdown(f"##### Porównanie: {source1_name} vs {source2_name}")
            
            # Compute metrics for each category
            metrics_by_category = {}
            
            for i, (cat_key, cat_label) in enumerate(cat_labels.items()):
                col1 = cols_dict[source1][i]
                col2 = cols_dict[source2][i]
                
                if col1 in df.columns and col2 in df.columns:
                    # Data is already in 0-2 ordinal scale (using _ordinal columns for automatic coding)
                    data1_norm = df[col1]
                    data2_norm = df[col2]
                    
                    # Remove NaN values
                    valid_mask = ~(data1_norm.isna() | data2_norm.isna())
                    if valid_mask.sum() == 0:
                        continue
                    
                    # Compute metrics
                    metrics = agreement_metrics.compute_all_metrics(
                        data1_norm[valid_mask].values,
                        data2_norm[valid_mask].values,
                        data_type='ordinal'
                    )
                    metrics_by_category[cat_label] = metrics
            
            # Show summary table
            if metrics_by_category:
                summary_data = []
                for cat_label, metrics in metrics_by_category.items():
                    row = {'Kategoria': cat_label}
                    
                    if metrics['percent_agreement']:
                        row['Zgodność %'] = f"{metrics['percent_agreement']['value']:.1f}%"
                    
                    if metrics['cohen_kappa']:
                        row["Cohen's κ"] = f"{metrics['cohen_kappa']['value']:.3f}"
                    
                    if metrics['weighted_kappa']:
                        row['Ważona κ'] = f"{metrics['weighted_kappa']['value']:.3f}"
                    
                    if metrics['krippendorff_alpha']:
                        row["Krippendorff's α"] = f"{metrics['krippendorff_alpha']['value']:.3f}"
                    
                    if metrics['icc']:
                        row['ICC'] = f"{metrics['icc']['value']:.3f}"
                    
                    if metrics['spearman_rho']:
                        row["Spearman's ρ"] = f"{metrics['spearman_rho']['value']:.3f}"
                    
                    summary_data.append(row)
                
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
                
                # Visualization
                col1, col2 = st.columns(2)
                
                # Unique key for this pair
                pair_key = f"{cat_type}_{source1}_{source2}"
                
                with col1:
                    # Bar chart for Cohen's Kappa
                    kappa_values = {cat: metrics['cohen_kappa']['value'] 
                                   for cat, metrics in metrics_by_category.items() 
                                   if metrics['cohen_kappa']}
                    if kappa_values:
                        fig = visualizations.plot_metrics_comparison(
                            {cat: {'cohen_kappa': {'value': val}} for cat, val in kappa_values.items()},
                            metric_name='cohen_kappa'
                        )
                        st.plotly_chart(fig, use_container_width=True, key=f"kappa_bar_{pair_key}")
                
                with col2:
                    # Radar chart
                    if len(metrics_by_category) > 0:
                        first_cat = list(metrics_by_category.keys())[0]
                        first_metrics = metrics_by_category[first_cat]
                        
                        radar_data = {}
                        if first_metrics['percent_agreement']:
                            radar_data['percent_agreement'] = first_metrics['percent_agreement']['value']
                        if first_metrics['cohen_kappa']:
                            radar_data['cohen_kappa'] = first_metrics['cohen_kappa']['value']
                        if first_metrics['weighted_kappa']:
                            radar_data['weighted_kappa'] = first_metrics['weighted_kappa']['value']
                        if first_metrics['krippendorff_alpha']:
                            radar_data['krippendorff_alpha'] = first_metrics['krippendorff_alpha']['value']
                        if first_metrics['icc']:
                            radar_data['icc'] = first_metrics['icc']['value']
                        if first_metrics['spearman_rho']:
                            radar_data['spearman_rho'] = first_metrics['spearman_rho']['value']
                        
                        fig = visualizations.plot_metrics_radar(
                            radar_data,
                            title=f"Profil metryk: {first_cat}"
                        )
                        st.plotly_chart(fig, use_container_width=True, key=f"radar_{pair_key}")
            
            st.markdown("---")


def show_detailed_analysis(df, categories, sources):
    """Show detailed analysis for selected category and source pair."""
    st.markdown("### 🎯 Szczegółowa analiza wybranej kategorii")
    
    labels = data_loader.get_category_labels()
    source_pairs = st.session_state.get('source_pairs', [])
    
    if not source_pairs:
        st.info("Wybierz co najmniej 2 źródła do porównania")
        return
    
    # Source name mapping
    source_names = {
        'sent_emo': 'SENT_EMO',
        'sent_emo_llm': 'SENT_EMO_LLM',
        'manual': 'Manual'
    }
    
    # Pair selection
    pair_options = [f"{source_names[s1]} vs {source_names[s2]}" for s1, s2 in source_pairs]
    selected_pair_str = st.selectbox(
        "Wybierz parę źródeł do porównania",
        options=pair_options,
        key='detailed_pair'
    )
    selected_pair_idx = pair_options.index(selected_pair_str)
    source1, source2 = source_pairs[selected_pair_idx]
    
    # Category selection
    cat_type = st.selectbox(
        "Wybierz typ",
        options=['Sentyment', 'Emocje'],
        key='detailed_cat_type'
    )
    
    if cat_type == 'Sentyment':
        cols_dict = data_loader.get_sentiment_columns()
        cat_labels = labels['sentiments']
    else:
        cols_dict = data_loader.get_emotion_columns()
        cat_labels = labels['emotions']
    
    selected_category = st.selectbox(
        "Wybierz kategorię",
        options=list(cat_labels.values()),
        key='detailed_category'
    )
    
    # Find index
    cat_index = list(cat_labels.values()).index(selected_category)
    cat_key = list(cat_labels.keys())[cat_index]
    
    col1 = cols_dict[source1][cat_index]
    col2 = cols_dict[source2][cat_index]
    
    if col1 in df.columns and col2 in df.columns:
        # Data is already in 0-2 ordinal scale
        data1_norm = df[col1]
        data2_norm = df[col2]
        
        # Remove NaN values
        valid_mask = ~(data1_norm.isna() | data2_norm.isna())
        data1_clean = data1_norm[valid_mask]
        data2_clean = data2_norm[valid_mask]
        
        if len(data1_clean) == 0:
            st.warning("⚠️ Brak prawidłowych danych do porównania")
            return
        
        # Compute all metrics
        metrics = agreement_metrics.compute_all_metrics(
            data1_clean.values,
            data2_clean.values,
            data_type='ordinal'
        )
        
        source1_name = source_names[source1]
        source2_name = source_names[source2]
        
        # Display metrics table
        col_a, col_b = st.columns([1, 1])
        
        with col_a:
            st.markdown(f"**Metryki zgodności: {source1_name} vs {source2_name}**")
            fig = visualizations.create_summary_table(metrics)
            st.plotly_chart(fig, use_container_width=True, key=f"detail_table_{source1}_{source2}_{selected_category}")
        
        with col_b:
            # Distribution comparison
            st.markdown(f"**Rozkład wartości**")
            fig = visualizations.plot_distribution_comparison(
                df[valid_mask],
                col1,
                [col2],
                selected_category,
                [source2_name]
            )
            st.plotly_chart(fig, use_container_width=True, key=f"detail_dist_{source1}_{source2}_{selected_category}")
        
        # Confusion matrix
        st.markdown("#### Macierz konfuzji")
        cm, cm_labels = agreement_metrics.compute_confusion_matrix(
            data1_clean.values,
            data2_clean.values,
            labels=[0, 1, 2]
        )
        
        if len(cm) > 0:
            label_names = ['Brak', 'Obecna', 'Silna']
            fig = visualizations.plot_confusion_matrix(
                cm,
                label_names,
                title=f"Macierz konfuzji: {selected_category} ({source1_name} vs {source2_name})"
            )
            st.plotly_chart(fig, use_container_width=True, key=f"detail_cm_{source1}_{source2}_{selected_category}")


def show_scatter_plots(df, categories, sources):
    """Show scatter plots comparing source pairs."""
    st.markdown("### 📉 Wykresy rozproszenia")
    
    labels = data_loader.get_category_labels()
    source_pairs = st.session_state.get('source_pairs', [])
    
    if not source_pairs:
        st.info("Wybierz co najmniej 2 źródła do porównania")
        return
    
    # Source name mapping
    source_names = {
        'sent_emo': 'SENT_EMO',
        'sent_emo_llm': 'SENT_EMO_LLM',
        'manual': 'Manual'
    }
    
    for cat_type in categories:
        cat_name = 'Sentyment' if cat_type == 'sentiment' else 'Emocje'
        
        if cat_type == 'sentiment':
            cols_dict = data_loader.get_sentiment_columns()
            cat_labels = labels['sentiments']
        else:
            cols_dict = data_loader.get_emotion_columns()
            cat_labels = labels['emotions']
        
        st.markdown(f"#### {cat_name}")
        
        # For each source pair
        for source1, source2 in source_pairs:
            source1_name = source_names[source1]
            source2_name = source_names[source2]
            st.markdown(f"##### {source1_name} vs {source2_name}")
            
            # Create grid of scatter plots
            n_cats = len(cat_labels)
            cols_per_row = 2
            n_rows = (n_cats + cols_per_row - 1) // cols_per_row
            
            idx = 0
            for i in range(n_rows):
                cols = st.columns(cols_per_row)
                
                for j in range(cols_per_row):
                    if idx >= n_cats:
                        break
                    
                    cat_key = list(cat_labels.keys())[idx]
                    cat_label = cat_labels[cat_key]
                    
                    col1 = cols_dict[source1][idx]
                    col2 = cols_dict[source2][idx]
                    
                    if col1 in df.columns and col2 in df.columns:
                        with cols[j]:
                            # Data is already in 0-2 ordinal scale
                            plot_df = df[[col1, col2]].copy()
                            
                            # Remove NaN
                            plot_df = plot_df.dropna()
                            
                            if len(plot_df) > 0:
                                fig = visualizations.plot_scatter_comparison(
                                    plot_df,
                                    col1,
                                    col2,
                                    cat_label,
                                    source1_name,
                                    source2_name
                                )
                                st.plotly_chart(fig, use_container_width=True, key=f"scatter_{cat_type}_{source1}_{source2}_{idx}")
                    
                    idx += 1
            
            st.markdown("---")


def show_element_preview(df, categories, sources):
    """
    Show preview of individual elements with coding comparison across all sources.
    Displays 6 elements in 2 columns with text and coding table.
    """
    st.markdown("### 🔍 Podgląd elementów")
    
    labels = data_loader.get_category_labels()
    
    # Source name mapping
    source_names = {
        'sent_emo': 'SENT_EMO',
        'sent_emo_llm': 'SENT_EMO_LLM',
        'manual': 'Manual'
    }
    
    # Get column mappings
    sent_cols = data_loader.get_sentiment_columns()
    emo_cols = data_loader.get_emotion_columns()
    
    # === COMPUTE AGREEMENT SCORES FOR EACH ROW ===
    def compute_row_agreement(row_data):
        """Compute agreement statistics for a single row."""
        agreements = {'full': 0, 'partial': 0, 'none': 0, 'total': 0}
        
        # Check sentiments
        if 'sentiment' in categories:
            for i in range(len(labels['sentiments'])):
                values = []
                for source in sources:
                    col = sent_cols[source][i]
                    if col in df.columns:
                        val = row_data[col]
                        if pd.notna(val):
                            values.append(int(val))
                
                if len(values) >= 2:
                    agreements['total'] += 1
                    if len(set(values)) == 1:
                        agreements['full'] += 1
                    elif max(values) - min(values) <= 1:
                        agreements['partial'] += 1
                    else:
                        agreements['none'] += 1
        
        # Check emotions
        if 'emotion' in categories:
            for i in range(len(labels['emotions'])):
                values = []
                for source in sources:
                    col = emo_cols[source][i]
                    if col in df.columns:
                        val = row_data[col]
                        if pd.notna(val):
                            values.append(int(val))
                
                if len(values) >= 2:
                    agreements['total'] += 1
                    if len(set(values)) == 1:
                        agreements['full'] += 1
                    elif max(values) - min(values) <= 1:
                        agreements['partial'] += 1
                    else:
                        agreements['none'] += 1
        
        return agreements
    
    # Compute agreement for all rows
    df_with_agreement = df.copy()
    agreement_data = df.apply(compute_row_agreement, axis=1)
    df_with_agreement['_agree_full'] = agreement_data.apply(lambda x: x['full'])
    df_with_agreement['_agree_partial'] = agreement_data.apply(lambda x: x['partial'])
    df_with_agreement['_agree_none'] = agreement_data.apply(lambda x: x['none'])
    df_with_agreement['_agree_total'] = agreement_data.apply(lambda x: x['total'])
    df_with_agreement['_agree_pct'] = df_with_agreement.apply(
        lambda r: (r['_agree_full'] / r['_agree_total'] * 100) if r['_agree_total'] > 0 else 0, axis=1
    )
    
    # === FILTERING AND SORTING OPTIONS ===
    st.markdown("#### 🔧 Filtrowanie i sortowanie")
    
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1.5, 1.5, 1, 1])
    
    with filter_col1:
        agreement_filter = st.selectbox(
            "Filtruj po zgodności",
            options=[
                "Wszystkie",
                "🟢 Tylko pełna zgodność (wszystkie)",
                "🟡 Częściowa zgodność (min. 1)",
                "🔴 Brak zgodności (min. 1)",
                "🔴🔴 Głównie niezgodne (>50%)",
                "🟢🟢 Głównie zgodne (>50%)"
            ],
            key="preview_agreement_filter"
        )
    
    with filter_col2:
        sort_option = st.selectbox(
            "Sortuj według",
            options=[
                "Kolejność w bazie",
                "% pełnej zgodności (rosnąco)",
                "% pełnej zgodności (malejąco)",
                "Liczba niezgodności (rosnąco)",
                "Liczba niezgodności (malejąco)",
                "Długość tekstu (rosnąco)",
                "Długość tekstu (malejąco)"
            ],
            key="preview_sort_option"
        )
    
    with filter_col3:
        # Text search
        text_search = st.text_input("🔎 Szukaj w tekście", key="preview_text_search", placeholder="Wpisz frazę...")
    
    with filter_col4:
        # Category filter for specific value
        category_value_filter = st.selectbox(
            "Filtruj po wartości",
            options=["Wszystkie", "Ma 'Brak'", "Ma 'Obecna'", "Ma 'Silna'"],
            key="preview_value_filter"
        )
    
    # === APPLY FILTERS ===
    filtered_df = df_with_agreement.copy()
    
    # Agreement filter
    if agreement_filter == "🟢 Tylko pełna zgodność (wszystkie)":
        filtered_df = filtered_df[filtered_df['_agree_none'] == 0]
        filtered_df = filtered_df[filtered_df['_agree_partial'] == 0]
    elif agreement_filter == "🟡 Częściowa zgodność (min. 1)":
        filtered_df = filtered_df[filtered_df['_agree_partial'] > 0]
    elif agreement_filter == "🔴 Brak zgodności (min. 1)":
        filtered_df = filtered_df[filtered_df['_agree_none'] > 0]
    elif agreement_filter == "🔴🔴 Głównie niezgodne (>50%)":
        filtered_df = filtered_df[filtered_df['_agree_none'] > filtered_df['_agree_total'] / 2]
    elif agreement_filter == "🟢🟢 Głównie zgodne (>50%)":
        filtered_df = filtered_df[filtered_df['_agree_full'] > filtered_df['_agree_total'] / 2]
    
    # Text search filter
    if text_search:
        text_col = 'text' if 'text' in filtered_df.columns else 'text_manual'
        if text_col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[text_col].astype(str).str.contains(text_search, case=False, na=False)]
    
    # Value filter
    if category_value_filter != "Wszystkie":
        # Map labels to numeric values
        label_to_value = {"Ma 'Brak'": 0, "Ma 'Obecna'": 1, "Ma 'Silna'": 2}
        target_val = label_to_value.get(category_value_filter, None)
        if target_val is not None:
            # Check if any source has this value
            value_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
            for source in sources:
                for col in sent_cols[source] + emo_cols[source]:
                    if col in filtered_df.columns:
                        value_mask |= (filtered_df[col] == target_val)
            filtered_df = filtered_df[value_mask]
    
    # === APPLY SORTING ===
    if sort_option == "% pełnej zgodności (rosnąco)":
        filtered_df = filtered_df.sort_values('_agree_pct', ascending=True)
    elif sort_option == "% pełnej zgodności (malejąco)":
        filtered_df = filtered_df.sort_values('_agree_pct', ascending=False)
    elif sort_option == "Liczba niezgodności (rosnąco)":
        filtered_df = filtered_df.sort_values('_agree_none', ascending=True)
    elif sort_option == "Liczba niezgodności (malejąco)":
        filtered_df = filtered_df.sort_values('_agree_none', ascending=False)
    elif sort_option == "Długość tekstu (rosnąco)":
        text_col = 'text' if 'text' in filtered_df.columns else 'text_manual'
        if text_col in filtered_df.columns:
            filtered_df = filtered_df.assign(_text_len=filtered_df[text_col].astype(str).str.len())
            filtered_df = filtered_df.sort_values('_text_len', ascending=True)
    elif sort_option == "Długość tekstu (malejąco)":
        text_col = 'text' if 'text' in filtered_df.columns else 'text_manual'
        if text_col in filtered_df.columns:
            filtered_df = filtered_df.assign(_text_len=filtered_df[text_col].astype(str).str.len())
            filtered_df = filtered_df.sort_values('_text_len', ascending=False)
    
    # Reset index for proper indexing
    filtered_df = filtered_df.reset_index(drop=True)
    
    # === INFO BOX ===
    st.info(f"""
    **Wyświetlanie {len(filtered_df)} z {len(df)} elementów** | 
    Kolory: 🟢 pełna zgodność | 🟡 częściowa (±1) | 🔴 brak zgodności
    """)
    
    # === NAVIGATION ===
    total_elements = len(filtered_df)
    
    if total_elements == 0:
        st.warning("Brak elementów spełniających kryteria filtrowania.")
        return
    
    elements_per_page = 6
    max_page = max(1, (total_elements + elements_per_page - 1) // elements_per_page)
    
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    
    with col_nav1:
        page = st.number_input("Strona", min_value=1, max_value=max_page, value=1, key="element_preview_page")
    
    with col_nav2:
        start_el = (page-1)*elements_per_page + 1
        end_el = min(page*elements_per_page, total_elements)
        st.markdown(f"**Elementy {start_el} - {end_el} z {total_elements}**")
    
    with col_nav3:
        if st.button("🎲 Losowe", key="random_elements_btn"):
            import random
            max_random = min(elements_per_page, total_elements)
            st.session_state.random_indices = random.sample(range(total_elements), max_random)
            st.session_state.use_random = True
        else:
            st.session_state.use_random = False
    
    # Get indices for current page
    if st.session_state.get('use_random', False) and 'random_indices' in st.session_state:
        indices = st.session_state.random_indices
    else:
        start_idx = (page - 1) * elements_per_page
        indices = list(range(start_idx, min(start_idx + elements_per_page, total_elements)))
    
    st.markdown("---")
    
    # Value labels
    value_labels = {0: 'Brak', 1: 'Obecna', 2: 'Silna'}
    
    # Create 2 columns, 3 rows
    for row in range(3):
        cols = st.columns(2)
        
        for col_idx in range(2):
            element_idx = row * 2 + col_idx
            if element_idx >= len(indices):
                break
            
            idx = indices[element_idx]
            if idx >= len(filtered_df):
                continue
            
            row_data = filtered_df.iloc[idx]
            
            with cols[col_idx]:
                # Element card
                with st.container():
                    # Get text - try different column names
                    text = ""
                    if 'text' in filtered_df.columns:
                        text = str(row_data['text'])
                    elif 'text_manual' in filtered_df.columns:
                        text = str(row_data['text_manual'])
                    
                    # Get post_id
                    post_id = ""
                    if 'post_id' in filtered_df.columns:
                        post_id = str(row_data['post_id'])[:12] + "..."
                    
                    # Agreement summary for this element
                    agree_full = row_data.get('_agree_full', 0)
                    agree_total = row_data.get('_agree_total', 1)
                    agree_pct = int(row_data.get('_agree_pct', 0))
                    
                    # Display text in expander
                    with st.expander(f"📝 #{idx + 1} | {post_id} | Zgodność: {agree_pct}%", expanded=True):
                        # Text preview (truncated) - dark mode friendly
                        text_display = text[:300] + "..." if len(text) > 300 else text
                        st.markdown(f"""
                        <div style='
                            background-color: rgba(255, 255, 255, 0.05); 
                            border: 1px solid rgba(255, 255, 255, 0.1);
                            padding: 12px; 
                            border-radius: 8px; 
                            margin-bottom: 12px; 
                            font-size: 0.9em;
                            color: inherit;
                        '>{text_display}</div>
                        """, unsafe_allow_html=True)
                        
                        # Build comparison table
                        table_data = []
                        
                        # Value to label mapping
                        value_to_label = {0: 'Brak', 1: 'Obecna', 2: 'Silna'}
                        
                        # Sentiments
                        if 'sentiment' in categories:
                            for i, (cat_key, cat_label) in enumerate(labels['sentiments'].items()):
                                row_values = {'Kategoria': f"🎭 {cat_label}"}
                                values_list = []
                                
                                for source in sources:
                                    col_name = sent_cols[source][i]
                                    if col_name in filtered_df.columns:
                                        val = row_data[col_name]
                                        if pd.notna(val):
                                            val = int(val)
                                            row_values[source_names[source]] = value_to_label.get(val, str(val))
                                            values_list.append(val)
                                        else:
                                            row_values[source_names[source]] = "—"
                                    else:
                                        row_values[source_names[source]] = "—"
                                
                                # Calculate agreement
                                numeric_vals = [v for v in values_list if isinstance(v, (int, float))]
                                if len(numeric_vals) >= 2:
                                    if len(set(numeric_vals)) == 1:
                                        row_values['Zgodność'] = '🟢'
                                    elif max(numeric_vals) - min(numeric_vals) <= 1:
                                        row_values['Zgodność'] = '🟡'
                                    else:
                                        row_values['Zgodność'] = '🔴'
                                else:
                                    row_values['Zgodność'] = '—'
                                
                                table_data.append(row_values)
                        
                        # Emotions
                        if 'emotion' in categories:
                            for i, (cat_key, cat_label) in enumerate(labels['emotions'].items()):
                                row_values = {'Kategoria': f"💭 {cat_label}"}
                                values_list = []
                                
                                for source in sources:
                                    col_name = emo_cols[source][i]
                                    if col_name in filtered_df.columns:
                                        val = row_data[col_name]
                                        if pd.notna(val):
                                            val = int(val)
                                            row_values[source_names[source]] = value_to_label.get(val, str(val))
                                            values_list.append(val)
                                        else:
                                            row_values[source_names[source]] = "—"
                                    else:
                                        row_values[source_names[source]] = "—"
                                
                                # Calculate agreement
                                numeric_vals = [v for v in values_list if isinstance(v, (int, float))]
                                if len(numeric_vals) >= 2:
                                    if len(set(numeric_vals)) == 1:
                                        row_values['Zgodność'] = '🟢'
                                    elif max(numeric_vals) - min(numeric_vals) <= 1:
                                        row_values['Zgodność'] = '🟡'
                                    else:
                                        row_values['Zgodność'] = '🔴'
                                else:
                                    row_values['Zgodność'] = '—'
                                
                                table_data.append(row_values)
                        
                        # Display table with colors
                        if table_data:
                            table_df = pd.DataFrame(table_data)
                            
                            # Style function for coloring cells - dark mode friendly with visible text
                            def color_values(val):
                                if val == 'Brak':
                                    return 'background-color: #1b5e20; color: white'  # Dark green
                                elif val == 'Obecna':
                                    return 'background-color: #e65100; color: white'  # Dark orange
                                elif val == 'Silna':
                                    return 'background-color: #b71c1c; color: white'  # Dark red
                                return ''
                            
                            def color_agreement(val):
                                if val == '🟢':
                                    return 'background-color: #2e7d32; color: white'  # Green
                                elif val == '🟡':
                                    return 'background-color: #f9a825; color: black'  # Yellow
                                elif val == '🔴':
                                    return 'background-color: #c62828; color: white'  # Red
                                return ''
                            
                            # Apply styling using map (newer pandas) or applymap (older)
                            source_cols = [source_names[s] for s in sources if source_names[s] in table_df.columns]
                            
                            styled_df = table_df.style
                            # Use map if available (pandas >= 2.1), else applymap
                            style_method = getattr(styled_df, 'map', None) or styled_df.applymap
                            for col in source_cols:
                                styled_df = style_method(color_values, subset=[col])
                            if 'Zgodność' in table_df.columns:
                                styled_df = style_method(color_agreement, subset=['Zgodność'])
                            
                            st.dataframe(styled_df, use_container_width=True, hide_index=True)
                        
                st.markdown("")  # Spacing


def show_confusion_matrices(df, categories, sources):
    """Show confusion matrices for all category and source pairs."""
    st.markdown("### 📋 Macierze konfuzji")
    
    st.info("Macierze konfuzji pokazują, jak często dwa źródła kodowania zgadzają się dla każdego poziomu natężenia.")
    
    labels = data_loader.get_category_labels()
    label_names = ['Brak', 'Obecna', 'Silna']
    source_pairs = st.session_state.get('source_pairs', [])
    
    if not source_pairs:
        st.info("Wybierz co najmniej 2 źródła do porównania")
        return
    
    # Source name mapping
    source_names = {
        'sent_emo': 'SENT_EMO',
        'sent_emo_llm': 'SENT_EMO_LLM',
        'manual': 'Manual'
    }
    
    for cat_type in categories:
        cat_name = 'Sentyment' if cat_type == 'sentiment' else 'Emocje'
        
        if cat_type == 'sentiment':
            cols_dict = data_loader.get_sentiment_columns()
            cat_labels = labels['sentiments']
        else:
            cols_dict = data_loader.get_emotion_columns()
            cat_labels = labels['emotions']
        
        st.markdown(f"#### {cat_name}")
        
        for source1, source2 in source_pairs:
            source1_name = source_names[source1]
            source2_name = source_names[source2]
            st.markdown(f"##### {source1_name} vs {source2_name}")
            
            # Create grid
            n_cats = len(cat_labels)
            cols_per_row = 2
            n_rows = (n_cats + cols_per_row - 1) // cols_per_row
            
            for i in range(n_rows):
                cols = st.columns(cols_per_row)
                
                for j in range(cols_per_row):
                    idx = i * cols_per_row + j
                    if idx >= n_cats:
                        break
                    
                    cat_key = list(cat_labels.keys())[idx]
                    cat_label = cat_labels[cat_key]
                    
                    col1 = cols_dict[source1][idx]
                    col2 = cols_dict[source2][idx]
                    
                    if col1 in df.columns and col2 in df.columns:
                        # Data is already in 0-2 ordinal scale
                        data1_norm = df[col1]
                        data2_norm = df[col2]
                        
                        # Remove NaN
                        valid_mask = ~(data1_norm.isna() | data2_norm.isna())
                        
                        if valid_mask.sum() > 0:
                            # Compute confusion matrix
                            cm, _ = agreement_metrics.compute_confusion_matrix(
                                data1_norm[valid_mask].values,
                                data2_norm[valid_mask].values,
                                labels=[0, 1, 2]
                            )
                            
                            if len(cm) > 0:
                                with cols[j]:
                                    fig = visualizations.plot_confusion_matrix(
                                        cm,
                                        label_names,
                                        title=cat_label,
                                        colorscale='Blues'
                                    )
                                    st.plotly_chart(fig, use_container_width=True, key=f"cm_{cat_type}_{source1}_{source2}_{idx}")
            
            st.markdown("---")


def main():
    """Main application logic."""
    initialize_session_state()
    sidebar_panel()
    main_panel()


if __name__ == "__main__":
    main()
