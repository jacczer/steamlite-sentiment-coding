"""
Moduł obliczający wskaźniki zgodności między różnymi metodami kodowania.

Implementuje rzetelne metody statystyczne zgodnie ze standardami badań
nad zgodnością międzykoderkową (inter-rater reliability).
"""
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional
from scipy import stats
from sklearn.metrics import confusion_matrix, cohen_kappa_score
import warnings


def cohen_kappa(
    rater1: np.ndarray,
    rater2: np.ndarray,
    weights: Optional[str] = None
) -> Tuple[float, str]:
    """
    Oblicz Cohen's Kappa - wskaźnik zgodności dla dwóch koderów.
    
    Cohen's Kappa uwzględnia zgodność przypadkową i jest odpowiedni
    dla danych nominalnych i porządkowych.
    
    Args:
        rater1: Oceny pierwszego kodera
        rater2: Oceny drugiego kodera
        weights: None (nieważona), 'linear' lub 'quadratic' dla danych porządkowych
        
    Returns:
        Tuple[float, str]: (wartość kappa, interpretacja)
        
    Interpretacja (Landis & Koch, 1977):
        < 0.00: Poor (Zła)
        0.00 - 0.20: Slight (Niewielka)
        0.21 - 0.40: Fair (Słaba)
        0.41 - 0.60: Moderate (Umiarkowana)
        0.61 - 0.80: Substantial (Znaczna)
        0.81 - 1.00: Almost Perfect (Prawie doskonała)
    """
    try:
        # Remove NaN values
        mask = ~(np.isnan(rater1) | np.isnan(rater2))
        r1 = rater1[mask]
        r2 = rater2[mask]
        
        if len(r1) < 2:
            return np.nan, "Niewystarczające dane"
        
        kappa = cohen_kappa_score(r1, r2, weights=weights)
        
        # Interpretacja
        if kappa < 0:
            interp = "Zła (gorsza niż losowa)"
        elif kappa < 0.20:
            interp = "Niewielka"
        elif kappa < 0.40:
            interp = "Słaba"
        elif kappa < 0.60:
            interp = "Umiarkowana"
        elif kappa < 0.80:
            interp = "Znaczna"
        else:
            interp = "Prawie doskonała"
        
        return kappa, interp
        
    except Exception as e:
        return np.nan, f"Błąd: {str(e)}"


def krippendorff_alpha(
    data: np.ndarray,
    level_of_measurement: str = 'ordinal'
) -> Tuple[float, str]:
    """
    Oblicz Krippendorff's Alpha - najbardziej uniwersalny wskaźnik zgodności.
    
    Krippendorff's Alpha:
    - Działa dla dowolnej liczby koderów
    - Obsługuje brakujące dane
    - Dostosowuje się do różnych poziomów pomiaru
    
    Args:
        data: Macierz (units × raters), wartości to oceny
        level_of_measurement: 'nominal', 'ordinal', 'interval', lub 'ratio'
        
    Returns:
        Tuple[float, str]: (wartość alpha, interpretacja)
        
    Interpretacja (Krippendorff, 2004):
        < 0.667: Odrzucić wnioski
        0.667 - 0.800: Wnioski wstępne (tentative)
        > 0.800: Wnioski definitywne (definite)
    """
    try:
        # Implementation of Krippendorff's Alpha
        # Based on: Krippendorff, K. (2004). Content Analysis: An Introduction to Its Methodology
        
        n_units, n_raters = data.shape
        
        # Create coincidence matrix
        values = np.unique(data[~np.isnan(data)])
        n_values = len(values)
        
        if n_values < 2:
            return np.nan, "Niewystarczająca wariancja"
        
        # Pairable values per unit
        m_u = np.sum(~np.isnan(data), axis=1)
        
        # Coincidence matrix
        coincidence = np.zeros((n_values, n_values))
        
        for u in range(n_units):
            unit_values = data[u, ~np.isnan(data[u])]
            if len(unit_values) < 2:
                continue
            
            for i, v1 in enumerate(values):
                for j, v2 in enumerate(values):
                    n_v1 = np.sum(unit_values == v1)
                    n_v2 = np.sum(unit_values == v2)
                    
                    if i == j:
                        coincidence[i, j] += n_v1 * (n_v1 - 1)
                    else:
                        coincidence[i, j] += n_v1 * n_v2
        
        # Normalize
        n_c = coincidence.sum()
        if n_c == 0:
            return np.nan, "Brak danych do analizy"
        
        coincidence = coincidence / n_c
        
        # Expected disagreement (based on level of measurement)
        n_k = coincidence.sum(axis=1)
        
        if level_of_measurement == 'nominal':
            D_e = 1 - np.sum(n_k ** 2)
            D_o = np.sum(coincidence * (1 - np.eye(n_values)))
        elif level_of_measurement == 'ordinal':
            # Use metric for ordinal data
            metric = np.zeros((n_values, n_values))
            for i in range(n_values):
                for j in range(n_values):
                    g = np.arange(min(i, j), max(i, j) + 1)
                    metric[i, j] = (np.sum(n_k[g]) - (n_k[i] + n_k[j]) / 2) ** 2
            
            D_e = np.sum(n_k[:, None] * n_k[None, :] * metric) / 2
            D_o = np.sum(coincidence * metric)
        else:  # interval or ratio
            # Use squared differences
            metric = (values[:, None] - values[None, :]) ** 2
            D_e = np.sum(n_k[:, None] * n_k[None, :] * metric) / 2
            D_o = np.sum(coincidence * metric)
        
        if D_e == 0:
            return np.nan, "Brak oczekiwanej niezgodności"
        
        alpha = 1 - (D_o / D_e)
        
        # Interpretacja
        if alpha < 0.667:
            interp = "Niedostateczna (odrzucić wnioski)"
        elif alpha < 0.800:
            interp = "Wstępna (tentative conclusions)"
        else:
            interp = "Definitywna (definite conclusions)"
        
        return alpha, interp
        
    except Exception as e:
        return np.nan, f"Błąd: {str(e)}"


