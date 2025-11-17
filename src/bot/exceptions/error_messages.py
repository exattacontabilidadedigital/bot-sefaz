"""
Módulo para mapear exceções do bot para mensagens amigáveis ao usuário
"""

def get_user_friendly_error_message(error_message: str, exception_type: str = None) -> str:
    """
    Converte mensagens de erro técnicas em mensagens amigáveis para o usuário
    
    Args:
        error_message: Mensagem de erro original
        exception_type: Tipo da exceção (opcional)
    
    Returns:
        Mensagem amigável para exibir ao usuário
    """
    
    error_lower = error_message.lower() if error_message else ""
    
    # Mapeamento de erros por etapa
    
    # ===== ERROS DE LOGIN =====
    if any(keyword in error_lower for keyword in ['login', 'senha', 'usuário', 'usuario', 'autenticação', 'autenticacao']):
        if 'senha' in error_lower or 'password' in error_lower:
            return "❌ Erro de Login: Senha incorreta ou inválida"
        if 'usuário' in error_lower or 'usuario' in error_lower or 'user' in error_lower:
            return "❌ Erro de Login: Usuário não encontrado ou inválido"
        if 'campo' in error_lower and 'não encontrado' in error_lower:
            return "❌ Erro de Login: Página de login não carregou corretamente"
        if 'botão' in error_lower or 'botao' in error_lower:
            return "❌ Erro de Login: Botão de login não encontrado"
        if 'timeout' in error_lower:
            return "❌ Erro de Login: Timeout - página demorou muito para responder"
        return "❌ Erro de Login: Falha ao autenticar no sistema"
    
    # ===== ERROS DE NAVEGAÇÃO =====
    if any(keyword in error_lower for keyword in ['navegação', 'navegacao', 'navigation', 'página', 'pagina']):
        if 'timeout' in error_lower:
            return "⏱️ Erro de Navegação: Timeout ao carregar página"
        if 'não encontr' in error_lower:
            return "🔍 Erro de Navegação: Página ou elemento não encontrado"
        return "🧭 Erro de Navegação: Falha ao acessar página do sistema"
    
    # ===== ERROS DE MENU =====
    if any(keyword in error_lower for keyword in ['menu', 'árvore', 'arvore', 'jstree']):
        if 'não encontr' in error_lower or 'not found' in error_lower:
            return "📋 Erro de Menu: Menu ou opção não encontrada no sistema"
        if 'timeout' in error_lower:
            return "📋 Erro de Menu: Timeout ao carregar menu do sistema"
        return "📋 Erro de Menu: Falha ao navegar no menu do sistema"
    
    # ===== ERROS DE EXTRAÇÃO DE DADOS =====
    if any(keyword in error_lower for keyword in ['extração', 'extracao', 'extraction', 'dados']):
        if 'timeout' in error_lower:
            return "📊 Erro de Extração: Timeout ao buscar dados"
        if 'não encontr' in error_lower:
            return "📊 Erro de Extração: Dados não encontrados na página"
        return "📊 Erro de Extração: Falha ao coletar informações do sistema"
    
    # ===== ERROS DE SESSÃO =====
    if any(keyword in error_lower for keyword in ['sessão', 'sessao', 'session', 'conflito']):
        if 'conflito' in error_lower or 'conflict' in error_lower:
            return "🔐 Erro de Sessão: Usuário já está logado em outra sessão"
        if 'expirou' in error_lower or 'expired' in error_lower:
            return "🔐 Erro de Sessão: Sessão expirada, faça login novamente"
        return "🔐 Erro de Sessão: Problema com a sessão do usuário"
    
    # ===== ERROS DE CAPTCHA =====
    if 'captcha' in error_lower:
        return "🤖 Erro de Captcha: Sistema detectou automação ou requer verificação"
    
    # ===== ERROS DE CPF/IE INVÁLIDOS =====
    if any(keyword in error_lower for keyword in ['cpf', 'inscri', 'ie', 'inválido', 'invalido']):
        if 'cpf' in error_lower:
            return "📝 Erro de Validação: CPF inválido ou não cadastrado"
        if 'inscri' in error_lower or 'ie' in error_lower:
            return "📝 Erro de Validação: Inscrição Estadual inválida ou não cadastrada"
        return "📝 Erro de Validação: Dados fornecidos são inválidos"
    
    # ===== ERROS DE DÍVIDAS/TVI =====
    if any(keyword in error_lower for keyword in ['dívida', 'divida', 'tvi', 'débito', 'debito']):
        if 'timeout' in error_lower:
            return "💰 Erro de Consulta: Timeout ao verificar dívidas/TVIs"
        return "💰 Erro de Consulta: Falha ao verificar dívidas e TVIs"
    
    # ===== ERROS DE BROWSER =====
    if any(keyword in error_lower for keyword in ['browser', 'navegador', 'chrome', 'playwright']):
        if 'não encontrado' in error_lower or 'not found' in error_lower:
            return "🌐 Erro de Navegador: Chrome não encontrado ou não instalado"
        if 'timeout' in error_lower:
            return "🌐 Erro de Navegador: Timeout ao iniciar navegador"
        if 'permissão' in error_lower or 'permission' in error_lower:
            return "🌐 Erro de Navegador: Sem permissão para acessar o navegador"
        return "🌐 Erro de Navegador: Falha ao iniciar ou conectar ao navegador"
    
    # ===== ERROS DE BANCO DE DADOS =====
    if any(keyword in error_lower for keyword in ['database', 'banco', 'sql', 'sqlite']):
        if 'duplicate' in error_lower or 'duplicado' in error_lower:
            return "💾 Erro de Banco: Registro já existe no sistema"
        if 'permissão' in error_lower or 'permission' in error_lower:
            return "💾 Erro de Banco: Sem permissão para acessar banco de dados"
        return "💾 Erro de Banco: Falha ao salvar ou consultar dados"
    
    # ===== ERROS DE TIMEOUT GENÉRICO =====
    if 'timeout' in error_lower:
        return "⏱️ Erro de Timeout: Operação demorou muito tempo"
    
    # ===== ERROS DE ELEMENTO NÃO ENCONTRADO =====
    if any(keyword in error_lower for keyword in ['elemento', 'element', 'não encontrado', 'not found']):
        return "🔍 Erro de Interface: Elemento não encontrado na página"
    
    # ===== ERRO GENÉRICO =====
    if not error_message or error_message.strip() == "":
        return "❌ Erro desconhecido na execução"
    
    # Se não conseguiu mapear, retorna uma versão mais amigável da mensagem original
    # Limita o tamanho para não poluir a interface
    if len(error_message) > 100:
        return f"❌ Erro: {error_message[:100]}..."
    
    return f"❌ Erro: {error_message}"


