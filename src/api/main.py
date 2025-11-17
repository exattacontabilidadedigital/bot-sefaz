# CRITICAL: Set event loop policy FIRST before any other imports
# This ensures Playwright can spawn its helper subprocesses on Windows
import asyncio
import sys
if sys.platform == 'win32' and sys.version_info >= (3, 8):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except AttributeError:
        pass

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import sqlite3
from datetime import datetime
from typing import List, Optional
import json
import os
import hashlib
from src.bot.sefaz_bot import SEFAZBot
from cryptography.fernet import Fernet
import base64
from src.bot.exceptions.error_messages import get_user_friendly_error_message, get_error_category

app = FastAPI(title="SEFAZ Bot API", description="API para consultas SEFAZ", version="1.0.0")

# Montar arquivos estáticos (CSS, JS)
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")

# Rota específica para favicon
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("frontend/favicon.ico")

# Rota para Chrome DevTools (suprime erro 404 nos logs)
@app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
async def chrome_devtools():
    return {}

# Configuração do banco de dados
DB_PATH = os.getenv('DB_PATH', 'sefaz_consulta.db')
DB_MENSAGENS = os.getenv('DB_MENSAGENS', 'sefaz_consulta.db')  # Mesmo banco para mensagens

# Controle de processamento da fila
processing_task = None
processing_active = False

# Configuração da criptografia de senhas - REMOVIDA
def get_encryption_key():
    """Função mantida por compatibilidade - não será mais usada"""
    key_file = "encryption_key.txt"
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        return key

# Inicializar cipher - REMOVIDO
ENCRYPTION_KEY = get_encryption_key()
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_password(password: str) -> str:
    """Retorna a senha sem criptografia"""
    return password

def decrypt_password(encrypted_password: str) -> str:
    """Retorna a senha sem descriptografia"""
    return encrypted_password

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class ConsultaRequest(BaseModel):
    usuario: Optional[str] = None
    senha: Optional[str] = None
    inscricao_estadual: Optional[str] = None  # Inscrição Estadual opcional
    headless: bool = True  # Modo headless (invisível) por padrão

class ConsultaResponse(BaseModel):
    id: int
    nome_empresa: Optional[str]
    cnpj: Optional[str]
    inscricao_estadual: Optional[str]
    cpf_socio: Optional[str]
    chave_acesso: Optional[str]
    status_ie: Optional[str]
    tem_tvi: Optional[str]
    valor_debitos: Optional[float]
    tem_divida_pendente: Optional[str]
    omisso_declaracao: Optional[str]
    inscrito_restritivo: Optional[str]
    data_consulta: str

class EmpresaRequest(BaseModel):
    nome_empresa: str
    cnpj: str
    inscricao_estadual: str
    cpf_socio: str
    senha: Optional[str] = None  # Opcional para updates
    observacoes: Optional[str] = None
    ativo: Optional[bool] = True

class EmpresaResponse(BaseModel):
    id: int
    nome_empresa: str
    cnpj: str
    inscricao_estadual: str
    cpf_socio: str
    data_criacao: str
    data_atualizacao: str
    ativo: bool
    observacoes: Optional[str]

class QueueJobRequest(BaseModel):
    empresa_ids: List[int]
    prioridade: Optional[int] = 0

class QueueJobResponse(BaseModel):
    id: int
    empresa_id: int
    nome_empresa: Optional[str] = None
    cnpj: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    status: str
    prioridade: int
    data_adicao: str
    data_processamento: Optional[str] = None
    tentativas: int
    max_tentativas: int
    erro: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None

class MensagemSefazResponse(BaseModel):
    id: int
    inscricao_estadual: Optional[str]
    cpf_socio: Optional[str]
    enviada_por: Optional[str]
    data_envio: Optional[str]
    assunto: Optional[str]
    classificacao: Optional[str]
    tributo: Optional[str]
    tipo_mensagem: Optional[str]
    numero_documento: Optional[str]
    vencimento: Optional[str]
    tipo_ciencia: Optional[str]
    data_ciencia: Optional[str]
    conteudo_mensagem: Optional[str]
    data_leitura: str

# Status global da consulta
consulta_status = {
    "running": False,
    "message": "Aguardando consulta",
    "progress": 0,
    "current_step": ""
}

# ================================
# ENDPOINTS PARA EMPRESAS
# ================================

