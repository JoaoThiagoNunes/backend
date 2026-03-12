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

### Separação por Tipo de Ensino

Os valores de complemento podem ser separados entre ensino **fundamental** e **médio**, similar ao processo de separação de parcelas normais:

- **Porcentagens Calculadas:** Baseadas nas diferenças de quantidades do complemento, usando os mesmos pesos do repasse normal
- **1 Parcela Única:** Cada cota de complemento é dividida em 1 parcela única (não 2 como nas parcelas normais)
- **Divisão por Ensino:** Cada parcela é subdividida entre fundamental e médio baseado nas porcentagens
- **Cotas Processadas:** Gestão, Merenda, Kit Escolar, Uniforme e Sala de Recurso
- **Armazenamento:** Valores são armazenados em centavos (inteiros) para precisão

**Exemplo:**
- Complemento de Gestão: R$ 5.000,00
- Porcentagem: 52.5% fundamental, 47.5% médio
- Resultado:
  - Fundamental: R$ 2.625,00
  - Médio: R$ 2.375,00

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
          "status": "AUMENTO",
          "parcelas_por_cota": [
            {
              "tipo_cota": "CUSTEIO",
              "valor_total_reais": 2000.00,
              "parcela_1": {
                "fundamental": 1050.00,
                "medio": 950.00
              },
              "porcentagens": {
                "fundamental": 52.5,
                "medio": 47.5
              }
            },
            {
              "tipo_cota": "MERENDA",
              "valor_total_reais": 3000.00,
              "parcela_1": {
                "fundamental": 1575.00,
                "medio": 1425.00
              },
              "porcentagens": {
                "fundamental": 52.5,
                "medio": 47.5
              }
            }
          ],
          "porcentagem_fundamental": 52.5,
          "porcentagem_medio": 47.5
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
  - `escolas`: Lista de escolas nesta folha, cada uma contendo:
    - Campos padrão: informações da escola, status, valores totais
    - **Novos campos (opcionais):** Valores separados por tipo de ensino (apenas se `POST /complemento/separar` foi executado):
      - `parcelas_por_cota`: Lista de cotas com valores separados por ensino (fundamental/médio)
      - `porcentagem_fundamental`: Porcentagem de alunos em ensino fundamental
      - `porcentagem_medio`: Porcentagem de alunos em ensino médio

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
      "valor_complemento_sala_recurso": 1000.00,
      "parcelas": [
        {
          "id": 1,
          "tipo_cota": "CUSTEIO",
          "numero_parcela": 1,
          "tipo_ensino": "FUNDAMENTAL",
          "valor_reais": 1050.00,
          "valor_centavos": 105000,
          "porcentagem_alunos": 52.5,
          "created_at": "2026-03-11T11:49:43"
        },
        {
          "id": 2,
          "tipo_cota": "CUSTEIO",
          "numero_parcela": 1,
          "tipo_ensino": "MEDIO",
          "valor_reais": 950.00,
          "valor_centavos": 95000,
          "porcentagem_alunos": 47.5,
          "created_at": "2026-03-11T11:49:43"
        }
      ],
      "porcentagem_fundamental": 52.5,
      "porcentagem_medio": 47.5
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
      "valor_complemento_sala_recurso": 0.00,
      "parcelas": null,
      "porcentagem_fundamental": null,
      "porcentagem_medio": null
    }
  ]
}
```

**Campos de Resposta:**
- Informações da escola (ID, nome, DRE)
- `complementos`: Lista cronológica de todos os complementos processados para esta escola
  - Campos padrão: informações do complemento, valores por cota
  - **Novos campos (opcionais):** Valores separados por tipo de ensino (apenas se `POST /complemento/separar` foi executado):
    - `parcelas`: Lista de parcelas detalhadas separadas por ensino (fundamental/médio)
    - `porcentagem_fundamental`: Porcentagem de alunos em ensino fundamental
    - `porcentagem_medio`: Porcentagem de alunos em ensino médio

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

### 8. **POST /separar** - Separar Complementos por Tipo de Ensino

Separa os valores de complemento entre ensino fundamental e médio, similar ao processo de separação de parcelas normais.

**Endpoint:** `POST /complemento/separar`

**Autenticação:** Não requerida

**Request Body:**
```json
{
  "complemento_upload_id": null,
  "ano_letivo_id": null,
  "recalcular": false,
  "calculation_version": null
}
```

**Campos:**
- `complemento_upload_id` (opcional, int): ID do upload de complemento. Se `null`, usa o mais recente do ano letivo.
- `ano_letivo_id` (opcional, int): ID do ano letivo. Se `null`, usa o ano ativo.
- `recalcular` (opcional, boolean): Se `true`, recalcula mesmo que já existam parcelas. Padrão: `false`.
- `calculation_version` (opcional, string): Versão do cálculo para auditoria. Se não fornecido, gera automaticamente (ex: `v1_20260311_114943`).

**Response 200 OK:**
```json
{
  "success": true,
  "message": "Separados 150 complemento(s) em 1500 parcela(s)",
  "total_escolas": 150,
  "escolas_processadas": 150,
  "total_parcelas_criadas": 1500,
  "complemento_upload_id": 15,
  "calculation_version": "v1_20260311_114943",
  "escolas": [
    {
      "escola_id": 100,
      "nome_uex": "ESCOLA MUNICIPAL EXEMPLO",
      "dre": "DRE-01",
      "porcentagem_fundamental": 52.5,
      "porcentagem_medio": 47.5,
      "parcelas_por_cota": [
        {
          "tipo_cota": "CUSTEIO",
          "valor_total_reais": 5000.00,
          "parcela_1": {
            "fundamental": 2625.00,
            "medio": 2375.00
          },
          "porcentagens": {
            "fundamental": 52.5,
            "medio": 47.5
          }
        },
        {
          "tipo_cota": "MERENDA",
          "valor_total_reais": 3000.00,
          "parcela_1": {
            "fundamental": 1575.00,
            "medio": 1425.00
          },
          "porcentagens": {
            "fundamental": 52.5,
            "medio": 47.5
          }
        },
        {
          "tipo_cota": "KIT_ESCOLAR",
          "valor_total_reais": 1500.00,
          "parcela_1": {
            "fundamental": 787.50,
            "medio": 712.50
          },
          "porcentagens": {
            "fundamental": 52.5,
            "medio": 47.5
          }
        },
        {
          "tipo_cota": "UNIFORME",
          "valor_total_reais": 600.00,
          "parcela_1": {
            "fundamental": 315.00,
            "medio": 285.00
          },
          "porcentagens": {
            "fundamental": 52.5,
            "medio": 47.5
          }
        },
        {
          "tipo_cota": "SALA_RECURSO",
          "valor_total_reais": 2000.00,
          "parcela_1": {
            "fundamental": 1050.00,
            "medio": 950.00
          },
          "porcentagens": {
            "fundamental": 52.5,
            "medio": 47.5
          }
        }
      ]
    }
    // ... mais escolas
  ]
}
```

**Campos de Resposta:**
- `success`: Indica se a operação foi bem-sucedida
- `message`: Mensagem descritiva do resultado
- `total_escolas`: Total de escolas com complemento processadas
- `escolas_processadas`: Quantidade de escolas que tiveram parcelas criadas
- `total_parcelas_criadas`: Total de parcelas criadas (escolas × cotas × 2 tipos de ensino)
- `complemento_upload_id`: ID do upload de complemento usado
- `calculation_version`: Versão do cálculo para auditoria
- `escolas`: Lista de escolas com suas parcelas separadas por tipo de ensino

**Estrutura de Parcelas por Cota:**
- Cada cota do complemento é separada em **1 parcela única** (diferente das parcelas normais que têm 2)
- Cada parcela é dividida entre `fundamental` e `medio` baseado nas porcentagens calculadas
- As porcentagens são calculadas usando os mesmos pesos do repasse normal, aplicados às **diferenças** de quantidades do complemento

**Cotas Processadas:**
1. **Gestão/Custeio** (`CUSTEIO`)
2. **Merenda** (`MERENDA`)
3. **Kit Escolar** (`KIT_ESCOLAR`)
4. **Uniforme** (`UNIFORME`)
5. **Sala de Recurso** (`SALA_RECURSO`)

**Nota:** As cotas "Projeto" e "Preuni" não são processadas no complemento.

**Cálculo de Porcentagens:**

As porcentagens são calculadas baseadas nas **diferenças** de quantidades do complemento, usando os mesmos pesos do repasse normal:

**Fundamental:**
- Fundamental Inicial: peso 1.0
- Fundamental Final: peso 1.10
- Fundamental Integral: peso 1.40
- Especial Fundamental Regular: peso 1.0
- Especial Fundamental Integral: peso 1.40

**Médio:**
- Profissionalizante: peso 1.30
- Profissionalizante Integrado: peso 1.30
- Alternância: peso 1.40
- Ensino Médio Integral: peso 1.40
- Ensino Médio Regular: peso 1.25
- Especial Médio Parcial: peso 1.25
- Especial Médio Integral: peso 1.40

**Fórmula:**
```
Valor_Fundamental = Σ(diferença_modalidade_fundamental × peso_modalidade)
Valor_Médio = Σ(diferença_modalidade_médio × peso_modalidade)
% Fundamental = (Valor_Fundamental / (Valor_Fundamental + Valor_Médio)) × 100
% Médio = 100% - % Fundamental
```

**Comportamento:**

1. **Idempotência:** Se `recalcular=false` e já existem parcelas, retorna as parcelas existentes sem recriar.
2. **Recálculo:** Se `recalcular=true`, deleta parcelas antigas e cria novas.
3. **Filtro Automático:** Processa apenas complementos com status `AUMENTO` e valores > 0.
4. **Valores em Centavos:** Internamente, os valores são armazenados em centavos (inteiros), mas a resposta retorna em reais.

**Erros Possíveis:**
- `404 Not Found`: Nenhum complemento encontrado para o ano letivo ou complemento_upload_id especificado.
- `404 Not Found`: Nenhum complemento com valores encontrado para separar.
- `500 Internal Server Error`: Erro ao processar a separação.

**Exemplo de Uso:**

Separar complementos (primeira vez):
```bash
curl -X POST http://localhost:8000/complemento/separar \
  -H "Content-Type: application/json" \
  -d '{
    "ano_letivo_id": 2,
    "recalcular": false
  }'
