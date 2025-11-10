#!/usr/bin/env python3
"""
Script para importar empresas de um arquivo CSV para o servidor via API
"""
import csv
import requests
import sys
from pathlib import Path

def importar_empresas_csv(csv_file: str, base_url: str):
    """
    Importa empresas de um arquivo CSV para o servidor
    
    Args:
        csv_file: Caminho do arquivo CSV
        base_url: URL base do servidor (ex: http://localhost:8000)
    """
    
    if not Path(csv_file).exists():
        print(f"❌ Arquivo não encontrado: {csv_file}")
        return
    
    base_url = base_url.rstrip('/')
    
    print(f"📂 Lendo arquivo: {csv_file}")
    print(f"🌐 Servidor: {base_url}")
    print("=" * 60)
    
    empresas = []
    
    # Ler CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Validar colunas obrigatórias
        required_columns = ['nome_empresa', 'cnpj', 'inscricao_estadual', 'cpf_socio', 'senha']
        missing_columns = [col for col in required_columns if col not in reader.fieldnames]
        
        if missing_columns:
            print(f"❌ Colunas obrigatórias faltando: {', '.join(missing_columns)}")
            print(f"Colunas disponíveis: {', '.join(reader.fieldnames)}")
            return
        
        for row in reader:
            empresas.append({
                'nome_empresa': row['nome_empresa'].strip(),
                'cnpj': row['cnpj'].strip(),
                'inscricao_estadual': row['inscricao_estadual'].strip(),
                'cpf_socio': row['cpf_socio'].strip(),
                'senha': row['senha'].strip(),
                'observacoes': row.get('observacoes', '').strip(),
                'ativo': True
            })
    
    print(f"📦 {len(empresas)} empresas encontradas no CSV\n")
    
    sucesso = 0
    falhas = 0
    erros = []
    
    for i, empresa in enumerate(empresas, 1):
        try:
            print(f"[{i}/{len(empresas)}] Importando: {empresa['nome_empresa']}...", end=' ')
            
            response = requests.post(
                f"{base_url}/api/empresas",
                json=empresa,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print("✅ OK")
                sucesso += 1
            else:
                print(f"❌ Erro {response.status_code}")
                erro_msg = response.json().get('detail', response.text) if response.headers.get('content-type') == 'application/json' else response.text
                erros.append(f"  - {empresa['nome_empresa']}: {erro_msg}")
                falhas += 1
                
        except requests.exceptions.ConnectionError:
            print("❌ Erro de conexão")
            erros.append(f"  - {empresa['nome_empresa']}: Não foi possível conectar ao servidor")
            falhas += 1
        except requests.exceptions.Timeout:
            print("❌ Timeout")
            erros.append(f"  - {empresa['nome_empresa']}: Tempo de resposta excedido")
            falhas += 1
        except Exception as e:
            print(f"❌ Erro: {e}")
            erros.append(f"  - {empresa['nome_empresa']}: {str(e)}")
            falhas += 1
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DA IMPORTAÇÃO")
    print("=" * 60)
    print(f"✅ Sucesso: {sucesso}")
    print(f"❌ Falhas: {falhas}")
    print(f"📦 Total: {len(empresas)}")
    
    if erros:
        print("\n⚠️  DETALHES DOS ERROS:")
        for erro in erros:
            print(erro)

def main():
    if len(sys.argv) < 3:
        print("=" * 60)
        print("📋 IMPORTADOR DE EMPRESAS VIA CSV")
        print("=" * 60)
        print("\n💡 Uso:")
        print("  python importar_csv.py <arquivo.csv> <url_servidor>\n")
        print("📝 Exemplo:")
        print("  python importar_csv.py empresas.csv http://localhost:8000")
        print("  python importar_csv.py empresas.csv http://seu-dominio.com\n")
        print("📄 Formato do CSV:")
        print("  - Colunas obrigatórias: nome_empresa, cnpj, inscricao_estadual, cpf_socio, senha")
        print("  - Coluna opcional: observacoes")
        print("  - Separador: vírgula (,)")
        print("  - Encoding: UTF-8\n")
        print("📋 Use o arquivo 'empresas_template.csv' como exemplo!")
        print("=" * 60)
        sys.exit(1)
    
    csv_file = sys.argv[1]
    base_url = sys.argv[2]
    
    importar_empresas_csv(csv_file, base_url)

if __name__ == '__main__':
    main()
