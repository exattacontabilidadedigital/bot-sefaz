# SEFAZ MessageBot Extension

Extensão Chrome para processamento automático de mensagens SEFAZ em modo visual.

## Instalação

1. Abra o Chrome e vá para `chrome://extensions`
2. Ative o "Modo do desenvolvedor" (canto superior direito)
3. Clique em "Carregar sem compactação"
4. Selecione a pasta `extensao-messagebot`

## Como Usar

1. Na interface web, clique no botão de **email** (📧) na linha da empresa
2. Uma nova aba do SEFAZ será aberta
3. O MessageBot fará login automaticamente
4. Navegará para a seção de mensagens
5. Processará cada mensagem pendente:
   - Abrirá a mensagem
   - Extrairá os dados
   - Salvará no servidor
   - Dará ciência
   - Voltará para a lista
6. Ao final, notificará o resultado (total processadas/erros)

## Funcionalidades

- ✅ Login automático
- ✅ Navegação automática para mensagens
- ✅ Processamento de múltiplas mensagens
- ✅ Extração de dados estruturados
- ✅ Envio para API backend
- ✅ Dar ciência automaticamente
- ✅ Modo visual (você vê tudo acontecendo)
- ✅ Feedback em tempo real

## Arquivos

- `manifest.json` - Configuração da extensão
- `background.js` - Service worker (gerencia abas)
- `content.js` - Script de automação (roda na página SEFAZ)
- `README.md` - Esta documentação

## Permissões

- `host_permissions`: Acesso ao domínio sefaz.ma.gov.br
- `externally_connectable`: Permite comunicação com localhost

## Desenvolvimento

A extensão se comunica com o frontend via `postMessage` e com a API backend via fetch.

**Fluxo de comunicação:**
```
Frontend → postMessage → Content Script → SEFAZ Portal
                ↓
         API Backend (salva dados)
```

## Troubleshooting

- **Não faz login**: Verifique se as credenciais estão corretas
- **Não encontra mensagens**: Verifique se há mensagens pendentes no SEFAZ
- **Erro ao salvar**: Verifique se a API está rodando em `localhost:8000`
