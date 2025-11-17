import sqlite3
from typing import Optional, List
import sys

DB_PATH = "sefaz_bot.db"

def test_endpoint():
    """Simula o código do endpoint /api/mensagens"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        limit = 5
        offset = 0
        search = None
        inscricao_estadual = None
        
        # Construir query com filtros
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(assunto LIKE ? OR conteudo_mensagem LIKE ? OR nome_empresa LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
        if inscricao_estadual:
            where_conditions.append("inscricao_estadual = ?")
            params.append(inscricao_estadual)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT * FROM mensagens_sefaz
            {where_clause}
            ORDER BY data_envio DESC, id DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        print(f"📝 Query: {query}")
        print(f"📝 Params: {params}")
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        print(f"\n✅ Query executada com sucesso!")
        print(f"📊 Linhas retornadas: {len(rows)}")
        
        if rows:
            print(f"\n📋 Primeira linha:")
            row = rows[0]
            print(f"   - Tipo: {type(row)}")
            print(f"   - Keys disponíveis: {row.keys()}")
            
            # Tentar criar o dicionário como no endpoint
            print(f"\n🔧 Tentando criar dicionário...")
            mensagem = {
                "id": row["id"],
                "inscricao_estadual": row["inscricao_estadual"],
                "nome_empresa": row.get("nome_empresa"),
                "enviada_por": row["enviada_por"],
                "data_envio": row["data_envio"],
                "assunto": row["assunto"],
                "classificacao": row.get("classificacao"),
                "tributo": row.get("tributo"),
                "tipo_mensagem": row.get("tipo_mensagem"),
                "numero_documento": row.get("numero_documento"),
                "vencimento": row.get("vencimento"),
                "competencia_dief": row.get("competencia_dief"),
                "status_dief": row.get("status_dief"),
                "chave_dief": row.get("chave_dief"),
                "protocolo_dief": row.get("protocolo_dief"),
                "data_leitura": row.get("data_leitura"),
                "data_ciencia": row.get("data_ciencia"),
                "conteudo_mensagem": row["conteudo_mensagem"],
                "conteudo_html": row.get("conteudo_html")
            }
            
            print(f"✅ Dicionário criado com sucesso!")
            print(f"📦 Campos:")
            for key, value in mensagem.items():
                value_preview = str(value)[:50] + "..." if value and len(str(value)) > 50 else value
                print(f"   - {key}: {value_preview}")
        
        conn.close()
        print(f"\n✅ Teste concluído com sucesso!")
        
    except Exception as e:
        import traceback
        print(f"\n❌ ERRO:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        print(f"\n📋 Traceback completo:")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    test_endpoint()
