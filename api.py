from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
import asyncio
from datetime import datetime
from typing import List, Optional
import json
import os
import hashlib
from bot import SEFAZBot
from cryptography.fernet import Fernet
import base64

app = FastAPI(title="SEFAZ Bot API", description="API para consultas SEFAZ", version="1.0.0")

# Configuração do banco de dados
DB_PATH = "sefaz_consulta.db"

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
            
        conn = sqlite3.connect("sefaz_consulta.db")
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
        conn = sqlite3.connect("sefaz_consulta.db")
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
        conn = sqlite3.connect("sefaz_consulta.db")
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

@app.get("/api/empresas/{empresa_id}", response_model=EmpresaResponse)
async def obter_empresa(empresa_id: int):
    """Obter empresa por ID"""
    try:
        conn = sqlite3.connect("sefaz_consulta.db")
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
        conn = sqlite3.connect("sefaz_consulta.db")
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
        conn = sqlite3.connect("sefaz_consulta.db")
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
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

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
        conn = sqlite3.connect("sefaz_consulta.db")
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
            consulta = ConsultaResponse(
                id=row["id"],
                nome_empresa=row["nome_empresa"],
                cnpj=row["cnpj"],
                inscricao_estadual=row["inscricao_estadual"],
                cpf_socio=row["cpf_socio"],
                chave_acesso=row["chave_acesso"],
                status_ie=row["status_ie"],
                tem_tvi=row["tem_tvi"],
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
        conn = sqlite3.connect("sefaz_consulta.db")
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
        conn = sqlite3.connect("sefaz_consulta.db")
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
        conn = sqlite3.connect("sefaz_consulta.db")
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
            
            # Adicionar à fila
            cursor.execute("""
                INSERT INTO queue_jobs (empresa_id, status, prioridade, data_criacao, tentativas, max_tentativas)
                VALUES (?, 'pending', ?, datetime('now'), 0, 3)
            """, (empresa_id, request.prioridade))
            
            job_ids.append(cursor.lastrowid)
        
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
                qj.data_criacao,
                qj.data_inicio,
                qj.tentativas,
                qj.max_tentativas,
                qj.erro_detalhes
            FROM queue_jobs qj
            JOIN empresas e ON qj.empresa_id = e.id
            ORDER BY qj.data_criacao DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        jobs = []
        for row in cursor.fetchall():
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
                "erro": row[11]
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
    
    print(f"🚀 INICIANDO processar_fila() - processing_active={processing_active}")
    
    try:
        while processing_active:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Buscar próximo job pendente
            cursor.execute("""
                SELECT qj.id, qj.empresa_id, e.nome_empresa, e.cpf_socio, e.inscricao_estadual, e.senha
                FROM queue_jobs qj
                JOIN empresas e ON qj.empresa_id = e.id
                WHERE qj.status = 'pending' AND qj.tentativas < qj.max_tentativas
                ORDER BY qj.prioridade DESC, qj.data_criacao ASC
                LIMIT 1
            """)
            
            job = cursor.fetchone()
            if not job:
                conn.close()
                # Aguardar 5 segundos antes de verificar novamente
                await asyncio.sleep(5)
                continue
            
            job_id, empresa_id, empresa_nome, cpf_socio, inscricao_estadual, senha = job
            
            # Marcar como executando
            cursor.execute("""
                UPDATE queue_jobs 
                SET status = 'running', data_inicio = datetime('now'), tentativas = tentativas + 1
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
                        SET status = 'completed', data_conclusao = datetime('now')
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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se o job existe
        cursor.execute("SELECT status FROM queue_jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        
        if not job:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
        
        # Atualizar status para failed
        cursor.execute("""
            UPDATE queue_jobs 
            SET status = 'failed', 
                erro_detalhes = 'Cancelado pelo usuário',
                data_fim = datetime('now')
            WHERE id = ?
        """, (job_id,))
        
        conn.commit()
        conn.close()
        
        return {"message": f"Job {job_id} cancelado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar job: {str(e)}")

@app.get("/api/fila/status")
async def status_processamento():
    """Retorna o status do processamento"""
    return {
        "processando": processing_active
    }

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


@app.get("/api/mensagens/{mensagem_id}", response_model=MensagemSefazResponse)
async def obter_mensagem(mensagem_id: int):
    """Obtém uma mensagem específica"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM mensagens_sefaz WHERE id = ?", (mensagem_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Mensagem não encontrada")
        
        mensagem = MensagemSefazResponse(
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
        )
        
        conn.close()
        return mensagem
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter mensagem: {str(e)}")

# Servir arquivos estáticos do frontend
try:
    # Montar diretórios CSS e JS diretamente
    app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
    app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
except Exception as e:
    print(f"Aviso: Não foi possível montar arquivos estáticos: {e}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando SEFAZ Bot API...")
    print("📊 Interface web disponível em: http://localhost:8000")
    print("📚 Documentação da API em: http://localhost:8000/docs")
    print("\n⏳ Aguardando requisições...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")