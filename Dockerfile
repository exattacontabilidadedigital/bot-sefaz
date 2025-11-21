# Dockerfile para Bot SEFAZ - Otimizado para Coolify
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Copiar e dar permissão ao script de start
RUN chmod +x start.sh

# Criar diretórios necessários
RUN mkdir -p /app/data && \
    chmod 777 /app/data

# Expor porta da API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/estatisticas', timeout=5)" || exit 1

# Comando para iniciar a aplicação
CMD ["./start.sh"]
