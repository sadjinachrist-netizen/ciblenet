@echo off
cd /d "%~dp0"
if exist .env for /f "usebackq tokens=1,* delims==" %%a in (".env") do set "%%a=%%b"
python -m streamlit run app.py
