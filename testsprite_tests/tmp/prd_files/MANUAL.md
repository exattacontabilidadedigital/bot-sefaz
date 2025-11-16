# Manual da Aplicação — SEFAZ Bot (Consulta Conta Corrente Fiscal)

> Guia completo para instalação, configuração, uso da interface web, API, fila de processamento e utilitários CLI.

## Sumário
- [Visão Geral](#visão-geral)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração (.env)](#configuração-env)
- [Execução Rápida](#execução-rápida)
- [Interface Web](#interface-web)
- [API REST](#api-rest)
- [Fila de Processamento](#fila-de-processamento)
- [Utilitários CLI](#utilitários-cli)
- [Banco de Dados](#banco-de-dados)
- [Modo Headless](#modo-headless)
- [Notificações por E-mail](#notificações-por-e-mail)
- [Deploy](#deploy)
- [Segurança](#segurança)
- [Solução de Problemas](#solução-de-problemas)

## Visão Geral
Aplicação para automação de consultas de conta corrente fiscal no SEFAZ/MA. Oferece:
- Automação com comportamento humano (Playwright) e anti-detecção
- Interface web com dashboard e controle de execução
- API REST completa para integração
- Fila de processamento para execução em lote
- Persistência em SQLite e exportação/importação de empresas

## Requisitos
- `Python 3.8+`
- Playwright (Chromium)
- Dependências Python: `requirements.txt` e `requirements-api.txt`

## Instalação
```bash
# Clonar e entrar no diretório
git clone <repo-url>
cd consulta-ie

# Ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# Dependências
pip install -r requirements.txt
pip install -r requirements-api.txt

# Playwright
playwright install chromium
```

## Configuração (.env)
Copie o arquivo de exemplo e ajuste credenciais e parâmetros:
```bash
copy .env.example .env
```
Variáveis principais:
```env
USUARIO=seu_usuario
SENHA=sua_senha
DB_PATH=sefaz_consulta.db
SEFAZ_URL=https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin
TIMEOUT=30000
HEADLESS=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASS=sua_senha_app
SMTP_FROM=seu_email@gmail.com
SMTP_TLS=true
NOTIFY_TO=fiscal@exattacontabilidade.com.br
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=production
WORKERS=1
```

## Execução Rápida
```bash
# Windows
start.bat

# Manual
python api.py
```
Acesse a interface em `http://localhost:8000` e a documentação da API em `http://localhost:8000/docs`.

## Interface Web
- Dashboard com estatísticas: total de consultas, empresas ativas, dívidas, TVIs e somatório de débitos
- Painel de controle: nova consulta, barra de progresso, logs de execução
- Tabela de resultados: últimas consultas por empresa, ordenação por data, badges visuais e formatação monetária

## API REST
Base: `http://localhost:8000`

### Consultas
- `GET /api/consultas` — lista últimas consultas por empresa com filtros e paginação
- `GET /api/consultas/count` — total para paginação (aplica os mesmos filtros)
- `DELETE /api/consultas/{id}` — exclui uma consulta específica
- `GET /api/estatisticas` — agregados (ativas, dívidas, TVIs, valor total, percentual)

### Status e Execução
- `GET /api/status` — status atual da execução
- `POST /api/consulta` — inicia consulta em background
  Exemplo:
  ```json
  {
    "usuario": "12345678900",
    "senha": "sua_senha",
    "inscricao_estadual": "123456789",
    "headless": true
  }
  ```

### Empresas
- `POST /api/empresas` — criar empresa (senha obrigatória)
- `GET /api/empresas` — listar com filtros (`search`, `ativo`, `limit`, `offset`)
- `GET /api/empresas/count` — total filtrado
- `GET /api/empresas/{empresa_id}` — obter por ID
- `PUT /api/empresas/{empresa_id}` — atualizar (senha só se enviada)
- `DELETE /api/empresas/{empresa_id}` — desativa ou exclui (se sem consultas)

Payload de criação (exemplo):
```json
{
  "nome_empresa": "Empresa X",
  "cnpj": "00.000.000/0000-00",
  "inscricao_estadual": "123456789",
  "cpf_socio": "12345678900",
  "senha": "senha123",
  "observacoes": "Opcional",
  "ativo": true
}
```

### Fila de Processamento
- `POST /api/fila/adicionar` — adiciona empresas à fila
  ```json
  { "empresa_ids": [1, 2, 3], "prioridade": 1 }
  ```
- `GET /api/fila` — lista jobs
- `GET /api/fila/stats` — estatísticas (pendente, processando, concluído, erro)
- `POST /api/fila/iniciar` — inicia processamento
- `POST /api/fila/parar` — pausa após job atual
- `DELETE /api/fila/{job_id}` — remove job (se não estiver `running`)
- `POST /api/fila/cancelar/{job_id}` — marca como `failed` (cancelado)
- `GET /api/fila/status` — indica se está processando

### Mensagens SEFAZ
- `GET /api/mensagens` — lista, com filtros (`inscricao_estadual`, `cpf_socio`, `assunto`)
- `GET /api/mensagens/count` — total filtrado
- `GET /api/mensagens/{mensagem_id}` — obtém uma mensagem

## Utilitários CLI
- `python bot.py` — executa consulta interativa/local
- Exportação/Importação de empresas:
  - `python export_empresas.py` → gera `empresas_export.json`
  - `python import_empresas.py http://localhost:8000` → importa JSON via API
  - `python exportar_csv.py` → gera `empresas_export.csv`
  - `python importar_csv.py empresas.csv http://localhost:8000` → importa CSV via API

## Banco de Dados
SQLite (`DB_PATH=sefaz_consulta.db`). Tabelas principais:
- `consultas` — resultados da automação (inclui últimas flags como `tem_tvi`, `valor_debitos`, `tem_divida_pendente`, `omisso_declaracao`, `inscrito_restritivo`)
- `empresas` — cadastro e credenciais (armazenadas em texto plano)
- `queue_jobs` — fila: status (`pending`, `running`, `completed`, `failed`), prioridade, tentativas
- `mensagens_sefaz` — mensagens processadas do portal

## Modo Headless
Controle pelo `.env` (`HEADLESS=true|false`) ou por parâmetro na API (`POST /api/consulta`), e fixo como `true` nos jobs da fila. Veja também `TOGGLE_HEADLESS.md`.

## Notificações por E-mail
Opcional, via SMTP. Configure `SMTP_*` no `.env`. Se não configurado, as notificações ficam desativadas.

## Deploy
Diretrizes de implantação e Docker em `DEPLOY.md`. Variáveis `PORT`, `HOST`, `WORKERS` disponíveis no `.env.example`.

## Segurança
- Nunca versionar `.env` com credenciais reais
- Use senhas de aplicativo para SMTP
- Em ambientes de produção, restrinja logs sensíveis e proteja acesso ao banco

## Solução de Problemas
- Playwright: reinstale navegadores `playwright install chromium`
- Porta ocupada: ajuste `PORT` ou libere `8000`
- Credenciais inválidas: verifique CPF/IE e `SENHA`
- Fila não inicia: verifique `/api/fila/status` e acione `POST /api/fila/iniciar`

---
Para uma visão rápida, consulte `README.md`. Para detalhes específicos, veja `TOGGLE_HEADLESS.md`, `DECORATOR_RETRY_IMPLEMENTADO.md` e `REFATORAMENTO_PROGRESSO.md`.
