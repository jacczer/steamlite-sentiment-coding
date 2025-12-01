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


def sidebar_panel():
    """Create sidebar with data loading and filtering options."""
    st.sidebar.markdown("## ⚙️ Ustawienia")
    
    # Section 1: Analysis Options (at the top)
    if st.session_state.get('data_loaded', False):
        st.sidebar.markdown("### 📊 Opcje analizy")
        
        analysis_type = st.sidebar.radio(
            "Typ analizy",
            options=["Sentyment", "Emocje", "Wszystko"],
            help="Wybierz kategorie do analizy"
        )
        st.session_state.analysis_type = analysis_type
        
        # Available sources
        available_sources = []
        if st.session_state.get('has_sent_emo', False):
            available_sources.append("SENT_EMO")
        if st.session_state.get('has_sent_emo_llm', False):
            available_sources.append("SENT_EMO_LLM")
        if st.session_state.get('has_manual', False):
            available_sources.append("Manual")
        
        st.sidebar.markdown("**Porównywane źródła**")
        st.sidebar.markdown("<div style='font-size: 0.85rem; color: #888; margin-bottom: 8px;'>Wybierz źródła do analizy porównawczej (min. 2)</div>", unsafe_allow_html=True)
        
        # Checkboxes for source selection
        selected_sources = []
        for source in available_sources:
            default_val = True  # All selected by default
            if st.sidebar.checkbox(source, value=default_val, key=f"source_select_{source}"):
                selected_sources.append(source)
        
        st.session_state.selected_sources = selected_sources if len(selected_sources) >= 2 else available_sources
        
        if len(selected_sources) < 2:
            st.sidebar.warning("⚠️ Wybierz min. 2 źródła do porównania")
        
        # Metric selection
        st.sidebar.markdown("**Metryki do obliczenia**")
        show_kappa = st.sidebar.checkbox("Cohen's Kappa", value=True)
        show_alpha = st.sidebar.checkbox("Krippendorff's Alpha", value=True)
        show_icc = st.sidebar.checkbox("ICC", value=True)
        show_correlation = st.sidebar.checkbox("Korelacje", value=True)
        
        st.session_state.metrics_config = {
            'kappa': show_kappa,
            'alpha': show_alpha,
            'icc': show_icc,
            'correlation': show_correlation
        }
        
        st.sidebar.markdown("---")
    
    # Section 2: Filters (only if data loaded)
    if st.session_state.get('data_loaded', False):
        st.sidebar.markdown("### 🔍 Filtry danych")
        
        merged_df = st.session_state.merged_data
        
        # Source filter
        if 'source' in merged_df.columns:
            sources = ['Wszystkie'] + sorted(merged_df['source'].unique().tolist())
            selected_sources = st.sidebar.multiselect(
                "Źródła postów",
                options=sources,
                default=['Wszystkie'],
                help="Wybierz źródła postów do analizy"
            )
            
            if 'Wszystkie' not in selected_sources and len(selected_sources) > 0:
                merged_df = merged_df[merged_df['source'].isin(selected_sources)]
        
        # Date range filter
        if 'timestamp' in merged_df.columns:
            st.sidebar.markdown("**Zakres dat kodowania manualnego**")
            date_range = st.sidebar.date_input(
                "Wybierz zakres",
                value=(merged_df['timestamp'].min(), merged_df['timestamp'].max()),
                help="Filtruj według daty kodowania manualnego",
                label_visibility="collapsed"
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                merged_df = merged_df[
                    (merged_df['timestamp'].dt.date >= start_date) &
                    (merged_df['timestamp'].dt.date <= end_date)
                ]
        
        # Coder filter
        if 'coder_id' in merged_df.columns:
            coders = ['Wszyscy'] + sorted(merged_df['coder_id'].unique().tolist())
            selected_coder = st.sidebar.selectbox(
                "Koder",
                options=coders,
                help="Wybierz kodera do analizy"
            )
            
            if selected_coder != 'Wszyscy':
                merged_df = merged_df[merged_df['coder_id'] == selected_coder]
        
        # Update filtered data
        st.session_state.filtered_data = merged_df
        
        # Show filter summary
        st.sidebar.markdown(f"**Przefiltrowane:** {len(merged_df)} rekordów")
        
        st.sidebar.markdown("---")
    
    # Section 3: Data Loading (at the bottom, collapsed by default)
    with st.sidebar.expander("📁 Dane wejściowe i połączenie", expanded=False):
        # Parquet file selection
        default_path = r"C:\aktywne\dysk-M\sdns\dr-fn\Analiza_Treści_Fake_News\fn_data_analysis\data\interim\posts.parquet"
        parquet_path = st.text_input(
            "Ścieżka do pliku Parquet",
            value=default_path,
            help="Plik z danymi automatycznymi (SENT_EMO i SENT_EMO_LLM)",
            key="parquet_path_input"
        )
        
        # Load data button
        if st.button("🔄 Wczytaj dane", type="primary", use_container_width=True, key="load_data_btn"):
            load_data(parquet_path)
        
        st.markdown("---")
        
        # Connection status
        st.markdown("**Status połączenia:**")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.session_state.get('parquet_data') is not None:
                st.markdown("📊 **Parquet:** <span class='status-success'>✓</span>", unsafe_allow_html=True)
            else:
                st.markdown("📊 **Parquet:** <span class='status-error'>✗</span>", unsafe_allow_html=True)
        
        col3, col4 = st.columns([3, 1])
        
        with col3:
            if st.session_state.get('gsheets_connected', False):
                st.markdown("📝 **Google Sheets:** <span class='status-success'>✓</span>", unsafe_allow_html=True)
            else:
                st.markdown("📝 **Google Sheets:** <span class='status-error'>✗</span>", unsafe_allow_html=True)
        
        with col4:
            # Button to open Google Sheets
            if st.session_state.get('gsheets_connected', False):
                spreadsheet_id = st.secrets.get("SPREADSHEET_ID", "")
                if spreadsheet_id:
                    sheets_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
                    st.markdown(f"[🔗]({sheets_url})", help="Otwórz arkusz w Google Sheets")
    
    # Auto-load data on first run
    if not st.session_state.get('data_loaded', False) and not st.session_state.get('auto_load_attempted', False):
        st.session_state.auto_load_attempted = True
        default_path = r"C:\aktywne\dysk-M\sdns\dr-fn\Analiza_Treści_Fake_News\fn_data_analysis\data\interim\posts.parquet"
        load_data(default_path)


def load_data(parquet_path):
    """Load data from Parquet and Google Sheets."""
    with st.spinner("Wczytywanie danych..."):
        # Load Parquet
        parquet_df, parquet_error = data_loader.load_parquet_data(parquet_path)
        if parquet_error:
            st.sidebar.error(f"❌ {parquet_error}")
            return
        
        st.session_state.parquet_data = parquet_df
        
        # Check which data sources are available in Parquet
        sent_emo_cols = data_loader.get_sentiment_columns()['sent_emo']
        sent_emo_llm_cols = data_loader.get_sentiment_columns()['sent_emo_llm']
        
        st.session_state.has_sent_emo = all(col in parquet_df.columns for col in sent_emo_cols[:1])
        st.session_state.has_sent_emo_llm = all(col in parquet_df.columns for col in sent_emo_llm_cols[:1])
        
        st.sidebar.success(f"✅ Wczytano {len(parquet_df)} wierszy z Parquet")
        
        # Load Google Sheets
        manual_df, manual_error = data_loader.load_manual_coding_data()
        if manual_error:
            st.sidebar.warning(f"⚠️ Google Sheets: {manual_error}")
            st.session_state.gsheets_connected = False
            st.session_state.has_manual = False
            st.session_state.manual_data = None
            
            # If no manual data, still mark as loaded (for automatic coding only)
            st.session_state.data_loaded = True
            st.session_state.merged_data = parquet_df
            st.session_state.filtered_data = parquet_df
        elif manual_df is None or len(manual_df) == 0:
            st.sidebar.warning("⚠️ Google Sheets: Brak danych (arkusz pusty)")
            st.session_state.gsheets_connected = True
            st.session_state.has_manual = False
            st.session_state.manual_data = None
            
            # If no manual data, still mark as loaded
            st.session_state.data_loaded = True
            st.session_state.merged_data = parquet_df
            st.session_state.filtered_data = parquet_df
        else:
            st.session_state.manual_data = manual_df
            st.session_state.gsheets_connected = True
            st.session_state.has_manual = True
            st.sidebar.success(f"✅ Wczytano {len(manual_df)} wierszy z Google Sheets")
            
            # Merge datasets
            merged_df, merge_error = data_loader.merge_datasets(
                parquet_df, manual_df, on_column='post_id'
            )
            if merge_error:
                st.sidebar.error(f"❌ Łączenie: {merge_error}")
                # Fall back to Parquet only
                st.session_state.data_loaded = True
                st.session_state.merged_data = parquet_df
                st.session_state.filtered_data = parquet_df
            else:
                st.session_state.merged_data = merged_df
                st.session_state.data_loaded = True
                st.session_state.filtered_data = merged_df
                st.sidebar.success(f"✅ Połączono: {len(merged_df)} wspólnych rekordów")


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
        
        return
    
    # Data loaded - show analysis
    merged_df = st.session_state.get('filtered_data', st.session_state.merged_data)
    
    # Data summary
    st.markdown("## 📈 Podsumowanie danych")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Liczba rekordów", len(merged_df))
    
    with col2:
        if 'coder_id' in merged_df.columns:
            st.metric("Liczba koderów", merged_df['coder_id'].nunique())
    
    with col3:
        if 'source' in merged_df.columns:
            st.metric("Liczba źródeł", merged_df['source'].nunique())
    
    with col4:
        if 'timestamp' in merged_df.columns:
            date_range = (merged_df['timestamp'].max() - merged_df['timestamp'].min()).days
            st.metric("Zakres dni", date_range)
    
    st.markdown("---")
    
    # Get analysis configuration
    analysis_type = st.session_state.get('analysis_type', 'Wszystko')
    selected_sources = st.session_state.get('selected_sources', [])
    
    # Determine which categories to analyze
    if analysis_type == 'Sentyment':
        categories_to_analyze = ['sentiment']
    elif analysis_type == 'Emocje':
        categories_to_analyze = ['emotion']
    else:
        categories_to_analyze = ['sentiment', 'emotion']
    
    # Map UI names to internal names
    source_mapping = {
        'SENT_EMO': 'sent_emo',
        'SENT_EMO_LLM': 'sent_emo_llm',
        'Manual': 'manual'
    }
    
    # Convert selected sources to internal format
    sources_to_compare = [source_mapping.get(s, s.lower()) for s in selected_sources if s in source_mapping]
    
    # Generate all possible pairs for comparison
    from itertools import combinations
    source_pairs = list(combinations(sources_to_compare, 2))
    
    # If no sources available or less than 2, show warning
    if len(sources_to_compare) < 2:
        st.warning("⚠️ Wybierz co najmniej 2 źródła danych do porównania w panelu bocznym.")
        return
    
    st.session_state.source_pairs = source_pairs
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Przegląd metryk",
        "🎯 Szczegółowa analiza",
        "📉 Wykresy rozproszenia",
        "📋 Macierze konfuzji"
    ])
    
    with tab1:
        show_metrics_overview(merged_df, categories_to_analyze, sources_to_compare)
    
    with tab2:
        show_detailed_analysis(merged_df, categories_to_analyze, sources_to_compare)
    
    with tab3:
        show_scatter_plots(merged_df, categories_to_analyze, sources_to_compare)
    
    with tab4:
        show_confusion_matrices(merged_df, categories_to_analyze, sources_to_compare)


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
                    # Normalize data to common scale
                    data1_norm = data_loader.normalize_to_scale(
                        df[col1], source1, target_scale='0-3'
                    )
                    data2_norm = data_loader.normalize_to_scale(
                        df[col2], source2, target_scale='0-3'
                    )
                    
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
                        st.plotly_chart(fig, use_container_width=True)
                
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
                        st.plotly_chart(fig, use_container_width=True)
            
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
        # Normalize data
        data1_norm = data_loader.normalize_to_scale(
            df[col1], source1, target_scale='0-3'
        )
        data2_norm = data_loader.normalize_to_scale(
            df[col2], source2, target_scale='0-3'
        )
        
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
            st.plotly_chart(fig, use_container_width=True)
        
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
            st.plotly_chart(fig, use_container_width=True)
        
        # Confusion matrix
        st.markdown("#### Macierz konfuzji")
        cm, cm_labels = agreement_metrics.compute_confusion_matrix(
            data1_clean.values,
            data2_clean.values,
            labels=[0, 1, 2, 3]
        )
        
        if len(cm) > 0:
            label_names = ['Brak', 'Niskie', 'Średnie', 'Wysokie']
            fig = visualizations.plot_confusion_matrix(
                cm,
                label_names,
                title=f"Macierz konfuzji: {selected_category} ({source1_name} vs {source2_name})"
            )
            st.plotly_chart(fig, use_container_width=True)


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
                            # Normalize for display
                            plot_df = df[[col1, col2]].copy()
                            plot_df[col1] = data_loader.normalize_to_scale(
                                plot_df[col1], source1, target_scale='0-3'
                            )
                            plot_df[col2] = data_loader.normalize_to_scale(
                                plot_df[col2], source2, target_scale='0-3'
                            )
                            
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
                                st.plotly_chart(fig, use_container_width=True)
                    
                    idx += 1
            
            st.markdown("---")


