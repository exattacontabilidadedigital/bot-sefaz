@echo off
echo Iniciando SEFAZ Bot Web Interface...
echo.

echo Verificando dependencias...
pip install -r requirements-api.txt

echo.
echo Iniciando servidor...
echo Interface web estara disponivel em: http://localhost:8000
echo.

python api.py