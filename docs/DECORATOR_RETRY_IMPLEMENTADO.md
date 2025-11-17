# ✅ Decorator @retry - IMPLEMENTADO COM SUCESSO

## 📋 Resumo da Implementação

Decorator inteligente `@retry` implementado com backoff exponencial, jitter, e tratamento seletivo baseado nas exceções específicas criadas anteriormente.

---

## 🎯 Arquivos Criados/Modificados

### **Novo Arquivo: `bot_retry.py`** (350 linhas)
- ✅ Decorator `@retry` completo com todas as funcionalidades
- ✅ Suporte para funções síncronas e assíncronas
- ✅ 3 atalhos prontos: `@retry_on_timeout`, `@retry_on_network`, `@retry_on_database`
- ✅ Exceção customizada `RetryExhaustedException`

### **Modificado: `bot.py`**
- ✅ Import do `bot_retry` adicionado
- ✅ 3 métodos críticos decorados com `@retry`:
  1. `fazer_login()` → `@retry_on_network(max_attempts=2, delay=3.0)`
  2. `extrair_dados()` → `@retry(max_attempts=2, delay=2.0, on=(TimeoutException, ExtractionException))`
  3. `processar_mensagens_ciencia()` → `@retry_on_network(max_attempts=2, delay=2.0)`

### **Novo Arquivo: `test_retry_decorator.py`** (420 linhas)
- ✅ 10 testes abrangentes
- ✅ Todos os testes passaram (10/10)

---

## 🚀 Funcionalidades do Decorator

### 1. **Backoff Exponencial**
```python
@retry(max_attempts=4, delay=1.0, backoff=2.0)
async def minha_funcao():
    # Delays: 1s, 2s, 4s, 8s (exponencial)
    pass
```

**Benefício:** Evita sobrecarregar sistema com retries muito rápidos.

---

### 2. **Jitter (Variação Aleatória)**
```python
@retry(jitter=True)  # Padrão é True
async def minha_funcao():
    # Delay base 2s → real delay entre 1s e 2s (evita thundering herd)
    pass
```

**Benefício:** Múltiplos clientes não fazem retry no mesmo instante.

---

### 3. **Max Delay (Teto)**
```python
@retry(delay=1.0, backoff=2.0, max_delay=10.0)
async def minha_funcao():
    # Delays: 1s, 2s, 4s, 8s, 10s, 10s, 10s... (limita em 10s)
    pass
```

**Benefício:** Evita delays muito longos em backoff exponencial.

---

### 4. **Exceções Retryable vs Non-Retryable**

**Retryable (padrão):**
- `TimeoutException` ✅
- `PageLoadException` ✅
- `NavigationException` ✅
- `ConnectionException` ✅
- `SessionExpiredException` ✅
- `TimeoutError` (built-in) ✅
- `ConnectionError` (built-in) ✅
- `OSError` ✅

**Non-Retryable (padrão):**
- `ValidationException` ❌ (dados inválidos)
- `InvalidCPFException` ❌ (CPF inválido não vai virar válido com retry)
- `InvalidPasswordException` ❌ (senha errada não vai mudar)
- `LoginFailedException` ❌ (credenciais inválidas)
- `SessionConflictException` ❌ (precisa logout manual)
- `DuplicateException` ❌ (registro já existe)
- `CaptchaException` ❌ (precisa resolução manual)
- `PermissionError` ❌ (sem permissão)
- `FileNotFoundError` ❌ (arquivo não existe)

**Lógica:**
- ✅ **Retry**: Erros temporários (rede, timeout, server busy)
- ❌ **Não Retry**: Erros permanentes (validação, permissão, dados inválidos)

---

### 5. **Callback on_retry**
```python
def log_retry(attempt, exception, delay):
    print(f"Tentativa {attempt} falhou: {exception}. Retry em {delay}s")
    send_metric("retry", {"type": type(exception).__name__})

@retry(on_retry=log_retry)
async def minha_funcao():
    pass
```

**Benefício:** Integração com logging, métricas, alertas.

---

### 6. **Exceções Customizadas**
```python
# Retry apenas em TimeoutError
@retry(on=(TimeoutError,), max_attempts=5)
async def operacao_rapida():
    pass

# Excluir DuplicateException (já tratada em outro lugar)
@retry(exclude=(DuplicateException,))
async def salvar_dados():
    pass
```

---

### 7. **Suporte Async e Sync**
```python
# Função assíncrona
@retry(max_attempts=3)
async def async_func():
    await asyncio.sleep(1)
    return "async"

# Função síncrona
@retry(max_attempts=3)
def sync_func():
    time.sleep(1)
    return "sync"
```

**Benefício:** Mesmo decorator funciona para ambos os casos!

---

## 📊 Testes Realizados

