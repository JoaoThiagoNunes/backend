# Índice de Documentação de Rotas

Este documento lista todas as documentações disponíveis para as rotas da API PROFIN.

---

## 📚 Documentações Disponíveis

### 1. [Rotas de Administração](DOC_ROTAS_ADMIN.md)
**Arquivo:** `src/modules/routes/admin_routes.py`  
**Prefixo:** `/admin`

Rotas para:
- Autenticação (login)
- Status do sistema
- Health check
- Limpeza de dados

**Principais rotas:**
- `GET /admin/` - Endpoint raiz
- `POST /admin/login` - Autenticação
- `GET /admin/status-dados` - Status do banco
- `GET /admin/health` - Health check
- `DELETE /admin/limpar-dados` - Limpar dados

---

### 2. [Rotas de Anos Letivos](DOC_ROTAS_ANOS.md)
**Arquivo:** `src/modules/routes/ano_routes.py`  
**Prefixo:** `/anos`

Rotas para:
- Gerenciamento de anos letivos
- Criação e arquivamento de anos
- Listagem de anos

**Principais rotas:**
- `GET /anos` - Listar todos os anos
- `GET /anos/ativo` - Obter ano ativo
- `POST /anos` - Criar novo ano
- `PUT /anos/{ano_id}/arquivar` - Arquivar ano
- `DELETE /anos/{ano_id}` - Deletar ano

---

### 3. [Rotas de Uploads](DOC_ROTAS_UPLOADS.md)
**Arquivo:** `src/modules/routes/upload_routes.py`  
**Prefixo:** `/uploads`

Rotas para:
- Upload de arquivos Excel/CSV
- Listagem de uploads
- Detalhes de uploads

**Principais rotas:**
- `GET /uploads` - Listar uploads
- `GET /uploads/{upload_id}` - Detalhes de upload
- `POST /uploads/excel` - Upload de arquivo

---

### 4. [Rotas de Cálculos](DOC_ROTAS_CALCULOS.md)
**Arquivo:** `src/modules/routes/calculos_routes.py`  
**Prefixo:** `/calculos`

Rotas para:
- Cálculo de valores PROFIN
- Cotas calculadas por escola

**Principais rotas:**
- `POST /calculos` - Calcular valores

---

### 5. [Rotas de Parcelas](DOC_ROTAS_PARCELAS.md)
**Arquivo:** `src/modules/routes/parcelas_routes.py`  
**Prefixo:** `/parcelas`

Rotas para:
- Divisão de valores em parcelas
- Parcelas por tipo de ensino
- Consulta de parcelas por escola
- Liberação manual por parcela/folha
- Consolidação para repasse financeiro

**Principais rotas:**
- `POST /parcelas` - Criar parcelas
- `GET /parcelas/escola/{escola_id}` - Parcelas de uma escola
- `POST /parcelas/liberar` - Liberar escolas por parcela/folha
- `GET /parcelas/previsao` - Previsão para liberação
- `GET /parcelas/repasse` - Dados para repasse

---

### 6. [Rotas de Complemento](DOC_ROTAS_COMPLEMENTO.md)
**Arquivo:** `src/modules/features/complemento/routes.py`  
**Prefixo:** `/complemento`

Rotas para:
- Upload e processamento de planilhas de complemento de alunos
- Cálculo de valores de complemento baseado em diferenças de alunos
- Gerenciamento de folhas (sheets) para liberação
- Consulta de histórico de complementos por escola
- Resumo agrupado por folhas para repasse financeiro

**Principais rotas:**
- `POST /complemento/upload` - Upload de planilha de complemento
- `POST /complemento/separar` - Separar complementos por tipo de ensino (fundamental/médio) ⭐ **NOVO**
- `GET /complemento/repasse` - Resumo agrupado por folhas
- `GET /complemento/{complemento_upload_id}` - Detalhes de um upload
- `GET /complemento/escola/{escola_id}` - Histórico de uma escola
- `POST /complemento/liberar` - Liberar escolas para folha
- `GET /complemento/liberacoes` - Listar liberações
- `PUT /complemento/liberacoes/{liberacao_id}` - Atualizar liberação

---

## 🔄 Fluxo de Trabalho Completo

### 1. Configuração Inicial

```bash
# Criar ano letivo
POST /anos
{
  "ano": 2026
}
```

### 2. Upload de Dados

```bash
# Upload de arquivo Excel/CSV
POST /uploads/excel
# FormData: file + ano_letivo_id (opcional)
```

### 3. Calcular Valores

```bash
# Calcular cotas PROFIN
POST /calculos
# Query: ano_letivo_id (opcional)
```

