# Documentação da API PROFIN

Bem-vindo à documentação completa da API PROFIN.

---

## 📚 Estrutura da Documentação

A documentação está organizada em subpastas por categoria:

### 📁 [Core](core/README.md)
Documentação dos componentes centrais da aplicação.

- Autenticação JWT
- Configurações e validação
- Banco de dados e transações
- Middlewares globais
- Exceções customizadas
- Scheduler e tarefas agendadas
- Logging

---

### 📁 [Rotas](rotas/README.md)
Documentação completa de todas as rotas da API.

- [Índice Geral de Rotas](rotas/DOC_INDICE_ROTAS.md)
- [Rotas de Administração](rotas/DOC_ROTAS_ADMIN.md)
- [Rotas de Anos Letivos](rotas/DOC_ROTAS_ANOS.md)
- [Rotas de Uploads](rotas/DOC_ROTAS_UPLOADS.md)
- [Rotas de Cálculos](rotas/DOC_ROTAS_CALCULOS.md)
- [Rotas de Parcelas](rotas/DOC_ROTAS_PARCELAS.md)
- [Rotas de Complemento](rotas/DOC_ROTAS_COMPLEMENTO.md)

---

### 📁 [Schemas](schemas/README.md)
Documentação dos schemas Pydantic utilizados na API.

- [📖 Documentação Completa](schemas/DOC_SCHEMAS_COMPLETO.md) - Todos os schemas detalhados
- Schemas de request/response
- Validação de dados
- Estrutura de dados

---

### 📁 [Modelos](modelos/README.md)
Documentação dos modelos SQLAlchemy do banco de dados.

- [📖 Documentação Completa](modelos/DOC_MODELOS_COMPLETO.md) - Todos os modelos detalhados
- Estrutura das tabelas
- Relacionamentos
- Constraints e índices
- Enums

---

### 📁 [Utilitários](utils/README.md)
Documentação das funções utilitárias do sistema.

- [📖 Documentação Completa](utils/DOC_UTILS_COMPLETO.md) - Todas as funções detalhadas
- Funções de processamento
- Funções de cálculo
- Funções auxiliares

**Nota:** Funções específicas de domínio foram movidas para seus respectivos módulos de features.

---

### 📁 [Configurações](config/README.md)
Documentação das configurações e variáveis de ambiente.

- Variáveis de ambiente
- Configurações do sistema
- Validação de configurações
- Arquivo .env

---

## 🚀 Quick Start

### 1. Criar Ano Letivo
```bash
POST /anos
{
  "ano": 2026
}
```

### 2. Upload de Dados
```bash
POST /uploads/excel
# FormData: file + ano_letivo_id (opcional)
```

### 3. Calcular Valores
```bash
POST /calculos
```

### 4. Criar Parcelas
```bash
POST /parcelas
{
  "recalcular": false
}
```

---

## 📝 Notas Gerais

- **Base URL:** `http://localhost:8000` (desenvolvimento)
- **Formato:** JSON
- **Autenticação:** JWT (apenas para rotas protegidas)

---

## 🏗️ Arquitetura

Para entender a arquitetura completa do projeto, consulte:
- [Arquitetura do Projeto](../ARCHITECTURE.md)

---

**Última atualização:** 2025-12-02


