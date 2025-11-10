# Toggle de Modo Visível/Headless do Browser

## 📋 Descrição

Foi adicionado um toggle no header do frontend que permite alternar entre dois modos de execução do browser Chromium:

### 🔹 Modo Headless (Invisível) - **PADRÃO**
- Toggle **ATIVADO** (azul)
- O browser roda em segundo plano, sem interface visual
- **Vantagens:**
  - Mais rápido
  - Consome menos recursos
  - Ideal para processamento em lote
  - Não interfere com outras janelas

### 🔹 Modo Visível
- Toggle **DESATIVADO** (cinza)
- O browser abre visível na tela
- **Vantagens:**
  - Útil para debugging
  - Permite ver o que o bot está fazendo
  - Facilita identificar erros visuais

## 🎯 Localização

O toggle está localizado no **header da aplicação**, ao lado do título "SEFAZ Bot":

```
┌─────────────────────────────────────────────────────┐
│  🛡️ SEFAZ Bot          👁️ Modo Visível [●──]      │
└─────────────────────────────────────────────────────┘
```

## ⚙️ Como Funciona

### Frontend
1. **Toggle HTML** (`frontend/index.html`):
   - Input checkbox com ID `headless-toggle`
   - Label visual com animação
   - Status text mostrando "Ativado" ou "Desativado"

2. **JavaScript** (`frontend/js/main.js`):
   - Função `setupHeadlessToggle()`
   - Salva configuração no `localStorage`
   - Mostra notificação toast ao trocar

3. **API** (`frontend/js/modules/api.js`):
   - Função `executarConsulta()` lê `localStorage`
   - Envia parâmetro `headless` para o backend

### Backend

1. **Modelo Pydantic** (`api.py`):
```python
class ConsultaRequest(BaseModel):
    usuario: Optional[str] = None
    senha: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    headless: bool = True  # Padrão: modo invisível
```

2. **Endpoint de Consulta**:
```python
@app.post("/api/consulta")
async def executar_consulta(request: ConsultaRequest, ...):
    background_tasks.add_task(
        run_consulta_background, 
        request.usuario, 
        request.senha, 
        request.inscricao_estadual,
        request.headless  # ← Passa para o bot
    )
```

3. **Bot** (`bot.py`):
```python
class SEFAZBot:
    def __init__(self, headless: bool = False, ...):
        self.headless = headless
        # Playwright usa esse parâmetro ao iniciar o browser
```

## 🔄 Fluxo Completo

```
┌────────────┐    ┌──────────────┐    ┌──────────┐    ┌──────────┐
│  Frontend  │ -> │ localStorage │ -> │   API    │ -> │   Bot    │
│   Toggle   │    │  headless=T  │    │ Request  │    │ Browser  │
└────────────┘    └──────────────┘    └──────────┘    └──────────┘
      │                   │                  │              │
      │ onChange          │                  │              │
      ├──────────────────>│ save('true')     │              │
      │                   │                  │              │
      │ Consulta Iniciada │                  │              │
      ├──────────────────────────────────────>│              │
      │                   │                  │              │
      │                   │<─────────────────┤ get value    │
      │                   │                  │              │
      │                   │                  ├─────────────>│
      │                   │                  │  headless=T  │
      │                   │                  │              │
      │                   │                  │      ┌───────┴──────┐
      │                   │                  │      │ Chromium     │
      │                   │                  │      │ (invisível)  │
      │                   │                  │      └──────────────┘
```

## 📝 Notas Importantes

1. **Persistência**: A configuração é salva no `localStorage` do navegador e persiste entre sessões

2. **Fila de Processamento**: Jobs na fila **sempre** rodam em modo headless (fixo) para otimizar performance

3. **Primeira execução**: Se o usuário nunca alterou o toggle, o padrão é **headless=true**

4. **Notificações**: Ao trocar o modo, uma notificação aparece confirmando a mudança

## 🧪 Testando

Execute o teste para verificar ambos os modos:

```bash
python test_headless_mode.py
```

O teste:
- ✅ Inicia bot em modo visível (browser deve aparecer)
- ✅ Inicia bot em modo headless (browser invisível)

## 🎨 Customização

### Alterar Comportamento Padrão

**Para iniciar VISÍVEL por padrão**:

Em `frontend/index.html`, linha do checkbox:
```html
<input type="checkbox" id="headless-toggle" class="sr-only peer">
<!-- Remove o 'checked' -->
```

Em `api.py`, modelo:
```python
headless: bool = False  # Muda para False
```

### Estilo Visual

O toggle usa:
- Tailwind CSS para layout
- `peer-checked:` para estados
- Ícone Lucide `eye` / `eye-off`
- Animações CSS customizadas

## 📊 Comportamento por Funcionalidade

| Funcionalidade | Modo | Motivo |
|----------------|------|--------|
| Consulta Manual | Configurável (toggle) | Usuário pode querer debugar |
| Fila Automática | Sempre Headless | Performance e estabilidade |
| Testes | Configurável | Facilita debugging |

## 🚀 Próximas Melhorias

Possíveis melhorias futuras:
- [ ] Adicionar opção de headless na fila também
- [ ] Salvar preferência por empresa
- [ ] Adicionar modo "Debug" com logs visuais
- [ ] Screenshot automático em caso de erro
