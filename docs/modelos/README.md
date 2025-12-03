# Documentação - Modelos do Banco de Dados

Esta pasta contém a documentação dos modelos SQLAlchemy utilizados no sistema.

---

## 📚 Documentação Completa

### [📖 Documentação Detalhada de Todos os Modelos](DOC_MODELOS_COMPLETO.md)

Documentação completa com todos os modelos, campos, relacionamentos, constraints e exemplos.

---

## 📋 Resumo dos Modelos

### 1. **AnoLetivo**
Tabela: `anos_letivos`

Armazena os anos letivos do sistema.

**Campos:**
- `id` (Integer, PK)
- `ano` (Integer, unique, index)
- `status` (Enum: ATIVO | ARQUIVADO)
- `created_at` (DateTime)
- `arquivado_em` (DateTime, nullable)

**Relacionamentos:**
- `uploads` - Lista de uploads do ano

**Regras:**
- Apenas um ano pode estar ATIVO por vez
- Anos arquivados são mantidos por 5 anos

---

### 2. **Upload**
Tabela: `uploads`

Armazena informações sobre cada upload de arquivo Excel/CSV.

**Campos:**
- `id` (Integer, PK)
- `ano_letivo_id` (Integer, FK -> anos_letivos)
- `filename` (String)
- `upload_date` (DateTime)
- `total_escolas` (Integer)
- `is_active` (Boolean, index)

**Relacionamentos:**
- `ano_letivo` - Ano letivo do upload
- `escolas` - Lista de escolas do upload

---

### 3. **Escola**
Tabela: `escolas`

Armazena os dados de cada escola/UEX.

**Campos:**
- `id` (Integer, PK)
- `upload_id` (Integer, FK -> uploads)
- `nome_uex` (String, index)
- `dre` (String, nullable)
- `total_alunos` (Integer)
- `fundamental_inicial` (Integer)
- `fundamental_final` (Integer)
- `fundamental_integral` (Integer)
- `profissionalizante` (Integer)
- `alternancia` (Integer)
- `ensino_medio_integral` (Integer)
- `ensino_medio_regular` (Integer)
- `especial_fund_regular` (Integer)
- `especial_fund_integral` (Integer)
- `especial_medio_parcial` (Integer)
- `especial_medio_integral` (Integer)
- `sala_recurso` (Integer)
- `climatizacao` (Integer)
- `preuni` (Integer)
- `indigena_quilombola` (String: "SIM" | "NÃO")
- `created_at` (DateTime)

**Constraints:**
- Unique: `(upload_id, nome_uex, dre)`

**Relacionamentos:**
- `upload` - Upload da escola
- `calculos` - Cálculo da escola (one-to-one)

---

### 4. **CalculosProfin**
Tabela: `calculos_profin`

Armazena os cálculos de todas as cotas PROFIN para cada escola.

**Campos:**
- `id` (Integer, PK)
- `escola_id` (Integer, FK -> escolas, unique)
- `profin_custeio` (Float)
- `profin_projeto` (Float)
- `profin_kit_escolar` (Float)
- `profin_uniforme` (Float)
- `profin_merenda` (Float)
- `profin_sala_recurso` (Float)
- `profin_permanente` (Float)
- `profin_climatizacao` (Float)
- `profin_preuni` (Float)
- `valor_total` (Float, index)
- `calculated_at` (DateTime)

**Relacionamentos:**
- `escola` - Escola do cálculo (one-to-one)
- `parcelas` - Lista de parcelas do cálculo

---

### 5. **ParcelasProfin**
Tabela: `parcelas_profin`

Armazena as parcelas divididas por cota, número da parcela e tipo de ensino.

**Campos:**
- `id` (Integer, PK)
- `calculo_id` (Integer, FK -> calculos_profin, index)
- `tipo_cota` (Enum: TipoCota, index)
- `numero_parcela` (Integer: 1 ou 2, index)
- `tipo_ensino` (Enum: TipoEnsino, index)
- `valor_centavos` (Integer) - Valor em centavos
- `porcentagem_alunos` (Float)
- `created_at` (DateTime)
- `calculation_version` (String, nullable)

**Constraints:**
- Unique: `(calculo_id, tipo_cota, numero_parcela, tipo_ensino)`

**Relacionamentos:**
- `calculo` - Cálculo da parcela

**Propriedades:**
- `valor_reais` - Retorna valor em reais (centavos / 100)

---

## 🔑 Enums

### StatusAnoLetivo
- `ATIVO` - Ano letivo ativo
- `ARQUIVADO` - Ano letivo arquivado

### TipoCota
- `CUSTEIO` - Cota de custeio (gestão)
- `PROJETO` - Cota de projeto
- `KIT_ESCOLAR` - Cota de kit escolar
- `UNIFORME` - Cota de uniforme
- `MERENDA` - Cota de merenda
- `SALA_RECURSO` - Cota de sala de recurso
- `PERMANENTE` - Cota permanente
- `CLIMATIZACAO` - Cota de climatização
- `PREUNI` - Cota PREUNI

### TipoEnsino
- `FUNDAMENTAL` - Ensino fundamental
- `MEDIO` - Ensino médio

---

## 🔗 Relacionamentos

```
AnoLetivo (1) ──< (N) Upload (1) ──< (N) Escola (1) ──< (1) CalculosProfin (1) ──< (N) ParcelasProfin
```

---

## 📝 Notas

- **Cascade Delete:** Deleção de ano letivo deleta uploads, escolas, cálculos e parcelas
- **Valores em Centavos:** ParcelasProfin armazena valores em centavos (inteiros) para evitar problemas com floats
- **Unique Constraints:** Garantem integridade dos dados
- **Indexes:** Campos mais consultados têm índices para melhor performance

---

## 🔗 Arquivos Relacionados

- `src/modules/models.py` - Código fonte dos modelos

