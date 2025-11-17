# 📁 Estrutura do Projeto - SEFAZ Bot

## 🎯 **Visão Geral da Arquitetura**

```
consulta-ie/
├── 📂 src/                          # Código-fonte principal (RECOMENDADO)
│   ├── 📂 bot/                      # Módulo principal do bot
│   │   ├── __init__.py
│   │   ├── sefaz_bot.py             # Orquestrador principal
│   │   ├── 📂 core/                 # Núcleo da aplicação
│   │   │   ├── __init__.py
│   │   │   ├── authenticator.py
│   │   │   ├── navigator.py
│   │   │   ├── data_extractor.py
│   │   │   └── message_processor.py
│   │   ├── 📂 utils/                # Utilitários
│   │   │   ├── __init__.py
│   │   │   ├── human_behavior.py
│   │   │   ├── selectors.py
│   │   │   ├── validators.py
│   │   │   ├── retry.py
│   │   │   └── constants.py
│   │   └── 📂 exceptions/           # Exceções customizadas
│   │       ├── __init__.py
│   │       ├── base.py
│   │       └── error_messages.py
│   │
│   ├── 📂 api/                      # API REST
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app
│   │   ├── 📂 routes/               # Endpoints
│   │   │   ├── __init__.py
│   │   │   ├── consultas.py
│   │   │   ├── empresas.py
│   │   │   ├── mensagens.py
│   │   │   └── fila.py
│   │   ├── 📂 models/               # Modelos Pydantic
│   │   │   ├── __init__.py
│   │   │   ├── consulta.py
│   │   │   ├── empresa.py
│   │   │   └── mensagem.py
│   │   └── 📂 services/             # Lógica de negócio
│   │       ├── __init__.py
│   │       ├── consulta_service.py
│   │       └── fila_service.py
│   │
│   ├── 📂 database/                 # Camada de persistência
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── 📂 repositories/         # Acesso a dados
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── consulta_repo.py
│   │   │   ├── empresa_repo.py
│   │   │   └── mensagem_repo.py
│   │   └── 📂 migrations/           # Scripts de migração
│   │       └── schema.sql
│   │
│   └── 📂 security/                 # Segurança
│       ├── __init__.py
│       ├── encryption.py
│       └── auth.py
│
├── 📂 frontend/                     # Interface web
│   ├── index.html
│   ├── 📂 css/
│   │   └── styles.css
│   └── 📂 js/
│       ├── main.js
│       └── 📂 modules/
│           ├── api.js
│           ├── consultas.js
│           ├── empresas.js
│           ├── fila.js
│           └── mensagens.js
│
├── 📂 scripts/                      # Scripts utilitários
│   ├── import_empresas.py
│   ├── export_empresas.py
│   ├── converter_senhas.py
│   ├── migrar_*.py
│   └── verificar_*.py
│
├── 📂 tests/                        # Testes automatizados
│   ├── __init__.py
│   ├── 📂 unit/
│   │   ├── test_authenticator.py
│   │   ├── test_extractor.py
│   │   └── test_validators.py
│   ├── 📂 integration/
│   │   ├── test_api.py
│   │   └── test_bot_flow.py
│   └── 📂 fixtures/
│       └── test_data.py
│
├── 📂 docs/                         # Documentação
│   ├── ARQUITETURA_ORQUESTRADOR.md
│   ├── MANUAL.md
│   ├── DEPLOY.md
│   └── API_REFERENCE.md
│
├── 📂 config/                       # Configurações
│   ├── __init__.py
│   ├── settings.py
│   └── logging_config.py
│
├── 📂 data/                         # Dados persistentes
│   ├── sefaz_consulta.db
│   ├── encryption_key.txt
│   └── logs/
│
├── .env.example                     # Exemplo de variáveis de ambiente
├── .gitignore
├── requirements.txt                 # Dependências
├── requirements-dev.txt             # Dependências de desenvolvimento
├── docker-compose.yml
├── Dockerfile
├── README.md
└── setup.py                         # Instalação como pacote

```

---

## 📊 **Estrutura Atual vs Recomendada**

### ❌ **Estrutura Atual (Problemática)**
```
consulta-ie/
├── bot.py (3251 linhas - MUITO GRANDE)
├── bot_authenticator.py
├── bot_navigator.py
├── bot_data_extractor.py
├── bot_ciencia.py
├── bot_validators.py
├── bot_selectors.py
├── bot_human_behavior.py
├── bot_retry.py
├── bot_constants.py
├── bot_exceptions.py
├── bot_error_messages.py
├── api.py (1794 linhas - MUITO GRANDE)
├── importar_csv.py
├── exportar_csv.py
├── converter_senhas.py
├── migrar_*.py
├── verificar_*.py
├── check_*.py
├── test_*.py
├── frontend/ (OK)
└── ... 40+ arquivos na raiz
```

