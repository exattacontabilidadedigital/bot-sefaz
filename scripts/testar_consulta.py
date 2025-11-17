"""
Script para testar consulta adicionando empresa à fila
"""
import requests
import time
import json

API_URL = "http://localhost:8000"

def adicionar_empresa_fila(empresa_id):
    """Adiciona empresa à fila"""
    url = f"{API_URL}/api/fila/adicionar"
    payload = {"empresa_id": empresa_id}
    
    print(f"➕ Adicionando empresa {empresa_id} à fila...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Empresa adicionada! Job ID: {data.get('job_id')}")
        return data.get('job_id')
    else:
        print(f"❌ Erro ao adicionar: {response.status_code}")
        print(response.text)
        return None

def verificar_status_job(job_id):
    """Verifica status de um job"""
    url = f"{API_URL}/api/fila/{job_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    return None

def iniciar_processamento():
    """Inicia o processamento da fila"""
    url = f"{API_URL}/api/fila/iniciar"
    print("🚀 Iniciando processamento da fila...")
    response = requests.post(url)
    
    if response.status_code == 200:
        print("✅ Processamento iniciado!")
        return True
    else:
        print(f"❌ Erro ao iniciar: {response.status_code}")
        return False

def monitorar_job(job_id, max_tempo=120):
    """Monitora execução do job"""
    print(f"\n📊 Monitorando Job {job_id}...")
    print("="*60)
    
    tempo_inicio = time.time()
    ultimo_status = None
    
    while time.time() - tempo_inicio < max_tempo:
        job = verificar_status_job(job_id)
        
        if job:
            status = job.get('status')
            
            if status != ultimo_status:
                tempo_decorrido = int(time.time() - tempo_inicio)
                print(f"[{tempo_decorrido}s] Status: {status}")
                ultimo_status = status
            
            # Se completou ou falhou, mostrar resultado
            if status == 'completed':
                print("\n✅ JOB COMPLETADO COM SUCESSO!")
                print("="*60)
                print(json.dumps(job, indent=2, ensure_ascii=False))
                return True
            
            elif status == 'failed':
                print("\n❌ JOB FALHOU!")
                print("="*60)
                erro = job.get('erro_mensagem', 'Erro desconhecido')
                print(f"Erro: {erro}")
                print(json.dumps(job, indent=2, ensure_ascii=False))
                return False
        
        time.sleep(2)  # Aguardar 2 segundos antes de verificar novamente
    
    print(f"\n⏰ Timeout após {max_tempo} segundos")
    return False

def main():
    """Executa teste completo"""
    print("="*60)
    print("🧪 TESTE DE CONSULTA SEFAZ")
    print("="*60)
    
    # Empresa THAÍS BRITO (ID 7)
    empresa_id = 7
    
    # Adicionar à fila
    job_id = adicionar_empresa_fila(empresa_id)
    
    if not job_id:
        print("❌ Não foi possível adicionar empresa à fila")
        return
    
    # Aguardar um pouco
    time.sleep(2)
    
    # Iniciar processamento
    if not iniciar_processamento():
        print("❌ Não foi possível iniciar processamento")
        return
    
    # Monitorar execução
    sucesso = monitorar_job(job_id, max_tempo=180)  # 3 minutos max
    
    print("\n" + "="*60)
    if sucesso:
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("❌ TESTE FALHOU")
    print("="*60)

if __name__ == "__main__":
    main()
