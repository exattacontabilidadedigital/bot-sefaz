# 🚀 Extensão Chrome SEFAZ-MA Auto Login v1.2.0

Extensão robusta do Chrome que automatiza consultas no portal da SEFAZ-MA com comunicação aprimorada e modo visual otimizado.

## ✨ Principais Melhorias v1.2.0

- 🔥 **Service Worker robusto** com heartbeat automático
- 🛡️ **Comunicação ultra-confiável** com retry automático e timeout otimizado
- 🎯 **Detecção inteligente** de status da extensão
- 📊 **Popup de diagnóstico** com status em tempo real  
- 🔧 **Validação avançada** de origem e permissões
- ⚡ **Performance otimizada** com gerenciamento de estado
- 🧪 **Modo de teste integrado** para diagnóstico
   - Edge: `edge://extensions/`

2. **Ative o "Modo do desenvolvedor"** (canto superior direito)

3. **Clique em "Carregar sem compactação"**

4. **Selecione a pasta:** `extensao-chrome`

5. **Pronto!** A extensão está instalada ✅

## 🎯 Como usar

1. **No seu sistema web**, clique em "Imprimir Recibo DIEF"
2. **Modal abre** com CPF e Senha
3. **Clique em "Abrir SEFAZ com Auto-Login"**
4. **Nova aba abre** e campos são preenchidos automaticamente
5. **Login é feito automaticamente** (ou clique em Entrar se configurado para manual)

## 🔧 Configuração

### Clicar automaticamente no botão Entrar?

Edite `content.js` linha 42:

```javascript
// ✅ Auto-clicar ATIVADO (padrão)
botaoEntrar.click();

// ❌ Auto-clicar DESATIVADO (usuário clica manualmente)
// botaoEntrar.click();
```

### Adicionar seu domínio de produção

Edite `content.js` linha 5:

```javascript
// Descomentar e ajustar para seu domínio em produção
if (event.origin !== "https://seu-dominio.com.br") return;
```

## 📝 Notas

- Funciona apenas no portal: `sefaznet.sefaz.ma.gov.br`
- Extensão roda localmente no navegador do usuário
- Não envia dados para lugar nenhum (100% local)
- Código aberto e auditável

## 🚀 Distribuição

### Uso interno (atual)
- Instalar manualmente em cada computador
- Modo desenvolvedor sempre ativo

### Publicar na Chrome Web Store (futuro)
1. Criar conta de desenvolvedor ($5 taxa única)
2. Preparar ícones e screenshots
3. Enviar para revisão (pode levar dias)
4. Usuários instalam da loja oficial

## 🛠️ Manutenção

Se SEFAZ mudar o HTML da página, atualizar seletores em `content.js`:
- `input[name="identificacao"]` (campo CPF)
- `input[name="senha"]` (campo senha)
- `button[type="submit"]` (botão entrar)
