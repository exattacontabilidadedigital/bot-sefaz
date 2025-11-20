#!/usr/bin/env python3
"""
Script de validação e teste para migração de agendamentos.
Verifica se a migração foi executada corretamente e testa funcionalidades.

Funcionalidades:
- Validação do schema da tabela
- Teste de criação de agendamentos
- Verificação de integridade dos dados
- Relatório de status do sistema
"""

import sqlite3
import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class AgendamentoValidator:
    """Validador para sistema de agendamentos"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.setup_database_path(db_path)
        self.expected_columns = {
            'id': 'INTEGER',
            'empresa_id': 'INTEGER', 
            'status': 'TEXT',
            'prioridade': 'INTEGER',
            'data_adicao': 'TIMESTAMP',
            'data_processamento': 'TIMESTAMP',
            'tentativas': 'INTEGER',
            'max_tentativas': 'INTEGER',
            'erro_detalhes': 'TEXT',
            'data_agendada': 'TIMESTAMP',
            'tipo_execucao': 'TEXT',
            'recorrencia': 'TEXT',
            'ativo_agendamento': 'BOOLEAN',
            'criado_por': 'TEXT'
        }
    
    def setup_database_path(self, db_path: Optional[str] = None):
        """Configura o caminho do banco de dados"""
        if db_path:
            self.db_path = db_path
        elif os.getenv('ENVIRONMENT') == 'production':
            self.db_path = '/data/sefaz_consulta.db'
        else:
            self.db_path = os.getenv('DB_PATH', 'sefaz_consulta.db')
    
    def validate_database_exists(self) -> bool:
        """Valida se o banco de dados existe"""
        if not os.path.exists(self.db_path):
            print(f"❌ Banco de dados não encontrado: {self.db_path}")
            return False
        
        print(f"✅ Banco de dados encontrado: {self.db_path}")
        return True
    
    def validate_table_structure(self) -> Dict[str, Any]:
        """Valida a estrutura da tabela queue_jobs"""
        print("\n🔍 Validando estrutura da tabela queue_jobs...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='queue_jobs'
            """)
            
            if not cursor.fetchone():
                print("❌ Tabela queue_jobs não encontrada")
                return {'success': False, 'error': 'Tabela não encontrada'}
            
            # Obter informações das colunas
            cursor.execute("PRAGMA table_info(queue_jobs)")
            columns_info = cursor.fetchall()
            
            current_columns = {}
            for col in columns_info:
                current_columns[col[1]] = {
                    'type': col[2],
                    'not_null': bool(col[3]),
                    'default_value': col[4],
                    'pk': bool(col[5])
                }
            
            conn.close()
            
            # Verificar colunas esperadas
            missing_columns = []
            extra_columns = []
            
            for expected_col in self.expected_columns:
                if expected_col not in current_columns:
                    missing_columns.append(expected_col)
            
            for current_col in current_columns:
                if current_col not in self.expected_columns:
                    extra_columns.append(current_col)
            
            result = {
                'success': len(missing_columns) == 0,
                'current_columns': current_columns,
                'missing_columns': missing_columns,
                'extra_columns': extra_columns,
                'total_columns': len(current_columns)
            }
            
            if result['success']:
                print(f"✅ Estrutura da tabela válida ({len(current_columns)} colunas)")
            else:
                print(f"❌ Estrutura inválida - {len(missing_columns)} colunas faltando")
                for col in missing_columns:
                    print(f"   - Faltando: {col}")
            
            if extra_columns:
                print(f"ℹ️ Colunas extras encontradas: {', '.join(extra_columns)}")
            
            return result
            
        except Exception as e:
            print(f"❌ Erro ao validar estrutura: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """Valida a integridade dos dados"""
        print("\n🔍 Validando integridade dos dados...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contar registros totais
            cursor.execute("SELECT COUNT(*) FROM queue_jobs")
            total_records = cursor.fetchone()[0]
            
            # Verificar registros com tipo_execucao NULL
            cursor.execute("SELECT COUNT(*) FROM queue_jobs WHERE tipo_execucao IS NULL")
            null_tipo_execucao = cursor.fetchone()[0]
            
            # Verificar registros com ativo_agendamento NULL
            cursor.execute("SELECT COUNT(*) FROM queue_jobs WHERE ativo_agendamento IS NULL")
            null_ativo = cursor.fetchone()[0]
            
            # Verificar registros agendados
            cursor.execute("SELECT COUNT(*) FROM queue_jobs WHERE tipo_execucao = 'agendada'")
            agendados = cursor.fetchone()[0]
            
            # Verificar registros imediatos
            cursor.execute("SELECT COUNT(*) FROM queue_jobs WHERE tipo_execucao = 'imediata'")
            imediatos = cursor.fetchone()[0]
            
            # Verificar registros com data_agendada no futuro
            cursor.execute("""
                SELECT COUNT(*) FROM queue_jobs 
                WHERE tipo_execucao = 'agendada' 
                AND datetime(data_agendada) > datetime('now')
            """)
            futuros = cursor.fetchone()[0]
            
            # Verificar integridade geral do banco
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            conn.close()
            
            result = {
                'success': integrity_result == "ok" and null_tipo_execucao == 0,
                'total_records': total_records,
                'null_tipo_execucao': null_tipo_execucao,
                'null_ativo_agendamento': null_ativo,
                'agendados': agendados,
                'imediatos': imediatos,
                'futuros': futuros,
                'database_integrity': integrity_result
            }
            
            if result['success']:
                print(f"✅ Integridade dos dados válida ({total_records} registros)")
            else:
                print(f"❌ Problemas de integridade detectados")
                if null_tipo_execucao > 0:
                    print(f"   - {null_tipo_execucao} registros com tipo_execucao NULL")
                if integrity_result != "ok":
                    print(f"   - Integridade do banco: {integrity_result}")
            
            print(f"📊 Estatísticas:")
            print(f"   - Total de registros: {total_records}")
            print(f"   - Jobs imediatos: {imediatos}")
            print(f"   - Jobs agendados: {agendados}")
            print(f"   - Jobs futuros: {futuros}")
            
            return result
            
        except Exception as e:
            print(f"❌ Erro ao validar dados: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_create_agendamento(self) -> Dict[str, Any]:
        """Testa a criação de um agendamento"""
        print("\n🧪 Testando criação de agendamento...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se existe uma empresa para teste
            cursor.execute("SELECT id FROM empresas WHERE ativo = 1 LIMIT 1")
            empresa_result = cursor.fetchone()
            
            if not empresa_result:
                print("⚠️ Nenhuma empresa ativa encontrada para teste")
                conn.close()
                return {'success': False, 'error': 'Nenhuma empresa para teste'}
            
            empresa_id = empresa_result[0]
            
            # Criar agendamento de teste
            data_agendada = datetime.now() + timedelta(hours=1)
            
            cursor.execute("""
                INSERT INTO queue_jobs (
                    empresa_id, status, prioridade, tipo_execucao,
                    data_agendada, recorrencia, ativo_agendamento, criado_por
                ) VALUES (?, 'pending', 0, 'agendada', ?, 'unica', 1, 'teste')
            """, (empresa_id, data_agendada.isoformat()))
            
            test_job_id = cursor.lastrowid
            
            # Verificar se foi criado corretamente
            cursor.execute("""
                SELECT empresa_id, tipo_execucao, data_agendada, recorrencia, criado_por
                FROM queue_jobs WHERE id = ?
            """, (test_job_id,))
            
            created_job = cursor.fetchone()
            
            if not created_job:
                raise Exception("Job de teste não foi encontrado após criação")
            
            # Limpar job de teste
            cursor.execute("DELETE FROM queue_jobs WHERE id = ?", (test_job_id,))
            
            conn.commit()
            conn.close()
            
            result = {
                'success': True,
                'test_job_id': test_job_id,
                'empresa_id': empresa_id,
                'data_agendada': data_agendada.isoformat(),
                'created_data': {
                    'empresa_id': created_job[0],
                    'tipo_execucao': created_job[1],
                    'data_agendada': created_job[2],
                    'recorrencia': created_job[3],
                    'criado_por': created_job[4]
                }
            }
            
            print(f"✅ Agendamento de teste criado com sucesso (ID: {test_job_id})")
            print(f"   - Empresa: {empresa_id}")
            print(f"   - Data agendada: {data_agendada.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   - Job removido após teste")
            
            return result
            
        except Exception as e:
            print(f"❌ Erro no teste de criação: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtém status geral do sistema"""
        print("\n📊 Coletando status do sistema...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Estatísticas da fila
            cursor.execute("SELECT status, COUNT(*) FROM queue_jobs GROUP BY status")
            status_counts = dict(cursor.fetchall())
            
            # Estatísticas por tipo
            cursor.execute("SELECT tipo_execucao, COUNT(*) FROM queue_jobs GROUP BY tipo_execucao")
            tipo_counts = dict(cursor.fetchall())
            
            # Jobs agendados ativos para o futuro
            cursor.execute("""
                SELECT COUNT(*) FROM queue_jobs 
                WHERE tipo_execucao = 'agendada' 
                AND ativo_agendamento = 1 
                AND datetime(data_agendada) > datetime('now')
            """)
            agendamentos_futuros = cursor.fetchone()[0]
            
            # Próximo agendamento
            cursor.execute("""
                SELECT data_agendada, empresa_id FROM queue_jobs 
                WHERE tipo_execucao = 'agendada' 
                AND ativo_agendamento = 1 
                AND datetime(data_agendada) > datetime('now')
                ORDER BY data_agendada ASC LIMIT 1
            """)
            proximo_agendamento = cursor.fetchone()
            
            # Total de empresas
            cursor.execute("SELECT COUNT(*) FROM empresas WHERE ativo = 1")
            total_empresas = cursor.fetchone()[0]
            
            conn.close()
            
            status = {
                'database_path': self.db_path,
                'timestamp': datetime.now().isoformat(),
                'queue_status': status_counts,
                'execution_types': tipo_counts,
                'future_schedules': agendamentos_futuros,
                'next_schedule': proximo_agendamento,
                'active_companies': total_empresas,
                'environment': os.getenv('ENVIRONMENT', 'development')
            }
            
            print(f"✅ Status coletado:")
            print(f"   - Ambiente: {status['environment']}")
            print(f"   - Empresas ativas: {total_empresas}")
            print(f"   - Agendamentos futuros: {agendamentos_futuros}")
            
            if proximo_agendamento:
                next_date = datetime.fromisoformat(proximo_agendamento[0].replace('Z', '+00:00'))
                print(f"   - Próximo agendamento: {next_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            print(f"   - Status da fila: {status_counts}")
            print(f"   - Tipos de execução: {tipo_counts}")
            
            return status
            
        except Exception as e:
            print(f"❌ Erro ao coletar status: {e}")
            return {'error': str(e)}
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Executa validação completa do sistema"""
        print("🔍 INICIANDO VALIDAÇÃO COMPLETA DO SISTEMA DE AGENDAMENTOS")
        print("=" * 70)
        
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'database_path': self.db_path,
            'tests': {}
        }
        
        try:
            # 1. Validar existência do banco
            validation_results['tests']['database_exists'] = self.validate_database_exists()
            
            if not validation_results['tests']['database_exists']:
                return validation_results
            
            # 2. Validar estrutura da tabela
            validation_results['tests']['table_structure'] = self.validate_table_structure()
            
            # 3. Validar integridade dos dados
            validation_results['tests']['data_integrity'] = self.validate_data_integrity()
            
            # 4. Testar criação de agendamento
            validation_results['tests']['create_test'] = self.test_create_agendamento()
            
            # 5. Obter status do sistema
            validation_results['system_status'] = self.get_system_status()
            
            # Determinar resultado geral
            all_tests_passed = all([
                validation_results['tests']['database_exists'],
                validation_results['tests']['table_structure']['success'],
                validation_results['tests']['data_integrity']['success'],
                validation_results['tests']['create_test']['success']
            ])
            
            validation_results['overall_success'] = all_tests_passed
            
            # Imprimir resumo
            self._print_validation_summary(validation_results)
            
            return validation_results
            
        except Exception as e:
            print(f"❌ Erro durante validação: {e}")
            validation_results['error'] = str(e)
            validation_results['overall_success'] = False
            return validation_results
    
    def _print_validation_summary(self, results: Dict[str, Any]):
        """Imprime resumo da validação"""
        print("\n" + "=" * 70)
        print("📊 RESUMO DA VALIDAÇÃO")
        print("=" * 70)
        
        if results['overall_success']:
            print("✅ SISTEMA DE AGENDAMENTOS: FUNCIONANDO CORRETAMENTE")
        else:
            print("❌ SISTEMA DE AGENDAMENTOS: PROBLEMAS DETECTADOS")
        
        print(f"\n📂 Banco de dados: {results['database_path']}")
        print(f"⏰ Validação realizada em: {results['timestamp']}")
        
        # Resultados dos testes
        tests = results['tests']
        print(f"\n🧪 Resultados dos testes:")
        print(f"   - Banco existe: {'✅' if tests['database_exists'] else '❌'}")
        print(f"   - Estrutura da tabela: {'✅' if tests['table_structure']['success'] else '❌'}")
        print(f"   - Integridade dos dados: {'✅' if tests['data_integrity']['success'] else '❌'}")
        print(f"   - Teste de criação: {'✅' if tests['create_test']['success'] else '❌'}")
        
        # Status do sistema
        if 'system_status' in results:
            status = results['system_status']
            print(f"\n📊 Status do sistema:")
            print(f"   - Ambiente: {status.get('environment', 'N/A')}")
            print(f"   - Empresas ativas: {status.get('active_companies', 'N/A')}")
            print(f"   - Agendamentos futuros: {status.get('future_schedules', 'N/A')}")
            
            if status.get('next_schedule'):
                next_date = datetime.fromisoformat(status['next_schedule'][0].replace('Z', '+00:00'))
                print(f"   - Próximo agendamento: {next_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("=" * 70)
        
        if not results['overall_success']:
            print("\n⚠️ AÇÕES RECOMENDADAS:")
            if not tests['database_exists']:
                print("   1. Verificar se o banco de dados existe")
            if not tests['table_structure']['success']:
                print("   2. Executar migração para criar colunas faltantes")
            if not tests['data_integrity']['success']:
                print("   3. Corrigir dados inconsistentes")
            if not tests['create_test']['success']:
                print("   4. Verificar permissões e configuração do banco")

def main():
    """Função principal"""
    try:
        # Permitir override do caminho do banco via argumento
        db_path = sys.argv[1] if len(sys.argv) > 1 else None
        
        # Criar validador
        validator = AgendamentoValidator(db_path=db_path)
        
        # Executar validação
        results = validator.run_full_validation()
        
        # Salvar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"validation_report_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Relatório salvo em: {results_file}")
        
        # Retornar código de saída baseado no resultado
        return 0 if results['overall_success'] else 1
        
    except KeyboardInterrupt:
        print("\n❌ Validação cancelada pelo usuário")
        return 1
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())