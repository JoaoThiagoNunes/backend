# Documentação - Schemas Pydantic

Esta pasta contém a documentação dos schemas Pydantic utilizados na API.

---

## 📚 Documentação Completa

### [📖 Documentação Detalhada de Todos os Schemas](DOC_SCHEMAS_COMPLETO.md)

Documentação completa com todos os schemas, exemplos, estruturas e validações.

---

## 📋 Resumo dos Schemas

### Schemas de Rotas

#### Admin (`admin.py`)
- `RootResponse` - Resposta do endpoint raiz
- `LimparDadosResponse` - Resposta de limpeza de dados
- `StatusDadosResponse` - Resposta de status do banco
- `HealthCheckResponse` - Resposta de health check
- `ResumoDados` - Resumo de dados do banco
- `AnoAtivoInfo` - Informações do ano ativo
- `AnoStatusInfo` - Informações de status de um ano

#### Anos (`ano.py`)
- `AnoLetivoCreate` - Request para criar ano letivo
- `AnoLetivoRead` - Dados de leitura de ano letivo
- `AnoLetivoListResponse` - Resposta de listagem
- `AnoLetivoDetailResponse` - Resposta de detalhes
- `AnoLetivoCreateResponse` - Resposta de criação
- `AnoLetivoArquivarResponse` - Resposta de arquivamento
- `AnoLetivoDeleteResponse` - Resposta de deleção

#### Uploads (`upload.py`)
- `UploadListResponse` - Resposta de listagem de uploads
- `UploadDetailResponse` - Resposta de detalhes de upload
- `UploadExcelResponse` - Resposta de upload de arquivo
- `UploadListItem` - Item de upload na listagem
- `UploadDetailInfo` - Informações detalhadas de upload
- `EscolaComCalculo` - Escola com seus cálculos
- `CalculoInfo` - Informações de cálculo
- `ErroUpload` - Detalhes de erro no upload

#### Cálculos (`calculos.py`)
- `CalculoItem` - Item de cálculo (valores das cotas)
- `EscolaCalculo` - Cálculo de uma escola
- `ResponseCalculos` - Resposta de cálculo de valores

#### Parcelas (`parcelas.py`)
- `SepararParcelasRequest` - Request para separar parcelas
- `SepararParcelasResponse` - Resposta de separação
- `EscolaParcelas` - Parcelas de uma escola
- `ParcelaPorCota` - Parcelas de uma cota específica
- `ParcelasEscolaResponse` - Resposta com parcelas de escola
- `ParcelaDetalhe` - Detalhe de uma parcela individual
- `ParcelaInfo` - Informações de uma parcela

#### Auth (`auth.py`)
- `LoginRequest` - Request de login
- `LoginResponse` - Resposta de login

#### Escolas (`escola.py`)
- `EscolaCreate` - Request para criar escola
- `EscolaRead` - Dados de leitura de escola
- `EscolaInfo` - Informações básicas de escola

#### Responses (`responses.py`)
- `SuccessResponse` - Resposta padrão de sucesso
- `ErrorResponse` - Resposta padrão de erro

---

## 📝 Notas

- Todos os schemas são validados automaticamente pelo Pydantic
- Schemas de resposta são serializados automaticamente para JSON
- Schemas de request são validados antes de processar a requisição

---

## 🔗 Arquivos Relacionados

- `src/modules/schemas/` - Código fonte dos schemas

