# Documentação - Rotas de Anos Letivos

**Arquivo:** `src/modules/routes/ano_routes.py`  
**Prefixo:** `/anos`

---

## 📋 Visão Geral

Rotas para gerenciamento de anos letivos. O sistema suporta apenas **um ano letivo ATIVO** por vez. Quando um novo ano é criado, o ano anterior é automaticamente arquivado (mas seus dados são preservados).

---

## 🔑 Conceitos Importantes

### Status de Ano Letivo

- **ATIVO:** Ano letivo em uso atualmente. Apenas um pode estar ativo.
- **ARQUIVADO:** Ano letivo encerrado, mas dados históricos preservados.

### Comportamento

- Ao criar um novo ano, o ano ativo anterior é **automaticamente arquivado**
- Dados históricos (uploads, escolas, cálculos) são **preservados** quando um ano é arquivado
- Anos arquivados são mantidos por 5 anos antes de serem deletados automaticamente

---

## 📍 Rotas Disponíveis

### 1. **GET /** - Listar Todos os Anos Letivos

Lista todos os anos letivos (ativos e arquivados), ordenados por ano (mais recente primeiro).

**Endpoint:** `GET /anos`

**Autenticação:** Não requerida

**Response:**
```json
{
  "success": true,
  "anos": [
    {
      "id": 2,
      "ano": 2026,
      "status": "ATIVO",
      "created_at": "2026-01-01T00:00:00",
      "arquivado_em": null,
      "total_uploads": 1
    },
    {
      "id": 1,
      "ano": 2025,
      "status": "ARQUIVADO",
      "created_at": "2025-01-01T00:00:00",
      "arquivado_em": "2026-01-01T00:00:00",
      "total_uploads": 2
    }
  ]
}
```

**Exemplo de uso:**
```bash
curl http://localhost:8000/anos
```

---

### 2. **GET /ativo** - Obter Ano Letivo Ativo

Retorna informações sobre o ano letivo ativo atual.

**Endpoint:** `GET /anos/ativo`

**Autenticação:** Não requerida

**Response:**
```json
{
  "success": true,
  "ano": {
    "id": 2,
    "ano": 2026,
    "status": "ATIVO",
    "created_at": "2026-01-01T00:00:00",
    "total_uploads": 1
  }
}
```

**Erros:**
- `404 Not Found`: Nenhum ano letivo ativo encontrado

**Exemplo de uso:**
```bash
curl http://localhost:8000/anos/ativo
```

---

### 3. **POST /** - Criar Novo Ano Letivo

Cria um novo ano letivo e o define como ATIVO. O ano ativo anterior é automaticamente arquivado.

**Endpoint:** `POST /anos`

**Autenticação:** Não requerida

**Request Body:**
```json
{
  "ano": 2026
}
```

**Response:**
```json
{
  "success": true,
  "message": "Ano letivo 2026 criado com sucesso",
  "ano": {
    "id": 2,
    "ano": 2026,
    "status": "ATIVO",
    "created_at": "2026-01-01T00:00:00"
  }
}
```

**Erros:**
- `400 Bad Request`: Ano letivo já existe

**Comportamento:**
- Se já existe um ano ativo, ele é **automaticamente arquivado**
- Dados históricos do ano anterior são **preservados**
- O novo ano é criado como ATIVO

**Exemplo de uso:**
```bash
curl -X POST http://localhost:8000/anos \
  -H "Content-Type: application/json" \
  -d '{"ano": 2026}'
```

---

### 4. **PUT /{ano_id}/arquivar** - Arquivar Ano Letivo Manualmente

Arquiva um ano letivo específico manualmente.

**Endpoint:** `PUT /anos/{ano_id}/arquivar`

**Autenticação:** Não requerida

**Path Parameters:**
- `ano_id` (int): ID do ano letivo a ser arquivado

**Response:**
```json
{
  "success": true,
  "message": "Ano letivo 2025 arquivado com sucesso",
  "ano": {
    "id": 1,
    "ano": 2025,
    "status": "ARQUIVADO",
    "arquivado_em": "2026-01-01T12:00:00"
  }
}
```

