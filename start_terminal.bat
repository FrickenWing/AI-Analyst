:loop
echo.
echo ========================================================
echo  Starte AI-Analyst... (Druecke STRG+C zum Beenden)
echo ========================================================
echo.

:: 1. Aktiviere die Miniconda-Umgebung
call "C:\Users\Luca1\anaconda3\Scripts\activate.bat" openbb_env

:: 2. Wechsle auf dein Laufwerk und in den Ordner
cd D:\GitHub-Repository\AI-Analyst

pip install -r requirements.txt

:: 3. Starte das Dashboard
echo Starte Streamlit-Server...
streamlit run app.py

:: Wenn Streamlit beendet wird (z.B. durch Fehler), wartet er 3 Sekunden
:: und startet dann von vorne
echo.
echo ⚠️  Server wurde beendet. Neustart in 3 Sekunden...
timeout /t 3 >nul
goto loop