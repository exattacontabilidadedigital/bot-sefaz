#!/usr/bin/env python3
"""
Script para importar empresas do JSON para o servidor via API
"""
import json
import requests
import sys

if len(sys.argv) < 2:
    print("Uso: python import_empresas.py http://seu-dominio.com")
    sys.exit(1)

BASE_URL = sys.argv[1].rstrip('/')

# Ler empresas do JSON
with open('empresas_export.json', 'r', encoding='utf-8') as f:
    empresas = json.load(f)

print(f"📦 Importando {len(empresas)} empresas para {BASE_URL}...")

sucesso = 0
falhas = 0

for empresa in empresas:
    try:
        response = requests.post(
            f"{BASE_URL}/api/empresas",
            json=empresa,
            timeout=10
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"✅ {empresa['nome_empresa']} - OK")
            sucesso += 1
        else:
            print(f"❌ {empresa['nome_empresa']} - Erro: {response.status_code}")
            print(f"   Detalhes: {response.text}")
            falhas += 1
            
    except Exception as e:
        print(f"❌ {empresa['nome_empresa']} - Erro: {e}")
        falhas += 1

print(f"\n✅ Sucesso: {sucesso}")
print(f"❌ Falhas: {falhas}")
print(f"📊 Total: {len(empresas)}")
