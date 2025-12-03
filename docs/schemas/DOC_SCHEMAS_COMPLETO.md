# Documentação Completa - Schemas Pydantic

**Diretório:** `src/modules/schemas/`

---

## 📋 Visão Geral

Os schemas Pydantic são utilizados para validação e serialização de dados na API. Eles garantem que os dados de entrada sejam válidos e que as respostas sejam consistentes.

---

## 📁 Estrutura por Arquivo

### 1. **admin.py** - Schemas de Administração

#### `RootResponse`
Resposta do endpoint raiz da API.

```python
{
  "message": str,
  "versao": str
}
```

**Exemplo:**
```json
{
  "message": "API funcionando!",
  "versao": "2.0 - Com Anos Letivos"
}
```

---

#### `LimparDadosResponse`
Resposta de limpeza de dados.

```python
{
  "success": bool,  # Padrão: True
  "message": str
}
```

**Exemplo:**
```json
{
  "success": true,
  "message": "✅ Ano letivo 2025 e todos os dados relacionados foram removidos"
}
```

---

#### `ResumoDados`
Resumo estatístico do banco de dados.

```python
{
  "total_anos_letivos": int,
  "total_uploads": int,
  "total_escolas": int,
  "total_calculos": int
}
```

**Exemplo:**
```json
{
  "total_anos_letivos": 2,
  "total_uploads": 3,
  "total_escolas": 500,
  "total_calculos": 500
}
```

---

#### `AnoAtivoInfo`
Informações do ano letivo ativo.

```python
{
  "id": int,
  "ano": int,
  "status": str  # "ATIVO" ou "ARQUIVADO"
}
```

---

#### `AnoStatusInfo`
Informações resumidas de um ano letivo.

```python
{
  "id": int,
  "ano": int,
  "status": str,
  "uploads": int,
  "escolas": int,
  "created_at": datetime | None,
  "arquivado_em": datetime | None
}
```

---

#### `StatusDadosResponse`
Resposta completa de status dos dados.

```python
{
  "success": bool,  # Padrão: True
  "resumo": ResumoDados,
  "ano_ativo": AnoAtivoInfo | None,
  "anos": List[AnoStatusInfo]
}
```

---

#### `HealthCheckResponse`
Resposta de health check.

```python
{
  "status": str,  # "healthy"
  "versao": str,
  "features": List[str]
}
```

**Exemplo:**
```json
{
  "status": "healthy",
  "versao": "2.0",
  "features": ["anos_letivos", "arquivamento_automatico", "isolamento_por_ano"]
}
```

---

### 2. **ano.py** - Schemas de Anos Letivos

#### `AnoLetivoBase`
Schema base para ano letivo.

```python
{
  "ano": int
}
```

---

#### `AnoLetivoCreate`
Request para criar ano letivo (herda de `AnoLetivoBase`).

```python
{
  "ano": int
}
```

**Exemplo:**
```json
{
  "ano": 2026
}
```

---

#### `AnoLetivoRead`
Dados de leitura de ano letivo.

```python
{
  "id": int,
  "ano": int,
  "status": str | None,  # "ATIVO" ou "ARQUIVADO"
  "arquivado_em": datetime | None,
  "created_at": datetime | None,
  "total_uploads": int | None
}
```

**Config:** `from_attributes = True` (compatível com SQLAlchemy)

---

#### `AnoLetivoListResponse`
Resposta de listagem de anos letivos.

```python
{
  "success": bool,  # Padrão: True
  "anos": List[AnoLetivoRead]
}
```

---

#### `AnoLetivoDetailResponse`
Resposta de detalhes de ano letivo.

```python
{
  "success": bool,  # Padrão: True
  "ano": AnoLetivoRead
}
```

---

#### `AnoLetivoCreateResponse`
Resposta de criação de ano letivo.

```python
{
  "success": bool,  # Padrão: True
  "message": str,
  "ano": AnoLetivoRead
}
```

---

#### `AnoLetivoArquivarResponse`
Resposta de arquivamento de ano letivo.

```python
{
  "success": bool,  # Padrão: True
  "message": str,
  "ano": AnoLetivoRead
}
```

---

#### `AnoLetivoDeleteResponse`
Resposta de exclusão de ano letivo.

```python
{
  "success": bool,  # Padrão: True
  "message": str
}
```

---

### 3. **upload.py** - Schemas de Uploads

#### `UploadListItem`
Item de upload na listagem.

```python
{
  "id": int,
  "ano_letivo_id": int,
  "ano_letivo": int,
  "filename": str,
  "upload_date": datetime,
  "total_escolas": int,
  "is_active": bool
}
```

**Config:** `from_attributes = True`

---

#### `UploadListResponse`
Resposta de listagem de uploads.

```python
{
  "success": bool,  # Padrão: True
  "uploads": List[UploadListItem]
}
```

---

#### `UploadDetailInfo`
Informações detalhadas de um upload.

```python
{
  "id": int,
  "ano_letivo_id": int,
  "ano_letivo": int,
  "filename": str,
  "upload_date": datetime,
  "total_escolas": int
}
```

