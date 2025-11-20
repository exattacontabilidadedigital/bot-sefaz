#!/usr/bin/env python3
"""
Script de teste para demonstrar o sistema de migração aprimorado.
Cria um banco temporário, executa migração e validação.

Este script serve como demonstração das melhorias implementadas.
"""

import sqlite3
import os
import tempfile
import sys
from pathlib import Path

# Adicionar path do projeto para imports
sys.path.append(str(Path(__file__).parent.parent))

def create_test_database(db_path):
    """Cria um banco de teste com dados básicos"""
    print(f"Criando banco de teste: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Criar tabela de empresas
    cursor.execute('''
        CREATE TABLE empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_empresa TEXT NOT NULL,
            cnpj TEXT NOT NULL UNIQUE,
            inscricao_estadual TEXT NOT NULL UNIQUE,
            cpf_socio TEXT NOT NULL,
            senha TEXT NOT NULL,
            observacoes TEXT,
            ativo BOOLEAN DEFAULT 1,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Criar tabela queue_jobs SEM colunas de agendamento
    cursor.execute('''
        CREATE TABLE queue_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            prioridade INTEGER DEFAULT 0,
            data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_processamento TIMESTAMP,
            tentativas INTEGER DEFAULT 0,
            max_tentativas INTEGER DEFAULT 3,
            erro_detalhes TEXT,
            FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        )
    ''')
    
    # Inserir empresa de teste
    cursor.execute('''
        INSERT INTO empresas (nome_empresa, cnpj, inscricao_estadual, cpf_socio, senha)
        VALUES ('Empresa Teste LTDA', '12345678000199', '123456789', '12345678901', 'senha123')
    ''')
    
    # Inserir alguns jobs de teste
    cursor.execute('''
        INSERT INTO queue_jobs (empresa_id, status, prioridade)
        VALUES (1, 'pending', 0), (1, 'completed', 1)
    ''')
    
    conn.commit()
    conn.close()
    
    print("Banco de teste criado com sucesso")

def run_migration_demo():
    """Executa demonstração completa do sistema de migração"""
    print("=" * 60)
    print("DEMONSTRAÇÃO DO SISTEMA DE MIGRAÇÃO APRIMORADO")
    print("=" * 60)
    
    # Criar diretório temporário
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_database.db")
        
        try:
            # 1. Criar banco de teste
            print("\n1. Criando banco de teste...")
            create_test_database(db_path)
            
            # 2. Executar migração
            print("\n2. Executando migração aprimorada...")
            from scripts.migrar_agendamento_v2 import AgendamentoMigrationManager
            
            migrator = AgendamentoMigrationManager(
                db_path=db_path,
                backup_dir=os.path.join(temp_dir, "backups")
            )
            
            success = migrator.run_migration()
            
            if success:
                print("\nMigração executada com sucesso!")
                
                # 3. Executar validação
                print("\n3. Executando validação...")
                from scripts.validate_agendamento import AgendamentoValidator
                
                validator = AgendamentoValidator(db_path=db_path)
                validation_results = validator.run_full_validation()
                
                if validation_results['overall_success']:
                    print("\nValidação passou em todos os testes!")
                    
                    # 4. Demonstrar funcionalidades
                    print("\n4. Demonstrando funcionalidades...")
                    demonstrate_features(db_path)
                else:
                    print("\nValidação detectou problemas!")
                    
            else:
                print("\nMigração falhou!")
                
        except Exception as e:
            print(f"\nErro durante demonstração: {e}")
            import traceback
            traceback.print_exc()

def demonstrate_features(db_path):
    """Demonstra as funcionalidades do sistema de agendamento"""
    print("Demonstrando criação de agendamentos...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar estrutura da tabela
    cursor.execute("PRAGMA table_info(queue_jobs)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Colunas disponíveis: {', '.join(columns)}")
    
    # Criar agendamento de teste
    from datetime import datetime, timedelta
    
    data_agendada = datetime.now() + timedelta(hours=2)
    
    cursor.execute('''
        INSERT INTO queue_jobs (
            empresa_id, status, prioridade, tipo_execucao,
            data_agendada, recorrencia, ativo_agendamento, criado_por
        ) VALUES (1, 'pending', 1, 'agendada', ?, 'diaria', 1, 'demonstracao')
    ''', (data_agendada.isoformat(),))
    
    agendamento_id = cursor.lastrowid
    
    # Verificar agendamento criado
    cursor.execute('''
        SELECT id, empresa_id, tipo_execucao, data_agendada, recorrencia, ativo_agendamento, criado_por
        FROM queue_jobs WHERE id = ?
    ''', (agendamento_id,))
    
    agendamento = cursor.fetchone()
    
    print(f"Agendamento criado:")
    print(f"  ID: {agendamento[0]}")
    print(f"  Empresa: {agendamento[1]}")
    print(f"  Tipo: {agendamento[2]}")
    print(f"  Data agendada: {agendamento[3]}")
    print(f"  Recorrência: {agendamento[4]}")
    print(f"  Ativo: {agendamento[5]}")
    print(f"  Criado por: {agendamento[6]}")
    
    # Listar todos os jobs
    cursor.execute('''
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN tipo_execucao = 'imediata' THEN 1 END) as imediatos,
               COUNT(CASE WHEN tipo_execucao = 'agendada' THEN 1 END) as agendados
        FROM queue_jobs
    ''')
    
    stats = cursor.fetchone()
    print(f"\nEstatísticas finais:")
    print(f"  Total de jobs: {stats[0]}")
    print(f"  Jobs imediatos: {stats[1]}")
    print(f"  Jobs agendados: {stats[2]}")
    
    conn.close()

if __name__ == "__main__":
    try:
        run_migration_demo()
        print("\n" + "=" * 60)
        print("DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\nDemonstração cancelada pelo usuário")
        
    except Exception as e:
        print(f"\nErro na demonstração: {e}")
        import traceback
        traceback.print_exc()