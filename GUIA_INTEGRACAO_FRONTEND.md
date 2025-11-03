# 🔗 Guia de Integração Frontend - PROFIN API

## 🎯 **Como Trabalhar Junto no Frontend**

### **Opção 1: Compartilhar o Projeto Frontend**
Você pode:
1. **Abrir o projeto frontend no Cursor** (mesma janela ou outra)
2. **Copiar arquivos principais** para este workspace
3. **Me dizer qual framework** você está usando

### **Opção 2: Me Passar Informações**
Me conte:
- ✅ Qual framework? (React, Vue, Angular, Next.js, etc.)
- ✅ Como está estruturado? (pastas, arquivos principais)
- ✅ O que já está funcionando?
- ✅ O que precisa de ajuda?

### **Opção 3: Criar Arquivos de Integração**
Posso criar:
- ✅ Funções/services prontas para usar
- ✅ Hooks customizados (se for React)
- ✅ Tipos TypeScript (se usar TS)
- ✅ Exemplos de componentes

---

## 📋 **Estrutura de Dados - Resumo**

### **Ano Letivo**
```typescript
interface AnoLetivo {
  id: number;
  ano: number;
  status: "ATIVO" | "ARQUIVADO";
  created_at: string;
  arquivado_em?: string;
  total_uploads?: number;
}
```

### **Upload**
```typescript
interface Upload {
  id: number;
  ano_letivo_id: number;
  ano_letivo: number;
  filename: string;
  upload_date: string;
  total_escolas: number;
  is_active: boolean;
}
```

### **Escola**
```typescript
interface Escola {
  id: number;
  nome_uex: string;
  dre?: string;
  total_alunos: number;
  // ... outros campos de modalidades
}
```

### **Cálculo**
```typescript
interface Calculo {
  id: number;
  escola_id: number;
  profin_custeio: number;
  profin_projeto: number;
  profin_kit_escolar: number;
  profin_uniforme: number;
  profin_merenda: number;
  profin_sala_recurso: number;
  profin_permanente: number;
  profin_climatizacao: number;
  profin_preuni: number;
  valor_total: number;
  calculated_at: string;
}
```

---

## 🚀 **Exemplos de Serviços (Prontos para Usar)**

### **JavaScript/TypeScript - Classe de Serviço**

