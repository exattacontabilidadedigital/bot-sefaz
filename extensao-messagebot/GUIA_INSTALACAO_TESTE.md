# Guia de Instalação e Teste - MessageBot Extension

## 1. Instalar a Extensão

### Chrome/Edge
1. Abra o navegador
2. Digite na barra de endereços: `chrome://extensions/` (ou `edge://extensions/`)
3. Ative o **"Modo do desenvolvedor"** (canto superior direito)
4. Clique em **"Carregar sem compactação"**
5. Selecione a pasta: `d:\CODIGOS\copilot\consulta-ie\extensao-messagebot\`
6. A extensão aparecerá na lista com o nome **"SEFAZ MessageBot"**

### Verificar Instalação
- O ícone da extensão deve aparecer na barra de ferramentas
- ID da extensão será algo como: `abcdefghijklmnopqrstuvwxyz123456`

## 2. Iniciar Backend

```powershell
cd d:\CODIGOS\copilot\consulta-ie
python -m uvicorn src.api.main:app --reload --port 8000
```

Verificar: `http://localhost:8000/docs`

## 3. Iniciar Frontend

```powershell
cd d:\CODIGOS\copilot\consulta-ie\frontend
# Se tiver Live Server instalado no VS Code:
# Clique direito em index.html → "Open with Live Server"
# Ou use qualquer servidor HTTP local na porta 5500
```

Verificar: `http://localhost:5500`

## 4. Teste Passo a Passo

### Teste 1: Verificar Extensão Carregada
1. Abra o Console do Dev Tools (F12) em qualquer página
2. Navegue para: `https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin`
3. No Console, você deve ver:
   ```
   SEFAZ MessageBot - Content script carregado
   URL: https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin
   ```

### Teste 2: Processar Mensagens de uma Empresa
1. Abra o frontend: `http://localhost:5500`
2. Vá para aba **"Empresas"**
3. Encontre uma empresa com credenciais cadastradas
4. Clique no ícone **📧** (mail-check) na linha da empresa
5. Uma nova aba do SEFAZ será aberta

### Teste 3: Acompanhar Execução
**Na aba do SEFAZ aberta:**
1. Abra Dev Tools (F12) → Console
2. Você verá os logs do MessageBot:

```javascript
[MessageBot] Iniciando fluxo
[MessageBot] Navegando para mensagens...
[MessageBot] Verificando aviso de ciencia...
[MessageBot] Tem aviso de ciencia: true
[MessageBot] Processando filtro: Aguardando Ciência
[MessageBot] Aplicando filtro: 4
[MessageBot] Mensagens disponiveis no filtro: 3
[MessageBot] Abrindo mensagem...
[MessageBot] Mensagem processada com sucesso
[MessageBot] Filtro Aguardando Ciência: 3 mensagens processadas
[MessageBot] Processando filtro: Não Lidas
[MessageBot] Aplicando filtro: 3
[MessageBot] Mensagens disponiveis no filtro: 7
[MessageBot] Total processadas: 10
```

**No frontend:**
- Verá uma notificação no final:
  ```
  MessageBot concluido! Total: 10, Processadas: 10, Erros: 0
  ```

### Teste 4: Verificar Dados Salvos

#### Via API
```bash
curl "http://localhost:8000/api/mensagens?inscricao_estadual=123456789"
```

#### Via Banco de Dados (SQLite)
```sql
SELECT 
    inscricao_estadual,
    cpf_socio,
    nome_empresa,
    assunto,
    competencia_dief,
    status_dief,
    chave_dief,
    protocolo_dief,
    link_recibo,
    data_envio
FROM mensagens
WHERE inscricao_estadual = '123456789'
ORDER BY data_envio DESC
LIMIT 5;
```

## 5. Troubleshooting

### Problema: Extensão não carrega
**Solução:**
1. Verifique se não há erros no `manifest.json`
2. Vá em `chrome://extensions/` e clique em "Recarregar"
3. Verifique o Console da extensão (clique em "Inspecionar visualizações - service worker")

### Problema: Login não acontece automaticamente
**Solução:**
1. Verifique no Console se o postMessage está sendo recebido
2. Verifique se os campos `cpf` e `senha` estão preenchidos
3. Verifique os seletores: `input[name="identificacao"]`, `input[name="senha"]`, `button[type="submit"]`

