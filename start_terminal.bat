@echo off
title KI Trading Terminal Start-Skript
echo Lade AI-Analyst Terminal v2 2026...
echo -----------------------------------

:: 1. Aktiviere die Miniconda-Umgebung
call "C:\Users\Luca1\miniconda3\Scripts\activate.bat" openbb_env

:: 2. Wechsle auf dein Laufwerk und in den Ordner
cd A:\OpenBB

pip install -r requirements.txt

:: 3. Starte das Dashboard
echo Starte Streamlit-Server...
streamlit run app.py

pause