"""
Seletores CSS e XPath centralizados para o bot SEFAZ.

Este módulo centraliza todos os seletores utilizados na automação,
facilitando manutenção quando a interface do sistema muda.
"""


class SEFAZSelectors:
    """Seletores para interação com o sistema SEFAZ"""
    
    # ============================================================================
    # LOGIN
    # ============================================================================
    LOGIN = {
        'username_field': "input[name='identificacao']",
        'password_field': "input[name='senha']", 
        'submit_button': "button[type='submit'], input[type='submit']",
        'page_url': "https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin"
    }
    
    # ============================================================================
    # MENU E NAVEGAÇÃO
    # ============================================================================
    MENU = {
        'sistemas_dropdown': "a.dropdown-toggle:has(i.glyphicon-cog)",
        'sistemas_by_text': "a:has-text('Sistemas')",
        'sistemas_icon': "i.glyphicon-cog",
        'todas_areas_negocio': "a:has-text('Todas as Áreas de Negócio')",
        'todas_areas_onclick': "a[onclick*=\"listMenu(document.menuForm,this,'all')\"]"
    }
    
    # ============================================================================
    # ÁRVORE JSTREE
    # ============================================================================
    JSTREE = {
        'container': ".jstree",
        'anchor': "a.jstree-anchor",
        'expand_collapse': ".jstree-ocl",
        'conta_fiscal_node': "a.jstree-anchor:has-text('Conta Fiscal')",
        'consultar_conta_corrente': "a.jstree-anchor:contains('Consultar Conta-Corrente Fiscal')"
    }
    
    # ============================================================================
    # FORMULÁRIO DE CONSULTA
    # ============================================================================
    FORM = {
        'inscricao_estadual_input': "input[name='inscricaoEstadual']",
        'razao_social_input': "input[name='razaoSocial']",
        'confirmar_ie_link': "a[href*='recuperarDadosInscricaoEstadual']",
        'confirmar_ie_img': "img[src*='ic_confirmar.gif']",
        'continuar_button': "button:has-text('Continuar')",
        'continuar_button_alt': "button[onclick*='validateForm']",
        'continuar_input': "input[type='button']:has-text('Continuar')"
    }
    
    # ============================================================================
    # EXTRAÇÃO DE DADOS DA CONTA CORRENTE
    # ============================================================================
    DATA_EXTRACTION = {
        # Inscrição Estadual
        'ie_primary': "td.texto_negrito:has-text('Inscrição Estadual') + td span.texto",
        'ie_secondary': "td:has-text('Inscrição Estadual') + td span",
        'ie_fallback': "td:has-text('Inscrição Estadual') + td",
        
        # Razão Social
        'razao_primary': "td.texto_negrito:has-text('Razão Social') + td span.texto",
        'razao_secondary': "td:has-text('Razão Social') + td span",
        'razao_fallback': "td:has-text('Razão Social') + td",
        
        # Situação Cadastral
        'situacao_primary': "td.texto_negrito:has-text('Situação Cadastral') + td span.texto",
        'situacao_secondary': "td:has-text('Situação Cadastral') + td span",
        'situacao_fallback': "td:has-text('Situação Cadastral') + td",
        
        # Checkboxes de pendências
        'divida_pendente_checkbox': "input[name='indicadorInadimplente']:checked",
        'omisso_declaracao_checkbox': "input[name='indicadorOmisso']:checked", 
        'inscrito_restritivo_checkbox': "input[name='indicadorSerasa']:checked"
    }
    
    # ============================================================================
    # BOTÕES DE AÇÃO
    # ============================================================================
    ACTION_BUTTONS = {
        'tvis_button': "button:has-text('TVIs')",
        'dividas_pendentes_button': "button:has-text('Dívidas Pendentes')",
        'voltar_button': "button[onclick*='voltar']",
        'voltar_button_class': "button.btn.btn-warning:has-text('Voltar')",
        'voltar_text': "button:has-text('Voltar')",
        'voltar_input': "input[type='button'][value*='Voltar']",
        'voltar_link': "a:has-text('Voltar')"
    }
    
    # ============================================================================
    # MENSAGENS E CAIXA DE ENTRADA
    # ============================================================================
    MESSAGES = {
        'filtro_mensagens': "select[name='visualizarMensagens']",
        'aguardando_ciencia_option': "option[value='4']",
        'link_abrir_mensagem': "a[href*='abrirMensagem']",
        'icon_msg_nova': "img[src*='ic_msg_nova.png']",
        'botao_dar_ciencia': "button.btn-success:has-text('Informar Ciência')",
        'botao_ok_ciencia': "input[type='button'][value='OK'].btn-primary",
        'botao_voltar_mensagem': "button.btn-warning:has-text('Voltar')"
    }
    
    # ============================================================================
    # EXTRAÇÃO DE DADOS DA MENSAGEM
    # ============================================================================
    MESSAGE_DATA = {
        'ie_mensagem': "th:has-text('Inscrição Estadual:') + td",
        'enviada_por': "th:has-text('Enviada por:') + td",
        'data_envio': "th:has-text('Data do Envio:') + td",
        'assunto': "th:has-text('Assunto:') + td",
        'classificacao': "th:has-text('Classificação:') + td",
        'tributo': "th:has-text('Tributo:') + td",
        'tipo_mensagem': "th:has-text('Tipo da Mensagem:') + td",
        'numero_documento': "th:has-text('Número do Documento:') + td",
        'vencimento': "th:has-text('Vencimento:') + td",
        'data_leitura': "th:has-text('Data da Leitura:') + td",
        'conteudo_mensagem': "table.table-tripped tbody tr td"
    }
    
    # ============================================================================
    # TABELAS DE DADOS
    # ============================================================================
    TABLES = {
        'tvi_rows': "table.table.table-striped tbody tr",
        'tvi_table_main': "table.cor_tabelamae tbody tr:has(td:not(.texto_header_pagination))",
        'generic_table_rows': "table tbody tr:has(td):not(:has(td.texto_header_pagination))",
        'data_rows': "tr:has(td):not(:has(.texto_header_pagination)):not(:has(.texto_negrito))"
    }
    
    # ============================================================================
    # LOGOUT
    # ============================================================================
    LOGOUT = {
        'logoff_link': "a[href*='logoff.do?method=efetuarLogoff']",
        'logoff_generic': "a[href*='logoff.do']",
        'sair_title': "a[title*='Sair do sistema']",
        'exit_icon': "a:has(img[src*='exit.png'])",
        'sair_text': "a:has-text('Sair')",
        'logout_text': "a:has-text('Logout')",
        'exit_img': "img[src*='exit.png']"
    }
    
    # ============================================================================
    # MODAIS E ALERTAS
    # ============================================================================
    MODALS = {
        'modal_show': ".modal.show",
        'modal_display_block': ".modal[style*='display: block']",
        'alert_show': ".alert.show",
        'swal_popup': ".swal2-popup",
        'ui_dialog': ".ui-dialog",
        'modal_fade_in': ".modal.fade.in",
        'close_button': ".btn-close",
        'close_x': ".close",
        'close_button_alt': "button.close",
        'dismiss_modal': "[data-dismiss='modal']"
    }
    
    # ============================================================================
    # ALERTAS E NOTIFICAÇÕES
    # ============================================================================
    ALERTS = {
        'visible_alerts': ".alert:not(.hide):not(.hidden)",
        'notifications': ".notification",
        'messages': ".message", 
        'msg_elements': ".msg",
        'red_span_warning': "thead tr td span[style*='red']"
    }
    
    # ============================================================================
    # SESSÃO E CONFLITOS
    # ============================================================================
    SESSION = {
        'continuar_sessao': "button:has-text('Continuar')",
        'forcar_login': "button:has-text('Forçar login')",
        'encerrar_sessao': "button:has-text('Encerrar sessão anterior')",
        'sim_button': "button:has-text('Sim')",
        'ok_button': "button:has-text('OK')",
        'confirmar_button': "button:has-text('Confirmar')",
        'ok_input': "input[type='button'][value*='OK']",
        'continuar_input': "input[type='submit'][value*='Continuar']"
    }

    # ============================================================================
    # MÉTODOS DE UTILIDADE
    # ============================================================================
    
    @staticmethod
    def get_login_selectors() -> dict:
        """Retorna todos os seletores relacionados ao login"""
        return SEFAZSelectors.LOGIN
    
    @staticmethod
    def get_menu_selectors() -> dict:
        """Retorna todos os seletores relacionados ao menu"""
        return SEFAZSelectors.MENU
    
    @staticmethod
    def get_form_selectors() -> dict:
        """Retorna todos os seletores relacionados aos formulários"""
        return SEFAZSelectors.FORM
    
    @staticmethod
    def get_data_extraction_selectors() -> dict:
        """Retorna todos os seletores para extração de dados"""
        return SEFAZSelectors.DATA_EXTRACTION
    
    @staticmethod
    def get_message_selectors() -> dict:
        """Retorna todos os seletores relacionados a mensagens"""
        return SEFAZSelectors.MESSAGES
    
    @staticmethod
    def get_all_ie_selectors() -> list:
        """Retorna lista ordenada de seletores para IE (do mais específico ao mais genérico)"""
        data = SEFAZSelectors.DATA_EXTRACTION
        return [
            data['ie_primary'],
            data['ie_secondary'], 
            data['ie_fallback']
        ]
    
    @staticmethod
    def get_all_razao_selectors() -> list:
        """Retorna lista ordenada de seletores para Razão Social"""
        data = SEFAZSelectors.DATA_EXTRACTION
        return [
            data['razao_primary'],
            data['razao_secondary'],
            data['razao_fallback']
        ]
    
    @staticmethod
    def get_all_situacao_selectors() -> list:
        """Retorna lista ordenada de seletores para Situação Cadastral"""
        data = SEFAZSelectors.DATA_EXTRACTION
        return [
            data['situacao_primary'],
            data['situacao_secondary'],
            data['situacao_fallback']
        ]
    
    @staticmethod
    def get_continuar_button_selectors() -> list:
        """Retorna lista de seletores para botão Continuar"""
        form = SEFAZSelectors.FORM
        return [
            form['continuar_button'],
            form['continuar_button_alt'],
            form['continuar_input']
        ]
    
    @staticmethod
    def get_voltar_button_selectors() -> list:
        """Retorna lista de seletores para botão Voltar"""
        buttons = SEFAZSelectors.ACTION_BUTTONS
        return [
            buttons['voltar_button'],
            buttons['voltar_button_class'],
            buttons['voltar_text'],
            buttons['voltar_input'],
            buttons['voltar_link']
        ]
    
    @staticmethod
    def get_logout_selectors() -> list:
        """Retorna lista de seletores para logout"""
        logout = SEFAZSelectors.LOGOUT
        return [
            logout['logoff_link'],
            logout['logoff_generic'],
            logout['sair_title'],
            logout['exit_icon'],
            logout['sair_text'],
            logout['logout_text']
        ]