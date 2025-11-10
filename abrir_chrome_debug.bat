@echo off
echo ================================================================================
echo INICIANDO CHROME COM DEBUG REMOTO
echo ================================================================================
echo.
echo Este Chrome vai permitir que o bot se conecte a ele
echo Faca o login manual no SEFAZ e depois execute o script Python
echo.
echo Abrindo Chrome...
echo.

"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome_debug_sefaz"