def show_confusion_matrices(df, categories, sources):
    """Show confusion matrices for all category and source pairs."""
    st.markdown("### 📋 Macierze konfuzji")
    
    st.info("Macierze konfuzji pokazują, jak często dwa źródła kodowania zgadzają się dla każdego poziomu natężenia.")
    
    labels = data_loader.get_category_labels()
    label_names = ['Brak', 'Niskie', 'Średnie', 'Wysokie']
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
                        # Normalize data
                        data1_norm = data_loader.normalize_to_scale(
                            df[col1], source1, target_scale='0-3'
                        )
                        data2_norm = data_loader.normalize_to_scale(
                            df[col2], source2, target_scale='0-3'
                        )
                        
                        # Remove NaN
                        valid_mask = ~(data1_norm.isna() | data2_norm.isna())
                        
                        if valid_mask.sum() > 0:
                            # Compute confusion matrix
                            cm, _ = agreement_metrics.compute_confusion_matrix(
                                data1_norm[valid_mask].values,
                                data2_norm[valid_mask].values,
                                labels=[0, 1, 2, 3]
                            )
                            
                            if len(cm) > 0:
                                with cols[j]:
                                    fig = visualizations.plot_confusion_matrix(
                                        cm,
                                        label_names,
                                        title=cat_label,
                                        colorscale='Blues'
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")


def main():
    """Main application logic."""
    initialize_session_state()
    sidebar_panel()
    main_panel()


if __name__ == "__main__":
    main()
