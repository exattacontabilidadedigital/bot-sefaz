#!/bin/bash
set -e

echo "🚀 Iniciando Bot SEFAZ..."
echo "📁 Diretório: $(pwd)"
echo "🐍 Python: $(python --version)"
echo "📦 Pip: $(pip --version)"

# Verificar arquivos
echo "📄 Arquivos disponíveis:"
ls -la

# Verificar dependências instaladas
echo "📦 Verificando dependências..."
python -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)" || echo "⚠️  FastAPI não encontrado"
python -c "import uvicorn; print('✅ Uvicorn:', uvicorn.__version__)" || echo "⚠️  Uvicorn não encontrado"
python -c "import playwright; print('✅ Playwright instalado')" || echo "⚠️  Playwright não encontrado"
python -c "import cryptography; print('✅ Cryptography instalada')" || echo "⚠️  Cryptography não encontrada"
python -c "import pydantic; print('✅ Pydantic:', pydantic.__version__)" || echo "⚠️  Pydantic não encontrado"

# Criar diretório de dados se não existir
mkdir -p /app/data
chmod 777 /app/data

# Inicializar banco de dados
echo "🗄️  Inicializando banco de dados..."
python -c "
from bot import SEFAZBot
import os
db_path = os.getenv('DB_PATH', '/app/data/sefaz_consulta.db')
bot = SEFAZBot(db_path=db_path)
print(f'✅ Banco de dados inicializado: {db_path}')
" || echo "⚠️  Erro ao inicializar banco"

echo "✅ Verificações completas!"
echo "🚀 Iniciando servidor na porta 8000..."
echo "📡 Servidor acessível em: http://0.0.0.0:8000"
echo "🏥 Health check: http://localhost:8000/api/estatisticas"
echo "📊 API Docs: http://localhost:8000/docs"
echo ""

# Iniciar uvicorn
exec python -m uvicorn api:app --host 0.0.0.0 --port 8000 --log-level info
