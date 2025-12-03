# Documentação Completa - Modelos do Banco de Dados

**Arquivo:** `src/modules/models.py`

---

## 📋 Visão Geral

Modelos SQLAlchemy que representam as tabelas do banco de dados PostgreSQL. Todos os modelos herdam de `Base` e são mapeados automaticamente para tabelas.

---

## 🔗 Relacionamentos

```
AnoLetivo (1) ──< (N) Upload (1) ──< (N) Escola (1) ──< (1) CalculosProfin (1) ──< (N) ParcelasProfin
```

---

## 📊 Modelos Detalhados

### 1. **StatusAnoLetivo** (Enum)

Enum para status de ano letivo.

**Valores:**
- `ATIVO` - Ano letivo ativo (apenas um pode estar ativo)
- `ARQUIVADO` - Ano letivo arquivado

**Uso:**
```python
StatusAnoLetivo.ATIVO
StatusAnoLetivo.ARQUIVADO
```

---

### 2. **AnoLetivo**

**Tabela:** `anos_letivos`

Armazena os anos letivos do sistema.

#### Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer (PK) | ID único do ano letivo |
| `ano` | Integer (unique, index) | Ano letivo (ex: 2025, 2026) |
| `status` | Enum (index) | Status: ATIVO ou ARQUIVADO |
| `created_at` | DateTime | Data de criação |
| `arquivado_em` | DateTime (nullable) | Data de arquivamento (null se ativo) |

#### Relacionamentos

- `uploads` (one-to-many): Lista de uploads do ano
  - `cascade="all, delete-orphan"` - Deleta uploads ao deletar ano

#### Regras de Negócio

- **Apenas um ano pode estar ATIVO por vez**
- Anos arquivados são mantidos por 5 anos
- Deleção em cascade: deletar ano deleta uploads, escolas, cálculos e parcelas

#### Exemplo de Uso

```python
# Criar ano letivo
ano = AnoLetivo(ano=2026, status=StatusAnoLetivo.ATIVO)
db.add(ano)
db.commit()

# Buscar ano ativo
ano_ativo = db.query(AnoLetivo).filter(
    AnoLetivo.status == StatusAnoLetivo.ATIVO
).first()
```

---

### 3. **Upload**

**Tabela:** `uploads`

Armazena informações sobre cada upload de arquivo Excel/CSV.

#### Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer (PK) | ID único do upload |
| `ano_letivo_id` | Integer (FK, index) | ID do ano letivo |
| `filename` | String(255) | Nome do arquivo |
| `upload_date` | DateTime | Data/hora do upload |
| `total_escolas` | Integer | Total de escolas no upload |
| `is_active` | Boolean (index) | Se é o upload ativo do ano |

#### Relacionamentos

- `ano_letivo` (many-to-one): Ano letivo do upload
- `escolas` (one-to-many): Lista de escolas do upload
  - `cascade="all, delete-orphan"` - Deleta escolas ao deletar upload

#### Regras de Negócio

- Cada ano letivo tem apenas um upload ativo (`is_active=True`)
- Novos uploads substituem o upload ativo anterior

#### Exemplo de Uso

```python
# Buscar upload ativo
upload = db.query(Upload).filter(
    Upload.ano_letivo_id == ano_id,
    Upload.is_active == True
).first()

# Criar upload
upload = Upload(
    ano_letivo_id=ano_id,
    filename="escolas_2026.xlsx",
    total_escolas=250,
    is_active=True
)
```

---

### 4. **Escola**

**Tabela:** `escolas`

Armazena os dados de cada escola/UEX.

#### Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer (PK) | ID único da escola |
| `upload_id` | Integer (FK) | ID do upload |
| `nome_uex` | String(255, index) | Nome da escola |
| `dre` | String(100, nullable) | Diretoria Regional de Educação |
| `total_alunos` | Integer | Total de alunos |
| `fundamental_inicial` | Integer | Alunos fundamental inicial |
| `fundamental_final` | Integer | Alunos fundamental final |
| `fundamental_integral` | Integer | Alunos fundamental integral |
| `profissionalizante` | Integer | Alunos profissionalizantes |
| `alternancia` | Integer | Alunos de alternância |
| `ensino_medio_integral` | Integer | Alunos ensino médio integral |
| `ensino_medio_regular` | Integer | Alunos ensino médio regular |
| `especial_fund_regular` | Integer | Alunos especial fundamental regular |
| `especial_fund_integral` | Integer | Alunos especial fundamental integral |
| `especial_medio_parcial` | Integer | Alunos especial médio parcial |
| `especial_medio_integral` | Integer | Alunos especial médio integral |
| `sala_recurso` | Integer | Alunos em sala de recurso |
| `climatizacao` | Integer | Quantidade de aparelhos de climatização |
| `preuni` | Integer | Alunos PREUNI |
| `indigena_quilombola` | String(10) | "SIM" ou "NÃO" |
| `created_at` | DateTime | Data de criação |