**Problemas:**
1. ❌ Todos os arquivos na raiz (dificulta navegação)
2. ❌ Sem separação clara de responsabilidades
3. ❌ Scripts utilitários misturados com código core
4. ❌ Testes misturados com código de produção
5. ❌ Arquivos de documentação dispersos
6. ❌ Nomes com prefixo `bot_*` (redundante dentro de um módulo bot)

---

### ✅ **Estrutura Recomendada (Organizada)**

#### **1. Módulo `src/bot/` - Core do Bot**
```python
src/bot/
├── __init__.py                      # Exporta classes principais
├── sefaz_bot.py                     # SEFAZBot (orquestrador)
│
├── core/                            # Componentes principais
│   ├── __init__.py
│   ├── authenticator.py             # SEFAZAuthenticator
│   ├── navigator.py                 # SEFAZNavigator
│   ├── data_extractor.py            # DataExtractor, MessageExtractor
│   └── message_processor.py         # SEFAZMessageProcessor
│
├── utils/                           # Utilitários reutilizáveis
│   ├── __init__.py
│   ├── human_behavior.py            # HumanBehavior, AntiDetection
│   ├── selectors.py                 # SEFAZSelectors
│   ├── validators.py                # SEFAZValidator
│   ├── retry.py                     # Decoradores @retry
│   └── constants.py                 # Constantes globais
│
└── exceptions/                      # Sistema de exceções
    ├── __init__.py
    ├── base.py                      # Exceções base
    └── error_messages.py            # Mensagens de erro
```

**Benefícios:**
- ✅ Código modularizado e fácil de importar
- ✅ Separação clara: `core` (lógica) vs `utils` (ferramentas)
- ✅ Imports limpos: `from bot.core import SEFAZAuthenticator`

---

#### **2. Módulo `src/api/` - API REST**
```python
src/api/
├── __init__.py
├── main.py                          # FastAPI app principal
│
├── routes/                          # Endpoints organizados
│   ├── __init__.py
│   ├── consultas.py                 # POST /consultas, GET /consultas
│   ├── empresas.py                  # CRUD de empresas
│   ├── mensagens.py                 # GET /mensagens
│   └── fila.py                      # Gerenciamento da fila
│
├── models/                          # Modelos Pydantic (validação)
│   ├── __init__.py
│   ├── consulta.py                  # ConsultaRequest, ConsultaResponse
│   ├── empresa.py                   # EmpresaCreate, EmpresaUpdate
│   └── mensagem.py                  # MensagemResponse
│
└── services/                        # Lógica de negócio
    ├── __init__.py
    ├── consulta_service.py          # Orquestra bot + database
    └── fila_service.py              # Processa fila em background
```

**Benefícios:**
- ✅ Endpoints isolados e testáveis
- ✅ Validação centralizada nos models
- ✅ Lógica de negócio separada das rotas

---

#### **3. Módulo `src/database/` - Persistência**
```python
src/database/
├── __init__.py
├── connection.py                    # Gerenciamento de conexões SQLite
│
├── repositories/                    # Padrão Repository
│   ├── __init__.py
│   ├── base.py                      # BaseRepository (métodos comuns)
│   ├── consulta_repo.py             # ConsultaRepository
│   ├── empresa_repo.py              # EmpresaRepository
│   └── mensagem_repo.py             # MensagemRepository
│
└── migrations/
    ├── 001_initial_schema.sql
    ├── 002_add_mensagens.sql
    └── 003_add_queue_jobs.sql
```

**Benefícios:**
- ✅ Acesso a dados centralizado
- ✅ Fácil substituir SQLite por PostgreSQL/MySQL
- ✅ Migrations versionadas

---

#### **4. Diretório `scripts/` - Utilitários**
```python
scripts/
├── import_empresas.py               # Importar empresas de JSON/CSV
├── export_empresas.py               # Exportar para JSON/CSV
├── converter_senhas.py              # Migração de criptografia
├── migrar_link_recibo.py
├── migrar_queue_jobs.py
├── verificar_bancos.py
└── check_sefaz_login.py
```

**Benefícios:**
- ✅ Separado do código core
- ✅ Fácil de executar: `python scripts/import_empresas.py`

---

#### **5. Diretório `tests/` - Testes**
```python
tests/
├── __init__.py
├── conftest.py                      # Fixtures do pytest
│
├── unit/                            # Testes unitários
│   ├── test_authenticator.py
│   ├── test_validators.py
│   ├── test_data_extractor.py
│   └── test_retry.py
│
├── integration/                     # Testes de integração
│   ├── test_api_endpoints.py
│   ├── test_bot_flow.py
│   └── test_database.py
│
└── fixtures/
    ├── mock_pages.py
    └── test_data.json
```

**Benefícios:**
- ✅ Organização por tipo de teste
- ✅ Compatível com pytest
- ✅ Fixtures reutilizáveis

---

## 🔄 **Plano de Migração (Passo a Passo)**

