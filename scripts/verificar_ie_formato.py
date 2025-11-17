import sqlite3

conn = sqlite3.connect('sefaz_bot.db')
cursor = conn.cursor()

print("=" * 80)
print("VERIFICANDO FORMATO DA INSCRIÇÃO ESTADUAL")
print("=" * 80)

# Verificar tabela empresas
print("\n1️⃣ TABELA EMPRESAS:")
cursor.execute("SELECT id, inscricao_estadual, nome_empresa FROM empresas WHERE nome_empresa LIKE '%A&D%'")
rows = cursor.fetchall()
for r in rows:
    ie = r[1]
    print(f"   ID: {r[0]}")
    print(f"   IE: [{ie}]")
    print(f"   Tamanho: {len(ie)} caracteres")
    print(f"   Tem traço? {'SIM' if '-' in ie else 'NÃO'}")
    print(f"   IE sem caracteres especiais: [{ie.replace('-', '')}]")
    print(f"   Empresa: {r[2]}")

# Verificar tabela mensagens_sefaz
print("\n2️⃣ TABELA MENSAGENS_SEFAZ:")
cursor.execute("SELECT id, inscricao_estadual, nome_empresa FROM mensagens_sefaz LIMIT 5")
rows = cursor.fetchall()
for r in rows:
    ie = r[1] or 'NULL'
    print(f"   ID: {r[0]}")
    print(f"   IE: [{ie}]")
    if ie != 'NULL':
        print(f"   Tamanho: {len(ie)} caracteres")
        print(f"   Tem traço? {'SIM' if '-' in ie else 'NÃO'}")
    print(f"   Empresa: {r[2]}")
    print()

# Testar busca com IE com traço
print("\n3️⃣ TESTE DE BUSCA COM TRAÇO:")
cursor.execute("SELECT COUNT(*) FROM mensagens_sefaz WHERE inscricao_estadual = '12538398-3'")
count_com_traco = cursor.fetchone()[0]
print(f"   Mensagens com IE '12538398-3': {count_com_traco}")

# Testar busca com IE sem traço
print("\n4️⃣ TESTE DE BUSCA SEM TRAÇO:")
cursor.execute("SELECT COUNT(*) FROM mensagens_sefaz WHERE inscricao_estadual = '125383983'")
count_sem_traco = cursor.fetchone()[0]
print(f"   Mensagens com IE '125383983': {count_sem_traco}")

print("\n" + "=" * 80)
print("CONCLUSÃO:")
if count_com_traco > 0:
    print("   ✅ As mensagens estão salvas COM traço (12538398-3)")
elif count_sem_traco > 0:
    print("   ✅ As mensagens estão salvas SEM traço (125383983)")
else:
    print("   ❌ Nenhuma mensagem encontrada com essa IE")
print("=" * 80)

conn.close()
