"""
Moduł wizualizacji dla analizy zgodności kodowania.
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import seaborn as sns
import matplotlib.pyplot as plt


def plot_confusion_matrix(
    cm: np.ndarray,
    labels: List[str],
    title: str = "Macierz konfuzji",
    colorscale: str = "Blues"
) -> go.Figure:
    """
    Tworzy interaktywną macierz konfuzji z użyciem Plotly.
    
    Args:
        cm: Macierz konfuzji
        labels: Etykiety kategorii
        title: Tytuł wykresu
        colorscale: Skala kolorów Plotly
        
    Returns:
        go.Figure: Figura Plotly
    """
    # Normalize to percentages
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
    
    # Create text annotations
    text = []
    for i in range(len(cm)):
        row_text = []
        for j in range(len(cm[0])):
            count = cm[i, j]
            pct = cm_normalized[i, j] if not np.isnan(cm_normalized[i, j]) else 0
            row_text.append(f"{count}<br>({pct:.1f}%)")
        text.append(row_text)
    
    fig = go.Figure(data=go.Heatmap(
        z=cm,
        x=labels,
        y=labels,
        text=text,
        texttemplate="%{text}",
        textfont={"size": 12},
        colorscale=colorscale,
        showscale=True,
        hovertemplate='Prawdziwa: %{y}<br>Przewidywana: %{x}<br>Liczba: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Kodowanie automatyczne",
        yaxis_title="Kodowanie manualne",
        width=600,
        height=550,
        font=dict(size=11)
    )
    
    return fig


def plot_agreement_heatmap(
    data: pd.DataFrame,
    manual_cols: List[str],
    auto_cols: List[str],
    metric_type: str = 'correlation',
    title: str = "Mapa zgodności"
) -> go.Figure:
    """
    Tworzy heatmapę pokazującą zgodność między kategoriami.
    
    Args:
        data: DataFrame z danymi
        manual_cols: Lista kolumn z kodowaniem manualnym
        auto_cols: Lista kolumn z kodowaniem automatycznym
        metric_type: 'correlation', 'kappa', lub 'icc'
        title: Tytuł wykresu
        
    Returns:
        go.Figure: Figura Plotly
    """
    from scipy.stats import spearmanr
    
    # Compute metric for each pair
    n_manual = len(manual_cols)
    n_auto = len(auto_cols)
    matrix = np.zeros((n_manual, n_auto))
    
    for i, mcol in enumerate(manual_cols):
        for j, acol in enumerate(auto_cols):
            mask = ~(data[mcol].isna() | data[acol].isna())
            if mask.sum() > 0:
                if metric_type == 'correlation':
                    rho, _ = spearmanr(data.loc[mask, mcol], data.loc[mask, acol])
                    matrix[i, j] = rho
                else:
                    # Placeholder for other metrics
                    matrix[i, j] = 0
    
    # Extract category names from column names
    manual_labels = [col.split('_')[-1] for col in manual_cols]
    auto_labels = [col.split('_')[-1] for col in auto_cols]
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=auto_labels,
        y=manual_labels,
        colorscale='RdYlGn',
        zmid=0,
        text=np.round(matrix, 2),
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="Korelacja<br>Spearmana")
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Kodowanie automatyczne",
        yaxis_title="Kodowanie manualne",
        width=700,
        height=500
    )
    
    return fig


def plot_scatter_comparison(
    data: pd.DataFrame,
    col1: str,
    col2: str,
    category_name: str,
    source1_name: str = "Źródło 1",
    source2_name: str = "Źródło 2"
) -> go.Figure:
    """
    Tworzy wykres rozproszenia porównujący dwa źródła kodowania.
    
    Args:
        data: DataFrame z danymi
        col1: Kolumna z pierwszym źródłem
        col2: Kolumna z drugim źródłem
        category_name: Nazwa kategorii (np. "Radość")
        source1_name: Nazwa pierwszego źródła
        source2_name: Nazwa drugiego źródła
        
    Returns:
        go.Figure: Figura Plotly
    """
    # Remove NaN values
    mask = ~(data[col1].isna() | data[col2].isna())
    plot_data = data[mask].copy()
    
    if len(plot_data) == 0:
        # Return empty figure
        fig = go.Figure()
        fig.add_annotation(
            text="Brak danych do wyświetlenia",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Check minimum data for correlation
    if len(plot_data) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Za mało danych (wymagane min. 2 punkty)",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Add jitter to better visualize overlapping points
    plot_data['col1_jitter'] = plot_data[col1] + np.random.normal(0, 0.05, len(plot_data))
    plot_data['col2_jitter'] = plot_data[col2] + np.random.normal(0, 0.02, len(plot_data))
    
    # Compute correlation (safely)
    from scipy.stats import spearmanr, pearsonr
    try:
        spearman_rho, spearman_p = spearmanr(plot_data[col1], plot_data[col2])
        pearson_r, pearson_p = pearsonr(plot_data[col1], plot_data[col2])
    except Exception:
        spearman_rho, pearson_r = 0.0, 0.0
    
    fig = go.Figure()
    
    # Scatter plot
    fig.add_trace(go.Scatter(
        x=plot_data['col1_jitter'],
        y=plot_data['col2_jitter'],
        mode='markers',
        marker=dict(
            size=8,
            color=plot_data[col2],
            colorscale='Viridis',
            showscale=False,
            opacity=0.6,
            line=dict(width=0.5, color='white')
        ),
        text=[f"{source1_name}: {m}<br>{source2_name}: {a}" for m, a in zip(plot_data[col1], plot_data[col2])],
        hovertemplate='%{text}<extra></extra>',
        name='Obserwacje'
    ))
    
    # Add diagonal line (perfect agreement)
    min_val = 0
    max_val = max(plot_data[col1].max(), plot_data[col2].max())
    fig.add_trace(go.Scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode='lines',
        line=dict(color='red', dash='dash', width=2),
        name='Idealna zgodność',
        showlegend=True
    ))
    
    # Add trend line
    z = np.polyfit(plot_data[col1], plot_data[col2], 1)
    p = np.poly1d(z)
    x_trend = np.linspace(min_val, max_val, 100)
    y_trend = p(x_trend)
    
    fig.add_trace(go.Scatter(
        x=x_trend,
        y=y_trend,
        mode='lines',
        line=dict(color='blue', width=2),
        name='Linia trendu',
        showlegend=True
    ))
    
    # Update layout
    fig.update_layout(
        title=f"{category_name}: {source1_name} vs {source2_name}<br>" +
              f"<sub>ρ Spearmana = {spearman_rho:.3f} (p = {spearman_p:.4f}), " +
              f"r Pearsona = {pearson_r:.3f} (p = {pearson_p:.4f})</sub>",
        xaxis_title=f"{source1_name} (0-2)",
        yaxis_title=f"{source2_name} (0-2)",
        width=600,
        height=500,
        hovermode='closest',
        showlegend=True
    )
    
    return fig


def plot_distribution_comparison(
    data: pd.DataFrame,
    manual_col: str,
    auto_cols: List[str],
    category_name: str,
    auto_names: List[str]
) -> go.Figure:
    """
    Tworzy wykres porównujący rozkłady wartości dla różnych źródeł.
    
    Args:
        data: DataFrame z danymi
        manual_col: Kolumna z kodowaniem manualnym
        auto_cols: Lista kolumn z kodowaniem automatycznym
        category_name: Nazwa kategorii
        auto_names: Nazwy źródeł automatycznych
        
    Returns:
        go.Figure: Figura Plotly
    """
    fig = go.Figure()
    
    # Manual coding distribution
    manual_counts = data[manual_col].value_counts().sort_index()
    fig.add_trace(go.Bar(
        x=manual_counts.index,
        y=manual_counts.values,
        name='Manualne',
        marker_color='lightblue',
        opacity=0.7
    ))
    
    # Auto coding distributions
    colors = ['salmon', 'lightgreen', 'lightyellow']
    for i, (auto_col, auto_name) in enumerate(zip(auto_cols, auto_names)):
        # Data is already in 0-2 ordinal scale (using _ordinal columns)
        auto_counts = data[auto_col].value_counts().sort_index()
        
        fig.add_trace(go.Bar(
            x=auto_counts.index,
            y=auto_counts.values,
            name=auto_name,
            marker_color=colors[i % len(colors)],
            opacity=0.7
        ))
    
    fig.update_layout(
        title=f"Rozkład wartości: {category_name}",
        xaxis_title="Wartość (0=Brak, 1=Obecna, 2=Obecność silna)",
        yaxis_title="Liczba obserwacji",
        barmode='group',
        width=700,
        height=400
    )
    
    return fig


def plot_metrics_comparison(
    metrics_dict: Dict[str, Dict],
    metric_name: str = 'cohen_kappa'
) -> go.Figure:
    """
    Tworzy wykres słupkowy porównujący wartości metryki dla różnych kategorii.
    
    Args:
        metrics_dict: Słownik {category_name: {metric_name: {value: ..., ...}}}
        metric_name: Nazwa metryki do wizualizacji
        
    Returns:
        go.Figure: Figura Plotly
    """
    categories = list(metrics_dict.keys())
    values = [metrics_dict[cat][metric_name]['value'] if metric_name in metrics_dict[cat] else 0 
              for cat in categories]
    
    # Color code by value
    colors = []
    for v in values:
        if v < 0.4:
            colors.append('rgb(239, 83, 80)')  # Red
        elif v < 0.6:
            colors.append('rgb(255, 167, 38)')  # Orange
        elif v < 0.8:
            colors.append('rgb(255, 235, 59)')  # Yellow
        else:
            colors.append('rgb(102, 187, 106)')  # Green
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f'{v:.3f}' for v in values],
            textposition='auto',
        )
    ])
    
    # Add threshold lines
    fig.add_hline(y=0.4, line_dash="dash", line_color="orange", 
                  annotation_text="Słaba", annotation_position="right")
    fig.add_hline(y=0.6, line_dash="dash", line_color="yellow", 
                  annotation_text="Umiarkowana", annotation_position="right")
    fig.add_hline(y=0.8, line_dash="dash", line_color="green", 
                  annotation_text="Znaczna", annotation_position="right")
    
    fig.update_layout(
        title=f"Porównanie: {metric_name.replace('_', ' ').title()}",
        xaxis_title="Kategoria",
        yaxis_title="Wartość metryki",
        yaxis_range=[0, 1],
        width=800,
        height=500
    )
    
    return fig


def plot_metrics_radar(
    metrics: Dict[str, float],
    title: str = "Profil metryk zgodności"
) -> go.Figure:
    """
    Tworzy wykres radarowy przedstawiający różne metryki zgodności.
    
    Args:
        metrics: Słownik {metric_name: value}
        title: Tytuł wykresu
        
    Returns:
        go.Figure: Figura Plotly
    """
    metric_labels = {
        'percent_agreement': 'Zgodność %',
        'cohen_kappa': "Cohen's κ",
        'weighted_kappa': 'Ważona κ',
        'krippendorff_alpha': "Krippendorff's α",
        'icc': 'ICC',
        'spearman_rho': "Spearman's ρ",
        'pearson_r': "Pearson's r"
    }
    
    categories = []
    values = []
    
    for key, label in metric_labels.items():
        if key in metrics and metrics[key] is not None:
            categories.append(label)
            # Normalize percent_agreement to 0-1 scale
            if key == 'percent_agreement':
                values.append(metrics[key] / 100)
            else:
                values.append(max(0, metrics[key]))  # Ensure non-negative
    
    # Close the radar chart
    categories.append(categories[0])
    values.append(values[0])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(102, 126, 234, 0.3)',
        line=dict(color='rgb(102, 126, 234)', width=2),
        marker=dict(size=8, color='rgb(102, 126, 234)')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                showline=True,
                linewidth=1,
                gridcolor="lightgray",
                tickformat='.2f'
            ),
            angularaxis=dict(
                linewidth=1,
                showline=True,
                linecolor="gray"
            )
        ),
        title=title,
        width=600,
        height=550,
        showlegend=False
    )
    
    return fig


def create_summary_table(metrics: Dict) -> go.Figure:
    """
    Tworzy tabelę podsumowującą wszystkie metryki.
    
    Args:
        metrics: Słownik z metrykami z funkcji compute_all_metrics
        
    Returns:
        go.Figure: Figura Plotly z tabelą
    """
    rows = []
    
    metric_info = {
        'percent_agreement': ('Zgodność procentowa', '%'),
        'cohen_kappa': ("Cohen's Kappa", ''),
        'weighted_kappa': ('Ważona Kappa', ''),
        'krippendorff_alpha': ("Krippendorff's Alpha", ''),
        'icc': ('ICC(2,1)', ''),
        'pearson_r': ("Korelacja Pearsona", ''),
        'spearman_rho': ("Korelacja Spearmana", '')
    }
    
    for key, (name, unit) in metric_info.items():
        if key in metrics and metrics[key] is not None:
            value = metrics[key]['value']
            interp = metrics[key].get('interpretation', '')
            
            if not np.isnan(value):
                if key == 'percent_agreement':
                    value_str = f"{value:.2f}{unit}"
                elif key == 'icc':
                    ci_lower = metrics[key].get('ci_lower', np.nan)
                    ci_upper = metrics[key].get('ci_upper', np.nan)
                    value_str = f"{value:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]"
                else:
                    value_str = f"{value:.3f}"
                
                rows.append([name, value_str, interp])
    
    if not rows:
        rows = [['Brak danych', '-', '-']]
    
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['<b>Metryka</b>', '<b>Wartość</b>', '<b>Interpretacja</b>'],
            fill_color='rgb(102, 126, 234)',
            font=dict(color='white', size=12),
            align='left'
        ),
        cells=dict(
            values=list(zip(*rows)),
            fill_color='lavender',
            font=dict(size=11),
            align='left',
            height=30
        )
    )])
    
    fig.update_layout(
        title="Podsumowanie metryk zgodności",
        width=700,
        height=min(400, 100 + len(rows) * 35)
    )
    
    return fig
