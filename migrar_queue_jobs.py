import sqlite3

DB_PATH = 'sefaz_consulta.db'

def migrar_tabela_queue_jobs():
    """Migra a tabela queue_jobs para o novo schema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se a coluna data_adicao existe
        cursor.execute("PRAGMA table_info(queue_jobs)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        print(f"Colunas atuais: {colunas}")
        
        if 'data_adicao' in colunas:
            print("✅ Tabela já está no formato correto!")
            conn.close()
            return
        
        print("🔄 Migrando tabela queue_jobs...")
        
        # Criar tabela temporária com schema correto
        cursor.execute("""
            CREATE TABLE queue_jobs_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                prioridade INTEGER DEFAULT 0,
                data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_processamento TIMESTAMP,
                tentativas INTEGER DEFAULT 0,
                max_tentativas INTEGER DEFAULT 3,
                erro_detalhes TEXT,
                FOREIGN KEY (empresa_id) REFERENCES empresas(id)
            )
        """)
        
        # Copiar dados (mapear colunas antigas para novas)
        # Mapear: data_criacao -> data_adicao, data_inicio/data_conclusao -> data_processamento
        cursor.execute("""
            INSERT INTO queue_jobs_new 
            (id, empresa_id, status, prioridade, data_adicao, data_processamento, tentativas, max_tentativas, erro_detalhes)
            SELECT 
                id, 
                empresa_id, 
                status, 
                prioridade, 
                data_criacao as data_adicao,
                COALESCE(data_conclusao, data_inicio) as data_processamento,
                tentativas, 
                max_tentativas, 
                erro_detalhes
            FROM queue_jobs
        """)
        
        # Remover tabela antiga
        cursor.execute("DROP TABLE queue_jobs")
        
        # Renomear tabela nova
        cursor.execute("ALTER TABLE queue_jobs_new RENAME TO queue_jobs")
        
        conn.commit()
        print("✅ Migração concluída com sucesso!")
        
        # Verificar novamente
        cursor.execute("PRAGMA table_info(queue_jobs)")
        colunas_novas = [col[1] for col in cursor.fetchall()]
        print(f"Colunas após migração: {colunas_novas}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrar_tabela_queue_jobs()
