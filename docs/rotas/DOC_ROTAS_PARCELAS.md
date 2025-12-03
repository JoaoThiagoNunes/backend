# Documentação - Rotas de Parcelas

**Arquivo:** `src/modules/routes/parcelas_routes.py`  
**Prefixo:** `/parcelas`

---

## 📋 Visão Geral

Rotas para dividir os valores das cotas PROFIN em **2 parcelas** e subdividir cada parcela por **tipo de ensino** (fundamental vs médio) baseado na porcentagem de alunos.

---

## 🔑 Conceitos Importantes

### Cotas Processadas

Apenas as seguintes cotas são processadas:

1. **Merenda** (`profin_merenda`)
2. **Gestão/Custeio** (`profin_custeio`)
3. **Preuni** (`profin_preuni`)
4. **Climatização** (`profin_climatizacao`)
5. **Sala de Recurso** (`profin_sala_recurso`)
6. **Uniforme** (`profin_uniforme`)
7. **Permanente** (`profin_permanente`)
8. **Kit Escolar** (`profin_kit_escolar`)

**Nota:** A cota "Projeto" (`profin_projeto`) **não é processada**.

### Divisão em Parcelas

1. **2 Parcelas:** Cada cota é dividida em 2 parcelas iguais (ou quase iguais)
2. **Por Tipo de Ensino:** Cada parcela é dividida entre Fundamental e Médio baseado na % de alunos

### Cálculo de Porcentagens

As porcentagens são calculadas usando **pesos (multiplicadores)** para cada modalidade:

**Fundamental:**
- Fundamental Inicial: peso 1.0
- Fundamental Final: peso 1.10
- Fundamental Integral: peso 1.40
- Especial Fundamental Regular: peso 1.0
- Especial Fundamental Integral: peso 1.40

**Médio:**
- Profissionalizante: peso 1.30
- Alternância: peso 1.40
- Ensino Médio Integral: peso 1.40
- Ensino Médio Regular: peso 1.25
- Especial Médio Parcial: peso 1.25
- Especial Médio Integral: peso 1.40

**Fórmula:**
```
% Fundamental = (Valor_Fundamental_Ponderado / Total_Ponderado) * 100
% Médio = 100% - % Fundamental
```

### Valores em Centavos

Todos os valores são armazenados em **centavos (inteiros)** para evitar problemas com floats.

---

## 📍 Rotas Disponíveis

### 1. **POST /** - Separar Valores em Parcelas

Divide os valores das cotas em 2 parcelas e subdivide cada parcela por tipo de ensino.

**Endpoint:** `POST /parcelas`

**Autenticação:** Não requerida

**Request Body:**
```json
{
  "ano_letivo_id": null,
  "recalcular": false,
  "calculation_version": null
}
```

**Campos:**
- `ano_letivo_id` (opcional, int): ID do ano letivo. Se `null`, usa o ano ativo.
- `recalcular` (opcional, boolean): Se `true`, recalcula mesmo que já existam parcelas. Padrão: `false`.
- `calculation_version` (opcional, string): Versão do cálculo para auditoria. Se não fornecido, gera automaticamente.

**Response:**
```json
{
  "success": true,
  "message": "Parcelas criadas para 250 escolas do ano 2026",
  "total_escolas": 250,
  "escolas_processadas": 250,
  "total_parcelas_criadas": 8000,
  "ano_letivo_id": 2,
  "calculation_version": "v1_20260115_103000",
  "escolas": [
    {
      "escola_id": 1,
      "nome_uex": "ESCOLA MUNICIPAL EXEMPLO",
      "dre": "DRE-01",
      "porcentagem_fundamental": 52.5,
      "porcentagem_medio": 47.5,
      "parcelas_por_cota": [
        {
          "tipo_cota": "custeio",
          "valor_total_reais": 50000.00,
          "parcela_1": {
            "fundamental": 13125.00,
            "medio": 11875.00
          },
          "parcela_2": {
            "fundamental": 13125.00,
            "medio": 11875.00
          },
          "porcentagens": {
            "fundamental": 52.5,
            "medio": 47.5
          }
        }
        // ... mais cotas
      ]
    }
    // ... mais escolas
  ]
}
```

