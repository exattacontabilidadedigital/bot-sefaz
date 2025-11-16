import requests
import json

try:
    # Testar endpoint de count
    print("=" * 60)
    print("Testando /api/mensagens/count")
    print("=" * 60)
    response = requests.get("http://localhost:8000/api/mensagens/count")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Testar endpoint de listagem
    print("\n" + "=" * 60)
    print("Testando /api/mensagens?limit=5")
    print("=" * 60)
    response = requests.get("http://localhost:8000/api/mensagens?limit=5")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Tipo de resposta: {type(data)}")
        print(f"Quantidade de mensagens: {len(data)}")
        
        if len(data) > 0:
            print(f"\n{'='*60}")
            print("Primeira mensagem:")
            print(f"{'='*60}")
            msg = data[0]
            print(json.dumps(msg, indent=2, ensure_ascii=False))
        else:
            print("\n❌ Array vazio retornado!")
    else:
        print(f"❌ Erro: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Erro na requisição: {e}")
    import traceback
    traceback.print_exc()
