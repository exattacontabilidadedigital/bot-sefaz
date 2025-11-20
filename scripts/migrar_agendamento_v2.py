#!/usr/bin/env python3
"""
Script de migração aprimorado para adicionar campos de agendamento à tabela queue_jobs.
Este script adiciona suporte para execuções programadas com robustez e segurança.

Melhorias implementadas:
- Backup automático antes da migração
- Validação de integridade de dados
- Rollback automático em caso de erro
- Logging detalhado
- Validação de ambiente
- Verificação de dependências
- Relatórios de progresso

Versão: 2.0
Autor: Sistema de Migração Automatizado
"""

import sqlite3
import os
import shutil
import logging
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

class DatabaseMigrationError(Exception):
    """Exceção customizada para erros de migração"""
    pass

class AgendamentoMigrationManager:
    """Gerenciador de migração para campos de agendamento"""
    
    def __init__(self, db_path: Optional[str] = None, backup_dir: Optional[str] = None):
        self.setup_environment(db_path, backup_dir)
        self.setup_logging()
        self.migration_version = "2.0"
        self.required_columns = {
            'data_agendada': 'TIMESTAMP',
            'tipo_execucao': "TEXT DEFAULT 'imediata'",
            'recorrencia': 'TEXT',
            'ativo_agendamento': 'BOOLEAN DEFAULT 1',
            'criado_por': "TEXT DEFAULT 'manual'"
        }
        
    def setup_environment(self, db_path: Optional[str] = None, backup_dir: Optional[str] = None):
        """Configura o ambiente de migração"""
        # Determinar caminho do banco
        if db_path:
            self.db_path = db_path
        elif os.getenv('ENVIRONMENT') == 'production':
            os.makedirs('/data', exist_ok=True)
            self.db_path = '/data/sefaz_consulta.db'
        else:
            self.db_path = os.getenv('DB_PATH', 'sefaz_consulta.db')
        
        # Configurar diretório de backup
        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            self.backup_dir = Path('backups')
        
        self.backup_dir.mkdir(exist_ok=True)
        
        # Definir caminho do backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = self.backup_dir / f"sefaz_consulta_backup_{timestamp}.db"
        
    def setup_logging(self):
        """Configura o sistema de logging"""
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        
        # Configurar logging para arquivo
        log_file = self.backup_dir / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Configurar handlers separadamente para evitar problemas de encoding
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # Configurar logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def validate_environment(self) -> bool:
        """Valida o ambiente antes da migração"""
        self.logger.info("Validando ambiente de migração...")
        
        try:
            # Verificar se o banco existe
            if not os.path.exists(self.db_path):
                raise DatabaseMigrationError(f"Banco de dados não encontrado: {self.db_path}")
            
            # Verificar permissões de leitura/escrita
            if not os.access(self.db_path, os.R_OK | os.W_OK):
                raise DatabaseMigrationError(f"Permissões insuficientes para o banco: {self.db_path}")
            
            # Verificar espaço em disco
            db_dir = os.path.dirname(self.db_path) or '.'
            if os.path.exists(db_dir):
                stat = shutil.disk_usage(db_dir)
                free_space_mb = stat.free / (1024 * 1024)
                
                if free_space_mb < 100:  # 100MB mínimo
                    raise DatabaseMigrationError(f"Espaço insuficiente em disco: {free_space_mb:.2f}MB disponível")
            else:
                # Se diretório não existe, criar
                os.makedirs(db_dir, exist_ok=True)
            
            # Verificar integridade do banco
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            conn.close()
            
            if integrity_result != "ok":
                raise DatabaseMigrationError(f"Integridade do banco comprometida: {integrity_result}")
            
            self.logger.info("Ambiente validado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Falha na validação do ambiente: {e}")
            raise DatabaseMigrationError(f"Ambiente inválido: {e}")
    
    def create_backup(self) -> bool:
        """Cria backup do banco de dados"""
        self.logger.info(f"Criando backup em: {self.backup_path}")
        
        try:
            # Criar backup usando SQLite backup API
            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(str(self.backup_path))
            
            source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            # Verificar integridade do backup
            backup_conn = sqlite3.connect(str(self.backup_path))
            cursor = backup_conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            backup_conn.close()
            
            if integrity_result != "ok":
                raise DatabaseMigrationError(f"Backup corrompido: {integrity_result}")
            
            backup_size = os.path.getsize(self.backup_path)
            self.logger.info(f"Backup criado com sucesso ({backup_size / 1024:.2f}KB)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Falha ao criar backup: {e}")
            raise DatabaseMigrationError(f"Erro no backup: {e}")
    
    def get_current_schema(self) -> Dict[str, Any]:
        """Obtém o schema atual da tabela queue_jobs"""
        self.logger.info("Analisando schema atual...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='queue_jobs'
            """)
            
            if not cursor.fetchone():
                raise DatabaseMigrationError("Tabela queue_jobs não encontrada")
            
            # Obter informações das colunas
            cursor.execute("PRAGMA table_info(queue_jobs)")
            columns_info = cursor.fetchall()
            
            # Obter contagem de registros
            cursor.execute("SELECT COUNT(*) FROM queue_jobs")
            record_count = cursor.fetchone()[0]
            
            # Obter índices
            cursor.execute("PRAGMA index_list(queue_jobs)")
            indexes = cursor.fetchall()
            
            conn.close()
            
            schema = {
                'columns': {col[1]: {'type': col[2], 'nullable': not col[3], 'default': col[4]} 
                           for col in columns_info},
                'record_count': record_count,
                'indexes': [idx[1] for idx in indexes if not idx[2]]  # Excluir índices automáticos
            }
            
            self.logger.info(f"Schema atual: {len(schema['columns'])} colunas, {record_count} registros")
            return schema
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao analisar schema: {e}")
            raise DatabaseMigrationError(f"Falha na análise do schema: {e}")
    
    def check_migration_needed(self, current_schema: Dict[str, Any]) -> bool:
        """Verifica se a migração é necessária"""
        existing_columns = set(current_schema['columns'].keys())
        required_columns = set(self.required_columns.keys())
        missing_columns = required_columns - existing_columns
        
        if not missing_columns:
            self.logger.info("Todas as colunas já existem - migração não necessária")
            return False
        
        self.logger.info(f"Migração necessária - colunas faltantes: {', '.join(missing_columns)}")
        return True
    
    def execute_migration(self, current_schema: Dict[str, Any]) -> bool:
        """Executa a migração das colunas"""
        self.logger.info("Iniciando migração das colunas...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Iniciar transação
            cursor.execute("BEGIN TRANSACTION")
            
            existing_columns = set(current_schema['columns'].keys())
            columns_added = []
            
            # Adicionar colunas faltantes
            for column_name, column_def in self.required_columns.items():
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE queue_jobs ADD COLUMN {column_name} {column_def}"
                        cursor.execute(sql)
                        columns_added.append(column_name)
                        self.logger.info(f"Coluna '{column_name}' adicionada")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" not in str(e).lower():
                            raise e
                        self.logger.info(f"Coluna '{column_name}' já existe")
            
            # Atualizar registros existentes com valores padrão
            updates_made = self._update_existing_records(cursor, current_schema['record_count'])
            
            # Commit da transação
            conn.commit()
            conn.close()
            
            self.logger.info(f"Migração concluída - {len(columns_added)} colunas adicionadas, {updates_made} registros atualizados")
            return True
            
        except Exception as e:
            # Rollback em caso de erro
            try:
                conn.rollback()
                conn.close()
            except:
                pass
                
            self.logger.error(f"❌ Erro durante migração: {e}")
            raise DatabaseMigrationError(f"Falha na migração: {e}")
    
    def _update_existing_records(self, cursor: sqlite3.Cursor, record_count: int) -> int:
        """Atualiza registros existentes com valores padrão"""
        if record_count == 0:
            return 0
        
        updates_made = 0
        
        # Atualizar tipo_execucao para 'imediata' onde NULL
        cursor.execute("""
            UPDATE queue_jobs 
            SET tipo_execucao = 'imediata' 
            WHERE tipo_execucao IS NULL
        """)
        updates_made += cursor.rowcount
        
        # Atualizar ativo_agendamento para 1 onde NULL
        cursor.execute("""
            UPDATE queue_jobs 
            SET ativo_agendamento = 1 
            WHERE ativo_agendamento IS NULL
        """)
        updates_made += cursor.rowcount
        
        # Atualizar criado_por para 'manual' onde NULL
        cursor.execute("""
            UPDATE queue_jobs 
            SET criado_por = 'manual' 
            WHERE criado_por IS NULL
        """)
        updates_made += cursor.rowcount
        
        return updates_made
    
    def validate_migration(self) -> bool:
        """Valida se a migração foi bem-sucedida"""
        self.logger.info("Validando migração...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se todas as colunas foram criadas
            cursor.execute("PRAGMA table_info(queue_jobs)")
            columns = {col[1]: col[2] for col in cursor.fetchall()}
            
            missing_columns = []
            for column_name in self.required_columns.keys():
                if column_name not in columns:
                    missing_columns.append(column_name)
            
            if missing_columns:
                raise DatabaseMigrationError(f"Colunas não criadas: {', '.join(missing_columns)}")
            
            # Verificar integridade dos dados
            cursor.execute("SELECT COUNT(*) FROM queue_jobs WHERE tipo_execucao IS NULL")
            null_tipo_execucao = cursor.fetchone()[0]
            
            if null_tipo_execucao > 0:
                self.logger.warning(f"⚠️ {null_tipo_execucao} registros com tipo_execucao NULL")
            
            # Verificar integridade do banco
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            if integrity_result != "ok":
                raise DatabaseMigrationError(f"Integridade comprometida: {integrity_result}")
            
            conn.close()
            
            self.logger.info("Validação concluída com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Falha na validação: {e}")
            raise DatabaseMigrationError(f"Validação falhou: {e}")
    
    def generate_migration_report(self, start_time: datetime, current_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Gera relatório da migração"""
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Obter schema final
        final_schema = self.get_current_schema()
        
        report = {
            'migration_version': self.migration_version,
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'database_path': self.db_path,
            'backup_path': str(self.backup_path),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'before': {
                'columns': len(current_schema['columns']),
                'records': current_schema['record_count']
            },
            'after': {
                'columns': len(final_schema['columns']),
                'records': final_schema['record_count']
            },
            'columns_added': list(set(final_schema['columns'].keys()) - set(current_schema['columns'].keys())),
            'success': True
        }
        
        # Salvar relatório
        report_file = self.backup_dir / f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📊 Relatório salvo em: {report_file}")
        return report
    
    def rollback_migration(self) -> bool:
        """Executa rollback da migração usando backup"""
        self.logger.info(f"Iniciando rollback usando backup: {self.backup_path}")
        
        try:
            if not os.path.exists(self.backup_path):
                raise DatabaseMigrationError(f"Backup não encontrado: {self.backup_path}")
            
            # Verificar integridade do backup
            backup_conn = sqlite3.connect(str(self.backup_path))
            cursor = backup_conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            backup_conn.close()
            
            if integrity_result != "ok":
                raise DatabaseMigrationError(f"Backup corrompido: {integrity_result}")
            
            # Restaurar backup
            shutil.copy2(self.backup_path, self.db_path)
            
            self.logger.info("Rollback concluído com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Falha no rollback: {e}")
            raise DatabaseMigrationError(f"Rollback falhou: {e}")
    
    def run_migration(self) -> bool:
        """Executa o processo completo de migração"""
        start_time = datetime.now()
        self.logger.info(f"Iniciando migração de agendamentos - Versão {self.migration_version}")
        self.logger.info(f"Banco: {self.db_path}")
        
        try:
            # 1. Validar ambiente
            self.validate_environment()
            
            # 2. Obter schema atual
            current_schema = self.get_current_schema()
            
            # 3. Verificar se migração é necessária
            if not self.check_migration_needed(current_schema):
                self.logger.info("Migração não necessária - sistema já atualizado")
                return True
            
            # 4. Criar backup
            self.create_backup()
            
            # 5. Executar migração
            self.execute_migration(current_schema)
            
            # 6. Validar migração
            self.validate_migration()
            
            # 7. Gerar relatório
            report = self.generate_migration_report(start_time, current_schema)
            
            self.logger.info("Migração concluída com sucesso!")
            self._print_migration_summary(report)
            
            return True
            
        except DatabaseMigrationError:
            # Tentar rollback automático
            try:
                if hasattr(self, 'backup_path') and os.path.exists(self.backup_path):
                    self.logger.error("Tentando rollback automático...")
                    self.rollback_migration()
            except:
                self.logger.error("Rollback automático falhou")
            
            raise
        
        except Exception as e:
            self.logger.error(f"Erro inesperado durante migração: {e}")
            raise DatabaseMigrationError(f"Migração falhou: {e}")
    
    def _print_migration_summary(self, report: Dict[str, Any]):
        """Imprime resumo da migração"""
        print("\n" + "="*60)
        print("RESUMO DA MIGRAÇÃO DE AGENDAMENTOS")
        print("="*60)
        print(f"Status: Concluída com sucesso")
        print(f"Duração: {report['duration_seconds']:.2f}s")
        print(f"Banco: {report['database_path']}")
        print(f"Backup: {report['backup_path']}")
        print(f"Ambiente: {report['environment']}")
        print(f"Colunas antes: {report['before']['columns']}")
        print(f"Colunas depois: {report['after']['columns']}")
        print(f"Registros: {report['after']['records']}")
        
        if report['columns_added']:
            print(f"Colunas adicionadas:")
            for col in report['columns_added']:
                print(f"   - {col}")
        
        print("\nConfiguração de persistência:")
        if report['environment'] == 'production':
            print("   - Modo produção: dados persistirão em volume Docker")
        else:
            print("   - Modo desenvolvimento: dados locais")
        
        print("\nFuncionalidades habilitadas:")
        print("   - Agendamento de execuções")
        print("   - Recorrência (única, diária, semanal, mensal)")
        print("   - Controle de ativação/desativação")
        print("   - Rastreamento de origem dos jobs")
        print("="*60)

def main():
    """Função principal do script"""
    try:
        # Permitir override do caminho do banco via argumento
        db_path = sys.argv[1] if len(sys.argv) > 1 else None
        
        # Criar instância do migrador
        migrator = AgendamentoMigrationManager(db_path=db_path)
        
        # Executar migração
        migrator.run_migration()
        
        return 0
        
    except KeyboardInterrupt:
        print("\nMigração cancelada pelo usuário")
        return 1
        
    except DatabaseMigrationError as e:
        print(f"\nErro de migração: {e}")
        return 1
        
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())