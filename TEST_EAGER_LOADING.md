# 🧪 Teste do Eager Loading (Item 8)

## Como Testar Manualmente:

### 1. **Ativar Log de Queries do SQLAlchemy**

Adicione isso temporariamente em `main.py` ou `src/core/database.py`:

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging

logging.basicConfig()
logger_db = logging.getLogger('sqlalchemy.engine')
logger_db.setLevel(logging.INFO)

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    print("SQL:", statement)
```

### 2. **Testar o Endpoint:**

```bash
GET http://localhost:8000/admin/status-dados
```

### 3. **O que Observar:**

**ANTES (sem eager loading):**
```
SQL: SELECT anos_letivos.id, anos_letivos.ano, ... FROM anos_letivos
SQL: SELECT uploads.id, ... FROM uploads WHERE uploads.ano_letivo_id = 1
SQL: SELECT uploads.id, ... FROM uploads WHERE uploads.ano_letivo_id = 2
SQL: SELECT escolas.id, ... FROM escolas WHERE escolas.upload_id = 1
SQL: SELECT escolas.id, ... FROM escolas WHERE escolas.upload_id = 2
SQL: SELECT escolas.id, ... FROM escolas WHERE escolas.upload_id = 3
... (muitas queries!)
```

**DEPOIS (com eager loading):**
```
SQL: SELECT anos_letivos.id, anos_letivos.ano, ...
      FROM anos_letivos 
      LEFT OUTER JOIN uploads ON anos_letivos.id = uploads.ano_letivo_id
      LEFT OUTER JOIN escolas ON uploads.id = escolas.upload_id
      ORDER BY anos_letivos.ano DESC
```

**1 única query com JOINs!** ✅

---

## Verificação da Sintaxe:

A sintaxe está correta:

```python
joinedload(AnoLetivo.uploads).joinedload(Upload.escolas)
```

Isso funciona porque:
- `AnoLetivo.uploads` é um `relationship` definido no modelo
- `Upload.escolas` também é um `relationship`
- SQLAlchemy consegue fazer o JOIN aninhado automaticamente

---

## Teste Prático Rápido:

1. Criar alguns anos letivos com uploads e escolas no banco
2. Chamar `/admin/status-dados`
3. Verificar no log se aparece apenas 1 query SQL (ou algumas, mas muito menos que antes)

**Se aparecerem muitas queries repetidas para cada ano/upload**, então o eager loading não está funcionando.

**Se aparecer apenas 1-2 queries complexas com JOINs**, está funcionando! ✅

