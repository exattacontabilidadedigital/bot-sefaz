"""
Script para adicionar coluna link_recibo e extrair links de mensagens existentes
"""
import sqlite3
import re

def migrar_link_recibo():
    print("🔄 Iniciando migração de link_recibo...")
    
    conn = sqlite3.connect('sefaz_bot.db')
    cursor = conn.cursor()
    
    # 1. Adicionar coluna se não existir
    try:
        cursor.execute("ALTER TABLE mensagens_sefaz ADD COLUMN link_recibo TEXT")
        print("✅ Coluna link_recibo adicionada")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("ℹ️  Coluna link_recibo já existe")
        else:
            raise
    
    conn.commit()
    
    # 2. Buscar mensagens sem link_recibo mas com conteudo_html
    cursor.execute("""
        SELECT id, conteudo_html, conteudo_mensagem 
        FROM mensagens_sefaz 
        WHERE (link_recibo IS NULL OR link_recibo = '')
    """)
    
    mensagens = cursor.fetchall()
    print(f"📊 Encontradas {len(mensagens)} mensagens para processar")
    
    # 3. Extrair e atualizar links
    atualizadas = 0
    for msg_id, conteudo_html, conteudo_mensagem in mensagens:
        # Tentar primeiro no HTML, depois no texto
        conteudo = conteudo_html or conteudo_mensagem or ''
        
        if 'listIReciboDief' in conteudo:
            match = re.search(r'href=["\']([^"\']*listIReciboDief\.do[^"\']*)["\']', conteudo, re.IGNORECASE)
            if match:
                link_recibo = match.group(1).replace('&amp;', '&')
                cursor.execute(
                    "UPDATE mensagens_sefaz SET link_recibo = ? WHERE id = ?",
                    (link_recibo, msg_id)
                )
                print(f"   ✅ Mensagem ID {msg_id}: {link_recibo}")
                atualizadas += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Migração concluída!")
    print(f"📊 {atualizadas} de {len(mensagens)} mensagens atualizadas com link_recibo")

if __name__ == '__main__':
    migrar_link_recibo()
