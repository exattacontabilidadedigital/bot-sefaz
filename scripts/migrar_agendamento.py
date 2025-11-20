#!/usr/bin/env python3
"""
Script de migração para adicionar campos de agendamento à tabela queue_jobs.
Este script adiciona suporte para execuções programadas mantendo compatibilidade com jobs imediatos.
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Adiciona campos de agendamento à tabela queue_jobs"""
    
    # Em produção, usar o diretório de dados persistente
    if os.getenv('ENVIRONMENT') == 'production':
        os.makedirs('/data', exist_ok=True)
        db_path = '/data/sefaz_consulta.db'
    else:
        db_path = os.getenv('DB_PATH', 'sefaz_consulta.db')
    
    print(f"📂 Usando banco: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Iniciando migração do banco de dados...")
        
        # Verificar se as colunas já existem
        cursor.execute("PRAGMA table_info(queue_jobs)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Adicionar coluna data_agendada se não existir
        if 'data_agendada' not in existing_columns:
            cursor.execute('ALTER TABLE queue_jobs ADD COLUMN data_agendada TIMESTAMP')
            print("✅ Adicionada coluna 'data_agendada'")
        else:
            print("ℹ️ Coluna 'data_agendada' já existe")
            
        # Adicionar coluna tipo_execucao se não existir
        if 'tipo_execucao' not in existing_columns:
            cursor.execute("ALTER TABLE queue_jobs ADD COLUMN tipo_execucao TEXT DEFAULT 'imediata'")
            print("✅ Adicionada coluna 'tipo_execucao'")
        else:
            print("ℹ️ Coluna 'tipo_execucao' já existe")
            
        # Adicionar coluna recorrencia se não existir
        if 'recorrencia' not in existing_columns:
            cursor.execute('ALTER TABLE queue_jobs ADD COLUMN recorrencia TEXT')
            print("✅ Adicionada coluna 'recorrencia'")
        else:
            print("ℹ️ Coluna 'recorrencia' já existe")
            
        # Adicionar coluna ativo_agendamento se não existir
        if 'ativo_agendamento' not in existing_columns:
            cursor.execute('ALTER TABLE queue_jobs ADD COLUMN ativo_agendamento BOOLEAN DEFAULT 1')
            print("✅ Adicionada coluna 'ativo_agendamento'")
        else:
            print("ℹ️ Coluna 'ativo_agendamento' já existe")
            
        # Adicionar coluna criado_por se não existir (para identificar agendamentos)
        if 'criado_por' not in existing_columns:
            cursor.execute("ALTER TABLE queue_jobs ADD COLUMN criado_por TEXT DEFAULT 'manual'")
            print("✅ Adicionada coluna 'criado_por'")
        else:
            print("ℹ️ Coluna 'criado_por' já existe")
        
        # Atualizar jobs existentes para serem do tipo 'imediata'
        cursor.execute("""
            UPDATE queue_jobs 
            SET tipo_execucao = 'imediata' 
            WHERE tipo_execucao IS NULL
        """)
        
        # Atualizar jobs existentes para serem ativos
        cursor.execute("""
            UPDATE queue_jobs 
            SET ativo_agendamento = 1 
            WHERE ativo_agendamento IS NULL
        """)
        
        # Atualizar jobs existentes como criados manualmente
        cursor.execute("""
            UPDATE queue_jobs 
            SET criado_por = 'manual' 
            WHERE criado_por IS NULL
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Migração concluída com sucesso!")
        print("\n📊 Estrutura atualizada da tabela queue_jobs:")
        print("   - data_agendada: TIMESTAMP (quando executar)")
        print("   - tipo_execucao: TEXT ('imediata' ou 'agendada')")
        print("   - recorrencia: TEXT ('unica', 'diaria', 'semanal', 'mensal')")
        print("   - ativo_agendamento: BOOLEAN (se agendamento está ativo)")
        print("   - criado_por: TEXT ('manual' ou 'recorrencia')")
        print("\n🔒 Configuração de persistência:")
        print(f"   - Banco localizado em: {db_path}")
        if os.getenv('ENVIRONMENT') == 'production':
            print("   - ✅ Modo produção: dados persistirão em volume Docker")
        else:
            print("   - ℹ️ Modo desenvolvimento: dados locais")
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        raise

if __name__ == "__main__":
    migrate_database()