**Comportamento:**

1. **Idempotência:** Se `recalcular=false` e já existem parcelas, retorna as parcelas existentes sem recriar.
2. **Recálculo:** Se `recalcular=true`, deleta parcelas antigas e cria novas.
3. **Versionamento:** Cada cálculo tem uma versão para auditoria.

**Erros:**
- `404 Not Found`: Nenhum cálculo encontrado para o ano letivo. Execute `/calculos` primeiro.

**Exemplo de uso:**

Criar parcelas (primeira vez):
```bash
curl -X POST http://localhost:8000/parcelas \
  -H "Content-Type: application/json" \
  -d '{}'
```

Recalcular parcelas:
```bash
curl -X POST http://localhost:8000/parcelas \
  -H "Content-Type: application/json" \
  -d '{"recalcular": true}'
```

Com versão customizada:
```bash
curl -X POST http://localhost:8000/parcelas \
  -H "Content-Type: application/json" \
  -d '{
    "recalcular": true,
    "calculation_version": "v2.0_20260115"
  }'
```

Com JavaScript:
```javascript
const criarParcelas = async (recalcular = false, anoLetivoId = null) => {
  const response = await fetch('http://localhost:8000/parcelas', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      recalcular,
      ano_letivo_id: anoLetivoId
    })
  });
  
  return response.json();
};

// Criar parcelas
const resultado = await criarParcelas();

// Recalcular
const resultadoRecalculado = await criarParcelas(true);
```

---

### 2. **GET /escola/{escola_id}** - Parcelas de uma Escola

Retorna todas as parcelas de uma escola específica.

**Endpoint:** `GET /parcelas/escola/{escola_id}`

**Autenticação:** Não requerida

**Path Parameters:**
- `escola_id` (int): ID da escola

**Response:**
```json
{
  "success": true,
  "escola_id": 1,
  "nome_uex": "ESCOLA MUNICIPAL EXEMPLO",
  "dre": "DRE-01",
  "porcentagem_fundamental": 52.5,
  "porcentagem_medio": 47.5,
  "parcelas": [
    {
      "id": 1,
      "tipo_cota": "custeio",
      "numero_parcela": 1,
      "tipo_ensino": "fundamental",
      "valor_reais": 13125.00,
      "valor_centavos": 1312500,
      "porcentagem_alunos": 52.5,
      "created_at": "2026-01-15T10:30:00"
    },
    {
      "id": 2,
      "tipo_cota": "custeio",
      "numero_parcela": 1,
      "tipo_ensino": "medio",
      "valor_reais": 11875.00,
      "valor_centavos": 1187500,
      "porcentagem_alunos": 47.5,
      "created_at": "2026-01-15T10:30:00"
    }
    // ... mais parcelas (2 parcelas x 8 cotas x 2 tipos ensino = 32 parcelas)
  ]
}
```

**Erros:**
- `404 Not Found`: Escola não encontrada, cálculo não encontrado, ou parcelas não encontradas

**Exemplo de uso:**
```bash
curl http://localhost:8000/parcelas/escola/1
```

Com JavaScript:
```javascript
const obterParcelasEscola = async (escolaId) => {
  const response = await fetch(
    `http://localhost:8000/parcelas/escola/${escolaId}`
  );
  return response.json();
};