**Erros:**
- `404 Not Found`: Ano letivo não encontrado
- `400 Bad Request`: Ano letivo já está arquivado

**Exemplo de uso:**
```bash
curl -X PUT http://localhost:8000/anos/1/arquivar
```

---

### 5. **DELETE /{ano_id}** - Deletar Ano Letivo

Deleta um ano letivo e **todos os dados relacionados** (uploads, escolas, cálculos, parcelas).

⚠️ **CUIDADO:** Esta operação é **irreversível**!

**Endpoint:** `DELETE /anos/{ano_id}`

**Autenticação:** Não requerida (mas recomendado proteger em produção)

**Path Parameters:**
- `ano_id` (int): ID do ano letivo a ser deletado

**Response:**
```json
{
  "success": true,
  "message": "Ano letivo 2025 e todos os dados relacionados foram deletados"
}
```

**Erros:**
- `404 Not Found`: Ano letivo não encontrado

**Comportamento:**
- Deleta o ano letivo e **cascade** deleta todos os dados relacionados:
  - Uploads
  - Escolas
  - Cálculos
  - Parcelas

**Exemplo de uso:**
```bash
curl -X DELETE http://localhost:8000/anos/1
```

**Nota:** Anos arquivados são deletados automaticamente após 5 anos pelo scheduler.

---

## 🔄 Fluxo de Trabalho Típico

### 1. Criar Ano Letivo

```bash
POST /anos
{
  "ano": 2026
}
```

### 2. Fazer Upload de Dados

```bash
POST /uploads/excel
# Upload de arquivo Excel com dados das escolas
```

### 3. Calcular Valores

```bash
POST /calculos
# Calcula valores PROFIN para todas as escolas
```

### 4. Criar Parcelas

```bash
POST /parcelas
# Divide valores em parcelas e por tipo de ensino
```

### 5. Criar Novo Ano (Arquivar Atual)

Quando o ano termina, criar um novo ano automaticamente arquiva o anterior:

```bash
POST /anos
{
  "ano": 2027
}
# Ano 2026 é automaticamente arquivado
```

---

## 📊 Estrutura de Dados

### AnoLetivo

```typescript
{
  id: number;
  ano: number;              // Ex: 2025, 2026
  status: "ATIVO" | "ARQUIVADO";
  created_at: string;       // ISO datetime
  arquivado_em: string | null;  // ISO datetime (null se ativo)
  total_uploads?: number;  // Quantidade de uploads
}
```

---

## 🚀 Exemplos de Integração

### JavaScript/TypeScript

```javascript
// Criar novo ano letivo
const criarAno = async (ano) => {
  const response = await fetch('http://localhost:8000/anos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ano })
  });
  return response.json();
};

// Obter ano ativo
const obterAnoAtivo = async () => {
  const response = await fetch('http://localhost:8000/anos/ativo');
  return response.json();
};

// Listar todos os anos
const listarAnos = async () => {
  const response = await fetch('http://localhost:8000/anos');
  return response.json();
};
```

### Python

```python
import requests

# Criar novo ano letivo
def criar_ano(ano):
    response = requests.post(
        'http://localhost:8000/anos',
        json={'ano': ano}
    )
    return response.json()

# Obter ano ativo
def obter_ano_ativo():
    response = requests.get('http://localhost:8000/anos/ativo')
    return response.json()
```

---

## ⚠️ Códigos de Erro

- `400 Bad Request`: Ano letivo já existe ou já está arquivado
- `404 Not Found`: Ano letivo não encontrado
- `500 Internal Server Error`: Erro interno do servidor

---

## 📝 Notas Importantes

1. **Isolamento de Dados:** Cada ano letivo mantém seus dados isolados. Uploads, escolas e cálculos são vinculados a um ano específico.

2. **Arquivamento Automático:** Quando um novo ano é criado, o ano anterior é automaticamente arquivado, mas seus dados são preservados.

3. **Deleção em Cascade:** Ao deletar um ano letivo, todos os dados relacionados são deletados automaticamente.

4. **Scheduler:** Anos arquivados há mais de 5 anos são deletados automaticamente pelo scheduler (executado diariamente).

