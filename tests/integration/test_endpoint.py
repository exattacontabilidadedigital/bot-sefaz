import requests
import json

# Testar endpoint de mensagens
try:
    print("Testando endpoint /api/mensagens...")
    response = requests.get("http://localhost:8000/api/mensagens?limit=5")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Sucesso! {len(data)} mensagens retornadas")
        print(json.dumps(data[0], indent=2))
    else:
        print(f"Erro: {response.status_code}")
        print(f"Resposta: {response.text}")
        
except Exception as e:
    print(f"Erro na requisição: {e}")

# Testar endpoint de count
print("\n" + "="*50)
print("Testando endpoint /api/mensagens/count...")
try:
    response = requests.get("http://localhost:8000/api/mensagens/count")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Count: {response.json()}")
except Exception as e:
    print(f"Erro: {e}")
