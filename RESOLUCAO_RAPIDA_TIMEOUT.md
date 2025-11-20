# 🚨 RESOLUÇÃO RÁPIDA - EXTENSÃO NÃO RESPONDE

## 📊 **STATUS ATUAL DOS LOGS:**
- ✅ Retry logic funcionando (3 tentativas)
- ❌ Todas as tentativas resultam em timeout (10s cada)
- ❌ Extensão não responde ao ping
- ⚠️ ID configurado: `gimjjdmndkikigfgmnaaejbnahdhailc`

---

## ⚡ **DIAGNÓSTICO AUTOMÁTICO**

Execute no console do navegador:

```javascript
// === DIAGNÓSTICO COMPLETO ===
async function diagnosticoCompleto() {
    console.log('🔍 === DIAGNÓSTICO AUTOMÁTICO ===');
    
    // 1. Verificar status detalhado
    const status = await visualModeUI.checkStatus();
    console.log('📊 Status:', status);
    
    // 2. Obter orientação específica
    const guide = await visualModeUI.troubleshoot();
    console.log('🛠️ Ação necessária:', guide);
    
    return guide;
}

diagnosticoCompleto();
```

---

## 🎯 **SOLUÇÕES POR CENÁRIO**

### **CENÁRIO 1: Extensão NÃO Instalada**
```
Sintoma: "Extensão não encontrada no sistema"
Ação: Instalar extensão

PASSOS:
1. chrome://extensions/
2. "Modo do desenvolvedor" ✅ ATIVO
3. "Carregar sem compactação"
4. Selecionar pasta: extensao-chrome/
5. Anotar ID gerado
6. visualModeUI.setExtensionId('NOVO_ID')
```

### **CENÁRIO 2: Extensão DESABILITADA**
```
Sintoma: "Extensão encontrada mas está DESABILITADA"
Ação: Ativar extensão

PASSOS:
1. chrome://extensions/
2. Encontrar "SEFAZ-MA Auto Login"
3. Toggle deve estar AZUL (ativo)
4. Se estiver cinza, clicar para ativar
```

### **CENÁRIO 3: Service Worker INATIVO (Mais Provável)**
```
Sintoma: "Timeout na comunicação" mas extensão ativa
Ação: Recarregar extensão

PASSOS:
1. chrome://extensions/
2. "SEFAZ-MA Auto Login" → 🔄 (recarregar)
3. Aguardar 3-5 segundos
4. Testar: visualModeUI.checkExtension()
```

---

## 🔧 **COMANDOS ESPECÍFICOS**

### **Teste 1: Status Detalhado**
```javascript
visualModeUI.checkStatus().then(status => {
    console.log('📦 Instalada:', status.installed);
    console.log('✅ Ativa:', status.enabled);  
    console.log('📡 Comunicando:', status.communicating);
    console.log('ℹ️ Info:', status.info);
});
```

### **Teste 2: Resolução Automática**
```javascript
visualModeUI.troubleshoot().then(guide => {
    console.log('🎯 Ação:', guide.action);
    console.log('📝 Passos:', guide.steps);
});
```

### **Teste 3: Ping Direto**
```javascript
// Testar comunicação direta sem timeout
chrome.runtime.sendMessage('gimjjdmndkikigfgmnaaejbnahdhailc', 
  {action: 'ping'}, (response) => {
    console.log('📨 Resposta:', response);
    console.log('❌ Erro:', chrome.runtime.lastError);
  }
);
```

---

## 🚀 **RESOLUÇÃO MAIS PROVÁVEL**

Baseado nos logs, o problema é **service worker inativo**. 

### **SOLUÇÃO RÁPIDA:**
```
1. chrome://extensions/
2. Localizar: "SEFAZ-MA Auto Login"  
3. Clicar: 🔄 (ícone recarregar)
4. Aguardar: 3-5 segundos
5. Testar: visualModeUI.checkExtension()
```

### **VERIFICAÇÃO:**
```javascript
// Após recarregar extensão, aguarde e teste
setTimeout(async () => {
    const working = await visualModeUI.checkExtension();
    console.log('🎉 Funcionando:', working ? 'SIM' : 'NÃO');
}, 5000);
```

---

## ⚠️ **SE AINDA NÃO FUNCIONAR**

### **Reinstalação Completa:**
```
1. chrome://extensions/
2. "SEFAZ-MA Auto Login" → "Remover"
3. Confirmar remoção
4. "Carregar sem compactação"  
5. Selecionar: extensao-chrome/
6. Copiar NOVO ID
7. visualModeUI.setExtensionId('NOVO_ID')
8. Testar comunicação
```

### **Verificar Console da Extensão:**
```
1. chrome://extensions/
2. "SEFAZ-MA Auto Login" → "Detalhes"
3. "Inspecionar visualizações" → "worker de serviço"
4. Verificar se aparece:
   🚀 SEFAZ Auto Login - Background script iniciado
   🆔 Extension ID: gimjjdmndkikigfgmnaaejbnahdhailc
```

---

## 📋 **CHECKLIST DE VERIFICAÇÃO**

Execute este checklist completo:

```javascript
async function checklistCompleto() {
    const results = {};
    
    // 1. APIs disponíveis
    results.chromeAPI = typeof chrome !== 'undefined';
    results.runtimeAPI = typeof chrome?.runtime !== 'undefined';
    results.managementAPI = typeof chrome?.management !== 'undefined';
    
    // 2. ID configurado
    results.idConfigured = visualModeUI.getExtensionId() !== 'your-extension-id-here';
    results.currentId = visualModeUI.getExtensionId();
    
    // 3. Status da extensão
    const status = await visualModeUI.checkStatus();
    results.installed = status.installed;
    results.enabled = status.enabled;
    results.communicating = status.communicating;
    
    // 4. Recomendação
    const guide = await visualModeUI.troubleshoot();
    results.action = guide.action;
    results.steps = guide.steps;
    
    console.log('📋 CHECKLIST COMPLETO:', results);
    return results;
}

checklistCompleto();
```

---

**🎯 Execute o diagnóstico automático e siga a orientação específica retornada!**

**📞 Comando rápido:**
```javascript
visualModeUI.troubleshoot();
```