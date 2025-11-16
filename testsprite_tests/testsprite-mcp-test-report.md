# Relatório de Teste Testsprite — consulta-ie

## Contexto
- Projeto backend em `Python/FastAPI` servindo estáticos do diretório `frontend`.
- Porta esperada: `8000` (definida em `Dockerfile:28` e `start.sh:42`).
- Serviço local não estava em execução durante os testes; instalação via `pip` falhou por dependência `pydantic-core` (build Rust).

## Requisitos e Casos de Teste
- Disponibilidade da API (`HTTP 200` em `GET /api/status`).
- Estatísticas disponíveis (`GET /api/estatisticas`).
- Listagem de empresas (`GET /api/empresas`).
- Documentação acessível (`GET /docs`).

## Execução
- Tentativa de execução automática do Testsprite falhou ao abrir túnel por ausência de serviço local em `http://localhost:8000`.
- Mensagem chave: "Because the local project is not running on port 8000".

## Resultado
- Todos os casos acima falharam por erro de conexão (serviço não iniciado).

## Como corrigir para próxima execução
- Instalar dependências e iniciar servidor:
  - Com Docker: `docker build -t consulta-ie . && docker run -p 8000:8000 consulta-ie`.
  - Sem Docker (pode exigir Rust>=1.65 para `pydantic-core` com Python 3.13): `python -m pip install -r requirements.txt` e `python -m uvicorn api:app --host 0.0.0.0 --port 8000`.
- Confirmar disponibilidade em `http://localhost:8000/api/status` e `http://localhost:8000/docs`.
- Reexecutar o Testsprite.

## Observações
- Endpoints principais implementados em `api.py`, incluindo `Empresas`, `Consultas`, `Fila`, `Mensagens`, `Status/Estatísticas`.
- Banco de dados `SQLite` acessado via `DB_PATH`.
