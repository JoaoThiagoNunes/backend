# 📚 DOCUMENTAÇÃO COMPLETA DA API - PROFIN

## 🔗 **Base URL**
```
http://localhost:8000
```

## 📋 **Índice**
- [Autenticação](#autenticação)
- [Anos Letivos](#anos-letivos)
- [Uploads](#uploads)
- [Cálculos](#cálculos)
- [Admin](#admin)

---

## 🔐 **AUTENTICAÇÃO**

### **POST /admin/login**
Login para obter token JWT.

**Request:**
```json
POST /admin/login
Content-Type: application/json

{
  "password": "profin2024"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "message": "Login realizado com sucesso"
}
```

**Response (401):**
```json
{
  "detail": "Senha incorreta"
}
```

**Uso do Token:**
```
Authorization: Bearer <access_token>
```

---

## 📅 **ANOS LETIVOS**

### **GET /anos/**
Lista todos os anos letivos.

**Request:**
```http
GET /anos/
```

**Response (200):**
```json
{
  "success": true,
  "anos": [
    {
      "id": 1,
      "ano": 2024,
      "status": "ATIVO",
      "created_at": "2024-01-15T10:00:00",
      "arquivado_em": null,
      "total_uploads": 3
    }
  ]
}
```

---

### **GET /anos/ativo**
Retorna o ano letivo ativo atual.

**Request:**
```http
GET /anos/ativo
```

**Response (200):**
```json
{
  "success": true,
  "ano": {
    "id": 1,
    "ano": 2024,
    "status": "ATIVO",
    "created_at": "2024-01-15T10:00:00",
    "total_uploads": 3
  }
}
```

**Response (404):**
```json
{
  "detail": "Nenhum ano letivo ativo encontrado"
}
```

---

### **POST /anos/**
Cria um novo ano letivo.

**Request:**
```json
POST /anos/
Content-Type: application/json

{
  "ano": 2024
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Ano letivo 2024 criado com sucesso",
  "ano": {
    "id": 1,
    "ano": 2024,
    "status": "ATIVO",
    "created_at": "2024-01-15T10:00:00"
  }
}
```

**Response (400):**
```json
{
  "detail": "Ano letivo 2024 já existe"
}
```

---

### **PUT /anos/{ano_id}/arquivar**
Arquiva um ano letivo.

**Request:**
```http
PUT /anos/1/arquivar
```

**Response (200):**
```json
{
  "success": true,
  "message": "Ano letivo 2024 arquivado com sucesso",
  "ano": {
    "id": 1,
    "ano": 2024,
    "status": "ARQUIVADO",
    "arquivado_em": "2024-12-31T23:59:59"
  }
}
```

---

### **DELETE /anos/{ano_id}**
Deleta um ano letivo e todos os dados relacionados.

**Request:**
```http
DELETE /anos/1
```

**Response (200):**
```json
{
  "success": true,
  "message": "Ano letivo 2024 e todos os dados relacionados foram deletados"
}
```

---

## 📤 **UPLOADS**

### **GET /uploads/**
Lista todos os uploads, opcionalmente filtrados por ano letivo.

**Request:**
```http
GET /uploads/?ano_letivo_id=1
```

**Response (200):**
```json
{
  "success": true,
  "uploads": [
    {
      "id": 1,
      "ano_letivo_id": 1,
      "ano_letivo": 2024,
      "filename": "escolas_2024.xlsx",
      "upload_date": "2024-01-15T10:30:00",
      "total_escolas": 318,
      "is_active": true
    }
  ]
}
```

---

### **GET /uploads/{upload_id}**
Retorna detalhes de um upload com suas escolas e cálculos.

**Request:**
```http
GET /uploads/1
```

**Response (200):**
```json
{
  "success": true,
  "upload": {
    "id": 1,
    "ano_letivo_id": 1,
    "ano_letivo": 2024,
    "filename": "escolas_2024.xlsx",
    "upload_date": "2024-01-15T10:30:00",
    "total_escolas": 318
  },
  "escolas": [
    {
      "escola": {
        "id": 1,
        "nome_uex": "Escola ABC",
        "dre": "DRE-01",
        "total_alunos": 500,
        "created_at": "2024-01-15T10:30:00"
      },
      "calculos": {
        "id": 1,
        "profin_custeio": 50000.00,
        "profin_projeto": 10000.00,
        "profin_kit_escolar": 75000.00,
        "profin_uniforme": 30000.00,
        "profin_merenda": 17500.00,
        "profin_sala_recurso": 2000.00,
        "profin_permanente": 55000.00,
        "profin_climatizacao": 0.00,
        "profin_preuni": 0.00,
        "valor_total": 237500.00,
        "calculated_at": "2024-01-15T10:35:00"
      }
    }
  ]
}
```

---

### **POST /uploads/excel**
Upload de arquivo Excel com dados das escolas.

**Request:**
```http
POST /uploads/excel
Content-Type: multipart/form-data

file: [arquivo.xlsx]
ano_letivo_id: 1 (opcional - usa ano ativo se não informado)
```

**Response (200):**
```json
{
  "success": true,
  "upload_id": 1,
  "ano_letivo_id": 1,
  "ano_letivo": 2024,
  "filename": "escolas_2024.xlsx",
  "total_linhas": 318,
  "escolas_salvas": 318,
  "escolas_confirmadas_banco": 318,
  "escolas_com_erro": 0,
  "colunas": ["NOME DA UEX", "DRE", "TOTAL", ...],
  "erros": null,
  "aviso": null
}
```

**Response com erros:**
```json
{
  "success": true,
  "upload_id": 1,
  "escolas_salvas": 315,
  "escolas_com_erro": 3,
  "erros": [
    {
      "linha": 50,
      "nome": "Escola XYZ",
      "erro": "Erro ao processar linha"
    }
  ],
  "aviso": "3 escolas tiveram erro ao salvar"
}
```

---

## 🧮 **CÁLCULOS**

### **POST /calculos/**
Calcula valores das escolas de um ano letivo.

**Request:**
```http
POST /calculos/?ano_letivo_id=1
```

**Response (200):**
```json
{
  "success": true,
  "message": "Cálculos realizados para 318 escolas do ano 2024",
  "total_escolas": 318,
  "valor_total_geral": 75000000.00,
  "upload_id": 1,
  "ano_letivo_id": 1,
  "escolas": [
    {
      "id": 1,
      "dre": "DRE-01",
      "nome_uex": "Escola ABC",
      "profin_custeio": 50000.00,
      "profin_projeto": 10000.00,
      "profin_kit_escolar": 75000.00,
      "profin_uniforme": 30000.00,
      "profin_merenda": 17500.00,
      "profin_sala_recurso": 2000.00,
      "profin_permanente": 55000.00,
      "profin_climatizacao": 0.00,
      "profin_preuni": 0.00,
      "valor_total": 237500.00
    }
  ]
}
```

---

## ⚙️ **ADMIN**

### **GET /admin/**
Endpoint raiz da API.

**Request:**
```http
GET /admin/
```

**Response (200):**
```json
{
  "message": "API funcionando!",
  "versao": "2.0 - Com Anos Letivos"
}
```

---

### **GET /admin/status-dados**
Estatísticas gerais do banco de dados.

**Request:**
```http
GET /admin/status-dados
```

**Response (200):**
```json
{
  "success": true,
  "resumo": {
    "total_anos_letivos": 3,
    "total_uploads": 5,
    "total_escolas": 1500,
    "total_calculos": 1500
  },
  "ano_ativo": {
    "id": 1,
    "ano": 2024,
    "status": "ATIVO"
  },
  "anos": [
    {
      "id": 1,
      "ano": 2024,
      "status": "ATIVO",
      "uploads": 3,
      "escolas": 318,
      "created_at": "2024-01-15T10:00:00",
      "arquivado_em": null
    }
  ]
}
```

---

### **GET /admin/health**
Health check da API.

**Request:**
```http
GET /admin/health
```

**Response (200):**
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

---

### **DELETE /admin/limpar-dados**
⚠️ **CUIDADO: Apaga dados do banco!** Requer autenticação.

**Request:**
```http
DELETE /admin/limpar-dados?ano_letivo_id=1
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "✅ Ano letivo 2024 e todos os dados relacionados foram removidos"
}
```

---

## 📊 **TIPOS DE ERRO**

### **400 - Bad Request**
```json
{
  "detail": "Mensagem de erro específica"
}
```

### **401 - Unauthorized**
```json
{
  "detail": "Token inválido ou expirado"
}
```

### **404 - Not Found**
```json
{
  "detail": "Recurso não encontrado"
}
```

### **500 - Internal Server Error**
```json
{
  "detail": "Erro ao processar arquivo: [detalhes]"
}
```

---

## 💡 **EXEMPLOS DE USO NO FRONTEND**

### **JavaScript/TypeScript (fetch):**

```javascript
// 1. Login
async function login(password) {
  const response = await fetch('http://localhost:8000/admin/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password })
  });
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  return data;
}

// 2. Listar anos letivos
async function getAnosLetivos() {
  const response = await fetch('http://localhost:8000/anos/');
  return await response.json();
}

// 3. Obter ano ativo
async function getAnoAtivo() {
  const response = await fetch('http://localhost:8000/anos/ativo');
  return await response.json();
}

// 4. Upload de arquivo
async function uploadExcel(file, anoLetivoId = null) {
  const formData = new FormData();
  formData.append('file', file);
  if (anoLetivoId) {
    formData.append('ano_letivo_id', anoLetivoId);
  }
  
  const response = await fetch('http://localhost:8000/uploads/excel', {
    method: 'POST',
    body: formData
  });
  return await response.json();
}

// 5. Calcular valores
async function calcularValores(anoLetivoId = null) {
  const url = anoLetivoId 
    ? `http://localhost:8000/calculos/?ano_letivo_id=${anoLetivoId}`
    : 'http://localhost:8000/calculos/';
    
  const response = await fetch(url, {
    method: 'POST'
  });
  return await response.json();
}

// 6. Requisição autenticada
async function limparDados(anoLetivoId = null) {
  const token = localStorage.getItem('token');
  const url = anoLetivoId
    ? `http://localhost:8000/admin/limpar-dados?ano_letivo_id=${anoLetivoId}`
    : 'http://localhost:8000/admin/limpar-dados';
    
  const response = await fetch(url, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
}
```

### **React Hook Example:**

```typescript
// hooks/useProfinAPI.ts
import { useState, useEffect } from 'react';

export function useAnosLetivos() {
  const [anos, setAnos] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetch('http://localhost:8000/anos/')
      .then(res => res.json())
      .then(data => {
        setAnos(data.anos);
        setLoading(false);
      });
  }, []);
  
  return { anos, loading };
}
```

---

## 🔄 **FLUXO TÍPICO DE USO**

1. **Inicialização:**
   - `GET /anos/ativo` → Obter ano letivo ativo
   
2. **Upload de dados:**
   - `POST /uploads/excel` → Enviar planilha
   - Aguardar resposta com `upload_id`
   
3. **Cálculos:**
   - `POST /calculos/` → Calcular valores
   - Aguardar resposta com valores calculados
   
4. **Visualização:**
   - `GET /uploads/{upload_id}` → Ver escolas e cálculos
   - `GET /anos/` → Listar todos os anos

---

## 📝 **OBSERVAÇÕES IMPORTANTES**

1. **Todas as rotas retornam `success: true`** quando bem-sucedidas
2. **Erros sempre retornam `detail`** com mensagem
3. **Upload sempre limpa uploads anteriores do mesmo ano**
4. **Cálculos são upsert** (atualiza se existe, cria se não existe)
5. **Ano letivo ativo**: Apenas um pode estar ativo por vez

---

## 🎯 **PRÓXIMOS PASSOS**

Com esta documentação, você pode:
- ✅ Integrar o frontend com o backend
- ✅ Entender todas as rotas disponíveis
- ✅ Saber formatos de requisição/resposta
- ✅ Tratar erros adequadamente

Se precisar de ajuda específica com alguma integração, me avise!

