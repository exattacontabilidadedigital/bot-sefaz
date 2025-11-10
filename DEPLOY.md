# 🚀 Guia de Deploy no Coolify

Este guia explica como fazer o deploy da aplicação **Bot SEFAZ** no Coolify.

---

## 📋 Pré-requisitos

- ✅ Coolify instalado e configurado no servidor
- ✅ Docker instalado no servidor
- ✅ Acesso SSH ao servidor
- ✅ Credenciais SEFAZ válidas
- ✅ Domínio configurado (opcional, mas recomendado)

---

## 🔧 Passo a Passo no Coolify

### 1️⃣ Criar Novo Recurso

1. Acesse o painel do **Coolify**
2. Clique em **"+ New"** ou **"Add Resource"**
3. Selecione **"Public Repository"**
4. Cole a URL do repositório:
   ```
   https://github.com/exattacontabilidadedigital/bot-sefaz.git
   ```
5. Selecione a branch: **`main`**
6. Clique em **"Continue"**

### 2️⃣ Configurar Build

1. **Build Pack**: Selecione **"Dockerfile"**
2. **Dockerfile Path**: `/Dockerfile` (padrão)
3. **Port**: `8000`

### 3️⃣ Configurar Variáveis de Ambiente

No Coolify, vá em **"Environment Variables"** e adicione:

#### Obrigatórias:
```env
HEADLESS=true
DB_PATH=/app/data/sefaz_consulta.db
```

#### Opcionais (Email):
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASS=sua_senha_app
SMTP_FROM=seu_email@gmail.com
SMTP_TLS=true
NOTIFY_TO=destinatario@email.com
```

#### Opcionais (Customização):
```env
SEFAZ_URL=https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do
TIMEOUT=30000
```

### 4️⃣ Configurar Volumes (Persistência)

Para manter os dados entre deploys, configure volumes:

1. Vá em **"Storages"** ou **"Volumes"**
2. Adicione um volume:
   - **Name**: `bot-sefaz-data`
   - **Mount Path**: `/app/data`
   - **Size**: `1GB` (ou conforme necessário)

### 5️⃣ Configurar Domínio (Opcional)

1. Vá em **"Domains"**
2. Adicione seu domínio: `bot-sefaz.seudominio.com`
3. Habilite **SSL/TLS** (Let's Encrypt)

### 6️⃣ Deploy

1. Revise todas as configurações
2. Clique em **"Deploy"**
3. Aguarde o build completar (pode levar alguns minutos)
4. Acompanhe os logs em **"Logs"**

---

## 🌐 Acessar a Aplicação

Após o deploy bem-sucedido:

- **Frontend**: `http://seu-servidor:8000` ou `https://seu-dominio.com`
- **API Docs**: `http://seu-servidor:8000/docs`
- **Health Check**: `http://seu-servidor:8000/api/estatisticas`

---

## 📊 Monitoramento

### Logs em Tempo Real

No Coolify:
1. Acesse o recurso
2. Clique em **"Logs"**
3. Veja os logs do container em tempo real

### Health Check

A aplicação possui health check automático:
- **Endpoint**: `/api/estatisticas`
- **Intervalo**: 30 segundos
- **Timeout**: 10 segundos
- **Retries**: 3

---

## 🔄 Atualizar a Aplicação

### Método 1: Webhook (Automático)

1. No Coolify, vá em **"Webhooks"**
2. Copie a URL do webhook
3. No GitHub, vá em **Settings** → **Webhooks**
4. Adicione o webhook do Coolify
5. Agora, a cada push na branch `main`, o Coolify fará redeploy automaticamente

### Método 2: Manual

1. Faça push das mudanças no GitHub:
   ```bash
   git add .
   git commit -m "Suas alterações"
   git push origin main
   ```
2. No Coolify, clique em **"Redeploy"**
3. Aguarde a nova build

---

## 🗄️ Backup do Banco de Dados

### Fazer Backup

No servidor, via SSH:
```bash
# Encontrar o container
docker ps | grep bot-sefaz

# Copiar banco de dados do container
docker cp <container_id>:/app/data/sefaz_consulta.db ./backup_$(date +%Y%m%d).db
```

### Restaurar Backup

```bash
# Copiar backup para o container
docker cp ./backup_20241109.db <container_id>:/app/data/sefaz_consulta.db

# Reiniciar container
docker restart <container_id>
```

---

## 🐛 Troubleshooting

### Problema: "Chrome not found" ou "Browser not installed"

**Solução**: O Dockerfile já instala o Chromium. Se o erro persistir:
1. Verifique se o build completou com sucesso
2. Reconstrua a imagem: Clique em **"Rebuild"** no Coolify

### Problema: "Database is locked"

**Solução**: 
1. Certifique-se de que o volume está montado corretamente
2. Reinicie o container
3. Se persistir, verifique permissões do volume

### Problema: Bot não inicia automaticamente ao adicionar empresas

**Solução**:
1. Verifique logs da API
2. Confirme que `processing_active` está sendo gerenciado corretamente
3. Teste manualmente o endpoint `/api/fila/iniciar`

### Problema: "Connection refused" ao acessar o frontend

**Solução**:
1. Verifique se o container está rodando: `docker ps`
2. Confirme que a porta 8000 está exposta
3. Verifique firewall do servidor
4. No Coolify, confirme o mapeamento de porta

### Problema: Memória alta / Container reiniciando

**Solução**:
1. No Coolify, aumente os recursos do container
2. Vá em **"Resources"** → Aumente RAM e CPU limits
3. Considere usar `HEADLESS=true` para economizar memória

---

## 📈 Otimizações de Produção

### 1. Configurar Recursos

No Coolify, defina limites:
- **CPU**: 1-2 cores
- **Memória**: 2-4 GB
- **Storage**: Conforme crescimento do banco

### 2. Configurar Workers

Para processar múltiplas empresas simultaneamente, edite `api.py`:
```python
# Aumentar número de workers do Uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 3. Backup Automático

Configure cron job no servidor:
```bash
# Editar crontab
crontab -e

# Adicionar backup diário às 2h da manhã
0 2 * * * docker cp $(docker ps -qf "name=bot-sefaz"):/app/data/sefaz_consulta.db /backups/sefaz_$(date +\%Y\%m\%d).db
```

### 4. Logs Externos

Configure log aggregation (opcional):
- Loki
- Grafana
- ELK Stack

---

## 🔒 Segurança

### Recomendações:

1. **Nunca commite** arquivos `.env` ou `encryption_key.txt`
2. **Use secrets** do Coolify para variáveis sensíveis
3. **Habilite SSL/TLS** para acesso HTTPS
4. **Restrinja acesso** à API se necessário (firewall, VPN)
5. **Rotacione credenciais** periodicamente

---

## 📞 Suporte

- **Issues**: https://github.com/exattacontabilidadedigital/bot-sefaz/issues
- **Email**: suporte@exattacontabilidade.com.br
- **Documentação Coolify**: https://coolify.io/docs

---

## ✅ Checklist de Deploy

Antes de fazer deploy, verifique:

- [ ] Repositório no GitHub atualizado
- [ ] Variáveis de ambiente configuradas no Coolify
- [ ] Volume de persistência configurado
- [ ] Porta 8000 exposta corretamente
- [ ] Health check funcionando
- [ ] Domínio configurado (se aplicável)
- [ ] SSL/TLS habilitado (se aplicável)
- [ ] Backup strategy definida
- [ ] Monitoramento configurado

---

**Bom deploy! 🚀**
