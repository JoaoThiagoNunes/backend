# Documentação - Rotas de Uploads

**Arquivo:** `src/modules/routes/upload_routes.py`  
**Prefixo:** `/uploads`

---

## 📋 Visão Geral

Rotas para upload e gerenciamento de arquivos Excel/CSV com dados das escolas. O sistema suporta uploads de arquivos `.xlsx`, `.xls` e `.csv`.

---

## 🔑 Comportamento Importante

### Upload em Ano Ativo

- **Substituição de Dados:** Quando um novo upload é feito para o mesmo ano ativo, os dados das escolas são **substituídos** (UPDATE), não acumulados.
- **Preservação de IDs:** IDs das escolas são **mantidos** quando os dados são atualizados (UPDATE ao invés de DELETE+INSERT).
- **Novos IDs:** Apenas escolas novas recebem novos IDs.

### Arquivos Suportados

- `.xlsx` (Excel 2007+)
- `.xls` (Excel 97-2003)
- `.csv` (CSV)

---

## 📍 Rotas Disponíveis

### 1. **GET /** - Listar Uploads

Lista todos os uploads, opcionalmente filtrados por ano letivo.

**Endpoint:** `GET /uploads`

**Autenticação:** Não requerida

**Query Parameters:**
- `ano_letivo_id` (opcional, int): Filtrar uploads por ano letivo

**Response:**
```json
{
  "success": true,
  "uploads": [
    {
      "id": 1,
      "ano_letivo_id": 2,
      "ano_letivo": 2026,
      "filename": "escolas_2026.xlsx",
      "upload_date": "2026-01-15T10:30:00",
      "total_escolas": 250,
      "is_active": true
    },
    {
      "id": 2,
      "ano_letivo_id": 1,
      "ano_letivo": 2025,
      "filename": "escolas_2025.xlsx",
      "upload_date": "2025-01-15T10:30:00",
      "total_escolas": 250,
      "is_active": false
    }
  ]
}
```

**Exemplo de uso:**

Listar todos os uploads:
```bash
curl http://localhost:8000/uploads
```

Listar uploads de um ano específico:
```bash
curl "http://localhost:8000/uploads?ano_letivo_id=2"
```

---

### 2. **GET /{upload_id}** - Detalhes de um Upload

Retorna detalhes completos de um upload específico, incluindo todas as escolas e seus cálculos (se existirem).

**Endpoint:** `GET /uploads/{upload_id}`

**Autenticação:** Não requerida

**Path Parameters:**
- `upload_id` (int): ID do upload

**Response:**
```json
{
  "success": true,
  "upload": {
    "id": 1,
    "ano_letivo_id": 2,
    "ano_letivo": 2026,
    "filename": "escolas_2026.xlsx",
    "upload_date": "2026-01-15T10:30:00",
    "total_escolas": 250
  },
  "escolas": [
    {
      "escola": {
        "id": 1,
        "nome_uex": "ESCOLA MUNICIPAL EXEMPLO",
        "dre": "DRE-01",
        "total_alunos": 500,
        "fundamental_inicial": 100,
        "fundamental_final": 150,
        "fundamental_integral": 50,
        "profissionalizante": 0,
        "alternancia": 0,
        "ensino_medio_integral": 50,
        "ensino_medio_regular": 150,
        "especial_fund_regular": 0,
        "especial_fund_integral": 0,
        "especial_medio_parcial": 0,
        "especial_medio_integral": 0,
        "sala_recurso": 10,
        "climatizacao": 5,
        "preuni": 0,
        "indigena_quilombola": "NÃO",
        "created_at": "2026-01-15T10:30:00"
      },
      "calculos": {
        "id": 1,
        "profin_custeio": 50000.00,
        "profin_projeto": 10000.00,
        "profin_kit_escolar": 25000.00,
        "profin_uniforme": 20000.00,
        "profin_merenda": 30000.00,
        "profin_sala_recurso": 5000.00,
        "profin_permanente": 15000.00,
        "profin_climatizacao": 10000.00,
        "profin_preuni": 0.00,
        "valor_total": 160000.00,
        "calculated_at": "2026-01-15T11:00:00"
      }
    }
    // ... mais escolas
  ]
}
```

**Erros:**
- `404 Not Found`: Upload não encontrado

**Exemplo de uso:**
```bash
curl http://localhost:8000/uploads/1
```

---

### 3. **POST /excel** - Upload de Arquivo Excel/CSV

Faz upload de um arquivo Excel ou CSV e processa os dados das escolas.

**Endpoint:** `POST /uploads/excel`

