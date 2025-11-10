# Dockerfile para Bot SEFAZ - Otimizado para Coolify
FROM python:3.11-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Instalar dependências do sistema necessárias para Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-unifont \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libnss3-dev \
    libgdk-pixbuf2.0-0 \
    libxss1 \
    libegl1 \
    libgles2 \
    gstreamer1.0-libav \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    libenchant-2-2 \
    libepoxy0 \
    libevdev2 \
    libgles2-mesa \
    libgudev-1.0-0 \
    libharfbuzz-icu0 \
    libhyphen0 \
    libmanette-0.2-0 \
    libopus0 \
    libsecret-1-0 \
    libvpx9 \
    libwebpdemux2 \
    libwoff1 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright e navegadores
RUN playwright install chromium

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p /app/data && \
    chmod 777 /app/data

# Expor porta da API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/estatisticas', timeout=5)" || exit 1

# Comando para iniciar a aplicação
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
