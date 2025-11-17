import sqlite3

conn = sqlite3.connect('sefaz_consulta.db')
cursor = conn.cursor()

print("=" * 80)
print("COMPARANDO FORMATO DA IE ENTRE TABELAS")
print("=" * 80)

# Tabela empresas
print("\n1️⃣ TABELA EMPRESAS (A&D SOLUTIONS):")
cursor.execute("SELECT inscricao_estadual FROM empresas WHERE nome_empresa LIKE '%A&D%'")
ie_empresa = cursor.fetchone()
if ie_empresa:
    ie = ie_empresa[0]
    print(f"   IE na tabela empresas: [{ie}]")
    print(f"   Tamanho: {len(ie)} caracteres")
    print(f"   Tem traço: {'SIM' if '-' in ie else 'NÃO'}")
else:
    print("   ❌ Empresa não encontrada")

# Tabela mensagens_sefaz - verificar colunas primeiro
print("\n2️⃣ TABELA MENSAGENS_SEFAZ:")
cursor.execute("PRAGMA table_info(mensagens_sefaz)")
columns = [col[1] for col in cursor.fetchall()]
print(f"   Colunas disponíveis: {', '.join(columns[:10])}...")

cursor.execute("SELECT DISTINCT inscricao_estadual FROM mensagens_sefaz WHERE inscricao_estadual IS NOT NULL LIMIT 5")
rows = cursor.fetchall()
if rows:
    for r in rows:
        ie = r[0]
        print(f"   IE: [{ie}]")
        print(f"      Tamanho: {len(ie)} caracteres, Tem traço: {'SIM' if '-' in ie else 'NÃO'}")
else:
    print("   ❌ Nenhuma mensagem com IE encontrada")

# Testar busca
print("\n3️⃣ TESTE DE BUSCA:")
if ie_empresa:
    ie_buscar = ie_empresa[0]
    cursor.execute("SELECT COUNT(*) FROM mensagens_sefaz WHERE inscricao_estadual = ?", (ie_buscar,))
    count = cursor.fetchone()[0]
    print(f"   Buscando por IE '{ie_buscar}': {count} mensagens")
    
    # Testar sem traço
    ie_sem_traco = ie_buscar.replace('-', '')
    cursor.execute("SELECT COUNT(*) FROM mensagens_sefaz WHERE inscricao_estadual = ?", (ie_sem_traco,))
    count2 = cursor.fetchone()[0]
    print(f"   Buscando por IE '{ie_sem_traco}' (sem traço): {count2} mensagens")

print("\n" + "=" * 80)
print("CONCLUSÃO:")
if ie_empresa:
    ie = ie_empresa[0]
    if '-' in ie:
        print("   ⚠️  TABELA EMPRESAS tem IE COM traço (12538398-3)")
    else:
        print("   ⚠️  TABELA EMPRESAS tem IE SEM traço (125383983)")

cursor.execute("SELECT inscricao_estadual FROM mensagens_sefaz LIMIT 1")
ie_msg = cursor.fetchone()
if ie_msg and ie_msg[0]:
    if '-' in ie_msg[0]:
        print("   ⚠️  TABELA MENSAGENS_SEFAZ tem IE COM traço")
    else:
        print("   ⚠️  TABELA MENSAGENS_SEFAZ tem IE SEM traço")
        
print("\n   ❗ Se os formatos são diferentes, o filtro NÃO vai funcionar!")
print("=" * 80)

conn.close()
