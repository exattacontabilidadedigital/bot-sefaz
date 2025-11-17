#!/usr/bin/env python3
"""
Script para exportar empresas do banco local para JSON
"""
import sqlite3
import json

# Conectar ao banco local
conn = sqlite3.connect('sefaz_consulta.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Buscar todas as empresas
cursor.execute("""
    SELECT 
        nome_empresa,
        cnpj,
        inscricao_estadual,
        cpf_socio,
        senha,
        observacoes,
        ativo
    FROM empresas
    WHERE ativo = 1
""")

empresas = []
for row in cursor.fetchall():
    empresas.append({
        'nome_empresa': row['nome_empresa'],
        'cnpj': row['cnpj'],
        'inscricao_estadual': row['inscricao_estadual'],
        'cpf_socio': row['cpf_socio'],
        'senha': row['senha'],
        'observacoes': row['observacoes'],
        'ativo': bool(row['ativo'])
    })

conn.close()

# Salvar em JSON
with open('empresas_export.json', 'w', encoding='utf-8') as f:
    json.dump(empresas, f, indent=2, ensure_ascii=False)

print(f"✅ {len(empresas)} empresas exportadas para empresas_export.json")
print("\nPróximo passo:")
print("python import_empresas.py http://seu-dominio.com")
