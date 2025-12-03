# Documentação - Rotas de Administração

**Arquivo:** `src/modules/routes/admin_routes.py`  
**Prefixo:** `/admin`

---

## 📋 Visão Geral

Rotas administrativas para gerenciamento da API, autenticação, status do sistema e limpeza de dados.

---

## 🔐 Autenticação

A maioria das rotas requer autenticação via JWT. Para obter o token:

1. Faça login em `POST /admin/login`
2. Use o token retornado no header: `Authorization: Bearer <token>`

---

## 📍 Rotas Disponíveis

### 1. **GET /** - Endpoint Raiz

Retorna informações básicas da API.

**Endpoint:** `GET /admin/`

**Autenticação:** Não requerida

**Response:**
```json
{
  "message": "API funcionando!",
  "versao": "2.0 - Com Anos Letivos"
}
```

**Exemplo de uso:**
```bash
curl http://localhost:8000/admin/
```

---

### 2. **POST /login** - Autenticação

Autentica o usuário e retorna um token JWT válido por 12 horas.

**Endpoint:** `POST /admin/login`

**Autenticação:** Não requerida

**Request Body:**
```json
{
  "password": "profin2025"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "message": "Login realizado com sucesso"
}
```

**Erros:**
- `401 Unauthorized`: Senha incorreta

**Exemplo de uso:**
```bash
curl -X POST http://localhost:8000/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password": "profin2025"}'
```

**Nota:** A senha padrão é `profin2025`, mas pode ser alterada via variável de ambiente `ADMIN_PASSWORD`.

---

### 3. **DELETE /limpar-dados** - Limpar Dados

⚠️ **CUIDADO:** Esta rota apaga dados do banco de dados.

**Endpoint:** `DELETE /admin/limpar-dados`

**Autenticação:** ✅ Requerida (Bearer Token)

**Query Parameters:**
- `ano_letivo_id` (opcional): Se fornecido, apaga apenas um ano específico. Se não fornecido, apaga **TUDO**.

**Response:**
```json
{
  "success": true,
  "message": "✅ Ano letivo 2025 e todos os dados relacionados foram removidos"
}
```

**Exemplo de uso:**

Limpar apenas um ano:
```bash
curl -X DELETE "http://localhost:8000/admin/limpar-dados?ano_letivo_id=1" \
  -H "Authorization: Bearer <token>"
```

Limpar tudo:
```bash
curl -X DELETE http://localhost:8000/admin/limpar-dados \
  -H "Authorization: Bearer <token>"
```

**Aviso:** Esta operação é **irreversível**!

---

### 4. **GET /status-dados** - Status do Banco de Dados

Retorna estatísticas gerais do banco de dados e informações sobre todos os anos letivos.

**Endpoint:** `GET /admin/status-dados`

**Autenticação:** Não requerida

**Response:**
```json
{
  "success": true,
  "resumo": {
    "total_anos_letivos": 2,
    "total_uploads": 3,
    "total_escolas": 500,
    "total_calculos": 500
  },
  "ano_ativo": {
    "id": 2,
    "ano": 2026,
    "status": "ATIVO"
  },
  "anos": [
    {
      "id": 2,
      "ano": 2026,
      "status": "ATIVO",
      "uploads": 1,
      "escolas": 250,
      "created_at": "2026-01-01T00:00:00",
      "arquivado_em": null
    },
    {
      "id": 1,
      "ano": 2025,
      "status": "ARQUIVADO",
      "uploads": 2,
      "escolas": 250,
      "created_at": "2025-01-01T00:00:00",
      "arquivado_em": "2026-01-01T00:00:00"
    }
  ]
}
```

**Exemplo de uso:**
```bash
curl http://localhost:8000/admin/status-dados
```

**Otimização:** Esta rota usa eager loading para evitar N+1 queries, carregando anos, uploads e escolas em uma única query otimizada.

---

### 5. **GET /health** - Health Check

Retorna o status de saúde da API.

**Endpoint:** `GET /admin/health`

**Autenticação:** Não requerida

**Response:**
```json
{
  "status": "healthy",
  "versao": "2.0",
  "features": [
    "anos_letivos",
    "arquivamento_automatico",
    "isolamento_por_ano"
  ]
}
```

**Exemplo de uso:**
```bash
curl http://localhost:8000/admin/health
```

---

## 🔒 Segurança

### Tokens JWT

- **Validade:** 24 horas (configurável via `ACCESS_TOKEN_EXPIRE_HOURS`)
- **Algoritmo:** HS256
- **Uso:** Incluir no header `Authorization: Bearer <token>`

### Senha Admin

- **Padrão:** `profin2024`
- **Configuração:** Via variável de ambiente `ADMIN_PASSWORD`
- **Recomendação:** Alterar em produção!

---

## 📝 Notas Importantes

1. **Limpeza de Dados:** A rota `DELETE /limpar-dados` é protegida por autenticação e deve ser usada com cuidado.

2. **Status de Dados:** A rota `/status-dados` é otimizada com eager loading para melhor performance.

3. **Health Check:** Use `/health` para monitoramento e verificação de disponibilidade da API.

---

## 🚀 Exemplos de Integração

### JavaScript/TypeScript (fetch)

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/admin/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ password: 'profin2024' })
});

const { access_token } = await loginResponse.json();

// Usar token em requisições protegidas
const statusResponse = await fetch('http://localhost:8000/admin/status-dados', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
```

### Python (requests)

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/admin/login',
    json={'password': 'profin2024'}
)
token = response.json()['access_token']

# Usar token
headers = {'Authorization': f'Bearer {token}'}
status = requests.get(
    'http://localhost:8000/admin/status-dados',
    headers=headers
)
```

---

## ⚠️ Códigos de Erro

- `400 Bad Request`: Requisição inválida
- `401 Unauthorized`: Token inválido ou senha incorreta
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro interno do servidor