const parcelas = await obterParcelasEscola(1);
console.log(`Total de parcelas: ${parcelas.parcelas.length}`);
```

---

### 3. **POST /liberar** - Liberar Escolas por Parcela e Folha

Libera manualmente uma lista de escolas para uma determinada parcela e folha.

**Endpoint:** `POST /parcelas/liberar`

**Request Body:**
```json
{
  "escola_ids": [1, 2, 3],
  "numero_parcela": 1,
  "numero_folha": 2
}
```

**Comportamento:**
- Garante que `numero_parcela` seja 1 ou 2
- Garante que `numero_folha` seja >= 1
- Atualiza ou cria registros na tabela `liberacoes_parcela`
- Marca as escolas como liberadas (`liberada=true`) e armazena `data_liberacao`

**Response (ex.):**
```json
{
  "success": true,
  "message": "3 escola(s) liberada(s) para a parcela 1, folha 2",
  "total_escolas_atualizadas": 3,
  "numero_parcela": 1,
  "numero_folha": 2,
  "liberacoes": [
    {
      "id": 15,
      "escola_id": 1,
      "nome_uex": "EMEIEF PROGRESSO",
      "dre": "DRE-01",
      "numero_parcela": 1,
      "liberada": true,
      "numero_folha": 2,
      "data_liberacao": "2026-03-01T10:32:11.123000",
      "created_at": "2026-02-15T09:00:00",
      "updated_at": "2026-03-01T10:32:11.123000"
    }
  ]
}
```

---

### 4. **GET /liberacoes** - Listar Liberações

Lista todas as liberações cadastradas com filtros opcionais.

**Endpoint:** `GET /parcelas/liberacoes`

**Parâmetros de Query (opcionais):**
- `numero_parcela` (1 ou 2)
- `numero_folha`
- `liberada` (true/false)
- `escola_id`
- `ano_letivo_id`

**Response:**
```json
{
  "success": true,
  "total": 25,
  "liberacoes": [
    {
      "id": 1,
      "escola_id": 10,
      "nome_uex": "EMEF CENTRO",
      "dre": "DRE-02",
      "numero_parcela": 1,
      "liberada": true,
      "numero_folha": 1,
      "data_liberacao": "2026-03-01T10:32:11.123000",
      "created_at": "2026-03-01T10:32:11.123000",
      "updated_at": "2026-03-01T10:32:11.123000"
    }
  ]
}
```

---

### 5. **PUT /liberacoes/{liberacao_id}** - Atualizar Liberação

Atualiza campos específicos (liberada, número da folha, data) de uma liberação existente.

**Endpoint:** `PUT /parcelas/liberacoes/{liberacao_id}`

**Request Body (ex.):**
```json
{
  "liberada": false,
  "numero_folha": null
}
```

**Response:**
```json
{
  "success": true,
  "message": "Liberação atualizada com sucesso",
  "liberacao": {
    "id": 1,
    "escola_id": 10,
    "nome_uex": "EMEF CENTRO",
    "dre": "DRE-02",
    "numero_parcela": 1,
    "liberada": false,
    "numero_folha": null,
    "data_liberacao": null,
    "created_at": "2026-03-01T10:32:11.123000",
    "updated_at": "2026-03-10T09:45:00.000000"
  }
}
```

---

### 6. **DELETE /liberacoes/{liberacao_id}** - Resetar Liberação

Reseta uma liberação (marca como não liberada e limpa número da folha/data).

**Endpoint:** `DELETE /parcelas/liberacoes/{liberacao_id}`

**Response:** semelhante ao PUT, com `liberada=false` e `numero_folha=null`.

---

### 7. **GET /escola/{escola_id}/liberacoes**

Retorna todas as liberações (parcela 1 e 2) de uma escola específica.

**Endpoint:** `GET /parcelas/escola/{escola_id}/liberacoes`

---

### 8. **GET /folha/{numero_parcela}/{numero_folha}**

Lista as liberações que pertencem a uma combinação de parcela/folha.

**Endpoint:** `GET /parcelas/folha/{numero_parcela}/{numero_folha}`

Retorna apenas liberações marcadas como `liberada=true`.

---

### 9. **GET /previsao** - Previsão de Liberação

Lista escolas aptas (ou todas, dependendo do filtro) para liberação de uma parcela.

**Endpoint:** `GET /parcelas/previsao`

**Parâmetros de Query:**
- `numero_parcela` (obrigatório: 1 ou 2)
- `ano_letivo_id` (opcional)
- `somente_pendentes` (opcional, padrão `true`)

**Response (ex.):**
```json
{
  "success": true,
  "numero_parcela": 1,
  "total_escolas": 10,
  "escolas": [
    {
      "escola_id": 5,
      "nome_uex": "EMEF FLORESCER",
      "dre": "DRE-03",
      "numero_parcela": 1,
      "liberada": false,
      "numero_folha": null,
      "valor_total_reais": 18500.00
    }
  ]
}
```

---

### 10. **GET /repasse** - Consolidação para Repasse

Agrupa liberações liberadas por parcela/folha apresentando totais financeiros.

**Endpoint:** `GET /parcelas/repasse`

**Parâmetros de Query (opcionais):**
- `ano_letivo_id`
- `numero_parcela`

**Response (ex.):**
```json
{
  "success": true,
  "total_parcelas": 2,
  "total_folhas": 3,
  "total_escolas": 20,
  "valor_total_reais": 350000.00,
  "folhas": [
    {
      "numero_parcela": 1,
      "numero_folha": 1,
      "total_escolas": 10,
      "valor_total_reais": 180000.00,
      "escolas": [
        {
          "escola_id": 1,
          "nome_uex": "EMEF CENTRO",
          "dre": "DRE-02",
          "numero_parcela": 1,
          "liberada": true,
          "numero_folha": 1,
          "valor_total_reais": 18000.00
        }
      ]
    }
  ]
}
```

---

## 🔄 Fluxo de Trabalho

### 1. Upload de Dados

```bash
POST /uploads/excel
```

### 2. Calcular Valores

```bash
POST /calculos
```

### 3. Criar Parcelas

```bash
POST /parcelas
```

### 4. Verificar Parcelas de uma Escola

```bash
GET /parcelas/escola/1
```

---

## 📊 Estrutura de Dados

### SepararParcelasResponse

```typescript
{
  success: boolean;
  message: string;
  total_escolas: number;
  escolas_processadas: number;
  total_parcelas_criadas: number;
  ano_letivo_id: number;
  calculation_version: string | null;
  escolas: EscolaParcelas[];
}
```

### EscolaParcelas

```typescript
{
  escola_id: number;
  nome_uex: string;
  dre: string | null;
  porcentagem_fundamental: number;  // 0-100
  porcentagem_medio: number;        // 0-100
  parcelas_por_cota: ParcelaPorCota[];
}
```

### ParcelaPorCota

```typescript
{
  tipo_cota: string;  // "custeio", "merenda", etc.
  valor_total_reais: number;
  parcela_1: {
    fundamental: number;
    medio: number;
  };
  parcela_2: {
    fundamental: number;
    medio: number;
  };
  porcentagens: {
    fundamental: number;
    medio: number;
  };
}
```

### ParcelaDetalhe

```typescript
{
  id: number;
  tipo_cota: string;
  numero_parcela: number;      // 1 ou 2
  tipo_ensino: string;         // "fundamental" ou "medio"
  valor_reais: number;
  valor_centavos: number;
  porcentagem_alunos: number;
  created_at: string;          // ISO datetime
}
```

### LiberacaoParcelaInfo

```typescript
{
  id: number;
  escola_id: number;
  nome_uex: string;
  dre: string | null;
  numero_parcela: number;   // 1 ou 2
  liberada: boolean;
  numero_folha: number | null;
  data_liberacao: string | null; // ISO datetime
  created_at: string;
  updated_at: string;
}
```

### LiberarParcelasResponse

```typescript
{
  success: boolean;
  message: string;
  total_escolas_atualizadas: number;
  numero_parcela: number;
  numero_folha: number;
  liberacoes: LiberacaoParcelaInfo[];
}
```

### EscolaPrevisaoInfo

```typescript
{
  escola_id: number;
  nome_uex: string;
  dre: string | null;
  numero_parcela: number;
  liberada: boolean;
  numero_folha: number | null;
  valor_total_reais: number;
}
```

### PrevisaoLiberacaoResponse

```typescript
{
  success: boolean;
  numero_parcela: number;
  total_escolas: number;
  escolas: EscolaPrevisaoInfo[];
}
```

### RepasseResumoResponse

```typescript
{
  success: boolean;
  total_parcelas: number;
  total_folhas: number;
  total_escolas: number;
  valor_total_reais: number;
  folhas: {
    numero_parcela: number;
    numero_folha: number | null;
    total_escolas: number;
    valor_total_reais: number;
    escolas: EscolaPrevisaoInfo[];
  }[];
}
```

---

## 🧮 Exemplo de Cálculo

### Escola com:
- Custeio: R$ 50.000,00
- 52,5% fundamental, 47,5% médio

### Resultado:

**Parcela 1:**
- Total: R$ 25.000,00
- Fundamental: R$ 13.125,00 (52,5% de 25.000)
- Médio: R$ 11.875,00 (47,5% de 25.000)

**Parcela 2:**
- Total: R$ 25.000,00
- Fundamental: R$ 13.125,00
- Médio: R$ 11.875,00

---

## ⚠️ Códigos de Erro

- `404 Not Found`: Nenhum cálculo encontrado, escola não encontrada, ou parcelas não encontradas
- `500 Internal Server Error`: Erro ao separar valores

---

## 📝 Notas Importantes

1. **Pré-requisito:** É necessário ter cálculos (via `/calculos`) antes de criar parcelas.

2. **Idempotência:** A rota é idempotente. Se já existem parcelas e `recalcular=false`, retorna as existentes.

3. **Valores em Centavos:** Valores são armazenados em centavos (inteiros) para evitar problemas com floats.

4. **Distribuição de Resto:** Centavos restantes são distribuídos para o tipo de ensino com maior porcentagem.

5. **Versionamento:** Cada cálculo tem uma versão para auditoria e rastreabilidade.

6. **Otimização:** A rota usa eager loading para evitar N+1 queries.

7. **Cotas Específicas:** Apenas 8 cotas são processadas (merenda, custeio, preuni, climatização, sala de recurso, uniforme, permanente, kit escolar).

---

## 🔗 Relacionamento com Outras Rotas

### Cálculos → Parcelas

```bash
# 1. Calcular valores
POST /calculos

