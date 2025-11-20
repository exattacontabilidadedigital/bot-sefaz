import sqlite3
import os

# Verificar se existe arquivo de banco
if os.path.exists('mensagens_sefaz.db'):
    print("Arquivo mensagens_sefaz.db encontrado")
    
    # Conectar ao banco de mensagens
    conn = sqlite3.connect('mensagens_sefaz.db')
    cursor = conn.cursor()

    # Listar tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tabelas existentes:", [t[0] for t in tables])
    
    conn.close()
else:
    print("Arquivo mensagens_sefaz.db NÃO encontrado")

# Verificar outros arquivos .db
db_files = [f for f in os.listdir('.') if f.endswith('.db')]
print("Arquivos .db encontrados:", db_files)