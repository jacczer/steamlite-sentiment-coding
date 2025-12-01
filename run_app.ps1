# Skrypt do uruchamiania aplikacji Streamlit
# Użycie: ./run_app.ps1

$venvPath = "c:\Users\jacze\Projects_vs_code\dr_fn\fn_data_analysis\.venv\Scripts\streamlit.exe"
$appPath = "C:\aktywne\dysk-M\sdns\dr-fn\Analiza_Treści_Fake_News\fn_data_analysis\app\wer_llm\sent_emo_app\sent_emo_app.py"

Write-Host "Uruchamianie aplikacji Streamlit..." -ForegroundColor Green
Write-Host "Aplikacja będzie dostępna pod adresem: http://localhost:8502" -ForegroundColor Cyan
Write-Host ""

& $venvPath run $appPath