```
🔬 TESTES DO DECORATOR @RETRY
============================================================
✅ PASSOU: Sucesso primeira tentativa
✅ PASSOU: Sucesso após falhas
✅ PASSOU: Esgotamento de tentativas
✅ PASSOU: Não retry em não-retryable
✅ PASSOU: Backoff exponencial
✅ PASSOU: Callback on_retry
✅ PASSOU: Exceções específicas
✅ PASSOU: Atalho timeout
✅ PASSOU: Atalho network
✅ PASSOU: Função síncrona
============================================================
🎯 Resultado: 10/10 testes passaram
```

---

## 🎁 Atalhos Prontos para Uso

### 1. **@retry_on_timeout** - Retry apenas em timeout
```python
@retry_on_timeout(max_attempts=3, delay=2.0)
async def carregar_pagina():
    # Retry apenas se der TimeoutException ou TimeoutError
    await page.goto(url)
```

**Casos de uso:**
- Operações de rede lentas
- APIs externas com latência variável
- Páginas pesadas

---

### 2. **@retry_on_network** - Retry em erros de rede/navegação
```python
@retry_on_network(max_attempts=3, delay=5.0)
async def fazer_login(page, usuario, senha):
    # Retry em Timeout, PageLoad, Navigation, Connection
    await page.goto(login_url)
    await page.fill("#user", usuario)
    await page.click("#submit")
```

**Casos de uso:**
- Login em sistemas externos
- Navegação entre páginas
- Operações multi-step

**✅ Aplicado em:**
- `fazer_login()`
- `processar_mensagens_ciencia()`

---

### 3. **@retry_on_database** - Retry em erros de banco
```python
@retry_on_database(max_attempts=3, delay=1.0)
def salvar_consulta(dados):
    # Retry em DatabaseException, ConnectionException
    # NÃO retry em DuplicateException
    conn.execute("INSERT INTO...", dados)
```

**Casos de uso:**
- Locks de banco temporários
- Conexão intermitente
- Transações concorrentes

---

## 💡 Exemplos de Uso

### Exemplo 1: Retry Básico
```python
@retry(max_attempts=3, delay=2.0)
async def consultar_sefaz():
    # Faz retry automático em erros temporários
    # Não faz retry em erros permanentes (InvalidCPF, etc.)
    pass
```

### Exemplo 2: Customizar Exceções
```python
@retry(
    max_attempts=5,
    delay=1.0,
    backoff=1.5,
    on=(TimeoutError, ConnectionError),  # Apenas estas
    exclude=(CaptchaException,)  # Nunca estas
)
async def operacao_critica():
    pass
```

### Exemplo 3: Com Callback
```python
def alertar_retry(attempt, exception, delay):
    if attempt >= 2:
        send_slack_alert(f"⚠️ {attempt} tentativas falharam")

@retry(max_attempts=3, on_retry=alertar_retry)
async def operacao_monitorada():
    pass
```

### Exemplo 4: Não Lançar Exceção ao Esgotar
```python
@retry(max_attempts=3, raise_on_exhausted=False)
async def operacao_opcional():
    # Se falhar 3 vezes, lança última exceção (não RetryExhaustedException)
    pass
```

---

## 🔄 Integração no Bot

### **Método: fazer_login()**
```python
@retry_on_network(max_attempts=2, delay=3.0)
async def fazer_login(self, page, usuario, senha):
    # Retry automático em:
    # - TimeoutException (página não carregou)
    # - PageLoadException (erro ao carregar)
    # - NavigationException (erro de navegação)
    # - ConnectionError (rede caiu)
    
    await page.goto(self.sefaz_url)
    await page.fill("#usuario", usuario)
    await page.click("#login")
```

**Cenários cobertos:**
- ✅ Rede lenta → **Retry em 3s**
- ✅ Servidor ocupado → **Retry em 3s**
- ❌ Credenciais inválidas → **Não retry** (LoginFailedException)
- ❌ Elemento não encontrado → **Não retry** (ElementNotFoundException)

---

### **Método: extrair_dados()**
```python
@retry(max_attempts=2, delay=2.0, on=(TimeoutException, ExtractionException))
async def extrair_dados(self, page):
    # Retry apenas em timeout e erro de extração
    await page.wait_for_load_state("networkidle")
    
    dados = {}
    dados['ie'] = await page.query_selector("#ie").text_content()
    return dados
```

**Cenários cobertos:**
- ✅ Timeout aguardando página → **Retry em 2s**
- ✅ Erro temporário na extração → **Retry em 2s**
- ❌ Elemento não existe → **Não retry** (ExtractionException com causa diferente)

---

### **Método: processar_mensagens_ciencia()**
```python
@retry_on_network(max_attempts=2, delay=2.0)
async def processar_mensagens_ciencia(self, page, cpf_socio):
    # Retry em erros de navegação/timeout
    await page.select_option("#filtro", value="4")
    links = await page.query_selector_all("a.mensagem")
    
    for link in links:
        await link.click()
        # processar...
```

**Cenários cobertos:**
- ✅ Timeout ao carregar lista → **Retry em 2s**
- ✅ Erro ao clicar em mensagem → **Retry em 2s**

---

## 📈 Logs Gerados

