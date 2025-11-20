import sqlite3

# Criar tabela e dados de teste
conn = sqlite3.connect('mensagens_sefaz.db')
cursor = conn.cursor()

# Criar tabela se não existir
cursor.execute('''
CREATE TABLE IF NOT EXISTS mensagens_sefaz (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocolo TEXT,
    assunto TEXT,
    data_envio TEXT,
    data_ciencia TEXT,
    tipo_mensagem TEXT,
    conteudo TEXT,
    anexos TEXT,
    lida BOOLEAN DEFAULT FALSE,
    processada BOOLEAN DEFAULT FALSE,
    inscricao_estadual TEXT,
    nome_empresa TEXT,
    enviada_por TEXT DEFAULT 'SEFAZ-MA',
    status TEXT DEFAULT 'pendente'
)
''')

# Inserir dados de teste
mensagens_teste = [
    {
        'protocolo': 'PROT001',
        'assunto': 'Notificação de Débito',
        'data_envio': '2024-01-15',
        'tipo_mensagem': 'Débito',
        'conteudo': 'Conteúdo da mensagem de débito',
        'inscricao_estadual': '123456789',
        'nome_empresa': 'Empresa ABC Ltda',
        'processada': True
    },
    {
        'protocolo': 'PROT002', 
        'assunto': 'Solicitação de Documentos',
        'data_envio': '2024-01-16',
        'tipo_mensagem': 'Documentação',
        'conteudo': 'Conteúdo da solicitação',
        'inscricao_estadual': '987654321',
        'nome_empresa': 'Empresa XYZ SA',
        'processada': False
    },
    {
        'protocolo': 'PROT003',
        'assunto': 'Comunicado Geral',
        'data_envio': '2024-01-17',
        'data_ciencia': '2024-01-18',
        'tipo_mensagem': 'Comunicado',
        'conteudo': 'Comunicado importante',
        'inscricao_estadual': '555666777',
        'nome_empresa': 'Empresa DEF Ltda',
        'lida': True,
        'processada': True
    }
]

for msg in mensagens_teste:
    cursor.execute('''
        INSERT INTO mensagens_sefaz 
        (protocolo, assunto, data_envio, data_ciencia, tipo_mensagem, conteudo, 
         inscricao_estadual, nome_empresa, lida, processada)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        msg['protocolo'], msg['assunto'], msg['data_envio'], 
        msg.get('data_ciencia'), msg['tipo_mensagem'], msg['conteudo'],
        msg['inscricao_estadual'], msg['nome_empresa'],
        msg.get('lida', False), msg['processada']
    ))

conn.commit()

# Verificar dados inseridos
cursor.execute('SELECT id, assunto, nome_empresa, processada FROM mensagens_sefaz')
print("Mensagens criadas:")
for row in cursor.fetchall():
    status = "Processada" if row[3] else "Não Processada"
    print(f"ID: {row[0]}, Assunto: {row[1]}, Empresa: {row[2]}, Status: {status}")

conn.close()
print("\nDados de teste criados com sucesso!")