---

#### `CalculoInfo`
Informações de cálculo de uma escola.

```python
{
  "id": int | None,
  "profin_custeio": float | None,
  "profin_projeto": float | None,
  "profin_kit_escolar": float | None,
  "profin_uniforme": float | None,
  "profin_merenda": float | None,
  "profin_sala_recurso": float | None,
  "profin_permanente": float | None,
  "profin_climatizacao": float | None,
  "profin_preuni": float | None,
  "valor_total": float | None,
  "calculated_at": datetime | None
}
```

**Nota:** Todos os campos são opcionais pois a escola pode não ter cálculos ainda.

---

#### `EscolaComCalculo`
Escola com seus cálculos associados.

```python
{
  "escola": EscolaInfo,
  "calculos": CalculoInfo | None
}
```

---

#### `UploadDetailResponse`
Resposta de detalhes de upload.

```python
{
  "success": bool,  # Padrão: True
  "upload": UploadDetailInfo,
  "escolas": List[EscolaComCalculo]
}
```

---

#### `ErroUpload`
Informação de erro no upload.

```python
{
  "linha": int,      # Número da linha do arquivo
  "nome": str,       # Nome da escola
  "erro": str        # Mensagem de erro
}
```

---

#### `UploadExcelResponse`
Resposta de upload de arquivo Excel/CSV.

```python
{
  "success": bool,  # Padrão: True
  "upload_id": int,
  "ano_letivo_id": int,
  "ano_letivo": int,
  "filename": str,
  "total_linhas": int,
  "escolas_salvas": int,
  "escolas_confirmadas_banco": int,
  "escolas_com_erro": int,
  "colunas": List[str],
  "erros": List[ErroUpload] | None,
  "aviso": str | None
}
```

**Exemplo:**
```json
{
  "success": true,
  "upload_id": 1,
  "ano_letivo_id": 2,
  "ano_letivo": 2026,
  "filename": "escolas_2026.xlsx",
  "total_linhas": 250,
  "escolas_salvas": 250,
  "escolas_confirmadas_banco": 250,
  "escolas_com_erro": 0,
  "colunas": ["NOME DA UEX", "DRE", "TOTAL", ...],
  "erros": null,
  "aviso": null
}
```

---

### 4. **calculos.py** - Schemas de Cálculos

#### `CalculoItem`
Item de cálculo com todas as cotas.

```python
{
  "profin_custeio": float,
  "profin_projeto": float,
  "profin_kit_escolar": float,
  "profin_uniforme": float,
  "profin_merenda": float,
  "profin_sala_recurso": float,
  "profin_permanente": float,
  "profin_climatizacao": float,
  "profin_preuni": float,
  "valor_total": float  # Soma de todas as cotas
}
```

---

#### `EscolaCalculo`
Cálculo de uma escola específica.

```python
{
  "id": int,
  "dre": str | None,
  "nome_uex": str,
  "profin_custeio": float,
  "profin_projeto": float,
  "profin_kit_escolar": float,
  "profin_uniforme": float,
  "profin_merenda": float,
  "profin_sala_recurso": float,
  "profin_permanente": float,
  "profin_climatizacao": float,
  "profin_preuni": float,
  "valor_total": float
}
```

---

#### `ResponseCalculos`
Resposta completa de cálculo de valores.

```python
{
  "success": bool,
  "message": str,
  "total_escolas": int,
  "valor_total_geral": float,  # Soma de todos os valores totais
  "escolas": List[EscolaCalculo],
  "upload_id": int,
  "ano_letivo_id": int | None
}
```

**Config:** `from_attributes = True`

**Exemplo:**
```json
{
  "success": true,
  "message": "Cálculos realizados para 250 escolas do ano 2026",
  "total_escolas": 250,
  "valor_total_geral": 40000000.00,
  "escolas": [...],
  "upload_id": 1,
  "ano_letivo_id": 2
}
```

---

### 5. **parcelas.py** - Schemas de Parcelas

#### `SepararParcelasRequest`
Request para separar valores em parcelas.

```python
{
  "ano_letivo_id": int | None,      # Se None, usa ano ativo
  "recalcular": bool,               # Padrão: False
  "calculation_version": str | None  # Versão do cálculo para auditoria
}
```

**Exemplo:**
```json
{
  "ano_letivo_id": null,
  "recalcular": false,
  "calculation_version": "v1.0"
}
```

---

#### `ParcelaInfo`
Informações de uma parcela específica.

```python
{
  "tipo_cota": str,           # "custeio", "merenda", etc.
  "numero_parcela": int,      # 1 ou 2
  "tipo_ensino": str,         # "fundamental" ou "medio"
  "valor_reais": float,
  "valor_centavos": int,
  "porcentagem_alunos": float
}
```

---

#### `ParcelaPorCota`
Parcelas de uma cota específica agrupadas.