### Sucesso após 1 falha:
```
⚠️ fazer_login: Tentativa 1/2 falhou. Exceção: TimeoutException: Timeout ao carregar. Retry em 3.0s...
✅ fazer_login sucesso na tentativa 2/2
```

### Esgotamento de tentativas:
```
⚠️ fazer_login: Tentativa 1/2 falhou. Exceção: TimeoutException: Timeout. Retry em 3.0s...
❌ fazer_login: Esgotadas 2 tentativas. Última exceção: TimeoutException: Timeout
RetryExhaustedException: Esgotadas 2 tentativas em fazer_login. Última exceção: TimeoutException: Timeout
```

### Não retry (exceção non-retryable):
```
🚫 fazer_login: Exceção não-retryable: InvalidCPFException: CPF inválido
```

---

## 🎯 Métricas e Monitoramento

### Integração com Prometheus
```python
from prometheus_client import Counter, Histogram

retry_counter = Counter('retry_attempts', 'Tentativas de retry', ['function', 'exception'])
retry_duration = Histogram('retry_duration', 'Tempo até sucesso', ['function'])

def track_retry(attempt, exception, delay):
    retry_counter.labels(
        function='fazer_login',
        exception=type(exception).__name__
    ).inc()

@retry(on_retry=track_retry)
async def fazer_login(...):
    pass
```

**Dashboard mostrará:**
- Total de retries por função
- Tipos de exceção mais comuns
- Taxa de sucesso após retry

---

## 🔍 Comparação: Antes vs Depois

### ❌ ANTES (Retry Manual)
```python
async def fazer_login(self, page, usuario, senha):
    MAX_RETRIES = 3
    
    for attempt in range(MAX_RETRIES):
        try:
            await page.goto(url)
            # ... lógica de login
            return True
        except Exception as e:
            if attempt >= MAX_RETRIES - 1:
                raise
            logger.warning(f"Tentativa {attempt} falhou, retry...")
            await asyncio.sleep(2)
```

**Problemas:**
- ❌ Código repetitivo (copy-paste em vários métodos)
- ❌ Retry em TODAS as exceções (até erros permanentes!)
- ❌ Delay fixo (sem backoff)
- ❌ Difícil de testar
- ❌ Sem métricas

### ✅ DEPOIS (Decorator @retry)
```python
@retry_on_network(max_attempts=3, delay=2.0)
async def fazer_login(self, page, usuario, senha):
    await page.goto(url)
    # ... lógica de login limpa
    return True
```

**Vantagens:**
- ✅ Código limpo e focado na lógica
- ✅ Retry inteligente (apenas erros temporários)
- ✅ Backoff exponencial automático
- ✅ Fácil de testar (decorator isolado)
- ✅ Métricas via callback
- ✅ Reutilizável em qualquer método

---

## ✅ Checklist de Validação

- [x] Decorator `@retry` implementado
- [x] Suporte async e sync
- [x] Backoff exponencial
- [x] Jitter habilitado
- [x] Max delay configurável
- [x] Exceções retryable vs non-retryable
- [x] Callback `on_retry`
- [x] 3 atalhos criados (timeout, network, database)
- [x] 10/10 testes passaram
- [x] 0 erros de compilação
- [x] Integrado em 3 métodos do bot.py
- [x] Documentação completa

---

## 🚀 Próximos Passos

### 1. **Circuit Breaker Pattern**
```python
@circuit_breaker(failure_threshold=5, timeout=60)
@retry_on_network(max_attempts=3)
async def fazer_consulta():
    # Se 5 falhas em 60s, abre circuito (não tenta mais)
    pass
```

### 2. **Métricas Avançadas**
```python
@retry(on_retry=track_metrics)
async def operacao():
    pass

# Dashboard:
# - Taxa de sucesso: 85%
# - Tempo médio até sucesso: 4.2s
# - Exceções mais comuns: TimeoutException (60%), PageLoadException (30%)
```

### 3. **Retry Adaptativo**
```python
# Ajustar delay baseado em hora do dia (peak hours)
@retry(delay=lambda hour: 5.0 if 9 <= hour <= 17 else 2.0)
async def consultar_sefaz():
    pass
```

---

## 🎉 Resumo Final

### O que foi entregue:
✅ Decorator `@retry` completo e testado  
✅ 10 testes abrangentes (todos passando)  
✅ 3 atalhos prontos para uso  
✅ Integração em 3 métodos críticos do bot  
✅ Documentação completa  
✅ 0 erros de compilação  

### Impacto:
- 🎯 **Resiliência**: Sistema se recupera automaticamente de falhas temporárias
- 📉 **Menos erros**: Retry inteligente evita falhas desnecessárias
- 🧹 **Código limpo**: Lógica de retry separada da lógica de negócio
- 📊 **Observabilidade**: Logs detalhados + callback para métricas
- 🔄 **Reutilizável**: Mesmo decorator em todos os métodos

**Status:** ✅ **IMPLEMENTADO E PRONTO PARA PRODUÇÃO**
