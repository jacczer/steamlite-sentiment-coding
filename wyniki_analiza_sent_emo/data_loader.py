"""
Moduł do wczytywania i łączenia danych z różnych źródeł dla analizy zgodności kodowania.
"""
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
from typing import Tuple, Optional, Dict, List
import streamlit as st


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def fix_private_key(key: str) -> str:
    """Fix escaped newlines in private key."""
    return key.replace(chr(92) + 'n', chr(10))


def get_google_sheets_client():
    """
    Create Google Sheets client and return worksheet.
    
    Returns:
        Tuple[Optional[gspread.Worksheet], Optional[str]]: (worksheet, error_message)
    """
    try:
        if "SPREADSHEET_ID" not in st.secrets:
            return None, "Brak SPREADSHEET_ID w secrets!"
        
        creds_info = None
        
        # Try different secret configurations
        if "service_account_json" in st.secrets:
            import json
            creds_info = json.loads(st.secrets["service_account_json"])
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


def load_parquet_data(file_path: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Load data from Parquet file.
    
    Args:
        file_path: Path to the Parquet file
        
    Returns:
        Tuple[Optional[pd.DataFrame], Optional[str]]: (dataframe, error_message)
    """
    try:
        df = pd.read_parquet(file_path)
        return df, None
    except Exception as e:
        return None, f"Błąd wczytywania pliku Parquet: {str(e)}"


def load_manual_coding_data() -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Load manual coding data from Google Sheets.
    
    Expected columns in Google Sheets:
    - timestamp
    - coder_id
    - oid (Object ID matching post_id in Parquet)
    - text
    - positive, negative, neutral (0-3) -> renamed to sentiment_positive, sentiment_negative, sentiment_neutral
    - joy, trust, anticipation, surprise, fear, sadness, disgust, anger (0-3) -> renamed to emotion_*
    
    Note: Columns are automatically renamed from short names (positive, joy) to prefixed names
    (sentiment_positive, emotion_joy) for consistency with the analysis code.
      
    Returns:
        Tuple[Optional[pd.DataFrame], Optional[str]]: (dataframe, error_message)
    """
    ws, error = get_google_sheets_client()
    if ws is None:
        return None, error
    
    try:
        # Get all records
        records = ws.get_all_records()
        if not records:
            return None, "Brak danych w arkuszu Google Sheets"
        
        df = pd.DataFrame(records)
        
        # Map old column names to expected names
        # Google Sheets has: positive, negative, neutral, joy, trust, etc.
        # We need: sentiment_positive, sentiment_negative, sentiment_neutral, emotion_joy, etc.
        column_mapping = {
            'positive': 'sentiment_positive',
            'negative': 'sentiment_negative',
            'neutral': 'sentiment_neutral',
            'joy': 'emotion_joy',
            'trust': 'emotion_trust',
            'anticipation': 'emotion_anticipation',
            'surprise': 'emotion_surprise',
            'fear': 'emotion_fear',
            'sadness': 'emotion_sadness',
            'disgust': 'emotion_disgust',
            'anger': 'emotion_anger'
        }
        
        # Rename columns if they exist in the old format
        df = df.rename(columns=column_mapping)
        
        # Expected columns
        expected_cols = [
            'timestamp', 'coder_id', 'oid', 'text',
            'sentiment_positive', 'sentiment_negative', 'sentiment_neutral',
            'emotion_joy', 'emotion_trust', 'emotion_anticipation', 'emotion_surprise',
            'emotion_fear', 'emotion_sadness', 'emotion_disgust', 'emotion_anger'
        ]
        
        missing_cols = [col for col in expected_cols if col not in df.columns]
        if missing_cols:
            return None, f"Brakujące kolumny w arkuszu: {', '.join(missing_cols)}"
        
        # Convert oid to string for matching
        df['oid'] = df['oid'].astype(str)
        
        # Convert sentiment and emotion columns to numeric
        sentiment_cols = ['sentiment_positive', 'sentiment_negative', 'sentiment_neutral']
        emotion_cols = ['emotion_joy', 'emotion_trust', 'emotion_anticipation', 'emotion_surprise',
                       'emotion_fear', 'emotion_sadness', 'emotion_disgust', 'emotion_anger']
        
        for col in sentiment_cols + emotion_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        return df, None
        
    except Exception as e:
        return None, f"Błąd wczytywania danych z Google Sheets: {str(e)}"


def merge_datasets(
    parquet_df: pd.DataFrame,
    manual_df: pd.DataFrame,
    on_column: str = 'post_id'
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Merge automatic and manual coding datasets.
    
    Args:
        parquet_df: DataFrame with automatic coding (from Parquet)
        manual_df: DataFrame with manual coding (from Google Sheets)
        on_column: Column name to merge on (default: 'post_id')
        
    Returns:
        Tuple[Optional[pd.DataFrame], Optional[str]]: (merged_dataframe, error_message)
    """
    try:
        # Ensure both have the merge column
        if on_column not in parquet_df.columns:
            return None, f"Kolumna '{on_column}' nie istnieje w danych automatycznych"
        
        # Convert parquet post_id to string for matching with oid
        parquet_df = parquet_df.copy()
        parquet_df[on_column] = parquet_df[on_column].astype(str)
        
        # Merge on post_id (parquet) = oid (manual)
        merged = parquet_df.merge(
            manual_df,
            left_on=on_column,
            right_on='oid',
            how='inner',
            suffixes=('_auto', '_manual')
        )
        
        if len(merged) == 0:
            return None, "Brak wspólnych rekordów między danymi automatycznymi a manualnymi"
        
        return merged, None
        
    except Exception as e:
        return None, f"Błąd łączenia danych: {str(e)}"


def get_sentiment_columns() -> Dict[str, List[str]]:
    """
    Get column names for different sentiment coding sources.
    
    Returns:
        Dict with keys: 'sent_emo', 'sent_emo_llm', 'manual'
    """
    return {
        'sent_emo': [
            'SENT_EMO_sentyment_positive',
            'SENT_EMO_sentyment_negative',
            'SENT_EMO_sentyment_neutral'
        ],
        'sent_emo_llm': [
            'SENT_EMO_LLM_sentyment_positive',
            'SENT_EMO_LLM_sentyment_negative',
            'SENT_EMO_LLM_sentyment_neutral'
        ],
        'manual': [
            'sentiment_positive',
            'sentiment_negative',
            'sentiment_neutral'
        ]
    }


def get_emotion_columns() -> Dict[str, List[str]]:
    """
    Get column names for different emotion coding sources.
    
    Returns:
        Dict with keys: 'sent_emo', 'sent_emo_llm', 'manual'
    """
    emotions = ['joy', 'trust', 'anticipation', 'surprise', 'fear', 'sadness', 'disgust', 'anger']
    
    return {
        'sent_emo': [f'SENT_EMO_emocje_{e}' for e in emotions],
        'sent_emo_llm': [f'SENT_EMO_LLM_emocje_{e}' for e in emotions],
        'manual': [f'emotion_{e}' for e in emotions]
    }


def get_category_labels() -> Dict[str, Dict[str, str]]:
    """
    Get human-readable labels for sentiment and emotion categories.
    
    Returns:
        Dict with keys: 'sentiments', 'emotions'
    """
    return {
        'sentiments': {
            'positive': 'Pozytywny',
            'negative': 'Negatywny',
            'neutral': 'Neutralny'
        },
        'emotions': {
            'joy': 'Radość',
            'trust': 'Zaufanie',
            'anticipation': 'Oczekiwanie',
            'surprise': 'Zaskoczenie',
            'fear': 'Strach',
            'sadness': 'Smutek',
            'disgust': 'Wstręt',
            'anger': 'Złość'
        }
    }


def normalize_to_scale(
    values: pd.Series,
    source_type: str,
    target_scale: str = '0-3'
) -> pd.Series:
    """
    Normalize values to a common scale for comparison.
    
    Args:
        values: Series of values to normalize
        source_type: Type of source data ('sent_emo', 'sent_emo_llm', 'manual')
        target_scale: Target scale ('0-3' or '0-1')
        
    Returns:
        Normalized Series
    """
    if source_type == 'manual':
        # Manual is already 0-3
        if target_scale == '0-1':
            return values / 3.0
        return values
    
    elif source_type == 'sent_emo':
        # SENT_EMO is 0-1 (continuous)
        if target_scale == '0-3':
            # Map to discrete 0-3 scale
            # 0-0.25 -> 0, 0.25-0.5 -> 1, 0.5-0.75 -> 2, 0.75-1.0 -> 3
            return pd.cut(values, bins=[-0.001, 0.25, 0.5, 0.75, 1.0], labels=[0, 1, 2, 3]).astype(int)
        return values
    
    elif source_type == 'sent_emo_llm':
        # SENT_EMO_LLM is 0-0.95 with step 0.05
        if target_scale == '0-3':
            # Map proportionally to 0-3 scale
            return (values / 0.95 * 3).round().astype(int)
        else:  # 0-1
            return values / 0.95
    
    return values


def get_category_labels() -> Dict[str, Dict[str, str]]:
    """
    Get Polish labels for sentiment and emotion categories.
    
    Returns:
        Dict with 'sentiments' and 'emotions' keys
    """
    return {
        'sentiments': {
            'positive': 'Pozytywny',
            'negative': 'Negatywny',
            'neutral': 'Neutralny'
        },
        'emotions': {
            'joy': 'Radość',
            'trust': 'Zaufanie',
            'anticipation': 'Oczekiwanie',
            'surprise': 'Zaskoczenie',
            'fear': 'Strach',
            'sadness': 'Smutek',
            'disgust': 'Wstręt',
            'anger': 'Złość'
        }
    }
