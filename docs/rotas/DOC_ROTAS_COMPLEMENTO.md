# Documentação - Rotas de Complemento

**Arquivo:** `src/modules/features/complemento/routes.py`  
**Prefixo:** `/complemento`

---

## 📋 Visão Geral

Rotas para processar e gerenciar **complementos de alunos** baseados em diferenças entre quantidades de alunos "antes" e "depois" de um upload. O sistema calcula valores de complemento para escolas que tiveram aumento no número de alunos e gerencia a liberação desses valores em folhas (sheets) para repasse financeiro.

---

## 🔑 Conceitos Importantes

### Complemento de Alunos

O complemento é calculado quando há diferença positiva entre o número de alunos em um upload base e um upload complemento. O sistema calcula valores para as seguintes cotas:

1. **Gestão** (`valor_complemento_gestao`)
2. **Merenda** (`valor_complemento_merenda`)
3. **Kit Escolar** (`valor_complemento_kit_escolar`)
4. **Uniforme** (`valor_complemento_uniforme`)
5. **Sala de Recurso** (`valor_complemento_sala_recurso`)

**Nota:** As cotas "Preuni" e "Projeto" não são mais calculadas no sistema de complemento.

### Status de Complemento

Cada escola pode ter um dos seguintes status:

- **AUMENTO**: Escola teve aumento no número de alunos e receberá complemento
- **SEM_MUDANCA**: Escola não teve mudança no número de alunos
- **DIMINUICAO**: Escola teve diminuição no número de alunos e **não receberá** complemento
- **ERRO**: Erro no processamento dos dados da escola

### Sistema de Folhas (Sheets)

Similar ao sistema de parcelas, o complemento permite criar múltiplas folhas para organizar as liberações:

- Cada escola pode ser liberada para uma folha específica (`numero_folha`)
- Não há limite de folhas (diferente das parcelas que são limitadas a 2)
- As folhas são usadas para agrupar escolas para repasse financeiro
- Uma escola pode ter apenas uma liberação por `complemento_upload_id`

### Upload Padrão

Quando `complemento_upload_id` não é informado, o sistema automaticamente usa o upload mais recente do ano letivo especificado (ou ano ativo).

---

## 📍 Rotas Disponíveis

### 1. **POST /upload** - Upload de Planilha de Complemento

Processa uma planilha Excel/CSV com dados de complemento de alunos e calcula os valores de complemento para cada escola.

**Endpoint:** `POST /complemento/upload`

**Autenticação:** Não requerida

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body:**
  - `file` (obrigatório, File): Arquivo Excel (.xlsx, .xls) ou CSV
  - `ano_letivo_id` (opcional, int, Query): ID do ano letivo. Se não informado, usa o ano ativo.
  - `upload_base_id` (opcional, int, Query): ID do upload base para comparação. Se não informado, usa o upload ativo.

**Response 200 OK:**
```json
{
  "success": true,
  "complemento_upload_id": 15,
  "ano_letivo_id": 2,
  "ano_letivo": 2026,
  "filename": "complemento_2026.xlsx",
  "upload_date": "2026-01-15T10:30:00",
  "total_escolas_processadas": 318,
  "escolas_com_aumento": 150,
  "escolas_sem_mudanca": 100,
  "escolas_com_diminuicao": 50,
  "escolas_com_erro": 18,
  "valor_complemento_total": 1250000.50,
  "escolas": null,
  "erros": null
}
```

**Campos de Resposta:**
- `complemento_upload_id`: ID do upload de complemento criado
- `total_escolas_processadas`: Total de escolas processadas na planilha
- `escolas_com_aumento`: Quantidade de escolas que receberão complemento
- `escolas_sem_mudanca`: Quantidade de escolas sem mudança
- `escolas_com_diminuicao`: Quantidade de escolas com diminuição (não recebem)
- `escolas_com_erro`: Quantidade de escolas com erro no processamento
- `valor_complemento_total`: Soma total de todos os valores de complemento calculados

**Erros Possíveis:**
- `400 Bad Request`: Arquivo não é Excel/CSV válido
- `500 Internal Server Error`: Erro ao processar a planilha

