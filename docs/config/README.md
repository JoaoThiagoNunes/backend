# Documentação - Configurações

Esta pasta contém a documentação das configurações do sistema.

---

## 📋 Configurações Disponíveis

### `src/core/config.py`

Arquivo centralizado de configurações do sistema.

---

## 🔧 Variáveis de Ambiente

### Banco de Dados

- `DB_USER` - Usuário do banco de dados (padrão: `postgres`)
- `DB_PASS` - Senha do banco de dados (padrão: `123456`)
- `DB_HOST` - Host do banco de dados (padrão: `localhost`)
- `DB_PORT` - Porta do banco de dados (padrão: `5432`)
- `DB_NAME` - Nome do banco de dados (padrão: `profin_db`)

### Autenticação

- `SECRET_KEY` - Chave secreta para assinar tokens JWT (padrão: `profin-secret-key-change-in-production-2025`)
- `ADMIN_PASSWORD` - Senha do admin (padrão: `profin2025`)
- `ACCESS_TOKEN_EXPIRE_HOURS` - Tempo de expiração do token em horas (padrão: `12`)

### CORS

- `CORS_ORIGINS` - Origens permitidas para CORS, separadas por vírgula (padrão: `http://localhost:3000`)

### Logging

- `LOG_LEVEL` - Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL) (padrão: `INFO`)
- `LOG_DIR` - Diretório de logs (padrão: `BASE_DIR/logs`)

### Scheduler

- `SCHEDULER_TIMEZONE` - Fuso horário para o scheduler (padrão: `America/Maceio`)

### Upload de Arquivos

- `MAX_UPLOAD_SIZE_MB` - Tamanho máximo de upload em MB (padrão: `50`)
- `ALLOWED_EXTENSIONS` - Extensões permitidas: `.xlsx`, `.xls`, `.csv`

---

## 📝 Arquivo .env

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# --- BANCO DE DADOS ---
DB_USER=postgres
DB_PASS=123456
DB_HOST=localhost
DB_PORT=5432
DB_NAME=profin_db

# --- AUTENTICAÇÃO ---
SECRET_KEY=profin-secret-key-change-in-production-2025
ADMIN_PASSWORD=profin2025
ACCESS_TOKEN_EXPIRE_HOURS=12

# --- CORS ---
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# --- LOGGING ---
LOG_LEVEL=INFO

# --- SCHEDULER ---
SCHEDULER_TIMEZONE=America/Maceio

# --- UPLOAD DE ARQUIVOS ---
MAX_UPLOAD_SIZE_MB=50
```

---

## ⚠️ Importante

- **Produção:** Altere `SECRET_KEY` e `ADMIN_PASSWORD` em produção!
- **Segurança:** Nunca commite o arquivo `.env` no Git
- **Exemplo:** Use `env.example` como template

---

---

## ✅ Validação de Configurações

### `src/core/config_validator.py`

O sistema valida automaticamente as configurações no startup da aplicação através da classe `ConfigValidator`.

#### Métodos Disponíveis

**`validate_database_config()`**
- Valida que as configurações do banco de dados não estão vazias
- Valida que a porta do banco é um número válido (1-65535)
- Emite logs informativos

**`validate_auth_config()`**
- Verifica se `SECRET_KEY` e `ADMIN_PASSWORD` estão configuradas
- Emite avisos se valores padrão estão sendo usados (não seguros para produção)
- Recomenda `SECRET_KEY` com pelo menos 32 caracteres

**`validate_all()`**
- Executa todas as validações
- Chamado automaticamente no startup em `main.py`

#### Comportamento

- **Desenvolvimento**: Aceita valores padrão e emite avisos
- **Produção**: Recomenda configurar todas as variáveis de ambiente
- **Erros**: Lança `BadRequestException` se configurações críticas estiverem inválidas

#### Exemplo de Uso

```python
from src.core.config_validator import ConfigValidator

# Validar todas as configurações
ConfigValidator.validate_all()

# Ou validar individualmente
ConfigValidator.validate_database_config()
ConfigValidator.validate_auth_config()
```

---

## 🔗 Arquivos Relacionados

- `src/core/config.py` - Código fonte das configurações
- `src/core/config_validator.py` - Validador de configurações
- `env.example` - Exemplo de arquivo .env