### **Fase 1: Criar Estrutura de Diretórios** ⏱️ 5 min
```bash
mkdir -p src/bot/core src/bot/utils src/bot/exceptions
mkdir -p src/api/routes src/api/models src/api/services
mkdir -p src/database/repositories src/database/migrations
mkdir -p scripts tests/unit tests/integration tests/fixtures
mkdir -p docs config data/logs
```

### **Fase 2: Mover Arquivos Bot** ⏱️ 10 min
```bash
# Core
mv bot_authenticator.py src/bot/core/authenticator.py
mv bot_navigator.py src/bot/core/navigator.py
mv bot_data_extractor.py src/bot/core/data_extractor.py
mv bot_ciencia.py src/bot/core/message_processor.py

# Utils
mv bot_human_behavior.py src/bot/utils/human_behavior.py
mv bot_selectors.py src/bot/utils/selectors.py
mv bot_validators.py src/bot/utils/validators.py
mv bot_retry.py src/bot/utils/retry.py
mv bot_constants.py src/bot/utils/constants.py

# Exceptions
mv bot_exceptions.py src/bot/exceptions/base.py
mv bot_error_messages.py src/bot/exceptions/error_messages.py

# Main Bot
mv bot.py src/bot/sefaz_bot.py
```

### **Fase 3: Mover Arquivos API** ⏱️ 10 min
```bash
mv api.py src/api/main.py
# Depois dividir main.py em routes/, models/, services/
```

### **Fase 4: Mover Scripts** ⏱️ 5 min
```bash
mv import_empresas.py importar_csv.py export_empresas.py scripts/
mv converter_senhas.py migrar_*.py verificar_*.py check_*.py scripts/
```

### **Fase 5: Mover Testes** ⏱️ 5 min
```bash
mv test_*.py tests/integration/
```

### **Fase 6: Mover Documentação** ⏱️ 5 min
```bash
mv ARQUITETURA_ORQUESTRADOR.md MANUAL.md DEPLOY.md docs/
mv *.md docs/  # Mover todos os .md exceto README.md
```

### **Fase 7: Atualizar Imports** ⏱️ 20 min
```python
# ANTES
from bot_authenticator import SEFAZAuthenticator
from bot_validators import SEFAZValidator

# DEPOIS
from bot.core.authenticator import SEFAZAuthenticator
from bot.utils.validators import SEFAZValidator
```

### **Fase 8: Criar `__init__.py`** ⏱️ 10 min
```python
# src/bot/__init__.py
from .sefaz_bot import SEFAZBot
from .core.authenticator import SEFAZAuthenticator
from .core.navigator import SEFAZNavigator
from .core.data_extractor import DataExtractor
from .core.message_processor import SEFAZMessageProcessor

__all__ = ['SEFAZBot', 'SEFAZAuthenticator', 'SEFAZNavigator', 
           'DataExtractor', 'SEFAZMessageProcessor']
```

---

## 📦 **Estrutura Final Simplificada**

```
consulta-ie/
├── src/                  # Todo código-fonte
│   ├── bot/              # Módulo do bot
│   ├── api/              # Módulo da API
│   └── database/         # Módulo de dados
├── frontend/             # Interface web (mantém)
├── scripts/              # Utilitários
├── tests/                # Testes
├── docs/                 # Documentação
├── data/                 # Banco de dados
├── .env
├── requirements.txt
└── README.md
```

**Raiz limpa com apenas 10 itens!**

---

## 🎯 **Vantagens da Nova Estrutura**

1. ✅ **Organização Clara**: Cada coisa no seu lugar
2. ✅ **Escalabilidade**: Fácil adicionar novos módulos
3. ✅ **Manutenibilidade**: Código fácil de encontrar
4. ✅ **Testabilidade**: Testes organizados por tipo
5. ✅ **Profissionalismo**: Estrutura padrão de mercado
6. ✅ **Imports Limpos**: `from bot.core import X`
7. ✅ **Documentação Centralizada**: Tudo em `docs/`
8. ✅ **Deploy Simples**: Estrutura compatível com Docker/K8s

---

## 🚀 **Próximos Passos**

1. ✅ Decidir se quer aplicar a migração
2. ⏱️ Executar Fase 1-6 (estrutura de diretórios e movimentação)
3. 🔧 Executar Fase 7-8 (atualizar imports e criar __init__.py)
4. ✅ Testar a aplicação após migração
5. 📝 Atualizar documentação

---

## ⚠️ **Considerações Importantes**

- **Backup**: Fazer backup antes de mover arquivos
- **Git**: Usar `git mv` para preservar histórico
- **Compatibilidade**: Pode quebrar imports existentes (precisa atualizar)
- **Tempo Estimado**: ~2h para migração completa
- **Benefício**: Código profissional e escalável

---

**Quer que eu aplique esta estrutura no seu projeto?** 🚀