**Exemplo de Uso:**
```bash
curl -X POST http://localhost:8000/complemento/upload \
  -F "file=@complemento_2026.xlsx" \
  -F "ano_letivo_id=2"
```

---

### 2. **GET /repasse** - Obter Resumo Agrupado por Folhas

Retorna um resumo de todos os complementos agrupados por folhas, incluindo total de escolas e valores por folha.

**Endpoint:** `GET /complemento/repasse`

**Autenticação:** Não requerida

**Query Parameters:**
- `ano_letivo_id` (opcional, int): ID do ano letivo. Se não informado, usa o ano ativo.
- `complemento_upload_id` (opcional, int): Filtrar por upload específico. Se não informado, usa o upload mais recente do ano.

**Response 200 OK:**
```json
{
  "success": true,
  "total_folhas": 3,
  "total_escolas": 150,
  "valor_total_reais": 1250000.50,
  "folhas": [
    {
      "numero_folha": 1,
      "total_escolas": 50,
      "valor_total_reais": 450000.00,
      "escolas": [
        {
          "escola_id": 100,
          "nome_uex": "Escola Exemplo",
          "dre": "DRE-01",
          "liberada": true,
          "numero_folha": 1,
          "valor_complemento_total": 9000.00,
          "status": "AUMENTO"
        }
      ]
    },
    {
      "numero_folha": 2,
      "total_escolas": 50,
      "valor_total_reais": 400000.00,
      "escolas": [...]
    },
    {
      "numero_folha": null,
      "total_escolas": 50,
      "valor_total_reais": 400000.50,
      "escolas": [...]
    }
  ]
}
```

**Campos de Resposta:**
- `total_folhas`: Número total de folhas distintas (incluindo `null` para escolas não liberadas)
- `total_escolas`: Total de escolas com complemento
- `valor_total_reais`: Soma total de todos os valores de complemento
- `folhas`: Lista de folhas, cada uma contendo:
  - `numero_folha`: Número da folha (ou `null` se não liberada)
  - `total_escolas`: Quantidade de escolas nesta folha
  - `valor_total_reais`: Soma dos valores de complemento desta folha
  - `escolas`: Lista de escolas nesta folha

**Exemplo de Uso:**
```bash
curl "http://localhost:8000/complemento/repasse?ano_letivo_id=2"
```

---

### 3. **GET /{complemento_upload_id}** - Obter Detalhes de um Upload

Retorna informações detalhadas sobre um upload de complemento específico, incluindo todas as escolas processadas e seus valores calculados.

**Endpoint:** `GET /complemento/{complemento_upload_id}`

**Autenticação:** Não requerida

**Path Parameters:**
- `complemento_upload_id` (obrigatório, int): ID do upload de complemento

**Response 200 OK:**
```json
{
  "complemento_upload_id": 15,
  "ano_letivo_id": 2,
  "ano_letivo": 2026,
  "filename": "complemento_2026.xlsx",
  "upload_date": "2026-01-15T10:30:00",
  "upload_base_id": 10,
  "upload_complemento_id": 15,
  "total_escolas_processadas": 318,
  "escolas_com_aumento": 150,
  "escolas_sem_mudanca": 100,
  "escolas_com_diminuicao": 50,
  "escolas_com_erro": 18,
  "valor_complemento_total": 1250000.50,
  "escolas": [
    {
      "escola_id": 100,
      "nome_uex": "Escola Exemplo",
      "dre": "DRE-01",
      "status": "AUMENTO",
      "total_alunos_antes": 200,
      "total_alunos_depois": 250,
      "total_alunos_diferenca": 50,
      "valor_complemento_total": 9000.00,
      "valor_complemento_gestao": 2000.00,
      "valor_complemento_kit_escolar": 1500.00,
      "valor_complemento_uniforme": 1500.00,
      "valor_complemento_merenda": 3000.00,
      "valor_complemento_sala_recurso": 1000.00
    }
  ]
}
```

**Campos de Resposta:**
- Informações do upload (ID, ano, arquivo, datas)
- Estatísticas gerais (total de escolas por status)
- `escolas`: Lista detalhada de cada escola com:
  - Informações da escola (ID, nome, DRE)
  - Status do complemento
  - Quantidades de alunos (antes, depois, diferença)
  - Valores calculados por cota