```

Recalcular parcelas existentes:
```bash
curl -X POST http://localhost:8000/complemento/separar \
  -H "Content-Type: application/json" \
  -d '{
    "complemento_upload_id": 15,
    "recalcular": true,
    "calculation_version": "v2_20260311_120000"
  }'
```

**Integração Frontend:**

```typescript
interface SepararComplementoRequest {
  complemento_upload_id?: number;
  ano_letivo_id?: number;
  recalcular?: boolean;
  calculation_version?: string;
}

interface ParcelaComplementoPorCota {
  tipo_cota: string;
  valor_total_reais: number;
  parcela_1: {
    fundamental: number;
    medio: number;
  };
  porcentagens: {
    fundamental: number;
    medio: number;
  };
}

interface EscolaComplementoParcelas {
  escola_id: number;
  nome_uex: string;
  dre?: string;
  porcentagem_fundamental: number;
  porcentagem_medio: number;
  parcelas_por_cota: ParcelaComplementoPorCota[];
}

interface SepararComplementoResponse {
  success: boolean;
  message: string;
  total_escolas: number;
  escolas_processadas: number;
  total_parcelas_criadas: number;
  complemento_upload_id: number;
  escolas: EscolaComplementoParcelas[];
  calculation_version?: string;
}

// Exemplo de uso
async function separarComplementos(
  complementoUploadId?: number,
  anoLetivoId?: number,
  recalcular = false
): Promise<SepararComplementoResponse> {
  const response = await fetch('http://localhost:8000/complemento/separar', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      complemento_upload_id: complementoUploadId,
      ano_letivo_id: anoLetivoId,
      recalcular,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Erro ao separar complementos: ${response.statusText}`);
  }
  
  return response.json();
}
```

**Diferenças entre Complemento e Parcelas Normais:**

| Aspecto | Complemento | Parcelas Normais |
|---------|-------------|------------------|
| Número de parcelas | 1 parcela única | 2 parcelas |
| Base de cálculo | Diferenças de quantidades | Quantidades totais |
| Cotas processadas | 5 cotas (Gestão, Merenda, Kit, Uniforme, Sala) | 8 cotas (inclui Preuni, Climatização, etc.) |
| Porcentagens | Baseadas nas diferenças | Baseadas nas quantidades totais |
| Quando usar | Após upload de complemento | Após cálculo de valores |

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
├── PUT    /liberacoes/{liberacao_id} # Atualizar liberação
└── POST   /separar                   # Separar por tipo de ensino
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

# 2. Separar complementos por tipo de ensino (fundamental/médio)
curl -X POST http://localhost:8000/complemento/separar \
  -H "Content-Type: application/json" \
  -d '{
    "ano_letivo_id": 2,
    "recalcular": false
  }'

# 3. Ver resumo agrupado por folhas
curl "http://localhost:8000/complemento/repasse?ano_letivo_id=2"

# 4. Liberar escolas para folha 1
curl -X POST http://localhost:8000/complemento/liberar \
  -H "Content-Type: application/json" \
  -d '{
    "escola_ids": [100, 101, 102],
    "numero_folha": 1
  }'

# 5. Listar liberações da folha 1
curl "http://localhost:8000/complemento/liberacoes?numero_folha=1"
```

---

**Última atualização:** 2026-03-11

**Novidades:**
- ✅ Separação de complementos por tipo de ensino (fundamental/médio) - Rota `/separar`
- ✅ Valores separados por ensino agora retornados em `GET /complemento/escola/{escola_id}` e `GET /complemento/repasse`
