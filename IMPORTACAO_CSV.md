# 📥 Importação de Empresas via CSV

## Como Usar

### 1. Acessar o Modal de Nova Empresa
- Na aba **Empresas**, clique no botão **"+ Nova Empresa"**
- No modal que abrir, clique na aba **"Importar CSV"**

### 2. Baixar o Template CSV
- Clique no link **"Baixar modelo CSV"** para obter o arquivo template
- O arquivo `empresas_template.csv` será baixado

### 3. Preencher o CSV
O arquivo CSV deve conter as seguintes colunas (obrigatórias):

```csv
nome_empresa,cnpj,inscricao_estadual,cpf_socio,senha,observacoes
```

#### Formato de cada coluna:

| Coluna | Formato | Exemplo | Obrigatória |
|--------|---------|---------|-------------|
| `nome_empresa` | Texto | EMPRESA EXEMPLO LTDA | ✅ Sim |
| `cnpj` | Texto (com ou sem formatação) | 12.345.678/0001-90 ou 12345678000190 | ✅ Sim |
| `inscricao_estadual` | Texto/Número | 123456789 | ✅ Sim |
| `cpf_socio` | Texto (com ou sem formatação) | 123.456.789-01 ou 12345678901 | ✅ Sim |
| `senha` | Texto | SenhaTeste123 | ✅ Sim |
| `observacoes` | Texto | Empresa de teste | ❌ Não |

### 4. Exemplo de CSV Válido

```csv
nome_empresa,cnpj,inscricao_estadual,cpf_socio,senha,observacoes
COMERCIO ABC LTDA,12.345.678/0001-90,123456789,123.456.789-01,Senha123,Cliente ativo
INDUSTRIA XYZ SA,98.765.432/0001-10,987654321,987.654.321-09,OutraSenha456,Novo cadastro
SERVICOS DEF ME,11.222.333/0001-44,111222333,111.222.333-44,Senha789,
```

### 5. Importar o Arquivo

1. **Selecionar arquivo**: Clique em "Selecionar arquivo" ou arraste o CSV para a área de upload
2. **Preview**: Uma prévia das primeiras 5 linhas será exibida automaticamente
3. **Validação**: O sistema mostra quantas empresas serão importadas
4. **Importar**: Clique no botão **"Importar Empresas"**

### 6. Resultado da Importação

Após a importação, você verá um resumo:

- ✅ **Sucessos**: Quantas empresas foram importadas
- ❌ **Erros**: Quantas empresas falharam
- 📋 **Detalhes**: Lista detalhada com status de cada empresa

#### Possíveis erros:

| Erro | Causa | Solução |
|------|-------|---------|
| "Campos obrigatórios faltando" | Alguma coluna obrigatória está vazia | Preencher todas as colunas obrigatórias |
| "CNPJ já cadastrado" | Empresa com mesmo CNPJ já existe | Verificar duplicatas no banco |
| "IE já cadastrada" | Inscrição Estadual já existe | Verificar duplicatas no banco |
| "Arquivo CSV com colunas inválidas" | Cabeçalho do CSV incorreto | Usar o template fornecido |

## Dicas

- ✨ O arquivo aceita CNPJ e CPF com ou sem formatação (pontos/traços)
- 📝 A coluna `observacoes` pode ficar vazia
- 🚫 CNPJs e IEs duplicadas serão ignoradas (não substituem registros existentes)
- 📊 Recomenda-se importar no máximo 100 empresas por vez para melhor desempenho
- 💾 O CSV deve estar codificado em UTF-8

## Exemplo Completo de Uso

1. Baixe o template: `empresas_template.csv`
2. Abra no Excel/Google Sheets/Editor de texto
3. Preencha com os dados das suas empresas
4. Salve como CSV (UTF-8)
5. Arraste o arquivo para a área de upload
6. Verifique a preview
7. Clique em "Importar Empresas"
8. Aguarde a confirmação
9. As empresas aparecem automaticamente na lista

## API Endpoint

Para integração programática:

```bash
POST /api/empresas/importar-csv
Content-Type: application/json

{
  "empresas": [
    {
      "nome_empresa": "EMPRESA EXEMPLO LTDA",
      "cnpj": "12345678000190",
      "inscricao_estadual": "123456789",
      "cpf_socio": "12345678901",
      "senha": "SenhaTeste123",
      "observacoes": "Empresa de teste"
    }
  ]
}
```

**Resposta:**
```json
{
  "sucesso": 1,
  "erros": 0,
  "total": 1,
  "detalhes": [
    "✓ EMPRESA EXEMPLO LTDA: importada com sucesso"
  ]
}
```

## Solução de Problemas

### Arquivo não carrega
- Verifique se o arquivo tem extensão `.csv`
- Confirme que o arquivo não excede 5MB
- Certifique-se de que está usando vírgula (`,`) como separador

### Nenhuma empresa importada
- Verifique se o cabeçalho está correto
- Confirme que há dados além do cabeçalho
- Verifique se não há linhas vazias no meio do arquivo

### Caracteres especiais aparecem errados
- Salve o arquivo como CSV UTF-8
- No Excel: "Salvar Como" → Escolher "CSV UTF-8"