def intraclass_correlation(
    data: np.ndarray,
    model: str = 'ICC(2,1)'
) -> Tuple[float, Tuple[float, float], str]:
    """
    Oblicz Intraclass Correlation Coefficient (ICC).
    
    ICC jest odpowiedni dla danych ciągłych i mierzy spójność
    między ocenami różnych koderów.
    
    Args:
        data: Macierz (units × raters)
        model: Model ICC - 'ICC(1,1)', 'ICC(2,1)', 'ICC(3,1)', etc.
               ICC(2,1) - Two-way random effects, single rater
               
    Returns:
        Tuple[float, Tuple[float, float], str]: (ICC, (CI_lower, CI_upper), interpretacja)
        
    Interpretacja (Koo & Li, 2016):
        < 0.50: Poor
        0.50 - 0.75: Moderate
        0.75 - 0.90: Good
        > 0.90: Excellent
    """
    try:
        # Remove rows with all NaN
        mask = ~np.all(np.isnan(data), axis=1)
        data = data[mask]
        
        n_units, n_raters = data.shape
        
        if n_units < 2 or n_raters < 2:
            return np.nan, (np.nan, np.nan), "Niewystarczające dane"
        
        # Calculate means
        grand_mean = np.nanmean(data)
        unit_means = np.nanmean(data, axis=1)
        rater_means = np.nanmean(data, axis=0)
        
        # Calculate sums of squares
        SS_total = np.nansum((data - grand_mean) ** 2)
        SS_rows = n_raters * np.nansum((unit_means - grand_mean) ** 2)
        SS_cols = n_units * np.nansum((rater_means - grand_mean) ** 2)
        SS_error = SS_total - SS_rows - SS_cols
        
        # Degrees of freedom
        df_rows = n_units - 1
        df_cols = n_raters - 1
        df_error = df_rows * df_cols
        
        # Mean squares
        MS_rows = SS_rows / df_rows
        MS_cols = SS_cols / df_cols
        MS_error = SS_error / df_error
        
        # ICC(2,1) - Two-way random effects, single measurement
        icc = (MS_rows - MS_error) / (MS_rows + (n_raters - 1) * MS_error + n_raters * (MS_cols - MS_error) / n_units)
        
        # Confidence interval (95%)
        F = MS_rows / MS_error
        df1 = df_rows
        df2 = df_error
        
        F_lower = F / stats.f.ppf(0.975, df1, df2)
        F_upper = F / stats.f.ppf(0.025, df1, df2)
        
        ci_lower = (F_lower - 1) / (F_lower + (n_raters - 1))
        ci_upper = (F_upper - 1) / (F_upper + (n_raters - 1))
        
        # Interpretacja
        if icc < 0.50:
            interp = "Słaba (Poor)"
        elif icc < 0.75:
            interp = "Umiarkowana (Moderate)"
        elif icc < 0.90:
            interp = "Dobra (Good)"
        else:
            interp = "Doskonała (Excellent)"
        
        return icc, (ci_lower, ci_upper), interp
        
    except Exception as e:
        return np.nan, (np.nan, np.nan), f"Błąd: {str(e)}"


def percent_agreement(rater1: np.ndarray, rater2: np.ndarray) -> Tuple[float, str]:
    """
    Oblicz prostą procentową zgodność.
    
    Uwaga: Ten wskaźnik nie uwzględnia zgodności przypadkowej!
    Używaj tylko jako uzupełnienie innych wskaźników.
    
    Args:
        rater1: Oceny pierwszego kodera
        rater2: Oceny drugiego kodera
        
    Returns:
        Tuple[float, str]: (procent zgodności, interpretacja)
    """
    try:
        mask = ~(np.isnan(rater1) | np.isnan(rater2))
        r1 = rater1[mask]
        r2 = rater2[mask]
        
        if len(r1) == 0:
            return np.nan, "Brak danych"
        
        agreement = np.sum(r1 == r2) / len(r1) * 100
        
        if agreement < 50:
            interp = "Bardzo niska"
        elif agreement < 70:
            interp = "Niska"
        elif agreement < 85:
            interp = "Umiarkowana"
        else:
            interp = "Wysoka"
        
        return agreement, interp
        
    except Exception as e:
        return np.nan, f"Błąd: {str(e)}"


