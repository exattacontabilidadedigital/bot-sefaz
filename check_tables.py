import sqlite3

conn = sqlite3.connect('sefaz_bot.db')
cursor = conn.cursor()

# Listar tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=" * 80)
print("TABELAS DISPONÍVEIS:")
print("=" * 80)
for t in tables:
    print(f"  - {t[0]}")
    # Mostrar estrutura de cada tabela
    cursor.execute(f"PRAGMA table_info({t[0]})")
    columns = cursor.fetchall()
    print(f"    Colunas:")
    for col in columns:
        print(f"      - {col[1]} ({col[2]})")
    print()

# Verificar se existe tabela empresas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='empresas'")
if cursor.fetchone():
    print("\n✅ Tabela 'empresas' existe!")
    cursor.execute("SELECT COUNT(*) FROM empresas")
    count = cursor.fetchone()[0]
    print(f"   Total de registros: {count}")
else:
    print("\n❌ Tabela 'empresas' NÃO existe!")
    print("   Frontend está tentando buscar de tabela inexistente")

conn.close()
