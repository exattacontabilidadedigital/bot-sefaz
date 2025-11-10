import sqlite3

conn = sqlite3.connect('sefaz_consulta.db')
cursor = conn.cursor()

# Verificar estrutura da tabela
cursor.execute("PRAGMA table_info(queue_jobs)")
columns = cursor.fetchall()
print("📋 Colunas da tabela queue_jobs:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# Cancelar job 60
cursor.execute("""
    UPDATE queue_jobs 
    SET status = 'failed', 
        erro_detalhes = 'Cancelado manualmente via script'
    WHERE id = 60
""")

conn.commit()
print(f'\n✅ Job 60 cancelado. Linhas afetadas: {cursor.rowcount}')

# Verificar status
cursor.execute("SELECT id, status, erro_detalhes FROM queue_jobs WHERE id = 60")
result = cursor.fetchone()
if result:
    print(f'📋 Job 60 agora está: {result[1]} - {result[2]}')

conn.close()
