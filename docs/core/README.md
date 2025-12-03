# Documentação - Módulo Core

Esta pasta contém a documentação dos componentes centrais da aplicação.

---

## 📋 Componentes Disponíveis

### 🔐 Autenticação (`auth.py`)

Sistema de autenticação JWT para proteção de rotas.

- Geração e validação de tokens JWT
- Hash de senhas com bcrypt
- Dependência `get_current_user` para rotas protegidas

---

### ⚙️ Configurações (`config.py`)

Arquivo centralizado de configurações do sistema.

- Variáveis de ambiente com valores padrão
- Configurações de banco de dados, autenticação, CORS, logging, etc.
- Consulte [docs/config/README.md](../config/README.md) para detalhes

---

### ✅ Validador de Configurações (`config_validator.py`)

Validação automática de configurações no startup.

- Valida configurações do banco de dados
- Verifica segurança de chaves de autenticação
- Emite avisos sobre uso de valores padrão

**Métodos:**
- `validate_database_config()` - Valida configurações do banco
- `validate_auth_config()` - Valida configurações de autenticação
- `validate_all()` - Executa todas as validações

---

### 🗄️ Banco de Dados (`database.py`)

Configuração e gerenciamento de sessões do banco de dados.

#### Componentes

**Engine e Session**
- `engine` - Engine SQLAlchemy configurado
- `SessionLocal` - Factory de sessões

**Funções**

**`get_db() -> Generator`**
- Dependência FastAPI para obter sessão do banco
- Gerencia ciclo de vida da sessão automaticamente
- Uso em rotas FastAPI

```python
@router.get("/endpoint")
def meu_endpoint(db: Session = Depends(get_db)):
    # usar db aqui
    pass
```

**`get_db_session() -> Generator[Session, None, None]`**
- Context manager para obter sessão fora do FastAPI
- Útil para scheduler, scripts, etc.
- Fecha sessão automaticamente ao sair do contexto

```python
from src.core.database import get_db_session

with get_db_session() as db:
    # usar db aqui
    db.commit()
```

**`transaction(db: Session) -> Generator[Session, None, None]`**
- Context manager para gerenciar transações
- Commit automático se sucesso
- Rollback automático se erro

```python
from src.core.database import get_db_session, transaction

with get_db_session() as db:
    with transaction(db):
        # operações no banco
        # commit automático se sucesso
        # rollback automático se erro
        pass
```

---

### 🚨 Exceções (`exceptions.py`)

Exceções customizadas para tratamento padronizado de erros.

**Classes:**
- `BaseAPIException` - Base para todas as exceções da API
- `NotFoundException` - Recurso não encontrado (404)
- `BadRequestException` - Requisição inválida (400)
- `ValidationException` - Erro de validação (422)
- `UnauthorizedException` - Não autorizado (401)
- `ForbiddenException` - Acesso negado (403)

**Função:**
- `handle_exception(e: Exception)` - Converte exceções genéricas em HTTPException

---

### 🔄 Middlewares (`middleware.py`)

Middlewares globais para tratamento de erros e logging.

#### `error_handler_middleware`

Middleware global para tratamento de erros.

**Funcionalidades:**
- Captura todas as exceções não tratadas
- Retorna respostas padronizadas em JSON
- Usa exceções customizadas quando disponível
- Loga erros para debugging

**Tipos de Erros Tratados:**
- `BaseAPIException` - Exceções customizadas do projeto
- `StarletteHTTPException` - HTTPException do FastAPI/Starlette
- `RequestValidationError` - Erros de validação do Pydantic
- `Exception` - Erros não tratados (genéricos)

**Formato de Resposta:**
```json
{
  "success": false,
  "error": "Mensagem de erro",
  "error_code": "ERROR_CODE",
  "path": "/caminho/da/requisicao"
}
```

#### `logging_middleware`

Middleware para logar todas as requisições HTTP.

**Funcionalidades:**
- Registra método, path e IP do cliente na entrada
- Registra status code e tempo de processamento na saída
- Adiciona header `X-Process-Time` nas respostas

**Formato de Log:**
```
→ GET /endpoint [Client: 127.0.0.1]
← GET /endpoint [Status: 200] [Time: 0.123s]
```

---

### 📅 Scheduler (`jobs/scheduler.py`)

Sistema de tarefas agendadas para operações automáticas.

**Tarefas:**
- `arquivar_anos_automaticamente()` - Arquivamento de anos letivos (31/12)
- `limpar_anos_antigos()` - Limpeza de anos arquivados há mais de 5 anos

**Configuração:**
- Executa diariamente à meia-noite (00:00 e 00:30)
- Usa timezone configurável (`SCHEDULER_TIMEZONE`)
- Usa context managers para gerenciamento seguro de sessões

---

### 📝 Logging (`logging_config.py`)

Configuração centralizada de logging.

- Logger principal: `profin`
- Rotação automática de arquivos
- Logs em `logs/app.log`
- Nível configurável via `LOG_LEVEL`

---

### 🛠️ Utilitários (`utils.py`)

Funções utilitárias genéricas compartilhadas.

Consulte [docs/utils/README.md](../utils/README.md) para documentação completa.

**Funções Principais:**
- `obter_ano_letivo()` - Busca ano letivo ativo ou por ID
- `obter_quantidade()` - Extrai quantidade de uma coluna da planilha
- `obter_quantidade_por_nome()` - Busca quantidade por nome normalizado
- `obter_texto()` - Extrai texto de uma coluna
- `validar_indigena_e_quilombola()` - Valida campos indígena/quilombola

---

## 🔗 Links Relacionados

- [Documentação de Configurações](../config/README.md)
- [Documentação de Utilitários](../utils/README.md)
- [Arquitetura do Projeto](../../ARCHITECTURE.md)