**Erros Possíveis:**
- `404 Not Found`: Upload de complemento não encontrado

**Exemplo de Uso:**
```bash
curl "http://localhost:8000/complemento/15"
```

---

### 4. **GET /escola/{escola_id}** - Histórico de Complementos de uma Escola

Retorna o histórico completo de todos os complementos processados para uma escola específica.

**Endpoint:** `GET /complemento/escola/{escola_id}`

**Autenticação:** Não requerida

**Path Parameters:**
- `escola_id` (obrigatório, int): ID da escola

**Response 200 OK:**
```json
{
  "escola_id": 100,
  "nome_uex": "Escola Exemplo",
  "dre": "DRE-01",
  "complementos": [
    {
      "complemento_upload_id": 15,
      "data": "2026-01-15T10:30:00",
      "status": "AUMENTO",
      "total_alunos_diferenca": 50,
      "valor_complemento_total": 9000.00,
      "valor_complemento_gestao": 2000.00,
      "valor_complemento_kit_escolar": 1500.00,
      "valor_complemento_uniforme": 1500.00,
      "valor_complemento_merenda": 3000.00,
      "valor_complemento_sala_recurso": 1000.00
    },
    {
      "complemento_upload_id": 12,
      "data": "2025-12-10T14:20:00",
      "status": "SEM_MUDANCA",
      "total_alunos_diferenca": 0,
      "valor_complemento_total": 0.00,
      "valor_complemento_gestao": 0.00,
      "valor_complemento_kit_escolar": 0.00,
      "valor_complemento_uniforme": 0.00,
      "valor_complemento_merenda": 0.00,
      "valor_complemento_sala_recurso": 0.00
    }
  ]
}
```

**Campos de Resposta:**
- Informações da escola (ID, nome, DRE)
- `complementos`: Lista cronológica de todos os complementos processados para esta escola

**Erros Possíveis:**
- `404 Not Found`: Escola não encontrada

**Exemplo de Uso:**
```bash
curl "http://localhost:8000/complemento/escola/100"
```

---

### 5. **GET /** - Listar Todos os Uploads de Complemento

Retorna uma lista paginada de todos os uploads de complemento, com opção de filtrar por ano letivo.

**Endpoint:** `GET /complemento/`

**Autenticação:** Não requerida

**Query Parameters:**
- `ano_letivo_id` (opcional, int): Filtrar por ano letivo específico
- `page` (opcional, int, padrão: 1): Número da página (mínimo: 1)
- `page_size` (opcional, int, padrão: 20): Tamanho da página (mínimo: 1, máximo: 100)

**Response 200 OK:**
```json
{
  "total": 10,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "complemento_upload_id": 15,
      "ano_letivo_id": 2,
      "ano_letivo": 2026,
      "filename": "complemento_2026.xlsx",
      "upload_date": "2026-01-15T10:30:00",
      "total_escolas_processadas": 318,
      "escolas_com_aumento": 150,
      "valor_complemento_total": 1250000.50
    }
  ]
}
```

**Campos de Resposta:**
- `total`: Total de uploads encontrados
- `page`: Página atual
- `page_size`: Tamanho da página
- `items`: Lista de uploads com informações resumidas

**Exemplo de Uso:**
```bash
curl "http://localhost:8000/complemento/?ano_letivo_id=2&page=1&page_size=20"
```

---

### 6. **POST /liberar** - Liberar Escolas para uma Folha

Libera uma ou mais escolas para uma folha específica de complemento. Cria ou atualiza registros de liberação.

**Endpoint:** `POST /complemento/liberar`

**Autenticação:** Não requerida

**Request Body:**
```json
{
  "escola_ids": [100, 101, 102],
  "numero_folha": 1,
  "complemento_upload_id": null,
  "ano_letivo_id": null
}
```

**Campos:**
- `escola_ids` (obrigatório, List[int]): Lista de IDs das escolas a serem liberadas
- `numero_folha` (obrigatório, int): Número da folha para liberação
- `complemento_upload_id` (opcional, int): ID do upload de complemento. Se não informado, usa o upload mais recente do ano.
- `ano_letivo_id` (opcional, int): ID do ano letivo. Usado apenas se `complemento_upload_id` não for informado. Se não informado, usa o ano ativo.