**Autenticação:** Não requerida

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file` (file, obrigatório): Arquivo Excel (.xlsx, .xls) ou CSV (.csv)
- `ano_letivo_id` (opcional, int): ID do ano letivo. Se não fornecido, usa o ano ativo.

**Response:**
```json
{
  "success": true,
  "upload_id": 1,
  "ano_letivo_id": 2,
  "ano_letivo": 2026,
  "filename": "escolas_2026.xlsx",
  "total_linhas": 250,
  "escolas_salvas": 250,
  "escolas_confirmadas_banco": 250,
  "escolas_com_erro": 0,
  "colunas": ["NOME DA UEX", "DRE", "TOTAL", "FUNDAMENTAL INICIAL", ...],
  "erros": null,
  "aviso": null
}
```

**Comportamento:**

1. **Determina Ano Letivo:** Se `ano_letivo_id` não for fornecido, usa o ano ativo.
2. **Busca/Cria Upload Ativo:** Busca upload ativo do ano ou cria novo.
3. **Processa Escolas (UPSERT):**
   - Se escola já existe (mesmo `nome_uex` + `dre`): **UPDATE** (mantém ID)
   - Se escola é nova: **INSERT** (novo ID)
   - Escolas que não estão mais no arquivo são **deletadas**
4. **Preserva IDs:** IDs das escolas são mantidos quando dados são atualizados.

**Colunas Esperadas no Arquivo:**

- `NOME DA UEX` (ou `nome`, `Escola`): Nome da escola
- `DRE`: Diretoria Regional de Educação
- `TOTAL`: Total de alunos
- `FUNDAMENTAL INICIAL`: Alunos de fundamental inicial
- `FUNDAMENTAL FINAL`: Alunos de fundamental final
- `FUNDAMENTAL INTEGRAL`: Alunos de fundamental integral
- `PROFISSIONALIZANTE`: Alunos profissionalizantes
- `ALTERNÂNCIA`: Alunos de alternância
- `ENSINO MÉDIO INTEGRAL`: Alunos de ensino médio integral
- `ENSINO MÉDIO REGULAR`: Alunos de ensino médio regular
- `ESPECIAL FUNDAMENTAL REGULAR`: Alunos especiais fundamental regular
- `ESPECIAL FUNDAMENTAL INTEGRAL`: Alunos especiais fundamental integral
- `ESPECIAL MÉDIO PARCIAL`: Alunos especiais médio parcial
- `ESPECIAL MÉDIO INTEGRAL`: Alunos especiais médio integral
- `SALA DE RECURSO`: Alunos em sala de recurso
- `CLIMATIZAÇÃO`: Alunos com climatização
- `PREUNI`: Alunos PREUNI
- `INDIGENA & QUILOMBOLA`: "SIM" ou "NÃO"

**Erros:**
- `400 Bad Request`: Arquivo deve ser Excel (.xlsx, .xls ou .csv)
- `404 Not Found`: Nenhum ano letivo ativo encontrado (se `ano_letivo_id` não fornecido)
- `500 Internal Server Error`: Erro ao processar arquivo

**Exemplo de uso:**

Com curl:
```bash
curl -X POST http://localhost:8000/uploads/excel \
  -F "file=@escolas_2026.xlsx" \
  -F "ano_letivo_id=2"
```

Com Python:
```python
import requests

files = {'file': open('escolas_2026.xlsx', 'rb')}
data = {'ano_letivo_id': 2}

response = requests.post(
    'http://localhost:8000/uploads/excel',
    files=files,
    data=data
)

print(response.json())
```

Com JavaScript (FormData):
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('ano_letivo_id', 2);

const response = await fetch('http://localhost:8000/uploads/excel', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result);
```

---

## 🔄 Fluxo de Trabalho

### 1. Upload Inicial

```bash
POST /uploads/excel
# Arquivo com 250 escolas
# IDs: 1-250
```

### 2. Upload de Atualização (Mesmo Ano)

```bash
POST /uploads/excel
# Arquivo atualizado com 250 escolas (mesmas escolas)
# IDs: 1-250 (mantidos, dados atualizados)
```

### 3. Upload com Novas Escolas

```bash
POST /uploads/excel
# Arquivo com 300 escolas (250 antigas + 50 novas)
# IDs: 1-250 (mantidos), 251-300 (novos)
```

### 4. Upload com Menos Escolas

```bash
POST /uploads/excel
# Arquivo com 200 escolas (50 removidas)
# IDs: 1-200 (mantidos), 201-250 (deletados)
```

---

## 📊 Estrutura de Dados

### UploadListItem

```typescript
{
  id: number;
  ano_letivo_id: number;
  ano_letivo: number;
  filename: string;
  upload_date: string;      // ISO datetime
  total_escolas: number;
  is_active: boolean;
}
```

### UploadDetailInfo

```typescript
{
  id: number;
  ano_letivo_id: number;
  ano_letivo: number;
  filename: string;
  upload_date: string;
  total_escolas: number;
}
```

### UploadExcelResponse

```typescript
{
  success: boolean;
  upload_id: number;
  ano_letivo_id: number;
  ano_letivo: number;
  filename: string;
  total_linhas: number;
  escolas_salvas: number;
  escolas_confirmadas_banco: number;
  escolas_com_erro: number;
  colunas: string[];
  erros: Array<{
    linha: number;
    nome: string;
    erro: string;
  }> | null;
  aviso: string | null;
}
```

---

## ⚠️ Códigos de Erro

- `400 Bad Request`: Arquivo inválido ou formato não suportado
- `404 Not Found`: Upload ou ano letivo não encontrado
- `500 Internal Server Error`: Erro ao processar arquivo

---

## 📝 Notas Importantes

1. **Preservação de IDs:** IDs das escolas são mantidos quando dados são atualizados dentro do mesmo ano ativo.

2. **Substituição vs. Acumulação:** Dados são **substituídos**, não acumulados. Cada upload substitui os dados anteriores do ano ativo.

3. **Erros de Processamento:** Se algumas escolas tiverem erro ao processar, elas são registradas em `erros` mas o upload continua para as outras.

4. **Validação de Dados:** O sistema valida automaticamente os dados (ex: `INDIGENA & QUILOMBOLA` deve ser "SIM" ou "NÃO").

5. **Upload Ativo:** Cada ano letivo tem apenas um upload ativo por vez. Novos uploads substituem o upload ativo anterior.