### Problema: Mensagens não são processadas
**Solução:**
1. Verifique se o login completou (procure por "Login completado! Iniciando MessageBot...")
2. Verifique se a navegação para mensagens funcionou
3. Verifique se os filtros estão sendo aplicados
4. Verifique se o select existe: `document.querySelector('select[name="listarMensagens"]')`

### Problema: Dados DIEF não são extraídos
**Solução:**
1. Verifique o HTML da mensagem no Console
2. Teste os regex patterns:
   ```javascript
   const texto = document.querySelector('td[width="100%"]').textContent;
   texto.match(/Período da DIEF:\s*(\d{6})/i);
   texto.match(/DIEF\s+(PROCESSADA|NÃO\s+PROCESSADA|REJEITADA)/i);
   texto.match(/Chave de segurança:\s*([\d-]+)/i);
   texto.match(/Protocolo:\s*(\d+)/i);
   ```

### Problema: Backend não recebe dados
**Solução:**
1. Verifique se o backend está rodando: `http://localhost:8000/docs`
2. Verifique o CORS: o backend deve permitir requisições do SEFAZ
3. Verifique o Console: procure por erros de `fetch`
4. Teste manualmente:
   ```javascript
   fetch('http://localhost:8000/api/mensagens', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ inscricao_estadual: 'teste' })
   }).then(r => r.json()).then(console.log);
   ```

## 6. Logs Detalhados

### Ativar Modo Debug
No arquivo `content.js`, todos os console.log já estão ativados. Para debug adicional:

```javascript
// Adicionar no início de handleMessageBotFluxo:
console.log('DEBUG - Dados recebidos:', JSON.stringify(dados, null, 2));

// Adicionar em extrairDadosMensagemCompleta:
console.log('DEBUG - Dados extraidos:', JSON.stringify(dados, null, 2));
```

### Arquivo de Log
Para salvar logs em arquivo (para análise posterior):

```javascript
// Adicionar no content.js:
const logs = [];
function log(msg) {
    const entry = `[${new Date().toISOString()}] ${msg}`;
    logs.push(entry);
    console.log(entry);
}

// Ao final do fluxo:
console.log('===== LOGS COMPLETOS =====');
console.log(logs.join('\n'));
```

## 7. Comparação com Python Bot

Para validar que a extensão está funcionando igual ao Python bot:

### Teste Paralelo
1. Execute o Python bot para uma empresa:
   ```bash
   python src/bot/message_bot.py --ie 123456789
   ```
2. Execute a extensão Chrome para a mesma empresa
3. Compare os resultados:
   - Quantidade de mensagens processadas
   - Dados extraídos (especialmente DIEF)
   - Mensagens que receberam ciência

### Validação de Dados
```sql
-- Comparar mensagens extraídas
SELECT 
    assunto,
    competencia_dief,
    status_dief,
    chave_dief,
    protocolo_dief
FROM mensagens
WHERE inscricao_estadual = '123456789'
AND data_envio > datetime('now', '-1 day')
ORDER BY data_envio DESC;
```

## 8. Métricas de Sucesso

✅ **Instalação bem-sucedida:**
- Extensão aparece em `chrome://extensions/`
- Console mostra "SEFAZ MessageBot - Content script carregado"

✅ **Fluxo completo:**
- Login automático funciona
- Navegação para mensagens funciona
- Filtros são aplicados corretamente
- Mensagens são processadas
- Dados são extraídos com todos os campos
- Ciência é dada
- Backend recebe os dados

✅ **Paridade com Python:**
- Mesma quantidade de mensagens processadas
- Mesmos dados extraídos (incluindo DIEF)
- Nenhum erro durante execução

## 9. Próximos Testes Recomendados

1. **Teste com múltiplas empresas**: Processar 5-10 empresas em sequência
2. **Teste com empresa sem mensagens**: Verificar se encerra corretamente
3. **Teste com mensagens sem DIEF**: Verificar se extrai dados básicos
4. **Teste de stress**: Empresa com 100+ mensagens
5. **Teste de recuperação**: Simular erro no meio e verificar se continua

## 10. Contato para Suporte

Se encontrar problemas durante os testes, verifique:
1. Logs do Console (Dev Tools - F12)
2. Logs do Backend (terminal onde uvicorn está rodando)
3. Estrutura HTML da página (pode ter mudado)
4. Seletores CSS (document.querySelector retorna null?)

---

**Data de criação:** 20/11/2025  
**Versão da extensão:** 1.0.0  
**Status:** ✅ Implementação completa - pronto para testes
