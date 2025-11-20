"""
Constantes e seletores CSS para o bot SEFAZ
"""

# URLs
URL_SEFAZ_LOGIN = 'https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin'

# Timeouts (em milissegundos) - Aumentados para lidar com instabilidade do SEFAZ
TIMEOUT_DEFAULT = 60000      # 1 minuto (era 30s)
TIMEOUT_NAVIGATION = 120000  # 2 minutos (era 30s) 
TIMEOUT_ELEMENT = 30000      # 30 segundos (era 10s)
TIMEOUT_NETWORK_IDLE = 60000 # 1 minuto (era 30s)

# Delays (em milissegundos)
DELAY_MIN_HUMAN = 50
DELAY_MAX_HUMAN = 150
DELAY_BETWEEN_FIELDS = 500
DELAY_AFTER_CLICK = 1000
DELAY_PAGE_LOAD = 2000

# Retry - Aumentado para maior robustez
MAX_RETRIES = 3              # Aumentado de 2 para 3
RETRY_DELAY_SECONDS = 10     # Aumentado de 5 para 10

# Seletores CSS - Login
SELECTOR_LOGIN_USER = "input[name='CPF']"
SELECTOR_LOGIN_PASSWORD = "input[name='PASSWORD']"
SELECTOR_LOGIN_BUTTON = "input[name='enviar']"
SELECTOR_LOGIN_IDENTIFICACAO = "input[name='identificacao']"
SELECTOR_LOGIN_SENHA = "input[name='senha']"
SELECTOR_LOGIN_SUBMIT = "button[type='submit']"

# Seletores CSS - Menu
SELECTOR_MENU_SISTEMAS = "a.dropdown-toggle:has(i.glyphicon-cog)"
SELECTOR_MENU_SISTEMAS_ALT = "a:has-text('Sistemas')"
SELECTOR_MENU_ICON_COG = "i.glyphicon-cog"

# Seletores CSS - Navegação
SELECTOR_TODAS_AREAS = "a:has-text('Todas as Áreas de Negócio')"
SELECTOR_CONTA_FISCAL = "a:has-text('Conta Fiscal')"
SELECTOR_CONSULTAR_CC = "a:has-text('Consultar Conta-Corrente Fiscal')"

# Seletores CSS - Inscrição Estadual
SELECTOR_IE_INPUT = "input[name='inscricaoEstadual']"
SELECTOR_IE_CONFIRMAR = "a[href*='recuperarDadosInscricaoEstadual']"
SELECTOR_IE_CONFIRMAR_IMG = "img[src*='ic_confirmar.gif']"
SELECTOR_RAZAO_SOCIAL = "input[name='razaoSocial']"

# Seletores CSS - Botões
SELECTOR_BTN_CONTINUAR = "button:has-text('Continuar')"
SELECTOR_BTN_CONTINUAR_ALT = "button[onclick*='validateForm']"
SELECTOR_BTN_CONTINUAR_PRIMARY = "button.btn-primary:has-text('Continuar')"
SELECTOR_BTN_TVIS = "button:has-text('TVIs')"
SELECTOR_BTN_DIVIDAS = "button:has-text('Dívidas Pendentes')"
SELECTOR_BTN_VOLTAR = "button:has-text('Voltar')"

# Seletores CSS - Caixa de Entrada / Mensagens
SELECTOR_FILTRO_MENSAGENS = "select[name='visualizarMensagens']"
SELECTOR_OPCAO_AGUARDANDO_CIENCIA = "option[value='4']"  # Aguardando Ciência
SELECTOR_LINK_ABRIR_MENSAGEM = "a[href*='abrirMensagemDomicilio.do']"
SELECTOR_BOTAO_DAR_CIENCIA = "button:has-text('Dar Ciência')"
SELECTOR_BOTAO_VOLTAR_MENSAGEM = "button:has-text('Voltar')"
SELECTOR_MSG_ENVIADA_POR = "th:has-text('Enviada por:') + td"
SELECTOR_MSG_DATA_ENVIO = "th:has-text('Data do Envio:') + td"
SELECTOR_MSG_ASSUNTO = "th:has-text('Assunto:') + td"
SELECTOR_MSG_CLASSIFICACAO = "th:has-text('Classificação:') + td"
SELECTOR_MSG_TRIBUTO = "th:has-text('Tributo:') + td"
SELECTOR_MSG_TIPO = "th:has-text('Tipo da Mensagem:') + td"
SELECTOR_MSG_IE = "th:has-text('Inscrição Estadual:') + td"
SELECTOR_MSG_NUM_DOC = "th:has-text('Número do Documento:') + td"
SELECTOR_MSG_VENCIMENTO = "th:has-text('Vencimento:') + td"
SELECTOR_MSG_CONTEUDO = "table.table-tripped tbody tr td"

# Seletores CSS - Logout
SELECTOR_LOGOUT = "a[href*='logoff.do?method=efetuarLogoff']"

# Seletores CSS - Extração de Dados
SELECTOR_IE_DATA = [
    "td.texto_negrito:has-text('Inscrição Estadual') + td span.texto",
    "td:has-text('Inscrição Estadual') + td span",
    "td:has-text('Inscrição Estadual') + td"
]

SELECTOR_RAZAO_DATA = [
    "td.texto_negrito:has-text('Razão Social') + td span.texto",
    "td:has-text('Razão Social') + td span",
    "td:has-text('Razão Social') + td"
]

SELECTOR_SITUACAO_DATA = [
    "td.texto_negrito:has-text('Situação Cadastral') + td span.texto",
    "td:has-text('Situação Cadastral') + td span",
    "td:has-text('Situação Cadastral') + td"
]

# Checkboxes
SELECTOR_CHECKBOX_DIVIDA = "input[name='indicadorInadimplente']:checked"
SELECTOR_CHECKBOX_OMISSO = "input[name='indicadorOmisso']:checked"
SELECTOR_CHECKBOX_RESTRITIVO = "input[name='indicadorInscritoRestritivo']:checked"

# Mensagens
MSG_SESSION_CONFLICT = "já está conectado"
MSG_SESSION_CONFLICT_ALT = "outra sessão"
MSG_NO_DATA = "Nenhum resultado foi encontrado"
MSG_NO_RECORDS = "Nenhum registro encontrado"

# Regex para validação
REGEX_CPF = r'^\d{11}$'
REGEX_IE = r'^\d{1,9}$'

# Status
STATUS_IE_ATIVO = "ATIVO"
STATUS_IE_SUSPENSO = "SUSPENSO"
STATUS_IE_BAIXADO = "BAIXADO"

# Arquivos de Debug
DEBUG_FILE_POST_LOGIN = "debug_post_login.html"
DEBUG_FILE_POST_LOGIN_PNG = "debug_post_login.png"
DEBUG_FILE_IE_ANTES_PNG = "debug_antes_ie.png"
DEBUG_FILE_IE_ANTES_HTML = "debug_antes_ie.html"
DEBUG_FILE_IE_VAZIO_PNG = "debug_ie_campo_vazio.png"
DEBUG_FILE_EXTRACAO_FALHA_PNG = "debug_extracao_falha.png"
DEBUG_FILE_EXTRACAO_FALHA_HTML = "debug_extracao_falha.html"
