"""
Arquivo de compatibilidade - Mantém API funcionando na raiz.
A API ainda espera encontrar api.py na raiz do projeto.
"""
from src.api.main import *

if __name__ == "__main__":
    # Importa e executa o servidor
    import sys
    import asyncio
    import uvicorn
    
    # Configuração para Windows
    if sys.platform == 'win32':
        policy_cls = getattr(asyncio, 'WindowsProactorEventLoopPolicy', None)
        if policy_cls:
            asyncio.set_event_loop_policy(policy_cls())
            print("✅ Configurado WindowsProactorEventLoopPolicy para Playwright no Windows")
        else:
            print("⚠️ WindowsProactorEventLoopPolicy indisponível, usando policy padrão")
    
    print("🚀 Iniciando SEFAZ Bot API...")
    print("📊 Interface web disponível em: http://localhost:8000")
    print("📚 Documentação da API em: http://localhost:8000/docs")
    print("\n⏳ Aguardando requisições...")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
