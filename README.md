# SEFAZ Bot - Consulta Conta Corrente Fiscal

Bot automatizado para consulta de conta corrente fiscal no sistema SEFAZ do Maranhão, com interface web moderna.

## 🚀 Funcionalidades

- **Automação Completa**: Login automático, navegação por menus complexos e extração de dados
- **Interface Web Moderna**: Dashboard com Tailwind CSS e componentes estilizados
- **Anti-Detecção**: Comportamento humano simulado com delays aleatórios e movimento de mouse
- **Extração Avançada**: Dados de TVIs, dívidas pendentes e status cadastral
- **Notificações Email**: Alertas automáticos para mensagens na caixa de entrada
- **Dashboard Analytics**: Estatísticas e visualização dos dados coletados
- **API RESTful**: Endpoints para integração e consulta programática

## 📋 Pré-requisitos

- Python 3.8+
- Playwright (instalado automaticamente)
- Navegador Chromium (instalado pelo Playwright)

## 🛠️ Instalação

1. **Clone o repositório**:
```bash
git clone <repo-url>
cd consulta-ie
```

2. **Crie um ambiente virtual**:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac
```

3. **Instale as dependências**:
```bash
pip install -r requirements.txt
pip install -r requirements-api.txt
```

4. **Instale o Playwright**:
```bash
playwright install chromium
```

5. **Configure as variáveis de ambiente**:
```bash
copy .env.example .env
```

Edite o arquivo `.env` com suas credenciais:
```env
# Credenciais SEFAZ
USUARIO=seu_usuario
SENHA=sua_senha

# Configurações
SEFAZ_URL=https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin
DB_PATH=sefaz_consulta.db
TIMEOUT=30000
HEADLESS=false

# Configurações SMTP (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASS=sua_senha_app
SMTP_FROM=seu_email@gmail.com
SMTP_TLS=true
NOTIFY_TO=fiscal@exattacontabilidade.com.br
```

## 🌐 Interface Web

### Início Rápido
Execute o arquivo batch para iniciar a interface web:
```bash
start.bat
```

Ou manualmente:
```bash
python api.py
```

Acesse: **http://localhost:8000**

### Funcionalidades da Interface

#### Dashboard Principal
- **Estatísticas em Tempo Real**: Total de consultas, empresas ativas, dívidas pendentes
- **Valores Monetários**: Soma total de dívidas formatada em Real brasileiro
- **Percentuais**: Análise de performance das consultas

#### Painel de Controle
- **Nova Consulta**: Formulário para executar consultas (credenciais opcionais)
- **Status em Tempo Real**: Barra de progresso e etapas da execução
- **Logs de Progresso**: Acompanhamento detalhado do processo

#### Tabela de Resultados
- **Dados Completos**: Nome da empresa, IE, status, TVIs, dívidas
- **Badges Coloridas**: Indicadores visuais para status e alertas
- **Formatação Monetária**: Valores em Real brasileiro
- **Ordenação**: Por data de consulta (mais recentes primeiro)

### API Endpoints

```
GET  /api/consultas        # Lista últimas consultas
GET  /api/status          # Status da consulta atual
POST /api/consulta        # Executa nova consulta
GET  /api/estatisticas    # Estatísticas gerais
```

## 🤖 Uso via Linha de Comando

```bash
python bot.py
```
```bash
python bot.py
```

## Banco de Dados

O bot cria automaticamente um banco SQLite com a seguinte estrutura:

- `id`: ID único da consulta
- `nome_empresa`: Nome da empresa
- `cnpj`: CNPJ da empresa
- `inscricao_estadual`: Inscrição Estadual
- `cpf_socio`: CPF do sócio
- `chave_acesso`: Chave de acesso
- `status_ie`: Status da IE
- `tem_tvi`: Possui TVI
- `valor_debitos`: Valor dos débitos
- `data_consulta`: Data e hora da consulta

## Segurança

- Nunca commite o arquivo `.env` com suas credenciais
- Use o arquivo `.env.example` como template
- As credenciais são carregadas apenas do ambiente local