def compute_confusion_matrix(
    rater1: np.ndarray,
    rater2: np.ndarray,
    labels: Optional[List] = None
) -> Tuple[np.ndarray, List]:
    """
    Oblicz macierz konfuzji między dwoma koderami.
    
    Args:
        rater1: Oceny pierwszego kodera (ground truth)
        rater2: Oceny drugiego kodera (predictions)
        labels: Lista etykiet kategorii
        
    Returns:
        Tuple[np.ndarray, List]: (macierz konfuzji, lista etykiet)
    """
    try:
        mask = ~(np.isnan(rater1) | np.isnan(rater2))
        r1 = rater1[mask]
        r2 = rater2[mask]
        
        if len(r1) == 0:
            return np.array([]), []
        
        if labels is None:
            labels = sorted(list(set(r1) | set(r2)))
        
        cm = confusion_matrix(r1, r2, labels=labels)
        
        return cm, labels
        
    except Exception as e:
        return np.array([]), []


def compute_all_metrics(
    rater1: np.ndarray,
    rater2: np.ndarray,
    data_type: str = 'ordinal'
) -> Dict:
    """
    Oblicz wszystkie wskaźniki zgodności dla pary koderów.
    
    Args:
        rater1: Oceny pierwszego kodera
        rater2: Oceny drugiego kodera
        data_type: 'nominal', 'ordinal', lub 'continuous'
        
    Returns:
        Dict ze wszystkimi obliczonymi metrykami
    """
    results = {
        'n_samples': int(np.sum(~(np.isnan(rater1) | np.isnan(rater2)))),
        'percent_agreement': None,
        'cohen_kappa': None,
        'weighted_kappa': None,
        'krippendorff_alpha': None,
        'icc': None,
        'pearson_r': None,
        'spearman_rho': None
    }
    
    # Percent agreement
    pa, pa_interp = percent_agreement(rater1, rater2)
    results['percent_agreement'] = {'value': pa, 'interpretation': pa_interp}
    
    # Cohen's Kappa
    if data_type in ['nominal', 'ordinal']:
        ck, ck_interp = cohen_kappa(rater1, rater2, weights=None)
        results['cohen_kappa'] = {'value': ck, 'interpretation': ck_interp}
        
        if data_type == 'ordinal':
            wk, wk_interp = cohen_kappa(rater1, rater2, weights='quadratic')
            results['weighted_kappa'] = {'value': wk, 'interpretation': wk_interp}
    
    # Krippendorff's Alpha
    data_matrix = np.column_stack([rater1, rater2])
    level = 'ordinal' if data_type == 'ordinal' else 'nominal' if data_type == 'nominal' else 'interval'
    ka, ka_interp = krippendorff_alpha(data_matrix, level_of_measurement=level)
    results['krippendorff_alpha'] = {'value': ka, 'interpretation': ka_interp}
    
    # ICC (for ordinal and continuous)
    if data_type in ['ordinal', 'continuous']:
        icc_val, icc_ci, icc_interp = intraclass_correlation(data_matrix, model='ICC(2,1)')
        results['icc'] = {
            'value': icc_val,
            'ci_lower': icc_ci[0],
            'ci_upper': icc_ci[1],
            'interpretation': icc_interp
        }
    
    # Correlations (for ordinal and continuous)
    if data_type in ['ordinal', 'continuous']:
        mask = ~(np.isnan(rater1) | np.isnan(rater2))
        r1 = rater1[mask]
        r2 = rater2[mask]
        
        if len(r1) >= 3:
            # Pearson correlation
            pearson_r, pearson_p = stats.pearsonr(r1, r2)
            results['pearson_r'] = {'value': pearson_r, 'p_value': pearson_p}
            
            # Spearman correlation (more appropriate for ordinal)
            spearman_rho, spearman_p = stats.spearmanr(r1, r2)
            results['spearman_rho'] = {'value': spearman_rho, 'p_value': spearman_p}
    
    return results


def compute_multi_rater_metrics(data: pd.DataFrame, columns: List[str]) -> Dict:
    """
    Oblicz wskaźniki dla więcej niż dwóch koderów.
    
    Args:
        data: DataFrame z oceną
        columns: Lista kolumn reprezentujących różnych koderów
        
    Returns:
        Dict z metrykami dla wielu koderów
    """
    data_matrix = data[columns].values
    
    results = {
        'n_raters': len(columns),
        'n_units': len(data),
        'krippendorff_alpha_ordinal': None,
        'fleiss_kappa': None,
        'icc': None
    }
    
    # Krippendorff's Alpha
    ka, ka_interp = krippendorff_alpha(data_matrix, level_of_measurement='ordinal')
    results['krippendorff_alpha_ordinal'] = {'value': ka, 'interpretation': ka_interp}
    
    # ICC
    icc_val, icc_ci, icc_interp = intraclass_correlation(data_matrix, model='ICC(2,1)')
    results['icc'] = {
        'value': icc_val,
        'ci_lower': icc_ci[0],
        'ci_upper': icc_ci[1],
        'interpretation': icc_interp
    }
    
    return results