# 2. Criar parcelas
POST /parcelas
```

### Parcelas → Consulta

```bash
# Ver parcelas de uma escola
GET /parcelas/escola/{escola_id}
```

---

## 🚀 Exemplos de Integração

### Calcular e Criar Parcelas

```javascript
const processarAno = async (anoLetivoId) => {
  // 1. Calcular valores
  await fetch('http://localhost:8000/calculos', {
    method: 'POST',
    params: { ano_letivo_id: anoLetivoId }
  });
  
  // 2. Criar parcelas
  const parcelas = await fetch('http://localhost:8000/parcelas', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ano_letivo_id: anoLetivoId })
  }).then(r => r.json());
  
  console.log(`✅ ${parcelas.escolas_processadas} escolas processadas`);
  console.log(`📊 ${parcelas.total_parcelas_criadas} parcelas criadas`);
  
  return parcelas;
};
```

### Agrupar Parcelas por Cota

```python
import requests

def agrupar_parcelas_por_cota(escola_id):
    response = requests.get(
        f'http://localhost:8000/parcelas/escola/{escola_id}'
    )
    parcelas = response.json()['parcelas']
    
    # Agrupar por cota
    por_cota = {}
    for parcela in parcelas:
        cota = parcela['tipo_cota']
        if cota not in por_cota:
            por_cota[cota] = {
                'parcela_1': {'fundamental': 0, 'medio': 0},
                'parcela_2': {'fundamental': 0, 'medio': 0}
            }
        
        parcela_key = f"parcela_{parcela['numero_parcela']}"
        ensino_key = parcela['tipo_ensino']
        por_cota[cota][parcela_key][ensino_key] += parcela['valor_reais']
    
    return por_cota
```

