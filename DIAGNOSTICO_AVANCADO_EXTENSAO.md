# 🔧 DIAGNÓSTICO AVANÇADO DA EXTENSÃO

## 🎯 **PROBLEMA ATUAL**
- ✅ ID correto: `gimjjdmndkikigfgmnaaejbnahdhailc`
- ❌ Timeout de 5s na comunicação
- ❓ Extensão não responde ao ping

---

## 🛠️ **PASSO A PASSO COMPLETO**

### **1. RECARREGAR A EXTENSÃO (OBRIGATÓRIO)**
```
1. Abrir: chrome://extensions/
2. Localizar: "SEFAZ-MA Auto Login"
3. Clicar no ícone: 🔄 (recarregar)
4. Aguardar aparecer: "✓ Carregado"
```

### **2. VERIFICAR CONSOLE DA EXTENSÃO**
```
1. Em chrome://extensions/
2. "SEFAZ-MA Auto Login" → "Detalhes"
3. "Inspecionar visualizações" → "worker de serviço"
4. Verificar se aparece:
   🚀 SEFAZ Auto Login - Background script iniciado
   🆔 Extension ID: gimjjdmndkikigfgmnaaejbnahdhailc
   🔗 Externally connectable configurado
```

### **3. TESTE ESPECÍFICO NO CONSOLE DA APLICAÇÃO**

**Passo 3.1 - Teste Básico:**
```javascript
// Verificar se Chrome API está disponível
console.log('Chrome API:', typeof chrome !== 'undefined' ? '✅' : '❌');
console.log('Runtime:', typeof chrome?.runtime !== 'undefined' ? '✅' : '❌');
```

**Passo 3.2 - Teste de Comunicação Avançado:**
```javascript
// Executar teste detalhado
visualModeUI.testCommunication().then(result => {
    console.log('🎯 RESULTADO FINAL:', result ? '✅ SUCESSO' : '❌ FALHA');
});
```

**Passo 3.3 - Ping Manual Direto:**
```javascript
// Teste direto sem timeout
chrome.runtime.sendMessage('gimjjdmndkikigfgmnaaejbnahdhailc', {
    action: 'ping',
    test: true
}, (response) => {
    console.log('📨 Resposta:', response);
    console.log('❌ Erro:', chrome.runtime.lastError);
});
```

---

## 🔍 **VERIFICAÇÕES ESPECÍFICAS**

### **A. Verificar Manifest (Console da Extensão):**
```javascript
const manifest = chrome.runtime.getManifest();
console.log('Externally connectable:', manifest.externally_connectable);
```

**Deve mostrar:**
```javascript
{
  "matches": [
    "http://localhost:*/*",
    "https://localhost:*/*", 
    "http://127.0.0.1:*/*",
    "https://127.0.0.1:*/*",
    "http://localhost:8000/*",
    "https://localhost:8000/*"
  ]
}
```

### **B. Verificar Service Worker Ativo:**
```
1. chrome://extensions/
2. "SEFAZ-MA Auto Login" → Se tiver "Inspecionar visualizações" = ✅ Ativo
3. Se não tiver = ❌ Service Worker inativo → Recarregar extensão
```

### **C. Testar de Origem Diferente:**
```
1. Abrir nova aba: http://127.0.0.1:8000/frontend/
2. Executar mesmo teste
3. Comparar resultados
```

---

## 🚨 **SOLUÇÕES POR SINTOMA**

### **Sintoma 1: "Could not establish connection"**
```javascript
// Causa: Service worker inativo ou extensão não carregada
// Solução:
visualModeUI.reloadExtension();
// OU recarregar manualmente
```

### **Sintoma 2: "Timeout na comunicação"**
```javascript
// Causa: Mensagem não chega ou resposta não volta
// Solução: Verificar console da extensão
```

### **Sintoma 3: "Origin not allowed"**
```javascript
// Causa: externally_connectable restritivo
// Solução: Verificar manifest.json
```

### **Sintoma 4: Chrome API undefined**
```javascript
// Causa: Navegador não suporta ou contexto inseguro
// Solução: Usar HTTPS ou localhost
```

---

## ⚡ **TESTE FINAL COMPLETO**

Execute este script no console da aplicação:

```javascript
async function testeCompleto() {
    console.log('🧪 === TESTE COMPLETO DA EXTENSÃO ===');
    
    // 1. Verificar APIs
    console.log('1. Chrome API:', typeof chrome !== 'undefined' ? '✅' : '❌');
    console.log('2. Runtime API:', typeof chrome?.runtime !== 'undefined' ? '✅' : '❌');
    
    // 2. Verificar configuração
    console.log('3. ID configurado:', visualModeUI.getExtensionId());
    console.log('4. Origem atual:', window.location.origin);
    
    // 3. Teste de comunicação
    console.log('5. Testando comunicação...');
    const result = await visualModeUI.testCommunication();
    console.log('6. Resultado comunicação:', result ? '✅' : '❌');
    
    // 4. Diagnóstico completo
    if (!result) {
        console.log('🔍 Executando diagnóstico...');
        visualModeUI.diagnose();
    }
    
    console.log('🧪 === FIM DO TESTE ===');
    return result;
}

// Executar teste
testeCompleto();
```

---

## 📋 **CHECKLIST DE VERIFICAÇÃO**

- [ ] ✅ Extensão recarregada
- [ ] ✅ Service Worker ativo (console da extensão funcionando)
- [ ] ✅ Logs aparecem no console da extensão
- [ ] ✅ externally_connectable inclui localhost:8000
- [ ] ✅ Chrome API disponível no frontend
- [ ] ✅ ID correto configurado
- [ ] ✅ Origem permitida (localhost:8000)
- [ ] ✅ Teste de comunicação passa

---

## 🆘 **SE NADA FUNCIONAR**

### **Reinstalação Total:**
```
1. Desinstalar extensão completamente
2. Fechar e abrir Chrome
3. chrome://extensions/ → "Carregar sem compactação"
4. Selecionar pasta: extensao-chrome/
5. Anotar novo ID
6. visualModeUI.setExtensionId('NOVO_ID')
7. Executar teste completo novamente
```

**🎯 Execute o teste completo e me mostre TODOS os resultados!**