### 4. Criar Parcelas

```bash
# Dividir em parcelas e por tipo de ensino
POST /parcelas
{
  "recalcular": false,
  "ano_letivo_id": null
}
```

### 5. Consultar Dados

```bash
# Ver parcelas de uma escola
GET /parcelas/escola/{escola_id}

# Ver detalhes de um upload
GET /uploads/{upload_id}

# Ver status do sistema
GET /admin/status-dados
```

---

## 📊 Mapa de Rotas

```
/admin
├── GET  /                    # Endpoint raiz
├── POST /login              # Autenticação
├── GET  /status-dados       # Status do banco
├── GET  /health             # Health check
└── DELETE /limpar-dados     # Limpar dados

/anos
├── GET  /                    # Listar anos
├── GET  /ativo              # Ano ativo
├── POST /                    # Criar ano
├── PUT  /{ano_id}/arquivar  # Arquivar ano
└── DELETE /{ano_id}         # Deletar ano

/uploads
├── GET  /                    # Listar uploads
├── GET  /{upload_id}        # Detalhes de upload
└── POST /excel              # Upload de arquivo

/calculos
└── POST /                    # Calcular valores

/parcelas
├── POST /                      # Criar parcelas
├── POST /liberar               # Liberar escolas por parcela/folha
├── GET  /liberacoes            # Listar liberações
├── PUT  /liberacoes/{id}       # Atualizar liberação
├── DELETE /liberacoes/{id}     # Resetar liberação
├── GET  /escola/{id}           # Parcelas de escola
├── GET  /escola/{id}/liberacoes# Liberações por escola
├── GET  /folha/{parcela}/{folha} # Liberações por folha
├── GET  /previsao              # Previsão de liberação
└── GET  /repasse               # Consolidação para repasse

/complemento
├── POST   /upload                    # Upload de planilha
├── POST   /separar                   # Separar por tipo de ensino ⭐ NOVO
├── GET    /repasse                   # Resumo agrupado por folhas
├── GET    /                          # Listar uploads (paginado)
├── GET    /{complemento_upload_id}   # Detalhes de um upload
├── GET    /escola/{escola_id}        # Histórico de uma escola
├── POST   /liberar                   # Liberar escolas para folha
├── GET    /liberacoes                # Listar liberações
└── PUT    /liberacoes/{liberacao_id} # Atualizar liberação
```

---

## 🔗 Links Rápidos

- [Documentação Completa - Admin](DOC_ROTAS_ADMIN.md)
- [Documentação Completa - Anos](DOC_ROTAS_ANOS.md)
- [Documentação Completa - Uploads](DOC_ROTAS_UPLOADS.md)
- [Documentação Completa - Cálculos](DOC_ROTAS_CALCULOS.md)
- [Documentação Completa - Parcelas](DOC_ROTAS_PARCELAS.md)
- [Documentação Completa - Complemento](DOC_ROTAS_COMPLEMENTO.md)
- [Documentação Frontend - Separação de Complementos](../frontend/DOC_FRONTEND_SEPARACAO_COMPLEMENTO.md) ⭐ **NOVO**

---

## 📝 Notas Gerais

1. **Base URL:** `http://localhost:8000` (desenvolvimento)

2. **Autenticação:** Apenas `DELETE /admin/limpar-dados` requer autenticação JWT.

3. **Formato de Resposta:** Todas as rotas retornam JSON.

4. **Códigos de Erro:**
   - `200 OK`: Sucesso
   - `400 Bad Request`: Requisição inválida
   - `401 Unauthorized`: Não autenticado
   - `404 Not Found`: Recurso não encontrado
   - `500 Internal Server Error`: Erro interno

5. **Isolamento por Ano:** Dados são isolados por ano letivo. Cada ano mantém seus próprios uploads, escolas, cálculos e parcelas.

---

## 🚀 Quick Start

```bash
# 1. Criar ano letivo
curl -X POST http://localhost:8000/anos \
  -H "Content-Type: application/json" \
  -d '{"ano": 2026}'

# 2. Upload de arquivo
curl -X POST http://localhost:8000/uploads/excel \
  -F "file=@escolas_2026.xlsx"

# 3. Calcular valores
curl -X POST http://localhost:8000/calculos

# 4. Criar parcelas
curl -X POST http://localhost:8000/parcelas \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

**Última atualização:** 2026-03-11

**Novidades:**
- ✅ Separação de complementos por tipo de ensino (fundamental/médio) - Ver [Documentação Frontend](../frontend/DOC_FRONTEND_SEPARACAO_COMPLEMENTO.md)