@app.post("/api/empresas", response_model=EmpresaResponse)
async def criar_empresa(empresa: EmpresaRequest):
    """Criar nova empresa"""
    try:
        # Validar senha obrigatória na criação
        if not empresa.senha or not empresa.senha.strip():
            raise HTTPException(status_code=400, detail="Senha é obrigatória para criar empresa")
            
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Senha agora é armazenada em texto plano
        senha_texto_plano = empresa.senha
        
        # Verificar se CNPJ já existe
        cursor.execute("SELECT id FROM empresas WHERE cnpj = ?", (empresa.cnpj,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="CNPJ já cadastrado")
        
        # Verificar se IE já existe
        cursor.execute("SELECT id FROM empresas WHERE inscricao_estadual = ?", (empresa.inscricao_estadual,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Inscrição Estadual já cadastrada")
        
        # Inserir empresa
        cursor.execute("""
            INSERT INTO empresas (nome_empresa, cnpj, inscricao_estadual, cpf_socio, senha, observacoes, ativo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (empresa.nome_empresa, empresa.cnpj, empresa.inscricao_estadual,
              empresa.cpf_socio, senha_texto_plano, empresa.observacoes, empresa.ativo))
        
        empresa_id = cursor.lastrowid
        
        # Buscar empresa criada
        cursor.execute("SELECT * FROM empresas WHERE id = ?", (empresa_id,))
        row = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        return EmpresaResponse(
            id=row["id"],
            nome_empresa=row["nome_empresa"],
            cnpj=row["cnpj"],
            inscricao_estadual=row["inscricao_estadual"],
            cpf_socio=row["cpf_socio"],
            data_criacao=row["data_criacao"],
            data_atualizacao=row["data_atualizacao"],
            ativo=bool(row["ativo"]),
            observacoes=row["observacoes"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar empresa: {str(e)}")

@app.get("/api/empresas", response_model=List[EmpresaResponse])
async def listar_empresas(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    ativo: Optional[bool] = None
):
    """Listar empresas com filtros e paginação"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Construir query com filtros
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(nome_empresa LIKE ? OR cnpj LIKE ? OR inscricao_estadual LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
        if ativo is not None:
            where_conditions.append("ativo = ?")
            params.append(ativo)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT * FROM empresas 
            {where_clause}
            ORDER BY data_criacao DESC 
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        conn.close()
        
        empresas = []
        for row in rows:
            empresas.append(EmpresaResponse(
                id=row["id"],
                nome_empresa=row["nome_empresa"],
                cnpj=row["cnpj"],
                inscricao_estadual=row["inscricao_estadual"],
                cpf_socio=row["cpf_socio"],
                data_criacao=row["data_criacao"],
                data_atualizacao=row["data_atualizacao"],
                ativo=bool(row["ativo"]),
                observacoes=row["observacoes"]
            ))
        
        return empresas
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar empresas: {str(e)}")

@app.get("/api/empresas/count")
async def contar_empresas(
    search: Optional[str] = None,
    ativo: Optional[bool] = None
):
    """Contar total de empresas com filtros"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Construir query com filtros
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(nome_empresa LIKE ? OR cnpj LIKE ? OR inscricao_estadual LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
        if ativo is not None:
            where_conditions.append("ativo = ?")
            params.append(ativo)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"SELECT COUNT(*) FROM empresas {where_clause}"
        cursor.execute(query, params)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {"total": total}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao contar empresas: {str(e)}")

@app.get("/api/empresas/template-csv", response_class=FileResponse)
def download_template_csv():
    """Baixar template CSV para importação de empresas"""
    file_path = "empresas_template.csv"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    return FileResponse(
        path=file_path,
        filename="empresas_template.csv",
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=empresas_template.csv"
        }
    )

@app.get("/api/empresas/{empresa_id}", response_model=EmpresaResponse)
async def obter_empresa(empresa_id: int):
    """Obter empresa por ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM empresas WHERE id = ?", (empresa_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        conn.close()
        
        return EmpresaResponse(
            id=row["id"],
            nome_empresa=row["nome_empresa"],
            cnpj=row["cnpj"],
            inscricao_estadual=row["inscricao_estadual"],
            cpf_socio=row["cpf_socio"],
            data_criacao=row["data_criacao"],
            data_atualizacao=row["data_atualizacao"],
            ativo=bool(row["ativo"]),
            observacoes=row["observacoes"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter empresa: {str(e)}")

@app.put("/api/empresas/{empresa_id}", response_model=EmpresaResponse)
async def atualizar_empresa(empresa_id: int, empresa: EmpresaRequest):
    """Atualizar empresa"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verificar se empresa existe
        cursor.execute("SELECT id FROM empresas WHERE id = ?", (empresa_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        # Verificar duplicatas (exceto a própria empresa)
        cursor.execute("SELECT id FROM empresas WHERE cnpj = ? AND id != ?", (empresa.cnpj, empresa_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="CNPJ já cadastrado")
        
        cursor.execute("SELECT id FROM empresas WHERE inscricao_estadual = ? AND id != ?", (empresa.inscricao_estadual, empresa_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Inscrição Estadual já cadastrada")
        
        # Preparar query de atualização
        if empresa.senha and empresa.senha.strip():
            # Atualizar senha se fornecida (texto plano)
            senha_texto_plano = empresa.senha
            cursor.execute("""
                UPDATE empresas SET 
                    nome_empresa = ?, cnpj = ?, inscricao_estadual = ?, cpf_socio = ?, 
                    senha = ?, observacoes = ?, ativo = ?, data_atualizacao = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (empresa.nome_empresa, empresa.cnpj, empresa.inscricao_estadual, 
                  empresa.cpf_socio, senha_texto_plano, empresa.observacoes, empresa.ativo, empresa_id))
        else:
            # Não atualizar senha se não fornecida
            cursor.execute("""
                UPDATE empresas SET 
                    nome_empresa = ?, cnpj = ?, inscricao_estadual = ?, cpf_socio = ?, 
                    observacoes = ?, ativo = ?, data_atualizacao = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (empresa.nome_empresa, empresa.cnpj, empresa.inscricao_estadual, 
                  empresa.cpf_socio, empresa.observacoes, empresa.ativo, empresa_id))
        
        # Buscar empresa atualizada
        cursor.execute("SELECT * FROM empresas WHERE id = ?", (empresa_id,))
        row = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        return EmpresaResponse(
            id=row["id"],
            nome_empresa=row["nome_empresa"],
            cnpj=row["cnpj"],
            inscricao_estadual=row["inscricao_estadual"],
            cpf_socio=row["cpf_socio"],
            data_criacao=row["data_criacao"],
            data_atualizacao=row["data_atualizacao"],
            ativo=bool(row["ativo"]),
            observacoes=row["observacoes"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar empresa: {str(e)}")

@app.delete("/api/empresas/{empresa_id}")
async def excluir_empresa(empresa_id: int):
    """Excluir empresa"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se empresa existe
        cursor.execute("SELECT id FROM empresas WHERE id = ?", (empresa_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        # Verificar se existem consultas vinculadas
        cursor.execute("SELECT COUNT(*) FROM consultas WHERE empresa_id = ?", (empresa_id,))
        total_consultas = cursor.fetchone()[0]
        
        if total_consultas > 0:
            # Apenas desativar ao invés de excluir se houver consultas
            cursor.execute("UPDATE empresas SET ativo = 0 WHERE id = ?", (empresa_id,))
            message = "Empresa desativada (possui consultas vinculadas)"
        else:
            # Excluir permanentemente se não houver consultas
            cursor.execute("DELETE FROM empresas WHERE id = ?", (empresa_id,))
            message = "Empresa excluída com sucesso"
        
        conn.commit()
        conn.close()
        
        return {"message": message, "id": empresa_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir empresa: {str(e)}")

@app.get("/api/empresas/{empresa_id}/credenciais")
async def obter_credenciais_empresa(empresa_id: int):
    """Obter credenciais de login da empresa (CPF e senha)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT cpf_socio, senha, nome_empresa, inscricao_estadual FROM empresas WHERE id = ?", (empresa_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        conn.close()
        
        return {
            "cpf_socio": row["cpf_socio"],
            "senha": row["senha"],
            "nome_empresa": row["nome_empresa"],
            "inscricao_estadual": row["inscricao_estadual"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter credenciais: {str(e)}")

@app.get("/api/empresas/credenciais-por-ie/{inscricao_estadual}")
async def obter_credenciais_por_ie(inscricao_estadual: str):
    """Obter credenciais de login da empresa por Inscrição Estadual"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, cpf_socio, senha, nome_empresa, inscricao_estadual FROM empresas WHERE inscricao_estadual = ?", (inscricao_estadual,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        conn.close()
        
        return {
            "id": row["id"],
            "cpf_socio": row["cpf_socio"],
            "senha": row["senha"],
            "nome_empresa": row["nome_empresa"],
            "inscricao_estadual": row["inscricao_estadual"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter credenciais: {str(e)}")

@app.post("/api/empresas/importar-csv")
async def importar_empresas_csv(request: dict):
    """Importar múltiplas empresas via CSV"""
    try:
        print(f"Recebido request: {request}")
        empresas = request.get('empresas', [])
        print(f"Total de empresas: {len(empresas)}")
        
        if not empresas:
            raise HTTPException(status_code=400, detail="Nenhuma empresa fornecida")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        sucesso = 0
        erros = 0
        detalhes = []
        
        for empresa in empresas:
            try:
                print(f"Processando empresa: {empresa}")
                
                # Validar campos obrigatórios
                nome = empresa.get('nome_empresa', '').strip()
                cnpj = empresa.get('cnpj', '').strip()
                ie = empresa.get('inscricao_estadual', '').strip()
                cpf = empresa.get('cpf_socio', '').strip()
                senha = empresa.get('senha', '').strip()
                obs = empresa.get('observacoes', '').strip()
                
                print(f"Campos: nome={nome}, cnpj={cnpj}, ie={ie}, cpf={cpf}")
                
                if not all([nome, cnpj, ie, cpf, senha]):
                    detalhes.append(f"❌ {nome or cnpj}: campos obrigatórios faltando")
                    erros += 1
                    continue
                
                # Verificar duplicatas no banco
                cursor.execute("SELECT nome_empresa FROM empresas WHERE cnpj = ?", (cnpj,))
                existing = cursor.fetchone()
                if existing:
                    detalhes.append(f"⚠️ {nome} (CNPJ: {cnpj}): já existe no sistema como '{existing[0]}'")
                    erros += 1
                    continue
                
                cursor.execute("SELECT nome_empresa FROM empresas WHERE inscricao_estadual = ?", (ie,))
                existing_ie = cursor.fetchone()
                if existing_ie:
                    detalhes.append(f"⚠️ {nome} (IE: {ie}): já existe no sistema como '{existing_ie[0]}'")
                    erros += 1
                    continue
                
                # Inserir empresa
                cursor.execute("""
                    INSERT INTO empresas (nome_empresa, cnpj, inscricao_estadual, cpf_socio, senha, observacoes, ativo)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (nome, cnpj, ie, cpf, senha, obs))
                
                detalhes.append(f"✓ {nome}: importada com sucesso")
                sucesso += 1
                
            except Exception as e:
                detalhes.append(f"❌ {empresa.get('nome_empresa', 'N/A')}: {str(e)}")
                erros += 1
        
        conn.commit()
        conn.close()
        
        return {
            "sucesso": sucesso,
            "erros": erros,
            "total": len(empresas),
            "detalhes": detalhes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao importar empresas: {str(e)}")

# ================================
# ENDPOINTS ORIGINAIS (CONSULTAS)
# ================================

consulta_status = {
    "running": False,
    "message": "Aguardando consulta",
    "progress": 0,
    "current_step": "",
    "last_result": None
}

@app.get("/")
async def read_root():
    """Serve a página principal"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>❌ Frontend não encontrado</h1><p>Verifique se o diretório 'frontend' existe.</p>",
            status_code=404
        )

@app.get("/api/consultas", response_model=List[ConsultaResponse])
async def get_consultas(
    limit: int = 50, 
    offset: int = 0,
    search: Optional[str] = None,
    status: Optional[str] = None,
    tem_tvi: Optional[str] = None,
    tem_divida: Optional[str] = None
):
    """Retorna consultas com filtros e paginação"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Construir query com filtros
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(c.nome_empresa LIKE ? OR c.inscricao_estadual LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        if status:
            where_conditions.append("c.status_ie = ?")
            params.append(status)
        
        if tem_tvi:
            where_conditions.append("c.tem_tvi = ?")
            params.append(tem_tvi)
        
        if tem_divida:
            where_conditions.append("c.tem_divida_pendente = ?")
            params.append(tem_divida)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Query principal - busca apenas a última consulta de cada empresa (inscricao_estadual)
        query = f"""
            SELECT c.* FROM consultas c
            INNER JOIN (
                SELECT inscricao_estadual, MAX(data_consulta) as max_data
                FROM consultas
                GROUP BY inscricao_estadual
            ) latest ON c.inscricao_estadual = latest.inscricao_estadual 
                   AND c.data_consulta = latest.max_data
            {where_clause}
            ORDER BY c.data_consulta DESC 
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Query para total (para paginação) - conta apenas últimas consultas
        count_query = f"""
            SELECT COUNT(*) FROM (
                SELECT c.* FROM consultas c
                INNER JOIN (
                    SELECT inscricao_estadual, MAX(data_consulta) as max_data
                    FROM consultas
                    GROUP BY inscricao_estadual
                ) latest ON c.inscricao_estadual = latest.inscricao_estadual 
                       AND c.data_consulta = latest.max_data
                {where_clause}
            )
        """
        cursor.execute(count_query, params[:-2])  # Remove limit e offset
        total = cursor.fetchone()[0]
        
        conn.close()
        
        consultas = []
        for row in rows:
            # Formatar tem_tvi para exibição
            tem_tvi_display = row["tem_tvi"]
            if tem_tvi_display:
                try:
                    # Tentar converter para float
                    tvi_valor = float(tem_tvi_display)
                    if tvi_valor > 0:
                        # Formatar como moeda brasileira
                        tem_tvi_display = f"R$ {tvi_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    elif tvi_valor == 0:
                        tem_tvi_display = "NÃO"
                except (ValueError, TypeError):
                    # Se não for número, manter o valor original (SIM, NÃO, ERRO, etc)
                    pass
            
            consulta = ConsultaResponse(
                id=row["id"],
                nome_empresa=row["nome_empresa"],
                cnpj=row["cnpj"],
                inscricao_estadual=row["inscricao_estadual"],
                cpf_socio=row["cpf_socio"],
                chave_acesso=row["chave_acesso"],
                status_ie=row["status_ie"],
                tem_tvi=tem_tvi_display,
                valor_debitos=row["valor_debitos"],
                tem_divida_pendente=row["tem_divida_pendente"],
                omisso_declaracao=row["omisso_declaracao"],
                inscrito_restritivo=row["inscrito_restritivo"],
                data_consulta=row["data_consulta"]
            )
            consultas.append(consulta)
        
        # Adicionar header com total para paginação
        return consultas
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar consultas: {str(e)}")

@app.delete("/api/consultas/{consulta_id}")
async def delete_consulta(consulta_id: int):
    """Exclui uma consulta específica"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se a consulta existe
        cursor.execute("SELECT id FROM consultas WHERE id = ?", (consulta_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Consulta não encontrada")
        
        # Excluir a consulta
        cursor.execute("DELETE FROM consultas WHERE id = ?", (consulta_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Consulta não encontrada")
        
        conn.close()
        
        return {"message": "Consulta excluída com sucesso", "id": consulta_id}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir consulta: {str(e)}")

@app.get("/api/consultas/count")
async def get_consultas_count(
    search: Optional[str] = None,
    status: Optional[str] = None,
    tem_tvi: Optional[str] = None,
    tem_divida: Optional[str] = None
):
    """Retorna o total de consultas com filtros aplicados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Construir query com filtros
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(c.nome_empresa LIKE ? OR c.inscricao_estadual LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        if status:
            where_conditions.append("c.status_ie = ?")
            params.append(status)
        
        if tem_tvi:
            where_conditions.append("c.tem_tvi = ?")
            params.append(tem_tvi)
        
        if tem_divida:
            where_conditions.append("c.tem_divida_pendente = ?")
            params.append(tem_divida)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Contar apenas a última consulta de cada empresa
        query = f"""
            SELECT COUNT(*) FROM (
                SELECT c.* FROM consultas c
                INNER JOIN (
                    SELECT inscricao_estadual, MAX(data_consulta) as max_data
                    FROM consultas
                    GROUP BY inscricao_estadual
                ) latest ON c.inscricao_estadual = latest.inscricao_estadual 
                       AND c.data_consulta = latest.max_data
                {where_clause}
            )
        """
        cursor.execute(query, params)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {"total": total}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao contar consultas: {str(e)}")

# ========================================
# ENDPOINTS DE MENSAGENS SEFAZ
# ========================================

class MensagemResponse(BaseModel):
    id: int
    inscricao_estadual: Optional[str]
    nome_empresa: Optional[str]
    enviada_por: Optional[str]
    data_envio: Optional[str]
    assunto: Optional[str]
    classificacao: Optional[str]
    tributo: Optional[str]
    tipo_mensagem: Optional[str]
    numero_documento: Optional[str]
    vencimento: Optional[str]
    competencia_dief: Optional[str]
    status_dief: Optional[str]
    chave_dief: Optional[str]
    protocolo_dief: Optional[str]
    data_leitura: Optional[str]
    data_ciencia: Optional[str]
    conteudo_mensagem: Optional[str]
    conteudo_html: Optional[str]
    link_recibo: Optional[str]

@app.get("/api/mensagens", response_model=List[MensagemResponse])
async def get_mensagens(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    inscricao_estadual: Optional[str] = None,
    assunto: Optional[str] = None
):
    """Retorna mensagens SEFAZ com filtros e paginação"""
    try:
        print(f"🔍 GET /api/mensagens - Parâmetros recebidos:")
        print(f"   - limit: {limit}")
        print(f"   - offset: {offset}")
        print(f"   - search: {search}")
        print(f"   - inscricao_estadual: {inscricao_estadual}")
        print(f"   - assunto: {assunto}")
        
        conn = sqlite3.connect(DB_MENSAGENS)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Construir query com filtros
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(assunto LIKE ? OR conteudo_mensagem LIKE ? OR nome_empresa LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
        if inscricao_estadual:
            where_conditions.append("inscricao_estadual = ?")
            params.append(inscricao_estadual)
            print(f"   ✓ Filtro IE aplicado: {inscricao_estadual}")
        
        if assunto:
            where_conditions.append("assunto LIKE ?")
            params.append(f"%{assunto}%")
            print(f"   ✓ Filtro assunto aplicado: {assunto}")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT * FROM mensagens_sefaz
            {where_clause}
            ORDER BY data_envio DESC, id DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        print(f"   📋 Query SQL: {query}")
        print(f"   📋 Parâmetros: {params}")
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        print(f"   ✅ Mensagens encontradas: {len(rows)}")
        
        mensagens = []
        for row in rows:
            row_dict = dict(row)
            mensagens.append({
                "id": row_dict["id"],
                "inscricao_estadual": row_dict["inscricao_estadual"],
                "nome_empresa": row_dict.get("nome_empresa"),
                "enviada_por": row_dict["enviada_por"],
                "data_envio": row_dict["data_envio"],
                "assunto": row_dict["assunto"],
                "classificacao": row_dict.get("classificacao"),
                "tributo": row_dict.get("tributo"),
                "tipo_mensagem": row_dict.get("tipo_mensagem"),
                "numero_documento": row_dict.get("numero_documento"),
                "vencimento": row_dict.get("vencimento"),
                "competencia_dief": row_dict.get("competencia_dief"),
                "status_dief": row_dict.get("status_dief"),
                "chave_dief": row_dict.get("chave_dief"),
                "protocolo_dief": row_dict.get("protocolo_dief"),
                "data_leitura": row_dict.get("data_leitura"),
                "data_ciencia": row_dict.get("data_ciencia"),
                "conteudo_mensagem": row_dict["conteudo_mensagem"],
                "conteudo_html": row_dict.get("conteudo_html"),
                "link_recibo": row_dict.get("link_recibo")
            })
        
        conn.close()
        return mensagens
    
    except Exception as e:
        import traceback
        error_detail = f"Erro ao buscar mensagens: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ ERRO NO ENDPOINT /api/mensagens:")
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar mensagens: {str(e)}")

@app.get("/api/mensagens/count")
async def get_mensagens_count(
    search: Optional[str] = None,
    inscricao_estadual: Optional[str] = None,
    assunto: Optional[str] = None
):
    """Retorna o total de mensagens"""
    try:
        print(f"🔍 GET /api/mensagens/count - Parâmetros:")
        print(f"   - inscricao_estadual: {inscricao_estadual}")
        print(f"   - assunto: {assunto}")
        
        conn = sqlite3.connect(DB_MENSAGENS)
        cursor = conn.cursor()
        
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(assunto LIKE ? OR conteudo_mensagem LIKE ? OR nome_empresa LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
        if inscricao_estadual:
            where_conditions.append("inscricao_estadual = ?")
            params.append(inscricao_estadual)
        
        if assunto:
            where_conditions.append("assunto LIKE ?")
            params.append(f"%{assunto}%")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"SELECT COUNT(*) FROM mensagens_sefaz {where_clause}"
        cursor.execute(query, params)
        total = cursor.fetchone()[0]
        
        conn.close()
        return {"total": total}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao contar mensagens: {str(e)}")

@app.get("/api/mensagens/empresas")
async def listar_empresas_mensagens():
    """Lista empresas únicas que têm mensagens"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT DISTINCT 
                inscricao_estadual,
                nome_empresa
            FROM mensagens_sefaz 
            WHERE inscricao_estadual IS NOT NULL 
                AND inscricao_estadual != ''
                AND nome_empresa IS NOT NULL
            ORDER BY nome_empresa
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        empresas = []
        for row in rows:
            empresas.append({
                "inscricao_estadual": row["inscricao_estadual"],
                "nome_empresa": row["nome_empresa"]
            })
        
        return empresas
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar empresas: {str(e)}")

@app.get("/api/mensagens/{mensagem_id}", response_model=MensagemResponse)
async def get_mensagem(mensagem_id: int):
    """Retorna uma mensagem específica pelo ID"""
    try:
        conn = sqlite3.connect(DB_MENSAGENS)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM mensagens_sefaz WHERE id = ?", (mensagem_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Mensagem não encontrada")
        
        row_dict = dict(row)
        mensagem = {
            "id": row_dict["id"],
            "inscricao_estadual": row_dict["inscricao_estadual"],
            "nome_empresa": row_dict.get("nome_empresa"),
            "enviada_por": row_dict["enviada_por"],
            "data_envio": row_dict["data_envio"],
            "assunto": row_dict["assunto"],
            "classificacao": row_dict.get("classificacao"),
            "tributo": row_dict.get("tributo"),
            "tipo_mensagem": row_dict.get("tipo_mensagem"),
            "numero_documento": row_dict.get("numero_documento"),
            "vencimento": row_dict.get("vencimento"),
            "competencia_dief": row_dict.get("competencia_dief"),
            "status_dief": row_dict.get("status_dief"),
            "chave_dief": row_dict.get("chave_dief"),
            "protocolo_dief": row_dict.get("protocolo_dief"),
            "data_leitura": row_dict.get("data_leitura"),
            "data_ciencia": row_dict.get("data_ciencia"),
            "conteudo_mensagem": row_dict["conteudo_mensagem"],
            "conteudo_html": row_dict.get("conteudo_html"),
            "link_recibo": row_dict.get("link_recibo")
        }
        
        conn.close()
        return mensagem
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar mensagem: {str(e)}")

# ========================================
# FIM ENDPOINTS DE MENSAGENS SEFAZ
# ========================================

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Retorna o status atual da consulta"""
    return StatusResponse(
        status="success" if not consulta_status["running"] else "running",
        message=consulta_status["message"],
        data={
            "running": consulta_status["running"],
            "progress": consulta_status["progress"],
            "current_step": consulta_status["current_step"],
            "last_result": consulta_status["last_result"]
        }
    )

@app.post("/api/consulta", response_model=StatusResponse)
async def executar_consulta(request: ConsultaRequest, background_tasks: BackgroundTasks):
    """Executa uma nova consulta em background"""
    global consulta_status
    
    if consulta_status["running"]:
        raise HTTPException(status_code=400, detail="Já existe uma consulta em execução")
    
    # Iniciar consulta em background
    background_tasks.add_task(
        run_consulta_background, 
        request.usuario, 
        request.senha, 
        request.inscricao_estadual,
        request.headless
    )
    
    consulta_status["running"] = True
    consulta_status["message"] = "Consulta iniciada"
    consulta_status["progress"] = 0
    consulta_status["current_step"] = "Iniciando..."
    
    return StatusResponse(
        status="success",
        message="Consulta iniciada com sucesso",
        data={"running": True}
    )

async def run_consulta_background(usuario: Optional[str], senha: Optional[str], inscricao_estadual: Optional[str] = None, headless: bool = True):
    """Executa a consulta em background"""
    global consulta_status
    
    try:
        consulta_status["current_step"] = "Inicializando bot..."
        consulta_status["progress"] = 10
        
        # Configurar modo headless via variável de ambiente
        os.environ['HEADLESS'] = 'true' if headless else 'false'
        bot = SEFAZBot()
        
        consulta_status["current_step"] = "Fazendo login..."
        consulta_status["progress"] = 20
        
        resultado = await bot.executar_consulta(usuario, senha, inscricao_estadual)
        
        consulta_status["progress"] = 100
        
        if resultado:
            consulta_status["message"] = "Consulta realizada com sucesso!"
            consulta_status["current_step"] = "Concluído"
            consulta_status["last_result"] = resultado
        else:
            consulta_status["message"] = "Falha na consulta"
            consulta_status["current_step"] = "Erro"
            
    except Exception as e:
        consulta_status["message"] = f"Erro: {str(e)}"
        consulta_status["current_step"] = "Erro"
        consulta_status["progress"] = 0
    
    finally:
        consulta_status["running"] = False

@app.get("/api/estatisticas")
async def get_estatisticas():
    """Retorna estatísticas das consultas (apenas últimas consultas por empresa)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Subquery para últimas consultas
        latest_query = """
            SELECT c.* FROM consultas c
            INNER JOIN (
                SELECT inscricao_estadual, MAX(data_consulta) as max_data
                FROM consultas
                GROUP BY inscricao_estadual
            ) latest ON c.inscricao_estadual = latest.inscricao_estadual 
                   AND c.data_consulta = latest.max_data
        """
        
        # Total de consultas (últimas por empresa)
        cursor.execute(f"SELECT COUNT(*) FROM ({latest_query})")
        total_consultas = cursor.fetchone()[0]
        
        # Empresas ativas
        cursor.execute(f"SELECT COUNT(*) FROM ({latest_query}) WHERE status_ie = 'ATIVO'")
        empresas_ativas = cursor.fetchone()[0]
        
        # Empresas com dívidas
        cursor.execute(f"SELECT COUNT(*) FROM ({latest_query}) WHERE valor_debitos > 0")
        empresas_com_dividas = cursor.fetchone()[0]
        
        # Empresas com TVIs
        cursor.execute(f"SELECT COUNT(*) FROM ({latest_query}) WHERE tem_tvi = 'SIM'")
        empresas_com_tvis = cursor.fetchone()[0]
        
        # Valor total de dívidas
        cursor.execute(f"SELECT SUM(valor_debitos) FROM ({latest_query}) WHERE valor_debitos > 0")
        valor_total_dividas = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_consultas": total_consultas,
            "empresas_ativas": empresas_ativas,
            "empresas_com_dividas": empresas_com_dividas,
            "empresas_com_tvis": empresas_com_tvis,
            "valor_total_dividas": valor_total_dividas,
            "percentual_ativas": round((empresas_ativas / total_consultas * 100) if total_consultas > 0 else 0, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular estatísticas: {str(e)}")

# Endpoints da Fila de Processamento
@app.post("/api/fila/adicionar", response_model=dict)
async def adicionar_fila(request: QueueJobRequest, background_tasks: BackgroundTasks):
    """Adiciona empresas à fila de processamento"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        job_ids = []
        for empresa_id in request.empresa_ids:
            # Verificar se a empresa existe
            cursor.execute("SELECT id FROM empresas WHERE id = ? AND ativo = 1", (empresa_id,))
            if not cursor.fetchone():
                print(f"❌ Empresa {empresa_id} não encontrada ou inativa")
                raise HTTPException(status_code=404, detail=f"Empresa com ID {empresa_id} não encontrada ou inativa")
            
            # Verificar se já existe um job pendente para esta empresa
            cursor.execute("""
                SELECT id FROM queue_jobs 
                WHERE empresa_id = ? AND status IN ('pending', 'running')
            """, (empresa_id,))
            
            existing_job = cursor.fetchone()
            if existing_job:
                print(f"⚠️ Empresa {empresa_id} já tem job pendente/em execução (ID: {existing_job[0]})")
                continue  # Pular se já existe job pendente/executando
            
            print(f"➕ Adicionando empresa {empresa_id} à fila")
            
            # Adicionar à fila (sem especificar data_adicao, deixar o DEFAULT CURRENT_TIMESTAMP)
            try:
                cursor.execute("""
                    INSERT INTO queue_jobs (empresa_id, status, prioridade, tentativas, max_tentativas)
                    VALUES (?, 'pending', ?, 0, 3)
                """, (empresa_id, request.prioridade))
                
                job_ids.append(cursor.lastrowid)
                print(f"✅ Job ID {cursor.lastrowid} criado com sucesso")
            except Exception as insert_error:
                print(f"❌ ERRO AO INSERIR: {type(insert_error).__name__}: {insert_error}")
                import traceback
                traceback.print_exc()
                raise
        
        conn.commit()
        conn.close()
        
        # Iniciar processamento automaticamente se houver jobs adicionados
        global processing_active
        print(f"🔍 DEBUG: job_ids={job_ids}, len={len(job_ids)}, processing_active={processing_active}")
        if len(job_ids) > 0 and not processing_active:
            processing_active = True
            print(f"✅ Iniciando processamento automático da fila...")
            background_tasks.add_task(processar_fila)
        else:
            print(f"⚠️ Não iniciou: job_ids vazio={len(job_ids)==0}, já processando={processing_active}")
        
        return {
            "message": f"{len(job_ids)} empresas adicionadas à fila",
            "job_ids": job_ids
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar à fila: {str(e)}")

@app.get("/api/fila", response_model=List[QueueJobResponse])
async def listar_fila(limit: int = 50, offset: int = 0):
    """Lista jobs na fila"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                qj.id,
                qj.empresa_id,
                e.nome_empresa,
                e.cnpj,
                e.inscricao_estadual,
                qj.status,
                qj.prioridade,
                qj.data_adicao,
                qj.data_processamento,
                qj.tentativas,
                qj.max_tentativas,
                qj.erro_detalhes
            FROM queue_jobs qj
            JOIN empresas e ON qj.empresa_id = e.id
            ORDER BY qj.data_adicao DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        jobs = []
        for row in cursor.fetchall():
            erro_original = row[11]
            erro_amigavel = get_user_friendly_error_message(erro_original) if erro_original else None
            
            jobs.append({
                "id": row[0],
                "empresa_id": row[1],
                "nome_empresa": row[2],
                "cnpj": row[3],
                "inscricao_estadual": row[4],
                "status": row[5],
                "prioridade": row[6],
                "data_adicao": row[7],
                "data_processamento": row[8],
                "tentativas": row[9],
                "max_tentativas": row[10],
                "erro": erro_amigavel
            })
        
        conn.close()
        return jobs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar fila: {str(e)}")

@app.get("/api/fila/stats")
async def stats_fila():
    """Estatísticas da fila"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT status, COUNT(*) FROM queue_jobs GROUP BY status")
        stats = dict(cursor.fetchall())
        
        conn.close()
        
        # Retornar com os nomes reais do banco de dados (em inglês)
        # O banco usa: pending, running, completed, failed
        pending = stats.get("pending", 0)
        completed = stats.get("completed", 0)
        failed = stats.get("failed", 0)
        running = stats.get("running", 0)
        
        return {
            "pendente": pending,
            "processando": running,
            "concluido": completed,
            "erro": failed,
            "total": pending + running + completed + failed
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas da fila: {str(e)}")

async def processar_fila():
    """Processa a fila de jobs sequencialmente"""
    global processing_active
    
    # Garantir que estamos usando a WindowsProactorEventLoopPolicy, necessária para asyncio subprocess
    if sys.platform == 'win32' and sys.version_info >= (3, 8):
        try:
            policy_cls = getattr(asyncio, 'WindowsProactorEventLoopPolicy', None)
            if policy_cls:
                current_policy = asyncio.get_event_loop_policy()
                if not isinstance(current_policy, policy_cls):
                    print(f"⚠️ Alterando event loop policy de {current_policy.__class__.__name__} para WindowsProactorEventLoopPolicy")
                    asyncio.set_event_loop_policy(policy_cls())
                    print("✅ Event loop policy alterada com sucesso")
            else:
                print("⚠️ WindowsProactorEventLoopPolicy não está disponível nesta versão do Python")
        except Exception as e:
            print(f"⚠️ Aviso ao configurar event loop policy: {e}")
    
    print(f"🚀 ========================================")
    print(f"🚀 INICIANDO processar_fila()")
    print(f"🚀 processing_active={processing_active}")
    print(f"🚀 ========================================")
    
    try:
        while processing_active:
            print(f"🔄 Loop: Buscando próximo job pendente...")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Buscar próximo job pendente
            cursor.execute("""
                SELECT qj.id, qj.empresa_id, e.nome_empresa, e.cpf_socio, e.inscricao_estadual, e.senha
                FROM queue_jobs qj
                JOIN empresas e ON qj.empresa_id = e.id
                WHERE qj.status = 'pending' AND qj.tentativas < qj.max_tentativas
                ORDER BY qj.prioridade DESC, qj.data_adicao ASC
                LIMIT 1
            """)
            
            job = cursor.fetchone()
            if not job:
                conn.close()
                print(f"⏸️ Nenhum job pendente encontrado. Aguardando 5 segundos...")
                # Aguardar 5 segundos antes de verificar novamente
                await asyncio.sleep(5)
                continue
            
            job_id, empresa_id, empresa_nome, cpf_socio, inscricao_estadual, senha = job
            print(f"✅ Job encontrado: ID={job_id}, Empresa={empresa_nome} (ID={empresa_id})")
            
            # Marcar como executando
            print(f"🔄 Marcando job {job_id} como 'running'...")
            cursor.execute("""
                UPDATE queue_jobs 
                SET status = 'running', data_processamento = datetime('now'), tentativas = tentativas + 1
                WHERE id = ?
            """, (job_id,))
            conn.commit()
            conn.close()
            
            print(f"🔄 Processando job {job_id} - Empresa: {empresa_nome}")
            
            # Executar consulta
            try:
                # Senha já está em texto plano
                senha_texto_plano = senha
                
                # Logs detalhados para debug - SENHA COMPLETA
                print(f"📋 Dados da empresa - DEBUG COMPLETO:")
                print(f"   • ID: {empresa_id}")
                print(f"   • Nome: {empresa_nome}")
                print(f"   • IE: {inscricao_estadual}")
                print(f"   • CPF (usuário login): {cpf_socio}")
                print(f"   • Senha do banco: '{senha}'")
                print(f"   • Senha texto plano: '{senha_texto_plano}'")
                print(f"   • Tipo da senha: {type(senha_texto_plano)}")
                print(f"   • Tamanho da senha: {len(senha_texto_plano)}")
                print(f"   • Representação da senha: {repr(senha_texto_plano)}")
                print(f"🚀 Enviando para bot:")
                print(f"   • Parâmetro 1 (CPF): '{cpf_socio}' (tipo: {type(cpf_socio)})")
                print(f"   • Parâmetro 2 (Senha): '{senha_texto_plano}' (tipo: {type(senha_texto_plano)})")
                print(f"   • Parâmetro 3 (IE): '{inscricao_estadual}' (tipo: {type(inscricao_estadual)})")
                
                # Bot sempre em modo headless na fila
                os.environ['HEADLESS'] = 'true'
                bot = SEFAZBot()
                resultado = await bot.executar_consulta(cpf_socio, senha_texto_plano, inscricao_estadual)
                
                # Atualizar status
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                if resultado:
                    cursor.execute("""
                        UPDATE queue_jobs 
                        SET status = 'completed', data_processamento = datetime('now')
                        WHERE id = ?
                    """, (job_id,))
                    print(f"✅ Job {job_id} concluído com sucesso")
                else:
                    cursor.execute("""
                        UPDATE queue_jobs 
                        SET status = 'failed', erro_detalhes = 'Falha na execução da consulta'
                        WHERE id = ?
                    """, (job_id,))
                    print(f"❌ Job {job_id} falhou")
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                print(f"❌ Erro no job {job_id}: {str(e)}")
                
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Verificar se deve tentar novamente
                cursor.execute("SELECT tentativas, max_tentativas FROM queue_jobs WHERE id = ?", (job_id,))
                tentativas, max_tentativas = cursor.fetchone()
                
                if tentativas >= max_tentativas:
                    cursor.execute("""
                        UPDATE queue_jobs 
                        SET status = 'failed', erro_detalhes = ?
                        WHERE id = ?
                    """, (str(e), job_id))
                else:
                    cursor.execute("""
                        UPDATE queue_jobs 
                        SET status = 'pending', erro_detalhes = ?
                        WHERE id = ?
                    """, (str(e), job_id))
                
                conn.commit()
                conn.close()
            
            # Pequeno delay entre jobs
            await asyncio.sleep(2)
    
    except Exception as e:
        print(f"❌ Erro no processamento da fila: {str(e)}")

# ================================
# ENDPOINTS DE CONTROLE DA FILA
# ================================

@app.post("/api/fila/iniciar")
async def iniciar_processamento(background_tasks: BackgroundTasks):
    """Inicia o processamento da fila"""
    global processing_active
    
    if processing_active:
        return {"message": "Processamento já está ativo", "processando": True}
    
    processing_active = True
    background_tasks.add_task(processar_fila)
    
    return {"message": "Processamento iniciado", "processando": True}

@app.post("/api/fila/parar")
async def parar_processamento():
    """Para o processamento da fila"""
    global processing_active
    
    if not processing_active:
        return {"message": "Processamento já está parado", "processando": False}
    
    processing_active = False
    
    return {"message": "Processamento será pausado após o job atual", "processando": False}

@app.delete("/api/fila/{job_id}")
async def deletar_job(job_id: int):
    """Deleta um job da fila (apenas se não estiver processando)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se o job existe e não está em processamento
        cursor.execute("SELECT status FROM queue_jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        
        if not job:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
        
        if job[0] == 'running':
            conn.close()
            raise HTTPException(status_code=400, detail="Não é possível deletar um job em processamento")
        
        # Deletar o job
        cursor.execute("DELETE FROM queue_jobs WHERE id = ?", (job_id,))
        conn.commit()
        conn.close()
        
        return {"message": f"Job {job_id} deletado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar job: {str(e)}")

@app.post("/api/fila/cancelar/{job_id}")
async def cancelar_job(job_id: int):
    """Cancela um job em execução"""
    try:
        from datetime import datetime
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se o job existe
        cursor.execute("SELECT status FROM queue_jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        
        if not job:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
        
        # Data atual formatada
        data_processamento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Atualizar status para failed (cancelado)
        cursor.execute("""
            UPDATE queue_jobs 
            SET status = 'failed', 
                erro_detalhes = 'Cancelado pelo usuário',
                data_processamento = ?
            WHERE id = ?
        """, (data_processamento, job_id))
        
        conn.commit()
        conn.close()
        
        return {"message": f"Job {job_id} cancelado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Erro ao cancelar job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar job: {str(e)}")

@app.get("/api/fila/status")
async def status_processamento():
    """Retorna o status do processamento"""
    return {
        "processando": processing_active
    }

@app.post("/api/fila/limpar-travados")
async def limpar_jobs_travados():
    """Limpa jobs travados (pendentes ou processando há muito tempo)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Marcar como failed jobs que estão processando há mais de 1 hora
        cursor.execute("""
            UPDATE queue_jobs 
            SET status = 'failed', 
                erro_detalhes = 'Job travado - limpeza automática',
                data_fim = datetime('now')
            WHERE status IN ('pendente', 'processando')
            AND (
                data_inicio IS NULL 
                OR datetime(data_inicio, '+1 hour') < datetime('now')
            )
        """)
        
        jobs_limpos = cursor.rowcount
        conn.commit()
        conn.close()
        
        return {
            "message": f"{jobs_limpos} job(s) travado(s) limpo(s) com sucesso",
            "jobs_limpos": jobs_limpos
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar jobs travados: {str(e)}")

# ================================
# ENDPOINTS PARA MENSAGENS SEFAZ
# ================================

@app.get("/api/mensagens", response_model=List[MensagemSefazResponse])
async def listar_mensagens(
    limit: int = 50, 
    offset: int = 0,
    inscricao_estadual: Optional[str] = None,
    cpf_socio: Optional[str] = None,
    assunto: Optional[str] = None
):
    """Lista mensagens SEFAZ processadas"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Construir query com filtros
        where_conditions = []
        params = []
        
        if inscricao_estadual:
            where_conditions.append("inscricao_estadual = ?")
            params.append(inscricao_estadual)
        
        if cpf_socio:
            where_conditions.append("cpf_socio = ?")
            params.append(cpf_socio)
        
        if assunto:
            where_conditions.append("assunto LIKE ?")
            params.append(f"%{assunto}%")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Query com limit e offset
        query = f"""
            SELECT * FROM mensagens_sefaz 
            {where_clause}
            ORDER BY data_leitura DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        mensagens = []
        for row in rows:
            mensagens.append(MensagemSefazResponse(
                id=row["id"],
                inscricao_estadual=row["inscricao_estadual"],
                cpf_socio=row["cpf_socio"],
                enviada_por=row["enviada_por"],
                data_envio=row["data_envio"],
                assunto=row["assunto"],
                classificacao=row["classificacao"],
                tributo=row["tributo"],
                tipo_mensagem=row["tipo_mensagem"],
                numero_documento=row["numero_documento"],
                vencimento=row["vencimento"],
                tipo_ciencia=row["tipo_ciencia"],
                data_ciencia=row["data_ciencia"],
                conteudo_mensagem=row["conteudo_mensagem"],
                data_leitura=row["data_leitura"]
            ))
        
        conn.close()
        return mensagens
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar mensagens: {str(e)}")


@app.get("/api/mensagens/count")
async def contar_mensagens(
    inscricao_estadual: Optional[str] = None,
    cpf_socio: Optional[str] = None
):
    """Conta total de mensagens"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        where_conditions = []
        params = []
        
        if inscricao_estadual:
            where_conditions.append("inscricao_estadual = ?")
            params.append(inscricao_estadual)
        
        if cpf_socio:
            where_conditions.append("cpf_socio = ?")
            params.append(cpf_socio)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"SELECT COUNT(*) FROM mensagens_sefaz {where_clause}"
        cursor.execute(query, params)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {"total": total}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao contar mensagens: {str(e)}")


# Servir arquivos estáticos do frontend
try:
    # Montar diretórios CSS e JS diretamente
    app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
    app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
except Exception as e:
    print(f"Aviso: Não foi possível montar arquivos estáticos: {e}")

if __name__ == "__main__":
    import uvicorn
    
    # CRITICAL: Forçar WindowsProactorEventLoopPolicy ANTES do Uvicorn criar o loop
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
