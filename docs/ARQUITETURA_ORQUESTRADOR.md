# 🎯 Arquitetura do Orquestrador Central

## Visão Geral

O `bot.py` funciona como **orquestrador central** que coordena todas as ações do sistema SEFAZ. Ele delega tarefas especializadas para módulos específicos, seguindo o princípio de **Separação de Responsabilidades**.

```
┌─────────────────────────────────────────────────────────────┐
│                         bot.py                              │
│                   (ORQUESTRADOR CENTRAL)                    │
│                                                             │
│  - Coordena fluxo principal                                │
│  - Gerencia login/logout                                   │
│  - Consultas de IE                                         │
│  - Delega tarefas especializadas                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ├──────────────────┬──────────────────┬──────────────────┐
                           │                  │                  │                  │
                           ▼                  ▼                  ▼                  ▼
            ┌──────────────────────┐  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
            │   bot_ciencia.py     │  │  bot_*.py        │  │  bot_*.py    │  │  bot_*.py    │
            │  (Bot Especializado) │  │  (Futuro)        │  │  (Futuro)    │  │  (Futuro)    │
            │                      │  │                  │  │              │  │              │
            │ - Processar mensagens│  │ - Outras tarefas │  │ - Outras     │  │ - Outras     │
            │ - Dar ciência        │  │   especializadas │  │   tarefas    │  │   tarefas    │
            │ - Extrair dados      │  │                  │  │              │  │              │
            └──────────────────────┘  └──────────────────┘  └──────────────┘  └──────────────┘
```

## 📦 Estrutura de Módulos

### 1. **bot.py** - Orquestrador Central
**Responsabilidades:**
- ✅ Gerenciar sessão do navegador
- ✅ Coordenar login/logout
- ✅ Realizar consultas de IE
- ✅ **DELEGAR** tarefas especializadas para bots específicos
- ✅ Orquestrar fluxo geral da aplicação

**Código Exemplo:**
```python
class SEFAZBot:
    def __init__(self, db_path: Optional[str] = None):
        # Inicializar bots especializados
        self.message_processor = SEFAZMessageProcessor(self.db_path)
        # Futuros bots especializados virão aqui
        
    async def processar_mensagens_com_ciencia_completa(self, page, ie, cpf):
        """
        ORQUESTRADOR: Delega para bot especializado
        """
        logger.info("🎯 Bot.py orquestrando processamento de mensagens...")
        
        # DELEGAR para bot especializado
        return await self.message_processor.processar_mensagens_aguardando_ciencia(
            page=page,
            cpf_socio=cpf,
            inscricao_estadual_contexto=ie
        )
```

### 2. **bot_ciencia.py** - Bot Especializado em Mensagens
**Responsabilidades:**
- ✅ Processar mensagens aguardando ciência
- ✅ Extrair dados completos das mensagens (incluindo DIEF)
- ✅ Salvar mensagens no banco de dados
- ✅ Dar ciência automaticamente
- ✅ Gerenciar fluxo completo de mensagens

**Métodos Principais:**
```python
class SEFAZMessageProcessor:
    async def processar_mensagens_aguardando_ciencia(self, page, cpf_socio, inscricao_estadual_contexto):
        """Processa TODAS as mensagens aguardando ciência"""
        
    async def _extract_complete_message_data(self, page, inscricao_estadual_contexto):
        """Extrai dados COMPLETOS da mensagem (tabela + HTML + DIEF)"""
        
    def _save_message_to_database(self, message_data):
        """Salva mensagem completa no banco"""
```

### 3. **Módulos de Suporte** (Usados por todos os bots)
- `bot_selectors.py` - Seletores CSS centralizados
- `bot_human_behavior.py` - Simulação de comportamento humano
- `bot_authenticator.py` - Login/Logout
- `bot_navigator.py` - Navegação entre páginas
- `bot_data_extractor.py` - Extração de dados gerais
- `bot_exceptions.py` - Hierarquia de exceções
- `bot_validators.py` - Validações
- `bot_retry.py` - Lógica de retry

## 🔄 Fluxo de Execução

### Exemplo: Processar Mensagens com Ciência

```python
# 1. BOT.PY - Orquestrador identifica necessidade
async def consultar_ie_com_tratamento_mensagens(self, cpf, senha, ie):
    # ... login e navegação ...
    
    # 2. Detecta mensagens pendentes
    if await self.detectar_mensagens_aguardando_ciencia(page):
        # 3. ORQUESTRA: Delega para bot especializado
        mensagens_processadas = await self.processar_mensagens_com_ciencia_completa(
            page=page,
            inscricao_estadual_contexto=ie,
            cpf_socio=cpf
        )
        
    # 4. Continua com consulta IE
    dados = await self.extrair_dados(page)
    return dados

# O bot.py NÃO implementa a lógica de mensagens diretamente!
# Ele apenas COORDENA e DELEGA
```

### Dentro do bot_ciencia.py (Especializado)

```python
# BOT_CIENCIA.PY - Implementação especializada
async def processar_mensagens_aguardando_ciencia(self, page, cpf_socio, ie_contexto):
    # 1. Filtrar mensagens
    await self._filter_messages_awaiting_acknowledgment(page)
    
    # 2. Buscar mensagens
    message_links = await self._get_pending_message_links(page)
    
    # 3. Processar cada mensagem
    for link in message_links:
        # 3.1. Abrir mensagem
        await HumanBehavior.human_click(page, link)
        
        # 3.2. Extrair dados completos (método interno especializado)
        dados = await self._extract_complete_message_data(page, ie_contexto)
        
        # 3.3. Salvar no banco
        message_id = self._save_message_to_database(dados)
        
        # 3.4. Dar ciência
        await self._give_acknowledgment(page)
        
        # 3.5. Voltar para lista
        await self._safe_return_to_list(page)
    
    return processed_count
```

