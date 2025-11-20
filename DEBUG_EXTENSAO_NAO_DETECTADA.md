# 🔍 DEBUG - EXTENSÃO CHROME NÃO DETECTADA

## 🚨 **Problema Reportado**
A extensão Chrome não está sendo identificada corretamente, mesmo já estando instalada.

---

## 🛠️ **PASSOS PARA DIAGNÓSTICO**

### **1. Abrir Console do Navegador**
```
1. Pressione F12 ou Ctrl+Shift+I
2. Vá na aba "Console"
3. Execute os comandos abaixo
```

### **2. Diagnóstico Básico**
```javascript
// Verificar se Chrome API está disponível
console.log('Chrome API:', typeof chrome !== 'undefined' ? 'Disponível' : 'Não disponível');

// Verificar ID atual configurado
visualModeUI.diagnose();
```

### **3. Verificar ID da Extensão**
```javascript
// Ver ID atual
console.log('ID atual:', visualModeUI.getExtensionId());

// Listar extensões instaladas (se possível)
visualModeUI.listExtensions();
```

### **4. Testar Comunicação Manual**
```javascript
// Testar ping direto (substitua YOUR_EXTENSION_ID pelo ID real)
chrome.runtime.sendMessage('YOUR_EXTENSION_ID', {action: 'ping'}, (response) => {
    console.log('Resposta:', response, 'Erro:', chrome.runtime.lastError);
});
```

### **5. Configurar ID Correto**
```javascript
// Configurar ID correto (pegar de chrome://extensions/)
visualModeUI.setExtensionId('SEU_ID_REAL_AQUI');
```

---

## 🔧 **SOLUÇÕES POSSÍVEIS**

### **Problema 1: ID Incorreto**
```javascript
// 1. Ir em chrome://extensions/
// 2. Ativar "Modo do desenvolvedor"
// 3. Copiar ID da extensão "SEFAZ-MA Auto Login"
// 4. Configurar o ID:
visualModeUI.setExtensionId('ID_COPIADO_AQUI');
```

### **Problema 2: Extensão Desabilitada**
```
1. Ir em chrome://extensions/
2. Verificar se "SEFAZ-MA Auto Login" está ATIVA
3. Se não estiver, clicar no toggle para ativar
```

### **Problema 3: Cache/localStorage**
```javascript
// Limpar configurações antigas
localStorage.removeItem('chrome_extension_id');
location.reload(); // Recarregar página
```

### **Problema 4: Extensão Não Instalada**
```
1. Ir para pasta: extensao-chrome/
2. Seguir instruções do INSTALACAO.md
3. Carregar extensão no Chrome
```

---

## 📋 **CHECKLIST COMPLETO**

### ✅ **Pré-requisitos**
- [ ] Chrome/Edge instalado
- [ ] Extensão "SEFAZ-MA Auto Login" instalada
- [ ] Extensão ATIVADA no painel de extensões
- [ ] Modo desenvolvedor ATIVO

### ✅ **Configuração**
- [ ] ID da extensão copiado corretamente
- [ ] ID configurado via `visualModeUI.setExtensionId()`
- [ ] Sem erros no console durante configuração

### ✅ **Comunicação**
- [ ] Chrome API disponível (`typeof chrome !== 'undefined'`)
- [ ] Ping manual funciona sem erros
- [ ] Extensão responde com `{pong: true}`

### ✅ **Interface**
- [ ] Status mostra "Disponível" (verde)
- [ ] Checkbox "Modo Visual" habilitado
- [ ] Botão de configuração (⚙️) presente

---

## 🆘 **SE NADA FUNCIONAR**

### **Reinstalação Completa:**
```bash
1. Desinstalar extensão atual
2. Ir em chrome://extensions/
3. "Carregar sem compactação"
4. Selecionar pasta: extensao-chrome/
5. Copiar novo ID
6. Limpar localStorage
7. Configurar novo ID
```

### **Verificação de Integridade:**
```javascript
// Verificar se arquivos da extensão existem
fetch('chrome-extension://SEU_ID/manifest.json')
  .then(response => console.log('Manifest existe:', response.ok))
  .catch(error => console.log('Erro:', error));
```

### **Log Detalhado:**
```javascript
// Ativar logs detalhados
localStorage.setItem('debug_visual_mode', 'true');
location.reload();
```

---

## 📞 **COMANDOS DE DIAGNÓSTICO RÁPIDO**

Execute todos de uma vez no console:

```javascript
// === DIAGNÓSTICO COMPLETO ===
console.log('=== DIAGNÓSTICO EXTENSÃO ===');
console.log('1. Chrome API:', typeof chrome !== 'undefined' ? '✅' : '❌');
console.log('2. Runtime API:', typeof chrome?.runtime !== 'undefined' ? '✅' : '❌');
console.log('3. ID atual:', visualModeUI.getExtensionId());
console.log('4. localStorage ID:', localStorage.getItem('chrome_extension_id'));

// Testar comunicação
visualModeUI.diagnose();

// Forçar verificação
visualModeUI.checkExtension().then(result => {
    console.log('5. Resultado verificação:', result ? '✅' : '❌');
});

console.log('=== FIM DIAGNÓSTICO ===');
```

---

**💡 Execute estes comandos e me mostre os resultados para identificar o problema específico!**