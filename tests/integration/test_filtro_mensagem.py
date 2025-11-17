"""
Script de teste para verificar filtro de mensagens por IE
"""
import sqlite3
import sys

DB_PATH = "sefaz_bot.db"
IE_TESTE = "125383983"

def testar_filtro_ie():
    """Testa o filtro de mensagens por Inscrição Estadual"""
    
    print("=" * 80)
    print("🧪 TESTE DE FILTRO DE MENSAGENS POR IE")
    print("=" * 80)
    print(f"📌 IE para teste: {IE_TESTE}")
    print()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Verificar total de mensagens no banco
        print("1️⃣ Verificando total de mensagens no banco...")
        cursor.execute("SELECT COUNT(*) as total FROM mensagens_sefaz")
        total = cursor.fetchone()['total']
        print(f"   ✅ Total de mensagens: {total}")
        print()
        
        # 2. Verificar mensagens para a IE específica
        print(f"2️⃣ Verificando mensagens para IE {IE_TESTE}...")
        cursor.execute("""
            SELECT id, inscricao_estadual, nome_empresa, assunto, 
                   data_envio, competencia_dief, status_dief
            FROM mensagens_sefaz
            WHERE inscricao_estadual = ?
            ORDER BY data_envio DESC
        """, (IE_TESTE,))
        
        mensagens = cursor.fetchall()
        print(f"   ✅ Mensagens encontradas: {len(mensagens)}")
        print()
        
        if mensagens:
            print("📋 DETALHES DAS MENSAGENS:")
            print("-" * 80)
            for idx, msg in enumerate(mensagens, 1):
                print(f"\n{idx}. Mensagem ID: {msg['id']}")
                print(f"   - IE: {msg['inscricao_estadual']}")
                print(f"   - Empresa: {msg['nome_empresa']}")
                print(f"   - Assunto: {msg['assunto']}")
                print(f"   - Data Envio: {msg['data_envio']}")
                print(f"   - Competência DIEF: {msg['competencia_dief']}")
                print(f"   - Status DIEF: {msg['status_dief']}")
        else:
            print("⚠️ NENHUMA MENSAGEM ENCONTRADA PARA ESTA IE")
            print()
            print("🔍 Verificando se há mensagens com IEs parecidas...")
            cursor.execute("""
                SELECT DISTINCT inscricao_estadual, nome_empresa, COUNT(*) as qtd
                FROM mensagens_sefaz
                GROUP BY inscricao_estadual
                ORDER BY qtd DESC
            """)
            todas_ies = cursor.fetchall()
            
            if todas_ies:
                print("\n📊 IEs existentes no banco:")
                print("-" * 80)
                for ie_info in todas_ies:
                    print(f"   - IE: {ie_info['inscricao_estadual']} | Empresa: {ie_info['nome_empresa']} | Qtd: {ie_info['qtd']}")
            else:
                print("⚠️ Nenhuma mensagem cadastrada no banco!")
        
        print()
        print("=" * 80)
        
        # 3. Testar a query exatamente como a API faz
        print("\n3️⃣ Testando query igual à API...")
        limit = 20
        offset = 0
        
        query = """
            SELECT * FROM mensagens_sefaz
            WHERE inscricao_estadual = ?
            ORDER BY data_envio DESC, id DESC
            LIMIT ? OFFSET ?
        """
        params = [IE_TESTE, limit, offset]
        
        print(f"   📋 Query: {query.strip()}")
        print(f"   📋 Params: {params}")
        
        cursor.execute(query, params)
        result = cursor.fetchall()
        
        print(f"   ✅ Resultado: {len(result)} mensagens")
        
        if result:
            print("\n   📄 Primeira mensagem retornada:")
            msg = result[0]
            print(f"      - ID: {msg['id']}")
            print(f"      - IE: {msg['inscricao_estadual']}")
            print(f"      - Empresa: {msg['nome_empresa']}")
            print(f"      - Assunto: {msg['assunto']}")
        
        conn.close()
        
        print()
        print("=" * 80)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 80)
        
        return len(mensagens) > 0
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = testar_filtro_ie()
    sys.exit(0 if success else 1)
