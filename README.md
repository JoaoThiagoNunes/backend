# PROFIN API

API REST para cálculo e gerenciamento de valores PROFIN por escola.

## 📋 Sobre o Projeto

A API PROFIN é uma aplicação FastAPI que gerencia cálculos de valores PROFIN (Programa de Financiamento da Educação Básica) por escola, incluindo:

- Gerenciamento de anos letivos
- Upload e processamento de planilhas Excel/CSV
- Cálculos automáticos de valores por cota (gestão, merenda, uniforme, etc.)
- Divisão de valores em parcelas por tipo de ensino
- Gerenciamento de liberações de pagamento
- Gerenciamento de projetos aprovados

## 🚀 Tecnologias

- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para banco de dados
- **PostgreSQL** - Banco de dados relacional
- **Pydantic** - Validação de dados
- **Alembic** - Migrações de banco de dados
- **APScheduler** - Tarefas agendadas
- **Pandas** - Processamento de dados

## 📁 Estrutura do Projeto

```
backend/
├── src/
│   ├── core/              # Funcionalidades centrais
│   │   ├── auth.py        # Autenticação JWT
│   │   ├── config.py      # Configurações
│   │   ├── config_validator.py  # Validação de config
│   │   ├── database.py    # Configuração do banco
│   │   ├── exceptions.py  # Exceções customizadas
│   │   ├── middleware.py  # Middlewares globais
│   │   ├── jobs/          # Tarefas agendadas
│   │   └── utils.py       # Utilitários genéricos
│   └── modules/
│       ├── api/           # Centralização de routers/models
│       ├── features/      # Features organizadas por domínio
│       ├── schemas/       # Schemas Pydantic
│       └── shared/        # Componentes compartilhados
├── docs/                  # Documentação completa
├── alembic/               # Migrações do banco
└── main.py               # Ponto de entrada
```

## 🛠️ Instalação

### Pré-requisitos

- Python 3.9+
- PostgreSQL
- pip

### Passos

1. **Clone o repositório**
```bash
git clone <repository-url>
cd backend
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv
```

3. **Ative o ambiente virtual**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Instale as dependências**
```bash
pip install -r requirements.txt
```

5. **Configure as variáveis de ambiente**

Copie o arquivo `env.example` para `.env` e configure:

```env
DB_USER=postgres
DB_PASS=sua_senha
DB_HOST=localhost
DB_PORT=5432
DB_NAME=profin_db

SECRET_KEY=sua_chave_secreta_aqui
ADMIN_PASSWORD=sua_senha_admin
```

6. **Configure o banco de dados**

Crie o banco de dados PostgreSQL:
```sql
CREATE DATABASE profin_db;
```

7. **Execute as migrações**
```bash
alembic upgrade head
```

8. **Inicie o servidor**
```bash
uvicorn main:app --reload
```

A API estará disponível em `http://localhost:8000`

## 📚 Documentação

### Documentação Interativa

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Documentação Completa

Consulte a pasta `docs/` para documentação detalhada:

- [📖 Documentação Geral](docs/README.md)
- [🔧 Configurações](docs/config/README.md)
- [🛣️ Rotas da API](docs/rotas/README.md)
- [📊 Modelos de Dados](docs/modelos/README.md)
- [📝 Schemas](docs/schemas/README.md)
- [🔨 Utilitários](docs/utils/README.md)
- [🏗️ Arquitetura](ARCHITECTURE.md)

## 🔑 Autenticação

A API usa JWT para autenticação. Para obter um token:

```bash
POST /admin/login
{
  "username": "admin",
  "password": "sua_senha_admin"
}
```

Use o token retornado no header:
```
Authorization: Bearer <token>
```

## 🎯 Funcionalidades Principais

### 1. Gerenciamento de Anos Letivos
- Criar, listar e arquivar anos letivos
- Um único ano letivo ativo por vez

### 2. Upload de Planilhas
- Upload de planilhas Excel/CSV com dados das escolas
- Processamento automático e validação de dados
- Suporte para múltiplos formatos de colunas

### 3. Cálculos Automáticos
- Cálculo de valores por cota (gestão, merenda, uniforme, etc.)
- Cálculo baseado em quantidade de alunos por modalidade
- Valores atualizados automaticamente

### 4. Gerenciamento de Parcelas
- Divisão automática de valores em parcelas
- Separação por tipo de ensino (fundamental/médio)
- Controle de liberações de pagamento

### 5. Projetos Aprovados
- Gerenciamento de projetos aprovados por escola
- Cálculo de valores baseado em quantidade de projetos
- Liberações de pagamento

## 🔧 Configuração Avançada

### Middlewares

A aplicação inclui middlewares globais:

- **Error Handler**: Tratamento centralizado de erros
- **Logging**: Log de todas as requisições HTTP

### Validação de Configuração

O sistema valida automaticamente as configurações no startup:

- Validação de configurações do banco de dados
- Avisos sobre uso de valores padrão (não seguros para produção)

### Gerenciamento de Transações

Context managers para gerenciamento seguro de transações:

```python
from src.core.database import get_db_session, transaction

with get_db_session() as db:
    with transaction(db):
        # operações no banco
        # commit automático se sucesso
        # rollback automático se erro
```

### Tarefas Agendadas

O scheduler executa automaticamente:

- Arquivamento de anos letivos (31/12)
- Limpeza de anos antigos (>5 anos arquivados)

## 📝 Exemplos de Uso

### Criar Ano Letivo
```bash
POST /anos
{
  "ano": 2026
}
```

### Upload de Planilha
```bash
POST /uploads/excel
Content-Type: multipart/form-data

file: <arquivo.xlsx>
ano_letivo_id: 1 (opcional)
```

### Calcular Valores
```bash
POST /calculos?ano_letivo_id=1
```

### Criar Parcelas
```bash
POST /parcelas
{
  "ano_letivo_id": 1,
  "recalcular": false
}
```

## 🧪 Testes

```bash
# Executar testes (quando implementados)
pytest
```

## 📦 Dependências Principais

- `fastapi` - Framework web
- `sqlalchemy` - ORM
- `pydantic` - Validação
- `alembic` - Migrações
- `apscheduler` - Tarefas agendadas
- `pandas` - Processamento de dados
- `python-jose` - JWT
- `passlib` - Hash de senhas

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob licença MIT.

## 👥 Autores

- Equipe PROFIN

## 🔗 Links Úteis

- [Documentação FastAPI](https://fastapi.tiangolo.com/)
- [Documentação SQLAlchemy](https://docs.sqlalchemy.org/)
- [Documentação Pydantic](https://docs.pydantic.dev/)

---

**Última atualização:** 2025-12-02