**Response 200 OK:**
```json
{
  "success": true,
  "message": "3 escola(s) liberada(s) para folha 1",
  "total_escolas_atualizadas": 3,
  "numero_folha": 1,
  "liberacoes": [
    {
      "id": 50,
      "escola_id": 100,
      "nome_uex": "Escola Exemplo",
      "dre": "DRE-01",
      "complemento_upload_id": 15,
      "liberada": true,
      "numero_folha": 1,
      "data_liberacao": "2026-01-15T10:30:00",
      "created_at": "2026-01-15T10:30:00",
      "updated_at": "2026-01-15T10:30:00"
    }
  ]
}
```

**Campos de Resposta:**
- `success`: Indica sucesso da operação
- `message`: Mensagem descritiva
- `total_escolas_atualizadas`: Quantidade de escolas atualizadas
- `numero_folha`: Número da folha atribuído
- `liberacoes`: Lista de liberações criadas/atualizadas

**Erros Possíveis:**
- `400 Bad Request`: Dados inválidos (ex: lista vazia de escolas)
- `500 Internal Server Error`: Erro ao processar liberação

**Exemplo de Uso:**
```bash
curl -X POST http://localhost:8000/complemento/liberar \
  -H "Content-Type: application/json" \
  -d '{
    "escola_ids": [100, 101, 102],
    "numero_folha": 1
  }'
```

---

### 7. **GET /liberacoes** - Listar Liberações

Retorna uma lista de liberações de complemento com filtros opcionais.

**Endpoint:** `GET /complemento/liberacoes`

**Autenticação:** Não requerida

**Query Parameters:**
- `complemento_upload_id` (opcional, int): Filtrar por upload específico. Se não informado, usa o upload mais recente do ano.
- `numero_folha` (opcional, int): Filtrar por número da folha
- `liberada` (opcional, boolean): Filtrar por status de liberação (`true` = liberada, `false` = não liberada)
- `escola_id` (opcional, int): Filtrar por escola específica
- `ano_letivo_id` (opcional, int): ID do ano letivo. Usado apenas se `complemento_upload_id` não for informado.

**Response 200 OK:**
```json
{
  "success": true,
  "total": 150,
  "liberacoes": [
    {
      "id": 50,
      "escola_id": 100,
      "nome_uex": "Escola Exemplo",
      "dre": "DRE-01",
      "complemento_upload_id": 15,
      "liberada": true,
      "numero_folha": 1,
      "data_liberacao": "2026-01-15T10:30:00",
      "created_at": "2026-01-15T10:30:00",
      "updated_at": "2026-01-15T10:30:00"
    }
  ]
}
```

**Campos de Resposta:**
- `success`: Indica sucesso da operação
- `total`: Total de liberações encontradas
- `liberacoes`: Lista de liberações que atendem aos filtros

**Exemplo de Uso:**
```bash
# Listar todas as liberações do upload mais recente
curl "http://localhost:8000/complemento/liberacoes"

# Filtrar por folha específica
curl "http://localhost:8000/complemento/liberacoes?numero_folha=1"

# Filtrar apenas escolas liberadas
curl "http://localhost:8000/complemento/liberacoes?liberada=true"
```

---

### 8. **PUT /liberacoes/{liberacao_id}** - Atualizar Liberação

Atualiza uma liberação específica de complemento.

**Endpoint:** `PUT /complemento/liberacoes/{liberacao_id}`

**Autenticação:** Não requerida

**Path Parameters:**
- `liberacao_id` (obrigatório, int): ID da liberação a ser atualizada

**Request Body:**
```json
{
  "liberada": true,
  "numero_folha": 2,
  "data_liberacao": "2026-01-15T10:30:00"
}
```

**Campos (todos opcionais):**
- `liberada` (opcional, boolean): Status de liberação
- `numero_folha` (opcional, int): Número da folha
- `data_liberacao` (opcional, datetime): Data da liberação

