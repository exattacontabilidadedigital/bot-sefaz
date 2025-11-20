# Modo Visual - Guia de Instalação e Configuração

## 📋 Visão Geral

O **Modo Visual** permite que você veja o bot em ação diretamente no seu navegador enquanto o servidor executa as consultas no VPS. Isso oferece a transparência visual que você precisa para acompanhar o processo.

## 🔧 Configuração da Extensão Chrome

### 1. Obter ID da Extensão

1. Abra o Chrome e vá para `chrome://extensions/`
2. Ative o **Modo do desenvolvedor** no canto superior direito
3. Localize a extensão "SEFAZ-MA Auto Login"
4. Copie o **ID da extensão** (string longa como `abcdefghijklmnopqrstuvwxyz123456`)

### 2. Configurar ID no Frontend

1. Abra o arquivo: `frontend/js/modules/visualMode.js`
2. Localize a linha:
   ```javascript
   const EXTENSION_ID = 'your-extension-id-here';
   ```
3. Substitua `'your-extension-id-here'` pelo ID real da sua extensão
4. Salve o arquivo

### 3. Atualizar Manifest da Extensão

1. Abra o arquivo: `extensao-chrome/manifest.json`
2. Na seção `externally_connectable`, adicione o domínio do seu servidor:
   ```json
   "externally_connectable": {
     "matches": [
       "http://localhost:*/*",
       "https://localhost:*/*",
       "*://127.0.0.1:*/*",
       "*://SEU-DOMINIO.com/*"
     ]
   }
   ```
3. Salve o arquivo

### 4. Recarregar Extensão

1. Volte para `chrome://extensions/`
2. Clique no botão **Recarregar** da extensão SEFAZ-MA Auto Login
3. Aguarde alguns segundos

## 🚀 Como Usar o Modo Visual

### 1. Interface Web

1. Acesse o frontend da aplicação
2. Observe o toggle **"Modo Visual"** no header
3. Status deve mostrar:
   - ✅ **"Disponível"** (verde) - Extensão detectada
   - ❌ **"Extensão necessária"** (vermelho) - Extensão não detectada

### 2. Executar Consulta Visual

1. Vá para a aba **"Consultas"**
2. Preencha o formulário:
   - CPF (obrigatório)
   - Senha (obrigatório)
   - IE (opcional)
3. Marque a checkbox **"Modo Visual"**
4. Clique em **"Executar"**

### 3. Acompanhar Execução

1. Uma nova aba do Chrome será aberta automaticamente
2. Você verá o bot:
   - Fazendo login no SEFAZ
   - Navegando pelas páginas
   - Preenchendo formulários
   - Coletando dados
3. A aba pode ser fechada após a conclusão ou permanecerá aberta para análise

## 🔍 Solução de Problemas

### Extensão não detectada

**Sintomas:**
- Status "Extensão não detectada"
- Checkbox do modo visual desabilitada

**Soluções:**
1. Verifique se a extensão está instalada e ativa
2. Confirme que o ID da extensão está correto no código
3. Recarregue a extensão em `chrome://extensions/`
4. Atualize a página do frontend (F5)

### Erro de comunicação

**Sintomas:**
- Extensão detectada mas consulta falha
- Erro "Erro na execução visual"

**Soluções:**
1. Verifique se o domínio está em `externally_connectable`
2. Confirme que as permissões estão corretas no manifest
3. Verifique console do Chrome (F12) para erros
4. Recarregue a extensão

### Timeout na consulta

**Sintomas:**
- Consulta fica "executando" indefinidamente
- Aba abre mas não faz nada

**Soluções:**
1. Verifique se está acessando o site correto do SEFAZ
2. Confirme que os seletores CSS estão atualizados
3. Verifique se o SEFAZ não mudou a estrutura da página
4. Tente executar consulta manual primeiro

## 📊 Logs e Debug

### Console do Chrome

1. Abra F12 na aba da consulta visual
2. Vá para a aba **Console**
3. Procure por mensagens com prefixos:
   - 🔐 (login)
   - 📋 (consulta)
   - ✅ (sucesso)
   - ❌ (erro)

### Background Script

1. Vá para `chrome://extensions/`
2. Clique em **"Service Worker"** na extensão
3. Observe logs do background script

### Console da Aplicação

No terminal do servidor, observe:
```
🎯 Iniciando consulta visual: {...}
✅ Consulta executada: {...}
❌ Erro na consulta visual: {...}
```

## ⚙️ Configurações Avançadas

### Timeout de Consulta

Alterar tempo limite em `content.js`:
```javascript
const maxTentativas = 60; // 30 segundos (500ms * 60)
```

### URL Base do SEFAZ

Alterar URL no `background.js`:
```javascript
url: 'https://sefaz.ma.gov.br/portal/cidadao/consultas/pj'
```

### Debug Verbose

Ativar mais logs em `visualMode.js`:
```javascript
console.log('Modo visual inicializado. Extensão:', extensionAvailable ? 'Disponível' : 'Não detectada');
```

## 🔄 Atualizações Futuras

O sistema foi projetado para ser facilmente expandido:

1. **Múltiplos Estados**: Suporte para outros SEFAZ
2. **Sessões Persistentes**: Manter login entre consultas
3. **Execução em Background**: Consultas em abas invisíveis
4. **Captcha Automático**: Integração com serviços de resolução

## 📞 Suporte

Se encontrar problemas:

1. Verifique todos os passos de configuração
2. Consulte os logs em todas as camadas
3. Teste primeiro o modo headless tradicional
4. Documente o erro específico com screenshots

**Arquivos importantes:**
- `frontend/js/modules/visualMode.js` - Lógica do frontend
- `extensao-chrome/background.js` - Service worker da extensão
- `extensao-chrome/content.js` - Script de automação
- `src/api/main.py` - Backend API