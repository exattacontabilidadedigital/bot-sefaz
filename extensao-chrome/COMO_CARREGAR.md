# 🔧 Como Carregar a Extensão Corrigida

## ✅ **PROBLEMA RESOLVIDO**
- ❌ **Antes**: "Não foi possível carregar content.js - não possui codificação UTF-8"  
- ✅ **Agora**: Arquivos em UTF-8 válido e funcionais

## 📋 **INSTRUÇÕES DE INSTALAÇÃO**

### **1. Abrir Chrome em Modo Desenvolvedor**
1. Abra o Google Chrome
2. Vá para `chrome://extensions/`
3. Ative o **"Modo do desenvolvedor"** (canto superior direito)

### **2. Carregar Extensão**
1. Clique em **"Carregar sem compactação"**
2. Navegue até a pasta: `D:\CODIGOS\copilot\consulta-ie\extensao-chrome`
3. Clique em **"Selecionar pasta"**

### **3. Verificar Instalação**
- ✅ **Sucesso**: Extensão "SEFAZ-MA Auto Login v1.1.0" aparece na lista
- ✅ **ID da Extensão**: Será gerado automaticamente
- ✅ **Status**: Habilitado e funcionando

## 🔍 **VERIFICAÇÃO DE FUNCIONAMENTO**

### **Console do Desenvolvedor:**
```javascript
// Se a extensão carregou corretamente, você verá:
🚀 SEFAZ Auto Login - Background script iniciado
```

### **Em Páginas do SEFAZ:**
```javascript
// Quando navegar para sefaznet.sefaz.ma.gov.br:
🔐 SEFAZ Auto Login - Extensão carregada
📍 URL da página: [URL da página]
🌐 Origin: https://sefaznet.sefaz.ma.gov.br
```

## 📁 **ARQUIVOS DA EXTENSÃO**

- ✅ `manifest.json` - Configuração válida (UTF-8)
- ✅ `background.js` - Service Worker funcionando (UTF-8)  
- ✅ `content.js` - Script de conteúdo funcionando (UTF-8)
- ✅ Outros arquivos auxiliares

## 🚨 **SE AINDA HOUVER PROBLEMAS**

1. **Remover Extensão Antiga:**
   - Desabilite e remova qualquer versão anterior
   - Limpe cache do Chrome: `chrome://settings/clearBrowserData`

2. **Reinstalar:**
   - Siga novamente as instruções acima
   - Use sempre a pasta atual com arquivos corrigidos

3. **Verificar Logs:**
   - F12 → Console para ver mensagens da extensão
   - `chrome://extensions/` → Detalhes → Inspecionar visualizações

## ✅ **RESULTADO ESPERADO**
- Extensão carrega sem erros
- Comunicação com aplicação web funcionando
- Automação do SEFAZ operacional
- Modo visual disponível

---
**Versão:** Commit e0386f8 (UTF-8 corrigido)  
**Data:** November 20, 2025  
**Status:** ✅ Funcionando