#### Constraints

- **Unique:** `(upload_id, nome_uex, dre)` - Evita duplicatas no mesmo upload

#### Relacionamentos

- `upload` (many-to-one): Upload da escola
- `calculos` (one-to-one): Cálculo da escola
  - `cascade="all, delete-orphan"` - Deleta cálculo ao deletar escola

#### Exemplo de Uso

```python
# Criar escola
escola = Escola(
    upload_id=upload_id,
    nome_uex="ESCOLA MUNICIPAL EXEMPLO",
    dre="DRE-01",
    total_alunos=500,
    fundamental_inicial=100,
    # ... outros campos
)
db.add(escola)
db.commit()

# Buscar escolas de um upload
escolas = db.query(Escola).filter(
    Escola.upload_id == upload_id
).all()
```

---

### 5. **CalculosProfin**

**Tabela:** `calculos_profin`

Armazena os cálculos de todas as cotas PROFIN para cada escola.

#### Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer (PK) | ID único do cálculo |
| `escola_id` | Integer (FK, unique) | ID da escola (único) |
| `profin_custeio` | Float | Valor da cota de custeio |
| `profin_projeto` | Float | Valor da cota de projeto |
| `profin_kit_escolar` | Float | Valor da cota de kit escolar |
| `profin_uniforme` | Float | Valor da cota de uniforme |
| `profin_merenda` | Float | Valor da cota de merenda |
| `profin_sala_recurso` | Float | Valor da cota de sala de recurso |
| `profin_permanente` | Float | Valor da cota permanente |
| `profin_climatizacao` | Float | Valor da cota de climatização |
| `profin_preuni` | Float | Valor da cota PREUNI |
| `valor_total` | Float (index) | Soma de todas as cotas |
| `calculated_at` | DateTime | Data/hora do cálculo |

#### Constraints

- **Unique:** `escola_id` - Uma escola tem apenas um cálculo

#### Relacionamentos

- `escola` (one-to-one): Escola do cálculo
- `parcelas` (one-to-many): Lista de parcelas do cálculo
  - `cascade="all, delete-orphan"` - Deleta parcelas ao deletar cálculo

#### Exemplo de Uso

```python
# Criar cálculo
calculo = CalculosProfin(
    escola_id=escola_id,
    profin_custeio=50000.00,
    profin_projeto=10000.00,
    # ... outras cotas
    valor_total=160000.00,
    calculated_at=datetime.now()
)
db.add(calculo)
db.commit()

# Buscar cálculo de uma escola
calculo = db.query(CalculosProfin).filter(
    CalculosProfin.escola_id == escola_id
).first()
```

---

### 6. **ParcelasProfin**

**Tabela:** `parcelas_profin`

Armazena as parcelas divididas por cota, número da parcela e tipo de ensino.

#### Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer (PK) | ID único da parcela |
| `calculo_id` | Integer (FK, index) | ID do cálculo |
| `tipo_cota` | Enum (index) | Tipo de cota (TipoCota) |
| `numero_parcela` | Integer (index) | Número da parcela (1 ou 2) |
| `tipo_ensino` | Enum (index) | Tipo de ensino (TipoEnsino) |
| `valor_centavos` | Integer | Valor em centavos (inteiro) |
| `porcentagem_alunos` | Float | Porcentagem de alunos (0-100) |
| `created_at` | DateTime | Data de criação |
| `calculation_version` | String(50, nullable) | Versão do cálculo (auditoria) |

#### Constraints

- **Unique:** `(calculo_id, tipo_cota, numero_parcela, tipo_ensino)` - Evita duplicatas

#### Relacionamentos

