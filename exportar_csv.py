#!/usr/bin/env python3
"""
Script para exportar empresas do banco local para CSV
"""
import sqlite3
import csv

def exportar_empresas_csv(db_path='sefaz_consulta.db', output_file='empresas_export.csv'):
    """Exporta empresas do banco para CSV"""
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Buscar todas as empresas ativas
        cursor.execute("""
            SELECT 
                nome_empresa,
                cnpj,
                inscricao_estadual,
                cpf_socio,
                senha,
                observacoes
            FROM empresas
            WHERE ativo = 1
            ORDER BY nome_empresa
        """)
        
        empresas = cursor.fetchall()
        conn.close()
        
        if not empresas:
            print("⚠️  Nenhuma empresa encontrada no banco de dados")
            return
        
        # Escrever CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Cabeçalho
            writer.writerow(['nome_empresa', 'cnpj', 'inscricao_estadual', 'cpf_socio', 'senha', 'observacoes'])
            
            # Dados
            for empresa in empresas:
                writer.writerow([
                    empresa['nome_empresa'],
                    empresa['cnpj'],
                    empresa['inscricao_estadual'],
                    empresa['cpf_socio'],
                    empresa['senha'],
                    empresa['observacoes'] or ''
                ])
        
        print(f"✅ {len(empresas)} empresas exportadas para: {output_file}")
        print(f"\n💡 Próximo passo:")
        print(f"   python importar_csv.py {output_file} http://seu-dominio.com")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao acessar banco de dados: {e}")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    exportar_empresas_csv()