## 🎨 Padrões de Design Aplicados

### 1. **Orchestrator Pattern (Orquestrador)**
- `bot.py` coordena o fluxo geral
- Não implementa lógicas especializadas
- Delega para especialistas

### 2. **Strategy Pattern (Estratégia)**
- Cada bot especializado implementa uma estratégia específica
- Fácil adicionar novos bots sem modificar o orquestrador

### 3. **Single Responsibility Principle (SRP)**
- Cada módulo tem UMA responsabilidade clara
- Fácil manter e testar

### 4. **Dependency Injection**
- Bots especializados são injetados no orquestrador
- Fácil testar e mockar

## 🚀 Como Adicionar Novos Bots Especializados

### Exemplo: Criar bot_relatorios.py

```python
# 1. Criar o bot especializado
# bot_relatorios.py
class SEFAZReportProcessor:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.selectors = SEFAZSelectors()
    
    async def gerar_relatorio_mensal(self, page, mes, ano):
        """Gera relatório mensal especializado"""
        # Implementação especializada aqui
        pass

# 2. Injetar no orquestrador
# bot.py
class SEFAZBot:
    def __init__(self, db_path):
        self.message_processor = SEFAZMessageProcessor(db_path)
        self.report_processor = SEFAZReportProcessor(db_path)  # NOVO BOT
        
    async def gerar_relatorio(self, page, mes, ano):
        """ORQUESTRADOR: Delega para bot de relatórios"""
        logger.info("🎯 Bot.py orquestrando geração de relatório...")
        return await self.report_processor.gerar_relatorio_mensal(page, mes, ano)
```

## 📊 Benefícios da Arquitetura

### ✅ Vantagens

1. **Separação Clara de Responsabilidades**
   - Cada bot cuida de uma área específica
   - Código mais organizado e legível

2. **Facilita Manutenção**
   - Mudanças em mensagens não afetam consultas IE
   - Cada módulo pode ser mantido independentemente

3. **Escalabilidade**
   - Fácil adicionar novos bots especializados
   - Não precisa modificar código existente

4. **Testabilidade**
   - Cada bot pode ser testado isoladamente
   - Mocks mais simples

5. **Reutilização**
   - Bots especializados podem ser usados em outros contextos
   - Módulos de suporte compartilhados

### 📈 Evolução Futura

```
Atual:
bot.py (orquestrador) → bot_ciencia.py (mensagens)

Futuro:
bot.py (orquestrador) → bot_ciencia.py (mensagens)
                      → bot_relatorios.py (relatórios)
                      → bot_certidoes.py (certidões)
                      → bot_notificacoes.py (notificações)
                      → bot_pagamentos.py (pagamentos)
```

## 🔍 Checklist para Novos Bots

Ao criar um novo bot especializado:

- [ ] Criar arquivo `bot_<nome>.py`
- [ ] Implementar classe `SEFAZ<Nome>Processor`
- [ ] Usar módulos de suporte (selectors, human_behavior, etc)
- [ ] Implementar métodos privados (`_metodo_interno`)
- [ ] Implementar método público principal
- [ ] Adicionar ao `bot.py` como propriedade
- [ ] Criar método orquestrador no `bot.py`
- [ ] Documentar no README
- [ ] Adicionar testes

## 📝 Exemplo Completo

```python
# ============================================
# bot.py - ORQUESTRADOR CENTRAL
# ============================================
class SEFAZBot:
    def __init__(self, db_path: str):
        # Injetar bots especializados
        self.message_processor = SEFAZMessageProcessor(db_path)
        
    async def processar_empresa_completo(self, cpf, senha, ie):
        """Fluxo completo: login → mensagens → consulta IE → logout"""
        async with BrowserManager() as browser_mgr:
            page = browser_mgr.page
            
            # 1. Login (responsabilidade do bot.py)
            await self.fazer_login(page, cpf, senha)
            
            # 2. ORQUESTRAR: Processar mensagens (delegar)
            if await self.detectar_mensagens(page):
                await self.message_processor.processar_mensagens_aguardando_ciencia(
                    page, cpf, ie
                )
            
            # 3. Consultar IE (responsabilidade do bot.py)
            dados = await self.extrair_dados(page)
            
            # 4. Logout (responsabilidade do bot.py)
            await self.fazer_logout(page)
            
            return dados

# ============================================
# bot_ciencia.py - BOT ESPECIALIZADO
# ============================================
class SEFAZMessageProcessor:
    async def processar_mensagens_aguardando_ciencia(self, page, cpf, ie):
        """Implementação completa e especializada"""
        # Toda a lógica de mensagens aqui
        # Não precisa conhecer o contexto maior do bot.py
        pass
```

## 🎓 Conclusão

Esta arquitetura de **orquestrador + bots especializados** torna o sistema:
- ✅ Mais modular
- ✅ Mais fácil de manter
- ✅ Mais escalável
- ✅ Mais testável
- ✅ Mais profissional

O `bot.py` permanece como **coordenador central**, mas não precisa conhecer todos os detalhes de implementação. Ele apenas sabe **QUANDO** chamar cada bot especializado e **COMO** passar os parâmetros necessários.