- `calculo` (many-to-one): Cálculo da parcela

#### Propriedades

- `valor_reais` (property): Retorna valor em reais (centavos / 100)

#### Exemplo de Uso

```python
# Criar parcela
parcela = ParcelasProfin(
    calculo_id=calculo_id,
    tipo_cota=TipoCota.CUSTEIO,
    numero_parcela=1,
    tipo_ensino=TipoEnsino.FUNDAMENTAL,
    valor_centavos=1312500,  # R$ 13.125,00 em centavos
    porcentagem_alunos=52.5,
    calculation_version="v1.0"
)
db.add(parcela)
db.commit()

# Acessar valor em reais
valor = parcela.valor_reais  # 13125.00
```

---

## 🔑 Enums

### TipoCota

Tipos de cotas PROFIN.

**Valores:**
- `CUSTEIO` - Cota de custeio (gestão)
- `PROJETO` - Cota de projeto
- `KIT_ESCOLAR` - Cota de kit escolar
- `UNIFORME` - Cota de uniforme
- `MERENDA` - Cota de merenda
- `SALA_RECURSO` - Cota de sala de recurso
- `PERMANENTE` - Cota permanente
- `CLIMATIZACAO` - Cota de climatização
- `PREUNI` - Cota PREUNI

**Uso:**
```python
TipoCota.CUSTEIO
TipoCota.MERENDA
```

---

### TipoEnsino

Tipos de ensino.

**Valores:**
- `FUNDAMENTAL` - Ensino fundamental
- `MEDIO` - Ensino médio

**Uso:**
```python
TipoEnsino.FUNDAMENTAL
TipoEnsino.MEDIO
```

---

## 🔄 Cascade Delete

A hierarquia de deleção em cascade:

1. **Deletar AnoLetivo** → Deleta Uploads → Deleta Escolas → Deleta Cálculos → Deleta Parcelas
2. **Deletar Upload** → Deleta Escolas → Deleta Cálculos → Deleta Parcelas
3. **Deletar Escola** → Deleta Cálculo → Deleta Parcelas
4. **Deletar CalculosProfin** → Deleta Parcelas

---

## 📊 Índices

Índices criados para melhor performance:

- `anos_letivos.ano` - Busca por ano
- `anos_letivos.status` - Busca por status
- `uploads.ano_letivo_id` - Join com anos
- `uploads.is_active` - Busca upload ativo
- `escolas.nome_uex` - Busca por nome
- `calculos_profin.valor_total` - Ordenação por valor
- `parcelas_profin.calculo_id` - Join com cálculos
- `parcelas_profin.tipo_cota` - Filtro por cota
- `parcelas_profin.numero_parcela` - Filtro por parcela
- `parcelas_profin.tipo_ensino` - Filtro por ensino

---

## 🔍 Queries Comuns

### Buscar escolas de um ano letivo

```python
escolas = db.query(Escola)\
    .join(Upload)\
    .filter(Upload.ano_letivo_id == ano_id)\
    .all()
```

### Buscar cálculos de um ano letivo

```python
calculos = db.query(CalculosProfin)\
    .join(Escola, CalculosProfin.escola_id == Escola.id)\
    .join(Upload, Escola.upload_id == Upload.id)\
    .filter(Upload.ano_letivo_id == ano_id)\
    .all()
```

### Buscar parcelas de uma escola

```python
parcelas = db.query(ParcelasProfin)\
    .join(CalculosProfin, ParcelasProfin.calculo_id == CalculosProfin.id)\
    .filter(CalculosProfin.escola_id == escola_id)\
    .all()
```

---

## 📝 Notas Importantes

1. **Valores em Centavos:** `ParcelasProfin.valor_centavos` armazena valores como inteiros para evitar problemas com floats
2. **Unique Constraints:** Garantem integridade dos dados (evita duplicatas)
3. **Cascade Delete:** Deleção em cascata mantém integridade referencial
4. **Indexes:** Campos mais consultados têm índices para melhor performance
5. **Relacionamentos:** SQLAlchemy gerencia relacionamentos automaticamente

---

## 🔗 Arquivos Relacionados

- `src/modules/models.py` - Código fonte dos modelos
- `src/core/database.py` - Configuração do banco de dados
- `src/core/init_db.py` - Script de inicialização do banco

