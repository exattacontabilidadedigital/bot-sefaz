"""
Script de teste para inserir uma mensagem SEFAZ de exemplo no banco de dados
e testar a visualização no frontend
"""

import sqlite3
from datetime import datetime

# HTML da mensagem real (limpo e formatado)
CONTEUDO_HTML = """
<div style="text-align: center;">
    <img src="https://sefaznet.sefaz.ma.gov.br/sefaznet/images/brasaoma.jpg" alt="Brasão MA">
</div>
<div style="text-align: center;">
    <div><b>ESTADO DO MARANHÃO</b></div>
    <div><b>SECRETARIA DE ESTADO DA FAZENDA</b></div>
    <div><b>RECIBO DEFINITIVO</b></div>
</div>
<br><br>
<div style="text-align: justify;">
    <b>DADOS DO PROCESSAMENTO</b><br>
    <b>Protocolo DIEF:</b> 1590248 &nbsp;&nbsp;&nbsp; <b>Versão:</b> 646<br>
    <b>Data Recepção:</b> 14/11/2025 10:53:56<br>
    <b>Data Processamento:</b> 14/11/2025 11:08:32<br>
    <b>Situação:</b> DIEF PROCESSADA<br><br>
    
    <b>Inscrição Estadual:</b> 12538398-3 &nbsp;&nbsp;&nbsp; <b>CNPJ:</b> 28494306000160<br>
    <b>Razão Social:</b> A&D SOLUTIONS LTDA<br>
    <b>Regime Pagamento:</b> SIMPLES NACIONAL<br>
    <b>Origem Declaração:</b> DIEF SIMPLES<br>
    <b>Período da DIEF:</b> 202510 &nbsp;&nbsp;&nbsp; <b>Tipo Declaração:</b> ORIGINAL &nbsp;&nbsp;&nbsp; <b>Movimento:</b> NÃO<br><br>
    
    Informamos que sua declaração foi processada com sucesso na base de dados da SEFAZ-MA.<br><br>
    O percentual apurado no confronto está em processamento, aguarde e consulte novamente em até 1 hora para visualizar esta informação<br><br>
    
    Maiores informações poderão ser obtidas no endereço http://www.sefaz.ma.gov.br, através de contato pelos e-mails dief@sefaz.ma.gov.br e decof@sefaz.ma.gov.br ou pelo Call Center 0800-5958100.<br><br>
    
    São Luís, 14/11/2025 11:08<br><br>
    <b>Chave de segurança:</b> 7713-9134-5865-7139-1345-8046-7921<br>
</div>
<div style="text-align: justify; color:red; font-size:15px; margin-top: 20px;">
    Para imprimir o recibo da DIEF clique 
    <a target="_blank" href="https://sefaznet.sefaz.ma.gov.br/sefaznet/listIReciboDief.do?method=reciboDIEF&idRecibo=30369794">aqui</a>
</div>
"""

CONTEUDO_TEXTO = """DADOS DO PROCESSAMENTO
Protocolo DIEF: 1590248                           Versão: 646
Data Recepção: 14/11/2025 10:53:56
Data Processamento: 14/11/2025 11:08:32
Situação: DIEF PROCESSADA

Inscrição Estadual: 12538398-3                    CNPJ: 28494306000160
Razão Social: A&D SOLUTIONS LTDA
Regime Pagamento: SIMPLES NACIONAL
Origem Declaração: DIEF SIMPLES
Período da DIEF: 202510       Tipo Declaração: ORIGINAL     Movimento: NÃO

Informamos que sua declaração foi processada com sucesso na base de dados da SEFAZ-MA.

O percentual apurado no confronto está em processamento, aguarde e consulte novamente em até 1 hora para visualizar esta informação

Maiores informações poderão ser obtidas no endereço http://www.sefaz.ma.gov.br, através de contato pelos e-mails dief@sefaz.ma.gov.br e decof@sefaz.ma.gov.br ou pelo Call Center 0800-5958100.

São Luís, 14/11/2025 11:08

Chave de segurança: 7713-9134-5865-7139-1345-8046-7921"""

def criar_tabela_se_nao_existe(cursor):
    """Cria a tabela mensagens_sefaz se não existir"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensagens_sefaz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inscricao_estadual TEXT,
            cpf_socio TEXT,
            enviada_por TEXT,
            data_envio TEXT,
            assunto TEXT,
            classificacao TEXT,
            tributo TEXT,
            tipo_mensagem TEXT,
            numero_documento TEXT,
            vencimento TEXT,
            conteudo_mensagem TEXT,
            competencia_dief TEXT,
            status_dief TEXT,
            chave_dief TEXT,
            protocolo_dief TEXT,
            conteudo_html TEXT,
            nome_empresa TEXT,
            data_leitura TEXT,
            data_ciencia TEXT
        )
    """)

