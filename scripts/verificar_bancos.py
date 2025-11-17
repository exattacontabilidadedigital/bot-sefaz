import sqlite3

print("=" * 80)
print("VERIFICANDO BANCOS DE DADOS")
print("=" * 80)

# Verificar sefaz_bot.db
print("\n📂 sefaz_bot.db:")
try:
    conn = sqlite3.connect('sefaz_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"   Tabelas: {', '.join(tables)}")
    if 'empresas' in tables:
        cursor.execute("SELECT COUNT(*) FROM empresas")
        print(f"   ✅ Tabela 'empresas' existe! Total: {cursor.fetchone()[0]} registros")
    conn.close()
except Exception as e:
    print(f"   ❌ Erro: {e}")

# Verificar sefaz_consulta.db
print("\n📂 sefaz_consulta.db:")
try:
    conn = sqlite3.connect('sefaz_consulta.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"   Tabelas: {', '.join(tables)}")
    if 'empresas' in tables:
        cursor.execute("SELECT COUNT(*) FROM empresas")
        print(f"   ✅ Tabela 'empresas' existe! Total: {cursor.fetchone()[0]} registros")
        
        # Buscar empresa A&D
        cursor.execute("SELECT id, inscricao_estadual, nome_empresa FROM empresas WHERE nome_empresa LIKE '%A&D%'")
        rows = cursor.fetchall()
        if rows:
            print("\n   Empresa A&D encontrada:")
            for r in rows:
                ie = r[1]
                print(f"      ID: {r[0]}")
                print(f"      IE: [{ie}]")
                print(f"      Empresa: {r[2]}")
    conn.close()
except Exception as e:
    print(f"   ❌ Erro: {e}")

print("\n" + "=" * 80)