**Response 200 OK:**
```json
{
  "success": true,
  "message": "Liberação atualizada com sucesso",
  "liberacao": {
    "id": 50,
    "escola_id": 100,
    "nome_uex": "Escola Exemplo",
    "dre": "DRE-01",
    "complemento_upload_id": 15,
    "liberada": true,
    "numero_folha": 2,
    "data_liberacao": "2026-01-15T10:30:00",
    "created_at": "2026-01-15T10:30:00",
    "updated_at": "2026-01-15T10:35:00"
  }
}
```

**Campos de Resposta:**
- `success`: Indica sucesso da operação
- `message`: Mensagem descritiva
- `liberacao`: Objeto da liberação atualizada

**Erros Possíveis:**
- `404 Not Found`: Liberação não encontrada
- `500 Internal Server Error`: Erro ao atualizar

**Exemplo de Uso:**
```bash
curl -X PUT http://localhost:8000/complemento/liberacoes/50 \
  -H "Content-Type: application/json" \
  -d '{
    "numero_folha": 2,
    "liberada": true
  }'
```

---

## 🔄 Fluxo de Trabalho Completo

### 1. Upload de Planilha de Complemento

```bash
# Fazer upload da planilha com dados de complemento
POST /complemento/upload
# FormData: file + ano_letivo_id (opcional)
```

### 2. Visualizar Resumo por Folhas

```bash
# Ver resumo agrupado por folhas
GET /complemento/repasse?ano_letivo_id=2
```

### 3. Liberar Escolas para Folhas

```bash
# Liberar escolas para uma folha específica
POST /complemento/liberar
{
  "escola_ids": [100, 101, 102],
  "numero_folha": 1
}
```

### 4. Consultar Liberações

```bash
# Listar todas as liberações de uma folha
GET /complemento/liberacoes?numero_folha=1

# Ver detalhes de um upload específico
GET /complemento/15

# Ver histórico de uma escola
GET /complemento/escola/100
```

### 5. Atualizar Liberações

```bash
# Atualizar uma liberação específica
PUT /complemento/liberacoes/50
{
  "numero_folha": 2,
  "liberada": true
}
```

---

## 📊 Mapa de Rotas

```
/complemento
├── POST   /upload                    # Upload de planilha
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

- [Índice Geral de Rotas](DOC_INDICE_ROTAS.md)
- [Rotas de Parcelas](DOC_ROTAS_PARCELAS.md) - Sistema similar para parcelas

---

## 📝 Notas Gerais

1. **Base URL:** `http://localhost:8000` (desenvolvimento)

2. **Formato de Resposta:** Todas as rotas retornam JSON.

3. **Códigos de Erro:**
   - `200 OK`: Sucesso
   - `400 Bad Request`: Requisição inválida
   - `404 Not Found`: Recurso não encontrado
   - `500 Internal Server Error`: Erro interno

4. **Isolamento por Ano:** Dados são isolados por ano letivo. Cada ano mantém seus próprios uploads e liberações de complemento.

5. **Upload Padrão:** Quando `complemento_upload_id` não é informado, o sistema usa automaticamente o upload mais recente do ano letivo especificado (ou ano ativo).

6. **Folhas vs Parcelas:** 
   - **Folhas (Complemento)**: Não há limite de folhas, usadas para organizar liberações de complemento
   - **Parcelas**: Limitadas a 2 parcelas, usadas para dividir valores das cotas principais

---

## 🚀 Quick Start

```bash
# 1. Upload de planilha de complemento
curl -X POST http://localhost:8000/complemento/upload \
  -F "file=@complemento_2026.xlsx" \
  -F "ano_letivo_id=2"

# 2. Ver resumo agrupado por folhas
curl "http://localhost:8000/complemento/repasse?ano_letivo_id=2"

# 3. Liberar escolas para folha 1
curl -X POST http://localhost:8000/complemento/liberar \
  -H "Content-Type: application/json" \
  -d '{
    "escola_ids": [100, 101, 102],
    "numero_folha": 1
  }'

# 4. Listar liberações da folha 1
curl "http://localhost:8000/complemento/liberacoes?numero_folha=1"
```

---

**Última atualização:** 2026-01-15