def adicionar_colunas_se_necessario(cursor):
    """Adiciona novas colunas se não existirem"""
    # Verificar colunas existentes
    cursor.execute("PRAGMA table_info(mensagens_sefaz)")
    colunas_existentes = [row[1] for row in cursor.fetchall()]
    
    # Colunas necessárias
    novas_colunas = {
        'competencia_dief': 'TEXT',
        'status_dief': 'TEXT',
        'chave_dief': 'TEXT',
        'protocolo_dief': 'TEXT',
        'conteudo_html': 'TEXT',
        'nome_empresa': 'TEXT',
        'data_leitura': 'TEXT',
        'data_ciencia': 'TEXT'
    }
    
    for col_name, col_type in novas_colunas.items():
        if col_name not in colunas_existentes:
            try:
                cursor.execute(f"ALTER TABLE mensagens_sefaz ADD COLUMN {col_name} {col_type}")
                print(f"✅ Coluna '{col_name}' adicionada")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    print(f"⚠️ Erro ao adicionar coluna '{col_name}': {e}")

def inserir_mensagem_teste():
    """Insere uma mensagem de teste no banco de dados"""
    
    DB_PATH = "sefaz_bot.db"
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("📋 Criando/atualizando estrutura da tabela...")
        criar_tabela_se_nao_existe(cursor)
        adicionar_colunas_se_necessario(cursor)
        conn.commit()
        
        print("\n💾 Inserindo mensagem de teste...")
        
        # Dados da mensagem
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT INTO mensagens_sefaz (
                inscricao_estadual,
                nome_empresa,
                cpf_socio,
                enviada_por,
                data_envio,
                assunto,
                classificacao,
                tributo,
                tipo_mensagem,
                numero_documento,
                vencimento,
                data_leitura,
                data_ciencia,
                conteudo_mensagem,
                conteudo_html,
                competencia_dief,
                status_dief,
                chave_dief,
                protocolo_dief
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '125383983',
            'A&D SOLUTIONS LTDA',
            '12345678901',  # CPF exemplo
            'SEFAZ-MA',
            '2025-11-14 11:08:34',
            'Recibo da DIEF',
            '-',
            'ICMS',
            'COMUNICADO',
            '1590248',
            '2025-11-29',
            '2025-11-16 15:26:54',
            data_atual,
            CONTEUDO_TEXTO,
            CONTEUDO_HTML,
            '202510',
            'DIEF PROCESSADA',
            '7713-9134-5865-7139-1345-8046-7921',
            '1590248'
        ))
        
        conn.commit()
        mensagem_id = cursor.lastrowid
        
        print(f"✅ Mensagem inserida com sucesso! ID: {mensagem_id}")
        
        # Verificar o que foi inserido
        print("\n📊 Verificando dados inseridos:")
        cursor.execute("SELECT * FROM mensagens_sefaz WHERE id = ?", (mensagem_id,))
        row = cursor.fetchone()
        
        cursor.execute("PRAGMA table_info(mensagens_sefaz)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        print("\n" + "="*80)
        for i, col in enumerate(colunas):
            valor = row[i] if i < len(row) else None
            if valor and len(str(valor)) > 100:
                print(f"{col}: {str(valor)[:100]}... (truncado)")
            else:
                print(f"{col}: {valor}")
        print("="*80)
        
        conn.close()
        
        print(f"\n🎉 Teste concluído!")
        print(f"\n📱 Agora você pode:")
        print(f"   1. Acessar http://localhost:8000")
        print(f"   2. Ir para a aba 'Mensagens SEFAZ'")
        print(f"   3. Clicar em 'Ver' na mensagem de teste")
        print(f"   4. Verificar se o HTML está sendo renderizado corretamente")
        print(f"\n💡 A mensagem aparecerá com:")
        print(f"   - Competência: 10/2025")
        print(f"   - Status: DIEF PROCESSADA")
        print(f"   - Chave: 7713-9134-5865-7139-1345-8046-7921")
        print(f"   - Conteúdo HTML formatado com brasão e dados completos")
        
        return mensagem_id
        
    except Exception as e:
        print(f"❌ Erro ao inserir mensagem: {e}")
        import traceback
        traceback.print_exc()
        return None

def limpar_mensagens_teste():
    """Remove todas as mensagens de teste"""
    DB_PATH = "sefaz_bot.db"
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM mensagens_sefaz")
        total_antes = cursor.fetchone()[0]
        
        resposta = input(f"\n⚠️ Deseja remover todas as {total_antes} mensagens? (s/n): ")
        
        if resposta.lower() == 's':
            cursor.execute("DELETE FROM mensagens_sefaz")
            conn.commit()
            print(f"✅ {total_antes} mensagens removidas")
        else:
            print("❌ Operação cancelada")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao limpar mensagens: {e}")

if __name__ == "__main__":
    print("="*80)
    print("🧪 TESTE DE MENSAGENS SEFAZ")
    print("="*80)
    print("\nEscolha uma opção:")
    print("1. Inserir mensagem de teste")
    print("2. Limpar todas as mensagens")
    print("3. Apenas criar/atualizar tabela")
    
    opcao = input("\nOpção: ").strip()
    
    if opcao == "1":
        inserir_mensagem_teste()
    elif opcao == "2":
        limpar_mensagens_teste()
    elif opcao == "3":
        DB_PATH = "sefaz_bot.db"
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        criar_tabela_se_nao_existe(cursor)
        adicionar_colunas_se_necessario(cursor)
        conn.commit()
        conn.close()
        print("✅ Tabela criada/atualizada com sucesso!")
    else:
        print("❌ Opção inválida")
