# 🔐 Sistema de Autenticação - Documentação Completa

## 📋 Visão Geral

Foi implementado um sistema de autenticação simples e eficiente que protege apenas os endpoints críticos (especialmente `/admin/limpar-dados`). O sistema usa **JWT (JSON Web Tokens)** e permite autenticação sem necessidade de banco de dados de usuários.

---

## 🏗️ Arquitetura do Sistema

### 1. **Arquivo Principal: `src/core/auth.py`**

Este arquivo contém toda a lógica de autenticação.

#### **Componentes Principais:**

```python
# Configurações de Segurança
SECRET_KEY          # Chave secreta para assinar tokens (variável de ambiente)
ADMIN_PASSWORD      # Senha do admin (variável de ambiente, padrão: "profin2024")
ACCESS_TOKEN_EXPIRE_HOURS = 24  # Tempo de validade do token
```

#### **Funções Principais:**

1. **`authenticate_admin(password: str) -> bool`**
   - Verifica se a senha fornecida está correta
   - Compara com a senha armazenada em `ADMIN_PASSWORD`

2. **`create_access_token(data: dict) -> str`**
   - Cria um token JWT válido por 24 horas
   - Inclui dados do usuário (ex: `{"sub": "admin", "role": "admin"}`)
   - Token é assinado com `SECRET_KEY`

3. **`verify_token(credentials) -> dict`**
   - Verifica se um token é válido e não expirou
   - Decodifica o token e retorna os dados
   - Usado automaticamente pelo FastAPI

4. **`get_current_admin(token_data: dict) -> dict`**
   - **Dependência do FastAPI** para proteger endpoints
   - Garante que o usuário está autenticado
   - Se o token for inválido, retorna erro 401

---

### 2. **Endpoint de Login: `POST /admin/login`**

#### **Localização:** `src/modules/routes/admin_routes.py`

#### **Como Funciona:**

1. Cliente envia senha:
```json
POST /admin/login
{
  "password": "profin2024"
}
```

2. Sistema verifica senha:
   - Compara com `ADMIN_PASSWORD` (variável de ambiente)
   - Se correto: gera token JWT
   - Se incorreto: retorna erro 401

3. Resposta de sucesso:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "message": "Login realizado com sucesso"
}
```

#### **Senha Padrão:**
- **Desenvolvimento:** `profin2024`
- **Produção:** Configure via variável de ambiente `ADMIN_PASSWORD`

---

### 3. **Endpoints Protegidos**

#### **Como Proteger um Endpoint:**

Adicione a dependência `get_current_admin`:

```python
@router.delete("/limpar-dados", tags=["Admin"])
def limpar_todos_dados(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)  # ← Proteção aqui
):
    # Esta função só será executada se o token for válido
    ...
