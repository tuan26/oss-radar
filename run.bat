@echo off
REM Chay OSS Radar khong can Docker (Windows)
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv (
  echo Tao moi truong ao .venv ...
  py -3 -m venv .venv || python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q --disable-pip-version-check -r requirements.txt
if "%DATA_DIR%"=="" set DATA_DIR=%cd%\data
if "%HOST%"=="" set HOST=127.0.0.1
if "%PORT%"=="" set PORT=8080
echo OSS Radar chay tai http://localhost:%PORT%  (Ctrl+C de dung)
python -m uvicorn app.main:app --host %HOST% --port %PORT%
