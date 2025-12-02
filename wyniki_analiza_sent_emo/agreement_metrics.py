"""
Moduł obliczający wskaźniki zgodności między różnymi metodami kodowania.

Implementuje rzetelne metody statystyczne zgodnie ze standardami badań
nad zgodnością międzykoderkową (inter-rater reliability).

Metodologia oparta na:
- Krippendorff, K. (2004). Content Analysis: An Introduction to Its Methodology
- Landis, J.R. & Koch, G.G. (1977). The measurement of observer agreement for categorical data
- Cicchetti, D.V. (1994). Guidelines, criteria, and rules of thumb for evaluating normed and standardized assessment instruments
- Koo, T.K. & Li, M.Y. (2016). A guideline of selecting and reporting intraclass correlation coefficients
"""
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional
from scipy import stats
from sklearn.metrics import confusion_matrix, cohen_kappa_score
import warnings

# Try to import krippendorff library (more accurate implementation)
try:
    import krippendorff as krippendorff_lib
    HAS_KRIPPENDORFF = True
except ImportError:
    HAS_KRIPPENDORFF = False


def compute_cohens_kappa(
    rater1: np.ndarray,
    rater2: np.ndarray,
    weights: Optional[str] = 'quadratic'
) -> Optional[Dict]:
    """
    Compute Cohen's Kappa with optional weighting for ordinal data.
    
    For ordinal data (like 0-1-2 scale), quadratic weights are recommended
    as they penalize larger disagreements more heavily, which is appropriate
    for ordered categories.
    
    Args:
        rater1: Ratings from first rater
        rater2: Ratings from second rater
        weights: None, 'linear', or 'quadratic' (recommended for ordinal data)
        
    Returns:
        Dict with 'value', 'interpretation', 'se' (standard error), 'ci_lower', 'ci_upper'
        or None if computation fails
        
    References:
        Cohen, J. (1968). Weighted kappa: Nominal scale agreement provision for scaled 
        disagreement or partial credit. Psychological Bulletin, 70(4), 213-220.
    """
    try:
        # Remove NaN values
        mask = ~(np.isnan(rater1) | np.isnan(rater2))
        r1 = rater1[mask].astype(int)
        r2 = rater2[mask].astype(int)
        
        n = len(r1)
        if n < 2:
            return None
        
        kappa = cohen_kappa_score(r1, r2, weights=weights)
        
        # Compute standard error using bootstrap (approximate)
        # For large samples, use analytical SE
        # SE(kappa) ≈ sqrt((p_o * (1 - p_o)) / (n * (1 - p_e)^2))
        # This is a simplified approximation
        p_o = np.sum(r1 == r2) / n
        categories = np.unique(np.concatenate([r1, r2]))
        p_e = sum((np.sum(r1 == c) / n) * (np.sum(r2 == c) / n) for c in categories)
        
        if (1 - p_e) > 0:
            se = np.sqrt((p_o * (1 - p_o)) / (n * (1 - p_e) ** 2))
        else:
            se = 0
        
        # 95% confidence interval
        z = 1.96
        ci_lower = max(-1, kappa - z * se)
        ci_upper = min(1, kappa + z * se)
        
        # Interpretation (Landis & Koch, 1977)
        if kappa < 0:
            interp = "Słaba (gorsza niż losowa)"
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
        
        return {
            'value': kappa,
            'interpretation': interp,
            'se': se,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'n': n
        }
        
    except Exception as e:
        return None


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
    
    Uses the 'krippendorff' library if available, otherwise falls back to
    a custom implementation.
    
    Args:
        data: Macierz (units × raters), wartości to oceny
        level_of_measurement: 'nominal', 'ordinal', 'interval', lub 'ratio'
        
    Returns:
        Tuple[float, str]: (wartość alpha, interpretacja)
        
    Interpretacja (Krippendorff, 2004):
        < 0.667: Odrzucić wnioski
        0.667 - 0.800: Wnioski wstępne (tentative)
        > 0.800: Wnioski definitywne (definite)
        
    References:
        Krippendorff, K. (2004). Content Analysis: An Introduction to Its Methodology.
        Krippendorff, K. (2011). Computing Krippendorff's Alpha-Reliability.
    """
    try:
        # Try using the krippendorff library first (more accurate)
        if HAS_KRIPPENDORFF:
            # The library expects data in format: rows=raters, cols=units
            # and uses np.nan for missing values
            data_transposed = data.T  # Convert from (units x raters) to (raters x units)
            
            alpha = krippendorff_lib.alpha(
                reliability_data=data_transposed,
                level_of_measurement=level_of_measurement,
                value_domain=None  # Auto-detect
            )
        else:
            # Fallback to custom implementation
            alpha = _compute_krippendorff_alpha_custom(data, level_of_measurement)
        
        if np.isnan(alpha):
            return np.nan, "Niewystarczające dane"
        
        # Interpretacja (Krippendorff, 2004)
        if alpha < 0.667:
            interp = "Niedostateczna (odrzucić wnioski)"
        elif alpha < 0.800:
            interp = "Wstępna (tentative conclusions)"
        else:
            interp = "Definitywna (definite conclusions)"
        
        return alpha, interp
        
    except Exception as e:
        return np.nan, f"Błąd: {str(e)}"


def _compute_krippendorff_alpha_custom(
    data: np.ndarray,
    level_of_measurement: str = 'ordinal'
) -> float:
    """
    Custom implementation of Krippendorff's Alpha (fallback).
    
    Based on: Krippendorff, K. (2004). Content Analysis: An Introduction to Its Methodology
    """
    n_units, n_raters = data.shape
    
    # Create coincidence matrix
    values = np.unique(data[~np.isnan(data)])
    n_values = len(values)
    
    if n_values < 2:
        return np.nan
    
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
        return np.nan
    
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
        return np.nan
    
    return 1 - (D_o / D_e)


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
    
    This function computes a comprehensive set of inter-rater reliability
    metrics appropriate for the specified data type.
    
    Args:
        rater1: Oceny pierwszego kodera
        rater2: Oceny drugiego kodera
        data_type: 'nominal', 'ordinal', lub 'continuous'
        
    Returns:
        Dict ze wszystkimi obliczonymi metrykami, w tym przedziałami ufności
        
    Notes:
        For ordinal data (like 0-1-2 scales), this function uses:
        - Quadratic-weighted Cohen's Kappa (penalizes larger disagreements more)
        - Krippendorff's Alpha with ordinal level of measurement
        - ICC(2,1) for consistency assessment
        - Spearman's rho (rank correlation, appropriate for ordinal data)
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
    
    # Percent agreement (simple, but doesn't account for chance)
    pa, pa_interp = percent_agreement(rater1, rater2)
    results['percent_agreement'] = {'value': pa, 'interpretation': pa_interp}
    
    # Cohen's Kappa - use the enhanced version with CI
    if data_type in ['nominal', 'ordinal']:
        # Unweighted kappa (for nominal comparison)
        ck_result = compute_cohens_kappa(rater1, rater2, weights=None)
        if ck_result:
            results['cohen_kappa'] = ck_result
        
        if data_type == 'ordinal':
            # Quadratic-weighted kappa (recommended for ordinal data)
            wk_result = compute_cohens_kappa(rater1, rater2, weights='quadratic')
            if wk_result:
                results['weighted_kappa'] = wk_result
    
    # Krippendorff's Alpha - most robust metric
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
            # Pearson correlation (for reference, less appropriate for ordinal)
            pearson_r, pearson_p = stats.pearsonr(r1, r2)
            results['pearson_r'] = {'value': pearson_r, 'p_value': pearson_p}
            
            # Spearman correlation (more appropriate for ordinal - rank-based)
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


def compute_krippendorff_alpha_with_ci(
    data: np.ndarray,
    level_of_measurement: str = 'ordinal',
    n_bootstrap: int = 1000,
    confidence: float = 0.95
) -> Dict:
    """
    Compute Krippendorff's Alpha with bootstrap confidence interval.
    
    Bootstrap resampling is the recommended method for computing confidence
    intervals for Krippendorff's Alpha (Krippendorff, 2011).
    
    Args:
        data: Matrix of shape (n_units, n_raters)
        level_of_measurement: 'nominal', 'ordinal', 'interval', or 'ratio'
        n_bootstrap: Number of bootstrap samples (default 1000)
        confidence: Confidence level (default 0.95 for 95% CI)
        
    Returns:
        Dict with 'value', 'ci_lower', 'ci_upper', 'interpretation', 'se'
        
    References:
        Krippendorff, K. (2011). Computing Krippendorff's Alpha-Reliability.
    """
    try:
        # Compute point estimate
        alpha, interp = krippendorff_alpha(data, level_of_measurement)
        
        if np.isnan(alpha):
            return {
                'value': np.nan,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'interpretation': interp,
                'se': np.nan
            }
        
        # Bootstrap for confidence interval
        n_units = data.shape[0]
        bootstrap_alphas = []
        
        for _ in range(n_bootstrap):
            # Resample units (rows) with replacement
            indices = np.random.choice(n_units, size=n_units, replace=True)
            bootstrap_sample = data[indices, :]
            
            try:
                boot_alpha, _ = krippendorff_alpha(bootstrap_sample, level_of_measurement)
                if not np.isnan(boot_alpha):
                    bootstrap_alphas.append(boot_alpha)
            except:
                pass
        
        if len(bootstrap_alphas) < 100:
            # Not enough successful bootstrap samples
            return {
                'value': alpha,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'interpretation': interp,
                'se': np.nan
            }
        
        # Compute percentile CI
        alpha_level = (1 - confidence) / 2
        ci_lower = np.percentile(bootstrap_alphas, alpha_level * 100)
        ci_upper = np.percentile(bootstrap_alphas, (1 - alpha_level) * 100)
        se = np.std(bootstrap_alphas)
        
        return {
            'value': alpha,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'interpretation': interp,
            'se': se
        }
        
    except Exception as e:
        return {
            'value': np.nan,
            'ci_lower': np.nan,
            'ci_upper': np.nan,
            'interpretation': f"Błąd: {str(e)}",
            'se': np.nan
        }


def compute_krippendorff_alpha_multi(
    data: np.ndarray,
    data_type: str = 'ordinal'
) -> Optional[float]:
    """
    Compute Krippendorff's Alpha for multiple raters.
    
    Args:
        data: Matrix of shape (n_raters, n_units) - each row is a rater
        data_type: 'nominal', 'ordinal', 'interval', or 'ratio'
        
    Returns:
        Alpha value or None if computation fails
    """
    try:
        # Transpose if needed: we need (units x raters) format for our krippendorff_alpha function
        if data.shape[0] < data.shape[1]:
            # Rows are raters, cols are units - transpose
            data = data.T
        
        alpha, _ = krippendorff_alpha(data, level_of_measurement=data_type)
        
        if np.isnan(alpha):
            return None
        return alpha
        
    except Exception:
        return None


def compute_fleiss_kappa(
    data: np.ndarray
) -> Optional[float]:
    """
    Compute Fleiss' Kappa for multiple raters with categorical data.
    
    Fleiss' Kappa is a generalization of Cohen's Kappa for more than 2 raters.
    
    Args:
        data: Matrix of shape (n_units, n_raters) - each column is a rater
        
    Returns:
        Fleiss' Kappa value or None if computation fails
    """
    try:
        n_subjects, n_raters = data.shape
        
        # Get unique categories
        categories = np.unique(data[~np.isnan(data)])
        n_categories = len(categories)
        
        if n_categories < 2:
            return None
        
        # Create category count matrix
        # n_ij = number of raters who assigned subject i to category j
        n_matrix = np.zeros((n_subjects, n_categories))
        
        for i, cat in enumerate(categories):
            n_matrix[:, i] = np.sum(data == cat, axis=1)
        
        # Compute P_i (proportion of agreement for each subject)
        n_total = n_raters  # assumes no missing data per row
        P_i = (np.sum(n_matrix ** 2, axis=1) - n_total) / (n_total * (n_total - 1))
        
        # Mean P
        P_bar = np.mean(P_i)
        
        # Compute P_j (proportion of all assignments to category j)
        P_j = np.sum(n_matrix, axis=0) / (n_subjects * n_raters)
        
        # P_e (expected agreement by chance)
        P_e = np.sum(P_j ** 2)
        
        # Fleiss' Kappa
        if P_e == 1:
            return 1.0  # Perfect agreement
        
        kappa = (P_bar - P_e) / (1 - P_e)
        
        return kappa
        
    except Exception:
        return None


def compute_icc_multi(
    data: np.ndarray
) -> Optional[float]:
    """
    Compute Intraclass Correlation Coefficient for multiple raters.
    
    Uses ICC(2,1) - two-way random effects, single measures, absolute agreement.
    
    Args:
        data: Matrix of shape (n_units, n_raters)
        
    Returns:
        ICC value or None if computation fails
    """
    try:
        # Remove rows with any NaN
        valid_rows = ~np.any(np.isnan(data), axis=1)
        clean_data = data[valid_rows]
        
        if len(clean_data) < 3:
            return None
        
        icc_val, _, _ = intraclass_correlation(clean_data, model='ICC(2,1)')
        
        if np.isnan(icc_val):
            return None
        
        return icc_val
        
    except Exception:
        return None
