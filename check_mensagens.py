import sqlite3

conn = sqlite3.connect('sefaz_bot.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM mensagens_sefaz')
count = cursor.fetchone()[0]
print(f'Total de mensagens no banco: {count}')

if count > 0:
    cursor.execute('SELECT id, inscricao_estadual, nome_empresa, assunto, competencia_dief, status_dief FROM mensagens_sefaz LIMIT 1')
    row = cursor.fetchone()
    print(f'\nPrimeira mensagem:')
    print(f'  ID: {row[0]}')
    print(f'  IE: {row[1]}')
    print(f'  Empresa: {row[2]}')
    print(f'  Assunto: {row[3][:60]}...')
    print(f'  Competência DIEF: {row[4]}')
    print(f'  Status DIEF: {row[5]}')
else:
    print('\n❌ Não há mensagens no banco!')

conn.close()
