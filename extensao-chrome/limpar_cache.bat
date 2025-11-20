@echo off
echo 🧹 Limpando cache da extensão Chrome...
echo.

echo ⏹️ Fechando Chrome (se aberto)...
taskkill /f /im chrome.exe 2>nul
timeout /t 2 /nobreak >nul

echo 🗑️ Removendo cache temporário...
if exist "%TEMP%\chrome_extension_cache" (
    rmdir /s /q "%TEMP%\chrome_extension_cache" 2>nul
)

echo 🔄 Removendo arquivos temporários da pasta extensão...
if exist "%~dp0\.tmp" (
    rmdir /s /q "%~dp0\.tmp" 2>nul
)

if exist "%~dp0\node_modules" (
    rmdir /s /q "%~dp0\node_modules" 2>nul
)

echo ✨ Iniciando Chrome com cache limpo...
start chrome.exe --disable-extensions-except="%~dp0" --load-extension="%~dp0" --disable-web-security --user-data-dir="%TEMP%\chrome_clean_profile" --no-first-run --disable-background-timer-throttling

echo.
echo ✅ Cache limpo e Chrome iniciado com perfil limpo!
echo 📍 Vá para chrome://extensions/ para verificar se a extensão carregou
echo.
pause