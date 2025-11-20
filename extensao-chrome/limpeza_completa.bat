@echo off
echo 🔥 LIMPEZA COMPLETA - Removendo extensão bloqueada gimjjdmndkikigfgmnaaejbnahdhailc
echo.

echo ⏹️ Fechando TODOS os processos do Chrome...
taskkill /f /im chrome.exe 2>nul
taskkill /f /im msedge.exe 2>nul
timeout /t 3 /nobreak >nul

echo 🗑️ Limpando dados da extensão antiga...
set "CHROME_USER_DATA=%LOCALAPPDATA%\Google\Chrome\User Data"
set "EDGE_USER_DATA=%LOCALAPPDATA%\Microsoft\Edge\User Data"

if exist "%CHROME_USER_DATA%\Default\Extensions\gimjjdmndkikigfgmnaaejbnahdhailc" (
    echo 🔍 Removendo extensão antiga do Chrome...
    rmdir /s /q "%CHROME_USER_DATA%\Default\Extensions\gimjjdmndkikigfgmnaaejbnahdhailc" 2>nul
)

if exist "%CHROME_USER_DATA%\Default\Local Extension Settings\gimjjdmndkikigfgmnaaejbnahdhailc" (
    echo 🔍 Removendo configurações da extensão...
    rmdir /s /q "%CHROME_USER_DATA%\Default\Local Extension Settings\gimjjdmndkikigfgmnaaejbnahdhailc" 2>nul
)

echo 🧹 Limpando cache geral do Chrome...
if exist "%CHROME_USER_DATA%\Default\Cache" (
    rmdir /s /q "%CHROME_USER_DATA%\Default\Cache" 2>nul
)

if exist "%CHROME_USER_DATA%\Default\Code Cache" (
    rmdir /s /q "%CHROME_USER_DATA%\Default\Code Cache" 2>nul
)

if exist "%CHROME_USER_DATA%\ShaderCache" (
    rmdir /s /q "%CHROME_USER_DATA%\ShaderCache" 2>nul
)

echo 🔄 Criando perfil limpo temporário...
set "TEMP_PROFILE=%TEMP%\chrome_clean_sefaz_%RANDOM%"
mkdir "%TEMP_PROFILE%" 2>nul

echo ✨ Iniciando Chrome com perfil completamente limpo...
start chrome.exe --user-data-dir="%TEMP_PROFILE%" --load-extension="%~dp0" --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-features=TranslateUI --disable-ipc-flooding-protection

echo.
echo ✅ LIMPEZA COMPLETA REALIZADA!
echo 📍 Chrome iniciado com perfil limpo e nova extensão
echo 🆔 NOVA EXTENSÃO: Portal SEFAZ Automator v2.0.0
echo 🔍 Vá para chrome://extensions/ para verificar o novo ID
echo.
echo ⚠️  IMPORTANTE: Anote o novo ID da extensão para usar na aplicação
echo.
pause