```python
{
  "tipo_cota": str,
  "valor_total_reais": float,
  "parcela_1": {
    "fundamental": float,
    "medio": float
  },
  "parcela_2": {
    "fundamental": float,
    "medio": float
  },
  "porcentagens": {
    "fundamental": float,  # 0-100
    "medio": float         # 0-100
  }
}
```

**Exemplo:**
```json
{
  "tipo_cota": "custeio",
  "valor_total_reais": 50000.00,
  "parcela_1": {
    "fundamental": 13125.00,
    "medio": 11875.00
  },
  "parcela_2": {
    "fundamental": 13125.00,
    "medio": 11875.00
  },
  "porcentagens": {
    "fundamental": 52.5,
    "medio": 47.5
  }
}
```

---

#### `EscolaParcelas`
Parcelas completas de uma escola.

```python
{
  "escola_id": int,
  "nome_uex": str,
  "dre": str | None,
  "porcentagem_fundamental": float,  # 0-100
  "porcentagem_medio": float,       # 0-100
  "parcelas_por_cota": List[ParcelaPorCota]
}
```

---

#### `SepararParcelasResponse`
Resposta completa de separação de parcelas.

```python
{
  "success": bool,
  "message": str,
  "total_escolas": int,
  "escolas_processadas": int,
  "total_parcelas_criadas": int,
  "ano_letivo_id": int,
  "escolas": List[EscolaParcelas],
  "calculation_version": str | None
}
```

---

#### `ParcelaDetalhe`
Detalhe de uma parcela individual do banco.

```python
{
  "id": int,
  "tipo_cota": str,
  "numero_parcela": int,      # 1 ou 2
  "tipo_ensino": str,         # "fundamental" ou "medio"
  "valor_reais": float,
  "valor_centavos": int,
  "porcentagem_alunos": float,
  "created_at": datetime
}
```

**Config:** `from_attributes = True`

---

#### `ParcelasEscolaResponse`
Resposta com parcelas de uma escola específica.

```python
{
  "success": bool,
  "escola_id": int,
  "nome_uex": str,
  "dre": str | None,
  "porcentagem_fundamental": float,
  "porcentagem_medio": float,
  "parcelas": List[ParcelaDetalhe]
}
```

---

### 6. **auth.py** - Schemas de Autenticação

#### `LoginRequest`
Request de login.

```python
{
  "password": str
}
```

**Exemplo:**
```json
{
  "password": "profin2024"
}
```

---

#### `LoginResponse`
Resposta de login bem-sucedido.

```python
{
  "access_token": str,          # Token JWT
  "token_type": str,            # Padrão: "bearer"
  "message": str               # Padrão: "Login realizado com sucesso"
}
```

**Exemplo:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "message": "Login realizado com sucesso"
}
```

---

### 7. **escola.py** - Schemas de Escola

#### `EscolaInfo`
Informações completas de uma escola.

```python
{
  "id": int,
  "nome_uex": str,
  "dre": str | None,
  "total_alunos": int,
  "fundamental_inicial": int,
  "fundamental_final": int,
  "fundamental_integral": int,
  "profissionalizante": int,
  "alternancia": int,
  "ensino_medio_integral": int,
  "ensino_medio_regular": int,
  "especial_fund_regular": int,
  "especial_fund_integral": int,
  "especial_medio_parcial": int,
  "especial_medio_integral": int,
  "sala_recurso": int,
  "climatizacao": int,
  "preuni": int,
  "indigena_quilombola": str,  # "SIM" ou "NÃO"
  "created_at": datetime
}
```

---

### 8. **responses.py** - Schemas Genéricos de Resposta

#### `SuccessResponse`
Resposta padrão de sucesso.

```python
{
  "success": bool,      # Padrão: True
  "message": str | None,
  "data": Any | None
}
```

---

#### `ErrorResponse`
Resposta padrão de erro.

```python
{
  "success": bool,      # Padrão: False
  "detail": str,
  "error_code": str | None
}
```

---

## 🔧 Validação Pydantic

Todos os schemas utilizam validação automática do Pydantic:

- **Tipos:** Validação automática de tipos
- **Valores obrigatórios:** Campos sem `None` ou valor padrão são obrigatórios
- **Valores opcionais:** Campos com `None` ou valor padrão são opcionais
- **Serialização:** Conversão automática para JSON
- **Compatibilidade SQLAlchemy:** `from_attributes = True` permite criar schemas a partir de objetos ORM

---

## 📝 Notas Importantes

1. **from_attributes:** Schemas com `from_attributes = True` podem ser criados diretamente de objetos SQLAlchemy
2. **Valores None:** Campos opcionais podem ser `None` ou omitidos na serialização
3. **Datetime:** Datas são serializadas como strings ISO 8601
4. **Validação:** Valores inválidos geram exceções `ValidationError` do Pydantic

---

## 🔗 Arquivos Relacionados

- `src/modules/schemas/` - Código fonte dos schemas
- `src/modules/models.py` - Modelos SQLAlchemy (fonte de dados)
- `src/modules/routes/` - Rotas que utilizam os schemas