```typescript
// services/api.ts
class ProfinAPI {
  private baseURL = 'http://localhost:8000';
  private token: string | null = null;

  // Login
  async login(password: string) {
    const response = await fetch(`${this.baseURL}/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });
    
    if (!response.ok) throw new Error('Login falhou');
    
    const data = await response.json();
    this.token = data.access_token;
    localStorage.setItem('token', this.token);
    return data;
  }

  // Anos Letivos
  async getAnosLetivos() {
    const res = await fetch(`${this.baseURL}/anos/`);
    return await res.json();
  }

  async getAnoAtivo() {
    const res = await fetch(`${this.baseURL}/anos/ativo`);
    return await res.json();
  }

  async criarAnoLetivo(ano: number) {
    const res = await fetch(`${this.baseURL}/anos/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ano })
    });
    return await res.json();
  }

  // Uploads
  async listarUploads(anoLetivoId?: number) {
    const url = anoLetivoId 
      ? `${this.baseURL}/uploads/?ano_letivo_id=${anoLetivoId}`
      : `${this.baseURL}/uploads/`;
    const res = await fetch(url);
    return await res.json();
  }

  async obterUpload(uploadId: number) {
    const res = await fetch(`${this.baseURL}/uploads/${uploadId}`);
    return await res.json();
  }

  async uploadExcel(file: File, anoLetivoId?: number) {
    const formData = new FormData();
    formData.append('file', file);
    if (anoLetivoId) {
      formData.append('ano_letivo_id', anoLetivoId.toString());
    }

    const res = await fetch(`${this.baseURL}/uploads/excel`, {
      method: 'POST',
      body: formData
    });
    return await res.json();
  }

  // Cálculos
  async calcularValores(anoLetivoId?: number) {
    const url = anoLetivoId
      ? `${this.baseURL}/calculos/?ano_letivo_id=${anoLetivoId}`
      : `${this.baseURL}/calculos/`;
      
    const res = await fetch(url, { method: 'POST' });
    return await res.json();
  }

  // Admin (requer token)
  async limparDados(anoLetivoId?: number) {
    const token = this.token || localStorage.getItem('token');
    if (!token) throw new Error('Não autenticado');

    const url = anoLetivoId
      ? `${this.baseURL}/admin/limpar-dados?ano_letivo_id=${anoLetivoId}`
      : `${this.baseURL}/admin/limpar-dados`;

    const res = await fetch(url, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return await res.json();
  }

  async getStatusDados() {
    const res = await fetch(`${this.baseURL}/admin/status-dados`);
    return await res.json();
  }
}

export const api = new ProfinAPI();
```

---

## ⚛️ **React Hooks (se usar React)**

```typescript
// hooks/useProfinAPI.ts
import { useState, useEffect } from 'react';
import { api } from '../services/api';

export function useAnosLetivos() {
  const [anos, setAnos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getAnosLetivos()
      .then(data => {
        setAnos(data.anos);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return { anos, loading, error };
}

export function useAnoAtivo() {
  const [ano, setAno] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAnoAtivo()
      .then(data => {
        setAno(data.ano);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return { ano, loading };
}

export function useUploads(anoLetivoId?: number) {
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listarUploads(anoLetivoId)
      .then(data => {
        setUploads(data.uploads);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [anoLetivoId]);

  return { uploads, loading };
}
```

---

## 🎨 **Exemplo de Componente React**

```tsx
// components/UploadForm.tsx
import { useState } from 'react';
import { api } from '../services/api';

export function UploadForm({ anoLetivoId }: { anoLetivoId?: number }) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    try {
      const data = await api.uploadExcel(file, anoLetivoId);
      setResult(data);
      alert(`✅ ${data.escolas_salvas} escolas salvas!`);
    } catch (error) {
      alert('Erro ao fazer upload');
    } finally {
      setUploading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="file"
        accept=".xlsx,.xls,.csv"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button type="submit" disabled={uploading}>
        {uploading ? 'Enviando...' : 'Enviar'}
      </button>
      {result && (
        <div>
          <p>Escolas salvas: {result.escolas_salvas}</p>
          {result.escolas_com_erro > 0 && (
            <p>⚠️ Erros: {result.escolas_com_erro}</p>
          )}
        </div>
      )}
    </form>
  );
}
```

---

## 🔄 **Fluxo Recomendado**

### **1. Inicialização**
```typescript
// Ao carregar a aplicação
const { ano } = await api.getAnoAtivo();
// Armazenar ano ativo no estado global
```

### **2. Upload**
```typescript
// 1. Selecionar arquivo
const file = event.target.files[0];

// 2. Fazer upload
const result = await api.uploadExcel(file, anoAtivo.id);
// result.upload_id → usar para próximos passos
```

### **3. Calcular**
```typescript
// Após upload bem-sucedido
const calculos = await api.calcularValores(anoAtivo.id);
// calculos.valor_total_geral → valor total
// calculos.escolas → lista de escolas com valores
```

### **4. Visualizar**
```typescript
// Ver detalhes de um upload
const detalhes = await api.obterUpload(uploadId);
// detalhes.escolas → escolas com cálculos
```

---

## 🛠️ **Próximos Passos**

1. **Me diga qual framework você usa**
2. **Compartilhe a estrutura do seu frontend**
3. **Eu crio os arquivos específicos** para seu projeto

---

## 💡 **Dicas**

- ✅ Use `try/catch` em todas as chamadas
- ✅ Armazene o token após login
- ✅ Sempre verifique `success` nas respostas
- ✅ Trate erros com mensagens amigáveis
- ✅ Use loading states para melhor UX

---

## 📞 **Como me ajudar a te ajudar**

Se você:
1. **Abrir o frontend no Cursor** → Posso ver e editar diretamente
2. **Copiar arquivos aqui** → Posso criar serviços/hooks
3. **Me dizer o framework** → Crio exemplos específicos

**Qual opção você prefere?** 🚀