```

#### **Endpoints Atualmente Protegidos:**

- ✅ `DELETE /admin/limpar-dados` - Apaga dados do banco

#### **Endpoints Públicos (sem autenticação):**

- `GET /admin/` - Status da API
- `GET /admin/status-dados` - Estatísticas
- `GET /admin/health` - Health check
- `POST /admin/login` - Endpoint de login
- Todos os outros endpoints (`/uploads/*`, `/calculos/*`, `/anos/*`)

---

### 4. **Como Usar no Frontend/Cliente**

#### **Passo 1: Fazer Login**

```javascript
// Exemplo em JavaScript/fetch
const loginResponse = await fetch('http://localhost:8000/admin/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ password: 'profin2024' })
});

const { access_token } = await loginResponse.json();
// Salvar o token (localStorage, sessionStorage, etc.)
```

#### **Passo 2: Usar Token em Requisições Protegidas**

```javascript
// Fazer requisição protegida
const response = await fetch('http://localhost:8000/admin/limpar-dados', {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${access_token}`,  // ← Token aqui
    'Content-Type': 'application/json'
  }
});
```

#### **Formato do Header:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### 5. **Variáveis de Ambiente**

Crie um arquivo `.env` na raiz do projeto:

```env
# Autenticação
SECRET_KEY=seu-secret-key-super-seguro-aqui-2024
ADMIN_PASSWORD=senha-secreta-do-admin

# Banco de Dados (já existentes)
DB_USER=postgres
DB_PASS=123456
DB_HOST=localhost
DB_PORT=5432
DB_NAME=profin_db
```

#### **O que cada variável faz:**

- **`SECRET_KEY`**: Chave para assinar tokens JWT. **Mude em produção!**
- **`ADMIN_PASSWORD`**: Senha do admin. **Mude em produção!**

**Valores padrão (se não configurados):**
- `SECRET_KEY` = `"profin-secret-key-change-in-production-2024"`
- `ADMIN_PASSWORD` = `"profin2024"`

---

### 6. **Schemas Pydantic**

#### **Arquivo:** `src/modules/schemas/auth.py`

Define estruturas de dados para validação:

- **`LoginRequest`**: Requisição de login (senha)
- **`LoginResponse`**: Resposta de login (token)

---

## 🔒 Segurança

### **O que está protegido:**
- ✅ Tokens são assinados com chave secreta
- ✅ Tokens expiram em 24 horas
- ✅ Validação automática em cada requisição
- ✅ Endpoints críticos requerem autenticação

### **Recomendações para Produção:**

1. **Mude `SECRET_KEY`** para uma chave forte e aleatória
2. **Mude `ADMIN_PASSWORD`** para senha segura
3. **Use HTTPS** em produção
4. **Considere reduzir tempo de expiração** do token (opcional)

---

## 📝 Fluxo Completo de Autenticação

```
┌─────────┐                    ┌─────────────┐                    ┌──────────┐
│ Cliente │                    │    API      │                    │  Banco   │
└────┬────┘                    └──────┬──────┘                    └────┬─────┘
     │                                │                               │
     │  1. POST /admin/login           │                               │
     │     {password: "..."}           │                               │
     ├────────────────────────────────>│                               │
     │                                │                               │
     │                                │ 2. Verifica senha             │
     │                                │    (compara com env var)      │
     │                                │                               │
     │                                │ 3. Gera token JWT             │
     │                                │                               │
     │  4. {access_token: "..."}      │                               │
     │<────────────────────────────────│                               │
     │                                │                               │
     │  5. DELETE /admin/limpar-dados  │                               │
     │     Authorization: Bearer ...   │                               │
     ├────────────────────────────────>│                               │
     │                                │                               │
     │                                │ 6. Verifica token             │
     │                                │    (valida assinatura, data)  │
     │                                │                               │
     │                                │ 7. Executa ação               │
     │                                ├───────────────────────────────>│
     │                                │                               │
     │                                │ 8. Retorna resultado          │
     │                                │<───────────────────────────────┤
     │  9. {success: true, ...}       │                               │
     │<────────────────────────────────│                               │
     │                                │                               │
```

---

## 🧪 Testando a Autenticação

### **1. Testar Login (Sucesso):**

```bash
curl -X POST "http://localhost:8000/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"password": "profin2024"}'
```

**Resposta esperada:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "message": "Login realizado com sucesso"
}
```

### **2. Testar Login (Falha):**

```bash
curl -X POST "http://localhost:8000/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"password": "senha-errada"}'
```

**Resposta esperada:**
```json
{
  "detail": "Senha incorreta"
}
```

### **3. Testar Endpoint Protegido (SEM token):**

```bash
curl -X DELETE "http://localhost:8000/admin/limpar-dados"
```

**Resposta esperada:**
```json
{
  "detail": "Not authenticated"
}
```

### **4. Testar Endpoint Protegido (COM token):**

```bash
# Primeiro, obter token (substitua TOKEN_AQUI pelo token real)
curl -X DELETE "http://localhost:8000/admin/limpar-dados" \
  -H "Authorization: Bearer TOKEN_AQUI"
```

---

## 📦 Dependências Adicionadas

```txt
python-jose[cryptography]==3.3.0  # Para trabalhar com JWT
passlib[bcrypt]==1.7.4             # Para hash de senhas (disponível para expansão)
```

**Para instalar:**
```bash
pip install -r requirements.txt
```

---

## 🎯 Resumo dos Arquivos Modificados/Criados

1. ✅ **`src/core/auth.py`** - Sistema de autenticação completo
2. ✅ **`src/modules/schemas/auth.py`** - Schemas de autenticação
3. ✅ **`src/modules/routes/admin_routes.py`** - Adicionado endpoint `/login` e proteção em `/limpar-dados`
4. ✅ **`requirements.txt`** - Adicionadas dependências de autenticação
5. ✅ **`src/modules/schemas/__init__.py`** - Exportação dos novos schemas

---

## ❓ Perguntas Frequentes

**Q: Por que apenas alguns endpoints estão protegidos?**  
A: Por ser um sistema interno, protegemos apenas operações críticas (ex: apagar dados). Uploads e cálculos permanecem públicos para facilitar o uso.

**Q: Posso adicionar mais usuários?**  
A: A estrutura atual suporta apenas um admin. Para múltiplos usuários, seria necessário banco de dados de usuários (pode ser adicionado depois se necessário).

**Q: O token expira quando?**  
A: 24 horas após o login. Após isso, é necessário fazer login novamente.

**Q: Posso proteger outros endpoints?**  
A: Sim! Basta adicionar `current_admin: dict = Depends(get_current_admin)` como parâmetro da função.

---

## ✅ Próximos Passos (Opcionais)

- [ ] Adicionar refresh token para renovar tokens sem login
- [ ] Adicionar múltiplos usuários com banco de dados
- [ ] Adicionar auditoria (quem fez login, quando, etc.)
- [ ] Adicionar roles/permissões (admin, usuário comum, etc.)