def get_error_category(error_message: str) -> str:
    """
    Retorna a categoria do erro para facilitar filtros e agrupamentos
    
    Args:
        error_message: Mensagem de erro original
    
    Returns:
        Categoria do erro (LOGIN, NAVEGACAO, EXTRACAO, etc.)
    """
    error_lower = error_message.lower() if error_message else ""
    
    if any(keyword in error_lower for keyword in ['login', 'senha', 'usuário', 'usuario']):
        return "LOGIN"
    if any(keyword in error_lower for keyword in ['navegação', 'navegacao', 'página', 'pagina']):
        return "NAVEGACAO"
    if any(keyword in error_lower for keyword in ['menu', 'árvore', 'arvore']):
        return "MENU"
    if any(keyword in error_lower for keyword in ['extração', 'extracao', 'dados']):
        return "EXTRACAO"
    if any(keyword in error_lower for keyword in ['sessão', 'sessao', 'conflito']):
        return "SESSAO"
    if 'captcha' in error_lower:
        return "CAPTCHA"
    if any(keyword in error_lower for keyword in ['cpf', 'inscri', 'ie', 'inválido', 'invalido']):
        return "VALIDACAO"
    if any(keyword in error_lower for keyword in ['dívida', 'divida', 'tvi', 'débito', 'debito']):
        return "CONSULTA"
    if any(keyword in error_lower for keyword in ['browser', 'navegador', 'chrome']):
        return "BROWSER"
    if any(keyword in error_lower for keyword in ['database', 'banco', 'sql']):
        return "BANCO"
    if 'timeout' in error_lower:
        return "TIMEOUT"
    
    return "GERAL"
